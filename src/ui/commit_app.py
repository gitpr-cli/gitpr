import os
import sys
import threading
from textual.app import App, ComposeResult
from textual.widgets import Button, Static

from src.config import get_ai_provider
from src.core import (
    append_coauthor_trailer,
    execute_git_commit,
    generate_pr_content,
    get_git_diff,
    get_git_staged_diff,
    get_unstaged_files,
    stage_files,
)
from src.i18n import __
from src.ui.pr_publish_app import (
    CommitMessageScreen,
    CommitProgressScreen,
    StageFilesScreen,
    _with_suppressed_stdout,
)


class CommitApp(App):
    """Interactive Pair-Programming & Commit TUI for gitpr -c / --commit."""

    ENABLE_COMMAND_PALETTE = False

    def __init__(self, provider=None, skip_unstaged=False, **kwargs):
        super().__init__(**kwargs)
        self.provider = provider
        self.skip_unstaged = skip_unstaged
        self.result = None
        self._pending_commit_msg = ""
        self._commit_success = False
        self._commit_output = ""
        self._progress_screen = None
        self._commit_msg_screen = None
        self._stage_screen = None

    def compose(self) -> ComposeResult:
        yield Static("")  # Minimal base container for modal orchestration

    def on_mount(self) -> None:
        """Start the interactive flow."""
        skip_check = self.skip_unstaged or (
            os.getenv("GITPR_SKIP_UNSTAGED_CHECK", "false").lower()
            in ("true", "1", "yes", "y")
        )
        if not skip_check:
            unstaged = get_unstaged_files()
            if unstaged:
                auto_stage = os.getenv("GITPR_AUTO_STAGE", "false").lower() in (
                    "true",
                    "1",
                    "yes",
                    "y",
                )
                if auto_stage:
                    stage_files([f for f, _ in unstaged])
                    self._check_diff_and_generate()
                    return

                screen = StageFilesScreen(
                    files=unstaged,
                    selected={f: True for f, _ in unstaged},
                )
                self._stage_screen = screen
                self.push_screen(screen, callback=self._on_stage_done)
                return

        self._check_diff_and_generate()

    def _on_stage_done(self, result: str) -> None:
        """Handle outcome of StageFilesScreen."""
        if result == "cancel":
            self.result = "cancelled"
            self.exit()
            return

        if result == "stage":
            selected = getattr(self._stage_screen, "staged", [])
            if selected:
                stage_files(selected)

        self._check_diff_and_generate()

    def _check_diff_and_generate(self) -> None:
        """Check for staged (or working tree) diff and generate the commit message."""
        staged_diff = _with_suppressed_stdout(get_git_staged_diff, quiet=True)
        if not staged_diff or not staged_diff.strip():
            # Fallback to general working tree diff if nothing was staged
            working_diff = _with_suppressed_stdout(get_git_diff, quiet=True)
            if not working_diff or not working_diff.strip():
                self.result = "no_changes"
                self.exit()
                return
            diff_text = working_diff
        else:
            diff_text = staged_diff

        def do_generate():
            self._generate_commit_msg(diff_text)

        self._progress_screen = CommitProgressScreen(
            work_callback=do_generate,
            initial_status=__("📝 Generating commit message..."),
            title=__("📝 Generating commit message..."),
        )
        self.push_screen(self._progress_screen)

    def _generate_commit_msg(self, diff_text: str) -> None:
        """Run AI call in background thread while progress screen animates."""
        def _ai_work():
            old = sys.stdout
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
            try:
                provider = self.provider or get_ai_provider()
                data = generate_pr_content("commit", "commit", diff_text, provider)
            except Exception:
                data = None
            finally:
                sys.stdout.close()
                sys.stdout = old

            commit_msg = (
                data.get("commit_message", __("Code update"))
                if data
                else __("Code update")
            )
            self.call_from_thread(self._on_commit_msg_ready, commit_msg)

        threading.Thread(target=_ai_work, daemon=True).start()

    def _on_commit_msg_ready(self, commit_msg: str) -> None:
        """Receive generated commit message on main thread and prompt for review."""
        self._pending_commit_msg = commit_msg
        if self._progress_screen:
            self._progress_screen.mark_finished(show_close=False)
        self.pop_screen()

        screen = CommitMessageScreen(commit_message=commit_msg)
        self._commit_msg_screen = screen
        self.push_screen(screen, callback=self._on_commit_message_result)

    def _on_commit_message_result(self, result: str) -> None:
        """Handle outcome of CommitMessageScreen."""
        if result == "confirm":
            if self._commit_msg_screen and hasattr(
                self._commit_msg_screen, "_commit_message"
            ):
                self._pending_commit_msg = self._commit_msg_screen._commit_message
            self._start_commit_execution()
        else:
            self.result = "cancelled"
            self.exit()

    def _start_commit_execution(self) -> None:
        """Show animated progress modal and execute git commit."""
        def do_commit():
            self._run_commit_worker()

        self._progress_screen = CommitProgressScreen(
            work_callback=do_commit,
            initial_status=__("📦 Executing commit..."),
            title=__("📦 Executing commit..."),
        )
        self.push_screen(
            self._progress_screen, callback=self._on_commit_progress_dismissed
        )

    def _run_commit_worker(self) -> None:
        """Execute git commit in background thread with status updates."""
        def _commit_work():
            log = self._progress_screen
            msg = append_coauthor_trailer(self._pending_commit_msg)
            try:
                success, output = execute_git_commit(msg)
            except Exception as e:
                success, output = False, str(e)

            self._commit_success = success
            self._commit_output = output
            self.result = "committed" if success else "failed"

            if success:
                self.call_from_thread(
                    log.add_log, __("✅ Commit successfully created!")
                )
                if output and output.strip():
                    first_line = output.strip().split("\n")[0]
                    self.call_from_thread(log.add_log, f"   {first_line}")
            else:
                out_summary = output.strip()[:100] if output else "unknown error"
                self.call_from_thread(
                    log.add_log,
                    __("❌ Failed to commit: {error}", error=out_summary),
                )

            self.call_from_thread(log.mark_finished, True)

        threading.Thread(target=_commit_work, daemon=True).start()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Catch close button on progress modal."""
        if event.button.id == "btn_close":
            self.result = "committed" if self._commit_success else "failed"
            self.exit()

    def _on_commit_progress_dismissed(self, result: str) -> None:
        """Called when user closes the commit progress screen."""
        self.result = "committed" if self._commit_success else "failed"
        self.exit()
