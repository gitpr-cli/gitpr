import json
from unittest.mock import patch
from click.testing import CliRunner
from src.main import cli


@patch("src.application.use_cases.generate_pr_explanation.call_ai_model")
@patch("src.application.use_cases.generate_pr_explanation.get_api_key", return_value="fake-key")
@patch("src.core.get_git_diff", return_value="diff --git a/src/core.py b/src/core.py\n+def new_feature(): pass")
def test_cli_explain_standalone_success(mock_diff, mock_key, mock_ai):
    mock_ai.return_value = json.dumps({
        "what_changes": "Adds new feature helper in core.",
        "why_it_changes": "Simplifies helper lookup.",
        "reviewer_focus_points": [{"description": "Verify function return type", "file_path": "src/core.py"}],
        "regression_risk": "Low.",
    })

    runner = CliRunner()
    result = runner.invoke(cli, ["explain"])

    assert result.exit_code == 0
    assert "REVIEWER GUIDE (Explain My PR)" in result.output
    assert "What changes:" in result.output
    assert "Adds new feature helper in core." in result.output
    assert "Why it changes:" in result.output
    assert "Where to focus review:" in result.output


@patch("src.core.get_git_diff", return_value="")
def test_cli_explain_empty_diff(mock_diff):
    runner = CliRunner()
    result = runner.invoke(cli, ["explain"])
    assert result.exit_code != 0
    assert "No diff found" in result.output

