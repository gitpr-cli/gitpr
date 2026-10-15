"""Tests for JUnit XML builder."""

import xml.etree.ElementTree as ET
from src.domain.check.check_types import (
    CheckFinding,
    CheckOutputFormat,
    CheckResult,
    CheckSeverity,
)
from src.infrastructure.ci.junit_builder import build_junit_xml


def test_build_junit_xml_with_failure():
    finding_error = CheckFinding(
        fingerprint="sha256:1",
        rule_id="SEC-AWS-KEY",
        category="security",
        file_path="src/config.py",
        line_start=10,
        line_end=10,
        severity=CheckSeverity.ERROR,
        source="linter",
        message="Hardcoded AWS key AKIAIOSFODNN7EXAMPLE",
        baseline_status="new",
    )
    finding_info = CheckFinding(
        fingerprint="sha256:2",
        rule_id="DOC-TODO",
        category="docs",
        file_path="src/main.py",
        line_start=5,
        line_end=5,
        severity=CheckSeverity.INFO,
        source="linter",
        message="TODO item left in code",
        baseline_status=None,
    )
    result = CheckResult(
        findings=[finding_error, finding_info],
        exit_code=1,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.JUNIT,
        output_path=None,
        analysis_version="1.0.0",
    )

    xml_text = build_junit_xml(result)
    root = ET.fromstring(xml_text)
    assert root.tag == "testsuites"
    assert root.attrib["tests"] == "2"
    assert root.attrib["failures"] == "1"

    testcases = root.findall(".//testcase")
    assert len(testcases) == 2

    # Error case has failure
    tc_err = testcases[0]
    failure = tc_err.find("failure")
    assert failure is not None
    assert failure.attrib["type"] == "error"
    assert "AKIAIOSFODNN7EXAMPLE" not in failure.attrib["message"]
    assert "***" in failure.attrib["message"]

    # Info case does not have failure, has system-out
    tc_info = testcases[1]
    assert tc_info.find("failure") is None
    sys_out = tc_info.find("system-out")
    assert sys_out is not None
    assert "[INFO]" in sys_out.text


def test_build_junit_xml_incomplete():
    result = CheckResult(
        findings=[],
        exit_code=2,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.JUNIT,
        output_path=None,
        analysis_version="1.0.0",
        incomplete=True,
    )
    xml_text = build_junit_xml(result)
    root = ET.fromstring(xml_text)
    assert root.attrib["errors"] == "1"
    err = root.find(".//error")
    assert err is not None
    assert err.attrib["type"] == "TimeoutError"
