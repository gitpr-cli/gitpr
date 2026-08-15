from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Label, Button
from src.i18n import __

class LinterApp(App):
    """TUI for displaying Linter errors."""
    CSS = """
    Screen { background: $surface; }
    .alert-container { margin: 1 2; }
    .error-text { color: red; text-style: bold; }
    .warning-text { color: yellow; }
    #btn-container { align: center bottom; margin-top: 2; height: 3; }
    """

    BINDINGS = [
        ("q", "quit", __("Quit")),
    ]

    def __init__(self, alerts):
        super().__init__()
        self.alerts = alerts

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(classes="alert-container"):
            if self.alerts["errors"]:
                yield Label(__("❌ Critical Errors:"), classes="error-text")
                for err in self.alerts["errors"]:
                    yield Label(f"  - {err}", classes="error-text")
                yield Label("")

            if self.alerts["warnings"]:
                yield Label(__("⚠️ Warnings:"), classes="warning-text")
                for warn in self.alerts["warnings"]:
                    yield Label(f"  - {warn}", classes="warning-text")

        with Horizontal(id="btn-container"):
            yield Button(__("Acknowledge & Exit"), variant="error", id="btn_exit")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_exit":
            self.exit(1)
