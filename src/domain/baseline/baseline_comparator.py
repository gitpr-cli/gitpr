"""Comparing what a run found against what the baseline already knew.

The comparison never changes the baseline — §5.9 of the spec is blunt about it:
the file moves only through `gitpr baseline create`/`update`, never as a side
effect of a review. Here a finding is read and classified, nothing more.

`is_blocking` is a property of the status alone. Severity is not consulted here
because it is not the comparison's business: `existing` never blocks, `new`
always does, and the caller combines that with the alert's own level — which is
how a `new` warning stays a warning and a `new` error keeps the pipeline red.
"""

from dataclasses import dataclass
from typing import Iterable, Sequence

from src.domain.baseline.baseline_fingerprint import (
    compute_fingerprint,
    normalize_path,
    rule_identity,
)
from src.domain.baseline.baseline_types import (
    SCOPE_PRECEDENCE,
    BaselineEntry,
    BaselineManifest,
    BaselineStatus,
    SuppressionScope,
)
from src.domain.baseline.suppression_policy import (
    AppliedSuppression,
    Overrides,
    apply_overrides,
    entry_debt,
    entry_suppression,
    match_debt,
    match_suppression,
)
from src.domain.finding.finding_types import NormalizedFinding
from src.i18n import __


@dataclass
class ComparedFinding:
    """One finding of this run, read against the baseline."""

    fingerprint: str
    identity: str
    current_severity: str
    baseline_status: BaselineStatus
    is_blocking: bool
    reason: str
    finding: NormalizedFinding
    entry: BaselineEntry | None = None
    applied: AppliedSuppression | None = None

    def is_error(self) -> bool:
        """Whether this finding is an error-level alert in this run."""
        return str(self.current_severity).lower() == "error"


def classify_findings(
    findings: Iterable[NormalizedFinding],
    manifest: BaselineManifest | None,
    overrides: Overrides | None = None,
    repo_path: str | None = None,
) -> list[ComparedFinding]:
    """Reads every finding of the run against the baseline and the layers.

    A finding whose entry was `resolved` and which is present again is `new`:
    the code came back, and saying `existing` would let a fixed problem return
    unnoticed. `baseline update` re-activates the entry on the next run.
    """
    layers = apply_overrides(overrides)
    compared: list[ComparedFinding] = []
    for finding in findings:
        fingerprint = compute_fingerprint(finding, repo_path)
        identity = rule_identity(finding.rule_id, finding.category)
        entry = manifest.entry_for(fingerprint) if manifest is not None else None

        if entry is not None and entry.status is BaselineStatus.RESOLVED:
            compared.append(
                _compared(
                    finding,
                    fingerprint,
                    identity,
                    BaselineStatus.NEW,
                    entry,
                    None,
                    _resolved_before(entry),
                )
            )
            continue

        applied = _apply_layers(entry, fingerprint, identity, finding, layers)
        if applied is not None:
            status = applied.status
            reason = applied.reason
        elif entry is not None:
            status = BaselineStatus.EXISTING
            reason = _known_since(entry)
        else:
            status = BaselineStatus.NEW
            reason = __("Not in the baseline yet.")

        compared.append(
            _compared(finding, fingerprint, identity, status, entry, applied, reason)
        )
    return compared


def status_counts(compared: Sequence[ComparedFinding]) -> dict[str, int]:
    """How many findings landed on each status.

    Every finding is counted, so the counts always add up to the number of
    findings — nothing may disappear between the run and the report.
    """
    counts = {status.value: 0 for status in BaselineStatus}
    for item in compared:
        counts[item.baseline_status.value] += 1
    return counts


def entries_resolved_by(
    entries: Iterable[BaselineEntry],
    touched_files: Iterable[str],
    seen_fingerprints: Iterable[str],
) -> list[BaselineEntry]:
    """Entries the current diff proves gone.

    An entry is resolved only when its file is part of the diff and the finding
    is not there any more. An entry in a file the diff never touched keeps its
    status: a narrow diff is not evidence that a finding elsewhere was fixed.
    """
    touched = {normalize_path(path) for path in touched_files}
    seen = set(seen_fingerprints)
    resolved: list[BaselineEntry] = []
    for entry in entries:
        if entry.fingerprint in seen:
            continue
        if normalize_path(entry.file_path) in touched:
            resolved.append(entry)
    return resolved


def _apply_layers(
    entry: BaselineEntry | None,
    fingerprint: str,
    identity: str,
    finding: NormalizedFinding,
    layers: Overrides,
) -> AppliedSuppression | None:
    """The winning decision among the entry and the declarative layers."""
    candidates: list[tuple[int, int, AppliedSuppression]] = []

    if entry is not None:
        stored = entry_suppression(entry)
        if stored is not None:
            candidates.append(
                (
                    _specificity(stored.scope),
                    0,
                    AppliedSuppression(
                        status=BaselineStatus.IGNORED,
                        reason=stored.reason,
                        scope=stored.scope,
                        origin=stored.origin,
                    ),
                )
            )
        debt = entry_debt(entry)
        if debt is not None:
            candidates.append(
                (
                    _specificity(SuppressionScope.FINDING),
                    0,
                    AppliedSuppression(
                        status=BaselineStatus.ACCEPTED_DEBT,
                        reason=debt.reason,
                        scope=SuppressionScope.FINDING,
                        origin=debt.origin,
                        owner=debt.owner,
                        due_date=debt.due_date,
                    ),
                )
            )

    matched = match_suppression(
        layers.suppressions,
        fingerprint=fingerprint,
        identity=identity,
        file_path=finding.file_path,
        line_start=finding.line_start,
        line_end=finding.line_end,
    )
    if matched is not None:
        candidates.append(
            (
                _specificity(matched.scope),
                1,
                AppliedSuppression(
                    status=BaselineStatus.IGNORED,
                    reason=matched.reason,
                    scope=matched.scope,
                    origin=matched.origin,
                ),
            )
        )

    matched_debt = match_debt(layers.accepted_debt, fingerprint=fingerprint)
    if matched_debt is not None:
        candidates.append(
            (
                _specificity(SuppressionScope.FINDING),
                1,
                AppliedSuppression(
                    status=BaselineStatus.ACCEPTED_DEBT,
                    reason=matched_debt.reason,
                    scope=SuppressionScope.FINDING,
                    origin=matched_debt.origin,
                    owner=matched_debt.owner,
                    due_date=matched_debt.due_date,
                ),
            )
        )

    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def _compared(
    finding: NormalizedFinding,
    fingerprint: str,
    identity: str,
    status: BaselineStatus,
    entry: BaselineEntry | None,
    applied: AppliedSuppression | None,
    reason: str,
) -> ComparedFinding:
    return ComparedFinding(
        fingerprint=fingerprint,
        identity=identity,
        current_severity=finding.severity,
        baseline_status=status,
        is_blocking=status is BaselineStatus.NEW,
        reason=reason,
        finding=finding,
        entry=entry,
        applied=applied,
    )


def _specificity(scope: SuppressionScope) -> int:
    return SCOPE_PRECEDENCE.index(scope)


def _resolved_before(entry: BaselineEntry) -> str:
    if entry.resolved_at:
        return __(
            "Was resolved on {date} and is back — a regression is new work.",
            date=entry.resolved_at,
        )
    return __("Was resolved in the baseline and is back — a regression is new work.")


def _known_since(entry: BaselineEntry) -> str:
    if entry.first_seen_date:
        return __("In the baseline since {date}.", date=entry.first_seen_date)
    return __("In the baseline.")
