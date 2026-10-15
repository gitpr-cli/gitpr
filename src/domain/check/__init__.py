"""Check domain module for GitPR unified CI execution."""

from src.domain.check.check_types import (
    CheckFinding,
    CheckOutputFormat,
    CheckResult,
    CheckSeverity,
    CheckSummary,
    parse_severity,
)
from src.domain.check.check_config import CheckConfig, load_check_config

from src.domain.check.check_output import (
    format_check_output,
    format_json_envelope,
    write_check_output,
)

__all__ = [
    "CheckFinding",
    "CheckOutputFormat",
    "CheckResult",
    "CheckSeverity",
    "CheckSummary",
    "CheckConfig",
    "parse_severity",
    "load_check_config",
    "format_check_output",
    "format_json_envelope",
    "write_check_output",
]
