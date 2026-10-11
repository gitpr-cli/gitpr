"""Use case: write the baseline a repository commits, and move it forward later.

`create` records what this diff shows as the state the team accepts: every
finding the linter can see, plus the structured findings of the last AI review
of the same diff, when there is one. `update` is the other half — it takes the
file that is there and moves it forward, preserving the decisions a human made
in it.

Two sources, one file, and only these two commands write it. §5.9 of the spec is
explicit that a review never updates the baseline on its own: a feature that
silently rewrites the record it is judged against is not a record.

The AI half is optional by design. A baseline built from the linter alone is
complete and correct, just narrower — and the linter is the half whose findings
carry a rule id, which is what makes a `rule` or `file` scope suppression
possible. Those findings are also the ones that matter for adoption, because
they are what turns the first run in a legacy tree red.

Nothing here prints. Each function returns what it did, and the CLI layer
decides what that looks like on a terminal.
"""

import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Sequence

from src.diff_parser import split_patch_sections
from src.domain.baseline import (
    FINGERPRINT_VERSION,
    SCHEMA_VERSION,
    BaselineEntry,
    BaselineError,
    BaselineManifest,
    BaselineStatus,
    ComparedFinding,
    classify_findings,
    compute_fingerprint,
    is_low_confidence,
    normalize_path,
    rule_identity,
    status_counts,
)
from src.domain.finding.finding_types import NormalizedFinding
from src.i18n import __
from src.infrastructure.baseline.local_baseline_repository import (
    read_baseline,
    read_manifest_raw,
    write_manifest,
)

PROVENANCE_ORIGIN = "local"
PROVENANCE_COMMAND_CREATE = "baseline create"
PROVENANCE_COMMAND_UPDATE = "baseline update"

# What an AI finding falls back to when the model omitted its category. It is
# not decoration: with no rule id the identity *is* the category, so this string
# is what a `rule`-scope suppression would have to name.
AI_DEFAULT_CATEGORY = "review"


@dataclass
class BaselineRun:
    """What a `create`/`update` did, ready to be printed.

    `counts` classifies the findings of this run against the manifest that was
    in force *before* the write, which is what makes the numbers readable: on a
    fresh repository every finding reads `new` — that is what the team has just
    accepted — and on a refresh the same number is the delta since the last
    baseline.
    """

    path: str
    manifest: BaselineManifest
    compared: list[ComparedFinding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created: bool = False
    written: bool = True
    ai_findings: int = 0

    @property
    def counts(self) -> dict[str, int]:
        """One count per status, over every finding that was classified."""
        return status_counts(self.compared)


def current_diff(base: str | None = None, quiet: bool = True) -> str:
    """The diff a baseline is built from.

    With *base* it runs the very command `gitpr risk --base` runs, same flags
    and same smart excludes, so the two commands see one diff — a baseline built
    from `HEAD` classifies nearly everything as new when risk later runs against
    a branch, and the pair has to walk together.
    """
    if not base:
        from src.core import get_git_diff

        return get_git_diff(quiet=quiet) or ""

    from src.core import SMART_EXCLUDES

    result = subprocess.run(
        ["git", "diff", "-U1", "-w", "-M", "-B", base, "--"] + SMART_EXCLUDES,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout if result.returncode == 0 else ""


def diff_files(diff_text: str) -> list[str]:
    """The paths the diff touches — what `update` needs to call a finding gone."""
    return [section.path for section in split_patch_sections(diff_text or "")]


def current_commit(repo_path: str | None = None) -> str | None:
    """The short hash of HEAD, or None outside a repository.

    An entry records the commit a finding was first and last seen at, and that
    is all it records about the tree: the hash is a label for a human reading
    the file, never part of a fingerprint.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=repo_path or None,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def collect_linter_findings(
    diff_text: str, repo_path: str | None = None
) -> list[NormalizedFinding]:
    """Everything the linter can see in this diff, as structured findings.

    Rules, secret ruleset and the SAST bridges that happen to be installed: the
    same call `gitpr --linter` makes, so what the baseline records is exactly
    what the next lint run will classify.
    """
    from src.linter_engine import lint_findings

    return lint_findings(diff_text, repo_path=repo_path or ".")


def ai_findings_from_record(record: Any) -> tuple[list[NormalizedFinding], list[str]]:
    """The `findings` array of a review response, as findings, plus the complaints.

    The array is optional in the envelope, so a review that came back as prose
    alone yields nothing and says nothing: skipping it is the designed reading,
    not a failure. An entry that *is* there and is malformed is reported by
    index — the team loses one finding, never the whole baseline, and never in
    silence.

    No digest is taken for these findings. The model reports a location in the
    file it read, and the review flow has no parsed line index to look the text
    up in; a digest invented here is one the next run could not reproduce. They
    are low-confidence for the same reason their identity rests on the category:
    nothing about an AI finding is as stable as a rule's name.
    """
    if not isinstance(record, dict):
        return [], []
    response = record.get("response") or {}
    if not isinstance(response, dict) or "findings" not in response:
        return [], []
    raw = response.get("findings")
    if not isinstance(raw, list):
        return [], [__("The review's 'findings' is not a list and was ignored.")]

    findings: list[NormalizedFinding] = []
    warnings: list[str] = []
    for index, item in enumerate(raw):
        finding, problem = _ai_finding(item, index)
        if finding is None:
            warnings.append(problem)
            continue
        findings.append(finding)
    return findings, warnings


def create_baseline(
    *,
    refresh: bool = False,
    base: str | None = None,
    repo_path: str | None = None,
    configured_path: str | None = None,
    quiet: bool = True,
    today: date | None = None,
) -> BaselineRun:
    """Records the findings of the current diff as the baseline.

    Over an existing file this *replaces* the record rather than moving it: that
    is what makes `create` the way to start over, and why the caller confirms it
    first. The previous file is still read, for two reasons — the date the
    baseline was first written, and the count of decisions about to be dropped,
    which the run reports as a warning instead of letting them disappear.

    *repo_path* is the tree the diff and the linter are read from;
    *configured_path* is `GITPR_BASELINE_PATH` and names the file itself. The
    two are separate because a repository can keep its baseline outside the tree
    it describes, and `load_baseline` already reads the configured path — a
    command that wrote the default one would hand the gate a file nobody edits.
    """
    diff_text = current_diff(base, quiet=quiet)
    if not diff_text.strip():
        raise BaselineError(
            __(
                "There is no diff to record — make some changes, or point --base at "
                "the branch this work is compared against."
            )
        )

    findings = collect_linter_findings(diff_text, repo_path)
    ai_findings, warnings = _ai_review_findings(diff_text, refresh, repo_path)
    findings.extend(ai_findings)

    previously, problems = read_manifest_raw(repo_path, configured_path)
    warnings.extend(problems)
    warnings.extend(_dropped_decisions(previously))

    manifest = build_manifest(
        findings,
        previous=previously,
        repo_path=repo_path,
        today=today,
        command=PROVENANCE_COMMAND_CREATE,
    )
    path = write_manifest(manifest, repo_path, configured_path)

    return BaselineRun(
        path=path,
        manifest=manifest,
        compared=classify_findings(findings, previously, repo_path=repo_path),
        warnings=warnings,
        created=previously is None,
        ai_findings=len(ai_findings),
    )


def update_baseline(
    *,
    recompute: bool = False,
    base: str | None = None,
    repo_path: str | None = None,
    configured_path: str | None = None,
    quiet: bool = True,
    today: date | None = None,
) -> BaselineRun:
    """Moves the baseline forward over the current diff.

    What it preserves is the point of the command: an entry seen again keeps the
    date it was first seen and the decision taken about it; an entry whose file
    the diff touched and whose finding is gone is stamped `resolved` once; an
    entry in a file the diff never touched is left alone, because a narrow diff
    is no evidence about a finding elsewhere.

    A divergent checksum stops it: the file was edited outside GitPR, so
    rewriting it would launder the edit into the record. *recompute=True* is the
    deliberate way past that — it reads the file anyway, re-fingerprints what a
    version bump had invalidated, and reports what it saw.

    An empty diff writes nothing. The one thing `update` would then change is a
    timestamp, and a command that dirties the record without recording anything
    is worse than one that says there was nothing to do.

    *repo_path* and *configured_path* split the tree from the file, as in
    `create_baseline` — and here it matters more: an update that read one file
    and wrote another would move forward a record nobody is judged against.
    """
    warnings: list[str] = []
    if recompute:
        previously, problems = read_manifest_raw(repo_path, configured_path)
        warnings.extend(problems)
    else:
        snapshot = read_baseline(repo_path, configured_path)
        if snapshot.exists and not snapshot.is_usable:
            raise BaselineError(
                __(
                    "The baseline on disk cannot be updated in place: {problem} Review "
                    "the file, then run 'gitpr baseline update --recompute' to accept "
                    "what is in it.",
                    problem=snapshot.first_problem(),
                ),
                path=snapshot.path,
            )
        previously = snapshot.manifest

    diff_text = current_diff(base, quiet=quiet)
    if not diff_text.strip():
        warnings.append(
            __("There is no diff to move the baseline over — nothing was written.")
        )
        return BaselineRun(
            path=read_baseline(repo_path, configured_path).path,
            manifest=previously or BaselineManifest(fingerprint_version=FINGERPRINT_VERSION),
            warnings=warnings,
            created=previously is None,
            written=False,
        )

    if previously is None:
        warnings.append(__("There was no baseline to update — this run created one."))

    findings = collect_linter_findings(diff_text, repo_path)
    ai_findings, ai_warnings = _ai_review_findings(diff_text, False, repo_path)
    findings.extend(ai_findings)
    warnings.extend(ai_warnings)

    reference = today or date.today()
    commit = current_commit(repo_path)
    entries = _entries_forward(
        previously.entries if previously else [],
        findings,
        touched_files=diff_files(diff_text),
        commit=commit,
        today=reference,
        repo_path=repo_path,
        recompute=recompute,
    )

    manifest = stamp_manifest(
        entries, previous=previously, command=PROVENANCE_COMMAND_UPDATE
    )
    path = write_manifest(manifest, repo_path, configured_path)

    return BaselineRun(
        path=path,
        manifest=manifest,
        compared=classify_findings(findings, previously, repo_path=repo_path),
        warnings=warnings,
        created=previously is None,
        ai_findings=len(ai_findings),
    )


def build_manifest(
    findings: Sequence[NormalizedFinding],
    *,
    previous: BaselineManifest | None = None,
    repo_path: str | None = None,
    today: date | None = None,
    command: str = PROVENANCE_COMMAND_CREATE,
) -> BaselineManifest:
    """A manifest that records exactly these findings, all of them `existing`."""
    reference = today or date.today()
    commit = current_commit(repo_path)
    entries = [
        _new_entry(
            finding, commit=commit, today=reference, repo_path=repo_path, command=command
        )
        for finding in findings
    ]
    return stamp_manifest(entries, previous=previous, command=command)


def stamp_manifest(
    entries: list[BaselineEntry],
    *,
    previous: BaselineManifest | None,
    command: str,
) -> BaselineManifest:
    """The manifest around a set of entries, stamped with who wrote it.

    Public because `baseline suppress`/`unsuppress` write the manifest too, and
    the stamping is the part they must not re-implement: a second definition of
    "who wrote this file" is how the two commands would start disagreeing about
    `created_at`, the policy tag or the version that produced the bytes.
    """
    from src.updater import __version__

    policy_name, policy_version = _active_policy()
    now = _now()
    return BaselineManifest(
        entries=entries,
        schema_version=SCHEMA_VERSION,
        fingerprint_version=FINGERPRINT_VERSION,
        policy_name=policy_name,
        policy_version=policy_version,
        gitpr_version=__version__,
        created_at=(previous.created_at if previous and previous.created_at else now),
        updated_at=now,
        checksum=None,
    )


def _new_entry(
    finding: NormalizedFinding,
    *,
    commit: str | None,
    today: date,
    repo_path: str | None,
    command: str,
    carried: BaselineEntry | None = None,
) -> BaselineEntry:
    """One entry for one finding, either fresh or carrying an older decision."""
    entry = BaselineEntry(
        fingerprint=compute_fingerprint(finding, repo_path),
        rule_id=finding.rule_id,
        category=finding.category,
        file_path=normalize_path(finding.file_path, repo_path),
        line_start=finding.line_start,
        line_end=finding.line_end,
        severity=finding.severity,
        source=finding.source,
        status=BaselineStatus.EXISTING,
        low_confidence=is_low_confidence(finding),
        first_seen_commit=commit,
        last_seen_commit=commit,
        first_seen_date=today.isoformat(),
        last_seen_date=today.isoformat(),
        provenance={
            "origin": PROVENANCE_ORIGIN,
            "command": command,
            "policy": policy_tag(),
        },
    )
    if carried is not None:
        _carry_decisions(entry, carried)
    return entry


def _carry_decisions(entry: BaselineEntry, carried: BaselineEntry) -> None:
    """Moves what a human decided onto a re-fingerprinted entry.

    Used only by `update --recompute`: the fingerprint changed because the
    algorithm did, so the finding is the same one and its suppression or its
    debt has to survive the migration. The dates travel; the location is the one
    this run reports, and the provenance is this command's, because this command
    is what wrote the entry that now exists.
    """
    entry.status = carried.status
    entry.first_seen_commit = carried.first_seen_commit or entry.first_seen_commit
    entry.first_seen_date = carried.first_seen_date or entry.first_seen_date
    entry.resolved_at = carried.resolved_at
    entry.suppressed = carried.suppressed
    entry.suppression_reason = carried.suppression_reason
    entry.suppression_scope = carried.suppression_scope
    entry.suppressed_by = carried.suppressed_by
    entry.suppressed_at = carried.suppressed_at
    entry.accepted_debt_owner = carried.accepted_debt_owner
    entry.accepted_debt_due_date = carried.accepted_debt_due_date
    entry.accepted_debt_reason = carried.accepted_debt_reason


def _entries_forward(
    previous: Sequence[BaselineEntry],
    findings: Sequence[NormalizedFinding],
    *,
    touched_files: Sequence[str],
    commit: str | None,
    today: date,
    repo_path: str | None,
    recompute: bool,
) -> list[BaselineEntry]:
    """The entries of the next baseline: the old ones moved on, the new ones added."""
    by_fingerprint = {
        compute_fingerprint(finding, repo_path): finding for finding in findings
    }
    # Only `--recompute` builds the location index, and that is the whole guard:
    # outside it, a finding is its fingerprint and nothing else, so no update can
    # quietly re-identify a finding behind the reader's back.
    by_location = (
        {_finding_location(finding, repo_path): finding for finding in findings}
        if recompute
        else {}
    )
    touched = {normalize_path(path, repo_path) for path in touched_files}
    entries: list[BaselineEntry] = []

    for entry in previous:
        finding = by_fingerprint.pop(entry.fingerprint, None)
        if finding is not None:
            _touch(entry, commit=commit, today=today)
            entries.append(entry)
            continue

        stale = by_location.get(_location(entry)) if recompute else None
        if stale is not None and entry.status is not BaselineStatus.RESOLVED:
            del by_location[_location(entry)]
            by_fingerprint.pop(compute_fingerprint(stale, repo_path), None)
            entries.append(
                _new_entry(
                    stale,
                    commit=commit,
                    today=today,
                    repo_path=repo_path,
                    command=PROVENANCE_COMMAND_UPDATE,
                    carried=entry,
                )
            )
            continue

        if entry.status is not BaselineStatus.RESOLVED and normalize_path(
            entry.file_path, repo_path
        ) in touched:
            _mark_resolved(entry, today=today)
        entries.append(entry)

    for finding in by_fingerprint.values():
        entries.append(
            _new_entry(
                finding,
                commit=commit,
                today=today,
                repo_path=repo_path,
                command=PROVENANCE_COMMAND_UPDATE,
            )
        )
    return entries


def _touch(entry: BaselineEntry, *, commit: str | None, today: date) -> None:
    """Records that the finding is still there, without touching its decisions."""
    entry.last_seen_commit = commit
    entry.last_seen_date = today.isoformat()
    entry.provenance = {
        "origin": PROVENANCE_ORIGIN,
        "command": PROVENANCE_COMMAND_UPDATE,
        "policy": policy_tag(),
    }
    if entry.status is BaselineStatus.RESOLVED:
        # The code came back: the entry is live again, and the resolution date
        # had its run — keeping it would date a finding that is back.
        entry.status = BaselineStatus.EXISTING
        entry.resolved_at = None


def _mark_resolved(entry: BaselineEntry, *, today: date) -> None:
    """Stamps a resolution once, and never moves the date afterwards."""
    entry.status = BaselineStatus.RESOLVED
    if not entry.resolved_at:
        entry.resolved_at = today.isoformat()
    entry.last_seen_date = today.isoformat()


def _location(entry: BaselineEntry) -> tuple:
    return (
        rule_identity(entry.rule_id, entry.category),
        normalize_path(entry.file_path),
        entry.line_start,
        entry.line_end,
        (entry.source or "").lower(),
    )


def _finding_location(finding: NormalizedFinding, repo_path: str | None) -> tuple:
    return (
        rule_identity(finding.rule_id, finding.category),
        normalize_path(finding.file_path, repo_path),
        finding.line_start,
        finding.line_end,
        (finding.source or "").lower(),
    )


def _ai_finding(item: Any, index: int) -> tuple[NormalizedFinding | None, str]:
    """One entry of the review's `findings` array, or the reason it was dropped."""
    where = __("Finding #{number} of the review", number=index + 1)
    if not isinstance(item, dict):
        return None, __("{where} is not an object and was ignored.", where=where)

    file_path = str(item.get("file_path") or "").strip()
    if not file_path:
        return None, __("{where} names no file and was ignored.", where=where)
    line_start = _positive_int(item.get("line_start"))
    if line_start is None:
        return None, __("{where} has no valid line and was ignored.", where=where)
    line_end = _positive_int(item.get("line_end")) or line_start
    message = str(item.get("message") or "").strip()
    if not message:
        return None, __("{where} has no message and was ignored.", where=where)

    severity = str(item.get("severity") or "warning").strip().lower()
    return (
        NormalizedFinding(
            severity="error" if severity == "error" else "warning",
            category=str(item.get("category") or "").strip().lower() or AI_DEFAULT_CATEGORY,
            file_path=file_path,
            line_start=line_start,
            line_end=max(line_start, line_end),
            message=message,
            source="ai",
            rule_id=None,
            snippet_hash=None,
        ),
        "",
    )


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _ai_review_findings(
    diff_text: str, refresh: bool, repo_path: str | None
) -> tuple[list[NormalizedFinding], list[str]]:
    """The AI findings for this diff, from the cache or from a fresh review.

    A cached review is used only when the diff it recorded is the diff in front
    of us: findings located by line number are worthless against another
    revision, and re-locating them would be guesswork. `refresh` is the way to
    spend one AI call instead.
    """
    if refresh:
        return _fresh_review_findings(diff_text)

    record = _last_review_record()
    if record is None:
        return [], []
    recorded = record.get("diff")
    if not isinstance(recorded, str) or recorded != diff_text:
        return [], [
            __(
                "The cached review was written over a different diff, so its findings "
                "were not used — run 'gitpr baseline create --refresh' to review the "
                "current one."
            )
        ]
    return ai_findings_from_record(record)


def _fresh_review_findings(
    diff_text: str,
) -> tuple[list[NormalizedFinding], list[str]]:
    """Asks the AI to review this diff, and keeps the findings it returned."""
    from src.config import get_ai_provider
    from src.core import generate_pr_content

    data = generate_pr_content(
        "review", "review", diff_text, get_ai_provider(), store_diff=True
    )
    if not data:
        return [], [__("The review returned nothing — the baseline has no AI findings.")]
    findings, warnings = ai_findings_from_record({"response": data})
    if not findings and not warnings:
        warnings.append(
            __(
                "The review came back as prose alone — this baseline records only "
                "what the linter found."
            )
        )
    return findings, warnings


def _last_review_record() -> dict[str, Any] | None:
    """The newest cached review for this repository and branch, if any."""
    from src.cache import resolve_last_review
    from src.core import get_current_branch, get_repo_name

    return resolve_last_review(get_repo_name(), get_current_branch())


def _dropped_decisions(previous: BaselineManifest | None) -> list[str]:
    """Names the decisions a `create` is about to drop, before it drops them."""
    if previous is None:
        return []
    decided = [
        entry for entry in previous.entries if entry.suppressed or entry.is_debt()
    ]
    if not decided:
        return []
    return [
        __(
            "The baseline being replaced carries {count} suppression(s) or accepted "
            "debt(s) — the new one records no reason for any finding. Use "
            "'gitpr baseline update' to keep them.",
            count=len(decided),
        )
    ]


def _active_policy() -> tuple[str | None, str | None]:
    """The pack in force, recorded in the manifest the way §7 asks for it."""
    from src.domain.policy import get_active_policy

    root = get_active_policy().root
    if root is None:
        return None, None
    return root.name, root.version


def policy_tag() -> str | None:
    """The `name@version` label, spelled the way the rest of the CLI spells it.

    Public for the same reason as `stamp_manifest`: it goes into the provenance
    of the entries this module writes *and* of the ones `baseline suppress`
    rewrites, and §7 asks for the active policy in both.
    """
    from src.domain.policy import get_active_policy

    return get_active_policy().policy_tag() or None


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
