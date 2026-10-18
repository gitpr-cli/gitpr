from unittest.mock import patch
from src.application.use_cases.generate_pr_explanation import generate_pr_explanation


@patch("src.application.use_cases.generate_pr_explanation.call_ai_model")
@patch("src.application.use_cases.generate_pr_explanation.get_api_key", return_value="dummy-key")
def test_generate_pr_explanation_success(mock_key, mock_ai):
    # call_ai_model returns a parsed dict, not a JSON string.
    mock_ai.return_value = {
        "what_changes": "Implements rate limiting on the login route.",
        "why_it_changes": "Mitigates brute-force credential stuffing attacks.",
        "reviewer_focus_points": [
            {"description": "Verify Redis key expiration time", "file_path": "src/auth/limiter.py", "related_line": 25}
        ],
        "regression_risk": "Legitimate users behind shared IPs could be temporarily throttled.",
    }

    diff = "diff --git a/src/auth/limiter.py b/src/auth/limiter.py\n+def rate_limit(): pass"
    result = generate_pr_explanation(diff, ai_provider="gemini")

    assert result.what_changes == "Implements rate limiting on the login route."
    assert result.has_sufficient_evidence is True
    assert len(result.reviewer_focus_points) == 1
    assert "## 🧐 Reviewer Guide" in result.markdown


def test_generate_pr_explanation_empty_diff():
    result = generate_pr_explanation("")
    assert result.what_changes == ""
    assert result.has_sufficient_evidence is False


@patch("src.application.use_cases.generate_pr_explanation.call_ai_model")
@patch("src.application.use_cases.generate_pr_explanation.get_api_key", return_value=None)
def test_generate_pr_explanation_without_api_key(mock_key, mock_ai, capsys):
    result = generate_pr_explanation("diff --git a/x b/x\n+change", ai_provider="gemini")

    assert result.markdown == ""
    assert result.has_sufficient_evidence is False
    assert "No API key configured for gemini" in capsys.readouterr().err
    mock_ai.assert_not_called()

