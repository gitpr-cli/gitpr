"""Output serialization layer for gitpr check (SARIF, JSON, JUnit).

Centralizes masking, schema compliance, and artifact file writing.
"""

import json
import os
from typing import Any

from src.domain.check.check_types import (
    CheckFinding,
    CheckOutputFormat,
    CheckResult,
)
from src.infrastructure.ci.junit_builder import build_junit_xml
from src.infrastructure.ci.masking import mask_sensitive_text
from src.infrastructure.ci.sarif_builder import build_sarif


def _finding_to_json_dict(f: CheckFinding) -> dict[str, Any]:
    return {
        "fingerprint": f.fingerprint,
        "rule_id": f.rule_id,
        "category": f.category,
        "file_path": f.file_path.replace("\\", "/"),
        "line_start": f.line_start,
        "line_end": f.line_end,
        "severity": f.severity.value,
        "source": f.source,
        "message": mask_sensitive_text(f.message),
        "suggestion": mask_sensitive_text(f.suggestion) if f.suggestion else None,
        "baseline_status": f.baseline_status,
        "risk_score": round(f.risk_score, 1) if f.risk_score is not None else None,
        "provenance": f.provenance,
    }


def format_json_envelope(result: CheckResult) -> dict[str, Any]:
    """Builds standard structured JSON dictionary for gitpr check."""
    if result.exit_code == 0:
        status_label = "success"
    elif result.exit_code == 1:
        status_label = "failure"
    else:
        status_label = "error"

    return {
        "version": "1.0.0",
        "gitpr_version": result.analysis_version,
        "status": status_label,
        "exit_code": result.exit_code,
        "incomplete": result.incomplete,
        "fail_on": result.fail_on.value,
        "output_format": result.output_format.value,
        "summary": {
            "total": result.summary.total,
            "countable": result.summary.countable,
            "errors": result.summary.errors,
            "warnings": result.summary.warnings,
            "info": result.summary.info,
            "new": result.summary.new,
            "existing": result.summary.existing,
            "ignored": result.summary.ignored,
            "accepted_debt": result.summary.accepted_debt,
            "resolved": result.summary.resolved,
        },
        "risk": result.risk_summary,
        "warnings": result.warnings,
        "findings": [_finding_to_json_dict(f) for f in result.findings],
    }


def format_check_output(
    result: CheckResult,
    output_format: CheckOutputFormat | None = None,
) -> str:
    """Serializes a CheckResult into the requested format (SARIF, JSON, JUnit)."""
    fmt = output_format or result.output_format

    if fmt == CheckOutputFormat.SARIF:
        sarif_dict = build_sarif(result)
        return json.dumps(sarif_dict, indent=2, ensure_ascii=False)

    if fmt == CheckOutputFormat.JUNIT:
        return build_junit_xml(result)

    if fmt == CheckOutputFormat.JSON:
        json_dict = format_json_envelope(result)
        return json.dumps(json_dict, indent=2, ensure_ascii=False)

    raise ValueError(f"Unsupported check output format: {fmt}")


def write_check_output(content: str, output_path: str) -> None:
    """Writes formatted check output content to target path atomically."""
    target_abs = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(target_abs), exist_ok=True)
    temp_path = f"{target_abs}.tmp.{os.getpid()}"
    try:
        with open(temp_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
        # Atomic replace
        if os.path.exists(target_abs):
            os.replace(temp_path, target_abs)
        else:
            os.rename(temp_path, target_abs)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
