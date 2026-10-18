from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from src.main import cli


@patch("src.application.use_cases.generate_test_file.call_ai_model")
@patch("src.application.use_cases.generate_test_file.get_api_key", return_value="fake-key")
@patch("src.core.get_git_diff", return_value="diff --git a/src/user.py b/src/user.py\n+def get_user(): pass")
def test_cli_tests_generate_dry_run(mock_diff, mock_key, mock_ai):
    # call_ai_model returns a parsed dict, not a JSON string.
    mock_ai.return_value = {
        "content": "def test_get_user():\n    assert get_user() is None\n",
        "covered_scenarios": ["Should return None when user does not exist"],
        "warnings": [],
    }

    runner = CliRunner()
    result = runner.invoke(cli, ["tests", "generate", "--framework", "pytest"])

    assert result.exit_code == 0
    assert "Target Framework: PYTEST" in result.output
    assert "Covered Scenarios:" in result.output
    assert "Dry-run mode" in result.output


@patch("src.application.use_cases.generate_test_file.call_ai_model")
@patch("src.application.use_cases.generate_test_file.get_api_key", return_value="fake-key")
@patch("src.core.get_git_diff", return_value="+new code")
def test_cli_tests_generate_apply(mock_diff, mock_key, mock_ai, tmp_path):
    mock_ai.return_value = {
        "content": "def test_applied(): assert True\n",
        "covered_scenarios": ["Applied test"],
        "warnings": [],
    }

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            ["tests", "generate", "--framework", "pytest", "--apply"],
            input="y\n",  # Confirm writing to disk
        )
        assert result.exit_code == 0
        assert "Test file successfully created" in result.output


@patch("src.application.use_cases.generate_test_file.call_ai_model")
@patch("src.application.use_cases.generate_test_file.get_api_key", return_value="fake-key")
@patch("src.fix.apply_fix.find_candidate")
@patch("src.fix.apply_fix.collect_candidates", return_value=[])
@patch("src.fix.apply_fix.resolve_review", return_value=object())
def test_cli_tests_generate_from_finding(
    mock_review, mock_collect, mock_find, mock_key, mock_ai, tmp_path
):
    """--finding reads suggested_test and diff_unified from the candidate."""
    candidate = MagicMock()
    candidate.suggested_test = "assert get_user() is None"
    candidate.diff_unified = "--- a/src/user.py\n+++ b/src/user.py\n+def get_user(): pass"
    candidate.finding.id = "FIX-001"
    candidate.finding.message = "Missing test for get_user"
    candidate.finding.file_path = "src/user.py"
    candidate.finding.line_start = 10
    candidate.finding.line_end = 12
    candidate.finding.severity = "high"
    candidate.finding.category = "testing"
    mock_find.return_value = candidate
    mock_ai.return_value = {
        "content": "def test_get_user():\n    assert get_user() is None\n",
        "covered_scenarios": ["Finding regression"],
        "warnings": [],
    }

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            ["tests", "generate", "--finding", "FIX-001", "--framework", "pytest"],
        )

    assert result.exit_code == 0
    assert "Target Finding: FIX-001" in result.output
    prompt = mock_ai.call_args.kwargs["prompt"]
    assert "assert get_user() is None" in prompt
    assert "+++ b/src/user.py" in prompt


def test_cli_tests_help_links_to_docs():
    runner = CliRunner()

    group_help = runner.invoke(cli, ["tests", "--help"])
    generate_help = runner.invoke(cli, ["tests", "generate", "--help"])

    assert group_help.exit_code == 0
    assert "/docs/tests-generate" in group_help.output
    assert generate_help.exit_code == 0
    assert "/docs/tests-generate" in generate_help.output

