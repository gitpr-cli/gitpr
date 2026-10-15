"""Tests for check_types domain models and helpers."""

import pytest
from src.domain.check.check_types import (
    CheckFinding,
    CheckOutputFormat,
    CheckResult,
    CheckSeverity,
    CheckSummary,
    parse_output_format,
    parse_severity,
)


def test_parse_severity_valid_canonical():
    assert parse_severity("info") == CheckSeverity.INFO
    assert parse_severity("warning") == CheckSeverity.WARNING
    assert parse_severity("error") == CheckSeverity.ERROR


def test_parse_severity_aliases():
    assert parse_severity("minor") == CheckSeverity.WARNING
    assert parse_severity("major") == CheckSeverity.ERROR
    assert parse_severity("critical") == CheckSeverity.ERROR
    assert parse_severity("blocker") == CheckSeverity.ERROR
    # Case insensitivity
    assert parse_severity("CRITICAL") == CheckSeverity.ERROR
    assert parse_severity(" Minor ") == CheckSeverity.WARNING


def test_parse_severity_invalid():
    with pytest.raises(ValueError, match="Invalid severity 'fatal'"):
        parse_severity("fatal")


def test_severity_ranks_and_thresholds():
    assert CheckSeverity.ERROR.rank > CheckSeverity.WARNING.rank > CheckSeverity.INFO.rank
    assert CheckSeverity.ERROR.meets_threshold(CheckSeverity.ERROR) is True
    assert CheckSeverity.ERROR.meets_threshold(CheckSeverity.WARNING) is True
    assert CheckSeverity.WARNING.meets_threshold(CheckSeverity.ERROR) is False
    assert CheckSeverity.WARNING.meets_threshold(CheckSeverity.WARNING) is True
    assert CheckSeverity.INFO.meets_threshold(CheckSeverity.WARNING) is False


def test_parse_output_format():
    assert parse_output_format("sarif") == CheckOutputFormat.SARIF
    assert parse_output_format("json") == CheckOutputFormat.JSON
    assert parse_output_format("junit") == CheckOutputFormat.JUNIT
    assert parse_output_format("SARIF") == CheckOutputFormat.SARIF

    with pytest.raises(ValueError, match="Invalid output format 'yaml'"):
        parse_output_format("yaml")


def test_check_finding_is_countable():
    f_no_baseline = CheckFinding(
        fingerprint="sha256:1",
        rule_id="SEC-01",
        category="security",
        file_path="app.py",
        line_start=10,
        line_end=10,
        severity=CheckSeverity.ERROR,
        source="linter",
        message="Hardcoded key",
        baseline_status=None,
    )
    assert f_no_baseline.is_countable is True

    f_new = CheckFinding(
        fingerprint="sha256:2",
        rule_id="SEC-01",
        category="security",
        file_path="app.py",
        line_start=12,
        line_end=12,
        severity=CheckSeverity.ERROR,
        source="linter",
        message="Hardcoded key",
        baseline_status="new",
    )
    assert f_new.is_countable is True

    f_existing = CheckFinding(
        fingerprint="sha256:3",
        rule_id="SEC-01",
        category="security",
        file_path="app.py",
        line_start=15,
        line_end=15,
        severity=CheckSeverity.ERROR,
        source="linter",
        message="Hardcoded key",
        baseline_status="existing",
    )
    assert f_existing.is_countable is False


def test_check_summary_aggregation():
    findings = [
        CheckFinding(
            fingerprint="sha256:1",
            rule_id="SEC-01",
            category="security",
            file_path="app.py",
            line_start=1,
            line_end=1,
            severity=CheckSeverity.ERROR,
            source="linter",
            message="Error 1",
            baseline_status="new",
        ),
        CheckFinding(
            fingerprint="sha256:2",
            rule_id="STYLE-01",
            category="style",
            file_path="app.py",
            line_start=2,
            line_end=2,
            severity=CheckSeverity.WARNING,
            source="linter",
            message="Warning 1",
            baseline_status="existing",
        ),
        CheckFinding(
            fingerprint="sha256:3",
            rule_id="DOC-01",
            category="docs",
            file_path="app.py",
            line_start=3,
            line_end=3,
            severity=CheckSeverity.INFO,
            source="ai",
            message="Info 1",
            baseline_status="ignored",
        ),
        CheckFinding(
            fingerprint="sha256:4",
            rule_id="SEC-02",
            category="security",
            file_path="app.py",
            line_start=4,
            line_end=4,
            severity=CheckSeverity.ERROR,
            source="linter",
            message="Debt",
            baseline_status="accepted_debt",
        ),
        CheckFinding(
            fingerprint="sha256:5",
            rule_id="SEC-03",
            category="security",
            file_path="app.py",
            line_start=5,
            line_end=5,
            severity=CheckSeverity.ERROR,
            source="linter",
            message="Resolved",
            baseline_status="resolved",
        ),
    ]

    summary = CheckSummary.from_findings(findings)
    assert summary.total == 5
    assert summary.countable == 1  # only finding 1 is "new"
    assert summary.errors == 3
    assert summary.warnings == 1
    assert summary.info == 1
    assert summary.new == 1
    assert summary.existing == 1
    assert summary.ignored == 1
    assert summary.accepted_debt == 1
    assert summary.resolved == 1


def test_check_result_auto_generates_summary():
    finding = CheckFinding(
        fingerprint="sha256:1",
        rule_id="SEC-01",
        category="security",
        file_path="app.py",
        line_start=1,
        line_end=1,
        severity=CheckSeverity.ERROR,
        source="linter",
        message="Error 1",
    )
    result = CheckResult(
        findings=[finding],
        exit_code=1,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.JSON,
        output_path=None,
        analysis_version="1.0.0",
    )
    assert result.summary.total == 1
    assert result.summary.errors == 1
    assert result.summary.countable == 1
