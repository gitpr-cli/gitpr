"""Unit tests for the external linter bridge (Checkstyle XML)."""
import os
import unittest
from unittest.mock import patch, MagicMock


class TestParseCheckstyleXml(unittest.TestCase):
    """Tests for the Checkstyle XML parser."""

    def test_parses_valid_checkstyle_xml(self):
        from src.linter_engine import _parse_checkstyle_xml

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<checkstyle version="8.0">
<file name="/path/src/app.js">
<error line="10" severity="error" message="Missing semicolon"/>
<error line="20" severity="warning" message="Use const"/>
</file>
</checkstyle>"""
        results = _parse_checkstyle_xml(xml)

        self.assertEqual(len(results), 2)
        # The owning <file name=...> is carried through so callers can attribute
        # each violation to its source file, not just to a line number.
        self.assertEqual(
            results[0],
            {
                "file": "/path/src/app.js",
                "line": 10,
                "severity": "error",
                "message": "Missing semicolon",
            },
        )
        self.assertEqual(results[1]["severity"], "warning")

    def test_file_attribute_is_captured_per_file_node(self):
        from src.linter_engine import _parse_checkstyle_xml

        xml = (
            "<checkstyle>"
            '<file name="src/a.js"><error line="5" severity="error" message="A"/></file>'
            '<file name="src/b.js"><error line="5" severity="error" message="B"/></file>'
            "</checkstyle>"
        )
        results = _parse_checkstyle_xml(xml)

        self.assertEqual([r["file"] for r in results], ["src/a.js", "src/b.js"])
        self.assertEqual([r["message"] for r in results], ["A", "B"])

    def test_missing_file_attribute_yields_empty_string(self):
        from src.linter_engine import _parse_checkstyle_xml

        xml = '<checkstyle><file><error line="1" severity="error" message="X"/></file></checkstyle>'
        self.assertEqual(_parse_checkstyle_xml(xml)[0]["file"], "")


class TestCheckstyleFileMatches(unittest.TestCase):
    """Tests for attributing a Checkstyle <file name=...> to a diff path."""

    def test_absolute_report_matches_relative_target(self):
        from src.linter_engine import _checkstyle_file_matches

        self.assertTrue(
            _checkstyle_file_matches("/home/ci/repo/src/app.js", "src/app.js")
        )

    def test_windows_separators_are_normalized(self):
        from src.linter_engine import _checkstyle_file_matches

        self.assertTrue(
            _checkstyle_file_matches(r"C:\repo\src\app.js", "src/app.js")
        )

    def test_different_file_does_not_match(self):
        from src.linter_engine import _checkstyle_file_matches

        self.assertFalse(
            _checkstyle_file_matches("/repo/src/other.js", "src/app.js")
        )

    def test_sibling_with_shared_suffix_does_not_match(self):
        """'src/app.js' must not swallow 'src/vendor/myapp.js'."""
        from src.linter_engine import _checkstyle_file_matches

        self.assertFalse(
            _checkstyle_file_matches("/repo/src/vendor/myapp.js", "src/app.js")
        )

    def test_empty_report_path_is_accepted(self):
        """A linter that omits name= must not lose every violation."""
        from src.linter_engine import _checkstyle_file_matches

        self.assertTrue(_checkstyle_file_matches("", "src/app.js"))

    def test_empty_content_returns_empty_list(self):
        from src.linter_engine import _parse_checkstyle_xml

        self.assertEqual(_parse_checkstyle_xml(""), [])
        self.assertEqual(_parse_checkstyle_xml("   \n  "), [])

    def test_invalid_xml_returns_empty_list(self):
        from src.linter_engine import _parse_checkstyle_xml

        self.assertEqual(_parse_checkstyle_xml("not xml at all"), [])

    def test_non_numeric_line_is_skipped(self):
        from src.linter_engine import _parse_checkstyle_xml

        xml = '<checkstyle><file name="a.js"><error line="abc" severity="error" message="bad"/></file></checkstyle>'
        self.assertEqual(_parse_checkstyle_xml(xml), [])


class TestRunExternalLinter(unittest.TestCase):
    """Tests for the subprocess-based external linter runner."""

    @patch("src.linter_engine.subprocess.run")
    def test_returns_stdout_even_with_exit_code_1(self, mock_run):
        """Linters exit 1 when they find problems — stdout must still be returned."""
        from src.linter_engine import _run_external_linter

        mock_run.return_value = MagicMock(stdout="<checkstyle/>", returncode=1)
        result = _run_external_linter("eslint --format checkstyle", "src/app.js")

        self.assertEqual(result, "<checkstyle/>")

    @patch("src.linter_engine.shutil.which", return_value=None)
    @patch("src.linter_engine.subprocess.run")
    def test_command_includes_target_file(self, mock_run, mock_which):
        from src.linter_engine import _run_external_linter

        mock_run.return_value = MagicMock(stdout="", returncode=0)
        _run_external_linter("vendor/bin/phpcs --report=checkstyle", "src/App.php")

        args, kwargs = mock_run.call_args
        self.assertIn("src/App.php", args[0])

    @patch("src.linter_engine.shutil.which", return_value=None)
    @patch("src.linter_engine.subprocess.run")
    def test_runs_without_a_shell(self, mock_run, mock_which):
        """shell=True is the injection vector — the command must run as argv."""
        from src.linter_engine import _run_external_linter

        mock_run.return_value = MagicMock(stdout="", returncode=0)
        _run_external_linter("npx eslint --format checkstyle", "src/app.js")

        args, kwargs = mock_run.call_args
        self.assertFalse(kwargs.get("shell", False))
        self.assertIsInstance(args[0], list)
        self.assertEqual(
            args[0], ["npx", "eslint", "--format", "checkstyle", "src/app.js"]
        )

    @patch("src.linter_engine.shutil.which", return_value=None)
    @patch("src.linter_engine.subprocess.run")
    def test_shell_metacharacters_stay_literal(self, mock_run, mock_which):
        """A path with ; && | must arrive as ONE argument, never be interpreted."""
        from src.linter_engine import _run_external_linter

        mock_run.return_value = MagicMock(stdout="", returncode=0)
        hostile = "src/a; rm -rf ~ && echo pwned | tee x.js"
        _run_external_linter("eslint", hostile)

        argv = mock_run.call_args[0][0]
        self.assertEqual(argv, ["eslint", hostile])
        self.assertEqual(argv[-1], hostile)  # single literal argv element

    @patch("src.linter_engine.shutil.which", return_value=None)
    @patch("src.linter_engine.subprocess.run")
    def test_quoted_arguments_are_unquoted_once(self, mock_run, mock_which):
        from src.linter_engine import _run_external_linter

        mock_run.return_value = MagicMock(stdout="", returncode=0)
        _run_external_linter('phpcs --standard="PSR 12"', "src/App.php")

        self.assertEqual(
            mock_run.call_args[0][0],
            ["phpcs", "--standard=PSR 12", "src/App.php"],
        )

    @patch("src.linter_engine.shutil.which", return_value=r"C:\npm\npx.cmd")
    @patch("src.linter_engine.subprocess.run")
    def test_executable_is_resolved_through_which(self, mock_run, mock_which):
        """CreateProcess only appends .exe — PATHEXT shims need explicit resolution."""
        from src.linter_engine import _run_external_linter

        mock_run.return_value = MagicMock(stdout="", returncode=0)
        _run_external_linter("npx eslint", "src/app.js")

        self.assertEqual(mock_run.call_args[0][0][0], r"C:\npm\npx.cmd")

    @patch("src.linter_engine.subprocess.run")
    def test_empty_command_returns_empty_string(self, mock_run):
        from src.linter_engine import _run_external_linter

        self.assertEqual(_run_external_linter("   ", "src/app.js"), "")
        mock_run.assert_not_called()

    @patch("src.linter_engine.shutil.which", return_value=None)
    @patch("src.linter_engine.subprocess.run")
    def test_timeout_is_passed_to_subprocess(self, mock_run, mock_which):
        from src.linter_engine import _run_external_linter

        mock_run.return_value = MagicMock(stdout="", returncode=0)
        _run_external_linter("eslint", "src/app.js", timeout=7)

        self.assertEqual(mock_run.call_args.kwargs["timeout"], 7)


class TestSplitCommand(unittest.TestCase):
    """Tests for argv splitting, which must survive Windows paths."""

    def test_windows_backslash_path_is_preserved(self):
        from src.linter_engine import _split_command

        self.assertEqual(
            _split_command(r"C:\tools\lint.exe --report=checkstyle"),
            [r"C:\tools\lint.exe", "--report=checkstyle"],
        )

    def test_quoted_path_with_spaces_stays_one_token(self):
        from src.linter_engine import _split_command

        self.assertEqual(
            _split_command(r'"C:\Program Files\lint.exe" --x'),
            [r"C:\Program Files\lint.exe", "--x"],
        )

    def test_empty_string_yields_empty_list(self):
        from src.linter_engine import _split_command

        self.assertEqual(_split_command("   "), [])

    @patch("src.linter_engine.subprocess.run")
    def test_exception_returns_empty_string(self, mock_run):
        from src.linter_engine import _run_external_linter

        mock_run.side_effect = OSError("linter not found")
        self.assertEqual(_run_external_linter("missing-linter", "src/app.js"), "")


class TestDiffCrossReference(unittest.TestCase):
    """Tests that external linter errors are filtered by added lines only."""

    @patch("src.linter_engine.load_linter_rules", return_value=[])
    @patch("src.linter_engine.load_external_linters")
    @patch("src.linter_engine.log_local_metric")
    def test_errors_only_for_added_lines(self, mock_metric, mock_ext, mock_rules):
        from src.linter_engine import parse_diff_and_lint

        mock_ext.return_value = [
            {
                "name": "ESLint",
                "extensions": ["js"],
                "command": "npx eslint --format checkstyle",
            }
        ]

        # Added lines are tracked in order: +const → line 1, +console.log → line 2
        diff_text = (
            "+++ b/src/app.js\n"
            "@@ -1,5 +1,6 @@\n"
            "+const x = 1\n"
            " const y = 2\n"
            "+console.log(x)\n"
        )

        # line 3 is a legacy error NOT touched by this diff — must be ignored
        xml_output = (
            '<checkstyle><file name="src/app.js">'
            '<error line="1" severity="error" message="Semicolon required"/>'
            '<error line="2" severity="warning" message="console not allowed"/>'
            '<error line="3" severity="error" message="Legacy issue"/>'
            "</file></checkstyle>"
        )

        with patch("src.linter_engine._run_external_linter", return_value=xml_output) as mock_run:
            result = parse_diff_and_lint(diff_text)

        mock_run.assert_called_once()
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Line 1", result["errors"][0])
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn("Line 2", result["warnings"][0])

    @patch("src.linter_engine.load_linter_rules", return_value=[])
    @patch("src.linter_engine.load_external_linters")
    @patch("src.linter_engine.log_local_metric")
    def test_extension_filter_skips_unmatched_linters(self, mock_metric, mock_ext, mock_rules):
        from src.linter_engine import parse_diff_and_lint

        mock_ext.return_value = [
            {"name": "PHPCS", "extensions": ["php"], "command": "phpcs"},
        ]

        diff_text = (
            "+++ b/src/app.js\n"
            "@@ -1,1 +1,2 @@\n"
            "+const x = 1\n"
        )

        with patch("src.linter_engine._run_external_linter") as mock_run:
            result = parse_diff_and_lint(diff_text)

        mock_run.assert_not_called()
        self.assertEqual(result, {"errors": [], "warnings": []})

    @patch("src.linter_engine.load_linter_rules", return_value=[])
    @patch("src.linter_engine.load_external_linters", return_value=[])
    def test_no_rules_no_external_returns_early(self, mock_ext, mock_rules):
        """Empty rules + empty external linters short-circuits."""
        from src.linter_engine import parse_diff_and_lint

        result = parse_diff_and_lint("+++ b/src/app.py\n+print('hi')\n")
        self.assertEqual(result, {"errors": [], "warnings": []})

    @patch("src.linter_engine.load_linter_rules", return_value=[])
    @patch("src.linter_engine.load_external_linters")
    @patch("src.linter_engine.log_local_metric")
    def test_violations_from_other_files_are_not_attributed(
        self, mock_metric, mock_ext, mock_rules
    ):
        """Regression: colliding line numbers across files created false positives.

        The linter is invoked for src/app.js but its project-wide config also
        reports src/other.js at the SAME line 1.  Matching on line alone blamed
        app.js for other.js's violation; the file guard drops it.
        """
        from src.linter_engine import parse_diff_and_lint

        mock_ext.return_value = [
            {"name": "ESLint", "extensions": ["js"], "command": "npx eslint"}
        ]

        diff_text = "+++ b/src/app.js\n@@ -1,1 +1,2 @@\n+const x = 1\n"

        xml_output = (
            "<checkstyle>"
            '<file name="src/app.js">'
            '<error line="1" severity="error" message="Real issue in app"/>'
            "</file>"
            '<file name="src/other.js">'
            '<error line="1" severity="error" message="Belongs to another file"/>'
            "</file>"
            "</checkstyle>"
        )

        with patch("src.linter_engine._run_external_linter", return_value=xml_output):
            result = parse_diff_and_lint(diff_text)

        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Real issue in app", result["errors"][0])
        self.assertNotIn("Belongs to another file", " ".join(result["errors"]))


class TestFullFileExternalLinters(unittest.TestCase):
    """Tests for external linters in full-file (--input) mode."""

    @patch("src.linter_engine.load_linter_rules", return_value=[])
    @patch("src.linter_engine.load_external_linters")
    @patch("src.linter_engine.log_local_metric")
    def test_full_file_runs_external_linter(self, mock_metric, mock_ext, mock_rules):
        """--input audits the whole file, so every reported line is in scope."""
        from src.linter_engine import parse_diff_and_lint

        mock_ext.return_value = [
            {"name": "ESLint", "extensions": ["js"], "command": "npx eslint"}
        ]

        xml_output = (
            '<checkstyle><file name="/repo/src/app.js">'
            '<error line="1" severity="error" message="Semicolon required"/>'
            '<error line="99" severity="warning" message="Line 99 still counts"/>'
            "</file></checkstyle>"
        )

        with patch(
            "src.linter_engine._run_external_linter", return_value=xml_output
        ) as mock_run:
            result = parse_diff_and_lint(
                "const x = 1\n", is_full_file=True, file_path="src/app.js"
            )

        mock_run.assert_called_once()
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn("Line 99 still counts", result["warnings"][0])

    @patch("src.linter_engine.load_linter_rules", return_value=[])
    @patch("src.linter_engine.load_external_linters")
    @patch("src.linter_engine.log_local_metric")
    def test_full_file_respects_extension_filter(
        self, mock_metric, mock_ext, mock_rules
    ):
        from src.linter_engine import parse_diff_and_lint

        mock_ext.return_value = [
            {"name": "PHPCS", "extensions": ["php"], "command": "phpcs"}
        ]

        with patch("src.linter_engine._run_external_linter") as mock_run:
            result = parse_diff_and_lint(
                "const x = 1\n", is_full_file=True, file_path="src/app.js"
            )

        mock_run.assert_not_called()
        self.assertEqual(result, {"errors": [], "warnings": []})

    @patch("src.linter_engine.load_linter_rules", return_value=[])
    @patch("src.linter_engine.load_external_linters")
    @patch("src.linter_engine.log_local_metric")
    def test_full_file_malformed_xml_does_not_crash(
        self, mock_metric, mock_ext, mock_rules
    ):
        from src.linter_engine import parse_diff_and_lint

        mock_ext.return_value = [
            {"name": "ESLint", "extensions": ["js"], "command": "npx eslint"}
        ]

        with patch(
            "src.linter_engine._run_external_linter", return_value="<not-xml"
        ):
            result = parse_diff_and_lint(
                "const x = 1\n", is_full_file=True, file_path="src/app.js"
            )

        self.assertEqual(result, {"errors": [], "warnings": []})


class TestLoadExternalLinters(unittest.TestCase):
    """Tests for external linter config loading (local project + global plugins)."""

    @patch("src.config.get_linter_plugins", return_value=[])
    @patch("src.config.resolve_skill_path")
    def test_local_and_plugin_merge(self, mock_resolve, mock_plugins):
        import tempfile
        import yaml
        from src.config import load_external_linters

        with tempfile.TemporaryDirectory() as tmp:
            local = os.path.join(tmp, "local.yml")
            plugin = os.path.join(tmp, "plugin.yml")
            with open(local, "w", encoding="utf-8") as f:
                yaml.dump({"rules": [], "external_linters": [
                    {"name": "ESLint", "extensions": ["js"], "command": "eslint"}]}, f)
            with open(plugin, "w", encoding="utf-8") as f:
                yaml.dump({"external_linters": [
                    {"name": "PHPCS", "extensions": ["php"], "command": "phpcs"}]}, f)

            mock_resolve.return_value = local
            mock_plugins.return_value = [plugin]

            result = load_external_linters()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "ESLint")
        self.assertEqual(result[1]["name"], "PHPCS")


class TestGenerateLinterReportContent(unittest.TestCase):
    """Tests for the Markdown report generator.

    TRANSLATIONS is pinned to {} (English) so assertions are independent of
    the machine's OS locale — on a pt-BR machine the loaded dictionary would
    otherwise produce Portuguese report headers.
    """

    @patch("src.i18n.TRANSLATIONS", {})
    def test_report_with_errors_and_warnings(self):
        from src.linter_engine import generate_linter_report_content

        alerts = {"errors": ["- issue a"], "warnings": ["- issue b"]}
        content = generate_linter_report_content(alerts)

        self.assertIn("GitPR Linter Report", content)
        self.assertIn("- issue a", content)
        self.assertIn("- issue b", content)

    @patch("src.i18n.TRANSLATIONS", {})
    def test_report_clean(self):
        from src.linter_engine import generate_linter_report_content

        content = generate_linter_report_content({"errors": [], "warnings": []})
        self.assertIn("No violations found", content)


if __name__ == "__main__":
    unittest.main()
