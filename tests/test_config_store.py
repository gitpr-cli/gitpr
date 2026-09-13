"""Round-trip tests for the .env writers backing the configuration screen.

These run against a real file in a temporary directory rather than a mock:
the whole reason these helpers exist instead of calling set_key() inline is
that .env integrity (comments, order, absence of the line after a reset) is
the contract the screen depends on.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from src.config import (
    read_env_file_values,
    remove_config_value,
    save_config_values,
)

# A file with comments, blank lines and a key that must survive untouched.
SEEDED_ENV = """\
# GitPR configuration
# Hand written comment that must survive every save.
GITPR_AUTO_STAGE=false

# Another section
GITPR_LANG=pt_br
GITPR_AI_TIMEOUT=180
"""


class ConfigStoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.env_path = os.path.join(self._tmpdir.name, ".env")
        self.addCleanup(self._tmpdir.cleanup)
        self._patcher = patch("src.config.ENV_FILE", self.env_path)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)

    def write_env(self, content=SEEDED_ENV):
        with open(self.env_path, "w", encoding="utf-8") as handle:
            handle.write(content)

    def read_raw(self):
        with open(self.env_path, encoding="utf-8", errors="replace") as handle:
            return handle.read()


class TestReadEnvFileValues(ConfigStoreTestCase):
    def test_missing_file_returns_empty_dict(self):
        self.assertEqual(read_env_file_values(), {})

    def test_reads_every_key_of_the_file(self):
        self.write_env()
        values = read_env_file_values()
        self.assertEqual(values["GITPR_AUTO_STAGE"], "false")
        self.assertEqual(values["GITPR_LANG"], "pt_br")
        self.assertEqual(values["GITPR_AI_TIMEOUT"], "180")

    def test_key_absent_from_the_file_is_absent_from_the_dict(self):
        """The screen relies on absence to render "not configured"."""
        self.write_env("GITPR_LANG=pt_br\n")
        self.assertNotIn("GITPR_AUTO_STAGE", read_env_file_values())

    def test_empty_value_becomes_empty_string_not_none(self):
        self.write_env("GITPR_REVIEWER_SUGGESTION_EXCLUDED=\n")
        self.assertEqual(read_env_file_values()["GITPR_REVIEWER_SUGGESTION_EXCLUDED"], "")

    def test_process_environment_does_not_leak_in(self):
        """load_dotenv(override=False) means os.environ wins over the file, so
        reading via os.getenv() would make the screen display a value that is
        not the one it is about to write."""
        self.write_env("GITPR_LANG=pt_br\n")
        with patch.dict(os.environ, {"GITPR_LANG": "fr_fr"}):
            self.assertEqual(read_env_file_values()["GITPR_LANG"], "pt_br")


class TestSaveConfigValues(ConfigStoreTestCase):
    def test_saves_into_a_missing_file(self):
        save_config_values({"GITPR_AUTO_STAGE": "true"})
        self.assertEqual(read_env_file_values()["GITPR_AUTO_STAGE"], "true")

    def test_creates_the_parent_directory(self):
        nested = os.path.join(self._tmpdir.name, "deep", "nested", ".env")
        with patch("src.config.ENV_FILE", nested):
            save_config_values({"GITPR_LANG": "pt_br"})
        self.assertTrue(os.path.exists(nested))

    def test_updates_an_existing_key_in_place(self):
        self.write_env()
        save_config_values({"GITPR_AI_TIMEOUT": "300"})
        self.assertEqual(read_env_file_values()["GITPR_AI_TIMEOUT"], "300")

    def test_comments_and_unrelated_lines_survive(self):
        self.write_env()
        save_config_values({"GITPR_AUTO_STAGE": "true"})
        raw = self.read_raw()
        self.assertIn("# GitPR configuration", raw)
        self.assertIn("# Hand written comment that must survive every save.", raw)
        self.assertIn("# Another section", raw)
        self.assertEqual(read_env_file_values()["GITPR_LANG"], "pt_br")

    def test_key_order_is_preserved(self):
        self.write_env()
        save_config_values({"GITPR_AUTO_STAGE": "true"})
        keys = [line.split("=")[0] for line in self.read_raw().splitlines() if "=" in line]
        self.assertEqual(
            keys, ["GITPR_AUTO_STAGE", "GITPR_LANG", "GITPR_AI_TIMEOUT"]
        )

    def test_new_key_is_appended_at_the_end(self):
        self.write_env("GITPR_LANG=pt_br\n")
        save_config_values({"GITPR_AUTO_STAGE": "true"})
        keys = [line.split("=")[0] for line in self.read_raw().splitlines() if "=" in line]
        self.assertEqual(keys, ["GITPR_LANG", "GITPR_AUTO_STAGE"])

    def test_several_keys_are_written_in_one_call(self):
        self.write_env()
        save_config_values({"GITPR_LANG": "es_es", "GITPR_AI_TIMEOUT": "90"})
        values = read_env_file_values()
        self.assertEqual(values["GITPR_LANG"], "es_es")
        self.assertEqual(values["GITPR_AI_TIMEOUT"], "90")

    def test_empty_dict_is_a_no_op(self):
        """Ctrl+R on a field that was never set must not create the file."""
        save_config_values({})
        self.assertFalse(os.path.exists(self.env_path))

    def test_empty_value_is_stored_as_an_empty_line_not_a_removal(self):
        """An explicitly emptied field is a value, not a reset — resetting has
        its own path (remove_config_value)."""
        self.write_env("GITPR_LANG=pt_br\n")
        save_config_values({"GITPR_LANG": ""})
        self.assertEqual(read_env_file_values()["GITPR_LANG"], "")

    def test_value_with_spaces_and_equals_sign_round_trips(self):
        save_config_values({"SPINNER_THINKING_WORDS": "thinking | pondering = yes"})
        self.assertEqual(
            read_env_file_values()["SPINNER_THINKING_WORDS"], "thinking | pondering = yes"
        )


class TestRemoveConfigValue(ConfigStoreTestCase):
    def test_removes_the_line_entirely(self):
        self.write_env()
        self.assertTrue(remove_config_value("GITPR_AI_TIMEOUT"))
        self.assertNotIn("GITPR_AI_TIMEOUT", self.read_raw())

    def test_removal_is_idempotent(self):
        self.write_env()
        self.assertTrue(remove_config_value("GITPR_AI_TIMEOUT"))
        self.assertFalse(remove_config_value("GITPR_AI_TIMEOUT"))

    def test_absent_key_returns_false(self):
        self.write_env()
        self.assertFalse(remove_config_value("NEVER_SET"))

    def test_missing_file_returns_false(self):
        self.assertFalse(remove_config_value("GITPR_LANG"))

    def test_surrounding_comments_and_keys_survive(self):
        self.write_env()
        remove_config_value("GITPR_LANG")
        raw = self.read_raw()
        self.assertIn("# GitPR configuration", raw)
        self.assertIn("# Another section", raw)
        values = read_env_file_values()
        self.assertEqual(values["GITPR_AUTO_STAGE"], "false")
        self.assertEqual(values["GITPR_AI_TIMEOUT"], "180")
        self.assertNotIn("GITPR_LANG", values)

    def test_save_after_remove_restores_the_key(self):
        """Ctrl+R marks a line for removal but the write only happens on F2, so
        both operations can land in the same save batch."""
        self.write_env()
        remove_config_value("GITPR_LANG")
        save_config_values({"GITPR_LANG": "fr_fr"})
        self.assertEqual(read_env_file_values()["GITPR_LANG"], "fr_fr")

    def test_removed_key_is_absent_not_empty(self):
        """Restoring the default means removing the line: an absent key keeps
        following the code default if that default ever changes."""
        self.write_env()
        remove_config_value("GITPR_AI_TIMEOUT")
        self.assertNotIn("GITPR_AI_TIMEOUT", read_env_file_values())


if __name__ == "__main__":
    unittest.main()
