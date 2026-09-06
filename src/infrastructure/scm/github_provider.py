"""GitHubProvider — GitHub REST implementation of the ScmProvider contract.

Extracted from the legacy src/github_api.py helpers (which now act as a thin
deprecated shim over this class). Behavioral notes:
  - Auth header stays "Authorization: token {token}" (deliberate deviation from
    the spec's "Bearer" — GitHub accepts both and the migrated tests pin the
    original header).
  - Payloads, URLs, expected status codes and timeouts mirror the legacy code
    byte-for-byte (create 30s, everything else 15s, test_connection 10s).
  - Errors RAISE ScmProviderError instead of the old (ok, data, status)
    tuples: http_status carries the HTTP code, 0 means no HTTP response.
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


def _extract_error_message(response):
    """Best-effort extraction of GitHub's error payload (message + errors[])."""
    try:
        j = response.json()
        details = j.get("message", "")
        for err in j.get("errors", []):
            field = err.get("field", "")
            msg = err.get("message", "")
            if field:
                details += f" [{field}: {msg}]"
            elif msg:
                details += f" {msg}"
        return details.strip() or response.text
    except Exception:
        return response.text


class GitHubProvider(ScmProvider):
    """GitHub (github.com SaaS and GitHub Enterprise base_urls)."""

    name = "github"

    def default_base_url(self) -> str:
        return "https://api.github.com"

    # -- parsing ---------------------------------------------------------

    def parse_repo_ref(self, remote_url: str) -> RepoRef:
        match = re.search(
            r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", remote_url.strip()
        )
        if not match:
            raise ValueError(
                f"Could not parse GitHub repository from remote URL: {remote_url}"
            )
        return RepoRef(
            raw=remote_url,
            workspace=match.group(1),
            name=match.group(2).rstrip("/"),
            provider=self.name,
        )

    # -- HTTP plumbing ---------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _repo_url(self, repo: RepoRef, *parts) -> str:
        """.../repos/{workspace}/{name}[/part/...]"""
        url = f"{self.base_url}/repos/{repo.workspace}/{repo.name}"
        if parts:
            url += "/" + "/".join(str(part) for part in parts)
        return url

    def _network_error_message(self, exc: Exception, *, create: bool = False) -> str:
        """Map a transport failure to the message the legacy layer surfaced."""
        if isinstance(exc, requests.exceptions.ConnectionError):
            if create:
                return __("No internet connection. Cannot create the pull request.")
            return __("No internet connection.")
        if isinstance(exc, requests.exceptions.Timeout):
            return __("GitHub API timeout. Check your connection and try again.")
        if create:
            return __("Failed to connect to GitHub: {error}", error=str(exc))
        return str(exc)

    def _request(self, verb, url, expected, timeout, *, create=False, **kwargs):
        """Run one REST call; convert failures into ScmProviderError.

        expected is the set of status codes treated as success. Anything else
        (or any transport error) raises.
        """
        headers = self._headers()
        headers.update(kwargs.pop("headers", {}))
        try:
            response = getattr(requests, verb)(
                url, headers=headers, timeout=timeout, **kwargs
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

    # -- pull requests ---------------------------------------------------

    def create_pull_request(
        self, repo: RepoRef, req: PullRequestRequest, timeout: int = 30
    ) -> PullRequestResult:
        payload = {
            "title": req.title,
            "body": req.description,
            "head": req.source_branch,
            "base": req.target_branch,
        }
        if req.draft:
            payload["draft"] = True
        response = self._request(
            "post",
            self._repo_url(repo, "pulls"),
            {201},
            timeout,
            create=True,
            json=payload,
        )
        j = response.json()
        return PullRequestResult(
            id=j.get("number"),
            url=j.get("html_url", ""),
            number=j.get("number"),
            state=j.get("state", "open"),
            source_branch=req.source_branch,
            target_branch=req.target_branch,
            provider=self.name,
        )

    def check_existing_pull_request(
        self, repo: RepoRef, source_branch: str, timeout: int = 15
    ):
        params = {
            "head": f"{repo.workspace}:{source_branch}",
            "state": "open",
        }
        response = self._request(
            "get",
            self._repo_url(repo, "pulls"),
            {200},
            timeout,
            params=params,
        )
        prs = response.json()
        if not prs:
            return None
        pr = prs[0]
        return PullRequestResult(
            id=pr.get("number"),
            url=pr.get("html_url", ""),
            number=pr.get("number"),
            state=pr.get("state", "open"),
            source_branch=pr.get("head", {}).get("ref", source_branch),
            target_branch=pr.get("base", {}).get("ref", ""),
            provider=self.name,
        )

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
            payload["body"] = description
        response = self._request(
            "patch",
            self._repo_url(repo, "pulls", pr_id),
            {200},
            timeout,
            json=payload,
        )
        j = response.json()
        return PullRequestResult(
            id=j.get("number"),
            url=j.get("html_url", ""),
            number=j.get("number"),
            state=j.get("state", "open"),
            source_branch="",
            target_branch="",
            provider=self.name,
        )

    def merge_pull_request(
        self, repo: RepoRef, pr_id: str | int, strategy: str = "merge", timeout: int = 15
    ) -> None:
        payload = {} if strategy == "merge" else {"merge_method": strategy}
        self._request(
            "put",
            self._repo_url(repo, "pulls", pr_id, "merge"),
            {200},
            timeout,
            json=payload,
        )

    def get_pull_request_diff(self, repo: RepoRef, pr_id: str | int) -> str:
        response = self._request(
            "get",
            self._repo_url(repo, "pulls", pr_id),
            {200},
            15,
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        return response.text

    def list_open_pull_requests(self, repo: RepoRef) -> list[PullRequestResult]:
        response = self._request(
            "get",
            self._repo_url(repo, "pulls"),
            {200},
            15,
            params={"state": "open"},
        )
        results = []
        for pr in response.json():
            results.append(
                PullRequestResult(
                    id=pr.get("number"),
                    url=pr.get("html_url", ""),
                    number=pr.get("number"),
                    state=pr.get("state", "open"),
                    source_branch=pr.get("head", {}).get("ref", ""),
                    target_branch=pr.get("base", {}).get("ref", ""),
                    provider=self.name,
                )
            )
        return results

    def add_comment(self, repo: RepoRef, pr_id: str | int, body: str) -> None:
        self._request(
            "post",
            self._repo_url(repo, "issues", pr_id, "comments"),
            {201},
            15,
            json={"body": body},
        )

    # -- issues ----------------------------------------------------------

    def create_issue(
        self, repo: RepoRef, req: IssueRequest, timeout: int = 15
    ) -> IssueResult:
        response = self._request(
            "post",
            self._repo_url(repo, "issues"),
            {201},
            timeout,
            json={"title": req.title, "body": req.description},
        )
        j = response.json()
        return IssueResult(
            id=j.get("number"),
            url=j.get("html_url", ""),
            number=j.get("number"),
            provider=self.name,
        )

    # -- connection ------------------------------------------------------

    def test_connection(self, timeout: int = 10) -> bool:
        response = self._request(
            "get", f"{self.base_url}/user", {200}, timeout
        )
        return response.status_code == 200
