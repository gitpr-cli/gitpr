"""Data models and value types for GitPR risk scoring."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class RiskSignal(str, Enum):
    CRITICAL_PATH = "critical_path"
    SECURITY_SENSITIVE = "security_sensitive"
    DATABASE_MIGRATION = "database_migration"
    INFRASTRUCTURE = "infrastructure"
    LARGE_DIFF = "large_diff"
    NO_TEST_CHANGE = "no_test_change"
    TEST_PRESENT = "test_present"
    HISTORICAL_BUGS = "historical_bugs"
    HISTORICAL_REVERTS = "historical_reverts"
    HIGH_CHURN = "high_churn"
    HIGH_COUPLING = "high_coupling"
    FINDING_BLOCKER = "finding_blocker"
    FINDING_CRITICAL = "finding_critical"
    FINDING_WARNING = "finding_warning"
    # A finding the baseline already knew about. It carries no weight on purpose:
    # the status is the answer to "does this count against the change?", and the
    # evidence exists so the report can say so out loud instead of dropping the
    # finding from the breakdown. See `baseline_gate.informational_evidence`.
    BASELINE_FINDING = "baseline_finding"
    NEW_FILE = "new_file"
    SIGNAL_UNAVAILABLE = "signal_unavailable"


@dataclass
class RiskEvidence:
    signal: RiskSignal
    points: float
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    confidence: str = "medium"  # high | medium | low

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal.value if isinstance(self.signal, RiskSignal) else str(self.signal),
            "points": self.points,
            "summary": self.summary,
            "details": self.details,
            "confidence": self.confidence,
        }


@dataclass
class FileRisk:
    file_path: str
    score: float  # 0.0–100.0
    level: RiskLevel
    changed_lines: int
    changed_hunks: int
    evidence: list[RiskEvidence] = field(default_factory=list)
    related_test_files: list[str] = field(default_factory=list)
    signals_available: list[RiskSignal] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "score": round(self.score, 1),
            "level": self.level.value if isinstance(self.level, RiskLevel) else str(self.level),
            "changed_lines": self.changed_lines,
            "changed_hunks": self.changed_hunks,
            "evidence": [e.to_dict() for e in self.evidence],
            "related_test_files": list(self.related_test_files),
            "signals_available": [
                s.value if isinstance(s, RiskSignal) else str(s)
                for s in self.signals_available
            ],
            "warnings": list(self.warnings),
        }


@dataclass
class PullRequestRisk:
    score: float  # 0.0–100.0
    level: RiskLevel
    files: list[FileRisk] = field(default_factory=list)
    evidence: list[RiskEvidence] = field(default_factory=list)  # Top aggregated evidence
    total_changed_files: int = 0
    total_changed_lines: int = 0
    tests_changed: bool = False
    critical_files: list[str] = field(default_factory=list)
    analysis_version: str = "1.0"
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "level": self.level.value if isinstance(self.level, RiskLevel) else str(self.level),
            "total_changed_files": self.total_changed_files,
            "total_changed_lines": self.total_changed_lines,
            "tests_changed": self.tests_changed,
            "critical_files": list(self.critical_files),
            "analysis_version": self.analysis_version,
            "evidence": [e.to_dict() for e in self.evidence],
            "files": [f.to_dict() for f in self.files],
            "warnings": list(self.warnings),
        }

