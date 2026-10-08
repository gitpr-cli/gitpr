"""CLI tests for gitpr risk command."""

import json
import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from src.main import cli


class TestRiskCli(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.sample_diff = """diff --git a/src/auth.py b/src/auth.py
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,3 +1,5 @@
+def login():
+    pass
"""

    @patch("src.main.get_git_diff")
    @patch("src.main.get_git_full_diff")
    @patch("src.application.use_cases.calculate_risk.read_file_git_history")
    def test_risk_cli_text_output(self, mock_history, mock_full, mock_diff):
        mock_diff.return_value = self.sample_diff
        mock_history.return_value = MagicMock(
            available=True,
            is_new_file=True,
            total_commits=0,
            bug_commits=0,
            revert_commits=0,
            warnings=[],
        )

        result = self.runner.invoke(cli, ["risk"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("GITPR LOCAL RISK ASSESSMENT", result.output)
        self.assertIn("Risk Level:", result.output)
        self.assertIn("src/auth.py", result.output)

    @patch("src.main.get_git_diff")
    @patch("src.main.get_git_full_diff")
    @patch("src.application.use_cases.calculate_risk.read_file_git_history")
    def test_risk_cli_json_output(self, mock_history, mock_full, mock_diff):
        mock_diff.return_value = self.sample_diff
        mock_history.return_value = MagicMock(
            available=True,
            is_new_file=True,
            total_commits=0,
            bug_commits=0,
            revert_commits=0,
            warnings=[],
        )

        result = self.runner.invoke(cli, ["risk", "--format", "json"])

        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("score", data)
        self.assertIn("level", data)
        self.assertIn("files", data)
        self.assertIn("analysis_version", data)
        self.assertEqual(data["analysis_version"], "1.0")
        self.assertEqual(len(data["files"]), 1)
        self.assertEqual(data["files"][0]["file_path"], "src/auth.py")

    @patch("src.main.get_git_diff")
    @patch("src.main.get_git_full_diff")
    def test_risk_cli_empty_diff_handling(self, mock_full, mock_diff):
        mock_diff.return_value = ""
        mock_full.return_value = ""

        result = self.runner.invoke(cli, ["risk"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("No diff found", result.output)

    @patch("src.main.get_git_diff")
    @patch("src.main.get_git_full_diff")
    @patch("src.application.use_cases.calculate_risk.read_file_git_history")
    def test_risk_cli_filter_file(self, mock_history, mock_full, mock_diff):
        multi_diff = self.sample_diff + """diff --git a/src/utils.py b/src/utils.py
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,2 +1,4 @@
+def helper():
+    pass
"""
        mock_diff.return_value = multi_diff
        mock_history.return_value = MagicMock(
            available=True,
            is_new_file=True,
            total_commits=0,
            bug_commits=0,
            revert_commits=0,
            warnings=[],
        )

        result = self.runner.invoke(cli, ["risk", "--file", "src/auth.py"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("src/auth.py", result.output)
        self.assertNotIn("src/utils.py", result.output)

