import click
from dotenv import set_key
from src.security import encrypt_data
from src.config import get_github_token, ENV_FILE

# Importa a classe do aplicativo da nossa nova pasta de classes
from src.ui.issue_app import IssueApp

def validate_or_request_github_token(repo_info):
    """Verifica se o PAT existe, caso contrário solicita ao usuário, encripta e salva."""
    token = get_github_token()
    if token:
        return token
    
    click.secho(f"\n🔐 Autenticação do GitHub Necessária", fg="cyan", bold=True)
    click.echo("Para criar issues diretamente, precisamos de um Personal Access Token (PAT).")
    click.echo("Clique no link abaixo para gerar um com a permissão 'repo' já selecionada:")
    
    repo_param = repo_info if repo_info else "seu-repositorio"
    url_token = f"https://github.com/settings/tokens/new?scopes=repo&description=GitPR+Token+({repo_param})"
    click.secho(f"👉 {url_token}\n", fg="blue", underline=True)
    
    # Link dinâmico para a documentação técnica
    click.secho("📚 Entenda por que precisamos do Token e como ele é protegido por criptografia:", fg="cyan", dim=True)
    click.secho("👉 https://github.com/natanfiuza/gitpr/blob/main/docs/github-pat-integration.md\n", fg="blue", underline=True)
    
    raw_token = click.prompt("Cole aqui o seu Token (PAT)", hide_input=True)
    
    encrypted_token = encrypt_data(raw_token.strip())
    
    set_key(ENV_FILE, "GITHUB_TOKEN_ENCRYPTED", encrypted_token)
    click.secho("✅ Token encriptado e salvo com segurança no .env!\n", fg="green")
    
    return raw_token.strip()
