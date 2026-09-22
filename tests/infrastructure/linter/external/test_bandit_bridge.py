"""Unit tests for Bandit SAST bridge."""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.infrastructure.linter.external.bandit_bridge import BanditBridge


def test_bandit_bridge_unavailable():
    bridge = BanditBridge()
    with patch.object(bridge, "resolve_binary_path", return_value=None):
        res = bridge.run(target_files=["file.py"])
        assert res.available is False
        assert "not found in PATH" in res.warnings[0]


def test_bandit_skips_non_python_files():
    bridge = BanditBridge()
    with patch.object(bridge, "resolve_binary_path", return_value="/usr/bin/bandit"), \
         patch.object(bridge, "_execute_subprocess") as mock_exec:
        res = bridge.run(target_files=["file.js", "style.css", "README.md"])
        assert res.available is True
        assert res.findings == []
        mock_exec.assert_not_called()


def test_bandit_parse_output_real_fixture():
    raw_fixture = json.dumps(
        {
            "results": [
                {
                    "code": "eval('2 + 2')",
                    "filename": "src/core.py",
                    "issue_confidence": "HIGH",
                    "issue_severity": "HIGH",
                    "issue_text": "Use of possibly insecure function - eval was detected.",
                    "line_number": 88,
                    "line_range": [88],
                    "test_id": "B307",
                    "test_name": "blacklist",
                },
                {
                    "code": "subprocess.Popen(cmd, shell=True)",
                    "filename": "src/utils.py",
                    "issue_confidence": "HIGH",
                    "issue_severity": "MEDIUM",
                    "issue_text": "subprocess call with shell=True identified.",
                    "line_number": 140,
                    "line_range": [140, 141],
                    "test_id": "B602",
                    "test_name": "subprocess_popen_with_shell_equals_true",
                },
            ]
        }
    )

    bridge = BanditBridge()
    findings = bridge.parse_output(raw_fixture, repo_path=".")

    assert len(findings) == 2
    assert findings[0].source == "bandit"
    assert findings[0].severity == "error"  # HIGH severity + HIGH confidence
    assert findings[0].rule_id == "B307"
    assert findings[0].file_path == "src/core.py"
    assert findings[0].line_start == 88
    assert "eval was detected" in findings[0].message

    assert findings[1].severity == "warning"  # MEDIUM severity
    assert findings[1].rule_id == "B602"
    assert findings[1].line_start == 140

