"""Tests for the MCP Prompts (message templates for common flows)."""

import unittest
from src import mcp_server


class TestMCPPrompts(unittest.TestCase):
    """Tests for the 7 MCP prompt functions."""

    def test_review_pr_prompt_returns_string(self):
        """Review PR prompt returns a non-empty string."""
        result = mcp_server.review_pr_prompt()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)
        self.assertIn("review", result.lower())

    def test_generate_commit_message_prompt_returns_string(self):
        """Generate Commit Message prompt references Conventional Commits."""
        result = mcp_server.generate_commit_message_prompt()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)
        self.assertIn("commit", result.lower())

    def test_create_pr_description_prompt_returns_string(self):
        """Create PR Description prompt returns a non-empty string."""
        result = mcp_server.create_pr_description_prompt()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)
        self.assertIn("pull request", result.lower())

    def test_run_linter_prompt_returns_string(self):
        """Run Linter prompt references linter violations."""
        result = mcp_server.run_linter_prompt()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)
        self.assertIn("lint", result.lower())

    def test_create_issue_prompt_returns_string(self):
        """Create Issue prompt references the What/Why/Where/How format."""
        result = mcp_server.create_issue_prompt()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)
        self.assertIn("what", result.lower())

    def test_trace_code_origin_prompt_returns_string(self):
        """Trace Code Origin prompt references git blame."""
        result = mcp_server.trace_code_origin_prompt()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)
        self.assertIn("git", result.lower())

    def test_explore_project_prompt_returns_string(self):
        """Explore Project Context prompt references branch and skills."""
        result = mcp_server.explore_project_prompt()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)
        self.assertIn("branch", result.lower())

    def test_all_prompts_are_unique(self):
        """No two prompts return the same message text."""
        prompts = [
            mcp_server.review_pr_prompt(),
            mcp_server.generate_commit_message_prompt(),
            mcp_server.create_pr_description_prompt(),
            mcp_server.run_linter_prompt(),
            mcp_server.create_issue_prompt(),
            mcp_server.trace_code_origin_prompt(),
            mcp_server.explore_project_prompt(),
        ]
        self.assertEqual(len(prompts), len(set(prompts)))


if __name__ == "__main__":
    unittest.main()
