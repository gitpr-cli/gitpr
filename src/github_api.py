"""DEPRECATED thin shim over GitHubProvider (src/infrastructure/scm).

Kept so external integrations (plugins, user scripts) that import github_api
directly keep working. Every function delegates to GitHubProvider and returns
the legacy (ok, data, http_status) tuples. New code must use
factory.resolve_scm_provider() instead of this module.
"""

import warnings

from src.infrastructure.scm.base import (
    PullRequestRequest,
    RepoRef,
    ScmProviderError,
)
from src.infrastructure.scm.github_provider import (
    GitHubProvider,
    _extract_error_message,
)


def _deprecated(function_name):
    warnings.warn(
        f"github_api.{function_name} is deprecated, "
        "use ScmProvider via factory.resolve_scm_provider",
        DeprecationWarning,
        stacklevel=3,
    )


def _repo_ref(repo_info):
    """Legacy code passes the bare "owner/repo" string — rebuild a RepoRef."""
    if "/" in repo_info:
        workspace, name = repo_info.split("/", 1)
    else:
        workspace, name = "", repo_info
    return RepoRef(raw=repo_info, workspace=workspace, name=name, provider="github")


def create_pull_request(repo_info, github_token, title, body, head, base, timeout=30):
    """
    Creates a GitHub Pull Request via REST API (DEPRECATED — delegate).

    Returns (ok: bool, data: dict, http_status: int) exactly as the legacy
    implementation did.
    """
    _deprecated("create_pull_request")
    provider = GitHubProvider(token=github_token)
    req = PullRequestRequest(
        title=title, description=body, source_branch=head, target_branch=base
    )
    try:
        result = provider.create_pull_request(_repo_ref(repo_info), req, timeout=timeout)
        return True, {"url": result.url, "number": result.number}, 201
    except ScmProviderError as e:
        return False, {"message": e.message}, e.http_status


def check_existing_pr(repo_info, github_token, head_branch, timeout=15):
    """
    Check if there's already an open PR from *head_branch* to any base
    (DEPRECATED — delegate). Returns (exists, pr_url, pr_number) exactly as
    the legacy implementation did, degrading to (False, None, None) on any
    failure.
    """
    _deprecated("check_existing_pr")
    provider = GitHubProvider(token=github_token)
    try:
        result = provider.check_existing_pull_request(
            _repo_ref(repo_info), head_branch, timeout=timeout
        )
    except ScmProviderError:
        return False, None, None
    if result is None:
        return False, None, None
    return True, result.url, result.number


def update_pull_request(
    repo_info, github_token, pr_number, title=None, body=None, timeout=15
):
    """
    Update a pull request's title and/or body via GitHub REST API
    (DEPRECATED — delegate). Returns (ok, data, http_status) as legacy.
    """
    _deprecated("update_pull_request")
    provider = GitHubProvider(token=github_token)
    try:
        result = provider.update_pull_request(
            _repo_ref(repo_info),
            pr_number,
            title=title,
            description=body,
            timeout=timeout,
        )
        return True, {"url": result.url, "number": result.number}, 200
    except ScmProviderError as e:
        return False, {"message": e.message}, e.http_status


def merge_pull_request(repo_info, github_token, pr_number, timeout=15):
    """
    Merge a pull request via GitHub REST API (DEPRECATED — delegate).
    Returns (ok, data, http_status) as legacy.
    """
    _deprecated("merge_pull_request")
    provider = GitHubProvider(token=github_token)
    try:
        provider.merge_pull_request(_repo_ref(repo_info), pr_number, timeout=timeout)
        return True, {"merged": True, "message": ""}, 200
    except ScmProviderError as e:
        return False, {"message": e.message}, e.http_status
