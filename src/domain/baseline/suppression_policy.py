"""Auditable suppressions and accepted debt, and the layers they arrive in.

A suppression is a decision, so it is never silent: every one of them carries a
non-empty reason, and the widest scopes carry the name of whoever wrote them and
the date. That is the whole point of the feature — the alternative, an inline
`# noqa` scattered through the tree, is a decision nobody can review, count or
expire.

Three layers feed the classification, from the narrowest statement to the
broadest: the entry stored in `.gitpr/baseline.json` (one finding, decided here),
`.gitpr/baseline.overrides.yml` (committed with the repository, so a teammate
reproduces it), and the active Policy Pack (shared between repositories, and
never written into the baseline — a pack's opinion is not the repository's
record). The most specific scope wins; among equally specific ones the narrower
layer does.

A scope reaches further than its own layer would suggest, and that is
deliberate: a `rule`-scope suppression also silences findings that have no entry
yet, which is exactly what "this rule is too noisy for a legacy tree" means.
"""

import fnmatch
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterable, Sequence

from src.domain.baseline.baseline_fingerprint import normalize_path
from src.domain.baseline.baseline_types import (
    SCOPE_PRECEDENCE,
    BaselineEntry,
    BaselineError,
    BaselineStatus,
    SuppressionScope,
)
from src.i18n import __

# Where a suppression came from. The baseline is the repository's own record, so
# it outranks the overrides file when two equally specific scopes match.
ORIGIN_ENTRY = "entry"
ORIGIN_LOCAL = "local"

_SUPPRESSION_KEYS = {
    "scope",
    "reason",
    "by",
    "date",
    "fingerprint",
    "rule_id",
    "file_path",
    "line_start",
    "line_end",
}
_DEBT_KEYS = {"fingerprint", "owner", "reason", "due_date"}
_OVERRIDES_KEYS = {"suppressions", "accepted_debt"}
_FINGERPRINT_LENGTH = 64


@dataclass
class Suppression:
    """One decision to stop reporting a finding, and why."""

    scope: SuppressionScope
    reason: str
    by: str | None = None
    date: str | None = None
    fingerprint: str | None = None
    rule_id: str | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    origin: str = ORIGIN_LOCAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope.value,
            "reason": self.reason,
            "by": self.by,
            "date": self.date,
            "fingerprint": self.fingerprint,
            "rule_id": self.rule_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }

    def matches(
        self,
        *,
        fingerprint: str,
        identity: str,
        file_path: str,
        line_start: int,
        line_end: int,
    ) -> bool:
        """Whether this suppression covers a finding.

        Every scope is matched against the finding's *rule identity* — the rule
        id when the source declares one, `category:<name>` otherwise — so a pack
        can silence the AI's prose findings by category without pretending they
        have a rule.
        """
        if self.scope is SuppressionScope.FINDING:
            return bool(self.fingerprint) and self.fingerprint == fingerprint
        if self.scope is SuppressionScope.RULE:
            return bool(self.rule_id) and self.rule_id == identity
        if self.scope is SuppressionScope.FILE:
            return (
                bool(self.rule_id)
                and self.rule_id == identity
                and _same_file(self.file_path, file_path)
            )
        if self.scope is SuppressionScope.LINE:
            # Containment, and the content hash is deliberately not consulted:
            # the point of a line scope is that editing the line does not undo
            # the decision — which is why it also demands a reason.
            return (
                bool(self.rule_id)
                and self.rule_id == identity
                and _same_file(self.file_path, file_path, glob=False)
                and self.line_start is not None
                and self.line_end is not None
                and self.line_start <= line_start
                and line_end <= self.line_end
            )
        return False


@dataclass
class AcceptedDebt:
    """A finding the team owns, with a deadline it should be gone by."""

    fingerprint: str
    owner: str
    reason: str
    due_date: str | None = None
    origin: str = ORIGIN_LOCAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "owner": self.owner,
            "reason": self.reason,
            "due_date": self.due_date,
        }


@dataclass
class Overrides:
    """The declarative layers, already validated: `.gitpr/baseline.overrides.yml`
    and the baseline block a Policy Pack may declare."""

    suppressions: list[Suppression] = field(default_factory=list)
    accepted_debt: list[AcceptedDebt] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.suppressions and not self.accepted_debt


@dataclass
class AppliedSuppression:
    """The winning decision for one finding, ready to be shown."""

    status: BaselineStatus
    reason: str
    scope: SuppressionScope
    origin: str
    owner: str | None = None
    due_date: str | None = None


def _same_file(candidate: str | None, file_path: str, glob: bool = True) -> bool:
    """Path comparison for a suppression: normalized on both sides.

    A `file` scope may be a glob (`app/Legacy/*`), the same idea the linter
    already has in `ignore_paths`; a `line` scope names one file.
    """
    if not candidate:
        return False
    pattern = normalize_path(candidate)
    path = normalize_path(file_path)
    if glob:
        return fnmatch.fnmatch(path, pattern)
    return pattern == path


def validate_suppression(raw: Any) -> Suppression:
    """Reads one suppression, refusing anything that would make it unauditable."""
    if not isinstance(raw, dict):
        raise BaselineError(__("Each suppression must be a mapping."))
    _check_unknown(raw, _SUPPRESSION_KEYS, "suppression")

    scope_raw = raw.get("scope")
    try:
        scope = SuppressionScope(str(scope_raw))
    except ValueError:
        raise BaselineError(
            __("Suppression scope must be one of: {scopes}.", scopes=_scope_list())
        )

    reason = str(raw.get("reason") or "").strip()
    if not reason:
        raise BaselineError(
            __("Every suppression needs a reason — that is what makes it auditable.")
        )

    suppression = Suppression(
        scope=scope,
        reason=reason,
        by=raw.get("by"),
        date=raw.get("date"),
        fingerprint=raw.get("fingerprint"),
        rule_id=raw.get("rule_id"),
        file_path=raw.get("file_path"),
        line_start=_optional_int(raw.get("line_start"), "line_start"),
        line_end=_optional_int(raw.get("line_end"), "line_end"),
    )
    _check_scope_fields(suppression)
    return suppression


def validate_debt(raw: Any) -> AcceptedDebt:
    """Reads one accepted debt, refusing one nobody owns."""
    if not isinstance(raw, dict):
        raise BaselineError(__("Each accepted debt must be a mapping."))
    _check_unknown(raw, _DEBT_KEYS, "accepted debt")

    owner = str(raw.get("owner") or "").strip()
    if not owner:
        raise BaselineError(
            __("Accepted debt needs an owner — a debt nobody owns is not accepted.")
        )
    reason = str(raw.get("reason") or "").strip()
    if not reason:
        raise BaselineError(__("Accepted debt needs a reason."))

    fingerprint = str(raw.get("fingerprint") or "").strip()
    if not fingerprint:
        raise BaselineError(
            __("Accepted debt needs the fingerprint of the finding it covers.")
        )
    _check_fingerprint(fingerprint)

    due_date = raw.get("due_date")
    if due_date is not None:
        due_date = str(due_date).strip() or None
        if due_date:
            _check_date(due_date, "due_date")

    return AcceptedDebt(
        fingerprint=fingerprint, owner=owner, reason=reason, due_date=due_date
    )


def parse_overrides(data: Any) -> Overrides:
    """Validates an overrides document into the layers the classification applies.

    The file may be written under a top-level ``overrides:`` key (as documented)
    or at the root; both are accepted, matching `policy.overrides.yml`.
    """
    if data is None:
        return Overrides()
    if not isinstance(data, dict):
        raise BaselineError(__("The overrides file must be a YAML mapping."))
    root = data.get("overrides", data)
    if not isinstance(root, dict):
        raise BaselineError(__("'overrides' must be a mapping."))
    _check_unknown(root, _OVERRIDES_KEYS, "the overrides file")

    parsed = Overrides(
        suppressions=[
            validate_suppression(item) for item in _as_list(root.get("suppressions"))
        ],
        accepted_debt=[
            validate_debt(item) for item in _as_list(root.get("accepted_debt"))
        ],
    )
    _reject_duplicates(parsed)
    return parsed


def apply_overrides(
    local: Overrides | None = None,
    *,
    pack: Overrides | None = None,
    pack_name: str | None = None,
    allow_local: bool = True,
) -> Overrides:
    """The layers as one list, local overrides first and the policy pack after.

    `allow_local=False` is the `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES=false` case:
    the repository's own overrides file is dropped and only the pack's opinion
    survives. The pack layer is always read from memory and is never written
    into the baseline.

    An entry of the pack layer that already names the pack it came from keeps
    that name, and `pack_name` only labels the ones that do not. A composed
    policy stamps each decision with its own pack, because a dependency's
    decision attributed to the root would be a false statement in the one
    surface that exists to attribute.
    """
    merged = Overrides()
    if local is not None and allow_local:
        merged.suppressions.extend(local.suppressions)
        merged.accepted_debt.extend(local.accepted_debt)
    if pack is not None:
        fallback = f"policy:{pack_name}" if pack_name else "policy"
        for suppression in pack.suppressions:
            origin = (
                suppression.origin if suppression.origin != ORIGIN_LOCAL else fallback
            )
            merged.suppressions.append(_reorigin_suppression(suppression, origin))
        for debt in pack.accepted_debt:
            origin = debt.origin if debt.origin != ORIGIN_LOCAL else fallback
            merged.accepted_debt.append(_reorigin_debt(debt, origin))
    return merged


def match_suppression(
    suppressions: Sequence[Suppression],
    *,
    fingerprint: str,
    identity: str,
    file_path: str,
    line_start: int,
    line_end: int,
) -> Suppression | None:
    """The most specific suppression covering the finding, or None.

    Ties go to the layer that came first — `apply_overrides` puts the
    repository's own overrides ahead of the pack's.
    """
    for scope in SCOPE_PRECEDENCE:
        for suppression in suppressions:
            if suppression.scope is not scope:
                continue
            if suppression.matches(
                fingerprint=fingerprint,
                identity=identity,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
            ):
                return suppression
    return None


def match_debt(
    debts: Sequence[AcceptedDebt], *, fingerprint: str
) -> AcceptedDebt | None:
    """The accepted debt covering this exact finding, or None."""
    for debt in debts:
        if debt.fingerprint == fingerprint:
            return debt
    return None


def entry_suppression(entry: BaselineEntry) -> Suppression | None:
    """The decision an entry already carries, as a suppression.

    `baseline suppress` records the status on the entry itself, so the reason
    survives in the file even when the override layers are gone.
    """
    if entry.status is not BaselineStatus.IGNORED and not entry.suppressed:
        return None
    scope = entry.suppression_scope or SuppressionScope.FINDING
    return Suppression(
        scope=scope,
        reason=entry.suppression_reason or "",
        by=entry.suppressed_by,
        date=entry.suppressed_at,
        fingerprint=entry.fingerprint,
        rule_id=entry.identity(),
        file_path=entry.file_path,
        line_start=entry.line_start,
        line_end=entry.line_end,
        origin=ORIGIN_ENTRY,
    )


def entry_debt(entry: BaselineEntry) -> AcceptedDebt | None:
    """The accepted debt an entry already carries, as an override does."""
    if not entry.is_debt():
        return None
    return AcceptedDebt(
        fingerprint=entry.fingerprint,
        owner=entry.accepted_debt_owner or "",
        reason=entry.accepted_debt_reason or "",
        due_date=entry.accepted_debt_due_date,
        origin=ORIGIN_ENTRY,
    )


def status_of_entry(
    entry: BaselineEntry,
    overrides: Overrides | None = None,
) -> AppliedSuppression | None:
    """What an entry's status reads as once the override layers are applied.

    Used by `show`, which has to display the same decision the gate would apply
    — a suppression that lives in an override is real even though the entry in
    the file says nothing about it.
    """
    layers = apply_overrides(overrides)
    candidates: list[tuple[int, int, AppliedSuppression]] = []

    stored = entry_suppression(entry)
    if stored is not None:
        candidates.append(
            _candidate(stored.scope, 0, BaselineStatus.IGNORED, stored.reason, stored.origin)
        )
    debt = entry_debt(entry)
    if debt is not None:
        candidates.append(
            _candidate(
                SuppressionScope.FINDING,
                0,
                BaselineStatus.ACCEPTED_DEBT,
                debt.reason,
                debt.origin,
                owner=debt.owner,
                due_date=debt.due_date,
            )
        )

    matched = match_suppression(
        layers.suppressions,
        fingerprint=entry.fingerprint,
        identity=entry.identity(),
        file_path=entry.file_path,
        line_start=entry.line_start,
        line_end=entry.line_end,
    )
    if matched is not None:
        candidates.append(
            _candidate(matched.scope, 1, BaselineStatus.IGNORED, matched.reason, matched.origin)
        )

    matched_debt = match_debt(layers.accepted_debt, fingerprint=entry.fingerprint)
    if matched_debt is not None:
        candidates.append(
            _candidate(
                SuppressionScope.FINDING,
                1,
                BaselineStatus.ACCEPTED_DEBT,
                matched_debt.reason,
                matched_debt.origin,
                owner=matched_debt.owner,
                due_date=matched_debt.due_date,
            )
        )

    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def overdue_decisions(
    entries: Iterable[BaselineEntry],
    overrides: Overrides | None = None,
    today: date | None = None,
) -> list[tuple[BaselineEntry, AppliedSuppression]]:
    """Every debt in force whose deadline has passed, with the winning decision.

    A deadline can be declared on the entry, in `.gitpr/baseline.overrides.yml`,
    or by a Policy Pack — and one that is only checked in the first of the three
    is not audited at all. The decision comes back with the entry because the
    owner and the date belong to the layer that won, not to the file: a pack's
    debt is owed by the pack's owner, and printing the entry's empty fields would
    say nobody owes it.

    A passed deadline is a warning, never a failure and never a silent
    disappearance: the finding stays accepted, and the caller says it is late.
    """
    reference = today or date.today()
    late: list[tuple[BaselineEntry, AppliedSuppression]] = []
    for entry in entries:
        if entry.status is BaselineStatus.RESOLVED:
            continue
        applied = status_of_entry(entry, overrides)
        if applied is None or applied.status is not BaselineStatus.ACCEPTED_DEBT:
            continue
        due = applied.due_date or entry.accepted_debt_due_date
        if not due:
            continue
        try:
            parsed = date.fromisoformat(str(due))
        except ValueError:
            continue
        if parsed < reference:
            late.append((entry, applied))
    return late


def overdue_debt(
    entries: Iterable[BaselineEntry], today: date | None = None
) -> list[BaselineEntry]:
    """Accepted debts whose deadline has passed, read from the entries alone.

    The reading for a caller that only holds the file. `overdue_decisions` is the
    one to reach for when the override layers are in hand — a deadline a pack
    declared is as real as the one written on the entry.
    """
    return [entry for entry, _ in overdue_decisions(entries, None, today)]


def _candidate(
    scope: SuppressionScope,
    layer: int,
    status: BaselineStatus,
    reason: str,
    origin: str,
    owner: str | None = None,
    due_date: str | None = None,
) -> tuple[int, int, AppliedSuppression]:
    return (
        SCOPE_PRECEDENCE.index(scope),
        layer,
        AppliedSuppression(
            status=status,
            reason=reason,
            scope=scope,
            origin=origin,
            owner=owner,
            due_date=due_date,
        ),
    )


def _reorigin_suppression(suppression: Suppression, origin: str) -> Suppression:
    return Suppression(
        scope=suppression.scope,
        reason=suppression.reason,
        by=suppression.by,
        date=suppression.date,
        fingerprint=suppression.fingerprint,
        rule_id=suppression.rule_id,
        file_path=suppression.file_path,
        line_start=suppression.line_start,
        line_end=suppression.line_end,
        origin=origin,
    )


def _reorigin_debt(debt: AcceptedDebt, origin: str) -> AcceptedDebt:
    return AcceptedDebt(
        fingerprint=debt.fingerprint,
        owner=debt.owner,
        reason=debt.reason,
        due_date=debt.due_date,
        origin=origin,
    )


def _check_scope_fields(suppression: Suppression) -> None:
    """Refuses a suppression that does not say what it reaches."""
    if suppression.scope is SuppressionScope.FINDING:
        if not suppression.fingerprint:
            raise BaselineError(
                __("A 'finding' suppression needs the fingerprint it covers.")
            )
        _check_fingerprint(suppression.fingerprint)
        return
    if not suppression.rule_id:
        raise BaselineError(
            __("A suppression at '{scope}' scope needs a rule_id.", scope=suppression.scope.value)
        )
    if suppression.scope is SuppressionScope.RULE:
        return
    if not suppression.file_path:
        raise BaselineError(
            __("A suppression at '{scope}' scope needs a file_path.", scope=suppression.scope.value)
        )
    if suppression.scope is SuppressionScope.LINE:
        if suppression.line_start is None or suppression.line_end is None:
            raise BaselineError(
                __("A 'line' suppression needs line_start and line_end.")
            )
        if suppression.line_start < 1 or suppression.line_end < suppression.line_start:
            raise BaselineError(
                __("The line range must be positive and end at or after it starts.")
            )


def _reject_duplicates(overrides: Overrides) -> None:
    """Two identical rules in one file is a copy-paste artifact, not a policy."""
    seen: set[str] = set()
    for suppression in overrides.suppressions:
        if suppression.scope is not SuppressionScope.FINDING:
            continue
        assert suppression.fingerprint is not None
        if suppression.fingerprint in seen:
            raise BaselineError(
                __("Fingerprint {fingerprint} is suppressed twice.", fingerprint=suppression.fingerprint)
            )
        seen.add(suppression.fingerprint)

    debts: set[str] = set()
    for debt in overrides.accepted_debt:
        if debt.fingerprint in debts:
            raise BaselineError(
                __("Fingerprint {fingerprint} has two accepted debts.", fingerprint=debt.fingerprint)
            )
        debts.add(debt.fingerprint)


def _check_fingerprint(fingerprint: str) -> None:
    body = fingerprint[len("sha256:"):] if fingerprint.startswith("sha256:") else fingerprint
    if len(body) != _FINGERPRINT_LENGTH or any(
        character not in "0123456789abcdef" for character in body
    ):
        raise BaselineError(
            __("{fingerprint} is not a fingerprint.", fingerprint=fingerprint)
        )


def _check_date(value: str, field_name: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError:
        # Named, because one document can carry two dates: when a suppression was
        # signed (`date`) and when a debt is due (`due_date`).
        raise BaselineError(
            __(
                "{field}: '{value}' is not a date (expected YYYY-MM-DD).",
                field=field_name,
                value=value,
            )
        )


def _check_unknown(data: dict, allowed: set[str], where: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise BaselineError(
            __(
                "Unknown key(s) in {where}: {keys}. GitPR ignores nothing in silence.",
                where=where,
                keys=", ".join(unknown),
            )
        )


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        raise BaselineError(__("Expected a list."))
    return value


def _optional_int(value: Any, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise BaselineError(__("'{value}' is not a number.", value=value))


def _scope_list() -> str:
    return ", ".join(scope.value for scope in SCOPE_PRECEDENCE)
