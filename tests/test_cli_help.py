import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src import ledger
from src.main import cli


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Ensure tests run in an isolated environment without writing to real user config."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("GITPR_SKIP_PROJECT_CONFIG_SEED", "1")
    ledger.configure_terminal(interactive=False, quiet=True)
    yield tmp_path


def test_help_flag_before_subcommand_config():
    """`gitpr -h config` must display `gitpr config` help and exit 0 without opening TUI."""
    runner = CliRunner()
    with patch("src.ui.config_app.launch_config_app") as mock_launch:
        result = runner.invoke(cli, ["-h", "config"], prog_name="gitpr")
        assert result.exit_code == 0
        assert not mock_launch.called, "launch_config_app should not be called when -h is passed"
        assert "Usage: gitpr config" in result.output
        assert "config-tui" in result.output


def test_help_long_flag_before_subcommand_config():
    """`gitpr --help config` must display `gitpr config` help and exit 0 without opening TUI."""
    runner = CliRunner()
    with patch("src.ui.config_app.launch_config_app") as mock_launch:
        result = runner.invoke(cli, ["--help", "config"], prog_name="gitpr")
        assert result.exit_code == 0
        assert not mock_launch.called
        assert "Usage: gitpr config" in result.output


def test_help_flag_after_subcommand_config():
    """`gitpr config -h` must continue to display `gitpr config` help and exit 0."""
    runner = CliRunner()
    with patch("src.ui.config_app.launch_config_app") as mock_launch:
        result = runner.invoke(cli, ["config", "-h"], prog_name="gitpr")
        assert result.exit_code == 0, f"Output was: {result.output}\nException was: {result.exception}"
        assert not mock_launch.called
        assert "Usage: gitpr config" in result.output


def test_help_flag_before_subcommand_release():
    """`gitpr -h release` must display `gitpr release` help and exit 0."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-h", "release"], prog_name="gitpr")
    assert result.exit_code == 0
    assert "Usage: gitpr release" in result.output


def test_help_flag_nested_subcommand():
    """`gitpr -h metrics export` must display leaf command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-h", "metrics", "export"], prog_name="gitpr")
    assert result.exit_code == 0, f"Output was: {result.output}\nException was: {result.exception}"
    assert "Usage: gitpr metrics export" in result.output


def test_help_flag_group_without_subcommand():
    """`gitpr -h metrics` must display group help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-h", "metrics"], prog_name="gitpr")
    assert result.exit_code == 0
    assert "Usage: gitpr metrics" in result.output


def test_plain_help_flag():
    """`gitpr -h` alone displays root help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-h"], prog_name="gitpr")
    assert result.exit_code == 0
    assert "Usage: gitpr" in result.output


def test_contextual_help_flag_commit():
    """`gitpr -h -c` displays contextual help for commit flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-h", "-c"], prog_name="gitpr")
    assert result.exit_code == 0
    assert "AI Commit Message Generation" in result.output
