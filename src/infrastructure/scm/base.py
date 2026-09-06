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
    """

    id: str | int
    url: str
    number: int
    state: str
    source_branch: str
    target_branch: str
    provider: str


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
    """Unified interface over Git hosting forges (PRs + issues).

    Subclasses are stateless-per-request HTTP clients: construction performs no
    network I/O (UI/TUI flows construct providers freely), and every public
    method raises ScmProviderError instead of returning error tuples.
    """

    name: str

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

    @abstractmethod
    def list_open_pull_requests(self, repo: RepoRef) -> list[PullRequestResult]:
        """List open pull requests of the repository."""

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

    def with_token(self, token: str) -> "ScmProvider":
        """Return a new provider instance with a fresh token (reauth loops)."""
        return type(self)(token=token, base_url=self.base_url, **self.extra)
