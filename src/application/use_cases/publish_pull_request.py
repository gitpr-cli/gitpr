"""Use case: Publish a pull request directly to the configured SCM forge.

Shared by the CLI ``--no-edit`` flow and the MCP ``publish_pull_request`` tool.
Never commits or pushes; checks for existing PRs or unpushed branches when
requested, maps forge errors into structured outcomes, and applies defense-in-depth
secret masking on error messages.
"""

from dataclasses import dataclass
import subprocess
from typing import Optional

import src.domain.check.check_types  # noqa: F401 - avoid circular import through src.infrastructure.ci
from src.i18n import __
from src.infrastructure.ci.masking import mask_sensitive_text
from src.infrastructure.scm import (
    PullRequestRequest,
    PullRequestResult,
    RepoRef,
    ScmProvider,
    ScmProviderError,
    provider_display_name,
)


@dataclass
class PublishPrOutcome:
    """Structured result of a pull request publication attempt.

    status is one of:
    - "success"        : PR created on the forge (url and number populated)
    - "already_exists" : an open PR already exists for source_branch (url and number populated)
    - "needs_push"     : source_branch is not on origin or has unpushed commits
    - "auth_required"  : missing or invalid/expired SCM token (HTTP 401/403)
    - "error"          : any other validation or API error
    """

    status: str
    url: str = ""
    number: int = 0
    provider: str = ""
    source_branch: str = ""
    target_branch: str = ""
    http_status: int = 0
    message: str = ""


def format_recommended_commit_body(commit_message: str, pr_body: str) -> str:
    """Formats the full PR body with the recommended commit message header (used by --no-edit)."""
    return (
        __("**Recommended Commit Message:**\n")
        + "```text\n"
        + f"{commit_message}\n"
        + "```\n\n---\n\n"
        + pr_body
    )


def _branch_needs_push(source_branch: str, repo_path: Optional[str] = None) -> bool:
    """True when origin/<source_branch> does not exist or local HEAD is ahead of it."""
    if not source_branch or source_branch == "HEAD":
        return False
    remote_ref = f"refs/remotes/origin/{source_branch}"
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", remote_ref],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=repo_path or None,
        )
        if proc.returncode != 0:
            return True
        ahead = subprocess.run(
            ["git", "rev-list", "--count", f"origin/{source_branch}..HEAD"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=repo_path or None,
        )
        if ahead.returncode == 0:
            count = int((ahead.stdout or "0").strip() or "0")
            return count > 0
    except (OSError, ValueError):
        return False
    return False


def publish_pull_request_use_case(
    provider: ScmProvider,
    repo_ref: RepoRef,
    title: str,
    description: str,
    source_branch: str,
    target_branch: str,
    draft: bool = False,
    check_remote_state: bool = False,
    repo_path: Optional[str] = None,
) -> PublishPrOutcome:
    """Creates a pull request on *provider* and returns a structured PublishPrOutcome.

    When *check_remote_state* is True (MCP flow), verifies that a token is present,
    checks whether the branch needs to be pushed first, and checks whether an open
    PR already exists for *source_branch* before attempting creation.
    """
    label = provider_display_name(provider)
    clean_title = (title or "").strip()
    clean_body = (description or "").strip()

    if not clean_title:
        return PublishPrOutcome(
            status="error",
            provider=provider.name,
            source_branch=source_branch,
            target_branch=target_branch,
            message=__("Pull request title must not be empty."),
        )

    if not clean_body:
        return PublishPrOutcome(
            status="error",
            provider=provider.name,
            source_branch=source_branch,
            target_branch=target_branch,
            message=__("PR description must not be empty."),
        )

    if not getattr(provider, "token", ""):
        return PublishPrOutcome(
            status="auth_required",
            provider=provider.name,
            source_branch=source_branch,
            target_branch=target_branch,
            http_status=401,
            message=__(
                "{provider} token is not configured. Run 'gitpr' in a terminal to authenticate.",
                provider=label,
            ),
        )

    if check_remote_state:
        try:
            existing: Optional[PullRequestResult] = provider.check_existing_pull_request(
                repo_ref, source_branch
            )
        except ScmProviderError as exc:
            if exc.http_status in (401, 403):
                return PublishPrOutcome(
                    status="auth_required",
                    provider=provider.name,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    http_status=exc.http_status,
                    message=mask_sensitive_text(
                        __(
                            "{provider} token expired or invalid. Run 'gitpr' in a terminal to re-authenticate.",
                            provider=label,
                        )
                    ),
                )
            existing = None
        except Exception:
            existing = None

        if existing is not None:
            return PublishPrOutcome(
                status="already_exists",
                url=existing.url,
                number=existing.number,
                provider=provider.name,
                source_branch=source_branch,
                target_branch=existing.target_branch or target_branch,
                message=__(
                    "An open Pull Request already exists for branch '{branch}': {url}",
                    branch=source_branch,
                    url=existing.url,
                ),
            )

        if _branch_needs_push(source_branch, repo_path=repo_path):
            return PublishPrOutcome(
                status="needs_push",
                provider=provider.name,
                source_branch=source_branch,
                target_branch=target_branch,
                message=__(
                    "Branch '{branch}' has not been pushed to origin or has unpushed commits.",
                    branch=source_branch,
                ),
            )

    try:
        result = provider.create_pull_request(
            repo_ref,
            PullRequestRequest(
                title=clean_title,
                description=clean_body,
                source_branch=source_branch,
                target_branch=target_branch,
                draft=bool(draft),
            ),
        )
    except ScmProviderError as exc:
        masked_msg = mask_sensitive_text(exc.message)
        if exc.http_status == 401:
            return PublishPrOutcome(
                status="auth_required",
                provider=provider.name,
                source_branch=source_branch,
                target_branch=target_branch,
                http_status=exc.http_status,
                message=masked_msg,
            )
        lower_msg = masked_msg.lower()
        if exc.http_status in (400, 409, 422) and "already exists" in lower_msg:
            return PublishPrOutcome(
                status="already_exists",
                provider=provider.name,
                source_branch=source_branch,
                target_branch=target_branch,
                http_status=exc.http_status,
                message=masked_msg,
            )
        if exc.http_status in (400, 404, 422) and (
            "head" in lower_msg or "source" in lower_msg or "branch" in lower_msg
        ) and _branch_needs_push(source_branch, repo_path=repo_path):
            return PublishPrOutcome(
                status="needs_push",
                provider=provider.name,
                source_branch=source_branch,
                target_branch=target_branch,
                http_status=exc.http_status,
                message=masked_msg,
            )
        return PublishPrOutcome(
            status="error",
            provider=provider.name,
            source_branch=source_branch,
            target_branch=target_branch,
            http_status=exc.http_status,
            message=masked_msg,
        )
    except Exception as exc:
        return PublishPrOutcome(
            status="error",
            provider=provider.name,
            source_branch=source_branch,
            target_branch=target_branch,
            http_status=0,
            message=mask_sensitive_text(str(exc)),
        )

    return PublishPrOutcome(
        status="success",
        url=result.url,
        number=result.number,
        provider=provider.name,
        source_branch=source_branch,
        target_branch=target_branch,
        http_status=201,
        message=__(
            "PR successfully created on {provider}: {pr_url}",
            provider=label,
            pr_url=result.url,
        ),
    )
