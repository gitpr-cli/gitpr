"""SCM provider factory: registry + resolution + remote-URL detection.

resolve_scm_provider is the single entry point for flows that need a forge
client (PR publishing, issues). Configuration comes from a plain dict with the
keys documented in the glossary:
  provider  — "github" (default), "gitlab", "bitbucket", "azure_devops"
  token     — raw credential; for "github" falls back to the legacy
              GITHUB_TOKEN_* (via src.config.get_github_token, imported lazily
              to keep the factory cycle-free)
  base_url  — optional API base (self-managed / enterprise)
  organization/project/username — provider extras, passed through as kwargs
"""

from src.i18n import __
from src.infrastructure.scm.azure_devops_provider import AzureDevOpsProvider
from src.infrastructure.scm.base import ScmProvider
from src.infrastructure.scm.bitbucket_provider import BitbucketProvider
from src.infrastructure.scm.github_provider import GitHubProvider
from src.infrastructure.scm.gitlab_provider import GitLabProvider

# Full registry since Etapa 7 (github+gitlab land in Etapa 4, azure_devops in
# Etapa 6, bitbucket in Etapa 7). Detection does not depend on this list —
# only resolution does.
_REGISTRY: dict[str, type[ScmProvider]] = {
    "github": GitHubProvider,
    "gitlab": GitLabProvider,
    "bitbucket": BitbucketProvider,
    "azure_devops": AzureDevOpsProvider,
}

# Extra keys recognized from the config dict and forwarded as provider kwargs
# (validated fail-fast by each provider's __init__).
_EXTRA_KEYS = ("organization", "project", "username")


def _valid_providers() -> str:
    return ", ".join(sorted(_REGISTRY))


def resolve_scm_provider(config: dict) -> ScmProvider:
    """Build a ScmProvider from a flat config dict (see module docstring)."""
    provider_key = (config.get("provider") or "github").strip().lower()
    cls = _REGISTRY.get(provider_key)
    if cls is None:
        raise ValueError(
            __(
                "Unknown SCM provider: {provider}. Valid providers: {providers}",
                provider=provider_key,
                providers=_valid_providers(),
            )
        )
    token = config.get("token") or ""
    if not token and provider_key == "github":
        # Legacy fallback: GitHub without SCM config keeps using the existing
        # GITHUB_TOKEN_ENCRYPTED (zero-migration path). Imported lazily so this
        # module stays free of config dependencies at import time.
        from src.config import get_github_token

        token = get_github_token()
    kwargs = {key: config[key] for key in _EXTRA_KEYS if config.get(key)}
    return cls(token=token, base_url=config.get("base_url"), **kwargs)


def detect_provider_from_remote(remote_url: str) -> str:
    """Guess the forge from a git remote URL (case-insensitive substrings).

    Order matters only for URLs that match several hosts — none exist today.
    Anything unknown defaults to "github" (the current GitPR behavior).
    """
    url = (remote_url or "").lower()
    if "gitlab" in url:
        return "gitlab"
    if "bitbucket" in url:
        return "bitbucket"
    if "dev.azure.com" in url or "visualstudio.com" in url:
        return "azure_devops"
    return "github"


# Human display names used when messages interpolate "{provider}".
_DISPLAY_NAMES = {
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "azure_devops": "Azure DevOps",
}


def provider_display_name(provider) -> str:
    """Human-readable forge name for a provider instance or key."""
    key = getattr(provider, "name", None) or str(provider).lower()
    return _DISPLAY_NAMES.get(key, key.title())


def provider_is_github(provider) -> bool:
    """True for GitHub flows (they reuse the legacy verbatim i18n texts)."""
    return (getattr(provider, "name", None) or "github") == "github"
