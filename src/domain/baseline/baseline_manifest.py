"""Reading, writing and validating `.gitpr/baseline.json`.

The file is committed, so two things matter beyond its content: an edit that
nobody reviewed has to be detectable, and two machines producing the same
baseline have to produce the same bytes. The first is the checksum, the second
is the canonical serialization — sorted keys, entries ordered by fingerprint.

The checksum cannot cover itself. It is computed over everything *except* the
`checksum` key, which is what makes it stable: write the file, then write the
digest of what you wrote.
"""

import json
from datetime import date
from typing import Any, Iterable

from src.domain.baseline.baseline_types import (
    PERSISTED_STATUSES,
    BaselineError,
    BaselineManifest,
    BaselineStatus,
    SuppressionScope,
)
from src.domain.policy.policy_checksum import checksum_bytes
from src.i18n import __

SCHEMA_VERSION = 1

_ROOT_KEYS = {
    "schema_version",
    "fingerprint_version",
    "policy_name",
    "policy_version",
    "gitpr_version",
    "created_at",
    "updated_at",
    "checksum",
    "entries",
}

_ENTRY_KEYS = {
    "fingerprint",
    "rule_id",
    "category",
    "file_path",
    "line_start",
    "line_end",
    "severity",
    "source",
    "status",
    "low_confidence",
    "first_seen_commit",
    "last_seen_commit",
    "first_seen_date",
    "last_seen_date",
    "resolved_at",
    "suppressed",
    "suppression_reason",
    "suppression_scope",
    "suppressed_by",
    "suppressed_at",
    "accepted_debt_owner",
    "accepted_debt_due_date",
    "accepted_debt_reason",
    "provenance",
}

_FINGERPRINT_LENGTH = 64
_PREFIX = "sha256:"


def canonical_json(data: Any) -> str:
    """The one serialization the checksum and the diff both use."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def manifest_checksum(data: dict[str, Any]) -> str:
    """SHA-256 over the manifest without its own `checksum` key."""
    payload = {key: value for key, value in data.items() if key != "checksum"}
    return _PREFIX + checksum_bytes(canonical_json(payload).encode("utf-8"))


def dump_manifest(manifest: BaselineManifest) -> dict[str, Any]:
    """Stamps the manifest with its checksum and returns it JSON-ready."""
    data = manifest.to_dict(include_checksum=False)
    manifest.checksum = manifest_checksum(data)
    data["checksum"] = manifest.checksum
    return data


def checksum_matches(data: dict[str, Any]) -> bool:
    """Whether the recorded checksum is the one the content produces."""
    recorded = data.get("checksum")
    if not recorded:
        return False
    return str(recorded) == manifest_checksum(data)


def parse_manifest(data: Any) -> BaselineManifest:
    """Reads a manifest, refusing a document that is not one."""
    if not isinstance(data, dict):
        raise BaselineError(__("The baseline must be a JSON object."))
    return BaselineManifest.from_dict(data)


def validate_manifest_dict(data: Any, fingerprint_version: str | None = None) -> list[str]:
    """Every problem found in a baseline document, as readable lines.

    Returns the whole list instead of raising on the first one: `gitpr baseline
    validate` exists so a human can fix the file in one pass, and a validator
    that stops at the first typo would make that a round trip per key.
    """
    problems: list[str] = []
    if not isinstance(data, dict):
        return [__("The baseline must be a JSON object.")]

    problems.extend(_validate_header(data, fingerprint_version))
    entries = data.get("entries")
    if entries is None:
        problems.append(__("'entries' is missing."))
        return problems
    if not isinstance(entries, list):
        problems.append(__("'entries' must be a list."))
        return problems

    seen: dict[str, int] = {}
    for index, entry in enumerate(entries):
        problems.extend(_validate_entry(entry, index))
        if isinstance(entry, dict) and entry.get("fingerprint"):
            seen.setdefault(str(entry["fingerprint"]), 0)
            seen[str(entry["fingerprint"])] += 1
    for fingerprint, count in seen.items():
        if count > 1:
            problems.append(
                __("Fingerprint {fingerprint} appears {count} times.", fingerprint=fingerprint, count=count)
            )
    return problems


def resolve_fingerprint_prefix(prefix: str, fingerprints: Iterable[str]) -> str:
    """The single fingerprint *prefix* names, or an error naming the ambiguity.

    Short ids are what a human types (`baseline suppress sha256:ab12cd34`), so a
    prefix that matches two findings has to be refused rather than guessed: the
    wrong guess would silence a finding nobody meant to silence.
    """
    wanted = (prefix or "").strip().lower()
    if not wanted:
        raise BaselineError(__("A finding id is required."))
    if not wanted.startswith(_PREFIX):
        wanted = _PREFIX + wanted

    matches = sorted({fp for fp in fingerprints if fp.lower().startswith(wanted)})
    if not matches:
        raise BaselineError(__("No finding in the baseline matches '{prefix}'.", prefix=prefix))
    if len(matches) > 1:
        raise BaselineError(
            __("'{prefix}' matches {count} findings — type a longer id.", prefix=prefix, count=len(matches))
        )
    return matches[0]


def _validate_header(data: dict[str, Any], fingerprint_version: str | None) -> list[str]:
    problems: list[str] = []

    unknown = sorted(set(data) - _ROOT_KEYS)
    if unknown:
        problems.append(
            __("Unknown key(s) in the baseline: {keys}.", keys=", ".join(unknown))
        )

    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        problems.append(
            __(
                "schema_version is {found}; this GitPR writes {expected}.",
                found=version,
                expected=SCHEMA_VERSION,
            )
        )

    recorded_version = data.get("fingerprint_version")
    if not recorded_version:
        problems.append(__("fingerprint_version is missing."))
    elif fingerprint_version and str(recorded_version) != str(fingerprint_version):
        problems.append(
            __(
                "fingerprint_version is {found}, but this GitPR computes {expected} — "
                "run 'gitpr baseline update --recompute'.",
                found=recorded_version,
                expected=fingerprint_version,
            )
        )

    if not data.get("checksum"):
        problems.append(
            __("checksum is missing — run 'gitpr baseline update --recompute'.")
        )
    elif not checksum_matches(data):
        problems.append(
            __(
                "checksum does not match the content: the file was edited outside GitPR — "
                "review the diff and run 'gitpr baseline update --recompute'."
            )
        )
    return problems


def _validate_entry(entry: Any, index: int) -> list[str]:
    problems: list[str] = []
    where = __("entry #{number}", number=index + 1)
    if not isinstance(entry, dict):
        return [__("{where} is not a JSON object.", where=where)]

    unknown = sorted(set(entry) - _ENTRY_KEYS)
    if unknown:
        problems.append(
            __("{where} has unknown key(s): {keys}.", where=where, keys=", ".join(unknown))
        )

    fingerprint = str(entry.get("fingerprint") or "")
    if not _is_fingerprint(fingerprint):
        problems.append(__("{where} has no valid fingerprint.", where=where))

    status = str(entry.get("status") or "")
    if status not in {item.value for item in PERSISTED_STATUSES}:
        problems.append(
            __(
                "{where}: status '{status}' cannot be stored — the baseline keeps "
                "{allowed}.",
                where=where,
                status=status or __("(empty)"),
                allowed=", ".join(item.value for item in PERSISTED_STATUSES),
            )
        )

    start = entry.get("line_start")
    end = entry.get("line_end")
    # 0 is a real line_start: Checkstyle reports it for a file-level violation
    # (file length, missing header), and refusing it here would make `validate`
    # reject a baseline that `create` legitimately wrote.
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
        problems.append(__("{where} has an invalid line range.", where=where))

    if not str(entry.get("file_path") or "").strip():
        problems.append(__("{where} has no file_path.", where=where))

    scope = entry.get("suppression_scope")
    if scope and str(scope) not in {item.value for item in SuppressionScope}:
        problems.append(
            __("{where}: unknown suppression_scope '{scope}'.", where=where, scope=scope)
        )

    # The invariants of §6, checked here as well as at write time: a hand-edited
    # file must not be able to silence a finding without saying why.
    if entry.get("suppressed") and not str(entry.get("suppression_reason") or "").strip():
        problems.append(
            __("{where} is suppressed without a reason.", where=where)
        )

    if entry.get("accepted_debt_owner") or status == BaselineStatus.ACCEPTED_DEBT.value:
        if not str(entry.get("accepted_debt_owner") or "").strip():
            problems.append(__("{where} is accepted debt without an owner.", where=where))
        if not str(entry.get("accepted_debt_reason") or "").strip():
            problems.append(__("{where} is accepted debt without a reason.", where=where))

    due = entry.get("accepted_debt_due_date")
    if due:
        try:
            date.fromisoformat(str(due))
        except ValueError:
            problems.append(
                __("{where}: '{due}' is not a date (expected YYYY-MM-DD).", where=where, due=due)
            )

    if entry.get("resolved_at") and status != BaselineStatus.RESOLVED.value:
        problems.append(
            __("{where} has a resolution date but is not resolved.", where=where)
        )

    if "provenance" in entry and not isinstance(entry["provenance"], dict):
        problems.append(__("{where}: 'provenance' must be a mapping.", where=where))

    return problems


def _is_fingerprint(value: str) -> bool:
    body = value[len(_PREFIX):] if value.startswith(_PREFIX) else value
    return len(body) == _FINGERPRINT_LENGTH and all(
        character in "0123456789abcdef" for character in body
    )
