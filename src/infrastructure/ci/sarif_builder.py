"""SARIF 2.1.0 builder for GitPR check results.

Produces standard SARIF documents compatible with GitHub Code Scanning,
GitLab SAST, Azure DevOps, and other SARIF-compliant analyzers.
"""

from typing import Any
from src.domain.check.check_types import CheckFinding, CheckResult, CheckSeverity
from src.infrastructure.ci.masking import mask_sensitive_text
from src.updater import __version__

SARIF_SCHEMA_URL = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
)
GITPR_REPO_URL = "https://github.com/natanfiuza/gitpr"

SEVERITY_TO_SARIF_LEVEL: dict[CheckSeverity, str] = {
    CheckSeverity.INFO: "note",
    CheckSeverity.WARNING: "warning",
    CheckSeverity.ERROR: "error",
}


def _normalize_sarif_uri(file_path: str) -> str:
    """Normalizes path to forward slashes relative to repository root."""
    path = file_path.replace("\\", "/").strip()
    while path.startswith("/"):
        path = path[1:]
    return path


def _build_sarif_rules(findings: list[CheckFinding]) -> list[dict[str, Any]]:
    """Builds unique driver.rules definitions from encountered findings."""
    rules_map: dict[str, dict[str, Any]] = {}

    for f in findings:
        rule_id = f.rule_id or f"CATEGORY-{f.category.upper()}"
        level = SEVERITY_TO_SARIF_LEVEL.get(f.severity, "warning")

        if rule_id not in rules_map:
            rule_name = rule_id.replace("-", " ").replace("_", " ").title().replace(" ", "")
            rules_map[rule_id] = {
                "id": rule_id,
                "name": rule_name,
                "shortDescription": {
                    "text": f"Rule {rule_id} ({f.category})"
                },
                "defaultConfiguration": {
                    "level": level
                },
                "properties": {
                    "category": f.category,
                    "source": f.source,
                },
            }
        else:
            # Upgrade default level if another finding has higher severity
            current_level = rules_map[rule_id]["defaultConfiguration"]["level"]
            if level == "error" and current_level != "error":
                rules_map[rule_id]["defaultConfiguration"]["level"] = "error"
            elif level == "warning" and current_level == "note":
                rules_map[rule_id]["defaultConfiguration"]["level"] = "warning"

    return [rules_map[k] for k in sorted(rules_map.keys())]


def _build_sarif_result(finding: CheckFinding) -> dict[str, Any]:
    """Builds a single SARIF result object from a CheckFinding."""
    level = SEVERITY_TO_SARIF_LEVEL.get(finding.severity, "warning")
    rule_id = finding.rule_id or f"CATEGORY-{finding.category.upper()}"
    line_start = max(1, finding.line_start)
    line_end = max(line_start, finding.line_end)

    sanitized_message = mask_sensitive_text(finding.message)
    res: dict[str, Any] = {
        "ruleId": rule_id,
        "level": level,
        "message": {
            "text": sanitized_message
        },
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": _normalize_sarif_uri(finding.file_path),
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": line_start,
                        "endLine": line_end,
                    },
                }
            }
        ],
        "properties": {
            "fingerprint": finding.fingerprint,
            "category": finding.category,
            "source": finding.source,
            "baseline_status": finding.baseline_status,
        },
    }

    if finding.risk_score is not None:
        res["properties"]["risk_score"] = round(finding.risk_score, 1)

    if finding.suggestion:
        res["properties"]["suggestion"] = mask_sensitive_text(finding.suggestion)

    if finding.provenance:
        res["properties"]["provenance"] = finding.provenance

    return res


def build_sarif(result: CheckResult, repo_path: str | None = None) -> dict[str, Any]:
    """Generates a complete SARIF 2.1.0 dictionary from a CheckResult."""
    rules = _build_sarif_rules(result.findings)
    results = [_build_sarif_result(f) for f in result.findings]

    run: dict[str, Any] = {
        "tool": {
            "driver": {
                "name": "GitPR",
                "version": result.analysis_version or __version__,
                "informationUri": GITPR_REPO_URL,
                "rules": rules,
            }
        },
        "results": results,
    }

    if result.incomplete:
        run["invocations"] = [
            {
                "executionSuccessful": False,
                "exitCode": result.exit_code,
                "toolExecutionNotifications": [
                    {
                        "message": {
                            "text": "Execution incomplete due to deadline timeout or execution error."
                        },
                        "level": "error",
                    }
                ],
            }
        ]

    return {
        "version": "2.1.0",
        "$schema": SARIF_SCHEMA_URL,
        "runs": [run],
    }
