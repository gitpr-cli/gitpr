"""Tests for src/ui/pr_publish_app.py beyond the linter modal.

Complements tests/test_pr_publish_linter_modal.py, which owns the
LinterErrorScreen flow. Everything here is headless: Git, AI and the GitHub
API are mocked, so no test needs a repository, a token or the network.

TRANSLATIONS is pinned to {} wherever a test asserts on user-facing English,
so results do not depend on the machine's OS locale.
"""
import asyncio
from unittest.mock import patch

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, Input, SelectionList, Static, TextArea

from src.ui.pr_publish_app import (
    CommitConfirmScreen,
    CommitMessageScreen,
    ErrorScreen,
    PrPublishApp,
    StageFilesApp,
    StageFilesScreen,
)


class _ModalHostApp(App):
    """Minimal host app to exercise a single modal screen in isolation."""

    def __init__(self, screen, **kwargs):
        super().__init__(**kwargs)
        self._hosted = screen
        self.screen_result = None

    def compose(self) -> ComposeResult:
        yield Static("")

    def on_mount(self):
        self.push_screen(self._hosted, callback=self._on_result)

    def _on_result(self, result):
        self.screen_result = result


def _run(coro_factory):
    """Runs an async test body on a fresh event loop."""
    asyncio.run(coro_factory())


# ═══════════════════════════════════════════════════════════════════
# StageFilesScreen — selection must come from the widget, not a mirror dict
# ═══════════════════════════════════════════════════════════════════

FILES = [("src/a.py", "M"), ("src/b.py", "??"), ("src/c.py", "D")]


class TestStageFilesScreen:
    def test_stage_reads_selection_from_the_widget(self):
        """Regression: a parallel 'selected' dict desynced from the SelectionList.

        Individual row toggles are tracked only by the widget, so the result
        must be read back from it — not from the dict passed at construction.
        """

        async def run():
            screen = StageFilesScreen(files=FILES, selected={f: True for f, _ in FILES})
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                selection = app.screen.query_one("#file_list", SelectionList)
                selection.deselect_all()
                selection.select("src/b.py")
                await pilot.pause()

                app.screen.query_one("#btn_stage", Button).press()
                await pilot.pause()

            assert screen.result == "stage"
            assert screen.staged == ["src/b.py"]

        _run(run)

    def test_select_all_stages_every_file(self):
        async def run():
            screen = StageFilesScreen(files=FILES, selected={f: False for f, _ in FILES})
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one("#btn_select_all", Button).press()
                await pilot.pause()
                app.screen.query_one("#btn_stage", Button).press()
                await pilot.pause()

            assert sorted(screen.staged) == ["src/a.py", "src/b.py", "src/c.py"]

        _run(run)

    def test_deselect_all_stages_nothing(self):
        async def run():
            screen = StageFilesScreen(files=FILES, selected={f: True for f, _ in FILES})
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one("#btn_deselect_all", Button).press()
                await pilot.pause()
                app.screen.query_one("#btn_stage", Button).press()
                await pilot.pause()

            assert screen.result == "stage"
            assert screen.staged == []

        _run(run)

    @pytest.mark.parametrize(
        "button_id,expected", [("btn_skip", "skip"), ("btn_cancel", "cancel")]
    )
    def test_skip_and_cancel_dismiss_with_their_result(self, button_id, expected):
        async def run():
            screen = StageFilesScreen(files=FILES, selected={f: True for f, _ in FILES})
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one(f"#{button_id}", Button).press()
                await pilot.pause()

            assert screen.result == expected
            assert app.screen_result == expected

        _run(run)

    def test_cancel_stages_no_files(self):
        """Cancelling must never leave files staged — no destructive side effect."""

        async def run():
            screen = StageFilesScreen(files=FILES, selected={f: True for f, _ in FILES})
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one("#btn_cancel", Button).press()
                await pilot.pause()

            assert screen.staged == []

        _run(run)


class TestStageFilesApp:
    def test_app_exposes_selected_files_on_stage(self):
        async def run():
            app = StageFilesApp(unstaged_files=FILES)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                selection = app.screen.query_one("#file_list", SelectionList)
                selection.deselect_all()
                selection.select("src/a.py")
                await pilot.pause()
                app.screen.query_one("#btn_stage", Button).press()
                await pilot.pause()

            assert app.result == "stage"
            assert app.selected_files == ["src/a.py"]

        _run(run)

    def test_app_reports_cancel_without_files(self):
        async def run():
            app = StageFilesApp(unstaged_files=FILES)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one("#btn_cancel", Button).press()
                await pilot.pause()

            assert app.result == "cancel"
            assert app.selected_files == []

        _run(run)


# ═══════════════════════════════════════════════════════════════════
# CommitConfirmScreen / CommitMessageScreen / ErrorScreen
# ═══════════════════════════════════════════════════════════════════


class TestCommitConfirmScreen:
    @pytest.mark.parametrize(
        "button_id,expected", [("btn_yes", "yes"), ("btn_no", "no")]
    )
    def test_buttons_dismiss_with_expected_result(self, button_id, expected):
        async def run():
            screen = CommitConfirmScreen(title="T", message="M")
            app = _ModalHostApp(screen)
            async with app.run_test(size=(80, 24)) as pilot:
                await pilot.pause()
                app.screen.query_one(f"#{button_id}", Button).press()
                await pilot.pause()

            assert app.screen_result == expected

        _run(run)


class TestCommitMessageScreen:
    def test_confirm_returns_the_edited_message(self):
        async def run():
            screen = CommitMessageScreen(commit_message="feat: original")
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one("#msg_input", Input).value = "feat: edited"
                await pilot.pause()
                app.screen.query_one("#btn_confirm", Button).press()
                await pilot.pause()

            assert app.screen_result == "confirm"
            assert screen._commit_message == "feat: edited"

        _run(run)

    def test_empty_message_is_rejected_and_modal_stays_open(self):
        async def run():
            screen = CommitMessageScreen(commit_message="feat: original")
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one("#msg_input", Input).value = "   "
                await pilot.pause()
                app.screen.query_one("#btn_confirm", Button).press()
                await pilot.pause()

                assert screen.result is None, "empty message must not confirm"
            assert app.screen_result is None

        _run(run)

    def test_message_is_stripped(self):
        async def run():
            screen = CommitMessageScreen(commit_message="x")
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one("#msg_input", Input).value = "  fix: pad  "
                await pilot.pause()
                app.screen.query_one("#btn_confirm", Button).press()
                await pilot.pause()

            assert screen._commit_message == "fix: pad"

        _run(run)

    def test_cancel_leaves_message_untouched(self):
        async def run():
            screen = CommitMessageScreen(commit_message="feat: original")
            app = _ModalHostApp(screen)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                app.screen.query_one("#msg_input", Input).value = "feat: edited"
                await pilot.pause()
                app.screen.query_one("#btn_cancel", Button).press()
                await pilot.pause()

            assert app.screen_result == "cancel"
            assert screen._commit_message == "feat: original"

        _run(run)


class TestErrorScreen:
    @pytest.mark.parametrize(
        "button_id,expected", [("btn_retry", "retry"), ("btn_cancel", "cancel")]
    )
    def test_buttons_dismiss_with_expected_result(self, button_id, expected):
        async def run():
            screen = ErrorScreen(title="❌ Merge Conflict", message="cannot merge")
            app = _ModalHostApp(screen)
            async with app.run_test(size=(80, 24)) as pilot:
                await pilot.pause()
                app.screen.query_one(f"#{button_id}", Button).press()
                await pilot.pause()

            assert app.screen_result == expected

        _run(run)

    def test_long_message_is_truncated(self):
        """A huge API error body must not blow up the dialog layout."""
        screen = ErrorScreen(title="T", message="x" * 900)
        assert len(screen._message) == 500

    def test_none_message_becomes_empty_string(self):
        screen = ErrorScreen(title="T", message=None)
        assert screen._message == ""


# ═══════════════════════════════════════════════════════════════════
# PrPublishApp — construction, F2 save, and state transitions
# ═══════════════════════════════════════════════════════════════════

PR_DATA = {"commit_message": "feat: add thing", "pr_description": "## What\nstuff"}


def _make_app(output_filename, **overrides):
    kwargs = dict(
        pr_data=PR_DATA,
        repo_info="natanfiuza/gitpr",
        github_token="ghp_fake",
        base_branch="main",
        output_filename=str(output_filename),
    )
    kwargs.update(overrides)
    return PrPublishApp(**kwargs)


@pytest.fixture(autouse=True)
def _no_publish_log(tmp_path):
    """Keep the publish log out of the real repo during tests."""
    with patch(
        "src.ui.pr_publish_app._init_publish_log", return_value=str(tmp_path / "pub.log")
    ):
        with patch("src.ui.pr_publish_app._log_event"):
            yield


class TestPrPublishAppConstruction:
    def test_title_and_body_seeded_from_pr_data(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        assert app.pr_title == "feat: add thing"
        assert app.pr_body == "## What\nstuff"
        assert app.head_branch == "feat/x"

    def test_subtitle_shows_branch_direction(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        assert "feat/x" in app.sub_title
        assert "main" in app.sub_title
        assert "natanfiuza/gitpr" in app.sub_title

    def test_initial_state_is_clean(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        assert app.final_action is None
        assert app.final_pr_url is None
        assert app._commit_no_verify is False
        assert app.needs_new_token is False


class TestSaveLocal:
    def test_f2_writes_file_and_sets_saved_state(self, tmp_path):
        out = tmp_path / "PR_DESC.md"

        async def run():
            with patch(
                "src.ui.pr_publish_app.get_current_branch", return_value="feat/x"
            ):
                app = _make_app(out)
                async with app.run_test(size=(100, 30)) as pilot:
                    await pilot.pause()
                    app.query_one("#pr_title", Input).value = "feat: edited title"
                    app.query_one("#pr_body", TextArea).text = "edited body"
                    await pilot.pause()
                    app.action_save_local()
                    await pilot.pause()

            assert app.final_action == "saved"
            content = out.read_text(encoding="utf-8")
            assert "feat: edited title" in content
            assert "edited body" in content

        _run(run)

    def test_save_uses_current_widget_values_not_initial(self, tmp_path):
        """Edits made in the TUI must reach the file, not the original pr_data."""
        out = tmp_path / "PR_DESC.md"

        async def run():
            with patch(
                "src.ui.pr_publish_app.get_current_branch", return_value="feat/x"
            ):
                app = _make_app(out)
                async with app.run_test(size=(100, 30)) as pilot:
                    await pilot.pause()
                    app.query_one("#pr_title", Input).value = "CHANGED"
                    await pilot.pause()
                    app.action_save_local()
                    await pilot.pause()

            assert "CHANGED" in out.read_text(encoding="utf-8")
            assert "feat: add thing" not in out.read_text(encoding="utf-8")

        _run(run)

    def test_write_failure_sets_error_state(self, tmp_path):
        async def run():
            with patch(
                "src.ui.pr_publish_app.get_current_branch", return_value="feat/x"
            ):
                app = _make_app(tmp_path / "out.md")
                async with app.run_test(size=(100, 30)) as pilot:
                    await pilot.pause()
                    with patch(
                        "builtins.open", side_effect=PermissionError("read-only fs")
                    ):
                        app.action_save_local()
                    await pilot.pause()

            assert app.final_action == "error"
            assert "read-only fs" in app.final_message

        _run(run)


class TestPublishStateTransitions:
    """The callbacks that route the F3 flow, exercised without Git or AI."""

    def test_publish_with_no_changes_goes_straight_to_publish(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        with patch(
            "src.ui.pr_publish_app.has_uncommitted_changes", return_value=False
        ), patch.object(app, "_start_commit_and_publish") as direct, patch.object(
            app, "push_screen"
        ) as push:
            app.action_publish_pr()

        direct.assert_called_once()
        push.assert_not_called()

    def test_publish_with_changes_asks_for_confirmation(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        with patch(
            "src.ui.pr_publish_app.has_uncommitted_changes", return_value=True
        ), patch.object(app, "_start_commit_and_publish") as direct, patch.object(
            app, "push_screen"
        ) as push:
            app.action_publish_pr()

        direct.assert_not_called()
        push.assert_called_once()
        assert isinstance(push.call_args[0][0], CommitConfirmScreen)

    def test_confirm_yes_starts_commit_flow(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        with patch.object(app, "_start_progress_and_commit") as commit, patch.object(
            app, "_start_commit_and_publish"
        ) as publish:
            app._on_commit_confirm("yes")

        commit.assert_called_once()
        publish.assert_not_called()

    def test_confirm_no_skips_commit_and_publishes(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        with patch.object(app, "_start_progress_and_commit") as commit, patch.object(
            app, "_start_commit_and_publish"
        ) as publish:
            app._on_commit_confirm("no")

        commit.assert_not_called()
        publish.assert_called_once()

    def test_dismissing_confirm_does_nothing(self, tmp_path):
        """Escaping the modal must not commit or publish."""
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        with patch.object(app, "_start_progress_and_commit") as commit, patch.object(
            app, "_start_commit_and_publish"
        ) as publish:
            app._on_commit_confirm(None)

        commit.assert_not_called()
        publish.assert_not_called()

    def test_linter_no_verify_resumes_with_linter_skipped(self, tmp_path):
        """Resuming must set skip_linter=True or the modal would loop forever."""
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        with patch.object(app, "_start_progress_and_commit") as resume:
            app._on_linter_result("no_verify")

        assert app._commit_no_verify is True
        resume.assert_called_once_with(skip_linter=True)

    def test_linter_abort_does_nothing(self, tmp_path):
        """Abort must leave no side effect — no commit, no --no-verify flag."""
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        with patch.object(app, "_start_progress_and_commit") as resume:
            app._on_linter_result("abort")

        assert app._commit_no_verify is False
        resume.assert_not_called()

    def test_commit_message_confirm_uses_edited_text(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")

        screen = CommitMessageScreen(commit_message="feat: edited by user")
        screen._commit_message = "feat: edited by user"
        app._commit_msg_screen = screen

        with patch.object(app, "_start_commit_and_publish") as publish:
            app._on_commit_message_result("confirm")

        assert app._pending_commit_msg == "feat: edited by user"
        publish.assert_called_once()

    def test_commit_message_cancel_does_not_publish(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _make_app(tmp_path / "out.md")
        app._commit_msg_screen = CommitMessageScreen(commit_message="x")

        with patch.object(app, "_start_commit_and_publish") as publish:
            app._on_commit_message_result("cancel")

        publish.assert_not_called()
