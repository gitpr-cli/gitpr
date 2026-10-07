"""CLI integration tests for GitPR Junior Mentor Mode (--mentor and gitpr mentor)."""
import unittest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from src.application.use_cases.generate_mentor_explanation import MentorRun
from src.domain.mentor.mentor_explanation_builder import MentorExplanation
from src.main import cli


def _fake_mentor_run():
    exp = MentorExplanation(
        finding_id="FIX-001",
        what_is_happening="Explanation of what happened",
        why_it_matters="Explanation of why it matters",
        analogy="Everyday analogy",
        learn_more_pointer="Topic to learn",
        has_sufficient_evidence=True,
        markdown="### 💡 FIX-001 · style · src/foo.py:10\n> Original technical message\n\n**What:** Explanation",
    )
    return MentorRun(
        explanations=(exp,),
        skipped_ids=(),
        markdown="## 🎓 Mentor (Junior Guidance)\n\n### 💡 FIX-001 · style · src/foo.py:10\n> Original technical message\n\n**What:** Explanation",
    )


class TestMentorCli(unittest.TestCase):
    @patch("src.main.render_review_result")
    @patch("src.main.parse_diff_and_lint", return_value={"errors": [], "warnings": []})
    @patch("src.main.generate_pr_content")
    @patch("src.core.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")
    @patch("src.main._append_mentor_section")
    def test_review_without_mentor_is_opt_in(
        self, mock_append, mock_diff, mock_gen_pr, mock_linter, mock_render
    ):
        mock_gen_pr.return_value = {"review": "Original code review content."}
        runner = CliRunner()
        result = runner.invoke(cli, ["-r", "--no-unstaged-check"])

        self.assertEqual(result.exit_code, 0)
        mock_append.assert_not_called()
        mock_render.assert_called_once()
        args, _ = mock_render.call_args
        self.assertEqual(args[0], "Original code review content.")

    @patch("src.main.render_review_result")
    @patch("src.main.parse_diff_and_lint", return_value={"errors": [], "warnings": []})
    @patch("src.main.generate_pr_content")
    @patch("src.core.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")
    @patch("src.main._append_mentor_section")
    def test_review_with_mentor_flag_invokes_append(
        self, mock_append, mock_diff, mock_gen_pr, mock_linter, mock_render
    ):
        mock_gen_pr.return_value = {"review": "Original code review content."}
        mock_append.return_value = "Original code review content.\n\n---\n\n## 🎓 Mentor (Junior Guidance)"

        runner = CliRunner()
        result = runner.invoke(cli, ["-r", "--mentor", "--no-unstaged-check"])

        self.assertEqual(result.exit_code, 0)
        mock_append.assert_called_once()
        mock_render.assert_called_once()
        args, _ = mock_render.call_args
        self.assertIn("Original code review content.", args[0])
        self.assertIn("## 🎓 Mentor", args[0])

    @patch("src.application.use_cases.generate_mentor_explanation.explain_review")
    @patch("src.fix.apply_fix.resolve_review")
    def test_standalone_mentor_command_success(self, mock_resolve, mock_explain):
        mock_resolve.return_value = {"action_type": "review", "response": {"review": "Text"}}
        mock_explain.return_value = _fake_mentor_run()

        runner = CliRunner()
        result = runner.invoke(cli, ["mentor"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("JUNIOR MENTOR GUIDANCE", result.output)
        self.assertIn("FIX-001", result.output)
        self.assertIn("Original technical message", result.output)
        mock_explain.assert_called_once()

    @patch("src.application.use_cases.generate_mentor_explanation.explain_review")
    @patch("src.fix.apply_fix.resolve_review")
    def test_standalone_mentor_command_with_finding_id(self, mock_resolve, mock_explain):
        mock_resolve.return_value = {"action_type": "review", "response": {"review": "Text"}}
        mock_explain.return_value = _fake_mentor_run()

        runner = CliRunner()
        result = runner.invoke(cli, ["mentor", "--finding", "FIX-001"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("JUNIOR MENTOR GUIDANCE", result.output)
        mock_explain.assert_called_once()
        _, kwargs = mock_explain.call_args
        self.assertEqual(kwargs.get("finding_id"), "FIX-001")


if __name__ == "__main__":
    unittest.main()

