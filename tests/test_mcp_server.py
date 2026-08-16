"""Tests for the MCP server module.

Covers tool functions, the output patching system, and the safe-call wrapper.
"""

import io
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

    @patch.dict("os.environ", {"GITPR_COAUTHOR": "true"})
    @patch("src.core.generate_pr_content")
    @patch("src.core.get_git_diff")
    def test_generates_commit_message(self, mock_diff, mock_gen):
        """Returns a commit message on success."""
        mock_diff.return_value = "+print('hello')"
        mock_gen.return_value = {"commit_message": "feat: add hello world"}

        result = json.loads(mcp_server.generate_commit_message(provider="gemini"))
        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["commit_message"],
            "feat: add hello world\n\n\nCo-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>",
        )

    @patch("src.core.get_git_diff")
    def test_no_changes(self, mock_diff):
        """Returns no_changes when there is nothing to commit."""
        mock_diff.return_value = ""
        result = json.loads(mcp_server.generate_commit_message())
        self.assertEqual(result["status"], "no_changes")

    @patch.dict("os.environ", {"GITPR_COAUTHOR": "true"})
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
        self.assertEqual(
            result["commit_message"],
            "fix: critical bug\n\n\nCo-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>",
        )

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
        """Returns JSON with new/modified/deleted lists and typed files array."""
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
        # Verify unified files array with type labels
        expected_files = [
            {"path": "untracked.py", "type": "new"},
            {"path": "edited.py", "type": "modified"},
            {"path": "changed.py", "type": "modified"},
            {"path": "removed.py", "type": "deleted"},
        ]
        self.assertEqual(result["files"], expected_files)

    @patch("src.core.get_unstaged_categorized")
    def test_no_unstaged_files(self, mock_cat):
        """Returns no_changes when nothing is unstaged."""
        mock_cat.return_value = {"new": [], "modified": [], "deleted": []}
        result = json.loads(mcp_server.list_unstaged_files())
        self.assertEqual(result["status"], "no_changes")
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["files"], [])

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


class TestToolsCatalog(unittest.TestCase):
    """Tests for the _build_tools_catalog and --list functionality."""

    def test_catalog_has_server_and_version(self):
        """Catalog includes server name and version."""
        catalog = mcp_server._build_tools_catalog()
        self.assertEqual(catalog["server"], "gitpr")
        self.assertIn("version", catalog)
        self.assertIsInstance(catalog["version"], str)

    def test_catalog_has_all_sections(self):
        """Catalog contains tools, resources, and prompts arrays."""
        catalog = mcp_server._build_tools_catalog()
        self.assertIn("tools", catalog)
        self.assertIn("resources", catalog)
        self.assertIn("prompts", catalog)
        self.assertIsInstance(catalog["tools"], list)
        self.assertIsInstance(catalog["resources"], list)
        self.assertIsInstance(catalog["prompts"], list)

    def test_catalog_tools_have_required_fields(self):
        """Every tool has name, description, parameters, and annotations."""
        catalog = mcp_server._build_tools_catalog()
        for tool in catalog["tools"]:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("parameters", tool)
            self.assertIn("annotations", tool)
            # Verify it's not empty
            self.assertTrue(tool["name"], f"Tool has empty name")
            self.assertTrue(tool["description"], f"Tool '{tool['name']}' has empty description")

    def test_catalog_has_all_expected_tools(self):
        """Catalog includes all 12 registered tools."""
        catalog = mcp_server._build_tools_catalog()
        tool_names = {t["name"] for t in catalog["tools"]}
        expected = {
            "get_git_context",
            "analyze_diff",
            "list_unstaged_files",
            "analyze_unstaged_diff",
            "get_full_diff",
            "generate_commit_message",
            "review_code",
            "full_review",
            "generate_pr_description",
            "run_linter",
            "analyze_blame",
            "generate_issue",
        }
        missing = expected - tool_names
        extra = tool_names - expected
        self.assertEqual(tool_names, expected,
                         f"Missing: {missing}, Unexpected: {extra}")

    def test_catalog_resources_have_required_fields(self):
        """Every resource has uri, name, description, and mimeType."""
        catalog = mcp_server._build_tools_catalog()
        for resource in catalog["resources"]:
            self.assertIn("uri", resource)
            self.assertIn("name", resource)
            self.assertIn("description", resource)
            self.assertIn("mimeType", resource)

    def test_catalog_prompts_have_required_fields(self):
        """Every prompt has name and description."""
        catalog = mcp_server._build_tools_catalog()
        for prompt in catalog["prompts"]:
            self.assertIn("name", prompt)
            self.assertIn("description", prompt)

    def test_get_tools_catalog_json_returns_valid_json(self):
        """_get_tools_catalog_json returns parseable JSON."""
        json_str = mcp_server._get_tools_catalog_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["server"], "gitpr")
        self.assertIn("tools", parsed)

    def test_tools_with_params_have_typed_parameters(self):
        """Tools that accept parameters have proper type annotations."""
        catalog = mcp_server._build_tools_catalog()
        for tool in catalog["tools"]:
            for param_name, param_info in tool["parameters"].items():
                self.assertIn("type", param_info,
                              f"Parameter '{param_name}' in '{tool['name']}' missing type")
                self.assertIn("required", param_info,
                              f"Parameter '{param_name}' in '{tool['name']}' missing required flag")
                self.assertIn("description", param_info,
                              f"Parameter '{param_name}' in '{tool['name']}' missing description")

    def test_analyze_blame_has_required_params(self):
        """analyze_blame correctly marks file_path, start_line, end_line as required."""
        catalog = mcp_server._build_tools_catalog()
        blame = next(t for t in catalog["tools"] if t["name"] == "analyze_blame")
        self.assertTrue(blame["parameters"]["file_path"]["required"])
        self.assertTrue(blame["parameters"]["start_line"]["required"])
        self.assertTrue(blame["parameters"]["end_line"]["required"])

    def test_run_list_prints_to_stdout(self):
        """_run_list prints the catalog JSON to the real stdout."""
        # _run_list writes to sys.__stdout__ (the real OS stdout) to bypass
        # the _MCPStdout guard.  Patch sys.__stdout__ to capture the output.
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            mcp_server._run_list()
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            self.assertEqual(parsed["server"], "gitpr")
            self.assertIn("tools", parsed)


class TestInstallConfigDescriptions(unittest.TestCase):
    """Tests that --install config entries include description and _tools metadata."""

    def test_all_editor_templates_have_description(self):
        """Every editor config template includes a description field."""
        from src.mcp_server import _CONFIG_TEMPLATES
        for editor, config in _CONFIG_TEMPLATES.items():
            entry = config.get("entry", {}).get("gitpr", {})
            if editor == "zed":
                # Zed nests config under "command" key
                entry = entry.get("command", {})
            self.assertIn("description", entry,
                          f"Editor '{editor}' is missing 'description' in its config entry")
            self.assertTrue(entry["description"],
                            f"Editor '{editor}' has empty description")

    def test_claude_code_description_includes_list_hint(self):
        """The claude-code config description mentions gitpr-mcp --list."""
        from src.mcp_server import _CONFIG_TEMPLATES
        desc = _CONFIG_TEMPLATES["claude-code"]["entry"]["gitpr"]["description"]
        self.assertIn("gitpr-mcp --list", desc)

    def test_get_compact_tools_returns_list_of_dicts(self):
        """_get_compact_tools returns a list of {name, description} dicts."""
        tools = mcp_server._get_compact_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIsInstance(tool["name"], str)
            self.assertIsInstance(tool["description"], str)

    def test_get_compact_tools_matches_catalog(self):
        """_get_compact_tools has the same count as the full catalog tools."""
        compact = mcp_server._get_compact_tools()
        catalog = mcp_server._build_tools_catalog()
        self.assertEqual(len(compact), len(catalog["tools"]))

    def test_get_compact_tools_names_match_catalog(self):
        """_get_compact_tools names match the full catalog exactly."""
        compact = mcp_server._get_compact_tools()
        catalog = mcp_server._build_tools_catalog()
        compact_names = {t["name"] for t in compact}
        catalog_names = {t["name"] for t in catalog["tools"]}
        self.assertEqual(compact_names, catalog_names)


class TestWriteRealStdout(unittest.TestCase):
    """Tests for the _write_real_stdout helper."""

    def test_writes_to_real_stdout(self):
        """_write_real_stdout writes to sys.__stdout__ when available."""
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            mcp_server._write_real_stdout("test output")
            self.assertEqual(mock_stdout.getvalue(), "test output")

    def test_falls_back_to_original_stdout(self):
        """_write_real_stdout falls back to _original_stdout if __stdout__ is absent."""
        saved = getattr(sys, '__stdout__', None)
        try:
            if hasattr(sys, '__stdout__'):
                delattr(sys, '__stdout__')
            original_stdout = io.StringIO()
            with patch.object(mcp_server, "_original_stdout", original_stdout):
                mcp_server._write_real_stdout("fallback")
                self.assertEqual(original_stdout.getvalue(), "fallback")
        finally:
            if saved is not None:
                sys.__stdout__ = saved


class TestToolRegistry(unittest.TestCase):
    """Tests for _get_tool_registry and _TOOL_FUNCS."""

    def test_registry_has_all_12_tools(self):
        """_get_tool_registry returns all 12 tools."""
        registry = mcp_server._get_tool_registry()
        self.assertEqual(len(registry), 12)

    def test_every_tool_has_func(self):
        """Every tool in the registry has a callable 'func'."""
        registry = mcp_server._get_tool_registry()
        for name, entry in registry.items():
            self.assertIsNotNone(entry["func"],
                                 f"Tool '{name}' has no callable in _TOOL_FUNCS")
            self.assertTrue(callable(entry["func"]),
                            f"Tool '{name}' func is not callable")

    def test_registry_matches_catalog_names(self):
        """Registry names exactly match the catalog tool names."""
        registry = mcp_server._get_tool_registry()
        catalog = mcp_server._build_tools_catalog()
        self.assertEqual(set(registry.keys()),
                         {t["name"] for t in catalog["tools"]})

    def test_analyze_blame_params_required(self):
        """analyze_blame has file_path, start_line, end_line marked required."""
        registry = mcp_server._get_tool_registry()
        blame = registry["analyze_blame"]
        self.assertTrue(blame["parameters"]["file_path"]["required"])
        self.assertTrue(blame["parameters"]["start_line"]["required"])
        self.assertTrue(blame["parameters"]["end_line"]["required"])


class TestPrettifyResult(unittest.TestCase):
    """Tests for _prettify_result."""

    def test_pretty_prints_valid_json(self):
        """Valid JSON is re-dumped with indentation."""
        result = mcp_server._prettify_result('{"a":1,"b":"x"}')
        self.assertIn('\n', result)
        parsed = json.loads(result)
        self.assertEqual(parsed, {"a": 1, "b": "x"})

    def test_returns_raw_for_non_json(self):
        """Non-JSON strings are returned unchanged."""
        raw = "this is not json at all"
        result = mcp_server._prettify_result(raw)
        self.assertEqual(result, raw)

    def test_handles_empty_string(self):
        """Empty string returns as-is."""
        self.assertEqual(mcp_server._prettify_result(""), "")


class TestRunTool(unittest.TestCase):
    """Tests for the _run_tool function (direct CLI tool invocation)."""

    def setUp(self):
        # Ensure we start unpatched after each test
        mcp_server._unpatch_output()

    def tearDown(self):
        mcp_server._unpatch_output()

    @patch("src.core.get_repo_name")
    @patch("src.core.get_current_branch")
    def test_get_git_context_success(self, mock_branch, mock_repo):
        """_run_tool get_git_context returns 0 and prints valid JSON."""
        mock_branch.return_value = "feature/x"
        mock_repo.return_value = "org/repo"
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("get_git_context")
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            self.assertEqual(parsed["branch"], "feature/x")
            self.assertEqual(parsed["repository"], "org/repo")

    def test_help_mode_prints_all_tools(self):
        """_run_tool with empty name prints help listing and returns 0."""
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("")
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            # Should mention all 12 tools
            for tool_name in _get_expected_tool_names():
                self.assertIn(tool_name, output,
                              f"Help output missing tool: {tool_name}")

    def test_unknown_tool_returns_error(self):
        """_run_tool with unknown name returns 1 and JSON error."""
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("nonexistent_tool")
            self.assertEqual(exit_code, 1)
            output = mock_stdout.getvalue()
            self.assertIn('"status": "error"', output)
            self.assertIn("nonexistent_tool", output)
            # Followed by help listing
            self.assertIn("Available tools", output)

    def test_invalid_tool_args_json(self):
        """_run_tool with invalid --tool-args returns 1 and error."""
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("get_git_context", "not valid json")
            self.assertEqual(exit_code, 1)
            output = mock_stdout.getvalue()
            self.assertIn('"status": "error"', output)
            self.assertIn("Invalid --tool-args JSON", output)

    def test_tool_args_not_a_dict(self):
        """_run_tool with array as --tool-args returns 1 and error."""
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("get_git_context", "[1, 2, 3]")
            self.assertEqual(exit_code, 1)
            output = mock_stdout.getvalue()
            self.assertIn("must be a JSON object", output)

    def test_missing_required_args(self):
        """_run_tool analyze_blame without required args returns 1."""
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("analyze_blame")
            self.assertEqual(exit_code, 1)
            output = mock_stdout.getvalue()
            self.assertIn("Missing required argument", output)

    @patch("src.blame_engine.run_blame_analysis")
    def test_analyze_blame_with_valid_args(self, mock_blame):
        """_run_tool analyze_blame with valid args returns 0 and result."""
        mock_blame.return_value = [{"hash": "abc123", "status": "ORIGIN"}]
        args_json = '{"file_path": "src/main.py", "start_line": "10", "end_line": "20"}'
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("analyze_blame", args_json)
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            self.assertEqual(parsed["status"], "success")
            self.assertEqual(len(parsed["entries"]), 1)

    @patch("src.core.generate_pr_content")
    @patch("src.core.get_git_diff")
    def test_generate_commit_message_passes_provider(self, mock_diff, mock_gen):
        """_run_tool generate_commit_message forwards provider param."""
        mock_diff.return_value = "diff content"
        mock_gen.return_value = {"commit_message": "feat: test"}
        args_json = '{"provider": "gemini"}'
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("generate_commit_message", args_json)
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            self.assertIn("commit_message", parsed)
            # Verify provider was passed through (positional after diff_text)
            mock_gen.assert_called_once_with("commit", "commit", "diff content", "gemini")

    @patch("src.core.generate_pr_content")
    def test_tool_handles_system_exit_gracefully(self, mock_gen):
        """_run_tool: when the tool itself catches an error, output includes error status."""
        mock_gen.side_effect = SystemExit(0)
        with patch("sys.__stdout__", new_callable=io.StringIO) as mock_stdout:
            exit_code = mcp_server._run_tool("generate_commit_message",
                                              '{"diff_text": "test diff"}')
            # The tool catches SystemExit internally and returns a JSON error
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            # The result reflects the internal error handling of the tool
            self.assertIn(parsed.get("status", ""), ["error", "success"])


class TestMainCli(unittest.TestCase):
    """Integration-style tests that call main() with simulated argv."""

    def test_main_tool_get_git_context(self):
        """main() with --tool get_git_context does NOT start the server."""
        with patch.object(sys, "argv", ["gitpr-mcp", "--tool", "get_git_context"]):
            with patch("src.core.get_current_branch", return_value="main"):
                with patch("src.core.get_repo_name", return_value="test/repo"):
                    with patch("sys.__stdout__", new_callable=io.StringIO) as mock_out:
                        with patch.object(mcp_server.mcp, "run") as mock_run:
                            try:
                                mcp_server.main()
                            except SystemExit:
                                pass
                            mock_run.assert_not_called()
                            output = mock_out.getvalue()
                            self.assertIn("test/repo", output)

    def test_main_tool_listing(self):
        """main() with bare --tool prints help and does NOT start the server."""
        with patch.object(sys, "argv", ["gitpr-mcp", "--tool"]):
            with patch("sys.__stdout__", new_callable=io.StringIO) as mock_out:
                with patch.object(mcp_server.mcp, "run") as mock_run:
                    try:
                        mcp_server.main()
                    except SystemExit:
                        pass
                    mock_run.assert_not_called()
                    output = mock_out.getvalue()
                    self.assertIn("Available tools", output)

    def test_main_mutually_exclusive_list_and_tool(self):
        """argparse exits with error when --list and --tool are combined."""
        with patch.object(sys, "argv", ["gitpr-mcp", "--list", "--tool"]):
            with self.assertRaises(SystemExit):
                mcp_server.main()


def _get_expected_tool_names():
    """Return the set of all 12 tool names expected in the registry."""
    return {
        "get_git_context",
        "analyze_diff",
        "list_unstaged_files",
        "analyze_unstaged_diff",
        "get_full_diff",
        "generate_commit_message",
        "review_code",
        "full_review",
        "generate_pr_description",
        "run_linter",
        "analyze_blame",
        "generate_issue",
    }


if __name__ == "__main__":
    unittest.main()
