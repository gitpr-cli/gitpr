import os
import sys
import socket
import shutil
import tempfile
import click
import yaml
from pathlib import Path
from dotenv import dotenv_values, load_dotenv, set_key, unset_key
from src.security import encrypt_data, decrypt_data, get_or_create_key
from src.i18n import __

# Path to the global .env file in the user's home folder (e.g.: ~/.gitpr/.env)
ENV_FILE = os.path.join(os.path.expanduser("~"), ".gitpr", ".env")

# Default configuration dictionary to ensure .env is always complete
DEFAULT_CONFIG = {
    "DEFAULT_AI_PROVIDER": "gemini",
    "GEMINI_API_MODEL_PRIMARY": "gemini-pro-latest",
    "GEMINI_API_MODEL_SECONDARY": "gemini-flash-lite-latest",
    "DEEPSEEK_API_MODEL_PRIMARY": "deepseek-v4-pro",
    "DEEPSEEK_API_MODEL_SECONDARY": "deepseek-v4-flash",
    "OLLAMA_API_MODEL_PRIMARY": "llama3",
    "OLLAMA_API_MODEL_SECONDARY": "llama3",
    "OUTPUT_FILE_NAME": "{branch}_{datetime}_PR_DESC.md",
    "OUTPUT_FILE_NAME_REVIEW": "{branch}_{datetime}_PR_REVIEW.txt",
    "OUTPUT_FILE_NAME_FULLREVIEW": "{branch}_{datetime}_PR_FULLREVIEW.txt",
    "OUTPUT_FILE_NAME_FILEREVIEW": "{branch}_{datetime}_FILE_REVIEW.txt",
    "OUTPUT_FILE_NAME_BLAME": "{branch}_{datetime}_BLAME_REPORT.md",
    "OUTPUT_FILE_NAME_ISSUE": "{branch}_{datetime}_ISSUE.md",
    "PR_DEFAULT_BASE": "",
    "GITPR_AUTO_COMMIT": "false",
    "GITPR_SKIP_LINT": "false",
    "GITPR_AUTO_STAGE": "false",
    "GITPR_SHOW_LOGS": "true",
    "GITPR_SKIP_UNSTAGED_CHECK": "false",
    "PR_PUBLISH_LOG": "true",
    # Reviewer suggestion (default PR flow): default ON, opt-out via --no-suggest-reviewers
    # or GITPR_SUGGEST_REVIEWERS=false. EXCLUDED is a CSV of names/emails.
    "GITPR_SUGGEST_REVIEWERS": "true",
    "GITPR_REVIEWER_SUGGESTION_TOP_N": "3",
    "GITPR_REVIEWER_SUGGESTION_EXCLUDED": "",
    "GITPR_AUTO_MERGE": "false",
    "OUTPUT_FILE_NAME_LINTER": "{branch}_{datetime}_LINTER.md",
    "OUTPUT_FILE_NAME_RELEASE": "{branch}_{datetime}_RELEASE.md",
    "GITPR_AI_TIMEOUT": "180",
    "GITPR_LINTER_TIMEOUT": "120",
    # Multi-forge SCM configuration (GitHub/GitLab/Bitbucket/Azure DevOps).
    # Empty values mean "not configured" — resolution falls back to github
    # with the legacy GITHUB_TOKEN_* store (see infrastructure/scm/factory.py).
    "GITPR_SCM_PROVIDER": "",
    "GITPR_SCM_TOKEN": "",
    "GITPR_SCM_TOKEN_ENCRYPTED": "",
    "GITPR_SCM_BASE_URL": "",
    "GITPR_SCM_ORGANIZATION": "",
    "GITPR_SCM_PROJECT": "",
    "GITPR_SCM_USERNAME": "",
    # Release/changelog feature (gitpr release). The changelog path is resolved
    # against the repository root when relative.
    "GITPR_RELEASE_CHANGELOG_PATH": "CHANGELOG.md",
    "GITPR_RELEASE_AI_SUMMARY": "true",
    "GITPR_RELEASE_AUTO_BUMP": "true",
    "GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT": "true",
}

# Fallbacks used when the .env value is missing or not a positive number.
_DEFAULT_AI_TIMEOUT = 180.0
_DEFAULT_LINTER_TIMEOUT = 120.0


def get_skill_dir():
    """Returns the absolute path to the project's skill folder (.gitpr/skill)."""
    return os.path.join(os.getcwd(), ".gitpr", "skill")


def resolve_skill_path(filename):
    """
    Resolves the path of a skill/config file (e.g.: .gitpr.commit.md).

    The canonical location is the '.gitpr/skill/' folder inside the project.
    For backward compatibility, if the file still lives in the project root,
    it is transparently migrated (moved) into '.gitpr/skill/'.

    Always returns the path inside '.gitpr/skill/' (whether the file exists or
    not), unless a migration failed — in that case it falls back to the legacy
    root path so the tool keeps working.
    """
    skill_dir = get_skill_dir()
    target_path = os.path.join(skill_dir, filename)
    legacy_path = os.path.join(os.getcwd(), filename)

    # Migrate a legacy root file into the skill folder (only if not already there)
    if os.path.exists(legacy_path) and not os.path.exists(target_path):
        try:
            os.makedirs(skill_dir, exist_ok=True)
            shutil.move(legacy_path, target_path)
            click.secho(
                __(
                    "📦 Skill file {filename} moved to .gitpr/skill/", filename=filename
                ),
                fg="cyan",
                dim=True,
            )
        except Exception as e:
            # If moving fails, fall back to the legacy location so the tool keeps working
            click.secho(
                __(
                    "⚠️ Warning: Could not move {filename} to .gitpr/skill/ ({error})",
                    filename=filename,
                    error=str(e),
                ),
                fg="yellow",
            )
            return legacy_path

    return target_path


# The skills GitPR loads, mapped to the file each one is read from inside
# .gitpr/skill/. This is the fixed set the whole tool agrees on: the commands
# load them through get_skill_context(), and the configuration screen lists and
# edits exactly these. A file in the folder that is not listed here is not a
# skill and is never offered for editing — .gitpr.linter.yml is the standing
# example (it is a rule catalogue, not an AI persona). The order is the order
# the screen shows.
SKILL_FILES_BY_TYPE = {
    "commit": ".gitpr.commit.md",
    "pr": ".gitpr.pr.md",
    "review": ".gitpr.review.md",
    "filereview": ".gitpr.filereview.md",
    "issue": ".gitpr.issue.md",
    "blame": ".gitpr.blame.md",
    "release": ".gitpr.release.md",
}
SKILL_TYPES = tuple(SKILL_FILES_BY_TYPE)

# get_skill_context() answers any other action with the review skill, so
# "fullreview" and an unknown type both read .gitpr.review.md.
DEFAULT_SKILL_TYPE = "review"


def skill_file_for(action_type):
    """The skill file an action reads, falling back to the review skill."""
    return SKILL_FILES_BY_TYPE.get(
        action_type, SKILL_FILES_BY_TYPE[DEFAULT_SKILL_TYPE]
    )


def skill_file_path(skill_type):
    """Absolute path of a skill file inside .gitpr/skill/.

    Deliberately not resolve_skill_path(): that one MOVES a legacy root file
    into the folder and prints about it, and a screen that lists the folder must
    not move files behind the user's back while drawing itself.
    """
    return os.path.join(get_skill_dir(), SKILL_FILES_BY_TYPE[skill_type])


def skill_template_remote_name(local_name):
    """The published template name of *local_name* for the session language.

    English ships without a suffix; every other language is a variant of the
    same base name (gitpr.pr.md -> gitpr.pr.pt_br.md). A language with no
    published edition keeps the suffixed name and simply is not there — the same
    outcome as ``gitpr --skill`` in that language.
    """
    # Read lazily: i18n.set_language() rebinds the module global, so a top-level
    # import would freeze the language the process started with.
    from src.i18n import CURRENT_LANG

    suffix = "" if CURRENT_LANG.startswith("en") else f".{CURRENT_LANG}"
    base, extension = os.path.splitext(local_name)
    return f"gitpr{base[len('.gitpr'):]}{suffix}{extension}"


def skill_file_status(skill_type):
    """Says whether a skill file can be edited, and why not when it cannot.

    Returns ``(state, detail)``, where *state* is "editable", "missing" (the
    project has no such file yet), "readonly" (the file is there but cannot be
    written) or "unreadable". *detail* carries the path or the reason for the
    screen to show, and is "" when there is nothing to report.

    This is what decides what the screen offers. It is not proof that a write
    will succeed — only the write is — so the caller still guards it.
    """
    path = skill_file_path(skill_type)
    if not os.path.exists(path):
        folder = get_skill_dir()
        if os.path.isdir(folder) and not os.access(folder, os.W_OK):
            # Not even a download could be written there; name the folder.
            return "missing", folder
        return "missing", ""
    if not os.access(path, os.R_OK):
        return "unreadable", path
    if not os.access(path, os.W_OK):
        return "readonly", path
    return "editable", ""


def read_skill_file(path):
    """Reads a skill file as text.

    Text mode turns CRLF into LF, which is what a text editor wants; the
    separator is recovered on write so the file is not rewritten wholesale.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _skill_line_ending(path):
    """The separator the file on disk already uses ("\\r\\n" or "\\n")."""
    try:
        with open(path, "rb") as handle:
            return "\r\n" if b"\r\n" in handle.read(8192) else "\n"
    except OSError:
        return "\n"


def write_skill_file(path, text):
    """Writes *text* back to a skill file, keeping its line endings.

    Two details that matter more than they look. The separator is read from the
    file BEFORE it is replaced: the skill files in the wild are a mix of CRLF
    and LF, and letting the platform decide would rewrite every line of half of
    them. And the write is atomic (a temp file in the same folder, then
    os.replace), the same guarantee save_config_values() gives the .env — a
    crash halfway through would otherwise leave a truncated persona behind,
    failing silently in every later command.
    """
    newline = _skill_line_ending(path)
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        errors="replace",
        newline=newline,
        dir=folder,
        prefix=".gitpr-skill-",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(text)
        os.replace(handle.name, path)
    except Exception:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise


def get_ai_provider():
    """Returns the configured default AI provider, or 'gemini' as fallback."""
    load_dotenv(ENV_FILE)
    return os.getenv("DEFAULT_AI_PROVIDER", "gemini").lower()


def _positive_float(raw, fallback):
    """Parses *raw* as a positive float, falling back on junk or non-positive values."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return fallback
    return value if value > 0 else fallback


def get_ai_timeout():
    """Returns the AI SDK request timeout in seconds (GITPR_AI_TIMEOUT, default 600).

    Bounds a single model call so a hung provider can never freeze the CLI
    indefinitely. Invalid or non-positive values fall back to the default.
    """
    load_dotenv(ENV_FILE)
    return _positive_float(os.getenv("GITPR_AI_TIMEOUT"), _DEFAULT_AI_TIMEOUT)


def get_linter_timeout():
    """Returns the external linter subprocess timeout in seconds (default 120)."""
    load_dotenv(ENV_FILE)
    return _positive_float(os.getenv("GITPR_LINTER_TIMEOUT"), _DEFAULT_LINTER_TIMEOUT)


def coauthor_enabled():
    """Returns True if the Gitpr-cli co-author trailer should be appended (default True).

    Read-only opt-out: set GITPR_COAUTHOR=false in ~/.gitpr/.env to disable.
    This variable is never auto-written to .env.
    """
    load_dotenv(ENV_FILE)
    return os.getenv("GITPR_COAUTHOR", "true").strip().lower() not in (
        "false",
        "0",
        "no",
        "off",
        "n",
    )


def suggest_reviewers_enabled():
    """Returns True when the default PR flow should compute reviewer suggestions.

    Read-only opt-out: set GITPR_SUGGEST_REVIEWERS=false in ~/.gitpr/.env (or
    pass --no-suggest-reviewers) to disable. Never auto-written to .env.
    """
    load_dotenv(ENV_FILE)
    return os.getenv("GITPR_SUGGEST_REVIEWERS", "true").strip().lower() not in (
        "false",
        "0",
        "no",
        "off",
        "n",
    )


def get_reviewer_suggestion_settings():
    """Returns the reviewer suggestion settings from ~/.gitpr/.env.

    ``top_n`` falls back to 3 when missing, invalid or non-positive;
    ``excluded`` parses the CSV of extra names/emails into a cleaned tuple.
    """
    load_dotenv(ENV_FILE)
    try:
        top_n = int((os.getenv("GITPR_REVIEWER_SUGGESTION_TOP_N") or "").strip() or 3)
        if top_n <= 0:
            raise ValueError
    except ValueError:
        top_n = 3
    excluded = tuple(
        item.strip()
        for item in (os.getenv("GITPR_REVIEWER_SUGGESTION_EXCLUDED") or "").split(",")
        if item.strip()
    )
    return {
        "enabled": suggest_reviewers_enabled(),
        "top_n": top_n,
        "excluded": excluded,
    }


def get_api_key(provider):
    """Reads and decrypts the API key corresponding to the chosen provider."""
    load_dotenv(ENV_FILE)

    # Suporte a CI/CD: Tenta ler a chave raw primeiro (ex: injetada via GitHub Secrets)
    raw_key = os.getenv(f"{provider.upper()}_API_KEY")
    if raw_key:
        return raw_key

    if provider == "gemini":
        encrypted_key = os.getenv("GEMINI_API_KEY_ENCRYPTED")
    elif provider == "deepseek":
        encrypted_key = os.getenv("DEEPSEEK_API_KEY_ENCRYPTED")
    elif provider == "ollama":
        return "ollama-local"  # Olama does not require authentication!
    else:
        return None

    if encrypted_key:
        return decrypt_data(encrypted_key)
    return None


def get_api_model(provider, task_complexity="advanced"):
    """
    Returns the AI model based on the provider and task complexity.
    'simple' uses secondary models (Flash/Lite) - cheaper.
    'advanced' uses primary models (Pro) - more robust.
    """
    load_dotenv(ENV_FILE)

    suffix = "PRIMARY" if task_complexity == "advanced" else "SECONDARY"
    env_var = f"{provider.upper()}_API_MODEL_{suffix}"

    # Fetch from .env, otherwise use the default dictionary value
    return os.getenv(env_var, DEFAULT_CONFIG.get(env_var))


def setup_environment():
    """Ensures that encryption keys, the default provider, and the API key are configured."""
    # Ensure the global folder exists
    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)

    # Create global plugin directories
    os.makedirs(
        os.path.join(os.path.dirname(ENV_FILE), "plugins", "linter"), exist_ok=True
    )
    os.makedirs(
        os.path.join(os.path.dirname(ENV_FILE), "plugins", "prompts"), exist_ok=True
    )

    # Call the existing function in security.py to ensure the master key exists
    get_or_create_key()

    load_dotenv(ENV_FILE)

    # Auto-fill missing variables with default values
    changes_made = False
    for key, value in DEFAULT_CONFIG.items():
        if os.getenv(key) is None:
            set_key(ENV_FILE, key, value)
            changes_made = True

    if changes_made:
        load_dotenv(ENV_FILE)  # Reload to ensure the new defaults are live

    # Ask for the default provider if none exists
    provider = os.getenv("DEFAULT_AI_PROVIDER")
    if not provider:
        click.secho(
            __("🤖 Welcome to GitPR! Let's configure your AI engine."),
            fg="cyan",
            bold=True,
        )
        provider = click.prompt(
            __("Which artificial intelligence do you want to use as default?"),
            type=click.Choice(["gemini", "deepseek", "ollama"], case_sensitive=False),
            default="gemini",
        ).lower()
        set_key(ENV_FILE, "DEFAULT_AI_PROVIDER", provider)
        click.echo("")

    # Check if the chosen provider's key exists
    api_key = get_api_key(provider)
    if not api_key:
        # 🛡️ Escudo de CI/CD: Impede que o prompt trave a pipeline do GitHub Actions
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            click.secho(
                __(
                    "❌ Error: API Key not configured for provider '{provider}' in the CI/CD environment.",
                    provider=provider,
                ),
                fg="red",
            )
            click.secho(
                __(
                    "💡 Tip: Pass the key as an environment variable (e.g., GEMINI_API_KEY)."
                ),
                fg="yellow",
            )
            sys.exit(1)

        click.secho(
            __("🔑 API Key for {provider} not found.", provider=provider.capitalize()),
            fg="yellow",
        )
        raw_key = click.prompt(
            __("Paste your {provider} API key here", provider=provider.capitalize()),
            hide_input=True,
        )

        # Encrypt and save with the correct prefix
        encrypted_key = encrypt_data(raw_key.strip())
        env_var_name = f"{provider.upper()}_API_KEY_ENCRYPTED"

        set_key(ENV_FILE, env_var_name, encrypted_key)
        click.secho(__("✅ Key safely stored on disk (Encrypted)!"), fg="green")
        click.echo("")


def check_internet_connection(timeout=2):
    """Checks for internet connection by attempting to connect to a global DNS."""
    try:
        # Save the system's default timeout
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)

        # Connect and close the socket automatically using 'with'
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("8.8.8.8", 53))

        # CRITICAL: Restore the timeout to avoid breaking the Gemini API!
        socket.setdefaulttimeout(original_timeout)
        return True
    except socket.error:
        click.secho(__("\n❌ Error: No internet connection."), fg="red", bold=True)
        click.secho(
            __("GitPR needs network access to query the AI and check for updates."),
            fg="yellow",
        )
        click.secho(__("Check your connection and try again.\n"), fg="white")
        sys.exit(1)


def get_plugin_dir(plugin_type):
    """Returns the absolute path to the global plugin directory."""
    return os.path.join(os.path.dirname(ENV_FILE), "plugins", plugin_type)


def get_linter_plugins():
    """Returns a list of all global linter plugin .yml files."""
    linter_dir = get_plugin_dir("linter")
    if not os.path.exists(linter_dir):
        return []
    return [
        os.path.join(linter_dir, f)
        for f in os.listdir(linter_dir)
        if f.endswith((".yml", ".yaml"))
    ]


def get_prompt_plugins():
    """Returns a list of all global prompt plugin .md files."""
    prompt_dir = get_plugin_dir("prompts")
    if not os.path.exists(prompt_dir):
        return []
    return [
        os.path.join(prompt_dir, f) for f in os.listdir(prompt_dir) if f.endswith(".md")
    ]


def load_linter_rules():
    """
    Loads the static linter rules from the local project and global plugins.
    Returns a combined list of rules.
    """
    rules = []

    # 1. Load Local Project Rules
    local_path = resolve_skill_path(".gitpr.linter.yml")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "rules" in config:
                    rules.extend(config.get("rules", []))
        except yaml.YAMLError as e:
            click.secho(
                __(
                    "\n❌ Syntax error in local .gitpr.linter.yml file:\n{error}",
                    error=str(e),
                ),
                fg="red",
            )
        except Exception as e:
            click.secho(
                __(
                    "\n❌ Unexpected error reading local linter rules: {error}",
                    error=str(e),
                ),
                fg="red",
            )

    # 2. Load Global Plugin Rules
    for plugin_file in get_linter_plugins():
        try:
            with open(plugin_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "rules" in config:
                    rules.extend(config.get("rules", []))
        except Exception as e:
            # Silently skip malformed global plugins so we don't break the main flow
            click.secho(
                __(
                    "⚠️ Warning: Could not load linter plugin {file} ({error})",
                    file=os.path.basename(plugin_file),
                    error=str(e),
                ),
                fg="yellow",
            )

    return rules


def load_external_linters():
    """
    Loads external linter configurations (name, command, extensions)
    from the local project and global plugins.
    """
    external_linters = []

    # 1. Load Local Project External Linters
    local_path = resolve_skill_path(".gitpr.linter.yml")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                config = yaml.safe_load(f)
                if config and "external_linters" in config:
                    external_linters.extend(config.get("external_linters", []))
        except Exception:
            pass

    # 2. Load Global Plugin External Linters
    for plugin_file in get_linter_plugins():
        try:
            with open(plugin_file, "r", encoding="utf-8", errors="replace") as f:
                config = yaml.safe_load(f)
                if config and "external_linters" in config:
                    external_linters.extend(config.get("external_linters", []))
        except Exception:
            pass

    return external_linters


def get_github_token():
    """Reads and decrypts the GitHub Personal Access Token (PAT)."""
    load_dotenv(ENV_FILE)
    encrypted_token = os.getenv("GITHUB_TOKEN_ENCRYPTED")

    if encrypted_token:
        return decrypt_data(encrypted_token)
    return None


def get_scm_token():
    """Reads and decrypts the multi-forge SCM token (GitLab/Bitbucket/Azure…).

    Mirrors get_api_key's CI-friendly pattern: the raw GITPR_SCM_TOKEN env
    takes precedence (CI/CD injection), otherwise the Fernet-encrypted
    GITPR_SCM_TOKEN_ENCRYPTED is decrypted.
    """
    load_dotenv(ENV_FILE)

    raw_token = os.getenv("GITPR_SCM_TOKEN")
    if raw_token:
        return raw_token

    encrypted_token = os.getenv("GITPR_SCM_TOKEN_ENCRYPTED")
    if encrypted_token:
        return decrypt_data(encrypted_token)
    return None


def get_scm_settings():
    """Returns the multi-forge SCM configuration as a flat dict.

    Empty values are omitted so resolve_scm_provider applies its defaults
    (provider "github", legacy GITHUB_TOKEN_* fallback for github without an
    SCM token — zero-migration path for existing users).
    """
    load_dotenv(ENV_FILE)
    settings = {
        "provider": os.getenv("GITPR_SCM_PROVIDER") or None,
        "token": get_scm_token(),
        "base_url": os.getenv("GITPR_SCM_BASE_URL") or None,
        "organization": os.getenv("GITPR_SCM_ORGANIZATION") or None,
        "project": os.getenv("GITPR_SCM_PROJECT") or None,
        "username": os.getenv("GITPR_SCM_USERNAME") or None,
    }
    return {key: value for key, value in settings.items() if value}


def get_scm_provider():
    """Returns the configured SCM provider key, or None when not configured."""
    load_dotenv(ENV_FILE)
    return os.getenv("GITPR_SCM_PROVIDER") or None


def _env_bool_default_true(key):
    """Parses a GITPR_* boolean that defaults to True when unset or invalid."""
    load_dotenv(ENV_FILE)
    return os.getenv(key, "true").strip().lower() not in (
        "false",
        "0",
        "no",
        "off",
        "n",
    )


def get_release_settings():
    """Returns the gitpr release configuration as a flat dict.

    ``changelog_path`` may be relative (resolved against the repository root
    by the release engine) or absolute; the booleans follow the project's
    "false disables" convention (any other value means True).
    """
    load_dotenv(ENV_FILE)
    return {
        "changelog_path": os.getenv("GITPR_RELEASE_CHANGELOG_PATH", "CHANGELOG.md"),
        "ai_summary": _env_bool_default_true("GITPR_RELEASE_AI_SUMMARY"),
        "auto_bump": _env_bool_default_true("GITPR_RELEASE_AUTO_BUMP"),
        "publish_draft_by_default": _env_bool_default_true(
            "GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT"
        ),
    }


def validate_github_token(token):
    """
    Validates a GitHub PAT by making a lightweight API call to /user.
    Returns (is_valid: bool, error_message: str).
    """
    import requests

    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )

        if response.status_code == 200:
            return True, ""
        elif response.status_code == 401:
            return False, __("Token expired or invalid. Please generate a new one.")
        else:
            return False, __(
                "Unexpected response from GitHub (HTTP {code})",
                code=response.status_code,
            )
    except requests.exceptions.ConnectionError:
        return False, __("No internet connection. Cannot validate GitHub token.")
    except requests.exceptions.Timeout:
        return False, __("GitHub API timeout. Check your connection and try again.")
    except Exception as e:
        return False, __("Failed to validate token: {error}", error=str(e))


# ============================================================
# Configuration screen support (gitpr config)
# ============================================================
#
# Everything below backs src/ui/config_app.py. It is deliberately additive:
# the pre-existing writers (setup_environment, run_scm_init_wizard, the
# downloaders) keep calling set_key directly and are not migrated here.

# Failure kinds returned by validate_ai_key(). Only an authentication failure
# blocks the save; a network failure must not, otherwise a correct key typed
# behind a corporate proxy could never be stored.
VALIDATION_OK = ""
VALIDATION_AUTH = "auth"
VALIDATION_NETWORK = "network"

# A credential probe is a round trip, not a generation — do not reuse
# GITPR_AI_TIMEOUT (180s by default), which would freeze the screen.
_AI_KEY_VALIDATION_TIMEOUT = 10.0

_AUTH_STATUS_CODES = (401, 403)


def read_env_file_values():
    """Returns the raw contents of ~/.gitpr/.env as a dict.

    Unlike os.getenv(), this reads ONLY the file: load_dotenv() runs with
    override=False all over the project, so a process environment variable
    silently wins over the file. The configuration screen needs both views to
    tell the user when the environment is shadowing what they just edited.
    """
    if not os.path.exists(ENV_FILE):
        return {}
    return {
        key: value if value is not None else ""
        for key, value in dotenv_values(ENV_FILE, encoding="utf-8").items()
    }


def save_config_values(values):
    """Writes *values* into ~/.gitpr/.env, one key at a time.

    Secrets must already be encrypted by the caller (security.encrypt_data).
    dotenv.set_key preserves comments and the original key order, appends new
    keys at the end and swaps the file atomically (temp file + os.replace), so
    a crash mid-save cannot leave a truncated .env behind.
    """
    if not values:
        return
    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)
    for key, value in values.items():
        set_key(ENV_FILE, key, value, encoding="utf-8")


def remove_config_value(key):
    """Deletes *key* from ~/.gitpr/.env so the code fallback takes over again.

    Restoring a default means removing the line, not writing the default value
    back: an absent key and a key holding its default are indistinguishable to
    every getter, but only the absent one survives a change of default.

    Returns True when a line was actually removed.
    """
    if key not in read_env_file_values():
        return False
    removed, _ = unset_key(ENV_FILE, key, encoding="utf-8")
    return bool(removed)


def _exception_status_code(exc):
    """Best-effort HTTP status carried by a provider SDK exception."""
    for attribute in ("status_code", "code", "http_status"):
        value = getattr(exc, attribute, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def _is_auth_failure(exc):
    """True only when the provider clearly rejected the credential itself.

    Being wrong here is asymmetric: a false positive blocks a valid key, so an
    unrecognised error is reported as a network problem and the caller allows
    the save.
    """
    status = _exception_status_code(exc)
    text = str(exc).lower()
    if status in _AUTH_STATUS_CODES:
        return True
    if "unauthorized" in text or "invalid api key" in text:
        return True
    # Gemini answers HTTP 400 "API key not valid" for a malformed key.
    return status == 400 and "api key" in text


def validate_ai_key(provider, api_key):
    """Probes *api_key* against *provider* without generating any content.

    Returns (is_valid, failure_kind, error_message) where failure_kind is one
    of VALIDATION_OK / VALIDATION_AUTH / VALIDATION_NETWORK.

    The provider SDKs are called directly instead of going through
    call_ai_model(): that helper swallows every exception, retries three times
    with a two second pause and returns None, so an invalid key and a dead
    network would be indistinguishable ~6 seconds later.
    """
    provider = (provider or "").lower()

    # Ollama runs locally and needs no credential (config.get_api_key returns
    # the literal "ollama-local" for it).
    if provider == "ollama":
        return True, VALIDATION_OK, ""

    if not api_key:
        return False, VALIDATION_AUTH, __("No API key configured.")

    try:
        from src.ai_providers import _make_gemini_client, _make_openai_client

        if provider == "gemini":
            client = _make_gemini_client(api_key, _AI_KEY_VALIDATION_TIMEOUT)
            # Cheap listing call: no tokens are billed and a bad key fails here.
            for _ in client.models.list():
                break
        elif provider == "deepseek":
            client = _make_openai_client(
                api_key, provider, _AI_KEY_VALIDATION_TIMEOUT
            )
            client.models.list()
        else:
            # Unknown provider: nothing meaningful to probe.
            return True, VALIDATION_OK, ""
    except Exception as exc:
        if _is_auth_failure(exc):
            return False, VALIDATION_AUTH, __(
                "{provider} rejected the API key.", provider=provider
            )
        return False, VALIDATION_NETWORK, __(
            "Could not reach {provider}: {error}", provider=provider, error=str(exc)
        )

    return True, VALIDATION_OK, ""
