"""Tests for the reviewer-suggestion configuration keys and getters."""
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from src.config import (
    get_reviewer_suggestion_settings,
    suggest_reviewers_enabled,
)

# Shared env map used by the patched os.getenv.
_DEFAULTS = {
    "GITPR_SUGGEST_REVIEWERS": "true",
    "GITPR_REVIEWER_SUGGESTION_TOP_N": "3",
    "GITPR_REVIEWER_SUGGESTION_EXCLUDED": "",
}


@contextmanager
def _env_patch(overrides):
    env = dict(_DEFAULTS)
    env.update(overrides)
    with patch("src.config.load_dotenv"), patch(
        "src.config.os.getenv",
        side_effect=lambda key, default=None: env.get(key, default),
    ):
        yield


class TestSuggestReviewersEnabled(unittest.TestCase):
    def test_defaults_to_true(self):
        with _env_patch({"GITPR_SUGGEST_REVIEWERS": ""}):
            self.assertTrue(suggest_reviewers_enabled())

    def test_false_variants_disable(self):
        for raw in ("false", "FALSE", "0", "no", "off", "n", "  false "):
            with _env_patch({"GITPR_SUGGEST_REVIEWERS": raw}):
                self.assertFalse(suggest_reviewers_enabled())

    def test_true_variants_enable(self):
        for raw in ("true", "True", "1", "yes", "on", "y"):
            with _env_patch({"GITPR_SUGGEST_REVIEWERS": raw}):
                self.assertTrue(suggest_reviewers_enabled())


class TestGetReviewerSuggestionSettings(unittest.TestCase):
    def test_defaults(self):
        with _env_patch({}):
            settings = get_reviewer_suggestion_settings()
        self.assertTrue(settings["enabled"])
        self.assertEqual(settings["top_n"], 3)
        self.assertEqual(settings["excluded"], ())

    def test_top_n_invalid_values_fall_back_to_3(self):
        for raw in ("abc", "-2", "0", ""):
            with _env_patch({"GITPR_REVIEWER_SUGGESTION_TOP_N": raw}):
                self.assertEqual(get_reviewer_suggestion_settings()["top_n"], 3)

    def test_top_n_parsed(self):
        with _env_patch({"GITPR_REVIEWER_SUGGESTION_TOP_N": "5"}):
            self.assertEqual(get_reviewer_suggestion_settings()["top_n"], 5)

    def test_excluded_csv_is_cleaned(self):
        with _env_patch(
            {
                "GITPR_REVIEWER_SUGGESTION_EXCLUDED": (
                    "a@example.com, Bob Lima ,,dependabot[bot]"
                )
            }
        ):
            self.assertEqual(
                get_reviewer_suggestion_settings()["excluded"],
                ("a@example.com", "Bob Lima", "dependabot[bot]"),
            )

    def test_excluded_empty(self):
        with _env_patch({"GITPR_REVIEWER_SUGGESTION_EXCLUDED": " , , "}):
            self.assertEqual(get_reviewer_suggestion_settings()["excluded"], ())


if __name__ == "__main__":
    unittest.main()
