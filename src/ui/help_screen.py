from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Vertical

class HelpScreen(ModalScreen):
    """Modal de ajuda com as instruções de uso da interface."""
    
    CSS = """
    HelpScreen { align: center middle; }
    #help_dialog { width: 60; height: auto; padding: 1 2; background: $surface; border: thick $background 80%; }
    .help_title { text-align: center; text-style: bold; margin-bottom: 1; }
    .help_text { margin-bottom: 1; }
    Button { width: 100%; }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="help_dialog"):
            yield Static("💡 Ajuda do GitPR Issue", classes="help_title")
            yield Static(
                "• F4 (Ajuda): Exibe este modal de instruções.\n"
                "• F2 (Salvar Local): Gera um arquivo Markdown (.md) com a issue.\n"
                "• F3 (Criar no GitHub): Cria a issue remotamente via API.\n"
                "• Esc (Sair): Fecha o aplicativo sem salvar.\n\n"
                "📚 Leia o guia completo de utilização da interface TUI:\n"
                "https://github.com/natanfiuza/gitpr/blob/main/docs/issue-tui-help.md", 
                classes="help_text"
            )
            yield Button("Entendi", variant="primary", id="close_help")
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_help":
            self.app.pop_screen()