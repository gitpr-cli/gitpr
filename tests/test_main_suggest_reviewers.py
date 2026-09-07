"""Tests for the main.py reviewer-suggestion integration.

Covers the _reviewer_suggestion_view mapping (GitHub vs local-only forges)
and the --no-suggest-reviewers flag surface (contextual help). The heavy
pipeline itself (blame over real diffs) is covered in test_suggest_reviewers
and the TUI attach logic in test_pr_publish_app.
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from click.testing import CliRunner

from src.main import _reviewer_suggestion_view, cli
from src.reviewer_suggestion import ReviewerCandidate, ReviewerSuggestionResult


def _result(*candidates):
    return ReviewerSuggestionResult(candidates=list(candidates))


def _candidate(name, email):
    return ReviewerCandidate(
        author_name=name,
        author_email=email,
        touched_lines=3,
        touched_files=1,
        last_touch_date="2026-09-01",
    )


def _github_provider(handle_map, raise_on=None):
    def email_to_handle(email):
        if email == raise_on:
            raise RuntimeError("search exploded")
        return handle_map.get(email)
    return SimpleNamespace(name="github", email_to_handle=email_to_handle)


class TestReviewerSuggestionView(unittest.TestCase):
    def test_empty_input_yields_none(self):
        self.assertIsNone(_reviewer_suggestion_view(None, object()))
        self.assertIsNone(_reviewer_suggestion_view(_result(), object()))

    @patch("src.i18n.TRANSLATIONS", {})
    def test_github_view_resolves_handles_and_justifies(self):
        provider = _github_provider(
            {"ana@example.com": "ana", "bob@example.com": "bob"}
        )
        view = _reviewer_suggestion_view(
            _result(
                _candidate("Ana Silva", "ana@example.com"),
                _candidate("Bob Lima", "bob@example.com"),
            ),
            provider,
        )
        self.assertTrue(view["submittable"])
        self.assertEqual(view["handles"], ["ana", "bob"])
        self.assertEqual(view["note"], None)
        self.assertEqual(len(view["lines"]), 2)
        self.assertTrue(view["lines"][0].startswith("Suggested @ana:"))
        self.assertTrue(view["lines"][1].startswith("Suggested @bob:"))

    @patch("src.i18n.TRANSLATIONS", {})
    def test_unresolvable_email_stays_out_of_handles_but_in_lines(self):
        provider = _github_provider({"ana@example.com": "ana"})
        view = _reviewer_suggestion_view(
            _result(
                _candidate("Ana Silva", "ana@example.com"),
                _candidate("Carla Reis", "carla@corp.com"),
            ),
            provider,
        )
        self.assertEqual(view["handles"], ["ana"])
        # The unresolvable candidate is justified under the author name.
        self.assertTrue(view["lines"][1].startswith("Suggested Carla Reis:"))

    @patch("src.i18n.TRANSLATIONS", {})
    def test_handle_lookup_failure_is_silent(self):
        provider = _github_provider({}, raise_on="ana@example.com")
        view = _reviewer_suggestion_view(
            _result(_candidate("Ana Silva", "ana@example.com")), provider
        )
        self.assertEqual(view["handles"], [])
        self.assertEqual(len(view["lines"]), 1)

    @patch("src.i18n.TRANSLATIONS", {})
    def test_non_github_forge_is_local_only(self):
        provider = SimpleNamespace(name="gitlab")
        view = _reviewer_suggestion_view(
            _result(_candidate("Ana Silva", "ana@example.com")), provider
        )
        self.assertFalse(view["submittable"])
        self.assertEqual(view["handles"], [])
        self.assertIn("GitLab", view["note"])
        self.assertIn("local", view["note"].lower())
        self.assertTrue(view["lines"][0].startswith("Suggested Ana Silva:"))


class TestNoSuggestReviewersFlag(unittest.TestCase):
    def test_flag_appears_in_contextual_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["-h", "--no-suggest-reviewers"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Skip Suggested Reviewers", result.output)
        self.assertIn("--no-suggest-reviewers", result.output)


if __name__ == "__main__":
    unittest.main()
