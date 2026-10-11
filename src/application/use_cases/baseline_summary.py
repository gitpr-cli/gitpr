"""What the repository's record says about itself, as one JSON document.

`gitpr baseline show` is written for a person at a terminal: it filters, it
prints the decisions it found, and it exits non-zero when the file cannot be
applied. An IDE agent needs the same facts without any of that — and without the
run the CLI commands do around them: no linter, no AI call, no policy resolution
publishing process-wide state. This module is that reading, and it is read-only
in the strict sense: it opens the file, counts what is in it, and stops.

An unusable file is *reported*, never raised: "the baseline is there and the gate
would refuse it" is one of the answers this surface exists to give, and a tool
that failed instead would leave the agent without the difference between a
repository with no baseline and one whose baseline is broken.
"""

from typing import Any, Iterable

from src.config import get_baseline_settings
from src.domain.baseline import (
    AppliedSuppression,
    BaselineEntry,
    BaselineError,
    BaselineManifest,
    BaselineStatus,
    Overrides,
    overdue_decisions,
    status_of_entry,
)
from src.i18n import __
from src.infrastructure.baseline.local_baseline_repository import (
    BaselineSnapshot,
    read_baseline,
    overrides_path,
)

# How many rules the summary lists. The rest is in the file — a digest that
# listed every rule of a large legacy tree would be the file again.
TOP_RULES = 10


def baseline_summary(repo_path: str | None = None) -> dict[str, Any]:
    """The baseline as data: what is recorded, decided, and late.

    Never raises for anything the file itself can be: absence, a malformed
    document, a divergent checksum and an unreadable overrides layer each come
    back as `problems` with the rest of the answer beside them. `status` is
    "success" whenever the question was answerable, "error" only when the
    repository could not be read at all.
    """
    try:
        settings = get_baseline_settings()
        snapshot = read_baseline(
            repo_path,
            settings["path"] or None,
            require_checksum=settings["require_checksum_match"],
        )
        overrides, warnings = _layers(repo_path, settings["allow_local_overrides"])
    except BaselineError as error:
        return {"status": "error", "message": str(error)}

    problems = list(snapshot.problems)
    manifest = snapshot.manifest
    counts = _counts(manifest, overrides) if manifest else _empty_counts()

    if snapshot.exists and not snapshot.checksum_ok:
        # The file is applied when the guard is off, but the divergence is the
        # one thing the digest exists to report — so it is reported either way.
        warnings.append(
            __(
                "{path} does not match its own checksum.",
                path=snapshot.path,
            )
        )

    return {
        "status": "success",
        "path": snapshot.path,
        "exists": snapshot.exists,
        "usable": snapshot.is_usable,
        "enabled": settings["enabled"],
        "checksum": _checksum_state(snapshot),
        "settings": {
            "require_checksum_match": settings["require_checksum_match"],
            "allow_local_overrides": settings["allow_local_overrides"],
            "configured_path": settings["path"] or None,
        },
        "manifest": _header(manifest) if manifest else None,
        "counts": counts,
        "total": sum(counts.values()),
        "rules": _top_rules(manifest.entries if manifest else []),
        "decisions": _decisions(manifest.entries if manifest else [], overrides),
        "debt": _debt(manifest.entries if manifest else [], overrides),
        "problems": problems,
        "warnings": warnings,
        # The five names are the vocabulary the whole feature speaks, and one of
        # them is not a status a file can hold: said here, because a count of
        # zero for `new` would otherwise read as "this change added nothing".
        "counts_note": __(
            "'new' is never recorded in the file: it is the result of comparing a "
            "run's findings against the record, so it is always 0 here."
        ),
    }


def _layers(repo_path: str | None, allow_local: bool) -> tuple[Overrides, list[str]]:
    """The decisions that are not written on the entries, and what to say about them.

    The same two layers the classification reads — the repository's
    `.gitpr/baseline.overrides.yml` and the active Policy Pack's block, merged by
    the gate's own reader — because a decision the summary left out would make its
    counts disagree with the gate that enforces them. A malformed overrides file
    becomes a warning rather than an exception: the classification stops on it,
    and a reader asking for a summary is better served by the answer plus that
    fact than by a tool call that failed.
    """
    from src.application.use_cases.baseline_gate import override_layers

    try:
        return override_layers(repo_path, allow_local)
    except BaselineError as error:
        return Overrides(), [
            __("{path} could not be read: {error}", path=overrides_path(repo_path), error=error)
        ]


def _checksum_state(snapshot: BaselineSnapshot) -> str:
    """"absent", "ok" or "divergent" — never a bare boolean."""
    if not snapshot.exists:
        return "absent"
    return "ok" if snapshot.checksum_ok else "divergent"


def _header(manifest: BaselineManifest) -> dict[str, Any]:
    """The manifest's own header, without the entries."""
    return {
        "schema_version": manifest.schema_version,
        "fingerprint_version": manifest.fingerprint_version,
        "gitpr_version": manifest.gitpr_version,
        "policy_name": manifest.policy_name,
        "policy_version": manifest.policy_version,
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
        "entries": len(manifest.entries),
    }


def _empty_counts() -> dict[str, int]:
    """One zero per status, so the shape never depends on there being a file."""
    return {status.value: 0 for status in BaselineStatus}


def _counts(
    manifest: BaselineManifest, overrides: Overrides | None
) -> dict[str, int]:
    """One count per status, each entry read through the override layers."""
    counts = _empty_counts()
    for entry in manifest.entries:
        applied = status_of_entry(entry, overrides)
        status = applied.status if applied is not None else entry.status
        counts[status.value] += 1
    return counts


def _top_rules(entries: Iterable[BaselineEntry]) -> list[dict[str, Any]]:
    """The rules the record repeats most, biggest first.

    A rule with no id counts under its category — the same identity the
    fingerprint falls back to, so the list never merges two different rules and
    never splits one finding from the rule that produced it.
    """
    tally: dict[str, int] = {}
    for entry in entries:
        tally[entry.identity()] = tally.get(entry.identity(), 0) + 1
    ordered = sorted(tally.items(), key=lambda item: (-item[1], item[0]))
    return [{"rule_id": name, "count": count} for name, count in ordered[:TOP_RULES]]


def _decisions(
    entries: Iterable[BaselineEntry], overrides: Overrides | None
) -> dict[str, Any]:
    """Where the decisions live, and how wide they are.

    Counted by the layer that supplied the winning decision (`entry`, `local`,
    `policy:<name>`) and by scope, which is what a reader auditing a repository's
    posture looks at: a `rule` scope silences a class, a `finding` scope one line.
    """
    by_origin: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    suppressed = 0
    debt = 0
    for entry in entries:
        applied = status_of_entry(entry, overrides)
        if applied is None:
            continue
        if applied.status is BaselineStatus.ACCEPTED_DEBT:
            debt += 1
        elif applied.status is BaselineStatus.IGNORED:
            suppressed += 1
        else:
            continue
        by_origin[applied.origin] = by_origin.get(applied.origin, 0) + 1
        by_scope[applied.scope.value] = by_scope.get(applied.scope.value, 0) + 1
    return {
        "suppressed": suppressed,
        "accepted_debt": debt,
        "by_origin": by_origin,
        "by_scope": by_scope,
    }


def _debt(
    entries: Iterable[BaselineEntry], overrides: Overrides | None
) -> dict[str, Any]:
    """The debt someone owns, and the part of it that is late.

    Read through the override layers like everything else here: a deadline a
    Policy Pack declared is as real as the one written on the entry, and a
    summary that only checked the file would report a repository as being on
    schedule while the gate printed the opposite.
    """
    live = _live_debt(entries, overrides)
    late = overdue_decisions([entry for entry, _applied in live], overrides)
    return {
        "total": len(live),
        "undated": sum(1 for _entry, applied in live if not applied.due_date),
        "overdue": [_debt_line(entry, applied) for entry, applied in late],
    }


def _live_debt(
    entries: Iterable[BaselineEntry], overrides: Overrides | None
) -> list[tuple[BaselineEntry, AppliedSuppression]]:
    """Every entry whose winning decision is accepted debt, and that decision.

    A resolved entry is left out whatever it carries: the finding is gone from a
    file the diff touched, so there is nothing left to owe.
    """
    live: list[tuple[BaselineEntry, AppliedSuppression]] = []
    for entry in entries:
        if entry.status is BaselineStatus.RESOLVED:
            continue
        applied = status_of_entry(entry, overrides)
        if applied is not None and applied.status is BaselineStatus.ACCEPTED_DEBT:
            live.append((entry, applied))
    return live


def _debt_line(entry: BaselineEntry, applied: AppliedSuppression) -> dict[str, Any]:
    """One late debt: who owes it, when it was due, and where the finding is."""
    return {
        "fingerprint": entry.fingerprint,
        "rule_id": entry.identity(),
        "file_path": entry.file_path,
        "line_start": entry.line_start,
        "owner": applied.owner,
        "due_date": applied.due_date,
        "reason": applied.reason,
        "origin": applied.origin,
    }
