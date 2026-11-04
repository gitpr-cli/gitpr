"""Tests for the issue-autoclose configuration (T7).

The getters mirror GITPR_BADGE's opt-out: on unless the file spells one of the
false literals. The schema assertions prove the two keys reach the `gitpr
config` screen with the control kinds whose parsing the getters mirror.
"""
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from src.config import (
    DEFAULT_CONFIG,
    get_issue_autoclose_timeout,
    issue_autoclose_enabled,
)
from src.config_schema import (
    FIELDS_BY_KEY,
    KIND_BOOL,
    KIND_INT,
    fields_of,
    validate_field_value,
)

_ENV_KEYS = ("GITPR_ISSUE_AUTOCLOSE", "GITPR_ISSUE_AUTOCLOSE_TIMEOUT")


@contextmanager
def _env_patch(overrides):
    """Patches the read path; a key absent from the map keeps its default."""
    with patch("src.config.load_dotenv"), patch(
        "src.config.os.getenv",
        side_effect=lambda key, default=None: overrides.get(key, default),
    ):
        yield


class TestIssueAutocloseEnabled(unittest.TestCase):
    def test_defaults_to_true(self):
        with _env_patch({}):
            self.assertTrue(issue_autoclose_enabled())

    def test_false_variants_disable(self):
        for raw in ("false", "FALSE", "0", "no", "NO", "off", "n", "  false "):
            with self.subTest(raw=raw), _env_patch({"GITPR_ISSUE_AUTOCLOSE": raw}):
                self.assertFalse(issue_autoclose_enabled())

    def test_any_other_value_keeps_it_on(self):
        # Opt-out, like GITPR_BADGE: an unknown literal cannot disable it.
        for raw in ("true", "1", "yes", "y", "on", "whatever", ""):
            with self.subTest(raw=raw), _env_patch({"GITPR_ISSUE_AUTOCLOSE": raw}):
                self.assertTrue(issue_autoclose_enabled())


class TestIssueAutocloseTimeout(unittest.TestCase):
    def test_defaults_to_five(self):
        with _env_patch({}):
            self.assertEqual(get_issue_autoclose_timeout(), 5)

    def test_reads_a_positive_integer(self):
        for raw, expected in (("17", 17), (" 17 ", 17), ("1", 1)):
            with self.subTest(raw=raw), _env_patch(
                {"GITPR_ISSUE_AUTOCLOSE_TIMEOUT": raw}
            ):
                self.assertEqual(get_issue_autoclose_timeout(), expected)

    def test_invalid_or_non_positive_falls_back_to_five(self):
        for raw in ("abc", "", "0", "-5", "1.5", "5s"):
            with self.subTest(raw=raw), _env_patch(
                {"GITPR_ISSUE_AUTOCLOSE_TIMEOUT": raw}
            ):
                self.assertEqual(get_issue_autoclose_timeout(), 5)


class TestIssueAutocloseSchema(unittest.TestCase):
    def test_both_fields_are_in_the_issue_category(self):
        keys = [field.key for field in fields_of("issue")]
        self.assertIn("GITPR_ISSUE_AUTOCLOSE", keys)
        self.assertIn("GITPR_ISSUE_AUTOCLOSE_TIMEOUT", keys)
        self.assertEqual(FIELDS_BY_KEY["GITPR_ISSUE_AUTOCLOSE"].category, "issue")
        self.assertEqual(
            FIELDS_BY_KEY["GITPR_ISSUE_AUTOCLOSE_TIMEOUT"].category, "issue"
        )

    def test_enabled_field_is_a_default_true_boolean(self):
        field = FIELDS_BY_KEY["GITPR_ISSUE_AUTOCLOSE"]
        self.assertEqual(field.kind, KIND_BOOL)
        self.assertEqual(field.default, "true")
        self.assertFalse(field.advanced)
        self.assertFalse(field.read_only)
        self.assertEqual(validate_field_value(field, field.default), "")
        self.assertNotEqual(validate_field_value(field, "maybe"), "")

    def test_timeout_field_is_a_positive_integer(self):
        field = FIELDS_BY_KEY["GITPR_ISSUE_AUTOCLOSE_TIMEOUT"]
        self.assertEqual(field.kind, KIND_INT)
        self.assertEqual(field.default, "5")
        self.assertFalse(field.advanced)
        self.assertFalse(field.read_only)
        self.assertEqual(validate_field_value(field, "5"), "")
        for rejected in ("0", "-1", "abc", "1.5"):
            with self.subTest(value=rejected):
                self.assertNotEqual(validate_field_value(field, rejected), "")

    def test_the_keys_are_not_seeded_into_the_env_file(self):
        # Read-only defaults, like GITPR_BADGE: setup_environment() must not
        # write them into every user's ~/.gitpr/.env.
        for key in _ENV_KEYS:
            with self.subTest(key=key):
                self.assertNotIn(key, DEFAULT_CONFIG)


if __name__ == "__main__":
    unittest.main()
