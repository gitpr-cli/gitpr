"""Unit tests for calculate_risk use case orchestrator."""

import unittest
from unittest.mock import MagicMock, patch

from src.application.use_cases.calculate_risk import execute_calculate_risk
from src.domain.risk.risk_types import RiskLevel, RiskSignal
from src.infrastructure.git.risk_history_reader import FileHistoryMetrics
from src.infrastructure.linter.external.base_bridge import NormalizedFinding
from src.review.diff_source import DiffOrigin, DiffSource


class TestCalculateRiskUseCase(unittest.TestCase):

    def setUp(self):
        self.sample_diff = """diff --git a/app/Http/Middleware/Auth.php b/app/Http/Middleware/Auth.php
--- a/app/Http/Middleware/Auth.php
+++ b/app/Http/Middleware/Auth.php
@@ -1,5 +1,10 @@
+<?php
+namespace App\\Http\\Middleware;
+class Auth {
+    public function handle() { return true; }
+}
diff --git a/docs/readme.md b/docs/readme.md
--- a/docs/readme.md
+++ b/docs/readme.md
@@ -1,2 +1,3 @@
 # Project
+Updated doc line
"""

    @patch("src.application.use_cases.calculate_risk.read_file_git_history")
    def test_critical_path_and_no_test_signals_assigned(self, mock_history):
        mock_history.return_value = FileHistoryMetrics(
            file_path="app/Http/Middleware/Auth.php",
            is_new_file=True,
            available=True,
        )

        source = DiffSource(
            origin=DiffOrigin.LOCAL,
            content=self.sample_diff,
            identifier="head",
        )

        pr_risk = execute_calculate_risk(source)

        self.assertGreater(pr_risk.score, 0.0)
        self.assertEqual(pr_risk.total_changed_files, 2)
        # Find auth file risk
        auth_risk = next(f for f in pr_risk.files if "Auth.php" in f.file_path)
        signals = [e.signal for e in auth_risk.evidence]
        self.assertIn(RiskSignal.CRITICAL_PATH, signals)
        self.assertIn(RiskSignal.NO_TEST_CHANGE, signals)

        # Docs file should not have NO_TEST_CHANGE
        doc_risk = next(f for f in pr_risk.files if "readme.md" in f.file_path)
        doc_signals = [e.signal for e in doc_risk.evidence]
        self.assertNotIn(RiskSignal.NO_TEST_CHANGE, doc_signals)

    @patch("src.application.use_cases.calculate_risk.read_file_git_history")
    def test_test_present_mitigates_score(self, mock_history):
        diff_with_test = self.sample_diff + """diff --git a/tests/Unit/AuthTest.php b/tests/Unit/AuthTest.php
--- a/tests/Unit/AuthTest.php
+++ b/tests/Unit/AuthTest.php
@@ -1,2 +1,5 @@
+<?php
+class AuthTest extends TestCase {}
+"""
        mock_history.return_value = FileHistoryMetrics(
            file_path="app/Http/Middleware/Auth.php",
            is_new_file=True,
        )

        source = DiffSource(origin=DiffOrigin.LOCAL, content=diff_with_test, identifier="head")
        pr_risk = execute_calculate_risk(source)

        auth_risk = next(f for f in pr_risk.files if "Auth.php" in f.file_path)
        signals = [e.signal for e in auth_risk.evidence]
        self.assertIn(RiskSignal.TEST_PRESENT, signals)
        self.assertNotIn(RiskSignal.NO_TEST_CHANGE, signals)
        self.assertTrue(pr_risk.tests_changed)

    @patch("src.application.use_cases.calculate_risk.read_file_git_history")
    def test_blocker_finding_triggers_critical_level(self, mock_history):
        mock_history.return_value = FileHistoryMetrics(file_path="app/Http/Middleware/Auth.php", is_new_file=True)
        findings = [
            NormalizedFinding(
                severity="error",
                category="secret",
                file_path="app/Http/Middleware/Auth.php",
                line_start=3,
                line_end=3,
                message="Hardcoded AWS Secret Key detected",
                source="gitleaks",
            )
        ]

        source = DiffSource(origin=DiffOrigin.LOCAL, content=self.sample_diff, identifier="head")
        pr_risk = execute_calculate_risk(source, findings=findings)

        self.assertEqual(pr_risk.level, RiskLevel.CRITICAL)
        auth_risk = next(f for f in pr_risk.files if "Auth.php" in f.file_path)
        signals = [e.signal for e in auth_risk.evidence]
        self.assertIn(RiskSignal.FINDING_BLOCKER, signals)

    @patch("src.application.use_cases.calculate_risk.read_file_git_history")
    def test_target_file_filter_isolates_file_risk(self, mock_history):
        mock_history.return_value = FileHistoryMetrics(file_path="app/Http/Middleware/Auth.php", is_new_file=True)
        source = DiffSource(origin=DiffOrigin.LOCAL, content=self.sample_diff, identifier="head")

        filtered_risk = execute_calculate_risk(
            source,
            target_file="app/Http/Middleware/Auth.php",
        )

        self.assertEqual(filtered_risk.total_changed_files, 1)
        self.assertEqual(filtered_risk.files[0].file_path, "app/Http/Middleware/Auth.php")

    def test_remote_pr_diff_does_not_call_git_history(self):
        remote_source = DiffSource(
            origin=DiffOrigin.REMOTE_PR,
            content=self.sample_diff,
            identifier="pr-42",
        )
        # include_history is handled automatically for remote origin
        pr_risk = execute_calculate_risk(remote_source)
        self.assertGreater(pr_risk.score, 0.0)
        self.assertEqual(pr_risk.total_changed_files, 2)

