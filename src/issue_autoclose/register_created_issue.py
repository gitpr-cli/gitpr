"""Record the issue ``gitpr -is`` just created (T3, ADR-001, ADR-010).

The issue number is only known inside ``IssueApp`` right after the forge
answers; once the TUI closes, it is gone. This module is the single call that
turns that answer into the local record the pull request flow reads back.

A failure here is deliberately swallowed: the issue already exists on
the forge, so a local bookkeeping problem must never turn a successful
creation into an error for the user.
"""
from dataclasses import dataclass
from datetime import datetime

from src.issue_autoclose.issue_registry import (
    IssueRegistry,
    IssueRegistryError,
    RegisteredIssue,
)


@dataclass(frozen=True)
class RegistrationOutcome:
    """What happened, so the caller can report it without catching anything."""

    recorded: bool = False
    skipped_reason: str = ""
    gitignore_updated: bool = False
    error: str = ""


def register_created_issue(provider, repo_ref, result, title, branch, registry=None):
    """Records *result* as the issue the next pull request may close.

    Returns what happened instead of raising: "no-provider", "no-repo" and
    "invalid-result" are expected skips, "write-failed" is the one the caller
    turns into a one-line warning. *branch* is passed in by the TUI, which
    already knows it, and *registry* is injectable for tests.
    """
    if provider is None:
        return RegistrationOutcome(skipped_reason="no-provider")

    repo = str(getattr(repo_ref, "display", "") or "")
    if "/" not in repo:
        return RegistrationOutcome(skipped_reason="no-repo")

    number = getattr(result, "number", None)
    url = str(getattr(result, "url", "") or "")
    if (
        not isinstance(number, int)
        or isinstance(number, bool)
        or number <= 0
        or not url
    ):
        # A record this module would make unreadable for load() is worse than
        # no record at all: report the skip and leave the previous one intact.
        return RegistrationOutcome(skipped_reason="invalid-result")

    provider_name = str(getattr(provider, "name", "") or "github")

    issue = RegisteredIssue(
        repo=repo,
        number=number,
        title=str(title or ""),
        url=url,
        created_at=datetime.now().isoformat(timespec="seconds"),
        branch=branch,
        provider=provider_name,
    )
    registry = registry or IssueRegistry()

    try:
        written = registry.record(issue)
    except IssueRegistryError as exc:
        return RegistrationOutcome(skipped_reason="write-failed", error=str(exc))
    except Exception as exc:
        # Bookkeeping must never break the creation that already succeeded.
        return RegistrationOutcome(skipped_reason="write-failed", error=str(exc))

    return RegistrationOutcome(
        recorded=True, gitignore_updated=bool(written.gitignore_updated)
    )
