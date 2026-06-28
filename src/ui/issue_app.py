import os
import requests
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, TextArea, Label
from textual.containers import Vertical
from textual.binding import Binding

from src.core import get_current_branch
from src.ui.help_screen import HelpScreen

class IssueApp(App):
    """Interface de Terminal para edição e submissão da Issue."""
    
    TITLE = "GitPR - Gerador de Issues"
    ENABLE_COMMAND_PALETTE = False
    
    CSS = """
    Input { margin-bottom: 1; }
    TextArea { height: 1fr; }
    Label { margin-top: 1; text-style: bold; color: $accent; }
    """
    
    BINDINGS = [
        Binding("f4", "show_help", "Ajuda"),
        Binding("f2", "save_local", "Salvar Local"),
        Binding("f3", "create_issue", "Criar no GitHub"),
        Binding("escape", "quit", "Sair")
    ]

    def __init__(self, issue_data, repo_info, github_token, **kwargs):
        super().__init__(**kwargs)
        self.issue_data = issue_data
        self.repo_info = repo_info
        self.github_token = github_token
        self.final_action = None
        self.final_message = ""
        
        branch = get_current_branch()
        repo_display = self.repo_info if self.repo_info else "Repositório Local"
        self.sub_title = f"{repo_display} | Branch: {branch}"

    def compose(self) -> ComposeResult:
        """Monta o layout da interface."""
        yield Header(show_clock=True)
        with Vertical():
            yield Label("📌 Título da Issue")
            yield Input(value=self.issue_data.get("titulo", ""), id="issue_title")
            
            yield Label("📝 Corpo da Issue")
            yield TextArea(text=self.issue_data.get("corpo", ""), id="issue_body")
        yield Footer()

    def action_show_help(self):
        """Ação do botão F1: Exibe o modal de ajuda."""
        self.push_screen(HelpScreen())

    def action_save_local(self):
        """Ação do botão F2: Salva o conteúdo em um arquivo markdown local."""
        title_input = self.query_one("#issue_title", Input)
        body_input = self.query_one("#issue_body", TextArea)
        
        branch_name = get_current_branch().replace("/", "-").replace("\\", "-")
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        
        pattern = os.getenv("OUTPUT_FILE_NAME_ISSUE", "{branch}_{datetime}_ISSUE.md")
        output_filename = pattern.format(branch=branch_name, datetime=current_time)
        
        md_content = f"# {title_input.value}\n\n{body_input.text}"
        
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(md_content)
            self.final_message = f"✅ Issue salva localmente: {output_filename}"
            self.final_action = "saved"
        except Exception as e:
            self.final_message = f"❌ Erro ao salvar arquivo: {e}"
            self.final_action = "error"
        
        self.exit()

    def action_create_issue(self):
        """Ação do botão F3: Envia a issue via API REST para o GitHub."""
        title_input = self.query_one("#issue_title", Input)
        body_input = self.query_one("#issue_body", TextArea)
        
        if not self.repo_info:
            self.final_message = "❌ Repositório remoto não identificado para criar a issue via API."
            self.final_action = "error"
            self.exit()
            return
        
        api_url = f"https://api.github.com/repos/{self.repo_info}/issues"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "title": title_input.value,
            "body": body_input.text
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            if response.status_code == 201:
                issue_url = response.json().get("html_url")
                self.final_message = f"✅ Issue criada com sucesso no GitHub:\n👉 {issue_url}"
                self.final_action = "created"
            else:
                self.final_message = f"❌ Erro na API do GitHub ({response.status_code}): {response.text}"
                self.final_action = "error"
        except Exception as e:
            self.final_message = f"❌ Falha na conexão com o GitHub: {e}"
            self.final_action = "error"
        
        self.exit()