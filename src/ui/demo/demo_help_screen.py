from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from src.i18n import __


class DemoHelpScreen(ModalScreen):
    """Help modal for the guided tour, mirroring src/ui/help_screen.py."""

    # While the modal is up the app's own bindings are out of the chain, so Esc
    # would otherwise do nothing — and the tour promises that Esc leaves.
    BINDINGS = [Binding("escape", "app.pop_screen", "", show=False)]

    CSS = """
    DemoHelpScreen { align: center middle; }
    #demo_help_dialog {
        width: 80; height: auto; padding: 1 2; background: $surface; border: thick $background 80%;
        align-horizontal: center;
    }
    .help_title { text-align: center; text-style: bold; margin-bottom: 1; }
    .help_text { margin-bottom: 1; }
    Button {
        width: 20%;
        margin-top: 1;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="demo_help_dialog"):
            yield Static(__("💡 GitPR Demo Help"), classes="help_title")
            yield Static(
                __("• N / → / Enter: next step of the tour.\n")
                + __("• P / ←: previous step.\n")
                + __("• F1 (Help): displays this instruction modal.\n")
                + __("• Esc (Exit): leaves the tour.\n\n")
                # One key, not two halves of a sentence: the line break sits
                # mid-clause and other languages would not put it there.
                + __(
                    "The tour runs on a recorded example: no API key, no Git\n"
                    "repository and no connection are needed.\n"
                ),
                classes="help_text",
            )
            yield Button(__("Got it"), variant="primary", id="close_demo_help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_demo_help":
            self.app.pop_screen()
