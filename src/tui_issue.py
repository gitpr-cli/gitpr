import click
from dotenv import set_key
from src.security import encrypt_data
from src.config import get_github_token, ENV_FILE
from src.i18n import __, CURRENT_LANG

# Import the app class from our UI sub-package
from src.ui.issue_app import IssueApp

def validate_or_request_github_token(repo_info):
    """Checks if the PAT exists, otherwise prompts the user, encrypts, and saves it."""
    token = get_github_token()
    if token:
        return token
    
    click.secho(__("\n🔐 GitHub Authentication Required"), fg="cyan", bold=True)
    click.echo(__("To create issues directly, we need a Personal Access Token (PAT)."))
    click.echo(__("Click the link below to generate one with the 'repo' scope already selected:"))
    
    repo_param = repo_info if repo_info else "your-repository"
    url_token = f"https://github.com/settings/tokens/new?scopes=repo&description=GitPR+Token+({repo_param})"
    click.secho(f"👉 {url_token}\n", fg="blue", underline=True)
    
    # Dynamic link to the technical documentation with language suffix
    lang_suffix = "" if CURRENT_LANG.startswith("en") else f".{CURRENT_LANG}"
    doc_url = f"https://github.com/natanfiuza/gitpr/blob/main/docs/github-pat-integration{lang_suffix}.md"
    click.secho(__("📚 Understand why we need the Token and how it is protected by encryption:"), fg="cyan", dim=True)
    click.secho(f"👉 {doc_url}\n", fg="blue", underline=True)
    
    raw_token = click.prompt(__("Paste your Token (PAT) here"), hide_input=True)
    
    encrypted_token = encrypt_data(raw_token.strip())
    
    set_key(ENV_FILE, "GITHUB_TOKEN_ENCRYPTED", encrypted_token)
    click.secho(__("✅ Token encrypted and safely saved in .env!\n"), fg="green")
    
    return raw_token.strip()
