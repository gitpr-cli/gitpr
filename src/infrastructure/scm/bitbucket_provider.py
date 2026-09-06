"""BitbucketProvider — Bitbucket Cloud REST 2.0 implementation.

Behavioral notes:
  - Authentication is HTTP Basic with the App Password: auth=(username, token).
    The username comes from the provider extras (GITPR_SCM_USERNAME) and is
    mandatory — construction fails fast when it is missing.
  - Repositories are addressed as {base}/repositories/{workspace}/{slug}; both
    path segments are slugs (URL-safe by Bitbucket's own rules), so no quoting
    is applied (matches the GitHub provider).
  - create/update use nested bodies ({"source": {"branch": {"name": ...}}});
    updates are PUT and merges POST .../pullrequests/{id}/merge with a
    {"merge_strategy": ...} body — the generic "merge" strategy maps to
    Bitbucket's "merge_commit".
  - Draft PRs are best-effort: {"draft": true} is sent only when requested.
  - The diff is Bitbucket's plain unified diff (REST serves text/plain).
  - Issues require the Issue Tracker feature enabled on the repository
    (documented in ADR-001); when it is disabled the API answers 404 and the
    error propagates as ScmProviderError like any other.
  - Errors RAISE ScmProviderError like every provider (http_status 0 = network).
"""

import re

import requests

from src.i18n import __
from src.infrastructure.scm.base import (
    IssueRequest,
    IssueResult,
    PullRequestRequest,
    PullRequestResult,
    RepoRef,
    ScmProvider,
    ScmProviderError,
)

# https://bitbucket.org/{workspace}/{slug}[/.git] and git@bitbucket.org:...
_BITBUCKET_RE = re.compile(
    r"^(?:https?://)?(?:[^/@]+@)?bitbucket\.org[:/]"
    r"(?P<workspace>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)

DISPLAY_NAME = "Bitbucket"

# Generic contract strategy -> Bitbucket merge strategies.
_STRATEGIES = {
    "merge": "merge_commit",
    "squash": "squash",
    "fast_forward": "fast_forward",
}


def _extract_error_message(response):
    """Best-effort extraction of Bitbucket's error payload.

    Bitbucket answers {"error": {"message": "...", "fields": {...}}} for REST
    errors; the "message" is usually enough, but the field errors are appended
    when present (they explain validation failures).
    """
    try:
        j = response.json()
        if isinstance(j, dict) and isinstance(j.get("error"), dict):
            error = j["error"]
            message = error.get("message")
            fields = error.get("fields")
            if isinstance(fields, dict) and fields:
                details = "; ".join(f"{k}: {v}" for k, v in fields.items())
                return f"{message} ({details})" if message else details
            if message:
                return str(message)
    except Exception:
        pass
    return response.text


class BitbucketProvider(ScmProvider):
    """Bitbucket Cloud (api.bitbucket.org/2.0, and self-hosted base_urls)."""

    name = "bitbucket"

    def __init__(self, token="", base_url=None, **kwargs):
        # Fail-fast: Bitbucket auth is Basic(username, App Password), so the
        # username is part of the credential, not of the repo URL. The error
        # names the .env key the user must configure.
        username = kwargs.get("username")
        if not username:
            raise ScmProviderError(
                self.name,
                0,
                __(
                    "{provider} requires {env_vars} to be configured. Run 'gitpr --init' or set them in the .env file.",
                    provider=DISPLAY_NAME,
                    env_vars="GITPR_SCM_USERNAME",
                ),
            )
        super().__init__(token, base_url, **kwargs)

    def default_base_url(self) -> str:
        return "https://api.bitbucket.org/2.0"

    # -- parsing ---------------------------------------------------------

    def parse_repo_ref(self, remote_url: str) -> RepoRef:
        url = remote_url.strip()
        match = _BITBUCKET_RE.match(url)
        if not match:
            raise ValueError(
                f"Could not parse Bitbucket repository from remote URL: {remote_url}"
            )
        return RepoRef(
            raw=remote_url,
            workspace=match.group("workspace"),
            name=match.group("repo"),
            provider=self.name,
        )

    # -- HTTP plumbing ---------------------------------------------------

    def _headers(self) -> dict:
        return {"Accept": "application/json"}

    def _request(self, verb, url, expected, timeout, *, create=False, **kwargs):
        """Run one REST call; convert failures into ScmProviderError."""
        headers = self._headers()
        headers.update(kwargs.pop("headers", {}))
        try:
            response = getattr(requests, verb)(
                url,
                headers=headers,
                auth=(self.extra.get("username", ""), self.token),
                timeout=timeout,
                **kwargs,
            )
        except requests.exceptions.RequestException as exc:
            raise ScmProviderError(
                self.name, 0, self._network_error_message(exc, create=create)
            ) from exc
        except Exception as exc:
            raise ScmProviderError(
                self.name, 0, self._network_error_message(exc, create=create)
            ) from exc
        if response.status_code not in expected:
            raise ScmProviderError(
                self.name, response.status_code, _extract_error_message(response)
            )
        return response

    def _network_error_message(self, exc: Exception, *, create: bool = False) -> str:
        """Map a transport failure to a localized message."""
        if isinstance(exc, requests.exceptions.ConnectionError):
            if create:
                return __("No internet connection. Cannot create the pull request.")
            return __("No internet connection.")
        if isinstance(exc, requests.exceptions.Timeout):
            return __(
                "{provider} API timeout. Check your connection and try again.",
                provider=DISPLAY_NAME,
            )
        if create:
            return __(
                "Failed to connect to {provider}: {error}",
                provider=DISPLAY_NAME,
                error=str(exc),
            )
        return str(exc)

    def _repo_url(self, repo: RepoRef, *parts) -> str:
        """{base}/repositories/{workspace}/{slug}[/part/...]"""
        url = f"{self.base_url}/repositories/{repo.workspace}/{repo.name}"
        if parts:
            url += "/" + "/".join(str(part) for part in parts)
        return url

    @staticmethod
    def _branch_of(j: dict, role: str, default: str = "") -> str:
        """Read source/destination branch names from a Bitbucket PR object."""
        return j.get(role, {}).get("branch", {}).get("name", default)

    def _to_result(self, j: dict) -> PullRequestResult:
        pr_id = j.get("id")
        links = j.get("links", {})
        html = links.get("html", {}) if isinstance(links, dict) else {}
        return PullRequestResult(
            id=pr_id,
            url=html.get("href", ""),
            number=pr_id,
            state=j.get("state", "OPEN"),
            source_branch=self._branch_of(j, "source"),
            target_branch=self._branch_of(j, "destination"),
            provider=self.name,
        )

    # -- pull requests ---------------------------------------------------

    def create_pull_request(
        self, repo: RepoRef, req: PullRequestRequest, timeout: int = 30
    ) -> PullRequestResult:
        payload = {
            "title": req.title,
            "description": req.description,
            "source": {"branch": {"name": req.source_branch}},
            "destination": {"branch": {"name": req.target_branch}},
        }
        if req.draft:
            payload["draft"] = True
        response = self._request(
            "post",
            self._repo_url(repo, "pullrequests"),
            {201},
            timeout,
            create=True,
            json=payload,
        )
        return self._to_result(response.json())

    def check_existing_pull_request(
        self, repo: RepoRef, source_branch: str, timeout: int = 15
    ):
        response = self._request(
            "get",
            self._repo_url(repo, "pullrequests"),
            {200},
            timeout,
            params={"state": "OPEN"},
        )
        for pr in response.json().get("values", []):
            if self._branch_of(pr, "source") == source_branch:
                return self._to_result(pr)
        return None

    def update_pull_request(
        self,
        repo: RepoRef,
        pr_id: str | int,
        title=None,
        description=None,
        timeout: int = 15,
    ) -> PullRequestResult:
        payload = {}
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        response = self._request(
            "put",
            self._repo_url(repo, "pullrequests", pr_id),
            {200},
            timeout,
            json=payload,
        )
        return self._to_result(response.json())

    def merge_pull_request(
        self, repo: RepoRef, pr_id: str | int, strategy: str = "merge", timeout: int = 15
    ) -> None:
        merge_strategy = _STRATEGIES.get(strategy, strategy)
        self._request(
            "post",
            self._repo_url(repo, "pullrequests", pr_id, "merge"),
            {200},
            timeout,
            json={"merge_strategy": merge_strategy},
        )

    def get_pull_request_diff(self, repo: RepoRef, pr_id: str | int) -> str:
        # Bitbucket serves the unified diff as text/plain — requesting JSON
        # Accept would get a 415, so this call overrides the base header.
        response = self._request(
            "get",
            self._repo_url(repo, "pullrequests", pr_id, "diff"),
            {200},
            15,
            headers={"Accept": "text/plain"},
        )
        return response.text

    def list_open_pull_requests(self, repo: RepoRef) -> list[PullRequestResult]:
        response = self._request(
            "get",
            self._repo_url(repo, "pullrequests"),
            {200},
            15,
            params={"state": "OPEN"},
        )
        return [self._to_result(pr) for pr in response.json().get("values", [])]

    def add_comment(self, repo: RepoRef, pr_id: str | int, body: str) -> None:
        self._request(
            "post",
            self._repo_url(repo, "pullrequests", pr_id, "comments"),
            {201},
            15,
            json={"content": {"raw": body}},
        )

    # -- issues ----------------------------------------------------------

    def create_issue(
        self, repo: RepoRef, req: IssueRequest, timeout: int = 15
    ) -> IssueResult:
        # Requires the Issue Tracker enabled on the repository — the API then
        # answers 404 and the ScmProviderError propagates (ADR-001). No
        # create=True on purpose: the create-network wording is PR-specific.
        response = self._request(
            "post",
            self._repo_url(repo, "issues"),
            {201},
            timeout,
            json={"title": req.title, "content": {"raw": req.description}},
        )
        j = response.json()
        issue_id = j.get("id")
        links = j.get("links", {})
        html = links.get("html", {}) if isinstance(links, dict) else {}
        return IssueResult(
            id=issue_id,
            url=html.get("href", ""),
            number=issue_id,
            provider=self.name,
        )

    # -- connection ------------------------------------------------------

    def test_connection(self, timeout: int = 10) -> bool:
        response = self._request("get", f"{self.base_url}/user", {200}, timeout)
        return response.status_code == 200
