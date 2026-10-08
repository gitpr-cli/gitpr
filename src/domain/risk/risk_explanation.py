"""Human-readable explanation, markdown report, and terminal formatting for risk scoring."""

from src.domain.risk.risk_types import FileRisk, PullRequestRisk, RiskEvidence, RiskLevel


def get_level_badge(level: RiskLevel) -> str:
    """Returns a visual badge representation for a RiskLevel."""
    if level == RiskLevel.CRITICAL:
        return "CRITICAL 🔴"
    if level == RiskLevel.HIGH:
        return "HIGH 🟠"
    if level == RiskLevel.MEDIUM:
        return "MEDIUM 🟡"
    if level == RiskLevel.LOW:
        return "LOW 🟢"
    return "UNKNOWN ⚪"


def format_evidence_line(evidence: RiskEvidence) -> str:
    """Format one RiskEvidence item for display."""
    sign = "+" if evidence.points > 0 else ""
    pts = f"{sign}{int(evidence.points)} pts" if evidence.points != 0 else "0 pts"
    conf = f"[{evidence.confidence}]" if evidence.confidence != "high" else ""
    extra = f" {conf}" if conf else ""
    return f"• {pts}: {evidence.summary}{extra}"


def format_risk_review_section(pr_risk: PullRequestRisk) -> str:
    """Format the Markdown section '## ⚡ Risk Assessment' for the review report file."""
    lines = [
        "## ⚡ Risk Assessment",
        "",
        f"**Risk Level:** `{pr_risk.level.value.upper()}` | **Score:** `{pr_risk.score}/100` (v{pr_risk.analysis_version})",
        "",
    ]

    if pr_risk.evidence:
        lines.append("**Top Contributing Risk Factors:**")
        for ev in pr_risk.evidence[:5]:
            lines.append(format_evidence_line(ev))
        lines.append("")

    if pr_risk.critical_files:
        lines.append(f"**Critical / High-Risk Files ({len(pr_risk.critical_files)}):**")
        for cf in pr_risk.critical_files[:8]:
            lines.append(f"- `{cf}`")
        if len(pr_risk.critical_files) > 8:
            lines.append(f"- *... and {len(pr_risk.critical_files) - 8} more*")
        lines.append("")

    if not pr_risk.tests_changed:
        lines.append("⚠️ **Notice:** No related tests were detected in this diff.")
        lines.append("")

    if pr_risk.warnings:
        lines.append("**Signal Notices:**")
        for w in pr_risk.warnings:
            lines.append(f"- *{w}*")
        lines.append("")

    return "\n".join(lines)


def format_ai_risk_context(pr_risk: PullRequestRisk) -> str:
    """Format a compact structured risk summary for inclusion in the AI review prompt."""
    ev_summaries = "; ".join(
        f"{e.summary} ({int(e.points):+d})" for e in pr_risk.evidence[:4]
    )
    crit_files_str = ", ".join(pr_risk.critical_files[:5]) or "None"
    return (
        f"[GitPR Deterministic Risk Assessment]\n"
        f"Score: {pr_risk.score}/100 ({pr_risk.level.value.upper()})\n"
        f"Key Factors: {ev_summaries or 'None'}\n"
        f"Critical Files: {crit_files_str}\n"
        f"Tests Detected: {'Yes' if pr_risk.tests_changed else 'No'}\n"
        f"Note: This score is pre-computed locally. Do not alter this score. Prioritize review scrutiny on critical files."
    )

