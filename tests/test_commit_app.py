import asyncio
from unittest.mock import MagicMock, patch
import pytest

from src.ui.commit_app import CommitApp
from src.ui.pr_publish_app import (
    CommitMessageScreen,
    CommitProgressScreen,
    StageFilesScreen,
)


def _run(coro_factory):
    asyncio.run(coro_factory())


async def _wait_until(pilot, predicate, timeout=5.0):
    """Poll the app between pauses until *predicate* becomes true."""
    for _ in range(int(timeout / 0.05)):
        try:
            if predicate():
                return
        except Exception:
            pass
        await pilot.pause(0.05)
    raise AssertionError(f"timed out waiting for condition. Current screen: {pilot.app.screen}")


class TestCommitAppUnit:
    """Unit tests for state transitions and callbacks in CommitApp."""

    def test_on_mount_pushes_stage_screen_when_unstaged_files_exist(self):
        app = CommitApp(provider="gemini")
        unstaged = [("src/file1.py", "??"), ("src/file2.py", "M")]

        with patch("src.ui.commit_app.get_unstaged_files", return_value=unstaged), \
             patch.object(app, "push_screen") as mock_push:
            app.on_mount()

            mock_push.assert_called_once()
            screen = mock_push.call_args[0][0]
            assert isinstance(screen, StageFilesScreen)
            assert screen._files == unstaged

    def test_on_mount_auto_stages_when_env_flag_set(self, monkeypatch):
        monkeypatch.setenv("GITPR_AUTO_STAGE", "true")
        app = CommitApp(provider="gemini")
        unstaged = [("src/file1.py", "??")]

        with patch("src.ui.commit_app.get_unstaged_files", return_value=unstaged), \
             patch("src.ui.commit_app.stage_files") as mock_stage, \
             patch.object(app, "_check_diff_and_generate") as mock_gen:
            app.on_mount()

            mock_stage.assert_called_once_with(["src/file1.py"])
            mock_gen.assert_called_once()

    def test_on_mount_skips_stage_screen_when_skip_unstaged_true(self):
        app = CommitApp(provider="gemini", skip_unstaged=True)

        with patch("src.ui.commit_app.get_unstaged_files") as mock_get_unstaged, \
             patch.object(app, "_check_diff_and_generate") as mock_gen:
            app.on_mount()

            mock_get_unstaged.assert_not_called()
            mock_gen.assert_called_once()

    def test_on_stage_done_cancel_aborts(self):
        app = CommitApp(provider="gemini")
        with patch.object(app, "exit") as mock_exit:
            app._on_stage_done("cancel")
            assert app.result == "cancelled"
            mock_exit.assert_called_once()

    def test_on_stage_done_stage_stages_files_and_generates(self):
        app = CommitApp(provider="gemini")
        app._stage_screen = MagicMock(staged=["src/file1.py"])

        with patch("src.ui.commit_app.stage_files") as mock_stage, \
             patch.object(app, "_check_diff_and_generate") as mock_gen:
            app._on_stage_done("stage")

            mock_stage.assert_called_once_with(["src/file1.py"])
            mock_gen.assert_called_once()

    def test_check_diff_and_generate_no_changes_exits(self):
        app = CommitApp(provider="gemini")
        with patch("src.ui.commit_app.get_git_staged_diff", return_value=""), \
             patch("src.ui.commit_app.get_git_diff", return_value=""), \
             patch.object(app, "exit") as mock_exit:
            app._check_diff_and_generate()
            assert app.result == "no_changes"
            mock_exit.assert_called_once()

    def test_check_diff_and_generate_pushes_progress_screen(self):
        app = CommitApp(provider="gemini")
        with patch("src.ui.commit_app.get_git_staged_diff", return_value="diff --git a/foo b/foo"), \
             patch.object(app, "push_screen") as mock_push:
            app._check_diff_and_generate()

            mock_push.assert_called_once()
            screen = mock_push.call_args[0][0]
            assert isinstance(screen, CommitProgressScreen)

    def test_on_commit_msg_ready_pushes_message_screen(self):
        app = CommitApp(provider="gemini")
        progress = MagicMock()
        app._progress_screen = progress

        with patch.object(app, "pop_screen") as mock_pop, \
             patch.object(app, "push_screen") as mock_push:
            app._on_commit_msg_ready("feat: awesome change")

            progress.mark_finished.assert_called_once_with(show_close=False)
            mock_pop.assert_called_once()
            mock_push.assert_called_once()
            msg_screen = mock_push.call_args[0][0]
            assert isinstance(msg_screen, CommitMessageScreen)
            assert msg_screen._commit_message == "feat: awesome change"

    def test_on_commit_message_result_cancel_aborts(self):
        app = CommitApp(provider="gemini")
        with patch.object(app, "exit") as mock_exit:
            app._on_commit_message_result("cancel")
            assert app.result == "cancelled"
            mock_exit.assert_called_once()

    def test_on_commit_message_result_confirm_starts_commit(self):
        app = CommitApp(provider="gemini")
        app._commit_msg_screen = MagicMock(_commit_message="feat: custom message")

        with patch.object(app, "_start_commit_execution") as mock_start:
            app._on_commit_message_result("confirm")
            assert app._pending_commit_msg == "feat: custom message"
            mock_start.assert_called_once()

    def test_run_commit_worker_executes_commit_and_marks_finished(self):
        app = CommitApp(provider="gemini")
        app._pending_commit_msg = "feat: add feature"
        progress = MagicMock()
        app._progress_screen = progress

        with patch("src.ui.commit_app.execute_git_commit", return_value=(True, "[main abc1234] feat: add feature")) as mock_exec, \
             patch("src.ui.commit_app.append_coauthor_trailer", side_effect=lambda m: m + "\n\nCo-author: Test"), \
             patch.object(app, "call_from_thread") as mock_call_from_thread, \
             patch("threading.Thread") as mock_thread:
            # Run the inner worker function synchronously
            app._run_commit_worker()
            target_fn = mock_thread.call_args[1]["target"]
            target_fn()

            mock_exec.assert_called_once_with("feat: add feature\n\nCo-author: Test")
            assert app._commit_success is True
            called_fns = [c[0][0] for c in mock_call_from_thread.call_args_list]
            assert progress.add_log in called_fns
            assert progress.mark_finished in called_fns
            assert app._schedule_auto_exit in called_fns

    def test_on_commit_progress_dismissed_sets_result(self):
        app = CommitApp(provider="gemini")
        app._commit_success = True
        with patch.object(app, "exit") as mock_exit:
            app._on_commit_progress_dismissed("done")
            assert app.result == "committed"
            mock_exit.assert_called_once()

    def test_schedule_auto_exit_sets_timer(self):
        app = CommitApp(provider="gemini")
        with patch.object(app, "set_timer") as mock_timer:
            app._schedule_auto_exit()
            mock_timer.assert_called_once_with(0.6, app.exit)


class TestCommitAppHeadlessFlow:
    """Headless integration tests using Textual run_test()."""

    def test_headless_full_flow(self):
        async def _test():
            unstaged = [("src/foo.py", "M")]
            with patch("src.ui.commit_app.get_unstaged_files", return_value=unstaged), \
                 patch("src.ui.commit_app.stage_files", return_value=(True, "")) as mock_stage, \
                 patch("src.ui.commit_app.get_git_staged_diff", return_value="diff --git a/foo.py b/foo.py"), \
                 patch("src.ui.commit_app.generate_pr_content", return_value={"commit_message": "feat: update foo"}), \
                 patch("src.ui.commit_app.execute_git_commit", return_value=(True, "[main 12345] feat: update foo")):

                app = CommitApp(provider="gemini")
                async with app.run_test(size=(100, 30)) as pilot:
                    await pilot.pause(0.1)
                    # StageFilesScreen is active
                    assert isinstance(app.screen, StageFilesScreen)
                    # Click btn_stage
                    await pilot.click("#btn_stage")
                    
                    # Wait for generation to complete and CommitMessageScreen's btn_confirm to appear
                    await _wait_until(pilot, lambda: bool(app.screen.query("#btn_confirm")))
                    assert isinstance(app.screen, CommitMessageScreen)

                    # Confirm commit
                    await pilot.click("#btn_confirm")

                    # Wait for commit execution to complete and auto-exit to set result
                    await _wait_until(pilot, lambda: app.result == "committed")

                assert app.result == "committed"
                mock_stage.assert_called_once_with(["src/foo.py"])

        _run(_test)
