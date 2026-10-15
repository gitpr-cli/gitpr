"""Tests for check_output formatting and atomic file writing."""

import json
import os
import tempfile

from src.domain.check.check_output import (
    format_check_output,
    format_json_envelope,
    write_check_output,
)
from src.domain.check.check_types import (
    CheckFinding,
    CheckOutputFormat,
    CheckResult,
    CheckSeverity,
)


def _sample_result() -> CheckResult:
    finding = CheckFinding(
        fingerprint="sha256:abc",
        rule_id="SEC-01",
        category="security",
        file_path="app/test.py",
        line_start=10,
        line_end=10,
        severity=CheckSeverity.ERROR,
        source="linter",
        message="Found token ghp_123456789012345678901234567890123456",
        suggestion="Remove token ghp_123456789012345678901234567890123456",
        baseline_status="new",
        risk_score=90.0,
    )
    return CheckResult(
        findings=[finding],
        exit_code=1,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.JSON,
        output_path=None,
        analysis_version="1.0.0",
        risk_summary={"score": 90.0, "level": "high"},
    )


def test_format_json_envelope():
    res = _sample_result()
    envelope = format_json_envelope(res)
    assert envelope["version"] == "1.0.0"
    assert envelope["gitpr_version"] == "1.0.0"
    assert envelope["status"] == "failure"
    assert envelope["exit_code"] == 1
    assert envelope["incomplete"] is False
    assert envelope["summary"]["total"] == 1
    assert envelope["summary"]["errors"] == 1
    assert envelope["summary"]["new"] == 1
    assert envelope["risk"]["score"] == 90.0

    finding_data = envelope["findings"][0]
    assert "ghp_" not in finding_data["message"]
    assert "***" in finding_data["message"]
    assert "***" in finding_data["suggestion"]


def test_format_check_output_dispatch():
    res = _sample_result()

    # JSON
    json_out = format_check_output(res, CheckOutputFormat.JSON)
    data = json.loads(json_out)
    assert data["status"] == "failure"

    # SARIF
    sarif_out = format_check_output(res, CheckOutputFormat.SARIF)
    sarif_data = json.loads(sarif_out)
    assert sarif_data["version"] == "2.1.0"

    # JUNIT
    junit_out = format_check_output(res, CheckOutputFormat.JUNIT)
    assert "<testsuites" in junit_out
    assert "</testsuites>" in junit_out


def test_write_check_output_atomic():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = os.path.join(tmpdir, "nested", "results.sarif")
        write_check_output('{"version": "2.1.0"}', target)
        assert os.path.isfile(target)
        with open(target, "r", encoding="utf-8") as f:
            assert f.read() == '{"version": "2.1.0"}'
