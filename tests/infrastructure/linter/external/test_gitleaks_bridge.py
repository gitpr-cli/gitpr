"""Unit tests for Gitleaks SAST bridge."""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.infrastructure.linter.external.gitleaks_bridge import (
    GitleaksBridge,
    mask_secret_value,
)


def test_mask_secret_value():
    assert mask_secret_value("") == "[MASKED]"
    assert mask_secret_value("abc") == "****"
    assert mask_secret_value("1234") == "****"
    assert mask_secret_value("AKIA1234567890ABCDEF") == "AKIA************"


def test_gitleaks_bridge_unavailable():
    bridge = GitleaksBridge()
    with patch.object(bridge, "resolve_binary_path", return_value=None):
        res = bridge.run(target_files=["file.txt"])
        assert res.available is False
        assert "not found in PATH" in res.warnings[0]
        assert res.findings == []


def test_gitleaks_parse_output_real_fixture():
    raw_fixture = json.dumps(
        [
            {
                "Description": "AWS Access Key",
                "StartLine": 12,
                "EndLine": 12,
                "StartColumn": 1,
                "EndColumn": 20,
                "Match": "AKIAIOSFODNN7EXAMPLE",
                "Secret": "AKIAIOSFODNN7EXAMPLE",
                "File": "src/config.py",
                "RuleID": "aws-access-token",
            },
            {
                "Description": "Generic API Key",
                "StartLine": 45,
                "EndLine": 45,
                "StartColumn": 5,
                "EndColumn": 35,
                "Match": "secret_key_1234567890",
                "Secret": "secret_key_1234567890",
                "File": "app.env",
                "RuleID": "generic-api-key",
            },
        ]
    )

    bridge = GitleaksBridge()
    findings = bridge.parse_output(raw_fixture, repo_path=".")

    assert len(findings) == 2
    assert findings[0].source == "gitleaks"
    assert findings[0].severity == "error"
    assert findings[0].rule_id == "aws-access-token"
    assert findings[0].line_start == 12
    assert "AKIAIOSFODNN7EXAMPLE" not in findings[0].message
    assert "AKIA" in findings[0].message
    assert "****" in findings[0].message

    assert findings[1].rule_id == "generic-api-key"
    assert findings[1].line_start == 45


def test_gitleaks_run_execution():
    bridge = GitleaksBridge()
    with patch.object(bridge, "resolve_binary_path", return_value="/usr/bin/gitleaks"), \
         patch("os.path.exists", return_value=True), \
         patch.object(bridge, "_execute_subprocess", return_value=("", "", 0, None)), \
         patch("builtins.open", MagicMock()):

        res = bridge.run(target_files=["test.py"], repo_path=".")
        assert res.available is True

