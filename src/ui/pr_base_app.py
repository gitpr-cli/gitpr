"""The picker shown when the pull request target is the current branch.

The full configuration screen is too much for a run that only needs one
answer: GitPR is about to publish, the resolved base equals the branch being
published, and the request cannot target itself. This screen asks for the one
value that fixes the run — the repository's PR target base branch — writes it
to the project file and lets the caller continue.

Kept apart from config_app.py so the publish path never imports the whole
screen for one modal, and so the modal can be driven headless in tests.
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Select, Static

from src.i18n import __

BRANCH_SELECT_ID = "prompt_branch"


class BaseBranchPromptApp(App):
    """Asks for a new PR target branch, offering every branch but the current."""

    TITLE = __("GitPR - PR Target Base Branch")
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    #prompt-box { padding: 1 2; width: 80; height: auto; border: solid $accent; }
    .prompt-title { text-style: bold; margin-bottom: 1; }
    .prompt-help { color: $text-muted; margin-bottom: 1; }
    #prompt-actions { height: auto; margin-top: 1; }
    #prompt-actions Button { margin-right: 2; }
    """

    BINDINGS = [("escape", "cancel", __("Cancel"))]

    def __init__(self, current, branches, **kwargs):
        super().__init__(**kwargs)
        self.current = current
        # The current branch is not an option: it is the one the pull request
        # is being opened from.
        self.branches = [branch for branch in branches if branch != current]

    def compose(self) -> ComposeResult:
        with Vertical(id="prompt-box"):
            yield Static(
                __("The pull request target must differ from the current branch."),
                classes="prompt-title",
            )
            yield Static(
                __(
                    "This repository targets '{current}', which is the branch you are on. A pull request cannot target itself. Choose another base branch — the choice is saved in the project configuration.",
                    current=self.current,
                ),
                classes="prompt-help",
            )
            yield Select(
                [(branch, branch) for branch in self.branches],
                value=self.branches[0],
                allow_blank=False,
                id=BRANCH_SELECT_ID,
            )
            with Horizontal(id="prompt-actions"):
                yield Button(
                    __("Save and continue"),
                    id="btn_prompt_confirm",
                    variant="primary",
                )
                yield Button(__("Cancel"), id="btn_prompt_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_prompt_confirm":
            self._confirm()
        else:
            self.exit("")

    def action_cancel(self) -> None:
        self.exit("")

    def _confirm(self) -> None:
        value = self.query_one(f"#{BRANCH_SELECT_ID}", Select).value
        if not value or value == self.current:
            self.notify(
                __("Choose a base branch other than the current one."),
                severity="warning",
            )
            return
        self.exit(str(value))


def prompt_for_base_branch(current, branches):
    """Runs the picker and returns the chosen branch, or "" on cancel."""
    options = [branch for branch in branches if branch != current]
    if not options:
        # Nothing to choose from — the caller reports the original error.
        return ""
    return str(BaseBranchPromptApp(current, options).run() or "")
