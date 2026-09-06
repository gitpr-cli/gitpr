"""GitLabProvider — GitLab REST API v4 implementation of the ScmProvider contract.

Behavioral notes:
  - Auth header is "PRIVATE-TOKEN: {token}" (Personal Access Token).
  - The project is addressed as `quote(f"{workspace}/{name}", safe="")` — the
    full namespace including subgroups, URL-encoded as one path segment.
    Never embed a raw namespace into a project URL.
  - The MR number the user sees is the merge request *iid* (project-scoped),
    never the global MR id — PullRequestResult.id/number both carry the iid.
  - GitLab v4 has no draft flag on MR creation: a draft request is expressed
    as the "Draft: " title prefix, which GitLab renders as the draft badge.
  - The v4 merge endpoint takes no merge_method: the strategy argument exists
    for interface parity only and is ignored (GitLab merges server-side).
  - Errors RAISE ScmProviderError like every provider (http_status 0 = network).
"""

import re
from urllib.parse import quote

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

# Matches any git remote URL: optional user@, host (with optional port), then
# ":" (ssh) or "/" (https) and the namespace path. The host is deliberately
# permissive — self-managed GitLab instances live on arbitrary hostnames.
_REMOTE_RE = re.compile(r"^(?:[^/@]+@)?(?P<host>[^/:]+(?::\d+)?)[:/](?P<path>.+?)(?:\.git)?/?$")

DISPLAY_NAME = "GitLab"


def _extract_error_message(response):
    """Best-effort extraction of GitLab's error payload.

    GitLab answers with either a plain string, `{"message": "<str>"}` or
    `{"message": {"field": ["reason", ...]}}` for validation errors.
    """
    try:
        j = response.json()
    except Exception:
        return response.text
    if isinstance(j, dict):
        message = j.get("message")
        if isinstance(message, str):
            return message
        if isinstance(message, dict):
            parts = []
            for field, reasons in message.items():
                if isinstance(reasons, list):
                    parts.append(f"{field}: {', '.join(str(r) for r in reasons)}")
                else:
                    parts.append(f"{field}: {reasons}")
            if parts:
                return "; ".join(parts)
        if "error" in j:
            return str(j["error"])
    return response.text


class GitLabProvider(ScmProvider):
    """GitLab (gitlab.com SaaS and self-managed base_urls)."""

    name = "gitlab"

    def default_base_url(self) -> str:
        return "https://gitlab.com/api/v4"

    # -- parsing ---------------------------------------------------------

    def parse_repo_ref(self, remote_url: str) -> RepoRef:
        url = remote_url.strip()
        if "://" in url:
            url = url.split("://", 1)[1]
        match = _REMOTE_RE.match(url)
        if not match:
            raise ValueError(
                f"Could not parse GitLab repository from remote URL: {remote_url}"
            )
        path = match.group("path")
        if "/" not in path:
            raise ValueError(
                f"Could not parse GitLab repository from remote URL: {remote_url}"
            )
        workspace, name = path.rsplit("/", 1)
        return RepoRef(
            raw=remote_url,
            workspace=workspace,
            name=name,
            provider=self.name,
        )

    # -- HTTP plumbing ---------------------------------------------------

    def _headers(self) -> dict:
        return {"PRIVATE-TOKEN": self.token}

    def _project_url(self, repo: RepoRef, *parts) -> str:
        """.../projects/{urlencoded namespace}[/part/...]"""
        project = quote(f"{repo.workspace}/{repo.name}", safe="")
        url = f"{self.base_url}/projects/{project}"
        if parts:
            url += "/" + "/".join(str(part) for part in parts)
        return url

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

    def _request(self, verb, url, expected, timeout, *, create=False, **kwargs):
        """Run one REST call; convert failures into ScmProviderError."""
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

    def _to_result(self, j: dict, source: str = "", target: str = "") -> PullRequestResult:
        """Map a GitLab MR object to the normalized result (number = iid)."""
        return PullRequestResult(
            id=j.get("iid"),
            url=j.get("web_url", ""),
            number=j.get("iid"),
            state=j.get("state", "opened"),
            source_branch=j.get("source_branch", source),
            target_branch=j.get("target_branch", target),
            provider=self.name,
        )

    # -- merge requests --------------------------------------------------

    def create_pull_request(
        self, repo: RepoRef, req: PullRequestRequest, timeout: int = 30
    ) -> PullRequestResult:
        title = f"Draft: {req.title}" if req.draft else req.title
        payload = {
            "title": title,
            "description": req.description,
            "source_branch": req.source_branch,
            "target_branch": req.target_branch,
        }
        response = self._request(
            "post",
            self._project_url(repo, "merge_requests"),
            {201},
            timeout,
            create=True,
            json=payload,
        )
        return self._to_result(
            response.json(), source=req.source_branch, target=req.target_branch
        )

    def check_existing_pull_request(
        self, repo: RepoRef, source_branch: str, timeout: int = 15
    ):
        params = {"state": "opened", "source_branch": source_branch}
        response = self._request(
            "get",
            self._project_url(repo, "merge_requests"),
            {200},
            timeout,
            params=params,
        )
        mrs = response.json()
        if not mrs:
            return None
        return self._to_result(mrs[0], source=source_branch)

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
            self._project_url(repo, "merge_requests", pr_id),
            {200},
            timeout,
            json=payload,
        )
        return self._to_result(response.json())

    def merge_pull_request(
        self, repo: RepoRef, pr_id: str | int, strategy: str = "merge", timeout: int = 15
    ) -> None:
        # GitLab v4's merge endpoint takes no merge_method: the merge itself is
        # resolved server-side. strategy is accepted for interface parity.
        self._request(
            "put",
            self._project_url(repo, "merge_requests", pr_id, "merge"),
            {200},
            timeout,
        )

    def get_pull_request_diff(self, repo: RepoRef, pr_id: str | int) -> str:
        response = self._request(
            "get",
            self._project_url(repo, "merge_requests", pr_id, "changes"),
            {200},
            15,
        )
        changes = response.json().get("changes", [])
        return "\n".join(
            item.get("diff", "") for item in changes if item.get("diff")
        )

    def list_open_pull_requests(self, repo: RepoRef) -> list[PullRequestResult]:
        response = self._request(
            "get",
            self._project_url(repo, "merge_requests"),
            {200},
            15,
            params={"state": "opened"},
        )
        return [self._to_result(mr) for mr in response.json()]

    def add_comment(self, repo: RepoRef, pr_id: str | int, body: str) -> None:
        self._request(
            "post",
            self._project_url(repo, "merge_requests", pr_id, "notes"),
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
            self._project_url(repo, "issues"),
            {201},
            timeout,
            json={"title": req.title, "description": req.description},
        )
        j = response.json()
        return IssueResult(
            id=j.get("iid"),
            url=j.get("web_url", ""),
            number=j.get("iid"),
            provider=self.name,
        )

    # -- connection ------------------------------------------------------

    def test_connection(self, timeout: int = 10) -> bool:
        response = self._request(
            "get", f"{self.base_url}/user", {200}, timeout
        )
        return response.status_code == 200
