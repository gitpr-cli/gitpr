import click
from dotenv import set_key
from src.security import encrypt_data
from src.config import get_github_token, validate_github_token, ENV_FILE
from src.i18n import __, CURRENT_LANG

# Import the app class from our UI sub-package
from src.ui.issue_app import IssueApp


MAX_TOKEN_ATTEMPTS = 3


def _remove_expired_token():
    """Removes the expired GITHUB_TOKEN_ENCRYPTED line from the .env file."""
    import os

    if not os.path.exists(ENV_FILE):
        return

    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            for line in lines:
                if not line.startswith("GITHUB_TOKEN_ENCRYPTED="):
                    f.write(line)
    except Exception:
        pass  # Non-critical — the user can manually remove it if needed


def _show_auth_instructions(repo_info):
    """Displays instructions for generating a new GitHub PAT."""
    click.secho(__("\n🔐 GitHub Authentication Required"), fg="cyan", bold=True)
    click.echo(__("To create issues directly, we need a Personal Access Token (PAT)."))
    click.echo(
        __(
            "Click the link below to generate one with the 'repo' scope already selected:"
        )
    )

    repo_param = repo_info if repo_info else "your-repository"
    url_token = f"https://github.com/settings/tokens/new?scopes=repo&description=GitPR+Token+({repo_param})"
    click.secho(f"👉 {url_token}\n", fg="blue", underline=True)

    # Dynamic link to the technical documentation with language suffix
    lang_suffix = "" if CURRENT_LANG.startswith("en") else f".{CURRENT_LANG}"
    doc_url = f"https://github.com/gitpr-cli/gitpr.git/blob/main/docs/github-pat-integration{lang_suffix}.md"
    click.secho(
        __(
            "📚 Understand why we need the Token and how it is protected by encryption:"
        ),
        fg="cyan",
        dim=True,
    )
    click.secho(f"👉 {doc_url}\n", fg="blue", underline=True)


def _prompt_and_save_token(repo_info):
    """Prompts the user for a new GitHub PAT, encrypts and saves it, then returns the raw token."""
    _show_auth_instructions(repo_info)

    raw_token = click.prompt(__("Paste your Token (PAT) here"), hide_input=True)

    encrypted_token = encrypt_data(raw_token.strip())

    set_key(ENV_FILE, "GITHUB_TOKEN_ENCRYPTED", encrypted_token)
    click.secho(__("✅ Token encrypted and safely saved in .env!"), fg="green")

    return raw_token.strip()


def validate_or_request_github_token(repo_info):
    """
    Checks if the PAT exists, validates it against the GitHub API,
    and re-prompts if the token is expired or invalid.

    Gives the user up to MAX_TOKEN_ATTEMPTS chances to provide a valid token.
    """
    for attempt in range(1, MAX_TOKEN_ATTEMPTS + 1):
        token = get_github_token()

        if token:
            # Token exists — validate it against the GitHub API
            click.secho(__("🔍 Validating GitHub token..."), fg="cyan", dim=True)
            is_valid, error_msg = validate_github_token(token)

            if is_valid:
                click.secho(__("✅ GitHub token is valid!\n"), fg="green")
                return token

            # Token is invalid (expired, revoked, etc.)
            click.secho(
                __(
                    "⚠️ GitHub token is no longer valid: {error_msg}",
                    error_msg=error_msg,
                ),
                fg="yellow",
            )
            click.secho(
                __(
                    "📋 Attempt {attempt} of {max}",
                    attempt=attempt,
                    max=MAX_TOKEN_ATTEMPTS,
                ),
                dim=True,
            )
            _remove_expired_token()
            click.secho(
                __("🗑️  Expired token removed. Let's configure a new one."), fg="yellow"
            )
        else:
            # No token found — first run or already removed
            if attempt == 1:
                click.secho(__("🔐 No GitHub token found."), fg="yellow", dim=True)

        # Prompt for a new token
        new_token = _prompt_and_save_token(repo_info)

        # Validate the newly provided token
        click.secho(__("🔍 Validating new token..."), fg="cyan", dim=True)
        is_valid, error_msg = validate_github_token(new_token)

        if is_valid:
            click.secho(__("✅ GitHub token is valid!\n"), fg="green")
            return new_token

        # New token is also invalid — remove it and try again
        click.secho(
            __(
                "⚠️ The provided token is also invalid: {error_msg}", error_msg=error_msg
            ),
            fg="yellow",
        )
        _remove_expired_token()

        if attempt < MAX_TOKEN_ATTEMPTS:
            click.secho(__("🔄 Let's try again...\n"), fg="yellow")

    # Exhausted all attempts
    click.secho(
        __(
            "❌ Maximum attempts ({max}) reached. Cannot proceed without a valid token.",
            max=MAX_TOKEN_ATTEMPTS,
        ),
        fg="red",
    )
    return None
