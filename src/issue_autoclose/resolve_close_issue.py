"""The decision behind the automatic issue closure (ADR-003, ADR-005).

The PR flow calls :func:`resolve_close_issue` before the stage TUI: the local
record is read, the forge is asked whether the issue is still open, and the
user is offered one line in the pull request description. Nothing is printed
here — the question goes through the injected ``ask`` callable and everything
else comes back as data, so the command that owns the screen decides how to
report it.

What the caller must do with the result:

* ``CloseIssueOutcome.warning`` is a one-line message to print (the forge
  could not be verified or the record is unreadable). It is never set when a
  question was asked.
* ``CloseIssueDecision.target_branch_warning`` is already part of the question
  the user read; it is repeated on the decision only so the caller can keep it
  with the line, and must not be printed again.
* ``CloseIssueOutcome.skipped_reason`` is the vocabulary the ``issue_autoclose``
  metric reports; an empty string means a decision was made.
* A decision never clears the record — clearing once the pull request exists
  is the caller's job (ADR-007), because a failed publish must keep the record
  for the next run.

``ask`` is deliberately called outside every ``try`` block: ``click``'s Abort
is a ``RuntimeError``, and Ctrl+C must leave the flow exactly like any other
prompt instead of being swallowed as a skipped feature.
"""
from dataclasses import dataclass

from src.i18n import __
from src.infrastructure.scm.base import ScmProviderError
from src.infrastructure.scm.factory import provider_is_github


@dataclass(frozen=True)
class CloseIssueFlags:
    """The two mutually exclusive CLI flags (the CLI rejects both together)."""

    accept: bool = False  # --close-issue
    disabled: bool = False  # --no-close-issue


@dataclass(frozen=True)
class CloseIssueDecision:
    """The line the PR body must carry, and what the user was told."""

    number: int
    title: str
    line: str
    target_branch_warning: str = ""


@dataclass(frozen=True)
class CloseIssueOutcome:
    """What the PR flow gets back; every field is safe to ignore."""

    decision: CloseIssueDecision | None = None
    warning: str = ""
    skipped_reason: str = ""
    asked: bool = False
    accepted: bool = False


def resolve_close_issue(
    provider,
    registry,
    repo_ref,
    *,
    flags=None,
    enabled=True,
    is_tty=True,
    target_branch="",
    ask=None,
    timeout=5,
) -> CloseIssueOutcome:
    """Decides whether this pull request should close the recorded issue.

    Gates that cost nothing (flags, config, a non-GitHub forge) run before any
    disk or network access. The record is read once; only a still-open issue
    reaches the question, and only the question path fetches the default branch
    to warn about a merge that would not close the issue.

    ``enabled`` and ``timeout`` carry ``GITPR_ISSUE_AUTOCLOSE`` and
    ``GITPR_ISSUE_AUTOCLOSE_TIMEOUT``; the caller wires them.
    """
    flags = flags if flags is not None else CloseIssueFlags()
    if flags.disabled:
        return CloseIssueOutcome(skipped_reason="flag-disabled")
    if not enabled:
        return CloseIssueOutcome(skipped_reason="disabled")
    if not provider_is_github(provider):
        return CloseIssueOutcome(skipped_reason="not-github")

    try:
        loaded = registry.load()
    except Exception as exc:
        return _unreadable_registry(exc)
    if loaded.error:
        return _unreadable_registry(loaded.error)

    issue = loaded.issue
    if issue is None:
        return CloseIssueOutcome(skipped_reason="no-record")

    repo = str(getattr(repo_ref, "display", "") or "").strip().casefold()
    if not repo or repo != issue.repo.strip().casefold():
        # A record from another repository is none of this flow's business;
        # it is never cleared (ADR-007).
        return CloseIssueOutcome(skipped_reason="other-repo")

    try:
        info = provider.get_issue(repo_ref, issue.number, timeout=timeout)
    except ScmProviderError as exc:
        if exc.http_status == 404:
            # The issue is gone: the record can never be used again.
            _clear_quietly(registry)
            return CloseIssueOutcome(skipped_reason="issue-missing")
        return _verify_failed(issue.number, exc)
    except Exception as exc:
        return _verify_failed(issue.number, exc)

    if bool(getattr(info, "is_pull_request", False)):
        # GitHub's issue endpoint answers pull request numbers too, so the
        # PR check must come before the state check.
        _clear_quietly(registry)
        return CloseIssueOutcome(skipped_reason="issue-is-pr")

    state = str(getattr(info, "state", "") or "").strip().lower()
    if state != "open":
        _clear_quietly(registry)
        return CloseIssueOutcome(skipped_reason="issue-not-open")

    if not flags.accept and (not is_tty or ask is None):
        return CloseIssueOutcome(skipped_reason="no-tty")

    line = provider.closing_line(issue.number)
    title = str(getattr(info, "title", "") or "").strip() or issue.title

    if flags.accept:
        return CloseIssueOutcome(
            decision=CloseIssueDecision(issue.number, title, line),
            accepted=True,
        )

    warning = _target_branch_warning(provider, repo_ref, target_branch, timeout)
    question = __(
        'Issue #{number} – {title} is open. Add "{line}" to the end of the '
        "pull request description?",
        number=issue.number,
        title=title,
        line=line,
    )
    if warning:
        question = f"{question}\n{warning}"

    if not ask(question, default=True):
        return CloseIssueOutcome(skipped_reason="declined", asked=True)

    return CloseIssueOutcome(
        decision=CloseIssueDecision(issue.number, title, line, warning),
        asked=True,
        accepted=True,
    )


def _target_branch_warning(provider, repo_ref, target_branch, timeout):
    """The merge-into-the-wrong-branch warning, or "" when it cannot apply.

    A failed or empty default-branch lookup degrades in silence: the forge only
    says "unknown", and a warning the caller cannot phrase correctly is worse
    than no warning at all.
    """
    try:
        default = str(
            provider.get_default_branch(repo_ref, timeout=timeout) or ""
        ).strip()
    except Exception:
        return ""

    target = str(target_branch or "").strip()
    if not default or not target or target == default:
        return ""

    return __(
        'Warning: the pull request targets "{target}" but the default branch '
        'is "{default}". GitHub only closes the issue when the merge lands on '
        "the default branch.",
        target=target,
        default=default,
    )


def _clear_quietly(registry):
    """Forgets a record that can never be used again.

    The record is local state; a failure to remove it leaves the file for the
    next run to overwrite and must never break the PR flow.
    """
    try:
        registry.clear()
    except Exception:
        pass


def _unreadable_registry(error):
    return CloseIssueOutcome(
        warning=__(
            "Could not read the local issue record: {error}.",
            error=error,
        ),
        skipped_reason="registry-error",
    )


def _verify_failed(number, error):
    return CloseIssueOutcome(
        warning=__(
            "Could not check issue #{number}: {error}. The local issue record "
            "was kept.",
            number=number,
            error=error,
        ),
        skipped_reason="verify-failed",
    )
