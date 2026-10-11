"""Canonical finding model shared by linter, SAST bridges and the AI review."""

from dataclasses import dataclass


@dataclass
class NormalizedFinding:
    """Standardized finding model used across all GitPR SAST & linter tools.

    `snippet_hash` is the digest of the offending line (never the line itself) and
    `rule_version` is the version of the rule that produced the finding, when the
    source declares one. Both are optional, so every existing positional
    construction keeps working.
    """

    severity: str  # "error" | "warning" | "info"
    category: str
    file_path: str
    line_start: int
    line_end: int
    message: str
    source: str  # "linter" | "ai" | "semgrep" | "gitleaks" | "bandit" | etc.
    rule_id: str | None = None
    snippet_hash: str | None = None
    rule_version: str | None = None
