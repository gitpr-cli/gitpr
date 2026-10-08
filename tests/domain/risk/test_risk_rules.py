"""Unit tests for pattern matching, critical paths, and config loading."""

import tempfile
import unittest
from src.domain.risk.risk_rules import (
    RiskConfig,
    is_non_executable_file,
    is_test_file,
    load_risk_config,
    matches_pattern,
    resolve_risk_level,
)
from src.domain.risk.risk_types import RiskLevel, RiskSignal


class TestRiskRules(unittest.TestCase):

    def test_matches_pattern_case_insensitive_and_glob(self):
        self.assertTrue(matches_pattern("app/Http/Middleware/VerifyCsrf.php", "**/middleware/**"))
        self.assertTrue(matches_pattern("SRC/AUTH/LOGIN.PY", "**/auth/**"))
        self.assertTrue(matches_pattern(".github/workflows/ci.yml", ".github/workflows/**"))
        self.assertTrue(matches_pattern("database/migrations/001_create_users.sql", "**/migration/**"))
        self.assertFalse(matches_pattern("src/utils/math.py", "**/auth/**"))

    def test_non_executable_file_detection(self):
        self.assertTrue(is_non_executable_file("README.md"))
        self.assertTrue(is_non_executable_file("docs/architecture.txt"))
        self.assertTrue(is_non_executable_file("Pipfile.lock"))
        self.assertTrue(is_non_executable_file("package-lock.json"))
        self.assertTrue(is_non_executable_file("assets/logo.png"))
        self.assertFalse(is_non_executable_file("src/main.py"))
        self.assertFalse(is_non_executable_file("app/Http/Kernel.php"))

    def test_is_test_file(self):
        self.assertTrue(is_test_file("tests/test_core.py"))
        self.assertTrue(is_test_file("tests/Unit/UserTest.php"))
        self.assertTrue(is_test_file("src/services/api.test.ts"))
        self.assertTrue(is_test_file("pkg/server/server_test.go"))
        self.assertFalse(is_test_file("src/services/api.ts"))
        self.assertFalse(is_test_file("src/core.py"))

    def test_load_risk_config_from_custom_yaml(self):
        yaml_content = """
risk:
  analysis_version: "2.0"
  thresholds:
    low_max: 30
    medium_max: 60
    high_max: 85
  weights:
    critical_path: 35
    no_test_change: 20
    test_present: -15
"""
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False, encoding="utf-8") as tmp:
            tmp.write(yaml_content)
            tmp_path = tmp.name

        cfg = load_risk_config(tmp_path)
        self.assertEqual(cfg.analysis_version, "2.0")
        self.assertEqual(cfg.thresholds["low_max"], 30.0)
        self.assertEqual(cfg.weights[RiskSignal.CRITICAL_PATH], 35.0)
        self.assertEqual(cfg.weights[RiskSignal.NO_TEST_CHANGE], 20.0)
        self.assertEqual(cfg.weights[RiskSignal.TEST_PRESENT], -15.0)

    def test_negative_weights_ignored_for_non_mitigating_signals(self):
        yaml_content = """
risk:
  weights:
    critical_path: -50
    test_present: -15
"""
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False, encoding="utf-8") as tmp:
            tmp.write(yaml_content)
            tmp_path = tmp.name

        cfg = load_risk_config(tmp_path)
        # critical_path cannot be negative, should keep default
        self.assertEqual(cfg.weights[RiskSignal.CRITICAL_PATH], 25.0)
        # test_present is mitigating, allowed
        self.assertEqual(cfg.weights[RiskSignal.TEST_PRESENT], -15.0)

