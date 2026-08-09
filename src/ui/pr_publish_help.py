from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Vertical
from src.i18n import CURRENT_LANG, __
from src.core import (    
    get_doc_url,    
)

class PrPublishHelpScreen(ModalScreen):
    """Help modal with PR publishing interface usage instructions."""

    CSS = """
    PrPublishHelpScreen { align: center middle; }
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
        help_url = get_doc_url("pull-request-publication.md")
        with Vertical(id="help_dialog"):
            yield Static(__("💡 GitPR PR Publisher Help"), classes="help_title")
            yield Static(
                __("• F1 (Help): Displays this instruction modal.\n") +
                __("• F2 (Save Local): Saves the updated PR content to a local .md file.\n") +
                __("• F3 (Publish PR): Auto-commits pending changes (with lint validation), then creates the Pull Request on GitHub via API.\n") +
                __("• Esc (Exit): Closes the application without publishing.\n\n") +
                __("📚 Read the complete PR publication guide:\n") +
                help_url,
                classes="help_text"
            )
            yield Button(__("Got it"), variant="primary", id="close_help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_help":
            self.app.pop_screen()
