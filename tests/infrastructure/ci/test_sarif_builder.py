"""Tests for SARIF 2.1.0 builder."""

from src.domain.check.check_types import (
    CheckFinding,
    CheckOutputFormat,
    CheckResult,
    CheckSeverity,
)
from src.infrastructure.ci.sarif_builder import build_sarif


def test_build_sarif_schema_and_driver():
    finding = CheckFinding(
        fingerprint="sha256:abc123",
        rule_id="SEC-AWS-KEY",
        category="security",
        file_path="src/config.py",
        line_start=42,
        line_end=42,
        severity=CheckSeverity.ERROR,
        source="linter",
        message="Hardcoded AWS key AKIAIOSFODNN7EXAMPLE",
        suggestion="Use os.environ['AWS_KEY'] instead",
        baseline_status="new",
        risk_score=85.5,
    )
    result = CheckResult(
        findings=[finding],
        exit_code=1,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.SARIF,
        output_path=None,
        analysis_version="1.0.0",
    )

    sarif = build_sarif(result)
    assert sarif["version"] == "2.1.0"
    assert "$schema" in sarif
    assert len(sarif["runs"]) == 1

    run = sarif["runs"][0]
    driver = run["tool"]["driver"]
    assert driver["name"] == "GitPR"
    assert driver["version"] == "1.0.0"
    assert len(driver["rules"]) == 1
    rule = driver["rules"][0]
    assert rule["id"] == "SEC-AWS-KEY"
    assert rule["defaultConfiguration"]["level"] == "error"

    # Results
    assert len(run["results"]) == 1
    res = run["results"][0]
    assert res["ruleId"] == "SEC-AWS-KEY"
    assert res["level"] == "error"
    assert "AKIAIOSFODNN7EXAMPLE" not in res["message"]["text"]
    assert "***" in res["message"]["text"]

    loc = res["locations"][0]["physicalLocation"]
    assert loc["artifactLocation"]["uri"] == "src/config.py"
    assert loc["region"]["startLine"] == 42
    assert loc["region"]["endLine"] == 42

    props = res["properties"]
    assert props["fingerprint"] == "sha256:abc123"
    assert props["category"] == "security"
    assert props["source"] == "linter"
    assert props["baseline_status"] == "new"
    assert props["risk_score"] == 85.5


def test_build_sarif_incomplete_execution():
    result = CheckResult(
        findings=[],
        exit_code=2,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.SARIF,
        output_path=None,
        analysis_version="1.0.0",
        incomplete=True,
    )
    sarif = build_sarif(result)
    run = sarif["runs"][0]
    assert "invocations" in run
    assert run["invocations"][0]["executionSuccessful"] is False
    assert run["invocations"][0]["exitCode"] == 2
