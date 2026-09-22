"""Unit tests for SAST finding mapper and deduplication."""

from src.domain.linter.sast_finding_mapper import (
    format_finding_message,
    deduplicate_secret_findings,
)
from src.infrastructure.linter.external.base_bridge import NormalizedFinding


def test_format_finding_message():
    finding = NormalizedFinding(
        severity="error",
        category="security/secret",
        file_path="src/config.py",
        line_start=42,
        line_end=42,
        message="AWS Access Key detected [AKIA****]",
        source="gitleaks",
        rule_id="aws-access-key",
    )
    msg = format_finding_message(finding)
    assert msg == "🚨 [Gitleaks:aws-access-key] AWS Access Key detected [AKIA****] (src/config.py, Line 42)"


def test_deduplicate_secret_findings_merges_duplicates():
    regex_alerts = {
        "errors": [
            "🚨 [Regex] Possible AWS Access Key ID hardcoded in src/config.py (Line 42).",
            "🚨 [Regex] Generic error in src/main.py (Line 10).",
        ],
        "warnings": [],
    }

    sast_findings = [
        NormalizedFinding(
            severity="error",
            category="security/secret",
            file_path="src/config.py",
            line_start=42,
            line_end=42,
            message="AWS Access Key [AKIA****]",
            source="gitleaks",
            rule_id="aws-access-key",
        ),
        NormalizedFinding(
            severity="warning",
            category="security/sast",
            file_path="src/utils.py",
            line_start=15,
            line_end=15,
            message="Insecure function",
            source="semgrep",
            rule_id="semgrep-rule",
        ),
    ]

    cleaned_alerts, merged_findings = deduplicate_secret_findings(regex_alerts, sast_findings)

    # Regex error for line 42 should have been removed from cleaned_alerts
    assert len(cleaned_alerts["errors"]) == 1
    assert "src/main.py" in cleaned_alerts["errors"][0]

    # Merged findings should have enhanced message for line 42
    assert len(merged_findings) == 2
    assert merged_findings[0].source == "gitleaks+regex"
    assert "Confirmed by Gitleaks + Static Regex" in merged_findings[0].message
    assert merged_findings[1].source == "semgrep"

