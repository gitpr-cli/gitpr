"""Tests for the gitpr fix configuration keys and the get_fix_settings reader.

No file is read: os.getenv is patched, which is also what keeps these tests
away from whatever ~/.gitpr/.env holds on the machine running them.
"""
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from src.config import DEFAULT_CONFIG, get_fix_settings
from src.config_schema import FIELDS

DEFAULT_EXCLUDED = (
    "database/migrations/**",
    "**/*.ci.yml",
    "docker/**",
    "terraform/**",
    ".github/workflows/**",
)

# Shared env map used by the patched os.getenv.
_DEFAULTS = {
    "GITPR_FIX_SAFE_MAX_LINES_CHANGED": "5",
    "GITPR_FIX_SAFE_EXCLUDED_PATHS": DEFAULT_CONFIG["GITPR_FIX_SAFE_EXCLUDED_PATHS"],
    "GITPR_FIX_REQUIRE_CONFIRMATION": "true",
    "GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE": "true",
    "GITPR_FIX_BRANCH_NAME_TEMPLATE": "fix/gitpr-{datetime}",
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


class TestDefaults(unittest.TestCase):
    def test_defaults(self):
        with _env_patch({}):
            settings = get_fix_settings()

        self.assertEqual(settings["safe_max_lines_changed"], 5)
        self.assertEqual(settings["safe_excluded_paths"], DEFAULT_EXCLUDED)
        self.assertTrue(settings["require_confirmation"])
        self.assertTrue(settings["create_branch_on_all_safe"])
        self.assertEqual(settings["branch_name_template"], "fix/gitpr-{datetime}")

    def test_every_key_is_declared_in_the_schema(self):
        """The screen and the getter must agree, or the setting is invisible."""
        declared = {field.key for field in FIELDS if field.category == "fix"}
        self.assertEqual(
            declared,
            {
                "GITPR_FIX_SAFE_MAX_LINES_CHANGED",
                "GITPR_FIX_SAFE_EXCLUDED_PATHS",
                "GITPR_FIX_REQUIRE_CONFIRMATION",
                "GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE",
                "GITPR_FIX_BRANCH_NAME_TEMPLATE",
            },
        )


class TestSafeMaxLines(unittest.TestCase):
    def test_invalid_values_fall_back_to_5(self):
        for raw in ("abc", "0", "-2", ""):
            with _env_patch({"GITPR_FIX_SAFE_MAX_LINES_CHANGED": raw}):
                self.assertEqual(get_fix_settings()["safe_max_lines_changed"], 5)

    def test_parsed(self):
        with _env_patch({"GITPR_FIX_SAFE_MAX_LINES_CHANGED": "12"}):
            self.assertEqual(get_fix_settings()["safe_max_lines_changed"], 12)


class TestExcludedPaths(unittest.TestCase):
    def test_semicolon_list_is_cleaned(self):
        with _env_patch(
            {"GITPR_FIX_SAFE_EXCLUDED_PATHS": " infra/**;; docker/** , x.yml "}
        ):
            settings = get_fix_settings()

        self.assertEqual(settings["safe_excluded_paths"], ("infra/**", "docker/** , x.yml"))

    def test_an_empty_value_keeps_the_built_in_list(self):
        # A field cleared by accident must not silently disable the protection.
        with _env_patch({"GITPR_FIX_SAFE_EXCLUDED_PATHS": ""}):
            self.assertEqual(get_fix_settings()["safe_excluded_paths"], DEFAULT_EXCLUDED)


class TestBooleans(unittest.TestCase):
    def test_false_variants_disable(self):
        for key in ("GITPR_FIX_REQUIRE_CONFIRMATION", "GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE"):
            for raw in ("false", "FALSE", "0", "no", "off", "n", " false "):
                with _env_patch({key: raw}):
                    settings = get_fix_settings()
                field = "require_confirmation" if "REQUIRE" in key else "create_branch_on_all_safe"
                self.assertFalse(settings[field], f"{key}={raw!r}")

    def test_anything_else_enables(self):
        for raw in ("true", "1", "yes", "on", "y", ""):
            with _env_patch({"GITPR_FIX_REQUIRE_CONFIRMATION": raw}):
                self.assertTrue(get_fix_settings()["require_confirmation"], repr(raw))


class TestBranchNameTemplate(unittest.TestCase):
    def test_blank_falls_back_to_the_default(self):
        for raw in ("", "   "):
            with _env_patch({"GITPR_FIX_BRANCH_NAME_TEMPLATE": raw}):
                self.assertEqual(
                    get_fix_settings()["branch_name_template"], "fix/gitpr-{datetime}"
                )

    def test_custom_template_is_kept(self):
        with _env_patch({"GITPR_FIX_BRANCH_NAME_TEMPLATE": " fix/{branch}-{datetime} "}):
            self.assertEqual(
                get_fix_settings()["branch_name_template"], "fix/{branch}-{datetime}"
            )


if __name__ == "__main__":
    unittest.main()
