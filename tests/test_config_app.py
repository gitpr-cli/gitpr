"""Behaviour tests for the configuration screen (Textual App.run_test()).

The screen is exercised against a real temporary .env so the tests cover the
whole path — widget, pending state, validation, write — instead of asserting
that methods were called.
"""
import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch

from textual.widgets import Button, Input, ListView, Select, Static, Switch, TextArea

from src.config import (
    SKILL_TYPES,
    VALIDATION_AUTH,
    VALIDATION_NETWORK,
    read_env_file_values,
)
from src.ui.config_app import ConfirmDiscardScreen
from src.config_schema import FIELDS_BY_KEY

SEEDED_ENV = """\
# GitPR configuration
GITPR_AUTO_STAGE=false
GITPR_AI_TIMEOUT=180
GITPR_LANG=pt_br
OUTPUT_FILE_NAME={branch}_{datetime}_PR_DESC.md
"""


def run(coro):
    return asyncio.run(coro)


def sidebar_ids(app):
    """Ids of the sidebar entries that are actually displayed."""
    return [item.id for item in app.query("#categories ListItem") if item.display]


class ConfigAppTestCase(unittest.TestCase):
    def setUp(self):
        # Textual's CSS parser is chatty on stderr; keep the test output clean.
        self._tmpdir = tempfile.TemporaryDirectory()
        self.env_path = os.path.join(self._tmpdir.name, ".env")
        self.addCleanup(self._tmpdir.cleanup)
        with open(self.env_path, "w", encoding="utf-8") as handle:
            handle.write(SEEDED_ENV)
        for target in ("src.config.ENV_FILE", "src.ui.config_app.ENV_FILE"):
            patcher = patch(target, self.env_path)
            patcher.start()
            self.addCleanup(patcher.stop)
        # The screen must never touch the real ~/.gitpr/.env or reach the network.
        for target in (
            "src.ui.config_app.validate_ai_key",
            "src.ui.config_app.encrypt_data",
        ):
            patcher = patch(target, side_effect=self._stub(target))
            patcher.start()
            self.addCleanup(patcher.stop)

    # Overridden by the credential tests; every other test accepts any key.
    probe_result = (True, "", "")

    def _stub(self, target):
        if target.endswith("validate_ai_key"):
            return lambda provider, key: self.probe_result
        return lambda value: f"enc({value})"

    def make_app(self):
        from src.ui.config_app import ConfigApp

        return ConfigApp()


class TestMountAndNavigation(ConfigAppTestCase):
    def test_opens_on_the_first_category(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.assertEqual(app.selected_category(), "general")
                # GITPR_LANG belongs to Geral and must be on screen.
                self.assertTrue(app.query(f"#value_GITPR_LANG"))

        run(scenario())

    def test_sidebar_lists_every_visible_category(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                ids = sidebar_ids(app)
                self.assertIn("cat_general", ids)
                self.assertIn("cat_pr", ids)
                # Advanced stays hidden until the toggle is on.
                self.assertNotIn("cat_advanced", ids)

        run(scenario())

    def test_switching_category_renders_that_category(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#categories", ListView).index = 2
                await pilot.pause()
                self.assertEqual(app.selected_category(), "pr")
                self.assertTrue(app.query("#value_GITPR_AUTO_STAGE"))

        run(scenario())

    def test_values_come_from_the_file(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                timeout = app.query_one("#value_GITPR_AI_TIMEOUT", Input)
                self.assertEqual(timeout.value, "180")

        run(scenario())

    def test_advanced_toggle_reveals_the_advanced_category(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#show_advanced", Switch).value = True
                await pilot.pause()
                ids = sidebar_ids(app)
                self.assertIn("cat_advanced", ids)

        run(scenario())


class TestDirtyState(ConfigAppTestCase):
    def test_editing_a_field_marks_it_dirty(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                self.assertTrue(app.is_dirty(FIELDS_BY_KEY["GITPR_AI_TIMEOUT"]))
                self.assertIn("1", str(app.query_one("#dirty_indicator", Static).content))

        run(scenario())

    def test_editing_back_to_the_file_value_clears_the_dirty_state(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                field = app.query_one("#value_GITPR_AI_TIMEOUT", Input)
                field.value = "300"
                await pilot.pause()
                field.value = "180"
                await pilot.pause()
                self.assertFalse(app.is_dirty(FIELDS_BY_KEY["GITPR_AI_TIMEOUT"]))

        run(scenario())

    def test_edit_survives_navigating_to_another_category(self):
        """Rows are destroyed on navigation, so the pending edit must not live
        in the widget — otherwise F2 would silently drop it."""
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                list_view = app.query_one("#categories", ListView)
                list_view.index = 2
                await pilot.pause()
                list_view.index = 1
                await pilot.pause()
                self.assertEqual(
                    app.query_one("#value_GITPR_AI_TIMEOUT", Input).value, "300"
                )

        run(scenario())

    def test_a_bool_toggled_back_is_not_dirty(self):
        """false/"" and false/false are the same setting; the raw string
        comparison would report a change that saving would not make."""
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#categories", ListView).index = 2
                await pilot.pause()
                switch = app.query_one("#value_GITPR_AUTO_STAGE", Switch)
                switch.value = True
                await pilot.pause()
                switch.value = False
                await pilot.pause()
                self.assertFalse(app.is_dirty(FIELDS_BY_KEY["GITPR_AUTO_STAGE"]))

        run(scenario())

    def test_enum_change_is_recorded(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_LANG", Select).value = "es_es"
                await pilot.pause()
                self.assertTrue(app.is_dirty(FIELDS_BY_KEY["GITPR_LANG"]))

        run(scenario())


class TestSave(ConfigAppTestCase):
    def test_save_writes_the_new_value_and_keeps_comments(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(read_env_file_values()["GITPR_AI_TIMEOUT"], "300")
                with open(self.env_path, encoding="utf-8", errors="replace") as handle:
                    self.assertIn("# GitPR configuration", handle.read())

        run(scenario())

    def test_save_clears_the_dirty_state(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(app.dirty_fields(), [])

        run(scenario())

    def test_save_is_a_no_op_when_nothing_changed(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                before = open(
                    self.env_path, encoding="utf-8", errors="replace"
                ).read()
                await pilot.press("f2")
                await pilot.pause()
                after = open(self.env_path, encoding="utf-8", errors="replace").read()
                self.assertEqual(before, after)

        run(scenario())

    def test_invalid_type_blocks_the_save(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "abc"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                # Nothing was written...
                self.assertEqual(read_env_file_values()["GITPR_AI_TIMEOUT"], "180")
                # ...and the error is on screen.
                error = app.query_one("#error_GITPR_AI_TIMEOUT", Static)
                self.assertIn("✖", str(error.content))

        run(scenario())

    def test_template_without_datetime_blocks_the_save(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#categories", ListView).index = 2
                await pilot.pause()
                app.query_one("#value_OUTPUT_FILE_NAME", Input).value = "{branch}_PR.md"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(
                    read_env_file_values()["OUTPUT_FILE_NAME"],
                    "{branch}_{datetime}_PR_DESC.md",
                )

        run(scenario())

    def test_a_secret_is_stored_encrypted_and_never_echoed_back(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#categories", ListView).index = 1
                await pilot.pause()
                secret = app.query_one("#value_GEMINI_API_KEY_ENCRYPTED", Input)
                self.assertTrue(secret.password)
                self.assertEqual(secret.value, "")
                secret.value = "plain-key"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(
                    read_env_file_values()["GEMINI_API_KEY_ENCRYPTED"],
                    "enc(plain-key)",
                )

        run(scenario())

    def test_an_unchanged_secret_is_never_rewritten(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#categories", ListView).index = 1
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertNotIn("GEMINI_API_KEY_ENCRYPTED", read_env_file_values())

        run(scenario())

    def test_save_stays_on_the_screen(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertTrue(app.is_running)

        run(scenario())


class TestRestoreDefault(ConfigAppTestCase):
    def test_ctrl_r_marks_the_field_and_save_removes_the_line(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).focus()
                await pilot.pause()
                await pilot.press("ctrl+r")
                await pilot.pause()
                self.assertIn("GITPR_AI_TIMEOUT", app.marked_for_removal)
                await pilot.press("f2")
                await pilot.pause()
                self.assertNotIn("GITPR_AI_TIMEOUT", read_env_file_values())

        run(scenario())

    def test_ctrl_r_discards_a_pending_edit_on_that_field(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).focus()
                await pilot.press("ctrl+r")
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                # The edit is gone, the line is gone — the default applies.
                self.assertNotIn("GITPR_AI_TIMEOUT", read_env_file_values())

        run(scenario())

    def test_ctrl_r_is_reversible(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).focus()
                await pilot.press("ctrl+r")
                await pilot.pause()
                await pilot.press("ctrl+r")
                await pilot.pause()
                self.assertNotIn("GITPR_AI_TIMEOUT", app.marked_for_removal)

        run(scenario())

    def test_ctrl_r_on_a_key_that_is_already_the_default_does_nothing(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#categories", ListView).index = 2
                await pilot.pause()
                # GITPR_SKIP_LINT is not in the seeded file.
                app.query_one("#value_GITPR_SKIP_LINT", Switch).focus()
                await pilot.press("ctrl+r")
                await pilot.pause()
                self.assertNotIn("GITPR_SKIP_LINT", app.marked_for_removal)

        run(scenario())

    def test_ctrl_r_on_a_read_only_field_is_refused(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#show_advanced", Switch).value = True
                await pilot.pause()
                app.query_one("#categories", ListView).index = (
                    app.sidebar_categories().index("advanced")
                )
                await pilot.pause()
                app.query_one("#value_LANG_VERSION", Input).focus()
                await pilot.press("ctrl+r")
                await pilot.pause()
                self.assertNotIn("LANG_VERSION", app.marked_for_removal)

        run(scenario())


class TestSearch(ConfigAppTestCase):
    def test_search_matches_across_categories(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#search", Input).value = "timeout"
                await pilot.pause()
                # GITPR_AI_TIMEOUT (Provedores) and GITPR_LINTER_TIMEOUT (Linter)
                self.assertTrue(app.query("#value_GITPR_AI_TIMEOUT"))
                self.assertTrue(app.query("#value_GITPR_LINTER_TIMEOUT"))

        run(scenario())

    def test_search_matches_a_label(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#search", Input).value = "co-author"
                await pilot.pause()
                self.assertTrue(app.query("#value_GITPR_COAUTHOR"))

        run(scenario())

    def test_clearing_the_search_returns_to_the_category(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#search", Input).value = "timeout"
                await pilot.pause()
                app.query_one("#search", Input).value = ""
                await pilot.pause()
                self.assertEqual(app.selected_category(), "general")
                self.assertTrue(app.query("#value_GITPR_LANG"))

        run(scenario())

    def test_no_match_shows_an_empty_state(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#search", Input).value = "zzzznothing"
                await pilot.pause()
                self.assertTrue(app.query("#empty"))

        run(scenario())


class TestUnknownKeys(ConfigAppTestCase):
    def test_unknown_keys_get_their_own_category(self):
        async def scenario():
            with open(self.env_path, "a", encoding="utf-8") as handle:
                handle.write("FOO=bar\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                ids = sidebar_ids(app)
                self.assertIn("cat_unknown", ids)

        run(scenario())

    def test_unknown_keys_are_read_only_and_listed(self):
        async def scenario():
            with open(self.env_path, "a", encoding="utf-8") as handle:
                handle.write("FOO=bar\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#categories", ListView).index = (
                    app.sidebar_categories().index("unknown")
                )
                await pilot.pause()
                control = app.query_one("#value_FOO", Input)
                self.assertTrue(control.disabled)
                self.assertEqual(control.value, "bar")

        run(scenario())

    def test_no_unknown_category_when_the_file_is_fully_known(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                ids = sidebar_ids(app)
                self.assertNotIn("cat_unknown", ids)

        run(scenario())


class TestExit(ConfigAppTestCase):
    def test_escape_quits_when_nothing_is_pending(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                self.assertFalse(app.is_running)

        run(scenario())

    def test_escape_asks_before_discarding_pending_changes(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                self.assertTrue(app.is_running)
                self.assertIsInstance(app.screen, ConfirmDiscardScreen)

        run(scenario())

    def test_confirming_the_discard_leaves_the_screen(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                app.screen.query_one("#btn_discard", Button).press()
                await pilot.pause()
                self.assertFalse(app.is_running)

        run(scenario())

    def test_keeping_the_edits_returns_to_the_screen_with_them_intact(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                app.screen.query_one("#btn_keep", Button).press()
                await pilot.pause()
                self.assertTrue(app.is_running)
                self.assertTrue(app.is_dirty(FIELDS_BY_KEY["GITPR_AI_TIMEOUT"]))
                # Nothing reached the file.
                self.assertEqual(read_env_file_values()["GITPR_AI_TIMEOUT"], "180")

        run(scenario())


class TestCredentialValidation(ConfigAppTestCase):
    """Decision 14: only a rejected credential blocks the save.

    A network failure has to let the value through, otherwise a correct key
    typed on a machine behind a proxy could never be stored at all.
    """

    def type_gemini_key(self, app):
        app.query_one("#categories", ListView).index = 1
        secret = app.query_one("#value_GEMINI_API_KEY_ENCRYPTED", Input)
        secret.value = "typed-key"

    def test_an_accepted_key_is_saved(self):
        self.probe_result = (True, "", "")

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.type_gemini_key(app)
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(
                    read_env_file_values()["GEMINI_API_KEY_ENCRYPTED"],
                    "enc(typed-key)",
                )

        run(scenario())

    def test_a_rejected_key_blocks_the_save(self):
        self.probe_result = (False, VALIDATION_AUTH, "rejected")

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.type_gemini_key(app)
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertNotIn("GEMINI_API_KEY_ENCRYPTED", read_env_file_values())
                # Still on screen with the edit intact, so it can be corrected.
                self.assertTrue(app.is_running)
                self.assertTrue(app.is_dirty(FIELDS_BY_KEY["GEMINI_API_KEY_ENCRYPTED"]))

        run(scenario())

    def test_an_unreachable_provider_still_saves(self):
        self.probe_result = (False, VALIDATION_NETWORK, "unreachable")

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.type_gemini_key(app)
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(
                    read_env_file_values()["GEMINI_API_KEY_ENCRYPTED"],
                    "enc(typed-key)",
                )

        run(scenario())

    def test_the_key_reaches_the_probe_unencrypted(self):
        """The provider has to be asked about the key the user typed, not the
        Fernet blob that is about to be written."""
        seen = []
        self.probe_result = (True, "", "")

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.type_gemini_key(app)
                await pilot.pause()
                with patch(
                    "src.ui.config_app.validate_ai_key",
                    side_effect=lambda provider, key: seen.append((provider, key))
                    or (True, "", ""),
                ):
                    await pilot.press("f2")
                    await pilot.pause()
                self.assertEqual(seen, [("gemini", "typed-key")])

        run(scenario())

    def test_an_unchanged_secret_is_not_probed(self):
        """Decision 13: only the credentials edited in this session are checked,
        so opening the screen and pressing F2 costs no network round trip."""
        calls = []

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                with patch(
                    "src.ui.config_app.validate_ai_key",
                    side_effect=lambda provider, key: calls.append(provider)
                    or (True, "", ""),
                ):
                    app.query_one("#categories", ListView).index = 1
                    await pilot.pause()
                    await pilot.press("f2")
                    await pilot.pause()
                self.assertEqual(calls, [])

        run(scenario())


class TestNonSecretValidationStillSaves(ConfigAppTestCase):
    def test_a_valid_edit_alongside_a_blocked_secret_is_not_written(self):
        """The whole save is rejected, not just the offending field — a partial
        write would leave the file in a state the user never asked for."""
        self.probe_result = (False, VALIDATION_AUTH, "rejected")

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                app.query_one("#categories", ListView).index = 1
                await pilot.pause()
                app.query_one("#value_GEMINI_API_KEY_ENCRYPTED", Input).value = "k"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(read_env_file_values()["GITPR_AI_TIMEOUT"], "180")

        run(scenario())


class SectionedAppTestCase(ConfigAppTestCase):
    """Base for the tests that need a different .env than SEEDED_ENV."""

    def seed(self, text):
        """Rewrites the .env the screen reads at mount time."""
        with open(self.env_path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def shown_rows(self, app):
        """Ids of the rows currently displayed."""
        return [row.id for row in app.query(".field") if row.display]

    def goto(self, app, category_id):
        app.query_one("#categories", ListView).index = (
            app.sidebar_categories().index(category_id)
        )


class TestProviderSections(SectionedAppTestCase):
    """Item 3: the AI section lists the selected provider's variables only."""

    def test_only_the_selected_provider_is_listed(self):
        async def scenario():
            self.seed("DEFAULT_AI_PROVIDER=deepseek\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.goto(app, "ai")
                await pilot.pause()
                rows = self.shown_rows(app)
                self.assertIn("row_DEFAULT_AI_PROVIDER", rows)
                self.assertIn("row_DEEPSEEK_API_MODEL_PRIMARY", rows)
                self.assertNotIn("row_GEMINI_API_MODEL_PRIMARY", rows)
                self.assertNotIn("row_OLLAMA_API_MODEL_PRIMARY", rows)

        run(scenario())

    def test_selecting_another_provider_refilters_without_saving(self):
        async def scenario():
            self.seed("DEFAULT_AI_PROVIDER=deepseek\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.goto(app, "ai")
                await pilot.pause()
                app.query_one("#value_DEFAULT_AI_PROVIDER", Select).value = "ollama"
                await pilot.pause()
                rows = self.shown_rows(app)
                self.assertIn("row_OLLAMA_API_MODEL_PRIMARY", rows)
                self.assertNotIn("row_DEEPSEEK_API_MODEL_PRIMARY", rows)

        run(scenario())

    def test_an_empty_provider_mounts_and_reads_as_not_configured(self):
        # Regression: Select(value="", allow_blank=False) raises at mount, and
        # an empty line in the .env is exactly what produces that value.
        async def scenario():
            self.seed("DEFAULT_AI_PROVIDER=\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.goto(app, "ai")
                await pilot.pause()
                select = app.query_one("#value_DEFAULT_AI_PROVIDER", Select)
                self.assertEqual(select.value, "")
                labels = [label for label, _ in select._options]
                self.assertIn("(not configured)", labels)

        run(scenario())

    def test_the_search_still_finds_an_unselected_provider(self):
        # The search ignores the gate on purpose: a value typed for a provider
        # that is not the default has to stay reachable from the screen.
        async def scenario():
            self.seed("DEFAULT_AI_PROVIDER=deepseek\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#search", Input).value = "ollama"
                await pilot.pause()
                self.assertIn("row_OLLAMA_API_MODEL_PRIMARY", self.shown_rows(app))

        run(scenario())


class TestForgeSections(SectionedAppTestCase):
    """Item 2: the SCM section is split per forge, the token left loose."""

    def test_the_default_forge_is_github(self):
        async def scenario():
            self.seed("GITPR_SCM_PROVIDER=\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.goto(app, "scm")
                await pilot.pause()
                rows = self.shown_rows(app)
                self.assertIn("row_GITHUB_TOKEN_ENCRYPTED", rows)
                self.assertNotIn("row_GITPR_SCM_ORGANIZATION", rows)
                self.assertNotIn("row_GITPR_SCM_USERNAME", rows)
                self.assertTrue(app.query_one("#grp_github").display)
                self.assertFalse(app.query_one("#grp_azure_devops").display)

        run(scenario())

    def test_another_forge_hides_the_github_group(self):
        async def scenario():
            self.seed("GITPR_SCM_PROVIDER=azure_devops\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.goto(app, "scm")
                await pilot.pause()
                rows = self.shown_rows(app)
                self.assertIn("row_GITPR_SCM_ORGANIZATION", rows)
                self.assertNotIn("row_GITHUB_TOKEN_ENCRYPTED", rows)

        run(scenario())

    def test_the_scm_token_is_listed_for_every_forge_and_stays_hidden(self):
        # Item 1: it was landing in the Unknown section. It is read for every
        # forge, so it sits outside the forge groups — and it is a secret, so
        # its value is never rendered back.
        async def scenario():
            for provider in ("", "azure_devops"):
                self.seed(
                    "GITPR_SCM_PROVIDER={}\nGITPR_SCM_TOKEN=segredo\n".format(provider)
                )
                app = self.make_app()
                async with app.run_test() as pilot:
                    await pilot.pause()
                    self.goto(app, "scm")
                    await pilot.pause()
                    self.assertIn("row_GITPR_SCM_TOKEN", self.shown_rows(app))
                    control = app.query_one("#value_GITPR_SCM_TOKEN", Input)
                    self.assertEqual(control.value, "")
                    self.assertTrue(control.disabled)
                    self.assertNotIn("GITPR_SCM_TOKEN", app.unknown_keys)

        run(scenario())


class TestAdvancedLayout(SectionedAppTestCase):
    """Items 4, 5 and 9: version fallback, word list, field order."""

    WORDS = "|".join("palavra{}".format(n) for n in range(30))

    def test_the_version_marker_sits_right_after_the_word_list(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#show_advanced", Switch).value = True
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                rows = self.shown_rows(app)
                self.assertEqual(
                    rows[:2],
                    ["row_SPINNER_THINKING_WORDS", "row_THINKING_WORDS_VERSION"],
                )

        run(scenario())

    def test_a_missing_marker_shows_the_code_version_and_says_so(self):
        # Item 4: LINTER_PRESETS_VERSION is only stamped by --linter-setup, so
        # the box stayed blank for everyone who never ran that command.
        async def scenario():
            from src.updater import __lang_version__

            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#show_advanced", Switch).value = True
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                self.assertEqual(
                    app.query_one("#value_LINTER_PRESETS_VERSION", Input).value,
                    __lang_version__,
                )
                annotation = app.query_one("#mark_LINTER_PRESETS_VERSION", Static)
                self.assertIn("not set in the file", str(annotation.render()))

        run(scenario())

    def test_the_word_list_is_a_list_and_not_an_input(self):
        async def scenario():
            self.seed("SPINNER_THINKING_WORDS={}\n".format(self.WORDS))
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#show_advanced", Switch).value = True
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                self.assertFalse(app.query("#value_SPINNER_THINKING_WORDS Input"))
                text = str(
                    app.query_one("#words_SPINNER_THINKING_WORDS", Static).render()
                )
                self.assertIn("palavra0 · palavra1", text)
                self.assertIn("palavra29", text)
                annotation = app.query_one("#mark_SPINNER_THINKING_WORDS", Static)
                self.assertIn("30 word(s)", str(annotation.render()))

        run(scenario())

    def test_an_empty_word_list_explains_the_fallback(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#show_advanced", Switch).value = True
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                text = str(
                    app.query_one("#words_SPINNER_THINKING_WORDS", Static).render()
                )
                self.assertIn("built-in list", text)
                annotation = app.query_one("#mark_SPINNER_THINKING_WORDS", Static)
                self.assertIn("0 word(s)", str(annotation.render()))

        run(scenario())

    def test_the_pane_still_scrolls_over_the_new_rows(self):
        # The word box and the action row added height to a category that was
        # already the tallest one; the pane has to keep scrolling as a whole
        # instead of clipping the last setting.
        async def scenario():
            self.seed("SPINNER_THINKING_WORDS={}\n".format(self.WORDS))
            app = self.make_app()
            async with app.run_test(size=(100, 24)) as pilot:
                await pilot.pause()
                app.query_one("#show_advanced", Switch).value = True
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                main = app.query_one("#main")
                self.assertGreater(main.max_scroll_y, 0)
                main.scroll_end(animate=False)
                await pilot.pause()
                self.assertEqual(main.scroll_offset.y, main.max_scroll_y)
                # The last row of the category is on screen once scrolled there.
                last = app.query(".field")[-1]
                self.assertTrue(main.region.contains_region(last.region))

        run(scenario())


class TestDownloadButtons(SectionedAppTestCase):
    """Items 5, 7 and 8: the buttons force a download and report the file.

    The loaders are replaced by fakes that write to the temp .env: what is
    under test is the screen's half — dispatch, run, verdict — not the network.
    """

    def show_advanced(self, app):
        """Turns the advanced toggle on — only valid while the app is running."""
        app.query_one("#show_advanced", Switch).value = True

    def test_a_successful_download_reports_the_marker_found_in_the_file(self):
        async def scenario():
            from src.updater import __lang_version__
            from src.ui import config_app
            from dotenv import set_key

            def fake_loader():
                set_key(self.env_path, "LINTER_PRESETS_VERSION", __lang_version__)

            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.show_advanced(app)
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                button = app.query_one("#act_LINTER_PRESETS_VERSION", Button)
                with patch.dict(
                    config_app._DOWNLOAD_SOURCES,
                    {"LINTER_PRESETS_VERSION": fake_loader},
                ), patch.object(app, "notify") as notify:
                    button.press()
                    await app.workers.wait_for_complete()
                    await pilot.pause()
                self.assertIn(
                    "✔",
                    str(app.query_one("#status_LINTER_PRESETS_VERSION", Static).render()),
                )
                notify.assert_called_once()
                self.assertIn("up to date", notify.call_args.args[0])
                self.assertIn(
                    __lang_version__, notify.call_args.args[0]
                )
                # The note that sent the user to the button is gone.
                annotation = app.query_one("#mark_LINTER_PRESETS_VERSION", Static)
                self.assertNotIn("not set in the file", str(annotation.render()))

        run(scenario())

    def test_the_button_is_disabled_while_the_download_runs(self):
        async def scenario():
            from src.ui import config_app
            import threading

            gate = threading.Event()

            def slow_loader():
                gate.wait(timeout=10)

            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.show_advanced(app)
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                button = app.query_one("#act_LINTER_PRESETS_VERSION", Button)
                with patch.dict(
                    config_app._DOWNLOAD_SOURCES,
                    {"LINTER_PRESETS_VERSION": slow_loader},
                ):
                    button.press()
                    await pilot.pause()
                    self.assertTrue(button.disabled)
                    gate.set()
                    await app.workers.wait_for_complete()
                    await pilot.pause()
                self.assertFalse(button.disabled)

        run(scenario())

    def test_a_failed_download_keeps_the_previous_copy(self):
        async def scenario():
            from src.ui import config_app

            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.show_advanced(app)
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                button = app.query_one("#act_SMART_EXCLUDES_VERSION", Button)
                with patch.dict(
                    config_app._DOWNLOAD_SOURCES,
                    {"SMART_EXCLUDES_VERSION": lambda: None},
                ), patch.object(app, "notify") as notify:
                    button.press()
                    await app.workers.wait_for_complete()
                    await pilot.pause()
                # No marker appeared in the file, so the screen must not claim
                # the list was refreshed.
                self.assertIn(
                    "✖",
                    str(app.query_one("#status_SMART_EXCLUDES_VERSION", Static).render()),
                )
                self.assertIn("previous copy", notify.call_args.args[0])
                self.assertEqual(notify.call_args.kwargs.get("severity"), "error")
                self.assertFalse(button.disabled)

        run(scenario())

    def test_the_word_list_button_refreshes_the_list_and_its_marker(self):
        async def scenario():
            from src.updater import __lang_version__
            from src.ui import config_app
            from dotenv import set_key

            def fake_loader():
                set_key(self.env_path, "SPINNER_THINKING_WORDS", "alfa|beta|gama")
                set_key(self.env_path, "THINKING_WORDS_VERSION", __lang_version__)

            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.show_advanced(app)
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                with patch.dict(
                    config_app._DOWNLOAD_SOURCES,
                    {"SPINNER_THINKING_WORDS": fake_loader},
                ), patch.object(app, "notify"):
                    app.query_one("#act_SPINNER_THINKING_WORDS", Button).press()
                    await app.workers.wait_for_complete()
                    await pilot.pause()
                text = str(
                    app.query_one("#words_SPINNER_THINKING_WORDS", Static).render()
                )
                self.assertEqual(text, "alfa · beta · gama")
                annotation = app.query_one("#mark_SPINNER_THINKING_WORDS", Static)
                self.assertIn("3 word(s)", str(annotation.render()))
                # The word list is proven by the version line, which has a row
                # of its own and was stale until the download landed.
                marker = app.query_one("#mark_THINKING_WORDS_VERSION", Static)
                self.assertNotIn("not set in the file", str(marker.render()))

        run(scenario())

    def test_english_has_no_pack_to_download(self):
        async def scenario():
            from src.ui import config_app

            calls = []
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.show_advanced(app)
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                with patch(
                    "src.ui.config_app._current_lang", return_value="en_us"
                ), patch.dict(
                    config_app._DOWNLOAD_SOURCES,
                    {"LANG_VERSION": lambda: calls.append(1)},
                ), patch.object(
                    app, "notify"
                ) as notify:
                    app.query_one("#act_LANG_VERSION", Button).press()
                    await pilot.pause()
                # Refused before the worker starts: nothing was fetched, and
                # the user is told why instead of seeing a failed download.
                self.assertEqual(calls, [])
                self.assertIn("English needs no translation pack", notify.call_args.args[0])

        run(scenario())

    def test_ctrl_r_reaches_the_field_when_its_button_has_the_focus(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.show_advanced(app)
                await pilot.pause()
                self.goto(app, "advanced")
                await pilot.pause()
                app.query_one("#act_LINTER_PRESETS_VERSION", Button).focus()
                await pilot.pause()
                field = app._focused_field()
                self.assertIsNotNone(field)
                self.assertEqual(field.key, "LINTER_PRESETS_VERSION")
                # A read-only field answers Ctrl+R with the "managed by GitPR"
                # notice; silence would mean the focus walk lost the field.
                with patch.object(app, "notify") as notify:
                    await pilot.press("ctrl+r")
                    await pilot.pause()
                notify.assert_called_once()

        run(scenario())


# --------------------------------------------------------------------- Skills
# The section edits the AI instruction files of the project the screen was
# opened in — get_skill_dir() resolves against the working directory — so these
# tests build a project folder of their own and run the screen from inside it.

# Mixed line endings on purpose: that is what the files in the wild look like,
# and a write that ignored it would show up as the whole file changed in git.
SKILL_SEED = {
    ".gitpr.commit.md": "# commit rules\r\n",
    ".gitpr.pr.md": "# pr rules\n",
    ".gitpr.review.md": "# review rules\n",
    ".gitpr.issue.md": "# issue rules\n",
    ".gitpr.blame.md": "# blame rules\n",
    ".gitpr.release.md": "# release rules\n",
}
# A supported skill this project has no file for: what the download button is for.
ABSENT_SKILL = "filereview"
# Present in the folder, and deliberately not a skill of get_skill_context().
NOT_A_SKILL = ".gitpr.linter.yml"


class SkillsAppTestCase(SectionedAppTestCase):
    """Base for the Skills section: a project folder with real skill files."""

    def setUp(self):
        super().setUp()
        self.project = tempfile.TemporaryDirectory()
        self.addCleanup(self.project.cleanup)
        self.skill_dir = os.path.join(self.project.name, ".gitpr", "skill")
        os.makedirs(self.skill_dir)
        for name, text in SKILL_SEED.items():
            self.write_skill(name, text)
        self.write_skill(NOT_A_SKILL, "rules: []\n")
        self._cwd = os.getcwd()
        # LIFO: this runs before the folder is removed, which Windows refuses
        # while it is still the working directory.
        self.addCleanup(os.chdir, self._cwd)
        os.chdir(self.project.name)

    def skill_path(self, name):
        return os.path.join(self.skill_dir, name)

    def write_skill(self, name, text):
        """Writes raw bytes: newline="" keeps a CRLF file a CRLF file."""
        path = self.skill_path(name)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def read_skill(self, name):
        """Reads raw bytes back, so an assertion can see the line endings."""
        with open(self.skill_path(name), "r", encoding="utf-8", newline="") as handle:
            return handle.read()

    def item_text(self, app, skill_type):
        widget = app.query_one(f"#skillitem_{skill_type} Static", Static)
        return str(widget.render())

    def editor(self, app):
        return app.query_one("#skill_editor", TextArea)

    async def open_skill(self, app, pilot, skill_type):
        """Navigates to the section and highlights one skill in the list."""
        self.goto(app, "skills")
        await pilot.pause()
        app.query_one("#skills_list", ListView).index = SKILL_TYPES.index(skill_type)
        await pilot.pause()
        return self.editor(app)


class TestSkillsSection(SkillsAppTestCase):
    def test_the_sidebar_lists_a_skills_section(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.assertIn("cat_skills", sidebar_ids(app))
                self.assertFalse(app.query_one("#skills_pane").display)
                await self.open_skill(app, pilot, "pr")
                self.assertEqual(app.selected_category(), "skills")
                self.assertTrue(app.query_one("#skills_pane").display)

        run(scenario())

    def test_the_folder_field_shows_where_the_skills_live(self):
        """The one row of the section, and the reason the pane exists: the
        folder is resolved from the directory gitpr was started in."""

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.goto(app, "skills")
                await pilot.pause()
                value = app.query_one("#value_SKILLS_FOLDER", Input).value
                self.assertEqual(
                    os.path.normcase(value), os.path.normcase(self.skill_dir)
                )

        run(scenario())

    def test_only_the_supported_skills_are_listed(self):
        """The list comes from the registry, not from the folder: a file that
        get_skill_context() does not read is not offered for editing."""

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                await self.open_skill(app, pilot, "pr")
                ids = [item.id for item in app.query("#skills_list ListItem")]
                self.assertEqual(ids, [f"skillitem_{t}" for t in SKILL_TYPES])
                # The file is there — the screen is what must not offer it.
                self.assertTrue(os.path.exists(self.skill_path(NOT_A_SKILL)))

        run(scenario())

    def test_a_skill_missing_from_the_project_is_marked_and_not_editable(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.assertIn(
                    "not in this project",
                    self.item_text(app, ABSENT_SKILL),
                )
                editor = await self.open_skill(app, pilot, ABSENT_SKILL)
                self.assertFalse(editor.display)
                self.assertTrue(editor.read_only)
                self.assertTrue(app.query_one("#skill_absent_note").display)
                self.assertTrue(app.query_one("#skill_actions").display)
                self.assertFalse(app.query_one("#skill_download", Button).disabled)

        run(scenario())

    def test_typing_in_the_editor_marks_the_skill_as_edited(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "pr")
                editor.focus()
                await pilot.press("x")
                await pilot.pause()
                self.assertIn("● edited", self.item_text(app, "pr"))
                self.assertEqual(app.dirty_skills(), ["pr"])
                self.assertIn(
                    "1", str(app.query_one("#dirty_indicator", Static).content)
                )
                # Nothing is on disk until F2.
                self.assertEqual(self.read_skill(".gitpr.pr.md"), "# pr rules\n")

        run(scenario())

    def test_saving_writes_the_skill_file_and_clears_the_pending_edit(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "pr")
                editor.text = "# pr rules v2\n"
                await pilot.pause()
                self.assertTrue(app.dirty_skills())
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(self.read_skill(".gitpr.pr.md"), "# pr rules v2\n")
                self.assertEqual(app.dirty_skills(), [])
                self.assertNotIn("● edited", self.item_text(app, "pr"))
                self.assertFalse(
                    str(app.query_one("#dirty_indicator", Static).content)
                )

        run(scenario())

    def test_saving_keeps_the_line_endings_the_file_already_had(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "commit")
                editor.text = "# commit rules v2\n"
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "pr")
                editor.text = "# pr rules v2\n"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                # .gitpr.commit.md was seeded CRLF and .gitpr.pr.md LF: each one
                # keeps the separator it had, so git sees the edit, not the file.
                self.assertEqual(
                    self.read_skill(".gitpr.commit.md"), "# commit rules v2\r\n"
                )
                self.assertEqual(self.read_skill(".gitpr.pr.md"), "# pr rules v2\n")

        run(scenario())

    def test_a_skill_and_a_setting_are_saved_by_the_same_f2(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#value_GITPR_AI_TIMEOUT", Input).value = "300"
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "pr")
                editor.text = "# both\n"
                await pilot.pause()
                await pilot.press("f2")
                await pilot.pause()
                self.assertEqual(read_env_file_values()["GITPR_AI_TIMEOUT"], "300")
                self.assertEqual(self.read_skill(".gitpr.pr.md"), "# both\n")
                self.assertEqual(app.dirty_skills(), [])

        run(scenario())

    def test_a_skill_that_cannot_be_written_is_read_only(self):
        """The prerequisite the plan asks for: the file is checked before the
        editor is offered. Not even a keystroke may get in."""

        async def scenario():
            from src.ui import config_app

            real_status = config_app.skill_file_status
            target = self.skill_path(".gitpr.pr.md")

            def status(skill_type):
                if config_app.SKILL_FILES_BY_TYPE.get(skill_type) == ".gitpr.pr.md":
                    return "readonly", target
                return real_status(skill_type)

            with patch("src.ui.config_app.skill_file_status", side_effect=status):
                app = self.make_app()
                async with app.run_test() as pilot:
                    await pilot.pause()
                    editor = await self.open_skill(app, pilot, "pr")
                    self.assertTrue(editor.read_only)
                    self.assertIn("read only", self.item_text(app, "pr"))
                    editor.focus()
                    await pilot.press("x")
                    await pilot.pause()
                    self.assertEqual(app.dirty_skills(), [])
                    self.assertEqual(self.read_skill(".gitpr.pr.md"), "# pr rules\n")

        run(scenario())

    def test_a_skill_that_fails_to_write_keeps_the_edit_pending(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "pr")
                editor.text = "# half written\n"
                await pilot.pause()
                with patch(
                    "src.ui.config_app.write_skill_file",
                    side_effect=OSError("denied"),
                ), patch.object(app, "notify") as notify:
                    await pilot.press("f2")
                    await pilot.pause()
                self.assertEqual(self.read_skill(".gitpr.pr.md"), "# pr rules\n")
                self.assertEqual(app.dirty_skills(), ["pr"])
                self.assertEqual(editor.text, "# half written\n")
                # The error is reported before the save summary that follows it,
                # so the whole call list is checked rather than the last call.
                self.assertTrue(
                    any(
                        call.kwargs.get("severity") == "error"
                        and "Could not write" in call.args[0]
                        for call in notify.call_args_list
                    ),
                    [call.args for call in notify.call_args_list],
                )

        run(scenario())

    def test_ctrl_r_reverts_a_skill_edit(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "pr")
                editor.text = "# typed by mistake\n"
                await pilot.pause()
                self.assertTrue(app.dirty_skills())
                editor.focus()
                await pilot.press("ctrl+r")
                await pilot.pause()
                self.assertEqual(app.dirty_skills(), [])
                self.assertEqual(editor.text, "# pr rules\n")
                self.assertEqual(self.read_skill(".gitpr.pr.md"), "# pr rules\n")

        run(scenario())

    def test_escape_asks_before_discarding_a_skill_edit(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "pr")
                editor.text = "# unsaved\n"
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                self.assertIsInstance(app.screen, ConfirmDiscardScreen)

        run(scenario())

    def test_switching_skills_keeps_each_edit(self):
        """The edits live in skill_pending, not in the widget, so walking the
        list and coming back returns to the same text."""

        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "pr")
                editor.text = "# half written\n"
                await pilot.pause()
                editor = await self.open_skill(app, pilot, "commit")
                self.assertEqual(editor.text, "# commit rules\n")
                editor = await self.open_skill(app, pilot, "pr")
                self.assertEqual(editor.text, "# half written\n")
                self.assertEqual(app.dirty_skills(), ["pr"])

        run(scenario())

    def test_search_hides_the_skills_pane(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                await self.open_skill(app, pilot, "pr")
                search = app.query_one("#search", Input)
                search.value = "commit"
                await pilot.pause()
                self.assertFalse(app.query_one("#skills_pane").display)
                search.value = ""
                await pilot.pause()
                self.assertTrue(app.query_one("#skills_pane").display)

        run(scenario())

    def test_the_download_button_fills_an_absent_skill(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                await self.open_skill(app, pilot, ABSENT_SKILL)

                def fake_download(local_name, remote_name, **kwargs):
                    self.write_skill(local_name, "# downloaded filereview\n")
                    return True

                with patch(
                    "src.core.download_skill_file", side_effect=fake_download
                ) as download, patch.object(app, "notify"):
                    app.query_one("#skill_download", Button).press()
                    await app.workers.wait_for_complete()
                    await pilot.pause()

                self.assertEqual(
                    self.read_skill(".gitpr.filereview.md"),
                    "# downloaded filereview\n",
                )
                self.assertEqual(
                    self.editor(app).text, "# downloaded filereview\n"
                )
                self.assertFalse(self.editor(app).read_only)
                self.assertNotIn(
                    "not in this project", self.item_text(app, ABSENT_SKILL)
                )
                self.assertEqual(download.call_args.args[0], ".gitpr.filereview.md")
                # The published template is the language variant of the file.
                self.assertTrue(
                    download.call_args.args[1].startswith("gitpr.filereview")
                )

        run(scenario())

    def test_a_failed_download_says_so_and_leaves_the_skill_absent(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                await self.open_skill(app, pilot, ABSENT_SKILL)
                with patch(
                    "src.core.download_skill_file", return_value=False
                ), patch.object(app, "notify") as notify:
                    app.query_one("#skill_download", Button).press()
                    await app.workers.wait_for_complete()
                    await pilot.pause()
                self.assertIn(
                    "not in this project", self.item_text(app, ABSENT_SKILL)
                )
                self.assertFalse(
                    os.path.exists(self.skill_path(".gitpr.filereview.md"))
                )
                # The button comes back, so the user can try again.
                self.assertFalse(app.query_one("#skill_download", Button).disabled)
                self.assertEqual(notify.call_args.kwargs.get("severity"), "error")
                self.assertIn("Could not download", notify.call_args.args[0])

        run(scenario())


class TestDocumentationLink(SectionedAppTestCase):
    """Item 11: every section links to its own technical page."""

    PAGES = {
        "general": "config-tui",
        "ai": "providers-ia",
        "pr": "pull-request-publication",
        "review": "code-review-ia",
        "issue": "gitpr-issue-option",
        "blame": "blame-arqueologo",
        "linter": "linter-regras-customizadas",
        "release": "release-notes",
        "scm": "scm-multiforge",
        "diff": "smart-excludes",
        "skills": "skill-template",
        "advanced": "version-markers",
    }

    def test_every_section_shows_its_page(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#show_advanced", Switch).value = True
                await pilot.pause()
                for category_id, page in self.PAGES.items():
                    self.goto(app, category_id)
                    await pilot.pause()
                    url = str(app.query_one("#doc_url", Static).render())
                    self.assertIn("/docs/{}".format(page), url)
                    self.assertTrue(
                        app.query_one("#category_doc").display,
                        "{} has no visible doc link".format(category_id),
                    )

        run(scenario())

    def test_the_button_opens_the_page_of_the_section(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.goto(app, "scm")
                await pilot.pause()
                url = str(app.query_one("#doc_url", Static).render())
                with patch("webbrowser.open") as open_url:
                    app.query_one("#doc_open", Button).press()
                    await pilot.pause()
                open_url.assert_called_once_with(url)

        run(scenario())

    def test_the_unknown_section_shows_no_link(self):
        # It has no Category, hence no page — and it must not offer the page of
        # whichever section happened to be selected before.
        async def scenario():
            self.seed("UMA_CHAVE_QUALQUER=1\n")
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.goto(app, "unknown")
                await pilot.pause()
                self.assertFalse(app.query_one("#category_doc").display)

        run(scenario())

    def test_the_search_hides_the_link(self):
        async def scenario():
            app = self.make_app()
            async with app.run_test() as pilot:
                await pilot.pause()
                self.assertTrue(app.query_one("#category_doc").display)
                app.query_one("#search", Input).value = "timeout"
                await pilot.pause()
                self.assertFalse(app.query_one("#category_doc").display)

        run(scenario())


if __name__ == "__main__":
    unittest.main()
