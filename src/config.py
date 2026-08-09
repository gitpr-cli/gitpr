import os
import sys
import socket
import shutil
import click
import yaml
from pathlib import Path
from dotenv import load_dotenv, set_key
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
    "GITPR_AUTO_MERGE": "false"
}

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
            click.secho(__("📦 Skill file {filename} moved to .gitpr/skill/", filename=filename), fg="cyan", dim=True)
        except Exception as e:
            # If moving fails, fall back to the legacy location so the tool keeps working
            click.secho(__("⚠️ Warning: Could not move {filename} to .gitpr/skill/ ({error})", filename=filename, error=str(e)), fg="yellow")
            return legacy_path

    return target_path


def get_ai_provider():
    """Returns the configured default AI provider, or 'gemini' as fallback."""
    load_dotenv(ENV_FILE)
    return os.getenv("DEFAULT_AI_PROVIDER", "gemini").lower()

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
        return "ollama-local" # Olama does not require authentication!
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
        click.secho(__("🤖 Welcome to GitPR! Let's configure your AI engine."), fg="cyan", bold=True)
        provider = click.prompt(
            __("Which artificial intelligence do you want to use as default?"),
            type=click.Choice(['gemini', 'deepseek', 'ollama'], case_sensitive=False),
            default='gemini'
        ).lower()
        set_key(ENV_FILE, "DEFAULT_AI_PROVIDER", provider)
        click.echo("")

    # Check if the chosen provider's key exists
    api_key = get_api_key(provider)
    if not api_key:
        # 🛡️ Escudo de CI/CD: Impede que o prompt trave a pipeline do GitHub Actions
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            click.secho(__("❌ Error: API Key not configured for provider '{provider}' in the CI/CD environment.", provider=provider), fg="red")
            click.secho(__("💡 Tip: Pass the key as an environment variable (e.g., GEMINI_API_KEY)."), fg="yellow")
            sys.exit(1)
            
        click.secho(__("🔑 API Key for {provider} not found.", provider=provider.capitalize()), fg="yellow")
        raw_key = click.prompt(__("Paste your {provider} API key here", provider=provider.capitalize()), hide_input=True)

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
        click.secho(__("GitPR needs network access to query the AI and check for updates."), fg="yellow")
        click.secho(__("Check your connection and try again.\n"), fg="white")
        sys.exit(1)
        

def load_linter_rules():
    """
    Loads the static linter rules from the .gitpr.linter.yml file.
    Returns a list of rules or an empty list if the file does not exist.
    """
    file_path = resolve_skill_path(".gitpr.linter.yml")

    # If the file does not exist in the project, it's not an error. There are simply no rules to apply.
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Return the list of rules or empty if the file is blank
        if not config or "rules" not in config:
            return []

        return config.get("rules", [])

    except yaml.YAMLError as e:
        # If the user makes an indentation or quote error, warn without crashing the terminal
        click.secho(__("\n❌ Syntax error in .gitpr.linter.yml file:\n{error}", error=str(e)), fg="red")
        return []
    except Exception as e:
        click.secho(__("\n❌ Unexpected error reading linter rules: {error}", error=str(e)), fg="red")
        return []

def get_github_token():
    """Reads and decrypts the GitHub Personal Access Token (PAT)."""
    load_dotenv(ENV_FILE)
    encrypted_token = os.getenv("GITHUB_TOKEN_ENCRYPTED")

    if encrypted_token:
        return decrypt_data(encrypted_token)
    return None


def validate_github_token(token):
    """
    Validates a GitHub PAT by making a lightweight API call to /user.
    Returns (is_valid: bool, error_message: str).
    """
    import requests

    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)

        if response.status_code == 200:
            return True, ""
        elif response.status_code == 401:
            return False, __("Token expired or invalid. Please generate a new one.")
        else:
            return False, __("Unexpected response from GitHub (HTTP {code})", code=response.status_code)
    except requests.exceptions.ConnectionError:
        return False, __("No internet connection. Cannot validate GitHub token.")
    except requests.exceptions.Timeout:
        return False, __("GitHub API timeout. Check your connection and try again.")
    except Exception as e:
        return False, __("Failed to validate token: {error}", error=str(e))