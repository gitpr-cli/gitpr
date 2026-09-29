"""SCM provider abstraction: the unified contract over Git hosting forges.

This module holds the domain contract only — the abstract ``ScmProvider``
interface, the request/result dataclasses and the error types. HTTP/API details
live in the concrete providers (github_provider.py, gitlab_provider.py,
bitbucket_provider.py, azure_devops_provider.py) selected via
``factory.resolve_scm_provider``.

Error convention (deliberate deviation from the old tuple-returning
``github_api`` helpers): every provider method raises ``ScmProviderError`` on
HTTP failures and network errors instead of swallowing them.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PullRequestRequest:
    """A pull request to be created on the forge.

    source_branch/target_branch are the canonical names (GitHub "head"/"base",
    GitLab "source"/"target", Bitbucket "source"/"destination", Azure
    sourceRefName/targetRefName).
    """

    title: str
    description: str
    source_branch: str
    target_branch: str
    draft: bool = False
    labels: list[str] = field(default_factory=list)
    reviewers: list[str] = field(default_factory=list)


@dataclass
class PullRequestResult:
    """A pull request as returned by the forge API.

    id is the resource identifier used by follow-up API calls (GitLab uses the
    MR ``iid`` here, never the global project-scoped id); number is the
    user-visible number (GitLab iid, GitHub number, Bitbucket id, Azure
    pullRequestId).

    The three dates are the forge's own ISO-8601 strings, exactly as published
    and in the forge's timezone (UTC everywhere today) — normalizing them would
    mean inventing a precision the source did not have. Empty means the forge
    published no such date for this pull request, which is not the same as
    "never": Bitbucket Cloud has no merged_on on the pull request list, so every
    Bitbucket row leaves merged_at empty (see ScmProvider.supports_merged_dates).
    """

    id: str | int
    url: str
    number: int
    state: str
    source_branch: str
    target_branch: str
    provider: str
    created_at: str = ""
    merged_at: str = ""
    closed_at: str = ""


def within_window(timestamp: str, since: Optional[str], until: Optional[str]) -> bool:
    """Whether an ISO-8601 timestamp falls inside inclusive YYYY-MM-DD bounds.

    Only the calendar day is compared — ``timestamp[:10]`` — which is what a
    window means to the reader and what every forge format agrees on
    (``...T10:00:00Z``, ``...T10:00:00.1234567Z``, ``...+00:00``). The day is
    the forge's, so a pull request merged late in the evening locally can land
    on the next day's UTC date; moving the window is the caller's to do.

    A row the forge gave no date for cannot be placed in a window: it passes
    only when no window was asked for.
    """
    day = str(timestamp or "")[:10]
    if not day:
        return not (since or until)
    if since and day < str(since)[:10]:
        return False
    if until and day > str(until)[:10]:
        return False
    return True


@dataclass
class RepoRef:
    """A repository parsed from a git remote URL.

    workspace is the forge-specific namespace segment: GitHub owner, GitLab
    group/subgroup namespace, Bitbucket workspace, or "{org}/{project}" for
    Azure DevOps (display only — Azure API calls use the organization/project
    from the provider extra config, never this field).
    """

    raw: str
    workspace: str
    name: str
    provider: str

    @property
    def display(self) -> str:
        """Human-readable repository label ("workspace/name", or name alone)."""
        return f"{self.workspace}/{self.name}" if self.workspace else self.name


@dataclass
class IssueRequest:
    """An issue to be created on the forge (create_issue)."""

    title: str
    description: str


@dataclass
class IssueResult:
    """An issue as returned by the forge API (create_issue)."""

    id: str | int
    url: str
    number: int
    provider: str


class ScmProviderError(Exception):
    """Raised by ScmProvider methods on HTTP failures and network errors.

    http_status carries the HTTP status code when the server answered
    (4xx/5xx) or 0 for network/connection failures (no HTTP response).
    message is the best-effort server/decoded message; network-failure
    messages are already localized.
    """

    def __init__(self, provider: str, http_status: int, message: str):
        self.provider = provider
        self.http_status = http_status
        self.message = message
        super().__init__(f"[{provider}] HTTP {http_status}: {message}")


class ScmNotSupportedError(ScmProviderError):
    """Raised when a forge has no equivalent API for the requested operation.

    Example: Azure DevOps has no "issue" resource — create_issue raises this.
    """

    def __init__(self, provider: str, message: str):
        super().__init__(provider, 0, message)


class ScmProvider(ABC):
    """Unified interface over Git hosting forges (PRs, issues, releases).

    Subclasses are stateless-per-request HTTP clients: construction performs no
    network I/O (UI/TUI flows construct providers freely), and every public
    method raises ScmProviderError instead of returning error tuples.
    """

    name: str

    # Whether get_pull_request_diff returns something the AI review engine can
    # actually review. Azure DevOps is False: Azure REST serves no unified diff
    # and its method returns "{path} (+additions -deletions)" summary lines, so
    # the remote-PR review refuses the forge up front instead of spending AI
    # tokens reviewing prose that has no hunks in it. Callers that only surface
    # a diff (the PR publisher) are unaffected — they never check this flag.
    supports_reviewable_diff: bool = True

    # Whether list_pull_requests can date a merge. Bitbucket Cloud is False: its
    # pull request object publishes created_on and updated_on and no merged_on
    # (nor a closed_on), and updated_on moves with every comment left after the
    # merge — so a Bitbucket row carries an empty merged_at rather than a date
    # that is not the one asked for. Callers that measure a commit-to-merge
    # cycle read this flag and say what they cannot measure, in the same spirit
    # as supports_reviewable_diff: declared before the call, not discovered
    # from a wrong number afterwards.
    supports_merged_dates: bool = True

    def __init__(self, token: str, base_url: Optional[str] = None, **kwargs):
        self.token = token or ""
        self.base_url = (base_url or self.default_base_url()).rstrip("/")
        self.extra = kwargs

    @abstractmethod
    def default_base_url(self) -> str:
        """Public SaaS API base URL used when no custom base_url is given."""

    @abstractmethod
    def parse_repo_ref(self, remote_url: str) -> RepoRef:
        """Parse a git remote URL into a RepoRef.

        Raises ValueError when the URL cannot be parsed.
        """

    @abstractmethod
    def create_pull_request(
        self, repo: RepoRef, req: PullRequestRequest
    ) -> PullRequestResult:
        """Create a pull request and return its normalized result."""

    @abstractmethod
    def get_pull_request_diff(self, repo: RepoRef, pr_id: str | int) -> str:
        """Fetch the pull request diff as text (provider-specific fidelity)."""

    def list_open_pull_requests(self, repo: RepoRef) -> list[PullRequestResult]:
        """List open pull requests of the repository.

        A thin wrapper over list_pull_requests(state="open"). The name stays —
        every call site and test uses it, and a forge that cannot list pull
        requests at all raises from underneath, with the same error it would
        have raised for any other state.
        """
        return self.list_pull_requests(repo, state="open")

    @abstractmethod
    def add_comment(self, repo: RepoRef, pr_id: str | int, body: str) -> None:
        """Add a comment/note to the pull request."""

    @abstractmethod
    def merge_pull_request(
        self, repo: RepoRef, pr_id: str | int, strategy: str = "merge"
    ) -> None:
        """Merge the pull request using the forge's merge strategy."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Validate the configured token against the forge (200 = ok)."""

    # -- Added to the original spec contract (needed by the PR publisher TUI
    # -- and the issue flows): keep all four implementations in sync.

    @abstractmethod
    def check_existing_pull_request(
        self, repo: RepoRef, source_branch: str
    ) -> Optional[PullRequestResult]:
        """Return the open pull request whose source branch matches, or None.

        Raises ScmProviderError on failures like any other method — swallowing
        (when desired) is the UI seam's job, not the provider's.
        """

    @abstractmethod
    def update_pull_request(
        self,
        repo: RepoRef,
        pr_id: str | int,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> PullRequestResult:
        """Update the pull request title/description (only provided fields)."""

    @abstractmethod
    def create_issue(self, repo: RepoRef, req: IssueRequest) -> IssueResult:
        """Create an issue on the forge.

        Raises ScmNotSupportedError when the forge has no issue resource
        (Azure DevOps).
        """

    def create_release(
        self, repo: RepoRef, tag: str, title: str, body: str, draft: bool = False
    ) -> str:
        """Create a release on the forge and return its URL.

        Deliberately NOT abstract: only forges with a native release resource
        support it (GitHub Releases, GitLab Releases). The default raises
        ScmNotSupportedError so Bitbucket/Azure keep compiling and the local
        changelog flow keeps working untouched (gitpr release grill, Q11).
        """
        raise ScmNotSupportedError(
            self.name,
            "This forge has no API to create releases.",
        )

    def request_pull_request_reviewers(
        self, repo: RepoRef, pr_id: str | int, reviewers: list[str]
    ) -> list[str]:
        """Request reviewers on an existing pull request.

        Returns the logins the forge actually attached (read back from the
        response), which is how the caller detects a request the forge
        accepted but silently ignored.

        Deliberately NOT abstract: only forges with a reviewer API support it
        (GitHub's requested_reviewers). The default raises
        ScmNotSupportedError so the four concrete providers keep compiling and
        the contract tests stay untouched.
        """
        raise ScmNotSupportedError(
            self.name,
            "This forge has no API to request pull request reviewers.",
        )

    def get_pull_request(self, repo: RepoRef, pr_id: str | int) -> PullRequestResult:
        """Fetch a single pull request by its user-visible number.

        Deliberately NOT abstract, for a different reason than the two above:
        every concrete provider implements it, but the default keeps third-party
        subclasses and the contract tests compiling. The remote-PR review needs
        this to resolve metadata and to tell "does not exist" from "merged or
        closed" — list_open_pull_requests cannot, since it only ever returns
        open PRs (it paginates now, but the state it filters by is still the
        one thing it cannot leave).
        """
        raise ScmNotSupportedError(
            self.name,
            "This forge has no API to fetch a single pull request.",
        )

    def list_pull_requests(
        self,
        repo: RepoRef,
        state: str = "all",
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> list[PullRequestResult]:
        """List the repository's pull requests by state and period, paginated.

        state is the canonical vocabulary — "open", "closed", "merged", "all" —
        and each provider translates it to its own and then filters the answers
        by it, because three of the four forges answer a request for merged
        pull requests with something wider: GitHub has no merged state at all
        (it reads ``state=closed`` and drops the rows without a merged_at),
        Azure calls a merge "completed" and a close "abandoned", Bitbucket says
        DECLINED. A caller asking for merged pull requests gets merged pull
        requests, or an error — never a superset dressed as the answer.

        since/until are inclusive YYYY-MM-DD bounds on the date the state
        implies: merged_at for "merged", closed_at for "closed", created_at
        otherwise. Every page is read until the forge says there is no next one
        — GitHub by Link, GitLab by X-Next-Page, Bitbucket by the body's next
        URL, Azure by continuation token — with one early stop: three of the
        four list newest-updated first, and since a pull request is updated at
        or after it is merged, a page whose newest entry predates ``since``
        cannot be followed by one that does not. Azure has no such ordering, so
        it hands the window to the server (minTime/maxTime with
        queryTimeRangeType) instead.

        Deliberately NOT abstract: a forge with no way to list pull requests
        raises ScmNotSupportedError, exactly like create_release above, so the
        caller can degrade instead of guessing at an empty list.
        """
        raise ScmNotSupportedError(
            self.name,
            "This forge has no API to list pull requests.",
        )

    def with_token(self, token: str) -> "ScmProvider":
        """Return a new provider instance with a fresh token (reauth loops)."""
        return type(self)(token=token, base_url=self.base_url, **self.extra)
