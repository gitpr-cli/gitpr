"""Unit tests for blame_engine metric logging integration."""
import unittest
from unittest.mock import patch, MagicMock


class TestBlameMetrics(unittest.TestCase):
    """Tests that log_local_metric is called with correct params after blame analysis."""

    @patch("src.blame_engine.log_local_metric")
    @patch("src.blame_engine.execute_git_blame")
    def test_return_data_mode_dispatches_metric(self, mock_blame, mock_metric):
        """return_data=True should fire log_local_metric with mode='return_data'."""
        from src.blame_engine import run_blame_analysis

        # Simulate one commit found
        mock_blame.return_value = ["abc12345"]

        with patch("src.blame_engine.get_commit_info") as mock_info, \
             patch("src.blame_engine.analyze_commit_with_ai") as mock_ai:
            mock_info.return_value = {
                "author": "Alice",
                "date": "2026-01-15",
                "message": "Initial implementation",
            }
            mock_ai.return_value = {
                "status": "ORIGIN",
                "reason": "New business rule introduced.",
            }

            result = run_blame_analysis("src/app.py", 10, 20, return_data=True)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        mock_metric.assert_called_once_with(
            command="blame",
            status="success",
            commits_analyzed=len(result),
            mode="return_data",
        )

    @patch("src.blame_engine.log_local_metric")
    @patch("src.blame_engine.execute_git_blame")
    def test_no_commits_returns_empty_without_metric(self, mock_blame, mock_metric):
        """When no commits found in return_data mode, return [] without metric call."""
        from src.blame_engine import run_blame_analysis

        mock_blame.return_value = []

        result = run_blame_analysis("src/app.py", 10, 20, return_data=True)

        self.assertEqual(result, [])
        # Metric should NOT be called because the early return happens before the metric line
        mock_metric.assert_not_called()

    @patch("src.blame_engine.log_local_metric")
    @patch("src.blame_engine.execute_git_blame")
    def test_save_to_disk_success_dispatches_metric(self, mock_blame, mock_metric):
        """Successful save to disk should fire log_local_metric with mode='report_generated'."""
        from src.blame_engine import run_blame_analysis

        mock_blame.return_value = ["abc12345"]

        with patch("src.blame_engine.get_commit_info") as mock_info, \
             patch("src.blame_engine.analyze_commit_with_ai") as mock_ai, \
             patch("src.blame_engine.call_ai_model") as mock_summary, \
             patch("src.blame_engine.get_current_branch") as mock_branch, \
             patch("builtins.open", unittest.mock.mock_open()):

            mock_info.return_value = {
                "author": "Bob",
                "date": "2026-03-20",
                "message": "Refactor auth logic",
            }
            mock_ai.return_value = {
                "status": "REFACTORING",
                "reason": "Extracted method.",
            }
            mock_summary.return_value = {"resumo": "A summary text."}
            mock_branch.return_value = "feature/test"

            # This runs twice: first ORIGIN stops the loop, but let's keep depth=1
            run_blame_analysis("src/app.py", 5, 10, return_data=False)

        # Should have been called for the success path
        success_calls = [
            c for c in mock_metric.call_args_list
            if c.kwargs.get("status") == "success"
        ]
        self.assertTrue(any(
            c.kwargs.get("mode") == "report_generated"
            for c in success_calls
        ), "Expected a success metric with mode='report_generated'")

    @patch("src.blame_engine.log_local_metric")
    @patch("src.blame_engine.execute_git_blame")
    def test_save_to_disk_error_dispatches_metric(self, mock_blame, mock_metric):
        """Save-to-disk failure should fire log_local_metric with status='error'."""
        from src.blame_engine import run_blame_analysis

        mock_blame.return_value = ["abc12345"]

        # Use a selective open mock: only raise on the output file, not .env
        real_open = open

        def selective_open(filename, *args, **kwargs):
            if "BLAME_REPORT" in str(filename) or filename.endswith(".md"):
                raise OSError("Disk full")
            return real_open(filename, *args, **kwargs)

        with patch("src.blame_engine.get_commit_info") as mock_info, \
             patch("src.blame_engine.analyze_commit_with_ai") as mock_ai, \
             patch("src.blame_engine.call_ai_model") as mock_summary, \
             patch("src.blame_engine.get_current_branch") as mock_branch, \
             patch("builtins.open", side_effect=selective_open):

            mock_info.return_value = {
                "author": "Carol",
                "date": "2026-05-10",
                "message": "Fix typo",
            }
            mock_ai.return_value = {
                "status": "ORIGIN",
                "reason": "Initial rule.",
            }
            mock_summary.return_value = {"resumo": "Summary."}
            mock_branch.return_value = "main"

            run_blame_analysis("src/app.py", 1, 3, return_data=False)

        # Should have an error metric
        error_calls = [
            c for c in mock_metric.call_args_list
            if c.kwargs.get("status") == "error"
        ]
        self.assertTrue(len(error_calls) > 0, "Expected an error metric on save failure")
        self.assertIn("error_message", error_calls[0].kwargs)


if __name__ == "__main__":
    unittest.main()
