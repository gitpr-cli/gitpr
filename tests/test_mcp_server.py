"""Tests for the MCP server module.

Covers tool functions, the output patching system, and the safe-call wrapper.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Import after patching checks — the mcp_server module does not call
# _patch_output() at import time (only inside main()), so importing is safe.
from src import mcp_server


class TestSafeCall(unittest.TestCase):
    """Tests for the _safe_call wrapper."""

    def test_returns_value_on_success(self):
        """_safe_call returns the function's return value."""
        result = mcp_server._safe_call(lambda: 42)
        self.assertEqual(result, 42)

    def test_returns_none_on_system_exit(self):
        """_safe_call catches SystemExit and returns None."""
        def boom():
            raise SystemExit(1)
        result = mcp_server._safe_call(boom)
        self.assertIsNone(result)

    def test_returns_none_on_exception(self):
        """_safe_call catches any Exception and returns None."""
        def oops():
            raise ValueError("something broke")
        result = mcp_server._safe_call(oops)
        self.assertIsNone(result)


class TestOutputPatching(unittest.TestCase):
    """Tests for the _patch_output / _unpatch_output system."""

    def setUp(self):
        # Ensure we start unpatched
        mcp_server._unpatch_output()

    def tearDown(self):
        mcp_server._unpatch_output()

    def test_patch_replaces_stdout(self):
        """_patch_output replaces sys.stdout with _MCPStdout."""
        mcp_server._patch_output()
        self.assertIsInstance(sys.stdout, mcp_server._MCPStdout)

    def test_patch_redirects_write_to_stderr(self):
        """_MCPStdout.write sends text to stderr."""
        mcp_server._patch_output()
        with patch.object(sys.stderr, 'write') as mock_stderr:
            sys.stdout.write("hello")
            mock_stderr.assert_called_once_with("hello")

    def test_unpatch_restores_stdout(self):
        """_unpatch_output restores sys.stdout to a non-_MCPStdout object."""
        mcp_server._patch_output()
        self.assertIsInstance(sys.stdout, mcp_server._MCPStdout)
        mcp_server._unpatch_output()
        # After unpatch, stdout should no longer be our redirect wrapper.
        # Note: pytest may wrap sys.stdout in an EncodedFile, so we just
        # verify the _MCPStdout wrapper is gone.
        self.assertNotIsInstance(sys.stdout, mcp_server._MCPStdout)

    def test_patch_neutralises_sys_exit(self):
        """After patching, sys.exit raises SystemExit instead of terminating."""
        mcp_server._patch_output()
        with self.assertRaises(SystemExit):
            sys.exit(1)

    def test_unpatch_restores_sys_exit(self):
        """After unpatched, sys.exit behaves normally."""
        mcp_server._patch_output()
        mcp_server._unpatch_output()
        # sys.exit should be the original (would really exit, but we can check identity)
        self.assertIs(sys.exit, mcp_server._original_exit)


class TestGitContextTool(unittest.TestCase):
    """Tests for the get_git_context MCP tool."""

    @patch("src.core.get_repo_name")
    @patch("src.core.get_current_branch")
    def test_returns_branch_and_repo(self, mock_branch, mock_repo):
        """Returns JSON with branch and repository info."""
        mock_branch.return_value = "feature/login"
        mock_repo.return_value = "natanfiuza/gitpr"

        result = json.loads(mcp_server.get_git_context())
        self.assertEqual(result["branch"], "feature/login")
        self.assertEqual(result["repository"], "natanfiuza/gitpr")

    @patch("src.core.get_repo_name")
    @patch("src.core.get_current_branch")
    def test_fallback_on_error(self, mock_branch, mock_repo):
        """Returns 'unknown' when git commands fail."""
        mock_branch.side_effect = Exception("git failed")
        mock_repo.side_effect = Exception("git failed")

        result = json.loads(mcp_server.get_git_context())
        self.assertEqual(result["branch"], "unknown")
        self.assertEqual(result["repository"], "unknown/repo")


class TestAnalyzeDiffTool(unittest.TestCase):
    """Tests for the analyze_diff MCP tool."""

    @patch("src.core.get_git_diff")
    def test_no_changes(self, mock_diff):
        """Returns no_changes status when there is no diff."""
        mock_diff.return_value = ""
        result = json.loads(mcp_server.analyze_diff())
        self.assertEqual(result["status"], "no_changes")

    @patch("src.core.get_git_diff")
    def test_with_changes(self, mock_diff):
        """Returns the diff content."""
        diff_content = "diff --git a/file.py b/file.py\n+print('hello')"
        mock_diff.return_value = diff_content
        result = json.loads(mcp_server.analyze_diff())
        self.assertEqual(result["status"], "changes_found")
        self.assertIn("diff --git a/file.py", result["diff"])


class TestLinterTool(unittest.TestCase):
    """Tests for the run_linter MCP tool."""

    @patch("src.linter_engine.parse_diff_and_lint")
    @patch("src.core.get_git_diff")
    def test_passes_when_no_errors(self, mock_diff, mock_lint):
        """Returns passed=True when linter finds no errors."""
        mock_diff.return_value = "+print('hello')"
        mock_lint.return_value = {"errors": [], "warnings": []}

        result = json.loads(mcp_server.run_linter())
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["passed"])
        self.assertEqual(result["error_count"], 0)

    @patch("src.linter_engine.parse_diff_and_lint")
    @patch("src.core.get_git_diff")
    def test_fails_when_errors_exist(self, mock_diff, mock_lint):
        """Returns passed=False when errors are found."""
        mock_diff.return_value = "+console.log('debug')"
        mock_lint.return_value = {
            "errors": ["console.log() found on line 1"],
            "warnings": ["Consider adding a docstring"],
        }

        result = json.loads(mcp_server.run_linter())
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["passed"])
        self.assertEqual(result["error_count"], 1)
        self.assertEqual(result["warning_count"], 1)

    @patch("src.core.get_git_diff")
    def test_empty_diff(self, mock_diff):
        """Returns no_changes when diff is empty."""
        mock_diff.return_value = ""
        result = json.loads(mcp_server.run_linter())
        self.assertEqual(result["status"], "no_changes")


class TestCommitMessageTool(unittest.TestCase):
    """Tests for the generate_commit_message MCP tool."""

    @patch("src.core.generate_pr_content")
    @patch("src.core.get_git_diff")
    def test_generates_commit_message(self, mock_diff, mock_gen):
        """Returns a commit message on success."""
        mock_diff.return_value = "+print('hello')"
        mock_gen.return_value = {"commit_message": "feat: add hello world"}

        result = json.loads(mcp_server.generate_commit_message(provider="gemini"))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["commit_message"], "feat: add hello world")

    @patch("src.core.get_git_diff")
    def test_no_changes(self, mock_diff):
        """Returns no_changes when there is nothing to commit."""
        mock_diff.return_value = ""
        result = json.loads(mcp_server.generate_commit_message())
        self.assertEqual(result["status"], "no_changes")

    @patch("src.core.generate_pr_content")
    @patch("src.core.get_git_diff")
    def test_uses_provided_diff(self, mock_diff, mock_gen):
        """Uses the provided diff_text when given."""
        mock_gen.return_value = {"commit_message": "fix: critical bug"}
        custom_diff = "diff --git a/x.py b/x.py\n-foo\n+bar"

        result = json.loads(mcp_server.generate_commit_message(
            provider="deepseek", diff_text=custom_diff
        ))
        mock_diff.assert_not_called()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["commit_message"], "fix: critical bug")

    @patch("src.core.generate_pr_content")
    @patch("src.core.get_git_diff")
    def test_handles_ai_failure(self, mock_diff, mock_gen):
        """Returns error status when AI fails."""
        mock_diff.return_value = "+some code"
        mock_gen.return_value = None

        result = json.loads(mcp_server.generate_commit_message())
        self.assertEqual(result["status"], "error")


class TestReviewCodeTool(unittest.TestCase):
    """Tests for the review_code MCP tool."""

    @patch("src.core.generate_pr_content")
    @patch("src.core.get_git_diff")
    def test_generates_review(self, mock_diff, mock_gen):
        """Returns a review on success."""
        mock_diff.return_value = "+new feature"
        mock_gen.return_value = {"review": "## Code Review\n\nLooks good!"}

        result = json.loads(mcp_server.review_code(provider="gemini"))
        self.assertEqual(result["status"], "success")
        self.assertIn("Code Review", result["review"])

    @patch("src.core.get_git_diff")
    def test_no_changes(self, mock_diff):
        """Returns no_changes when diff is empty."""
        mock_diff.return_value = ""
        result = json.loads(mcp_server.review_code())
        self.assertEqual(result["status"], "no_changes")


class TestPRDescriptionTool(unittest.TestCase):
    """Tests for the generate_pr_description MCP tool."""

    @patch("src.core.generate_pr_content")
    @patch("src.core.get_git_full_diff")
    def test_generates_pr(self, mock_diff, mock_gen):
        """Returns PR description and commit message."""
        mock_diff.return_value = "diff content"
        mock_gen.return_value = {
            "commit_message": "feat: new feature",
            "pr_description": "## Summary\n\nThis PR adds...",
        }

        result = json.loads(mcp_server.generate_pr_description(provider="deepseek"))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["commit_message"], "feat: new feature")
        self.assertIn("Summary", result["pr_description"])


class TestListUnstagedFilesTool(unittest.TestCase):
    """Tests for the list_unstaged_files MCP tool."""

    @patch("src.core.get_unstaged_categorized")
    def test_returns_categorized_lists(self, mock_cat):
        """Returns JSON with new/modified/deleted lists."""
        mock_cat.return_value = {
            "new": ["untracked.py"],
            "modified": ["edited.py", "changed.py"],
            "deleted": ["removed.py"],
        }
        result = json.loads(mcp_server.list_unstaged_files())
        self.assertEqual(result["status"], "changes_found")
        self.assertEqual(result["new"], ["untracked.py"])
        self.assertEqual(result["modified"], ["edited.py", "changed.py"])
        self.assertEqual(result["deleted"], ["removed.py"])
        self.assertEqual(result["total"], 4)

    @patch("src.core.get_unstaged_categorized")
    def test_no_unstaged_files(self, mock_cat):
        """Returns no_changes when nothing is unstaged."""
        mock_cat.return_value = {"new": [], "modified": [], "deleted": []}
        result = json.loads(mcp_server.list_unstaged_files())
        self.assertEqual(result["status"], "no_changes")
        self.assertEqual(result["total"], 0)

    @patch("src.core.get_unstaged_categorized")
    def test_handles_none_from_core(self, mock_cat):
        """Handles None return from core function gracefully."""
        mock_cat.return_value = None
        result = json.loads(mcp_server.list_unstaged_files())
        self.assertEqual(result["status"], "no_changes")
        self.assertEqual(result["new"], [])
        self.assertEqual(result["modified"], [])
        self.assertEqual(result["deleted"], [])


class TestAnalyzeUnstagedDiffTool(unittest.TestCase):
    """Tests for the analyze_unstaged_diff MCP tool."""

    @patch("src.core.get_unstaged_diff")
    def test_returns_unstaged_diff(self, mock_diff):
        """Returns only unstaged diff content."""
        mock_diff.return_value = "diff --git a/x.py b/x.py\n-old\n+new"
        result = json.loads(mcp_server.analyze_unstaged_diff())
        self.assertEqual(result["status"], "changes_found")
        self.assertIn("diff --git a/x.py", result["diff"])

    @patch("src.core.get_unstaged_diff")
    def test_no_unstaged_changes(self, mock_diff):
        """Returns no_changes when working tree is clean."""
        mock_diff.return_value = ""
        result = json.loads(mcp_server.analyze_unstaged_diff())
        self.assertEqual(result["status"], "no_changes")

    @patch("src.core.get_unstaged_diff")
    def test_handles_none_from_core(self, mock_diff):
        """Handles None return from core function gracefully."""
        mock_diff.return_value = None
        result = json.loads(mcp_server.analyze_unstaged_diff())
        self.assertEqual(result["status"], "no_changes")


class TestBlameTool(unittest.TestCase):
    """Tests for the analyze_blame MCP tool."""

    @patch("src.blame_engine.run_blame_analysis")
    def test_analyzes_blame(self, mock_blame):
        """Returns blame analysis entries."""
        mock_blame.return_value = [
            {"hash": "abc123", "classification": "ORIGIN", "message": "Initial commit"},
            {"hash": "def456", "classification": "REFACTORING", "message": "Refactor"},
        ]

        with patch.object(os.path, "exists", return_value=True):
            result = json.loads(mcp_server.analyze_blame(
                file_path="src/main.py",
                start_line="10",
                end_line="20",
            ))

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["entries"]), 2)
        self.assertEqual(result["entries"][0]["classification"], "ORIGIN")

    def test_file_not_found(self):
        """Returns error when the file does not exist."""
        with patch.object(os.path, "exists", return_value=False):
            result = json.loads(mcp_server.analyze_blame(
                file_path="nonexistent.py",
                start_line="1",
                end_line="10",
            ))
        self.assertEqual(result["status"], "error")
        # Message is i18n-aware; just verify it contains the file path
        self.assertIn("nonexistent.py", result["message"])

    @patch("src.blame_engine.run_blame_analysis")
    def test_no_traceable_commits(self, mock_blame):
        """Returns no_data when no commits found."""
        mock_blame.return_value = None
        with patch.object(os.path, "exists", return_value=True):
            result = json.loads(mcp_server.analyze_blame(
                file_path="src/main.py",
                start_line="1",
                end_line="1",
            ))
        self.assertEqual(result["status"], "no_data")


class TestIssueTool(unittest.TestCase):
    """Tests for the generate_issue MCP tool."""

    @patch("src.issue_engine.generate_issue_content")
    @patch("src.core.get_git_diff")
    def test_generates_issue_from_diff(self, mock_diff, mock_gen):
        """Generates issue from diff context."""
        mock_diff.return_value = "+new feature"
        mock_gen.return_value = {
            "titulo": "Add user authentication",
            "corpo": "## What\n\n...\n## Why\n\n...",
        }

        result = json.loads(mcp_server.generate_issue(context_type="diff"))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "Add user authentication")
        self.assertIn("What", result["body"])

    @patch("src.core.get_branch_history_text")
    @patch("src.issue_engine.generate_issue_content")
    def test_generates_issue_from_history(self, mock_gen, mock_history):
        """Generates epic issue from branch history."""
        mock_history.return_value = "history content"
        mock_gen.return_value = {
            "titulo": "Epic: Dashboard v2",
            "corpo": "## Context\n\n...",
        }

        result = json.loads(mcp_server.generate_issue(context_type="history"))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "Epic: Dashboard v2")

    @patch("src.core.get_git_diff")
    def test_no_context(self, mock_diff):
        """Returns no_changes when no context is available."""
        mock_diff.return_value = ""
        result = json.loads(mcp_server.generate_issue())
        self.assertEqual(result["status"], "no_changes")


class TestResources(unittest.TestCase):
    """Tests for MCP resources (skill templates)."""

    @patch("src.mcp_server._read_resource_file")
    def test_list_skills(self, mock_read):
        """list_skills returns all skill URIs."""
        result = json.loads(mcp_server.list_skills())
        self.assertIn("skills", result)
        self.assertIn("skill://pr", result["skills"])
        self.assertIn("skill://commit", result["skills"])
        self.assertIn("skill://review", result["skills"])
        self.assertIn("skill://filereview", result["skills"])
        self.assertIn("skill://issue", result["skills"])
        self.assertIn("skill://blame", result["skills"])
        self.assertIn("linter", result)
        self.assertEqual(result["linter"], "linter://config")

    def test_skill_resources_exist(self):
        """Verify all resource handler functions are defined."""
        funcs = [
            mcp_server.get_skill_pr,
            mcp_server.get_skill_commit,
            mcp_server.get_skill_review,
            mcp_server.get_skill_filereview,
            mcp_server.get_skill_issue,
            mcp_server.get_skill_blame,
            mcp_server.get_linter_config,
        ]
        for fn in funcs:
            self.assertTrue(callable(fn), f"{fn} should be callable")


class TestResolveProvider(unittest.TestCase):
    """Tests for the _resolve_provider helper."""

    @patch("src.config.get_ai_provider")
    def test_returns_explicit_provider(self, mock_get):
        """Returns the explicitly requested provider."""
        result = mcp_server._resolve_provider("deepseek")
        self.assertEqual(result, "deepseek")
        mock_get.assert_not_called()

    @patch("src.config.get_ai_provider")
    def test_falls_back_to_default(self, mock_get):
        """Falls back to the .env default when no provider specified."""
        mock_get.return_value = "gemini"
        result = mcp_server._resolve_provider("")
        self.assertEqual(result, "gemini")

    @patch("src.config.get_ai_provider")
    def test_ultimate_fallback(self, mock_get):
        """Returns 'gemini' when everything fails."""
        mock_get.side_effect = Exception("no config")
        result = mcp_server._resolve_provider("")
        self.assertEqual(result, "gemini")


if __name__ == "__main__":
    unittest.main()
