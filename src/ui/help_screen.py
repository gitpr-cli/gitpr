from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Vertical
from src.i18n import CURRENT_LANG, __


class HelpScreen(ModalScreen):
    """Help modal with interface usage instructions."""

    CSS = """
    HelpScreen { align: center middle; }
    #help_dialog { 
        width: 90; height: auto; padding: 1 2; background: $surface; border: thick $background 80%; 
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
        lang_suffix = "" if CURRENT_LANG.startswith("en") else f".{CURRENT_LANG}"
        help_url = f"https://github.com/gitpr-cli/gitpr.git/blob/main/docs/issue-tui-help{lang_suffix}.md"
        with Vertical(id="help_dialog"):
            yield Static(__("💡 GitPR Issue Help"), classes="help_title")
            yield Static(
                __("• F1 (Help): Displays this instruction modal.\n")
                + __(
                    "• F2 (Save Local): Generates a Markdown (.md) file with the issue.\n"
                )
                + __("• F3 (Create on GitHub): Creates the issue remotely via API.\n")
                + __("• Esc (Exit): Closes the application without saving.\n\n")
                + __("📚 Read the complete TUI interface usage guide:\n")
                + help_url,
                classes="help_text",
            )
            yield Button(__("Got it"), variant="primary", id="close_help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_help":
            self.app.pop_screen()
