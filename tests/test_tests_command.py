import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from src.main import cli


@patch("src.application.use_cases.generate_test_file.call_ai_model")
@patch("src.application.use_cases.generate_test_file.get_api_key", return_value="fake-key")
@patch("src.core.get_git_diff", return_value="diff --git a/src/user.py b/src/user.py\n+def get_user(): pass")
def test_cli_tests_generate_dry_run(mock_diff, mock_key, mock_ai):
    mock_ai.return_value = json.dumps({
        "content": "def test_get_user():\n    assert get_user() is None\n",
        "covered_scenarios": ["Should return None when user does not exist"],
        "warnings": [],
    })

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
    mock_ai.return_value = json.dumps({
        "content": "def test_applied(): assert True\n",
        "covered_scenarios": ["Applied test"],
        "warnings": [],
    })

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            ["tests", "generate", "--framework", "pytest", "--apply"],
            input="y\n",  # Confirm writing to disk
        )
        assert result.exit_code == 0
        assert "Test file successfully created" in result.output

