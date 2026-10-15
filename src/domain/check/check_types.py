"""Domain types for the unified GitPR CI check."""

from dataclasses import dataclass, field
from enum import Enum


class CheckSeverity(str, Enum):
    """Normalized 3-level severity scale for GitPR findings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    @property
    def rank(self) -> int:
        ranks = {
            CheckSeverity.INFO: 1,
            CheckSeverity.WARNING: 2,
            CheckSeverity.ERROR: 3,
        }
        return ranks[self]

    def meets_threshold(self, threshold: "CheckSeverity") -> bool:
        """Returns True if this severity is greater than or equal to the threshold."""
        return self.rank >= threshold.rank


SEVERITY_ALIASES: dict[str, CheckSeverity] = {
    "info": CheckSeverity.INFO,
    "warning": CheckSeverity.WARNING,
    "minor": CheckSeverity.WARNING,
    "error": CheckSeverity.ERROR,
    "major": CheckSeverity.ERROR,
    "critical": CheckSeverity.ERROR,
    "blocker": CheckSeverity.ERROR,
}


def parse_severity(value: str) -> CheckSeverity:
    """Parses a severity string or spec alias into a canonical CheckSeverity.

    Accepts 'info', 'warning', 'minor', 'error', 'major', 'critical', 'blocker'
    (case-insensitive). Raises ValueError if unrecognized.
    """
    if not isinstance(value, str):
        raise ValueError(f"Severity must be a string, got {type(value).__name__}")
    normalized = value.strip().lower()
    if normalized in SEVERITY_ALIASES:
        return SEVERITY_ALIASES[normalized]
    valid_options = ", ".join(sorted(SEVERITY_ALIASES.keys()))
    raise ValueError(
        f"Invalid severity '{value}'. Allowed options are: {valid_options}"
    )


class CheckOutputFormat(str, Enum):
    """Supported output formats for CI artifacts."""

    SARIF = "sarif"
    JSON = "json"
    JUNIT = "junit"


def parse_output_format(value: str) -> CheckOutputFormat:
    """Parses output format string (case-insensitive)."""
    if not isinstance(value, str):
        raise ValueError(f"Format must be a string, got {type(value).__name__}")
    normalized = value.strip().lower()
    for fmt in CheckOutputFormat:
        if fmt.value == normalized:
            return fmt
    valid_options = ", ".join(f.value for f in CheckOutputFormat)
    raise ValueError(
        f"Invalid output format '{value}'. Allowed options are: {valid_options}"
    )


@dataclass
class CheckFinding:
    """Unified finding model evaluated by gitpr check."""

    fingerprint: str
    rule_id: str
    category: str
    file_path: str
    line_start: int
    line_end: int
    severity: CheckSeverity
    source: str
    message: str
    suggestion: str | None = None
    baseline_status: str | None = None  # new, existing, ignored, accepted_debt, resolved, or None
    risk_score: float | None = None
    provenance: dict = field(default_factory=dict)

    @property
    def is_countable(self) -> bool:
        """Whether this finding can fail the run under --fail-on.

        A finding is countable if baseline_status is None (no baseline in force)
        or if baseline_status is 'new'.
        """
        return self.baseline_status is None or self.baseline_status == "new"


@dataclass
class CheckSummary:
    """Aggregated counters for findings by severity and baseline status."""

    total: int = 0
    countable: int = 0
    errors: int = 0
    warnings: int = 0
    info: int = 0
    new: int = 0
    existing: int = 0
    ignored: int = 0
    accepted_debt: int = 0
    resolved: int = 0

    @classmethod
    def from_findings(cls, findings: list[CheckFinding]) -> "CheckSummary":
        summary = cls(total=len(findings))
        for f in findings:
            if f.is_countable:
                summary.countable += 1
            if f.severity == CheckSeverity.ERROR:
                summary.errors += 1
            elif f.severity == CheckSeverity.WARNING:
                summary.warnings += 1
            elif f.severity == CheckSeverity.INFO:
                summary.info += 1

            status = f.baseline_status
            if status == "new":
                summary.new += 1
            elif status == "existing":
                summary.existing += 1
            elif status == "ignored":
                summary.ignored += 1
            elif status == "accepted_debt":
                summary.accepted_debt += 1
            elif status == "resolved":
                summary.resolved += 1
        return summary


@dataclass
class CheckResult:
    """Complete result of a gitpr check execution."""

    findings: list[CheckFinding]
    exit_code: int  # 0 | 1 | 2
    fail_on: CheckSeverity
    output_format: CheckOutputFormat
    output_path: str | None
    analysis_version: str
    warnings: list[str] = field(default_factory=list)
    incomplete: bool = False
    risk_summary: dict | None = None
    summary: CheckSummary = field(default_factory=CheckSummary)

    def __post_init__(self):
        if not self.summary or self.summary.total == 0 and self.findings:
            self.summary = CheckSummary.from_findings(self.findings)
