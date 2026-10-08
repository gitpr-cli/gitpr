"""Unit tests for git history reader with mocks and fixtures."""

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from src.infrastructure.git.risk_history_reader import (
    FileHistoryMetrics,
    read_file_git_history,
)


class TestRiskHistoryReader(unittest.TestCase):

    @patch("subprocess.run")
    def test_parses_bug_and_revert_commits_successfully(self, mock_run):
        git_log_output = """
a1b2c3d|fix: resolve authentication race condition|2026-09-01
d4e5f6a|revert: rollback broken migration|2026-09-02
789abc0|feat: add login session management|2026-09-03
1122334|hotfix(security): sanitize session cookies|2026-09-04
"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=git_log_output.strip(),
            stderr="",
        )

        metrics = read_file_git_history("src/auth.py", repo_path="/fake/repo")
        self.assertTrue(metrics.available)
        self.assertFalse(metrics.is_new_file)
        self.assertEqual(metrics.total_commits, 4)
        self.assertEqual(metrics.bug_commits, 2)  # fix: and hotfix:
        self.assertEqual(metrics.revert_commits, 1)  # revert:

    @patch("subprocess.run")
    def test_new_file_when_empty_log(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        metrics = read_file_git_history("src/brand_new.py")
        self.assertTrue(metrics.available)
        self.assertTrue(metrics.is_new_file)
        self.assertEqual(metrics.total_commits, 0)
        self.assertEqual(metrics.bug_commits, 0)

    @patch("subprocess.run")
    def test_graceful_degradation_on_subprocess_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "log"])
        metrics = read_file_git_history("src/broken.py")
        self.assertFalse(metrics.available)
        self.assertGreater(len(metrics.warnings), 0)

    @patch("subprocess.run")
    def test_graceful_degradation_when_git_missing(self, mock_run):
        mock_run.side_effect = FileNotFoundError("git not found")
        metrics = read_file_git_history("src/file.py")
        self.assertFalse(metrics.available)
        self.assertIn("unavailable", metrics.warnings[0].lower())

