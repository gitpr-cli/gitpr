import click
from dotenv import set_key
from src.security import encrypt_data
from src.config import ENV_FILE
from src.i18n import __, CURRENT_LANG
from src.infrastructure.scm import (
    ScmProviderError,
    provider_display_name,
    provider_is_github,
)


MAX_TOKEN_ATTEMPTS = 3


def _remove_expired_token(env_var="GITHUB_TOKEN_ENCRYPTED"):
    """Removes the expired *env_var* line from the .env file."""
    import os

    if not os.path.exists(ENV_FILE):
        return

    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            for line in lines:
                if not line.startswith(f"{env_var}="):
                    f.write(line)
    except Exception:
        pass  # Non-critical — the user can manually remove it if needed


def _scm_token_configured():
    """True when GITPR_SCM_TOKEN* holds a credential (raw or encrypted).

    GitHub flows keep the legacy GITHUB_TOKEN_ENCRYPTED store unless the user
    explicitly configured the multi-forge token store.
    """
    from src.config import get_scm_token

    return bool(get_scm_token())


def _token_env_var(provider):
    """.env key that receives a re-authenticated token for *provider*.

    GitHub without multi-forge config keeps the legacy GITHUB_TOKEN_ENCRYPTED
    store (zero migration, byte parity); GitHub configured through GITPR_SCM_*
    and every other forge persist to GITPR_SCM_TOKEN_ENCRYPTED.
    """
    if provider_is_github(provider) and not _scm_token_configured():
        return "GITHUB_TOKEN_ENCRYPTED"
    return "GITPR_SCM_TOKEN_ENCRYPTED"


def _show_auth_instructions(provider, repo_display):
    """Displays instructions for generating a new access token for the forge."""
    if provider_is_github(provider):
        click.secho(__("\n🔐 GitHub Authentication Required"), fg="cyan", bold=True)
        click.echo(
            __("To create issues directly, we need a Personal Access Token (PAT).")
        )
        click.echo(
            __(
                "Click the link below to generate one with the 'repo' scope already selected:"
            )
        )

        repo_param = repo_display if repo_display else "your-repository"
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
        return

    label = provider_display_name(provider)
    click.secho(
        __("\n🔐 {provider} Authentication Required", provider=label),
        fg="cyan",
        bold=True,
    )
    click.echo(
        __(
            "{provider} needs an access token to create pull requests and issues on your behalf.",
            provider=label,
        )
    )
    click.echo(
        __(
            "Generate the token in your {provider} account settings, then paste it below:",
            provider=label,
        )
    )
    click.echo("")


def _prompt_and_save_token(provider, repo_display, env_var):
    """Prompts for a new forge token, encrypts and saves it, then returns the raw token."""
    _show_auth_instructions(provider, repo_display)

    if provider_is_github(provider):
        raw_token = click.prompt(__("Paste your Token (PAT) here"), hide_input=True)
    else:
        raw_token = click.prompt(
            __(
                "Paste your {provider} token here",
                provider=provider_display_name(provider),
            ),
            hide_input=True,
        )

    encrypted_token = encrypt_data(raw_token.strip())

    set_key(ENV_FILE, env_var, encrypted_token)
    click.secho(__("✅ Token encrypted and safely saved in .env!"), fg="green")

    return raw_token.strip()


def _error_message(exc, github_flow, label):
    """User-facing message for a failed test_connection (ScmProviderError)."""
    if exc.http_status == 401:
        return __("Token expired or invalid. Please generate a new one.")
    if exc.http_status > 0:
        if github_flow:
            return __(
                "Unexpected response from GitHub (HTTP {code})", code=exc.http_status
            )
        return __(
            "Unexpected response from {provider} (HTTP {code})",
            provider=label,
            code=exc.http_status,
        )
    return exc.message  # network failures already arrive localized


def _valid_token_message(provider):
    """Green confirmation shown when the token validated successfully."""
    if provider_is_github(provider):
        return __("✅ GitHub token is valid!\n")
    return __(
        "✅ {provider} token is valid!\n",
        provider=provider_display_name(provider),
    )


def _no_longer_valid_message(provider, error_msg):
    """Yellow warning shown when an existing token fails validation (401)."""
    if provider_is_github(provider):
        return __(
            "⚠️ GitHub token is no longer valid: {error_msg}", error_msg=error_msg
        )
    return __(
        "⚠️ {provider} token is no longer valid: {error_msg}",
        provider=provider_display_name(provider),
        error_msg=error_msg,
    )


def validate_or_request_scm_token(provider, repo_display):
    """
    Ensures the forge has a valid token, validating it against the forge API
    and re-prompting (up to MAX_TOKEN_ATTEMPTS chances) when it is missing,
    expired or invalid.

    Token storage follows the forge configuration (see _token_env_var):
    GitHub without multi-forge config keeps the legacy GITHUB_TOKEN_ENCRYPTED
    store — zero migration for existing users. Connectivity/server-side
    failures abort with a message: they cannot be fixed by re-prompting.

    Returns (token, provider) on success — when a fresh token was saved the
    returned provider carries it (via with_token) — or (None, provider) when
    the user cancels or the attempts run out.
    """
    github_flow = provider_is_github(provider)
    label = provider_display_name(provider)
    token = provider.token

    for attempt in range(1, MAX_TOKEN_ATTEMPTS + 1):
        if token:
            # Token exists — validate it against the forge API
            if github_flow:
                click.secho(__("🔍 Validating GitHub token..."), fg="cyan", dim=True)
            else:
                click.secho(
                    __("🔍 Validating {provider} token...", provider=label),
                    fg="cyan",
                    dim=True,
                )
            try:
                provider.test_connection()
                click.secho(_valid_token_message(provider), fg="green")
                return token, provider
            except ScmProviderError as e:
                error_msg = _error_message(e, github_flow, label)
                if e.http_status == 401:
                    # Token is invalid (expired, revoked, etc.)
                    click.secho(
                        _no_longer_valid_message(provider, error_msg), fg="yellow"
                    )
                    click.secho(
                        __(
                            "📋 Attempt {attempt} of {max}",
                            attempt=attempt,
                            max=MAX_TOKEN_ATTEMPTS,
                        ),
                        dim=True,
                    )
                    _remove_expired_token(_token_env_var(provider))
                    click.secho(
                        __("🗑️  Expired token removed. Let's configure a new one."),
                        fg="yellow",
                    )
                    token = None
                else:
                    # Connectivity/server-side failure — re-prompting cannot
                    # fix it; surface the localized message and stop.
                    click.secho(f"❌ {error_msg}", fg="red")
                    return None, provider
        else:
            # No token found — first run or already removed
            if attempt == 1:
                if github_flow:
                    click.secho(__("🔐 No GitHub token found."), fg="yellow", dim=True)
                else:
                    click.secho(
                        __("🔐 No {provider} token found.", provider=label),
                        fg="yellow",
                        dim=True,
                    )

        # Prompt for a new token
        env_var = _token_env_var(provider)
        new_token = _prompt_and_save_token(provider, repo_display, env_var)

        # Validate the newly provided token
        click.secho(__("🔍 Validating new token..."), fg="cyan", dim=True)
        fresh_provider = provider.with_token(new_token)
        try:
            fresh_provider.test_connection()
            click.secho(_valid_token_message(provider), fg="green")
            return new_token, fresh_provider
        except ScmProviderError as e:
            error_msg = _error_message(e, github_flow, label)
            # New token is also invalid — remove it and try again
            click.secho(
                __(
                    "⚠️ The provided token is also invalid: {error_msg}",
                    error_msg=error_msg,
                ),
                fg="yellow",
            )
            if e.http_status != 401:
                click.secho(f"❌ {error_msg}", fg="red")
                return None, provider
            _remove_expired_token(env_var)
            token = None

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
    return None, provider
