"""JUnit XML builder for GitPR check results.

Produces standard JUnit XML test suite reports compatible with Jenkins,
GitLab CI test reports, Azure Pipelines, and CircleCI.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom

from src.domain.check.check_types import CheckFinding, CheckResult, CheckSeverity
from src.infrastructure.ci.masking import mask_sensitive_text


def build_junit_xml(result: CheckResult) -> str:
    """Generates standard JUnit XML string from a CheckResult."""
    testsuites = ET.Element("testsuites", name="GitPR")

    total_tests = len(result.findings)
    failures_count = 0
    errors_count = 0

    suite = ET.SubElement(
        testsuites,
        "testsuite",
        name="gitpr.check",
        tests=str(total_tests),
    )

    for finding in result.findings:
        classname = finding.file_path.replace("\\", "/")
        rule_name = finding.rule_id or f"CATEGORY-{finding.category.upper()}"
        line_start = finding.line_start

        testcase = ET.SubElement(
            suite,
            "testcase",
            classname=classname,
            name=f"{rule_name} (Line {line_start})",
        )

        sanitized_msg = mask_sensitive_text(finding.message)
        details = (
            f"Rule: {rule_name}\n"
            f"Category: {finding.category}\n"
            f"File: {classname}:{line_start}\n"
            f"Severity: {finding.severity.value}\n"
            f"Source: {finding.source}\n"
            f"Fingerprint: {finding.fingerprint}\n"
        )
        if finding.baseline_status:
            details += f"Baseline Status: {finding.baseline_status}\n"
        if finding.risk_score is not None:
            details += f"Risk Score: {finding.risk_score}\n"
        if finding.suggestion:
            details += f"Suggestion: {mask_sensitive_text(finding.suggestion)}\n"
        details += f"\nMessage: {sanitized_msg}"

        # If severity meets or exceeds fail_on threshold, record as failure
        if finding.severity.meets_threshold(result.fail_on) and finding.is_countable:
            failure_type = "error" if finding.severity == CheckSeverity.ERROR else "warning"
            failure = ET.SubElement(
                testcase,
                "failure",
                message=sanitized_msg,
                type=failure_type,
            )
            failure.text = details
            failures_count += 1
        elif finding.severity == CheckSeverity.ERROR:
            # Error but not countable (e.g. suppressed or existing in baseline)
            sys_out = ET.SubElement(testcase, "system-out")
            sys_out.text = f"[NON-BLOCKING ERROR]\n{details}"
        else:
            # Informational / Warning under threshold
            sys_out = ET.SubElement(testcase, "system-out")
            sys_out.text = f"[{finding.severity.value.upper()}]\n{details}"

    if result.incomplete:
        errors_count += 1
        incomplete_tc = ET.SubElement(
            suite,
            "testcase",
            classname="gitpr.check",
            name="execution_status",
        )
        err = ET.SubElement(
            incomplete_tc,
            "error",
            message="Check run did not finish within timeout or encountered an error",
            type="TimeoutError",
        )
        err.text = "Check run was terminated before full completion."

    testsuites.set("tests", str(total_tests + (1 if result.incomplete else 0)))
    testsuites.set("failures", str(failures_count))
    testsuites.set("errors", str(errors_count))
    suite.set("failures", str(failures_count))
    suite.set("errors", str(errors_count))

    rough_string = ET.tostring(testsuites, encoding="utf-8")
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
