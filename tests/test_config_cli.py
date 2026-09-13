"""CLI tests for the ``gitpr config`` command surface (TUI mocked).

The screen itself is covered by tests/test_config_app.py. What is pinned here
is the wiring in main.py, where three things are easy to get wrong and
invisible until someone runs the command for real:

  * the command exists and is reachable as ``gitpr config``;
  * ``setup_environment()`` is NOT called first — it prompts for a missing API
    key on stdin, which would fight the screen for the terminal;
  * the root callback does not intercept the subcommand, so no banner is
    printed into the TUI's stdout.
"""

import unittest
from unittest.mock import patch

from click.testing import CliRunner

from src.i18n import CURRENT_LANG, set_lang
from src.main import cli


class ConfigCliTestCase(unittest.TestCase):
    """Pins the interface language to English for deterministic assertions."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)


class TestConfigCommandRegistration(ConfigCliTestCase):
    def test_config_is_registered_as_a_subcommand(self):
        self.assertIn("config", cli.commands)

    def test_config_declares_both_help_spellings(self):
        """Click's default is --help only; -h has to be declared, and the rest
        of the CLI uses -h everywhere."""
        command = cli.commands["config"]
        self.assertIn("-h", command.context_settings["help_option_names"])
        self.assertIn("--help", command.context_settings["help_option_names"])

    def test_config_takes_no_arguments(self):
        """Every setting is edited inside the screen; nothing is passed on the
        command line, so an accidental extra argument must be an error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--nope"])

        self.assertNotEqual(result.exit_code, 0)


class TestConfigInvocation(ConfigCliTestCase):
    def test_config_launches_the_screen(self):
        with patch("src.ui.config_app.launch_config_app") as launch:
            runner = CliRunner()
            result = runner.invoke(cli, ["config"])

        self.assertEqual(result.exit_code, 0, result.output)
        launch.assert_called_once_with()

    def test_config_never_prompts_for_an_api_key(self):
        """setup_environment() asks for a missing API key with click.prompt.
        Inside a full-screen app that write lands in the middle of the layout,
        so the subcommand must not reach it."""
        with patch("src.ui.config_app.launch_config_app"), \
             patch("src.main.setup_environment") as setup:
            runner = CliRunner()
            result = runner.invoke(cli, ["config"])

        self.assertEqual(result.exit_code, 0, result.output)
        setup.assert_not_called()

    def test_config_does_not_print_a_banner(self):
        """The root callback returns early for subcommands, so nothing is
        written to stdout before the screen takes over the terminal."""
        with patch("src.ui.config_app.launch_config_app"):
            runner = CliRunner()
            result = runner.invoke(cli, ["config"])

        self.assertEqual(result.output, "")

    def test_the_screen_import_stays_inside_the_command(self):
        """Importing src.ui.config_app pulls in Textual and the whole schema,
        and every other subcommand imports its app the same way — inside the
        function. A module-level import would bind the name here."""
        import src.main

        self.assertFalse(hasattr(src.main, "ConfigApp"))
        self.assertFalse(hasattr(src.main, "launch_config_app"))


class TestConfigHelp(ConfigCliTestCase):
    def test_help_names_the_settings_file(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "-h"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(".env", result.output)
        self.assertIn("--help", result.output)

    def test_help_points_to_the_config_tui_docs(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "-h"])

        self.assertEqual(result.exit_code, 0, result.output)
        # The epilog freezes at import under the machine locale, so only the
        # locale-independent docs URL fragment is asserted.
        self.assertIn("config-tui", result.output)


if __name__ == "__main__":
    unittest.main()
