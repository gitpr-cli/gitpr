"""Unit tests for the issue engine (skill feedback + Smart Excludes metadata)."""
import unittest
from unittest.mock import patch


class TestIssueSkillAndSmartExcludes(unittest.TestCase):
    """Tests skill loading and excluded-docs metadata in generate_issue_content."""

    def _run_issue(self, skill_content="", changed_docs=None, context_type="diff"):
        """Runs generate_issue_content with external calls mocked.

        Returns (mock_skill, mock_docs, mock_ai, mock_secho) for assertions.
        """
        from src.issue_engine import generate_issue_content

        with patch("src.issue_engine.get_ai_provider", return_value="gemini"), \
             patch("src.issue_engine.get_api_key", return_value="fake-key"), \
             patch("src.issue_engine.get_api_model", return_value="gemini-pro-latest"), \
             patch("src.issue_engine.get_cached_response", return_value=None), \
             patch("src.issue_engine.save_cached_response"), \
             patch("src.issue_engine.get_skill_context") as mock_skill, \
             patch("src.issue_engine.get_changed_docs_list") as mock_docs, \
             patch("src.issue_engine.call_ai_model") as mock_ai, \
             patch("src.issue_engine.click.secho") as mock_secho, \
             patch("src.metrics.log_command_metric"):

            mock_skill.return_value = skill_content
            mock_docs.return_value = changed_docs or []
            mock_ai.return_value = {"titulo": "T", "corpo": "C"}

            generate_issue_content("some diff text", context_type=context_type)

        return mock_skill, mock_docs, mock_ai, mock_secho

    def test_skill_loaded_via_get_skill_context_and_used(self):
        """get_skill_context('issue') must be called once; its content is the sys_inst."""
        mock_skill, _, mock_ai, _ = self._run_issue(skill_content="CUSTOM ISSUE SKILL")

        mock_skill.assert_called_once_with("issue")
        sys_inst = mock_ai.call_args[0][4]
        self.assertEqual(sys_inst, "CUSTOM ISSUE SKILL")

    def test_default_persona_used_when_skill_missing(self):
        """Empty skill context must fall back to the Software Architect persona."""
        from src.i18n import __

        _, _, mock_ai, _ = self._run_issue(skill_content="")

        sys_inst = mock_ai.call_args[0][4]
        expected = __(
            "You are a Software Architect. Follow the What / Why / Where / How format to document the Issue."
        )
        self.assertEqual(sys_inst, expected)

    def test_diff_context_adds_excluded_docs_section(self):
        """Diff context with changed docs: section reaches the AI and the message is printed."""
        from src.i18n import __

        _, mock_docs, mock_ai, mock_secho = self._run_issue(
            skill_content="SKILL", changed_docs=["docs/guide.md", "README.md"]
        )

        mock_docs.assert_called_once()
        sys_inst = mock_ai.call_args[0][4]
        self.assertIn(
            __("Changed documentation (content excluded from diff):\n"), sys_inst
        )
        self.assertIn("- docs/guide.md", sys_inst)
        self.assertIn("- README.md", sys_inst)

        expected_msg = __(
            "📄 {count} documentation file(s) excluded from diff (Smart Excludes).",
            count=2,
        )
        messages = [str(c.args[0]) for c in mock_secho.call_args_list]
        self.assertIn(expected_msg, messages)

    def test_non_diff_contexts_skip_docs_metadata(self):
        """History/blame contexts must not query or inject excluded docs."""
        _, mock_docs, mock_ai, _ = self._run_issue(
            skill_content="SKILL", changed_docs=["docs/guide.md"], context_type="history"
        )

        mock_docs.assert_not_called()
        self.assertEqual(mock_ai.call_args[0][4], "SKILL")


if __name__ == "__main__":
    unittest.main()
