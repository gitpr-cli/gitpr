import json
from src.domain.pr.explain_section_builder import (
    ReviewerFocusPoint,
    PrExplanation,
    build_explain_markdown,
    parse_explain_payload,
)


def test_build_explain_markdown():
    what = "Refactored user authentication to use JWT tokens."
    why = "Improves API scalability and statelessness."
    focus = [
        ReviewerFocusPoint(description="Validate token expiration logic", file_path="src/auth.py", related_line=45),
        ReviewerFocusPoint(description="Ensure backward compatibility of refresh token endpoint"),
    ]
    risk = "May break older clients if they do not send the Authorization header."

    md = build_explain_markdown(what, why, focus, risk)

    assert "## 🧐 Reviewer Guide" in md
    assert "### 🔍 What changes" in md
    assert what in md
    assert "### 💡 Why it changes" in md
    assert why in md
    assert "### 🎯 Where to focus review" in md
    assert "- **Validate token expiration logic** (`src/auth.py:45`)" in md
    assert "- **Ensure backward compatibility of refresh token endpoint**" in md
    assert "### ⚠️ Regression Risk" in md
    assert risk in md


def test_parse_explain_payload_valid_json():
    raw_payload = json.dumps({
        "what_changes": "Added caching for user permissions.",
        "why_it_changes": "Reduces DB queries on hot endpoints.",
        "reviewer_focus_points": [
            {"description": "Check cache invalidation on role update", "file_path": "src/roles.py", "related_line": 80}
        ],
        "regression_risk": "Stale permissions if cache invalidation fails.",
    })

    explanation = parse_explain_payload(raw_payload)

    assert explanation.what_changes == "Added caching for user permissions."
    assert explanation.why_it_changes == "Reduces DB queries on hot endpoints."
    assert len(explanation.reviewer_focus_points) == 1
    assert explanation.reviewer_focus_points[0].file_path == "src/roles.py"
    assert explanation.regression_risk == "Stale permissions if cache invalidation fails."
    assert explanation.has_sufficient_evidence is True
    assert "## 🧐 Reviewer Guide" in explanation.markdown


def test_parse_explain_payload_placeholder_detection():
    raw_payload = json.dumps({
        "what_changes": "Updated database columns.",
        "why_it_changes": "[FILL: What is the primary business motivation for this change?]",
        "reviewer_focus_points": [],
        "regression_risk": "None noted.",
    })

    explanation = parse_explain_payload(raw_payload)

    assert explanation.has_sufficient_evidence is False
    assert "[FILL:" in explanation.why_it_changes


def test_parse_explain_payload_empty():
    explanation = parse_explain_payload("")
    assert explanation.what_changes == ""
    assert explanation.has_sufficient_evidence is False
