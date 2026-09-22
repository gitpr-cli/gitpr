"""Mapping, normalization, and deduplication of SAST and secret findings."""

import re
from src.infrastructure.linter.external.base_bridge import NormalizedFinding


def format_finding_message(finding: NormalizedFinding) -> str:
    """Formats a NormalizedFinding into GitPR's standard linter alert message."""
    tool_label = finding.source.capitalize()
    rule_suffix = f":{finding.rule_id}" if finding.rule_id else ""
    return (
        f"🚨 [{tool_label}{rule_suffix}] {finding.message} "
        f"({finding.file_path}, Line {finding.line_start})"
    )


def deduplicate_secret_findings(
    regex_alerts: dict[str, list[str]],
    sast_findings: list[NormalizedFinding],
) -> tuple[dict[str, list[str]], list[NormalizedFinding]]:
    """Deduplicates findings between regex security ruleset and SAST secret scanners (e.g. Gitleaks).

    If both regex ruleset and Gitleaks detect a secret on the same file and line,
    the finding is merged to indicate multi-source confirmation ([Gitleaks + Regex])
    and avoid duplicated alerts.
    """
    cleaned_alerts = {
        "errors": list(regex_alerts.get("errors", [])),
        "warnings": list(regex_alerts.get("warnings", [])),
    }

    # Extract location index from regex alerts: (file_path, line_number)
    # Regex messages follow: "... in {file_name} (Line {line_number})."
    regex_locations = {}
    pattern = re.compile(r"in\s+([^\s]+)\s+\(Line\s+(\d+)\)", re.IGNORECASE)

    for level in ("errors", "warnings"):
        remaining = []
        for msg in cleaned_alerts[level]:
            match = pattern.search(msg)
            if match:
                f_path = match.group(1).replace("\\", "/").lower()
                line_no = int(match.group(2))
                regex_locations[(f_path, line_no)] = (level, msg)
                remaining.append(msg)
            else:
                remaining.append(msg)
        cleaned_alerts[level] = remaining

    merged_sast_findings: list[NormalizedFinding] = []

    for f in sast_findings:
        normalized_fpath = f.file_path.replace("\\", "/").lower()
        key = (normalized_fpath, f.line_start)

        if key in regex_locations and f.source == "gitleaks":
            # Both detected! Merge them and enhance confidence
            level, old_msg = regex_locations[key]
            # Remove original regex alert from cleaned_alerts
            if old_msg in cleaned_alerts[level]:
                cleaned_alerts[level].remove(old_msg)

            # Update finding message with multi-source marker
            merged_finding = NormalizedFinding(
                severity=f.severity,
                category=f.category,
                file_path=f.file_path,
                line_start=f.line_start,
                line_end=f.line_end,
                message=f"{f.message} (Confirmed by Gitleaks + Static Regex)",
                source="gitleaks+regex",
                rule_id=f.rule_id,
            )
            merged_sast_findings.append(merged_finding)
        else:
            merged_sast_findings.append(f)

    return cleaned_alerts, merged_sast_findings

