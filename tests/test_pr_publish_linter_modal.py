"""Regression tests for the linter error modal in the PR publish TUI.

Covers the bugs fixed on 2026-08-19:
1. Buttons overlapped: "Commit with --no-verify" and "Abort" now sit side
   by side inside the dialog, both fully rendered.
2. Clicking "Commit with --no-verify" dismissed the modal and did nothing
   (the linter would even run again and loop back into the modal). It now
   resumes the flow with the linter skipped and the commit executes with
   no_verify=True.
3. "Abort" dismisses the modal and returns to the TUI without committing.
"""
import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Button, Static

from src.infrastructure.scm import PullRequestResult
from src.ui.pr_publish_app import (
    CommitConfirmScreen,
    CommitMessageScreen,
    LinterErrorScreen,
    PrPublishApp,
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


def _make_linter_screen(errors=None):
    return LinterErrorScreen(
        errors=errors or [f"violation {i}: line too long" for i in range(1, 13)]
    )


def test_linter_buttons_side_by_side_no_overlap():
    """Both buttons share the same row, don't overlap, and fit the dialog."""

    async def run():
        app = _ModalHostApp(_make_linter_screen())
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            no_verify = app.screen.query_one("#btn_no_verify", Button)
            abort = app.screen.query_one("#btn_abort", Button)
            assert no_verify.region.y == abort.region.y, "buttons must share the same row"
            assert not no_verify.region.overlaps(abort.region), "buttons must not overlap"
            dialog = app.screen.query_one("#linter_dialog")
            assert dialog.region.contains_region(no_verify.region), "no-verify button clipped"
            assert dialog.region.contains_region(abort.region), "abort button clipped"
            # The dialog hugs content instead of filling the whole screen.
            assert dialog.region.height < 24

    asyncio.run(run())


def test_abort_button_dismisses_with_abort_result():
    """Abort dismisses the modal with an 'abort' result."""

    async def run():
        app = _ModalHostApp(_make_linter_screen())
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.click("#btn_abort")
            await pilot.pause()
            assert app.screen_result == "abort"

    asyncio.run(run())


def test_no_verify_button_dismisses_with_no_verify_result():
    """The no-verify button dismisses the modal with a 'no_verify' result."""

    async def run():
        app = _ModalHostApp(_make_linter_screen())
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.click("#btn_no_verify")
            await pilot.pause()
            assert app.screen_result == "no_verify"

    asyncio.run(run())


def test_no_verify_flow_skips_linter_and_commits(monkeypatch, tmp_path):
    """Full flow: linter error modal -> --no-verify -> commit with no_verify=True.

    Guards against the old behavior where the button dismissed the modal and
    the flow either stopped or looped back into the linter modal forever.
    """
    lint_calls = []
    commit_calls = []

    def fake_lint(diff_text):
        lint_calls.append(diff_text)
        return {"errors": ["ERR fake violation"], "warnings": []}

    def fake_commit(message, no_verify=False):
        commit_calls.append((message, no_verify))
        return (True, "ok")

    monkeypatch.setattr("src.linter_engine.parse_diff_and_lint", fake_lint)
    monkeypatch.setattr("src.core.get_git_diff", lambda *a, **k: "fake diff")
    monkeypatch.setattr(
        "src.core.generate_pr_content",
        lambda *a, **k: {"commit_message": "feat: fake commit"},
    )
    monkeypatch.setattr("src.core.append_coauthor_trailer", lambda msg: msg)
    monkeypatch.setattr("src.config.get_ai_provider", lambda: "gemini")
    monkeypatch.setattr(
        "src.ui.pr_publish_app.execute_git_commit", fake_commit
    )
    monkeypatch.setattr(
        "src.ui.pr_publish_app.has_uncommitted_changes", lambda: True
    )
    monkeypatch.setattr(
        "src.ui.pr_publish_app._check_existing_pull_request",
        lambda *a, **k: PullRequestResult(
            id=42,
            url="https://example.com/pr/42",
            number=42,
            state="open",
            source_branch="head",
            target_branch="main",
            provider="github",
        ),
    )
    monkeypatch.setenv("PR_PUBLISH_LOG", "false")

    async def run():
        app = PrPublishApp(
            pr_data={"commit_message": "m", "pr_description": "d"},
            repo_info="owner/repo",
            github_token="tok",
            base_branch="main",
            output_filename=str(tmp_path / "pr.md"),
        )
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()

            # F3 flow: uncommitted changes -> commit confirmation
            app.action_publish_pr()
            await pilot.pause()
            assert isinstance(app.screen, CommitConfirmScreen)
            await pilot.click("#btn_yes")

            # Progress screen runs the linter -> error modal appears
            await pilot.pause(0.6)
            assert isinstance(app.screen, LinterErrorScreen)
            assert len(lint_calls) == 1

            # Choose --no-verify: flow resumes with the linter skipped
            await pilot.click("#btn_no_verify")
            await pilot.pause(0.6)
            assert len(lint_calls) == 1, "linter must not run again after --no-verify"
            assert app._commit_no_verify is True

            # AI commit message ready -> message confirmation screen
            await pilot.pause(0.6)
            assert isinstance(app.screen, CommitMessageScreen)
            await pilot.click("#btn_confirm")

            # Commit executes with no_verify=True; existing-PR prompt ends the flow
            await pilot.pause(0.8)
            assert commit_calls, "commit must be executed"
            assert commit_calls[0][1] is True, "commit must run with no_verify=True"
            assert isinstance(app.screen, CommitConfirmScreen)

    asyncio.run(run())
