"""SCM provider abstraction: unified interface over Git hosting forges.

Public surface for consumers (main.py, the TUI apps, the wizard):
  - domain contract in base.py (ScmProvider ABC, dataclasses, errors)
  - concrete providers (github_provider.py, gitlab_provider.py,
    bitbucket_provider.py, azure_devops_provider.py)
  - factory.resolve_scm_provider / detect_provider_from_remote

Internal code must go through resolve_scm_provider and never import the
concrete provider modules directly.
"""

from src.infrastructure.scm.base import (
    IssueRequest,
    IssueResult,
    PullRequestRequest,
    PullRequestResult,
    RepoRef,
    ScmNotSupportedError,
    ScmProvider,
    ScmProviderError,
)
from src.infrastructure.scm.factory import (
    detect_provider_from_remote,
    provider_display_name,
    provider_is_github,
    resolve_scm_provider,
)
from src.infrastructure.scm.azure_devops_provider import AzureDevOpsProvider
from src.infrastructure.scm.bitbucket_provider import BitbucketProvider
from src.infrastructure.scm.github_provider import GitHubProvider
from src.infrastructure.scm.gitlab_provider import GitLabProvider

__all__ = [
    "IssueRequest",
    "IssueResult",
    "PullRequestRequest",
    "PullRequestResult",
    "RepoRef",
    "ScmNotSupportedError",
    "ScmProvider",
    "ScmProviderError",
    "detect_provider_from_remote",
    "provider_display_name",
    "provider_is_github",
    "resolve_scm_provider",
    "AzureDevOpsProvider",
    "BitbucketProvider",
    "GitHubProvider",
    "GitLabProvider",
]
