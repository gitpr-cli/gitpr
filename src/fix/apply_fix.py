"""Turning a review into patches a human reads before they touch the tree.

``gitpr fix`` is one pipeline, and this module owns all of it:

1. **Resolve the review** — the most recent cached ``review``/``fullreview``
   record for this repository and branch (``cache.resolve_last_review``).
2. **Re-derive the diff** — with the very function that produced the review, so
   the patches are written against the tree in front of the user now instead of
   the tree of the day the review ran.
3. **Ask the AI for findings** — ONE call, cached under ``fix/`` like every
   other AI call in the project, returning one structured finding per issue the
   review raised, each carrying its own unified diff.
4. **Validate and classify** — ``git apply --check`` first, then the
   deterministic safety classifier. Nothing is applied without passing both.

The call goes straight to ``call_ai_model`` — never through
``core.generate_pr_content``. That function's dispatch ends in an ``else`` that
is the *PR* branch, so an unknown action type would silently return
``{"commit_message", "pr_description"}`` instead of an error.

Reading and writing are separate on purpose: ``collect_candidates`` touches no
file (only the prompt cache), and ``apply_candidates`` — the one function here
that can write — defaults to a dry run.
"""
from datetime import datetime

import click

from src.ai_providers import call_ai_model
from src.cache import get_cached_response, resolve_last_review, save_cached_response
from src.config import get_ai_provider, get_api_key, get_api_model
from src.diff_parser import summarize_patch
from src.fix.fix_history import TIMESTAMP_FORMAT, append_entry, make_entry
from src.fix.patch_applier import (
    apply_patch,
    check_patch,
    create_branch,
    modified_files,
    repo_root,
)
from src.fix.patch_extractor import extract_unified_diff
from src.fix.patch_provenance import (
    ApplyFixResult,
    FindingRef,
    PatchCandidate,
    PatchProvenance,
    PatchSafety,
)
from src.fix.patch_safety_classifier import classify_patch
from src.i18n import __
from src.updater import __version__

#: Cache folder of the findings call — one folder per command, as everywhere
#: else in the project (~/.gitpr/cache/prompts/fix/<md5>.json).
FIX_ACTION = "fix"

#: Bump when the findings prompt below changes. The MD5 cache already keys on
#: the prompt text, so this is not what invalidates a cached answer — it is what
#: tells a later reader which prompt produced a patch recorded in the history.
PROMPT_VERSION = "1"

#: The envelope the prompt asks for. Kept as one literal so the shape the model
#: is shown and the shape the parser expects can never drift apart.
FINDINGS_JSON = (
    '{"findings": [{"file_path": "path/as/in/the/diff", "line_start": 0, '
    '"line_end": 0, "severity": "...", "category": "...", "message": "...", '
    '"confidence": "high", "diff": "--- a/path\\n+++ b/path\\n@@ ...", '
    '"suggested_test": "..."}]}'
)


class FixError(Exception):
    """The pipeline cannot run — no review, no changes, no key, no repository.

    Raised for the situations where carrying on would produce a *meaningless*
    answer rather than a failure: with no cached review there are no findings
    to look at, and with a clean working tree there is nothing to patch.
    ``rollback_fix`` raises it too, so the command catches a single type.
    """


def resolve_review():
    """The most recent cached review of the current repository and branch.

    Errors instead of returning None: "there is no review" and "the review
    found nothing" must never look alike, and the message has to name the
    command that produces the missing half.
    """
    from src.core import get_current_branch, get_repo_name

    repo_name = get_repo_name()
    branch_name = get_current_branch()
    record = resolve_last_review(repo_name, branch_name)
    if not record:
        raise FixError(
            __(
                "❌ No review found for {repo} on branch '{branch}'. Run 'gitpr -r' first.",
                repo=repo_name,
                branch=branch_name,
            )
        )
    return record


def review_text(record):
    """The review prose out of a cache record."""
    return (record.get("response") or {}).get("review") or ""


def reviewed_diff(record, quiet=False):
    """The diff the review ran on: the recorded one, else re-derive it.

    Records written since the diff started being stored carry it outright, and
    that is always the better answer — a review fetched from a pull request has
    no local tree that could reproduce it.

    Older records have no such field, so the diff is re-derived: a ``review``
    reads ``git diff HEAD`` and a ``fullreview`` reads the branch against the
    remote base, with the recorded ``action_type`` selecting between them. That
    is a reconstruction of the revision the reviewer saw, not the revision
    itself, which is why storing it was worth doing.
    """
    recorded = record.get("diff")
    if recorded:
        return recorded

    from src.core import get_git_diff, get_git_full_diff

    if record.get("action_type") == "fullreview":
        return get_git_full_diff() or ""
    return get_git_diff(quiet=quiet) or ""


def findings_prompt(review, diff):
    """The pipeline's single prompt: review plus current diff in, findings out."""
    return (
        __(
            "Below is a code review of this branch, followed by the current diff. "
            "For each problem the review raises, write the smallest unified diff that fixes it "
            "in the code as it is now: use the exact paths, and include the context lines the "
            "patch needs in order to apply. Generate ONLY a JSON object in the format {json_format}:\n",
            json_format=FINDINGS_JSON,
        )
        + "\n"
        + __("=== CODE REVIEW ===")
        + f"\n{review}\n\n"
        + __("=== CURRENT DIFF ===")
        + f"\n{diff}"
    )


def collect_candidates(
    record,
    root=None,
    provider=None,
    quiet=False,
    max_lines_changed=5,
    excluded_paths=(),
):
    """Every finding of *record* that gitpr could turn into a patch, classified.

    Reads and validates; writes nothing — ``git apply --check`` leaves no trace
    and the AI call only touches the prompt cache. ``root`` is resolved once and
    used for everything below it: a unified diff carries paths relative to the
    repository top level, so checking it from a subdirectory would look for
    files that are not there. It must be the repository the process runs in,
    because that is where ``get_git_diff`` reads the diff from.

    A finding the model answered without a usable patch still becomes a
    candidate, classified ``EXPERIMENTAL`` with an empty diff: dropping it would
    hide an issue the review raised, and the empty diff is the truth — git
    refuses it, so it can never be applied by accident.
    """
    root = _require_repository(root)

    diff_text = reviewed_diff(record, quiet=quiet)
    if not diff_text.strip():
        raise FixError(
            __(
                "❌ The working tree has no changes to apply fixes to. Make the changes and run 'gitpr -r' again."
            )
        )

    provider = provider or get_ai_provider()
    api_key = get_api_key(provider)
    if not api_key:
        raise FixError(
            __(
                "❌ No API key configured for {provider}. Generate one with --install.",
                provider=provider,
            )
        )
    api_model = get_api_model(provider, task_complexity="advanced")

    payload = _findings(
        review_text(record), diff_text, provider, api_key, api_model, quiet=quiet
    )
    generated_at = datetime.now().strftime(TIMESTAMP_FORMAT)

    return tuple(
        _candidate(
            raw,
            finding_id=f"FIX-{index:03d}",
            root=root,
            provider=provider,
            api_model=api_model,
            generated_at=generated_at,
            max_lines_changed=max_lines_changed,
            excluded_paths=excluded_paths,
        )
        for index, raw in enumerate(_raw_findings(payload), start=1)
    )


def find_candidate(candidates, finding_id):
    """The candidate addressed by *finding_id*, or an error naming the ones there are.

    Listing what does exist is the difference between the user retrying with the
    right id and the user guessing at it.
    """
    wanted = str(finding_id or "").strip().upper()
    for candidate in candidates:
        if candidate.finding.id == wanted:
            return candidate

    available = ", ".join(candidate.finding.id for candidate in candidates) or __("none")
    raise FixError(
        __(
            "❌ Unknown finding '{finding_id}'. Available: {available}",
            finding_id=finding_id,
            available=available,
        )
    )


def select_safe(candidates):
    """The candidates ``--all-safe`` may batch-apply, in the order given.

    The single definition of "the safe ones" — the command and the MCP tool both
    read it from here, so neither can drift into using a different bar.
    """
    return tuple(
        candidate for candidate in candidates if candidate.safety is PatchSafety.SAFE
    )


def apply_candidates(candidates, root=None, dry_run=True, branch=None, quiet=False):
    """Run *candidates* through git, or report what running them would do.

    Returns one :class:`ApplyFixResult` per candidate, in the order given. The
    default is a dry run: it writes nothing at all and never creates a branch,
    reporting the diffs and classifications ``collect_candidates`` produced.

    ``branch`` is created once, before the first patch, and only on a real run.
    A branch that cannot be created aborts with :class:`FixError` — carrying on
    would apply the patches to the branch the user was trying to leave.

    A patch git refuses is reported as ``applied=False`` with git's own message
    in ``warnings``, and the batch continues: one candidate failing to apply
    says nothing about the next. Nothing is recorded in the history for it —
    the record exists to undo what was applied, and nothing was.
    """
    root = _require_repository(root)

    branch_created = None
    if not dry_run and branch:
        created, error = create_branch(branch, cwd=root)
        if not created:
            raise FixError(
                __(
                    "❌ Could not create branch '{branch}': {error}",
                    branch=branch,
                    error=error,
                )
            )
        branch_created = branch

    results = []
    for candidate in candidates:
        warnings = list(_dirty_warnings(candidate, root))

        if not dry_run:
            applied, error = apply_patch(candidate.diff_unified, cwd=root)
            if not applied:
                warnings.append(__("❌ git apply failed: {error}", error=error))
                results.append(_result(candidate, False, warnings, branch_created))
                continue
            append_entry(
                make_entry(
                    patch_id=candidate.patch_id,
                    finding=candidate.finding,
                    diff=candidate.diff_unified,
                    provenance=candidate.provenance,
                    files_changed=summarize_patch(candidate.diff_unified).files,
                    safety=candidate.safety,
                    branch=branch_created,
                ),
                root,
            )
            results.append(_result(candidate, True, warnings, branch_created))
            continue

        results.append(_result(candidate, False, warnings, branch_created))

    return tuple(results)


def _require_repository(root=None):
    """The repository top level, or a FixError when there is none.

    Everything below runs from that top level because the patches carry paths
    relative to it.
    """
    resolved = repo_root(cwd=root)
    if not resolved:
        raise FixError(__("❌ Not inside a git repository."))
    return resolved


def _system_instruction(quiet=False):
    """The fix persona: the user's ``.gitpr.fix.md`` when there is one."""
    from src.core import get_skill_context

    return get_skill_context("fix", quiet=quiet) or __(
        "You are a Senior Software Engineer. Turn each finding of a code review into the smallest unified diff that fixes it."
    )


def _findings(review, diff, provider, api_key, api_model, quiet=False):
    """The findings payload for this review and tree — from cache, or the AI.

    The cache is what makes ``FIX-001`` mean the same thing twice: the same
    review and the same diff build the same prompt, so the same answer comes
    back without a second call and the ids assigned to its findings stay put.
    """
    prompt = findings_prompt(review, diff)

    cached = get_cached_response(FIX_ACTION, prompt)
    if isinstance(cached, dict) and cached.get("findings"):
        _say(quiet, __("⚡ Fix candidates retrieved from local cache."), fg="green", dim=True)
        return cached

    response = call_ai_model(
        provider, api_key, api_model, prompt, _system_instruction(quiet), action=FIX_ACTION
    )
    if not response:
        raise FixError(
            __("❌ The AI did not return any fix candidates. Try again or check the provider.")
        )

    # A fresh dict, so the telemetry the transport attaches never reaches the
    # cache; prose instead of the envelope is stored as "no findings" rather
    # than raising — it is an ordinary answer, just an empty one.
    findings = response.get("findings") if isinstance(response, dict) else None
    payload = {"findings": findings if isinstance(findings, list) else []}
    save_cached_response(FIX_ACTION, FIX_ACTION, prompt, payload)
    return payload


def _raw_findings(payload):
    """The finding objects of a payload, however malformed it came back.

    Anything that is not the expected envelope yields ``[]``: the pipeline then
    reports "no candidates" instead of raising, because a model that answers
    with prose is an ordinary outcome rather than a crash.
    """
    if not isinstance(payload, dict):
        return []
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return []
    return [item for item in findings if isinstance(item, dict)]


def _candidate(
    raw,
    finding_id,
    root,
    provider,
    api_model,
    generated_at,
    max_lines_changed,
    excluded_paths,
):
    """One raw finding, validated and classified into a PatchCandidate."""
    diff = extract_unified_diff(str(raw.get("diff") or "")) or ""

    applies = False
    if diff:
        applies, _error = check_patch(diff, cwd=root)

    summary = summarize_patch(diff)
    safety, reason = classify_patch(
        summary,
        confidence=raw.get("confidence"),
        # An empty diff is not a patch that applies, so it never escapes the
        # EXPERIMENTAL class that keeps --all-safe away from it.
        applies_cleanly=bool(diff) and applies,
        max_lines_changed=max_lines_changed,
        excluded_paths=excluded_paths,
    )

    return PatchCandidate(
        finding=FindingRef(
            id=finding_id,
            # The patch is authoritative about where it applies; the model's
            # field is the fallback for a finding that has no patch at all.
            file_path=str(raw.get("file_path") or "").strip()
            or (summary.files[0] if summary.files else ""),
            line_start=_as_int(raw.get("line_start")),
            line_end=_as_int(raw.get("line_end")),
            severity=str(raw.get("severity") or "").strip().lower(),
            category=str(raw.get("category") or "").strip().lower(),
            message=str(raw.get("message") or "").strip(),
        ),
        diff_unified=diff,
        suggested_test=str(raw.get("suggested_test") or "").strip(),
        confidence=str(raw.get("confidence") or "").strip().lower(),
        safety=safety,
        safety_reason=reason,
        provenance=PatchProvenance(
            finding_id=finding_id,
            ai_provider=provider,
            ai_model=api_model,
            prompt_version=PROMPT_VERSION,
            generated_at=generated_at,
            gitpr_version=__version__,
        ),
    )


def _as_int(value):
    """*value* as an int, or 0 — a line number the model wrote as text."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _dirty_warnings(candidate, root):
    """Warn when a patch targets a file that is already modified (grill Q9).

    Only then: a patch writing into a file that already has uncommitted changes
    is the case where applying can surprise the user. Warning about every dirty
    file in the repository would fire on nearly every real run and stop meaning
    anything.
    """
    already_changed = set(modified_files(cwd=root))
    touched = [
        path
        for path in summarize_patch(candidate.diff_unified).files
        if path in already_changed
    ]
    if not touched:
        return ()
    return (
        __(
            "⚠️ These files already have uncommitted changes: {files}",
            files=", ".join(touched),
        ),
    )


def _result(candidate, applied, warnings, branch_created):
    """One ApplyFixResult for *candidate* (see ApplyFixResult's docstring)."""
    return ApplyFixResult(
        applied=applied,
        patch_id=candidate.patch_id,
        files_changed=summarize_patch(candidate.diff_unified).files,
        dry_run_diff=candidate.diff_unified,
        warnings=tuple(warnings),
        branch_created=branch_created,
    )


def _say(quiet, text, **kwargs):
    """Prints *text* unless the caller asked for silence (MCP, --quiet flows)."""
    if not quiet:
        click.secho(text, **kwargs)
