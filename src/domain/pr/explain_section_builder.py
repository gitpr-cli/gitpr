import json
from dataclasses import dataclass, field
from src.i18n import __


@dataclass
class ReviewerFocusPoint:
    """Specific point of focus in the changes for the reviewer."""

    description: str
    file_path: str | None = None
    related_line: int | None = None


@dataclass
class PrExplanation:
    """Reviewer-centric explanation of changes."""

    what_changes: str
    why_it_changes: str
    reviewer_focus_points: list[ReviewerFocusPoint] = field(default_factory=list)
    regression_risk: str = ""
    has_sufficient_evidence: bool = True
    markdown: str = ""


def build_explain_markdown(
    what_changes: str,
    why_it_changes: str,
    reviewer_focus_points: list[ReviewerFocusPoint],
    regression_risk: str,
) -> str:
    """Constructs the markdown block for the reviewer explanation section."""
    lines = [
        "## 🧐 " + __("Reviewer Guide (Explain My PR)"),
        "",
        "### 🔍 " + __("What changes"),
        what_changes.strip(),
        "",
        "### 💡 " + __("Why it changes"),
        why_it_changes.strip(),
        "",
    ]

    if reviewer_focus_points:
        lines.extend([
            "### 🎯 " + __("Where to focus review"),
            "",
        ])
        for pt in reviewer_focus_points:
            loc = ""
            if pt.file_path:
                if pt.related_line:
                    loc = f" (`{pt.file_path}:{pt.related_line}`)"
                else:
                    loc = f" (`{pt.file_path}`)"
            lines.append(f"- **{pt.description.strip()}**{loc}")
        lines.append("")

    if regression_risk:
        lines.extend([
            "### ⚠️ " + __("Regression Risk"),
            regression_risk.strip(),
            "",
        ])

    return "\n".join(lines).strip()


def parse_explain_payload(raw_json_or_text: str) -> PrExplanation:
    """Parses raw AI output into a PrExplanation object."""
    if not raw_json_or_text or not raw_json_or_text.strip():
        return PrExplanation(
            what_changes="",
            why_it_changes="",
            reviewer_focus_points=[],
            regression_risk="",
            has_sufficient_evidence=False,
            markdown="",
        )

    what = ""
    why = ""
    focus_points: list[ReviewerFocusPoint] = []
    risk = ""
    has_evidence = True

    try:
        data = json.loads(raw_json_or_text)
        what = data.get("what_changes", "")
        why = data.get("why_it_changes", "")
        risk = data.get("regression_risk", "")
        for raw_pt in data.get("reviewer_focus_points", []):
            if isinstance(raw_pt, dict):
                focus_points.append(
                    ReviewerFocusPoint(
                        description=raw_pt.get("description", ""),
                        file_path=raw_pt.get("file_path"),
                        related_line=raw_pt.get("related_line"),
                    )
                )
            elif isinstance(raw_pt, str):
                focus_points.append(ReviewerFocusPoint(description=raw_pt))
    except Exception:
        # Fallback if raw text returned
        what = raw_json_or_text.strip()
        why = __("[FILL: Please explain the motivation for these changes]")
        has_evidence = False

    # Check for placeholder markers indicating lack of evidence
    placeholder_indicators = ["[PREENCHER", "[FILL", "[TODO", "[REQUIRED"]
    if any(ind in why.upper() or ind in what.upper() for ind in placeholder_indicators):
        has_evidence = False

    md = build_explain_markdown(what, why, focus_points, risk)

    return PrExplanation(
        what_changes=what,
        why_it_changes=why,
        reviewer_focus_points=focus_points,
        regression_risk=risk,
        has_sufficient_evidence=has_evidence,
        markdown=md,
    )
