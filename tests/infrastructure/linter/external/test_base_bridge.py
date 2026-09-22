"""Unit tests for base bridge and data classes."""

import pytest
from unittest.mock import patch, MagicMock
import subprocess
from src.infrastructure.linter.external.base_bridge import (
    ExternalLinterBridge,
    ExternalLinterResult,
    NormalizedFinding,
)


class DummyBridge(ExternalLinterBridge):
    tool_name = "dummy"
    binary_name = "dummy-bin"

    def run(self, target_files, repo_path=".", diff_only=True, timeout=60):
        return ExternalLinterResult(
            tool_name=self.tool_name,
            available=self.is_available(),
            findings=[],
        )

    def parse_output(self, raw_output, repo_path="."):
        return []


def test_base_bridge_availability():
    bridge = DummyBridge()
    with patch("shutil.which", return_value=None):
        assert bridge.is_available() is False
        assert bridge.resolve_binary_path() is None

    with patch("shutil.which", return_value="/usr/bin/dummy-bin"):
        assert bridge.is_available() is True
        assert bridge.resolve_binary_path() == "/usr/bin/dummy-bin"


def test_base_bridge_subprocess_timeout():
    bridge = DummyBridge()
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["dummy"], timeout=5)):
        stdout, stderr, code, err = bridge._execute_subprocess(["dummy"], timeout=5)
        assert err == "Execution timed out after 5 seconds"
        assert stdout == ""
        assert code is None


def test_base_bridge_subprocess_file_not_found():
    bridge = DummyBridge()
    with patch("subprocess.run", side_effect=FileNotFoundError):
        stdout, stderr, code, err = bridge._execute_subprocess(["dummy"])
        assert "not found" in err


def test_base_bridge_subprocess_success():
    bridge = DummyBridge()
    mock_res = MagicMock()
    mock_res.stdout = "dummy stdout"
    mock_res.stderr = ""
    mock_res.returncode = 0

    with patch("subprocess.run", return_value=mock_res) as mock_run:
        stdout, stderr, code, err = bridge._execute_subprocess(["dummy", "arg1"])
        assert err is None
        assert stdout == "dummy stdout"
        assert code == 0
        mock_run.assert_called_once_with(
            ["dummy", "arg1"],
            cwd=None,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=60,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )

