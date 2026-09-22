"""Unit tests for Semgrep SAST bridge."""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.infrastructure.linter.external.semgrep_bridge import SemgrepBridge


def test_semgrep_bridge_unavailable():
    bridge = SemgrepBridge()
    with patch.object(bridge, "resolve_binary_path", return_value=None):
        res = bridge.run(target_files=["file.py"])
        assert res.available is False
        assert "not found in PATH" in res.warnings[0]


def test_semgrep_parse_output_real_fixture():
    raw_fixture = json.dumps(
        {
            "results": [
                {
                    "check_id": "python.lang.security.deserialization.pickle.avoid-pickle",
                    "path": "src/utils.py",
                    "start": {"line": 25, "col": 5},
                    "end": {"line": 25, "col": 20},
                    "extra": {
                        "message": "Avoid using pickle deserialization on untrusted input",
                        "severity": "ERROR",
                    },
                },
                {
                    "check_id": "javascript.express.security.audit.xss.direct-response-write",
                    "path": "server.js",
                    "start": {"line": 100, "col": 1},
                    "end": {"line": 102, "col": 1},
                    "extra": {
                        "message": "Direct response write may cause XSS",
                        "severity": "WARNING",
                    },
                },
            ]
        }
    )

    bridge = SemgrepBridge()
    findings = bridge.parse_output(raw_fixture, repo_path=".")

    assert len(findings) == 2
    assert findings[0].source == "semgrep"
    assert findings[0].severity == "error"
    assert findings[0].rule_id == "python.lang.security.deserialization.pickle.avoid-pickle"
    assert findings[0].file_path == "src/utils.py"
    assert findings[0].line_start == 25
    assert "Avoid using pickle" in findings[0].message

    assert findings[1].severity == "warning"
    assert findings[1].rule_id == "javascript.express.security.audit.xss.direct-response-write"
    assert findings[1].line_start == 100


def test_semgrep_run_execution():
    bridge = SemgrepBridge()
    with patch.object(bridge, "resolve_binary_path", return_value="/usr/bin/semgrep"), \
         patch("os.path.exists", return_value=True), \
         patch.object(bridge, "_execute_subprocess", return_value=('{"results": []}', "", 0, None)):

        res = bridge.run(target_files=["src/app.py"], repo_path=".")
        assert res.available is True
        assert res.findings == []

