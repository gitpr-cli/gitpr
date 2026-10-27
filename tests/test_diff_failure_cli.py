"""A git failure must not be reported as an empty branch diff.

get_git_full_diff() returns None when git fails. The PR/review/fullreview flow
used to fold that into the same "no new code found" message a genuinely empty
diff produces; the two now have different exit codes.
"""
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from src.main import cli


class TestDiffFailureExitCode(unittest.TestCase):
    def _invoke(self, diff):
        with patch("src.main.get_git_full_diff", return_value=diff), patch(
            "src.main.setup_environment"
        ), patch("src.main.check_and_update_hooks_scripts"):
            return CliRunner().invoke(cli, ["--no-unstaged-check"])

    def test_git_failure_exits_non_zero(self):
        result = self._invoke(None)
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertNotIn("No new code found", result.output)

    def test_empty_diff_still_reports_no_new_code(self):
        result = self._invoke("")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("No new code found", result.output)

    def test_hook_mode_fails_open(self):
        # A non-zero prepare-commit-msg hook aborts the user's commit, so a git
        # failure there must not be turned into a non-zero exit.
        with patch("src.main.get_git_diff", return_value=None), patch(
            "src.main.setup_environment"
        ), patch("src.main.check_and_update_hooks_scripts"):
            result = CliRunner().invoke(
                cli, ["-c", "--hook", "--no-unstaged-check"]
            )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("No new code found", result.output)


if __name__ == "__main__":
    unittest.main()
