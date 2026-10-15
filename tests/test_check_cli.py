"""CLI tests for `gitpr check` unified command."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from src.domain.check.check_types import (
    CheckFinding,
    CheckOutputFormat,
    CheckResult,
    CheckSeverity,
)
from src.main import cli


def test_check_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--help"])
    assert result.exit_code == 0
    assert "Unified CI check command" in result.output
    assert "--base" in result.output
    assert "--format" in result.output
    assert "--output" in result.output
    assert "--fail-on" in result.output
    assert "--no-ia" in result.output
    assert "--ia-only-high-risk" in result.output
    assert "--baseline" in result.output
    assert "--policy" in result.output
    assert "check-ci" in result.output


def test_check_cli_stdout_only_artifact_when_no_output_flag():
    runner = CliRunner()
    mock_result = CheckResult(
        findings=[],
        exit_code=0,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.SARIF,
        output_path=None,
        analysis_version="1.0.0",
    )

    with patch("src.application.use_cases.run_check.execute_check", return_value=mock_result):
        res = runner.invoke(cli, ["check", "--no-ia"])
        assert res.exit_code == 0
        # Output should be valid SARIF JSON
        data = json.loads(res.output)
        assert data["version"] == "2.1.0"
        assert len(data["runs"]) == 1


def test_check_cli_with_output_file():
    runner = CliRunner()
    mock_result = CheckResult(
        findings=[],
        exit_code=0,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.JSON,
        output_path="test_artifact.json",
        analysis_version="1.0.0",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "ci_results.json")
        with patch("src.application.use_cases.run_check.execute_check", return_value=mock_result):
            res = runner.invoke(cli, ["check", "--format", "json", "--output", out_file])
            assert res.exit_code == 0
            assert os.path.isfile(out_file)
            with open(out_file, "r", encoding="utf-8") as f:
                content = json.load(f)
                assert content["status"] == "success"


def test_check_cli_failing_exit_code():
    runner = CliRunner()
    finding = CheckFinding(
        fingerprint="sha256:1",
        rule_id="SEC-01",
        category="security",
        file_path="src/app.py",
        line_start=10,
        line_end=10,
        severity=CheckSeverity.ERROR,
        source="linter",
        message="Hardcoded API key",
    )
    mock_result = CheckResult(
        findings=[finding],
        exit_code=1,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.SARIF,
        output_path=None,
        analysis_version="1.0.0",
    )

    with patch("src.application.use_cases.run_check.execute_check", return_value=mock_result):
        res = runner.invoke(cli, ["check"])
        assert res.exit_code == 1


def test_check_cli_error_exit_code():
    runner = CliRunner()
    mock_result = CheckResult(
        findings=[],
        exit_code=2,
        fail_on=CheckSeverity.ERROR,
        output_format=CheckOutputFormat.SARIF,
        output_path=None,
        analysis_version="1.0.0",
        incomplete=True,
        warnings=["Corrupted baseline"],
    )

    with patch("src.application.use_cases.run_check.execute_check", return_value=mock_result):
        res = runner.invoke(cli, ["check", "--policy", "bad@1.0.0"])
        assert res.exit_code == 2
