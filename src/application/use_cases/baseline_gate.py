"""The only place the pipeline asks about the baseline.

Everything the review, the linter and the risk path need from
``.gitpr/baseline.json`` is answered here: whether there is a baseline at all,
what it says about each finding of this run, how an alert is annotated with that
answer, and how a finding that does not count is rendered as evidence.

Two rules hold the "nothing changes without a file" promise, and they are
structural rather than a discipline each call site has to remember:

- ``load_baseline(required=False)`` — every flow that does not *enforce* the
  baseline — reads nothing from disk. No file, no comparison, not one byte of
  extra output;
- a flow that does enforce it and finds a file that cannot be applied stops
  instead of proceeding with a gate that answers for nothing. A tampered
  checksum, another fingerprint version, a newer schema: each of them changes
  what the classification would *mean*, so the run refuses and says why — which
  is also the exit code the spec's decision 6 asks for.

The status vocabulary stays as the enum declares it — ``new``, ``existing``,
``ignored``, ``accepted_debt``, ``resolved`` — in the report and in the counts
line. It is the same vocabulary the CLI filters with (``--status``) and the JSON
carries in ``details["status"]``, and the risk report already prints its levels
the same way. Only the prose around it is translated.
"""

import os
from dataclasses import dataclass, field
from typing import Sequence

from src.application.use_cases.compare_against_baseline import (
    compare_against_baseline,
)
from src.config import get_baseline_settings
from src.domain.baseline import (
    BaselineError,
    BaselineManifest,
    BaselineStatus,
    Overrides,
    apply_overrides,
    is_low_confidence,
    normalize_path,
    set_active_baseline,
)
from src.domain.baseline.baseline_comparator import ComparedFinding, status_counts
from src.domain.finding.finding_types import NormalizedFinding
from src.domain.linter.sast_finding_mapper import format_finding_message
from src.domain.risk.risk_types import RiskEvidence, RiskSignal
from src.i18n import __
from src.infrastructure.baseline.local_baseline_repository import (
    BaselineSnapshot,
    baseline_path,
    overrides_path,
    read_baseline,
    read_overrides,
)
from src.linter_engine import external_alert_message


@dataclass
class BaselineGate:
    """The baseline this run resolved, and the layers it is read with.

    `snapshot` is the file as the repository found it: `manifest` is the part
    that may be applied, and it is None both when there is no file and when the
    file was refused. In the second case `is_unusable` is true — and that is only
    reachable from a flow that enforced the baseline, because a flow that did not
    never read the file.
    """

    snapshot: BaselineSnapshot
    overrides: Overrides = field(default_factory=Overrides)
    warnings: list[str] = field(default_factory=list)

    @property
    def manifest(self) -> BaselineManifest | None:
        """The manifest to classify against, or None when there is none."""
        return self.snapshot.manifest

    @property
    def path(self) -> str:
        """Where the baseline was looked for."""
        return self.snapshot.path

    @property
    def is_active(self) -> bool:
        """Whether this run has a baseline to classify against."""
        return self.snapshot.manifest is not None

    @property
    def is_unusable(self) -> bool:
        """Whether a file is there and could not be applied."""
        return self.snapshot.exists and self.snapshot.manifest is None


def load_baseline(
    required: bool = False,
    repo_path: str | None = None,
    publish: bool = True,
) -> BaselineGate:
    """Resolves the baseline for this run.

    *required* is the flow saying it enforces the baseline: the linter, the
    review and the full review. A flow that does not pass it gets an inactive
    gate without a single read, so `-c`, the PR flows, blame, the issue flows and
    the rest of the CLI are untouched by this feature's existence.

    *repo_path* is the working tree the file is looked for in, and *publish*
    installs the manifest as the process-wide baseline (`publish=False` is the
    MCP server, whose stdout is the JSON-RPC stream and where a stray print of a
    warning would corrupt the session — the gate itself never prints).

    Raises `BaselineError` when the flow enforces the baseline and the file
    cannot be applied, or when `baseline.overrides.yml` is malformed: a decision
    a human wrote is never dropped in silence.
    """
    settings = get_baseline_settings()
    configured_path = settings["path"] or None

    if not required or not settings["enabled"]:
        gate = BaselineGate(
            snapshot=BaselineSnapshot(path=baseline_path(repo_path, configured_path))
        )
        if publish:
            set_active_baseline(None)
        return gate

    snapshot = read_baseline(
        repo_path,
        configured_path,
        require_checksum=settings["require_checksum_match"],
    )
    overrides, warnings = override_layers(repo_path, settings["allow_local_overrides"])
    gate = BaselineGate(snapshot=snapshot, overrides=overrides, warnings=warnings)

    if not snapshot.checksum_ok and snapshot.exists and snapshot.manifest is not None:
        # The guard was turned off, so the file is applied — but the divergence
        # is not hidden: it is exactly the signal the digest exists to raise.
        gate.warnings.append(
            __(
                "{path} does not match its own checksum and was applied anyway "
                "because GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH is off.",
                path=snapshot.path,
            )
        )

    if gate.is_unusable:
        raise BaselineError(_unusable_message(snapshot), path=snapshot.path)

    if publish:
        set_active_baseline(snapshot.manifest)
    return gate


def classify_findings_for_gate(
    findings: Sequence[NormalizedFinding],
    gate: BaselineGate,
    repo_path: str | None = None,
) -> list[ComparedFinding]:
    """This run's findings, read against the baseline the gate resolved.

    An inactive gate raises rather than classifying: a run with no baseline has
    no comparison, and handing back a list in which everything is `new` would
    put a verdict in the report that nothing in the repository supports.
    """
    if gate.manifest is None:
        raise BaselineError(
            __("No baseline is loaded for this run — there is nothing to compare against.")
        )
    return compare_against_baseline(
        findings, gate.manifest, overrides=gate.overrides, repo_path=repo_path
    )


def new_findings(compared: Sequence[ComparedFinding]) -> list[NormalizedFinding]:
    """The findings that count against this change: the new ones.

    Everything else the run found is known work, a decision, or a decision with
    an owner — none of it is this change's debt, which is why the risk engine is
    handed this list and not the whole run. The findings left out are not
    dropped from the report: they come back as `informational_evidence`.
    """
    return [item.finding for item in compared if item.is_blocking]


def blocking_errors(compared: Sequence[ComparedFinding]) -> list[ComparedFinding]:
    """The findings that keep a blocking flow red: new, and an error.

    `is_blocking` is the status alone, so a new *warning* is not here — the
    linter's exit code has always followed the alert's level, and a legacy
    repository that baselined its errors still gets its warnings.
    """
    return [item for item in compared if item.is_blocking and item.is_error()]


# The counts in the order the line reads: what this change added, then what the
# repository already had, then the decisions and the ones that are gone.
_STATUS_LINE_ORDER = (
    BaselineStatus.NEW,
    BaselineStatus.EXISTING,
    BaselineStatus.RESOLVED,
    BaselineStatus.IGNORED,
    BaselineStatus.ACCEPTED_DEBT,
)


def status_line(compared: Sequence[ComparedFinding] | dict[str, int]) -> str:
    """The one-line summary of a classification, or "" when there is nothing to say.

    Accepts the counts (`status_counts`) or the list they came from, so a caller
    that has already classified does not classify twice to print a line. The
    order is the one a reader wants first: what the change did, then what the
    repository already knew.
    """
    counts = (
        compared if isinstance(compared, dict) else status_counts(compared)
    )
    parts = [
        f"{counts.get(status.value, 0)} {status.value}"
        for status in _STATUS_LINE_ORDER
        if counts.get(status.value)
    ]
    if not parts:
        return ""
    return __("Baseline: {counts}", counts=", ".join(parts))


def alert_for(finding: NormalizedFinding) -> str:
    """The alert line a finding was rendered as, or "" when it renders to none.

    The linter's own findings carry their alert as their message; a bridge
    finding's alert is a decorated rendering, so it is rebuilt with the very
    function that wrote it. A finding whose source is neither is formatted
    generically — the SAST bridges render every finding the same way, so this is
    exact for them rather than a guess.
    """
    source = (finding.source or "").strip().lower()
    if source == "linter":
        return finding.message or ""
    if source == "external":
        return external_alert_message(
            finding.rule_id or "External linter",
            finding.message,
            finding.file_path,
            finding.line_start,
        )
    return format_finding_message(finding)


def alert_status_index(
    compared: Sequence[ComparedFinding],
) -> dict[str, BaselineStatus]:
    """Which status each alert line of this run carries.

    Keyed by the rendered line because that is what the report, the console and
    the TUI all read. Two findings can render the same line — the same rule on
    two lines of one file, when the rule's message carries no line number — and
    then one of the two statuses has to win: `new` does, because hiding a new
    alert behind an older one is the only mistake here that loses information a
    reviewer needed.
    """
    index: dict[str, BaselineStatus] = {}
    for item in compared:
        alert = alert_for(item.finding)
        if not alert:
            continue
        previous = index.get(alert)
        if previous is None or item.baseline_status is BaselineStatus.NEW:
            index[alert] = item.baseline_status
    return index


def annotate_alerts(
    alerts: dict[str, list[str]], index: dict[str, BaselineStatus]
) -> dict[str, list[str]]:
    """The same alerts, each finding's status written in front of it.

    A copy: the alert lists are what the exit code, the metric and the report are
    counted from, and this only changes how they read. A line the index does not
    know — a tool warning, which is not a finding — is left exactly as it was.
    """
    annotated = {}
    for level in ("errors", "warnings"):
        annotated[level] = [
            f"[{index[alert].value}] {alert}" if alert in index else alert
            for alert in alerts.get(level, [])
        ]
    return annotated


def informational_evidence(item: ComparedFinding) -> RiskEvidence:
    """A finding the baseline already knew about, as zero-weight evidence.

    Zero points on purpose: the status is the answer to "does this count against
    the change?", and a finding that does not count must not move the score. It
    still appears in the breakdown, with the status and the reason the decision
    was made, so the report says "this is legacy" instead of going quiet about it.
    """
    status = item.baseline_status.value
    applied = item.applied
    return RiskEvidence(
        signal=RiskSignal.BASELINE_FINDING,
        points=0.0,
        summary=f"[{status}] {(item.finding.message or '')[:80]}",
        details={
            "status": status,
            "rule_id": item.finding.rule_id,
            "source": item.finding.source,
            "file_path": item.finding.file_path,
            "line_start": item.finding.line_start,
            "reason": item.reason,
            "scope": applied.scope.value if applied else None,
            "origin": applied.origin if applied else None,
            "owner": applied.owner if applied else None,
            "due_date": applied.due_date if applied else None,
        },
        confidence="low" if is_low_confidence(item.finding) else "high",
    )


def attach_informational_evidence(
    risk, compared: Sequence[ComparedFinding]
) -> int:
    """Writes the findings that did not count onto the risk result's own files.

    Nothing is scored here, and nothing may be: these findings are worth zero by
    definition. What the attachment buys is a report that can still say *why* a
    finding it saw carries no weight — its status, the reason, the owner, the
    deadline — instead of reading like a run that never found it at all.

    The evidence lands on the file it belongs to, matched the way the risk
    calculator matches findings to patches, and the count is returned so the
    caller can say how many were marked. A compared finding that *is* blocking
    is skipped: it already scored, and a 0-point copy next to it would read as
    a contradiction.
    """
    pending: dict[str, list[ComparedFinding]] = {}
    for item in compared:
        if item.is_blocking:
            continue
        pending.setdefault(normalize_path(item.finding.file_path), []).append(item)
    if not pending:
        return 0

    attached = 0
    for file_risk in getattr(risk, "files", None) or []:
        for item in pending.get(normalize_path(file_risk.file_path), []):
            file_risk.evidence.append(informational_evidence(item))
            attached += 1
    return attached


def pack_layers() -> Overrides | None:
    """The ``baseline:`` block of the active policy pack, or None when there is none.

    Read from the policy this process already resolved, and never from disk: the
    block is the pack's opinion about findings, not the repository's record of
    them, and nothing here may write it anywhere.
    """
    from src.domain.policy import get_active_policy

    pack = get_active_policy().baseline_overrides
    return None if pack is None or pack.is_empty() else pack


def override_layers(
    repo_path: str | None = None, allow_local: bool | None = None
) -> tuple[Overrides, list[str]]:
    """Every declarative layer in force, and anything to say about them.

    The repository's own file first, then the pack's block — the order the
    classification prefers, and the same merge for the gate, `baseline show` and
    `unsuppress`, so none of them can disagree about what silences a finding.
    """
    allowed = (
        get_baseline_settings()["allow_local_overrides"]
        if allow_local is None
        else allow_local
    )
    local, warnings = _layers(repo_path, allowed)
    pack = pack_layers()
    if pack is None:
        return local, warnings
    return apply_overrides(local, pack=pack), warnings


def _layers(
    repo_path: str | None, allow_local: bool
) -> tuple[Overrides, list[str]]:
    """The declarative layer of this run, and anything to say about it."""
    target = overrides_path(repo_path)
    if not allow_local:
        if os.path.isfile(target):
            return Overrides(), [
                __(
                    "{path} is ignored because GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES is off.",
                    path=target,
                )
            ]
        return Overrides(), []

    overrides, _path = read_overrides(repo_path)
    return overrides, []


def _unusable_message(snapshot: BaselineSnapshot) -> str:
    """Why the run stopped, and the two ways forward."""
    problems = " ".join(snapshot.problems) or __("The file cannot be applied.")
    return __(
        "{path} cannot be applied, so the run stopped: {problems} "
        "Inspect it with 'gitpr baseline validate'; if it was edited by hand, "
        "'gitpr baseline update --recompute' rebuilds it from the working tree.",
        path=snapshot.path,
        problems=problems,
    )
