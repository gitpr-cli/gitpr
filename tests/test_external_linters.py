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
        self.assertEqual(results[0], {"line": 10, "severity": "error", "message": "Missing semicolon"})
        self.assertEqual(results[1]["severity"], "warning")

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

    @patch("src.linter_engine.subprocess.run")
    def test_command_includes_target_file(self, mock_run):
        from src.linter_engine import _run_external_linter

        mock_run.return_value = MagicMock(stdout="", returncode=0)
        _run_external_linter("vendor/bin/phpcs --report=checkstyle", "src/App.php")

        args, kwargs = mock_run.call_args
        self.assertIn("src/App.php", args[0])

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
