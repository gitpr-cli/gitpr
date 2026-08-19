import re
import io
import os
import sys
import subprocess
from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Input,
    TextArea,
    Label,
    Button,
    Static,
    RichLog,
    SelectionList,
    ProgressBar,
)
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.binding import Binding

from src.core import get_current_branch, has_uncommitted_changes, execute_git_commit
from src.github_api import create_pull_request
from src.ui.pr_publish_help import PrPublishHelpScreen
from src.i18n import __


# ═══════════════════════════════════════════════════════════════════
# File status display helper
# ═══════════════════════════════════════════════════════════════════

_STATUS_LABELS = {
    "new": ("🆕", __("New")),
    "mod": ("✏️ ", __("Modified")),
    "del": ("🗑️ ", __("Deleted")),
}


def _fmt_status(status):
    """Returns (emoji, label) for a file status code.

    Maps internal short codes to user-facing display labels:
      'new' → 🆕 New (untracked)
      'mod' → ✏️ Modified (unstaged)
      'del' → 🗑️ Deleted (unstaged)
    """
    return _STATUS_LABELS.get(status, ("❓", status))


# Capture the real stdout before Textual replaces it.
_REAL_STDOUT = sys.stdout


def _with_real_stdout(func, *args, **kwargs):
    """Call func with the real sys.stdout temporarily restored."""
    _clear_click_cache()
    old_stdout = sys.stdout
    sys.stdout = _REAL_STDOUT
    try:
        return func(*args, **kwargs)
    finally:
        sys.stdout = old_stdout
        _clear_click_cache()


def _call_with_log(log_widget, func, *args, **kwargs):
    """Call func, capturing click output to log_widget instead of terminal.

    Click caches its stdout wrapper via @lru_cache on _default_text_stdout,
    so merely replacing sys.stdout is not enough.  We clear the cache before
    and after the call to force click to re-read sys.stdout each time.
    """
    import click._compat

    _clear_click_cache()

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    try:
        result = func(*args, **kwargs)
        captured = buffer.getvalue()
        if captured.strip():
            for line in captured.strip().split("\n"):
                stripped = line.strip()
                if stripped:
                    log_widget.add_log(stripped)
        return result
    finally:
        sys.stdout = old_stdout
        _clear_click_cache()


def _with_suppressed_stdout(func, *args, **kwargs):
    """Call func with stdout redirected to /dev/null.

    Used inside the TUI so click.secho/click.echo calls from core.py
    functions are silently discarded instead of crashing (Textual's
    _PrintCapture has no valid fd) or leaking to the real terminal.
    """
    _clear_click_cache()
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
    try:
        return func(*args, **kwargs)
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout
        _clear_click_cache()


def _clear_click_cache():
    """Clear click's cached stdout/stderr wrappers so they pick up sys.stdout changes."""
    import click._compat

    for fn in (click._compat._default_text_stdout, click._compat._default_text_stderr):
        try:
            fn.cache_clear()
        except Exception:
            pass


def _extract_title_from_body(body_text: str) -> str:
    """Extracts the first markdown heading from the PR body."""
    if not body_text:
        return ""
    match = re.search(r"^#+\s+(.+)$", body_text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _build_bar(pos, direction):
    """Build the animated bar string for the given position and direction."""
    trail_off = -direction  # trail behind the block
    parts = ["▐"]
    for i in range(1, 31):  # BAR_WIDTH = 30
        if i == pos:
            parts.append("█")
        elif i == pos + trail_off:
            parts.append("▓")
        elif i == pos + trail_off * 2:
            parts.append("▒")
        elif i == pos + trail_off * 3:
            parts.append("░")
        else:
            parts.append(" ")
    parts.append("▌")
    return "".join(parts)


def _init_publish_log():
    """Initialize the PR publish log file. Returns the file path or None if disabled."""
    if os.getenv("PR_PUBLISH_LOG", "true").lower() not in ("true", "1", "yes", "y"):
        return None
    from src.chat_memory import gerar_uuid_base_15

    log_dir = os.path.join(os.path.expanduser("~"), ".gitpr", "logs", "pr_desc")
    os.makedirs(log_dir, exist_ok=True)
    session_id = gerar_uuid_base_15()
    log_path = os.path.join(log_dir, f"pr_desc_{session_id}.log")
    return log_path


def _log_event(log_path, message):
    """Write a timestamped single-line log entry."""
    if not log_path:
        return
    from datetime import datetime

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Collapse newlines so every entry is a single line
    flat = message.replace("\n", " | ").replace("\r", "")
    try:
        with open(log_path, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[{ts}] | {flat}\n")
    except Exception:
        pass


class StageFilesScreen(ModalScreen):
    """Modal for selecting unstaged files. Dismisses with result."""

    CSS = """
    StageFilesScreen { align: center middle; }
    #stage_root {
        width: 75%; height: auto; max-height: 85%;
        padding: 1 2;
        background: $surface; border: thick $background 80%;
    }
    .stage_title { text-align: center; text-style: bold; margin-bottom: 1; }
    .stage_info { text-align: center; color: $text-muted; margin-bottom: 1; }
    #file_list { height: 6; overflow-y: auto; margin-bottom: 1; }
    #stage_top_buttons { align-horizontal: center; margin-bottom: 1; }
    #stage_bottom_buttons { align-horizontal: center; margin-top: 1; }
    Button { margin: 0 1; min-width: 20; }
    """

    def __init__(self, files, selected, **kwargs):
        super().__init__(**kwargs)
        self._files = files
        self._selected = selected
        self.result = None
        self.staged = []

    def compose(self) -> ComposeResult:
        with Vertical(id="stage_root"):
            yield Static(__("📂 Unstaged Files"), classes="stage_title")
            yield Static(
                __(
                    "{count} file(s) not staged. Select which ones to add:",
                    count=len(self._files),
                ),
                classes="stage_info",
            )
            options = [
                (
                    f"{_fmt_status(status)[0]} {_fmt_status(status)[1]}: {fname}",
                    fname,
                    self._selected.get(fname, True),
                )
                for fname, status in self._files
            ]
            yield SelectionList(*options, id="file_list")
            with Horizontal(id="stage_top_buttons"):
                yield Button(__("Select All"), variant="default", id="btn_select_all")
                yield Button(
                    __("Deselect All"), variant="default", id="btn_deselect_all"
                )
            with Horizontal(id="stage_bottom_buttons"):
                yield Button(__("Stage Selected"), variant="primary", id="btn_stage")
                yield Button(__("Skip Staging"), variant="default", id="btn_skip")
                yield Button(__("Cancel"), variant="error", id="btn_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_select_all":
            self.query_one("#file_list", SelectionList).select_all()
        elif bid == "btn_deselect_all":
            self.query_one("#file_list", SelectionList).deselect_all()
        elif bid == "btn_stage":
            # Read the real selection from the widget — individual row
            # toggles are only tracked by the SelectionList itself.
            self.staged = list(self.query_one("#file_list", SelectionList).selected)
            self.result = "stage"
            self.dismiss("stage")
        elif bid == "btn_skip":
            self.result = "skip"
            self.dismiss("skip")
        elif bid == "btn_cancel":
            self.result = "cancel"
            self.dismiss("cancel")


class StageFilesApp(App):
    """Minimal TUI: empty base screen + StageFilesScreen modal."""

    ENABLE_COMMAND_PALETTE = False

    def __init__(self, unstaged_files, **kwargs):
        super().__init__(**kwargs)
        self._unstaged = unstaged_files
        self.result = None
        self.selected_files = []

    def compose(self) -> ComposeResult:
        yield Static("")  # empty base screen — required for ModalScreen

    def on_mount(self) -> None:
        screen = StageFilesScreen(
            files=self._unstaged,
            selected={f: True for f, _ in self._unstaged},
        )
        self._stage_screen = screen
        self.push_screen(screen, callback=self._on_stage_done)

    def _on_stage_done(self, result):
        self.result = result
        if result == "stage":
            self.selected_files = list(self._stage_screen.staged)
        self.exit()


# ═══════════════════════════════════════════════════════════════════
# Modal Screens
# ═══════════════════════════════════════════════════════════════════


class CommitConfirmScreen(ModalScreen):
    """Modal with Yes/No/Cancel buttons for commit confirmation."""

    CSS = """
    CommitConfirmScreen { align: center middle; }
    #confirm_dialog {
        width: 70%; height: auto; max-height: 50%;
        padding: 2 3;
        background: $surface; border: thick $background 80%;
    }
    .confirm_title {
        text-align: center; text-style: bold; margin-bottom: 1;
    }
    .confirm_message {
        margin-bottom: 1; text-align: center; overflow-y: auto;
        max-height: 20;
    }
    #confirm_buttons {
        align-horizontal: center; margin-top: 1;
    }
    Button {
        margin: 0 1;
        min-width: 16;
    }
    """

    def __init__(self, title, message, btn_yes=None, btn_no=None, **kwargs):
        super().__init__(**kwargs)
        self._title_text = title
        self._message_text = message
        self._btn_yes = btn_yes or __("Yes, Commit")
        self._btn_no = btn_no or __("No, Skip")
        self.result = None

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm_dialog"):
            yield Static(self._title_text, classes="confirm_title")
            yield Static(self._message_text, classes="confirm_message")
            with Horizontal(id="confirm_buttons"):
                yield Button(self._btn_yes, variant="primary", id="btn_yes")
                yield Button(self._btn_no, variant="default", id="btn_no")
                yield Button(__("Cancel"), variant="error", id="btn_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_yes":
            self.result = "yes"
        elif event.button.id == "btn_no":
            self.result = "no"
        elif event.button.id == "btn_cancel":
            self.result = "cancel"
        self.dismiss(self.result)


class CommitProgressScreen(ModalScreen):
    """Modal with animated bouncing-block bar with gradient trail."""

    CSS = """
    CommitProgressScreen { align: center middle; }
    #progress_dialog {
        width: 60%; height: 35%; padding: 1 3;
        background: $surface; border: thick $background 80%;
    }
    .progress_title {
        text-align: center; text-style: bold; margin-bottom: 1;
        color: $accent;
    }
    #progress_anim_line {
        text-align: center; width: 100%; min-height: 1;
        color: $accent; background: $background-darken-2;
    }
    #progress_status {
        text-align: center; color: $text-muted; margin-top: 1;
        min-height: 1;
    }
    #progress_buttons {
        align-horizontal: center; margin-top: 1;
    }
    Button {
        margin: 0 1;
        min-width: 16;
    }
    """

    BAR_WIDTH = 30

    def __init__(self, work_callback=None, initial_status="", **kwargs):
        super().__init__(**kwargs)
        self._finished = False
        self.result = None
        self._work_callback = work_callback
        self._initial_status = initial_status
        self._anim_pos = 0
        self._anim_dir = 1
        self._anim_timer = None

    def compose(self) -> ComposeResult:
        with Vertical(id="progress_dialog"):
            yield Static(__("📦 Processing commit..."), classes="progress_title")
            yield Static(_build_bar(0, 1), id="progress_anim_line")
            yield Static(self._initial_status, id="progress_status")
            with Horizontal(id="progress_buttons"):
                yield Button(__("Close"), variant="primary", id="btn_close")

    def on_mount(self) -> None:
        """Start animation, hide close button, then trigger work."""
        btn = self.query_one("#btn_close", Button)
        btn.display = False
        self._anim_timer = self.set_interval(0.05, self._tick_animation)
        if self._work_callback:
            # Start after a short delay so the animation is visible first
            self.set_timer(0.3, self._work_callback)

    def _tick_animation(self) -> None:
        """Advance the bouncing-block animation."""
        if self._finished:
            return
        self._anim_pos += self._anim_dir
        if self._anim_pos >= self.BAR_WIDTH - 3:
            self._anim_pos = self.BAR_WIDTH - 4
            self._anim_dir = -1
        elif self._anim_pos <= 3:
            self._anim_pos = 4
            self._anim_dir = 1
        line = _build_bar(self._anim_pos, self._anim_dir)
        w = self.query_one("#progress_anim_line", Static)
        w.update(line)
        w.refresh()

    def add_log(self, message: str):
        """Update the status label below the animation."""
        self.query_one("#progress_status", Static).update(message)

    def mark_finished(self):
        """Stop animation, fill bar, show close button."""
        self._finished = True
        if self._anim_timer:
            self._anim_timer.stop()
        self.query_one("#progress_anim_line", Static).update(
            "▐" + "█" * self.BAR_WIDTH + "▌"
        )
        btn = self.query_one("#btn_close", Button)
        btn.display = True
        btn.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_close" and self._finished:
            self.result = "done"
            self.dismiss(self.result)


class CommitMessageScreen(ModalScreen):
    """Modal with editable commit message and Confirm/Regenerate/Cancel."""

    CSS = """
    CommitMessageScreen { align: center middle; }
    #msg_dialog {
        width: 80%; height: auto; min-height: 20; max-height: 60%;
        padding: 2 2;
        background: $surface; border: thick $background 80%;
        align-horizontal: center;
    }
    .msg_title { text-align: center; text-style: bold; margin-bottom: 1; }
    .msg_edit_label { margin-bottom: 0; text-style: bold; color: $accent; }
    #msg_input { margin: 1 0; }
    #msg_buttons {
        align-horizontal: center; margin-top: 1; padding-bottom: 1;
    }
    Button {
        margin: 0 1;
        min-width: 16;
    }
    """

    def __init__(self, commit_message, **kwargs):
        super().__init__(**kwargs)
        self._commit_message = commit_message
        self.result = None

    def compose(self) -> ComposeResult:
        with Vertical(id="msg_dialog"):
            yield Static(__("📝 Commit Message:"), classes="msg_title")
            yield Label(
                __("Edit the message below before confirming:"),
                classes="msg_edit_label",
            )
            yield Input(value=self._commit_message, id="msg_input")
            with Horizontal(id="msg_buttons"):
                yield Button(__("Confirm"), variant="primary", id="btn_confirm")
                yield Button(__("Cancel"), variant="error", id="btn_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_confirm":
            msg_input = self.query_one("#msg_input", Input)
            edited_msg = msg_input.value.strip()
            if not edited_msg:
                self.notify(__("⚠ Commit message cannot be empty."), severity="error")
                return
            self._commit_message = edited_msg
            self.result = "confirm"
        elif event.button.id == "btn_cancel":
            self.result = "cancel"
        if self.result:
            self.dismiss(self.result)


class LinterErrorScreen(ModalScreen):
    """Modal showing linter errors and asking about --no-verify."""

    CSS = """
    LinterErrorScreen { align: center middle; }
    #linter_dialog {
        width: 80%; height: auto; padding: 1 2;
        background: $surface; border: thick $background 80%;
        align-horizontal: center;
    }
    .linter_title { text-align: center; text-style: bold; margin-bottom: 1; color: $error; }
    .linter_errors {
        margin-bottom: 1; padding: 1; background: $boost;
        color: $error; max-height: 15; overflow-y: auto;
    }
    #linter_buttons {
        align-horizontal: center; height: auto;
    }
    Button {
        margin: 0 1;
        min-width: 22;
    }
    """

    def __init__(self, errors, **kwargs):
        super().__init__(**kwargs)
        self._errors = errors
        self.result = None

    def compose(self) -> ComposeResult:
        errors_text = "\n".join(f"  - {e}" for e in self._errors[:10])
        if len(self._errors) > 10:
            errors_text += f"\n  ... ({len(self._errors) - 10} more)"
        with Vertical(id="linter_dialog"):
            yield Static(
                __("🚨 Linter found {count} error(s):", count=len(self._errors)),
                classes="linter_title",
            )
            yield Static(errors_text, classes="linter_errors")
            with Horizontal(id="linter_buttons"):
                yield Button(
                    __("Commit with --no-verify"), variant="warning", id="btn_no_verify"
                )
                yield Button(__("Abort"), variant="error", id="btn_abort")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_no_verify":
            self.result = "no_verify"
        elif event.button.id == "btn_abort":
            self.result = "abort"
        self.dismiss(self.result)


class ErrorScreen(ModalScreen):
    """Modal for displaying errors with retry / cancel options."""

    CSS = """
    ErrorScreen { align: center middle; }
    #error_dialog {
        width: 75%; height: auto; max-height: 80%;
        padding: 2 3; overflow-y: auto;
        background: $surface; border: thick $background 80%;
    }
    .error_title { text-align: center; text-style: bold; margin-bottom: 1; color: $error; }
    .error_message {
        margin-bottom: 1; padding: 1; background: $boost;
        color: $text; max-height: 12; overflow-y: auto;
    }
    #error_buttons { align-horizontal: center; }
    Button { margin: 0 1; min-width: 18; }
    """

    def __init__(self, title, message, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._message = message[:500] if message else ""
        self.result = None

    def compose(self) -> ComposeResult:
        with Vertical(id="error_dialog"):
            yield Static(self._title, classes="error_title")
            yield Static(self._message, classes="error_message")
            with Horizontal(id="error_buttons"):
                yield Button(__("Try Again"), variant="primary", id="btn_retry")
                yield Button(__("Cancel"), variant="error", id="btn_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_retry":
            self.result = "retry"
        elif event.button.id == "btn_cancel":
            self.result = "cancel"
        self.dismiss(self.result)


# ═══════════════════════════════════════════════════════════════════
# Main App
# ═══════════════════════════════════════════════════════════════════


class PrPublishApp(App):
    """Terminal Interface for reviewing, editing, and publishing Pull Requests."""

    TITLE = __("GitPR - PR Publisher")
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Input { margin-bottom: 1; }
    TextArea { height: 1fr; }
    Label { margin-top: 1; text-style: bold; color: $accent; }
    """

    BINDINGS = [
        Binding("f1", "show_help", __("Help")),
        Binding("f2", "save_local", __("Save Local")),
        Binding("f3", "publish_pr", __("Publish PR")),
        Binding("escape", "quit", __("Exit")),
    ]

    def __init__(
        self, pr_data, repo_info, github_token, base_branch, output_filename, **kwargs
    ):
        super().__init__(**kwargs)
        self.pr_data = pr_data
        self.repo_info = repo_info
        self.github_token = github_token
        self.base_branch = base_branch
        self.output_filename = output_filename
        self.head_branch = get_current_branch()
        self.final_action = None
        self.final_message = ""
        self.final_pr_url = None
        self.needs_new_token = False
        self._commit_no_verify = False
        self._pending_commit_msg = ""
        self._progress_screen = None
        self._log_path = _init_publish_log()

        repo_display = self.repo_info if self.repo_info else __("Local Repository")
        self.sub_title = f"{repo_display} | {self.head_branch} → {self.base_branch}"

        self.pr_title = pr_data.get("commit_message", "")
        self.pr_body = pr_data.get("pr_description", "")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Label(__("📌 PR Title"))
            yield Input(value=self.pr_title, id="pr_title")
            yield Label(__("📝 PR Body"))
            yield TextArea(text=self.pr_body, id="pr_body")
        yield Footer()

    def action_show_help(self):
        self.push_screen(PrPublishHelpScreen())

    def action_save_local(self):
        title_input = self.query_one("#pr_title", Input)
        body_input = self.query_one("#pr_body", TextArea)
        md_content = (
            __("# 🚀 Pull Request Suggestion\n\n**Recommended Commit Message:**\n")
            + "```text\n"
            + f"{title_input.value}\n"
            + "```\n\n---\n\n"
            + body_input.text
        )
        try:
            with open(self.output_filename, "w", encoding="utf-8") as f:
                f.write(md_content)
            self.final_message = __(
                "✅ PR saved locally: {output_filename}",
                output_filename=self.output_filename,
            )
            self.final_action = "saved"
        except Exception as e:
            self.final_message = __("❌ Error saving file: {error}", error=str(e))
            self.final_action = "error"
        self.exit()

    def _log(self, message):
        """Write a debug log entry for this session."""
        _log_event(self._log_path, message)

    # ── Auto-Commit Flow (F3) ──

    def action_publish_pr(self):
        """F3: Auto-commit (if needed) then publish PR."""
        self._log("F3 pressed — action_publish_pr")
        if has_uncommitted_changes():
            self._log("Uncommitted changes detected, showing CommitConfirmScreen")
            self.push_screen(
                CommitConfirmScreen(
                    title=__("Uncommitted Changes"),
                    message=__(
                        "Uncommitted changes detected. Auto-commit before publishing?"
                    ),
                ),
                callback=self._on_commit_confirm,
            )
        else:
            self._start_commit_and_publish()

    def _on_commit_confirm(self, result):
        if result == "yes":
            self._start_progress_and_commit()
        elif result == "no":
            self._start_commit_and_publish()

    # ── Progress + commit flow ──

    def _start_progress_and_commit(self, skip_linter=False):
        """Push the progress screen; work starts via on_mount when RichLog is ready.

        skip_linter=True resumes the flow after the user chose --no-verify in
        the linter error modal, so the linter is not run again.
        """

        def do_work():
            self._run_linter_and_commit(skip_linter=skip_linter)

        self._progress_screen = CommitProgressScreen(
            work_callback=do_work,
            initial_status=(
                __("📝 Generating commit message...")
                if skip_linter
                else __("🔍 Running linter...")
            ),
        )
        self.push_screen(self._progress_screen)

    def _run_linter_and_commit(self, skip_linter=False):
        """Run linter then generate commit message, logging to progress screen."""
        log = self._progress_screen
        skip_lint = (
            skip_linter
            or self._commit_no_verify
            or os.getenv("GITPR_SKIP_LINT", "false").lower()
            in ("true", "1", "yes", "y")
        )

        if not skip_lint:
            log.add_log(__("🔍 Running linter..."))
            from src.linter_engine import parse_diff_and_lint
            from src.core import get_git_diff

            diff_text = _with_suppressed_stdout(get_git_diff, quiet=True)
            linter_results = parse_diff_and_lint(diff_text)
            has_errors = len(linter_results["errors"]) > 0
            has_warnings = len(linter_results["warnings"]) > 0

            if has_warnings:
                for w in linter_results["warnings"]:
                    log.add_log(f"⚠️ {w}")

            if has_errors:
                for e in linter_results["errors"]:
                    log.add_log(f"🚨 {e}")
                log.add_log("")
                self._progress_screen = log
                # Defer to the app's message pump: this runs inside the
                # progress screen's timer, and pushing the modal inline would
                # bind its dismiss callback to the popped screen's dead queue
                # (Textual uses the active message pump as callback requester),
                # so the button result would never be delivered. call_next
                # posts to the app itself, unlike call_after_refresh, which
                # is forwarded to the current screen.
                self.call_next(
                    self._show_linter_error_modal, linter_results["errors"]
                )
                return

            if has_warnings:
                log.add_log(__("✅ Linter passed with warnings."))
            else:
                log.add_log(__("✅ Linter passed — no violations."))

        # Generate commit message
        log.add_log(__("📝 Generating commit message..."))
        self._generate_commit_msg()

    def _show_linter_error_modal(self, errors):
        """Pop the progress screen and show the linter error modal."""
        self.pop_screen()
        self.push_screen(
            LinterErrorScreen(errors=errors),
            callback=self._on_linter_result,
        )

    def _on_linter_result(self, result):
        if result == "no_verify":
            self._commit_no_verify = True
            # Resume the flow with the linter skipped; otherwise it would run
            # again, re-report the same errors, and loop back into this modal.
            self._start_progress_and_commit(skip_linter=True)
        # abort: do nothing

    def _generate_commit_msg(self):
        """Generate commit message via AI (heavy part in background thread)."""
        from src.core import get_git_diff, generate_pr_content
        from src.config import get_ai_provider

        provider = get_ai_provider()
        log = self._progress_screen
        diff_text = _with_suppressed_stdout(get_git_diff, quiet=True)
        if not diff_text or not diff_text.strip():
            log.add_log(__("⚠️ No diff to generate commit message."))
            log.mark_finished()
            return

        log.add_log(__("📝 Generating commit message..."))

        # Run AI call in background thread so animation keeps playing
        def _ai_work():
            # Suppress stdout for click safety in worker thread
            old = sys.stdout
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
            try:
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
            # Bounce back to main thread for UI updates
            self.call_from_thread(self._on_commit_msg_ready, commit_msg)

        import threading

        threading.Thread(target=_ai_work, daemon=True).start()

    def _on_commit_msg_ready(self, commit_msg):
        """Called on main thread after AI generates the commit message."""
        self._pending_commit_msg = commit_msg
        self._progress_screen.add_log(__("✅ Commit message generated."))
        self._progress_screen.mark_finished()

        self.pop_screen()
        screen = CommitMessageScreen(commit_message=commit_msg)
        self._commit_msg_screen = screen
        self.push_screen(screen, callback=self._on_commit_message_result)

    def _on_commit_message_result(self, result):
        self._log(f"CommitMessageScreen result: {result}")
        if result == "confirm":
            screen = self._commit_msg_screen
            if screen and hasattr(screen, "_commit_message"):
                self._pending_commit_msg = screen._commit_message
                self._log(f"Edited commit message: {self._pending_commit_msg}")
            self._start_commit_and_publish()
        # cancel: do nothing

    def _start_commit_and_publish(self):
        """Show progress screen, then execute commit + push + publish in background thread."""
        self._log("Starting commit and publish flow")
        self._log(f"Commit message: {self._pending_commit_msg}")
        self._log(f"no_verify: {self._commit_no_verify}")

        def do_work():
            log = self._progress_screen
            # Suppress stdout for thread safety
            old = sys.stdout
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
            try:
                # ── Execute commit ──
                self.call_from_thread(log.add_log, __("📦 Executing commit..."))
                self._log("Executing git commit...")
                # Inject the co-author trailer only now, so it never shows in the TUI
                commit_msg = self._pending_commit_msg
                if commit_msg:
                    from src.core import append_coauthor_trailer

                    commit_msg = append_coauthor_trailer(commit_msg)
                try:
                    success, output = execute_git_commit(
                        commit_msg, no_verify=self._commit_no_verify
                    )
                    self._log(
                        f"git commit result: success={success}, output={output.strip()}"
                    )
                except Exception as e:
                    self._log(f"git commit exception: {e}")
                    success, output = False, str(e)

                if not success:
                    out_lower = output.lower()
                    if any(
                        phrase in out_lower
                        for phrase in (
                            "nothing to commit",
                            "nothing added to commit",
                            "no changes added to commit",
                            "changes not staged",
                            "no changes",
                            "working tree clean",
                        )
                    ):
                        # Nothing new to commit — already done or staged, proceed
                        self._log(f"Commit skipped: {output.strip()[:200]}")
                        self.call_from_thread(
                            log.add_log, __("✅ Commit already done. Proceeding...")
                        )
                    else:
                        self.call_from_thread(
                            self._on_commit_publish_error,
                            __("❌ Commit Failed"),
                            output.strip() or __("Unknown error"),
                        )
                        return
                else:
                    self.call_from_thread(
                        log.add_log, __("✅ Commit executed successfully!")
                    )

                # ── Check for existing PR BEFORE pushing ──
                self._log("Checking for existing PR before push...")
                try:
                    from src.github_api import check_existing_pr

                    exists, pr_url, pr_num = check_existing_pr(
                        self.repo_info, self.github_token, self.head_branch
                    )
                    self._log(f"Existing PR check: exists={exists}, url={pr_url}")
                except Exception as e:
                    self._log(f"Existing PR check exception: {e}")
                    exists, pr_url, pr_num = False, None, None

                if exists:
                    self.call_from_thread(
                        self._on_existing_pr_found_before_push, pr_url, pr_num
                    )
                    self.call_from_thread(log.mark_finished)
                    return

                # ── Push ──
                self.call_from_thread(log.add_log, __("📤 Pushing to remote..."))
                self._log("Executing git push...")
                try:
                    push_result = subprocess.run(
                        ["git", "push", "origin", self.head_branch],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    self._log(f"git push result: rc={push_result.returncode}")
                    if push_result.returncode != 0:
                        err = push_result.stderr.strip() or push_result.stdout.strip()
                        # Auto-set upstream if needed
                        if "upstream" in err.lower() or "no upstream" in err.lower():
                            self._log("No upstream branch, setting upstream...")
                            up_result = subprocess.run(
                                [
                                    "git",
                                    "push",
                                    "--set-upstream",
                                    "origin",
                                    self.head_branch,
                                ],
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                            )
                            if up_result.returncode == 0:
                                self.call_from_thread(
                                    log.add_log, __("✅ Push successful!")
                                )
                            else:
                                err2 = (
                                    up_result.stderr.strip()
                                    or up_result.stdout.strip()
                                    or __("Unknown error")
                                )
                                self.call_from_thread(
                                    self._on_commit_publish_error,
                                    __("❌ Push Failed"),
                                    err2,
                                )
                                return
                        else:
                            self.call_from_thread(
                                self._on_commit_publish_error,
                                __("❌ Push Failed"),
                                err or __("Unknown error"),
                            )
                            return
                    else:
                        self.call_from_thread(log.add_log, __("✅ Push successful!"))
                    self.call_from_thread(log.add_log, __("✅ Push successful!"))
                except Exception as e:
                    self._log(f"git push exception: {e}")
                    self.call_from_thread(
                        self._on_commit_publish_error, __("❌ Push Failed"), str(e)
                    )
                    return

                # ── Create PR ──
                self.call_from_thread(
                    log.add_log, __("🚀 Creating pull request on GitHub...")
                )
                self.call_from_thread(self._publish_pr_from_progress, log)
                self.call_from_thread(log.mark_finished)
            finally:
                sys.stdout.close()
                sys.stdout = old

        self._progress_screen = CommitProgressScreen(
            initial_status=__("📦 Executing commit...")
        )
        self.push_screen(self._progress_screen)

        import threading

        threading.Thread(target=do_work, daemon=True).start()

    def _on_commit_publish_error(self, title, message):
        """Called on main thread when commit/push/publish fails."""
        self._progress_screen.mark_finished()
        self.pop_screen()
        self._show_error(
            title=title, message=message, on_retry=self._start_commit_and_publish
        )

    def _on_existing_pr_found_before_push(self, pr_url, pr_num):
        """Called BEFORE push when an open PR already exists for this branch."""
        self._progress_screen.mark_finished()
        self.pop_screen()
        self.push_screen(
            CommitConfirmScreen(
                title=__("⚠️ Existing Pull Request"),
                message=__(
                    "An open Pull Request already exists for this branch.\n\n"
                    "Push and update the existing PR?"
                ),
                btn_yes=__("Yes, Push and Update PR"),
                btn_no=__("No, Just Open Existing"),
            ),
            callback=lambda r: self._on_existing_pr_before_push_result(
                r, pr_url, pr_num
            ),
        )

    def _on_existing_pr_before_push_result(self, result, pr_url, pr_num):
        if result == "yes":
            self._push_and_exit(pr_url, pr_num)
        elif result == "no":
            if pr_url:
                self.final_pr_url = pr_url
                self.final_action = "created"
                self._prompt_open_browser(pr_url)
            else:
                self.final_message = __("⚠️ Open PR exists but URL not found.")
                self.final_action = "error"
                self.exit()
        else:
            # cancel: keep commit local, warn user
            self.final_message = __("⚠️ Open PR already exists. Commit kept locally.")
            self.final_action = "error"
            self.exit()

    def _push_and_exit(self, pr_url, pr_num):
        """Push to remote and update PR description in background, then show result."""
        body_input = self.query_one("#pr_body", TextArea)
        pr_body = body_input.text.strip()

        def _do_push():
            old = sys.stdout
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
            try:
                result = subprocess.run(
                    ["git", "push", "origin", self.head_branch],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                ok = result.returncode == 0
                self._log(f"Push to existing PR: ok={ok}, rc={result.returncode}")
                if not ok:
                    err = result.stderr.strip() or result.stdout.strip()
                    if "upstream" in err.lower():
                        self._log("No upstream branch, setting upstream...")
                        result2 = subprocess.run(
                            [
                                "git",
                                "push",
                                "--set-upstream",
                                "origin",
                                self.head_branch,
                            ],
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                        )
                        ok = result2.returncode == 0
                if ok:
                    self.final_action = "created"
                    # Update PR description with new body
                    self._log(
                        f"Push to existing PR succeeded, pr_num={pr_num}, updating description"
                    )
                    if pr_num and pr_body:
                        from src.github_api import update_pull_request

                        up_ok, up_data, up_status = update_pull_request(
                            self.repo_info,
                            self.github_token,
                            pr_num,
                            body=pr_body,
                        )
                        self._log(
                            f"Update PR description: ok={up_ok}, status={up_status}"
                        )
                    self.final_message = __(
                        "✅ PR updated:\n👉 {pr_url}",
                        pr_url=pr_url,
                    )
                    if pr_num:
                        auto_merge = os.getenv("GITPR_AUTO_MERGE", "false").lower() in (
                            "true",
                            "1",
                            "yes",
                            "y",
                        )
                        if auto_merge:
                            self.call_from_thread(self._do_merge, pr_num, pr_url)
                            return
                        self.call_from_thread(self._prompt_merge, pr_num, pr_url)
                        return
                else:
                    self.final_action = "error"
                    self.final_message = __(
                        "❌ Push failed: {error}",
                        error=result.stderr.strip() or result.stdout.strip(),
                    )
            except Exception as e:
                self._log(f"Push exception: {e}")
                self.final_action = "error"
                self.final_message = __("❌ Push failed: {error}", error=str(e))
            finally:
                sys.stdout.close()
                sys.stdout = old
            self.call_from_thread(self._prompt_open_browser, pr_url)

        import threading

        threading.Thread(target=_do_push, daemon=True).start()

    def _prompt_open_browser(self, pr_url):
        """Ask user if they want to open the PR in browser, then exit."""
        self.push_screen(
            CommitConfirmScreen(
                title=__("🔗 Open in Browser"),
                message=__("Open the Pull Request in your browser?"),
                btn_yes=__("Yes, Open Browser"),
                btn_no=__("No, Close"),
            ),
            callback=lambda r: self._on_browser_prompt_result(r, pr_url),
        )

    def _on_browser_prompt_result(self, result, pr_url):
        if result == "yes":
            import webbrowser

            webbrowser.open(pr_url)
        self.exit()

    def _prompt_merge(self, pr_number, pr_url):
        """Ask user if they want to merge the PR."""
        if not pr_number:
            self._prompt_open_browser(pr_url)
            return
        self.push_screen(
            CommitConfirmScreen(
                title=__("🔄 Merge Pull Request"),
                message=__("PR created successfully. Merge it now?"),
                btn_yes=__("Yes, Merge Now"),
                btn_no=__("No, Just Open PR"),
            ),
            callback=lambda r: self._on_merge_prompt_result(r, pr_number, pr_url),
        )

    def _on_merge_prompt_result(self, result, pr_number, pr_url):
        if result == "yes":
            self._do_merge(pr_number, pr_url)
        elif result == "no":
            self._prompt_open_browser(pr_url)
        else:
            self.exit()

    def _do_merge(self, pr_number, pr_url):
        """Execute merge via GitHub API in background thread."""

        def _merge():
            from src.github_api import merge_pull_request

            self._log(f"Merging PR #{pr_number}...")
            ok, data, status = merge_pull_request(
                self.repo_info, self.github_token, pr_number
            )
            self._log(f"Merge result: ok={ok}, status={status}, data={data}")
            if ok:
                self.call_from_thread(self._on_merge_success, pr_url)
            else:
                self.call_from_thread(self._on_merge_failure, pr_url, data, status)

        import threading

        threading.Thread(target=_merge, daemon=True).start()

    def _on_merge_success(self, pr_url):
        """Called on main thread after successful merge."""
        self.final_action = "merged"
        self.final_message = __(
            "✅ PR merged successfully:\n👉 {pr_url}",
            pr_url=pr_url,
        )
        self._prompt_open_browser(pr_url)

    def _on_merge_failure(self, pr_url, data, status):
        """Called on main thread after failed merge."""
        self.final_action = "merge_failed"
        msg = data.get("message", __("Unknown error"))

        # Special handling for merge conflicts (HTTP 405)
        if status == 405:
            title = __("❌ Merge Conflict")
            detail = __(
                "Pull Request has merge conflicts that must be resolved manually.\n\n"
                "👉 {pr_url}\n\n"
                "Error: {error}",
                pr_url=pr_url,
                error=msg,
            )
        else:
            title = __("❌ Merge Failed")
            detail = __(
                "Merge failed with status {status}.\n\n👉 {pr_url}\n\nError: {error}",
                status=status,
                pr_url=pr_url,
                error=msg,
            )

        self.final_message = f"{title}\n{detail}"

        # Show error modal and offer to open the PR in browser
        self.push_screen(
            CommitConfirmScreen(
                title=title,
                message=detail,
                btn_yes=__("Open PR in Browser"),
                btn_no=__("Close"),
            ),
            callback=lambda r: self._on_browser_prompt_result(r, pr_url),
        )

    def _publish_pr_from_progress(self, log_widget):
        """Create PR via GitHub API from within the progress screen. Updates final_* attrs."""
        from src.metrics import log_command_metric

        title_input = self.query_one("#pr_title", Input)
        body_input = self.query_one("#pr_body", TextArea)

        if not self.repo_info:
            self._log("PR publish failed: no repo_info")
            self.pop_screen()
            self._show_error(
                title=__("❌ PR Publication Failed"),
                message=__("Remote repository not identified."),
                on_retry=self._start_commit_and_publish,
            )
            return

        pr_title = (
            title_input.value.strip() or self._pending_commit_msg or self.pr_title
        )
        pr_body = body_input.text.strip()
        if not pr_body:
            self._log("PR publish failed: empty body")
            self.pop_screen()
            self._show_error(
                title=__("❌ PR Publication Failed"),
                message=__("PR description must not be empty."),
                on_retry=self._start_commit_and_publish,
            )
            return

        self._log(f"PR title: {pr_title}")
        self._log(f"PR body length: {len(pr_body)} chars, preview: {pr_body[:200]}")
        self._log(
            f"PR base: {self.base_branch}, head: {self.head_branch}, repo: {self.repo_info}"
        )

        try:
            md_content = (
                __("# 🚀 Pull Request Suggestion\n\n**Recommended Commit Message:**\n")
                + "```text\n"
                + f"{pr_title}\n"
                + "```\n\n---\n\n"
                + pr_body
            )
            with open(self.output_filename, "w", encoding="utf-8") as f:
                f.write(md_content)
        except Exception:
            pass

        full_body = pr_body

        try:
            ok, data, status = create_pull_request(
                self.repo_info,
                self.github_token,
                pr_title,
                full_body,
                self.head_branch,
                self.base_branch,
            )
            self._log(f"create_pull_request result: ok={ok}, status={status}")
        except Exception as e:
            self._log(f"create_pull_request exception: {e}")
            ok, data, status = False, {"message": str(e)}, 0

        if ok:
            self.pop_screen()
            pr_url = data.get("url", "")
            pr_number = data.get("number", 0)
            self._log(f"PR created successfully: {pr_url}, number={pr_number}")
            log_command_metric(
                command="pr:publish", status="success", provider="github"
            )
            self.final_pr_url = pr_url
            self.final_action = "created"
            self.final_message = __(
                "✅ PR successfully created on GitHub:\n👉 {pr_url}",
                pr_url=pr_url,
            )
            if self._log_path:
                self.final_message += f"\n📋 Log: {self._log_path}"

            auto_merge = os.getenv("GITPR_AUTO_MERGE", "false").lower() in (
                "true",
                "1",
                "yes",
                "y",
            )
            if auto_merge and pr_number:
                self._do_merge(pr_number, pr_url)
            else:
                self._prompt_merge(pr_number, pr_url)
        elif status == 401:
            self._log("PR publish failed: 401 unauthorized")
            self.pop_screen()
            self.final_action = "reauth"
            self.needs_new_token = True
            self.final_message = __(
                "🔐 GitHub token expired or invalid. You'll be prompted for a new one."
            )
            log_command_metric(command="pr:publish", status="reauth", provider="github")
            self.exit()
        else:
            error_msg = data.get("message", __("Unknown API error"))
            self._log(f"PR publish failed: {error_msg}")
            self.pop_screen()
            self._show_error(
                title=__("❌ PR Publication Failed"),
                message=error_msg,
                on_retry=self._start_commit_and_publish,
            )

    def _show_error(self, title, message, on_retry):
        """Show ErrorScreen with retry/cancel. Retry calls on_retry."""
        self.push_screen(
            ErrorScreen(title=title, message=message),
            callback=lambda r: self._on_error_result(r, on_retry),
        )

    def _on_error_result(self, result, on_retry):
        if result == "retry":
            on_retry()
        # cancel: stay on main TUI
