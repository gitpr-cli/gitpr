"""Unit tests for linter_engine metric logging integration."""
import unittest
from unittest.mock import patch, MagicMock


class TestLinterMetrics(unittest.TestCase):
    """Tests that log_local_metric is called with correct params after linting."""

    @patch("src.linter_engine.load_external_linters", return_value=[])
    @patch("src.linter_engine.log_local_metric")
    @patch("src.linter_engine.load_linter_rules")
    def test_full_file_mode_dispatches_metric(self, mock_load_rules, mock_metric, mock_ext):
        """Full file mode should fire log_local_metric with mode='full_file'."""
        from src.linter_engine import parse_diff_and_lint

        mock_load_rules.return_value = [
            {
                "name": "no_debug",
                "regex": r"debugger",
                "message": "Found debugger",
                "extensions": ["py"],
                "level": "error",
            }
        ]

        diff_text = "debugger\nprint('hello')\n"
        result = parse_diff_and_lint(diff_text, is_full_file=True, file_path="test.py")

        self.assertIsInstance(result, dict)
        self.assertIn("errors", result)
        mock_metric.assert_called_once_with(
            command="linter",
            status="success",
            linter_errors=len(result["errors"]),
            linter_warnings=len(result["warnings"]),
            mode="full_file",
        )

    @patch("src.linter_engine.load_external_linters", return_value=[])
    @patch("src.linter_engine.log_local_metric")
    @patch("src.linter_engine.load_linter_rules")
    def test_diff_mode_dispatches_metric(self, mock_load_rules, mock_metric, mock_ext):
        """Standard diff mode should fire log_local_metric with mode='diff'."""
        from src.linter_engine import parse_diff_and_lint

        mock_load_rules.return_value = [
            {
                "name": "no_todo",
                "regex": r"TODO",
                "message": "Found TODO",
                "extensions": ["py"],
                "level": "warning",
            }
        ]

        diff_text = (
            "+++ b/src/app.py\n"
            "@@ -1,3 +1,4 @@\n"
            "+TODO: refactor this\n"
            " print('ok')\n"
        )
        result = parse_diff_and_lint(diff_text, is_full_file=False)

        self.assertIsInstance(result, dict)
        self.assertIn("warnings", result)
        mock_metric.assert_called_once_with(
            command="linter",
            status="success",
            linter_errors=len(result["errors"]),
            linter_warnings=len(result["warnings"]),
            mode="diff",
        )

    @patch("src.linter_engine.load_external_linters", return_value=[])
    @patch("src.linter_engine.log_local_metric")
    @patch("src.linter_engine.load_linter_rules")
    def test_full_file_mode_no_rules(self, mock_load_rules, mock_metric, mock_ext):
        """When no rules match, metric should still fire with zero counts."""
        from src.linter_engine import parse_diff_and_lint

        mock_load_rules.return_value = [
            {
                "name": "js_only",
                "regex": r"var",
                "message": "Use let/const",
                "extensions": ["js"],
                "level": "warning",
            }
        ]

        diff_text = "print('hello')\n"
        result = parse_diff_and_lint(diff_text, is_full_file=True, file_path="test.py")

        self.assertEqual(result["errors"], [])
        self.assertEqual(result["warnings"], [])
        mock_metric.assert_called_once_with(
            command="linter",
            status="success",
            linter_errors=0,
            linter_warnings=0,
            mode="full_file",
        )

    @patch("src.linter_engine.load_external_linters", return_value=[])
    @patch("src.linter_engine.log_local_metric")
    @patch("src.linter_engine.load_linter_rules")
    def test_full_file_mode_no_file_path_skips_metric(self, mock_load_rules, mock_metric, mock_ext):
        """When is_full_file is True but file_path is None, should return early without metric."""
        from src.linter_engine import parse_diff_and_lint

        mock_load_rules.return_value = []

        result = parse_diff_and_lint("some content", is_full_file=True, file_path=None)

        self.assertEqual(result, {"errors": [], "warnings": []})
        mock_metric.assert_not_called()


if __name__ == "__main__":
    unittest.main()
