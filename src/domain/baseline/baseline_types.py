"""Value contracts for the technical baseline and its auditable suppressions.

The baseline is a file meant to be committed: `.gitpr/baseline.json` lists every
finding the repository has decided to live with, and the decision behind each
one. It is what lets a team adopt GitPR on a legacy tree without the first run
failing on a hundred pre-existing problems — the gate then only answers for what
the change under review introduced.

These are plain value types. Nothing here reads a file, touches the network or
knows about JSON: that keeps the domain testable without fixtures on disk. See
docs/plans/glossary-baseline.md for the vocabulary and
docs/plans/ADR-012-baseline-suppressions.md for why the shape is what it is.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.domain.baseline.baseline_fingerprint import rule_identity
from src.i18n import __


class BaselineStatus(str, Enum):
    """Where a finding stands relative to the baseline.

    `NEW` is produced by a comparison and never written to the file: an entry
    saved as "new" would be born stale, because the next run would have to
    re-derive it anyway. The other four are the persisted states.
    """

    NEW = "new"
    EXISTING = "existing"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    ACCEPTED_DEBT = "accepted_debt"


class SuppressionScope(str, Enum):
    """How wide a suppression reaches, from the narrowest to the widest."""

    FINDING = "finding"  # one exact fingerprint
    LINE = "line"        # a rule in a file inside a line range
    FILE = "file"        # a rule in a file (or path glob)
    RULE = "rule"        # a rule anywhere in the repository


# Specificity order, narrowest first: the most specific match is the one that
# supplies the status and the reason shown to the reader.
SCOPE_PRECEDENCE = (
    SuppressionScope.FINDING,
    SuppressionScope.LINE,
    SuppressionScope.FILE,
    SuppressionScope.RULE,
)

# What may be written to the file. `new` is deliberately absent.
PERSISTED_STATUSES = (
    BaselineStatus.EXISTING,
    BaselineStatus.IGNORED,
    BaselineStatus.ACCEPTED_DEBT,
    BaselineStatus.RESOLVED,
)


class BaselineError(Exception):
    """The baseline is unusable and the operation cannot continue.

    Carries the path the problem came from, so a message can name the file the
    user has to look at instead of only saying what is wrong.
    """

    def __init__(self, message: str, path: str | None = None):
        super().__init__(message)
        self.message = message
        self.path = path


@dataclass
class FindingFingerprint:
    """The identity fields a fingerprint was derived from, kept for the report."""

    fingerprint: str
    rule_id: str | None
    category: str
    file_path: str
    line_start: int
    line_end: int
    source: str
    severity: str

    def identity(self) -> str:
        """The rule identity behind the fingerprint — the id, or the category."""
        return rule_identity(self.rule_id, self.category)


@dataclass
class BaselineEntry:
    """One finding the repository has acknowledged, and what was decided about it.

    No message is stored: the prose a rule emits belongs to the rule and would
    make every rewording look like a baseline change. The reasoning a human
    needs is in the suppression reason or the accepted-debt fields.
    """

    fingerprint: str
    rule_id: str | None
    category: str
    file_path: str
    line_start: int
    line_end: int
    severity: str
    source: str
    status: BaselineStatus = BaselineStatus.EXISTING
    low_confidence: bool = False
    first_seen_commit: str | None = None
    last_seen_commit: str | None = None
    first_seen_date: str | None = None
    last_seen_date: str | None = None
    resolved_at: str | None = None
    suppressed: bool = False
    suppression_reason: str | None = None
    suppression_scope: SuppressionScope | None = None
    suppressed_by: str | None = None
    suppressed_at: str | None = None
    accepted_debt_owner: str | None = None
    accepted_debt_due_date: str | None = None
    accepted_debt_reason: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def identity(self) -> str:
        """The rule identity this entry was fingerprinted under."""
        return rule_identity(self.rule_id, self.category)

    def is_debt(self) -> bool:
        """Whether the entry carries accepted technical debt."""
        return self.status == BaselineStatus.ACCEPTED_DEBT or bool(self.accepted_debt_owner)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "rule_id": self.rule_id,
            "category": self.category,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "severity": self.severity,
            "source": self.source,
            "status": self.status.value if isinstance(self.status, BaselineStatus) else str(self.status),
            "low_confidence": self.low_confidence,
            "first_seen_commit": self.first_seen_commit,
            "last_seen_commit": self.last_seen_commit,
            "first_seen_date": self.first_seen_date,
            "last_seen_date": self.last_seen_date,
            "resolved_at": self.resolved_at,
            "suppressed": self.suppressed,
            "suppression_reason": self.suppression_reason,
            "suppression_scope": (
                self.suppression_scope.value
                if isinstance(self.suppression_scope, SuppressionScope)
                else self.suppression_scope
            ),
            "suppressed_by": self.suppressed_by,
            "suppressed_at": self.suppressed_at,
            "accepted_debt_owner": self.accepted_debt_owner,
            "accepted_debt_due_date": self.accepted_debt_due_date,
            "accepted_debt_reason": self.accepted_debt_reason,
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaselineEntry":
        """Rebuilds an entry, refusing one that is missing its identity.

        Tolerant about what it does not know (a newer GitPR may have written
        extra keys — validation is where that is reported) and strict about what
        it cannot work without.
        """
        if not isinstance(data, dict):
            raise BaselineError(__("A baseline entry must be a JSON object."))
        fingerprint = data.get("fingerprint")
        if not fingerprint:
            raise BaselineError(__("A baseline entry has no fingerprint."))
        scope = data.get("suppression_scope")
        return cls(
            fingerprint=str(fingerprint),
            rule_id=data.get("rule_id"),
            category=str(data.get("category") or ""),
            file_path=str(data.get("file_path") or ""),
            line_start=int(data.get("line_start") or 0),
            line_end=int(data.get("line_end") or 0),
            severity=str(data.get("severity") or "warning"),
            source=str(data.get("source") or ""),
            status=_status(data.get("status")),
            low_confidence=bool(data.get("low_confidence")),
            first_seen_commit=data.get("first_seen_commit"),
            last_seen_commit=data.get("last_seen_commit"),
            first_seen_date=data.get("first_seen_date"),
            last_seen_date=data.get("last_seen_date"),
            resolved_at=data.get("resolved_at"),
            suppressed=bool(data.get("suppressed")),
            suppression_reason=data.get("suppression_reason"),
            suppression_scope=SuppressionScope(scope) if scope else None,
            suppressed_by=data.get("suppressed_by"),
            suppressed_at=data.get("suppressed_at"),
            accepted_debt_owner=data.get("accepted_debt_owner"),
            accepted_debt_due_date=data.get("accepted_debt_due_date"),
            accepted_debt_reason=data.get("accepted_debt_reason"),
            provenance=dict(data.get("provenance") or {}),
        )


@dataclass
class BaselineManifest:
    """The baseline file: which findings exist, and the checksum over them."""

    entries: list[BaselineEntry] = field(default_factory=list)
    schema_version: int = 1
    fingerprint_version: str = ""
    policy_name: str | None = None
    policy_version: str | None = None
    gitpr_version: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    checksum: str | None = None

    def entry_for(self, fingerprint: str) -> BaselineEntry | None:
        """The entry with this fingerprint, or None."""
        for entry in self.entries:
            if entry.fingerprint == fingerprint:
                return entry
        return None

    def to_dict(self, include_checksum: bool = True) -> dict[str, Any]:
        """The manifest as JSON-ready data, entries ordered by fingerprint.

        Ordering is part of the contract: the file is committed, and two runs
        over the same findings on two machines have to produce the same diff.
        """
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "fingerprint_version": self.fingerprint_version,
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "gitpr_version": self.gitpr_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_checksum:
            data["checksum"] = self.checksum
        data["entries"] = [
            entry.to_dict() for entry in sorted(self.entries, key=lambda e: e.fingerprint)
        ]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaselineManifest":
        if not isinstance(data, dict):
            raise BaselineError(__("The baseline must be a JSON object."))
        raw_entries = data.get("entries")
        if raw_entries is None:
            raw_entries = []
        if not isinstance(raw_entries, list):
            raise BaselineError(__("'entries' must be a list."))
        return cls(
            entries=[BaselineEntry.from_dict(entry) for entry in raw_entries],
            schema_version=int(data.get("schema_version") or 1),
            fingerprint_version=str(data.get("fingerprint_version") or ""),
            policy_name=data.get("policy_name"),
            policy_version=data.get("policy_version"),
            gitpr_version=data.get("gitpr_version"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            checksum=data.get("checksum"),
        )


def _status(value: Any) -> BaselineStatus:
    """Reads a status, mapping an unknown one to `existing` rather than crashing.

    A file written by a future GitPR may carry a state this version does not
    know; treating it as "already there" is the reading that never blocks a
    pipeline on a word it has not learned yet. `validate` reports it.
    """
    if isinstance(value, BaselineStatus):
        return value
    try:
        return BaselineStatus(str(value))
    except ValueError:
        return BaselineStatus.EXISTING
