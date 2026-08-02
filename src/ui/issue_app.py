import os
import requests
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, TextArea, Label
from textual.containers import Vertical
from textual.binding import Binding

from src.core import get_current_branch
from src.ui.help_screen import HelpScreen
from src.i18n import __

class IssueApp(App):
    """Terminal Interface for editing and submitting Issues."""
    
    TITLE = __("GitPR - Issue Generator")
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Input { margin-bottom: 1; }
    TextArea { height: 1fr; }
    Label { margin-top: 1; text-style: bold; color: $accent; }
    """

    BINDINGS = [
        Binding("f1", "show_help", __("Help")),
        Binding("f2", "save_local", __("Save Local")),
        Binding("f3", "create_issue", __("Create on GitHub")),
        Binding("escape", "quit", __("Exit"))
    ]

    def __init__(self, issue_data, repo_info, github_token, **kwargs):
        super().__init__(**kwargs)
        self.issue_data = issue_data
        self.repo_info = repo_info
        self.github_token = github_token
        self.final_action = None
        self.final_message = ""
        self.needs_new_token = False
        
        branch = get_current_branch()
        repo_display = self.repo_info if self.repo_info else __("Local Repository")
        self.sub_title = f"{repo_display} | Branch: {branch}"

    def compose(self) -> ComposeResult:
        """Builds the interface layout."""
        yield Header(show_clock=True)
        with Vertical():
            yield Label(__("📌 Issue Title"))
            yield Input(value=self.issue_data.get("titulo", ""), id="issue_title")

            yield Label(__("📝 Issue Body"))
            yield TextArea(text=self.issue_data.get("corpo", ""), id="issue_body")
        yield Footer()

    def action_show_help(self):
        """F1 button action: Displays the help modal."""
        self.push_screen(HelpScreen())

    def action_save_local(self):
        """F2 button action: Saves the content to a local markdown file."""
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
            self.final_message = __("✅ Issue saved locally: {output_filename}", output_filename=output_filename)
            self.final_action = "saved"
        except Exception as e:
            self.final_message = __("❌ Error saving file: {error}", error=str(e))
            self.final_action = "error"
        
        self.exit()

    def action_create_issue(self):
        """F3 button action: Sends the issue via REST API to GitHub."""
        from src.metrics import log_command_metric

        title_input = self.query_one("#issue_title", Input)
        body_input = self.query_one("#issue_body", TextArea)

        if not self.repo_info:
            self.final_message = __("❌ Remote repository not identified to create the issue via API.")
            self.final_action = "error"
            log_command_metric(command="issue:github_create", status="error", provider="github")
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
                self.final_message = __("✅ Issue successfully created on GitHub:\n👉 {issue_url}", issue_url=issue_url)
                self.final_action = "created"
                log_command_metric(command="issue:github_create", status="success", provider="github")
            elif response.status_code == 401:
                self.final_message = __("🔐 GitHub token expired or invalid. You'll be prompted for a new one.")
                self.final_action = "reauth"
                self.needs_new_token = True
                log_command_metric(command="issue:github_create", status="reauth", provider="github")
            else:
                self.final_message = __("❌ GitHub API Error ({status_code}): {response_text}", status_code=response.status_code, response_text=response.text)
                self.final_action = "error"
                log_command_metric(command="issue:github_create", status="error", provider="github", http_status=response.status_code)
        except Exception as e:
            self.final_message = __("❌ Failed to connect to GitHub: {error}", error=str(e))
            self.final_action = "error"
            log_command_metric(command="issue:github_create", status="error", provider="github")

        self.exit()