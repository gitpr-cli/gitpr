"""Resolve which forge a repository uses, and which credential belongs to it.

This module answers one question — "for this repository, which forge and which
token?" — and is the only place that answers it. ADR-016.

Resolution order (a project override always wins):

    .gitpr/conf/gitpr.config.yml (scm.provider)
      -> forge detected from the ``origin`` remote
      -> github

Credentials are stored per forge in ``~/.gitpr/.env``:

    GITHUB_TOKEN_ENCRYPTED / GITLAB_TOKEN_ENCRYPTED /
    BITBUCKET_TOKEN_ENCRYPTED / AZURE_DEVOPS_TOKEN_ENCRYPTED

The raw ``GITPR_SCM_TOKEN`` is the single CI/CD override and is tried first for
every forge. ``GITPR_SCM_ORGANIZATION``/``GITPR_SCM_PROJECT``/
``GITPR_SCM_USERNAME`` stay global because each one is read by exactly one
provider.

Why a separate module and not ``src/config.py``: resolving the forge needs the
repository (a git command and a YAML file at its root), while ``config.py`` is
the machine-wide dotenv layer and must not depend on either. The factory keeps
its own rule of reading no environment variables at all.
"""

import os
import subprocess
import threading
from dataclasses import dataclass
from typing import Optional

from src import config as config_module
from src.i18n import __
from src.infrastructure.scm.factory import (
    detect_provider_from_remote,
    provider_display_name,
)
from src.project_config import read_project_config
from src.security import decrypt_data

RAW_TOKEN_KEY = "GITPR_SCM_TOKEN"

TOKEN_KEYS = {
    "github": "GITHUB_TOKEN_ENCRYPTED",
    "gitlab": "GITLAB_TOKEN_ENCRYPTED",
    "bitbucket": "BITBUCKET_TOKEN_ENCRYPTED",
    "azure_devops": "AZURE_DEVOPS_TOKEN_ENCRYPTED",
}

BASE_URL_KEYS = {
    "github": "GITHUB_BASE_URL",
    "gitlab": "GITLAB_BASE_URL",
    "bitbucket": "BITBUCKET_BASE_URL",
    "azure_devops": "AZURE_DEVOPS_BASE_URL",
}

EXTRA_ENV_KEYS = {
    "organization": "GITPR_SCM_ORGANIZATION",
    "project": "GITPR_SCM_PROJECT",
    "username": "GITPR_SCM_USERNAME",
}

LEGACY_PROVIDER_KEY = "GITPR_SCM_PROVIDER"
LEGACY_TOKEN_KEY = "GITPR_SCM_TOKEN_ENCRYPTED"
LEGACY_BASE_URL_KEY = "GITPR_SCM_BASE_URL"

_LEGACY_KEYS = (LEGACY_PROVIDER_KEY, LEGACY_TOKEN_KEY, LEGACY_BASE_URL_KEY)

SOURCE_PROJECT = "project"
SOURCE_REMOTE = "remote"
SOURCE_DEFAULT = "default"

TOKEN_SOURCE_RAW = "raw"
TOKEN_SOURCE_STORED = "stored"

DEFAULT_PROVIDER = "github"


@dataclass(frozen=True)
class ProviderChoice:
    """The forge chosen for a repository, and why."""

    key: str
    source: str
    configured: str = ""
    ignored: str = ""


@dataclass(frozen=True)
class MigrationResult:
    """Outcome of the one-shot move from the legacy global SCM keys."""

    ran: bool = False
    migrated: bool = False
    provider: str = ""
    persisted: bool = True
    warning: str = ""


@dataclass(frozen=True)
class ScmSettings:
    """Everything the factory needs, already scoped to one repository."""

    provider: str
    source: str
    configured_provider: str
    token: str
    token_source: str
    base_url: Optional[str]
    organization: str = ""
    project: str = ""
    username: str = ""
    remote_url: Optional[str] = None
    warnings: tuple = ()


def origin_remote_url(start_dir=None) -> Optional[str]:
    """The ``origin`` remote URL verbatim, or None. Never raises.

    Deliberately not ``core.get_origin_remote_url``: importing core pulls the
    AI stack, and this module must stay importable from the configuration
    screen and from the MCP server.
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=start_dir,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def resolve_provider_choice(project_value, remote_url) -> ProviderChoice:
    """Apply the precedence: project override, then detection, then GitHub.

    A project value that is not a known forge key is ignored (never fatal) and
    reported through ``ignored`` so the caller can warn. A malformed project
    file must never stop every command from running.
    """
    value = (project_value or "").strip().lower()
    if value in TOKEN_KEYS:
        return ProviderChoice(value, SOURCE_PROJECT, configured=value)

    detected = detect_provider_from_remote(remote_url, default=None)
    if detected:
        return ProviderChoice(detected, SOURCE_REMOTE, configured=value, ignored=value)
    return ProviderChoice(
        DEFAULT_PROVIDER, SOURCE_DEFAULT, configured=value, ignored=value
    )


def provider_token(provider: str) -> str:
    """Decrypted token for *provider*, or "". The raw CI token wins.

    There is no fallback between forges: a GitLab token never answers for a
    GitHub repository.
    """
    _ensure_migrated()
    return _token_for(provider)


def provider_base_url(provider: str) -> Optional[str]:
    """The configured API base for *provider*, or None for its own default."""
    _ensure_migrated()
    return _base_url_for(provider)


def provider_extras() -> dict:
    """Global provider extras (organization/project/username) that are set."""
    _ensure_migrated()
    return {
        name: value
        for name, value in (
            (name, os.getenv(env_key) or "")
            for name, env_key in EXTRA_ENV_KEYS.items()
        )
        if value
    }


def _load_env():
    config_module.load_dotenv(config_module.ENV_FILE)


def _token_for(provider: str) -> str:
    _load_env()
    raw_token = os.getenv(RAW_TOKEN_KEY)
    if raw_token:
        return raw_token
    encrypted = os.getenv(TOKEN_KEYS.get(provider, ""), "")
    return decrypt_data(encrypted) if encrypted else ""


def _base_url_for(provider: str) -> Optional[str]:
    _load_env()
    return os.getenv(BASE_URL_KEYS.get(provider, "")) or None


_MIGRATION_LOCK = threading.Lock()
_MIGRATION_STATE = {"done": False, "result": None}


def _ensure_migrated() -> MigrationResult:
    return migrate_legacy_scm_config()


def migrate_legacy_scm_config() -> MigrationResult:
    """Move the legacy global SCM keys to their per-forge slots, once.

    The move is idempotent (it only acts while the legacy keys exist),
    never overwrites a per-forge value already configured, and never breaks
    the command when ``~/.gitpr/.env`` cannot be written: the migrated value
    is still materialised into this process, and the next run retries.
    """
    with _MIGRATION_LOCK:
        if _MIGRATION_STATE["done"]:
            return _MIGRATION_STATE["result"]
        try:
            result = _migrate_legacy_scm_config()
        except Exception as exc:  # a configuration move must never crash a run
            result = MigrationResult(ran=True, persisted=False, warning=str(exc))
        _MIGRATION_STATE["done"] = True
        _MIGRATION_STATE["result"] = result
        return result


def _migrate_legacy_scm_config() -> MigrationResult:
    _load_env()
    file_values = config_module.read_env_file_values()

    legacy_provider = (os.getenv(LEGACY_PROVIDER_KEY) or "").strip().lower()
    legacy_token = os.getenv(LEGACY_TOKEN_KEY) or ""
    legacy_base_url = os.getenv(LEGACY_BASE_URL_KEY) or ""

    if not legacy_provider and not legacy_token:
        # Only seeded empty lines (and maybe a stale base URL) remain.
        try:
            persisted = _remove_legacy_lines(file_values)
        except (OSError, PermissionError) as exc:
            return MigrationResult(
                ran=True,
                persisted=False,
                warning=__(
                    "The legacy SCM configuration could not be removed from {path}: {error}",
                    path=config_module.ENV_FILE,
                    error=str(exc),
                ),
            )
        return MigrationResult(ran=True, persisted=persisted)

    if not legacy_provider:
        if legacy_token:
            # A token with no recorded forge: guessing would send it to the
            # wrong host. Leave everything alone and point at the wizard.
            return MigrationResult(
                ran=True,
                persisted=True,
                warning=__(
                    "A legacy SCM token was found without GITPR_SCM_PROVIDER. "
                    "Run 'gitpr --init' in each repository to store it for the right forge."
                ),
            )
        # Only seeded empty lines (and maybe a stale base URL) remain.
        persisted = _remove_legacy_lines(file_values)
        return MigrationResult(ran=True, persisted=persisted)

    if legacy_provider not in TOKEN_KEYS:
        return MigrationResult(
            ran=True,
            warning=__(
                "Unknown legacy SCM provider '{provider}'; nothing was migrated. "
                "Run 'gitpr --init' to configure the forge of this repository.",
                provider=legacy_provider,
            ),
        )

    token_key = TOKEN_KEYS[legacy_provider]
    base_url_key = BASE_URL_KEYS[legacy_provider]

    writes = {}
    source_keys = {}
    if legacy_token and not (os.getenv(token_key) or ""):
        writes[token_key] = legacy_token
        source_keys[token_key] = LEGACY_TOKEN_KEY
    if legacy_base_url and not (os.getenv(base_url_key) or ""):
        writes[base_url_key] = legacy_base_url
        source_keys[base_url_key] = LEGACY_BASE_URL_KEY

    # Only values that live in the file belong in the file; a CI-injected
    # legacy token keeps working for this process alone.
    persisted = True
    warning = ""
    to_persist = {
        key: value
        for key, value in writes.items()
        if source_keys[key] in file_values
    }
    try:
        if to_persist:
            config_module.save_config_values(to_persist)
        _remove_legacy_lines(file_values)
    except (OSError, PermissionError) as exc:
        persisted = False
        warning = __(
            "The legacy SCM configuration could not be migrated in {path}: {error}",
            path=config_module.ENV_FILE,
            error=str(exc),
        )

    # Materialise the result for this process even when the write failed: no
    # reader below ever looks at the legacy keys again.
    for key, value in writes.items():
        os.environ[key] = value
    for key in _LEGACY_KEYS:
        os.environ.pop(key, None)

    if not warning and legacy_provider != DEFAULT_PROVIDER:
        warning = __(
            "The legacy {provider} token was migrated to {target}. Repositories whose "
            "remote does not name the forge must run 'gitpr --init' once.",
            provider=provider_display_name(legacy_provider),
            target=token_key,
        )

    return MigrationResult(
        ran=True,
        migrated=bool(writes),
        provider=legacy_provider,
        persisted=persisted,
        warning=warning,
    )


def _remove_legacy_lines(file_values) -> bool:
    """Delete the legacy keys that are actually written in the .env file."""
    removed = False
    for key in _LEGACY_KEYS:
        if key in file_values:
            removed = config_module.remove_config_value(key) or removed
    return removed


def _project_warning(project) -> str:
    return __(
        "⚠️ Ignoring project configuration at {path}: {error}",
        path=project.path,
        error=project.error,
    )


def _ignored_provider_warning(choice) -> str:
    return __(
        "⚠️ Unknown forge '{value}' in the project configuration; using {provider}.",
        value=choice.ignored,
        provider=provider_display_name(choice.key),
    )


def resolve_scm_settings(
    start_dir=None, remote_url=None, config_path=None, warnings=None
) -> ScmSettings:
    """Resolve provider, credential, base URL and extras for this repository.

    ``warnings`` is an optional list; every user-facing caveat (a malformed
    project file, an unknown forge override, a migration that could not be
    persisted) is appended to it so console flows can print them while MCP and
    JSON callers silently drop them.
    """
    collected = []

    migration = _ensure_migrated()
    if migration.warning:
        collected.append(migration.warning)

    remote = remote_url if remote_url is not None else origin_remote_url(start_dir)
    project_file = read_project_config(path=config_path, start_dir=start_dir)
    if project_file.error:
        collected.append(_project_warning(project_file))

    choice = resolve_provider_choice(project_file.provider, remote)
    if choice.ignored:
        collected.append(_ignored_provider_warning(choice))

    token = _token_for(choice.key)
    if os.getenv(RAW_TOKEN_KEY):
        token_source = TOKEN_SOURCE_RAW
    else:
        token_source = TOKEN_SOURCE_STORED if token else ""

    extras = {
        name: os.getenv(env_key) or ""
        for name, env_key in EXTRA_ENV_KEYS.items()
    }

    if warnings is not None:
        warnings.extend(collected)

    return ScmSettings(
        provider=choice.key,
        source=choice.source,
        configured_provider=choice.configured,
        token=token,
        token_source=token_source,
        base_url=_base_url_for(choice.key),
        organization=extras["organization"],
        project=extras["project"],
        username=extras["username"],
        remote_url=remote,
        warnings=tuple(collected),
    )


def get_scm_settings(
    start_dir=None, remote_url=None, config_path=None, warnings=None
) -> dict:
    """Flat dict consumed by ``resolve_scm_provider`` (empty values dropped)."""
    settings = resolve_scm_settings(
        start_dir=start_dir,
        remote_url=remote_url,
        config_path=config_path,
        warnings=warnings,
    )
    flat = {
        "provider": settings.provider,
        "token": settings.token,
        "base_url": settings.base_url,
        "organization": settings.organization,
        "project": settings.project,
        "username": settings.username,
    }
    return {key: value for key, value in flat.items() if value}
