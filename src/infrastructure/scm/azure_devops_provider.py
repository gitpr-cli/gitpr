"""AzureDevOpsProvider — Azure DevOps REST (api-version 7.1) implementation.

Behavioral notes:
  - The API is addressed per organization+project taken from the provider
    extras (GITPR_SCM_ORGANIZATION / GITPR_SCM_PROJECT), never from RepoRef —
    Azure's RepoRef.workspace ("{org}/{project}") is display-only.
  - Authentication uses requests' Basic auth with an empty user and the PAT as
    password: auth=("", token). Azure accepts PATs as the Basic password.
  - Every URL carries ?api-version=7.1 (injected in _request, so all verbs get
    it, not only the read calls).
  - Branches are addressed as refs/heads/{branch} (sourceRefName/targetRefName).
  - The pull request diff is a textual SUMMARY of the last iteration's
    changeEntries ("{path} (+additions -deletions)") — Azure REST does not
    serve unified diffs (deliberate deviation, documented in ADR-001).
  - Merges PATCH {"status": "completed", "completionOptions":
    {"mergeStrategy": ...}}; the generic "merge" strategy maps to Azure's
    "noFastForward" (merge commit).
  - Azure DevOps has no issue resource: create_issue raises ScmNotSupportedError.
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
    ScmNotSupportedError,
    ScmProvider,
    ScmProviderError,
)

# https://dev.azure.com/{org}/{project}/_git/{repo} and the ssh variants
# git@ssh.dev.azure.com:v3/{org}/{project}/{repo} / vs-ssh.visualstudio.com.
_AZURE_DEV_OPS_RE = re.compile(
    r"^(?:https?://)?(?:[^/@]+@)?"
    r"(?:dev\.azure\.com|ssh\.dev\.azure\.com|vs-ssh\.visualstudio\.com)"
    r"[:/](?:v3/)?(?P<org>[^/]+)/(?P<project>[^/]+?)(?:/_git/|/)"
    r"(?P<repo>[^/]+?)(?:\.git)?/?$"
)

# Legacy layout: https://{org}.visualstudio.com/{project}/_git/{repo}
_VSO_RE = re.compile(
    r"^(?:https?://)?(?P<org>[^/@]+)\.visualstudio\.com/"
    r"(?P<project>[^/]+?)/_git/(?P<repo>[^/]+?)(?:\.git)?/?$"
)

DISPLAY_NAME = "Azure DevOps"

# Generic contract strategy -> Azure completionOptions.mergeStrategy.
_STRATEGIES = {
    "merge": "noFastForward",
    "squash": "squash",
    "rebase": "rebase",
    "rebase_merge": "rebaseMerge",
}


def _extract_error_message(response):
    """Best-effort extraction of Azure's error payload.

    Azure answers {"message": "...", "typeKey": ...} for REST errors (inside
    "$id"/"innerException" wrappers on some endpoints).
    """
    try:
        j = response.json()
        if isinstance(j, dict):
            message = j.get("message")
            if message:
                return str(message)
            inner = j.get("innerException")
            if isinstance(inner, dict) and inner.get("message"):
                return str(inner["message"])
            if j.get("typeKey"):
                return str(j["typeKey"])
    except Exception:
        pass
    return response.text


class AzureDevOpsProvider(ScmProvider):
    """Azure DevOps Services (dev.azure.com, and TFS-style base_urls)."""

    name = "azure_devops"

    def __init__(self, token="", base_url=None, **kwargs):
        # Fail-fast: the org/project come from the provider extras, so both are
        # mandatory — the error names the .env keys the user must configure.
        organization = kwargs.get("organization")
        project = kwargs.get("project")
        missing = []
        if not organization:
            missing.append("GITPR_SCM_ORGANIZATION")
        if not project:
            missing.append("GITPR_SCM_PROJECT")
        if missing:
            raise ScmProviderError(
                self.name,
                0,
                __(
                    "{provider} requires {env_vars} to be configured. Run 'gitpr --init' or set them in the .env file.",
                    provider=DISPLAY_NAME,
                    env_vars=", ".join(missing),
                ),
            )
        super().__init__(token, base_url, **kwargs)

    def default_base_url(self) -> str:
        return "https://dev.azure.com"

    # -- parsing ---------------------------------------------------------

    def parse_repo_ref(self, remote_url: str) -> RepoRef:
        url = remote_url.strip()
        match = _AZURE_DEV_OPS_RE.match(url) or _VSO_RE.match(url)
        if not match:
            raise ValueError(
                f"Could not parse Azure DevOps repository from remote URL: {remote_url}"
            )
        org = match.group("org")
        project = match.group("project")
        return RepoRef(
            raw=remote_url,
            workspace=f"{org}/{project}",
            name=match.group("repo"),
            provider=self.name,
        )

    # -- HTTP plumbing ---------------------------------------------------

    def _headers(self) -> dict:
        return {"Accept": "application/json"}

    def _request(self, verb, url, expected, timeout, *, create=False, **kwargs):
        """Run one REST call; convert failures into ScmProviderError.

        Every Azure REST call needs ?api-version=7.1 — injected here so all
        verbs carry it. Auth is Basic with an empty user and the PAT password.
        """
        params = dict(kwargs.pop("params", {}))
        params["api-version"] = "7.1"
        headers = self._headers()
        headers.update(kwargs.pop("headers", {}))
        try:
            response = getattr(requests, verb)(
                url,
                headers=headers,
                params=params,
                auth=("", self.token),
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
        """.../{org}/{project}/_apis/git/repositories/{quoted name}[/part/...]"""
        org = quote(self.extra.get("organization", ""), safe="")
        project = quote(self.extra.get("project", ""), safe="")
        url = (
            f"{self.base_url}/{org}/{project}/_apis/git/repositories/"
            f"{quote(repo.name, safe='')}"
        )
        if parts:
            url += "/" + "/".join(str(part) for part in parts)
        return url

    @staticmethod
    def _branch_name(ref_name: str) -> str:
        """Strip the refs/heads/ prefix — never the branch's own slashes."""
        prefix = "refs/heads/"
        if ref_name and ref_name.startswith(prefix):
            return ref_name[len(prefix):]
        return ref_name

    def _to_result(
        self, j: dict, source: str = "", target: str = ""
    ) -> PullRequestResult:
        pr_id = j.get("pullRequestId")
        return PullRequestResult(
            id=pr_id,
            url=self._pr_web_url_from_pr(j),
            number=pr_id,
            state=j.get("status", "active"),
            source_branch=self._branch_name(j.get("sourceRefName", source)),
            target_branch=self._branch_name(j.get("targetRefName", target)),
            provider=self.name,
        )

    def _pr_web_url_from_pr(self, j: dict) -> str:
        """Best browser URL for a PR object (falls back to the API url field)."""
        pr_id = j.get("pullRequestId")
        org = self.extra.get("organization", "")
        project = self.extra.get("project", "")
        repository = j.get("repository", {})
        repo_name = repository.get("name", "")
        if pr_id and repo_name:
            return (
                f"{self.base_url}/{org}/{project}/_git/{repo_name}/pullrequest/{pr_id}"
            )
        return j.get("url", "")

    # -- pull requests ---------------------------------------------------

    def create_pull_request(
        self, repo: RepoRef, req: PullRequestRequest, timeout: int = 30
    ) -> PullRequestResult:
        payload = {
            "sourceRefName": f"refs/heads/{req.source_branch}",
            "targetRefName": f"refs/heads/{req.target_branch}",
            "title": req.title,
            "description": req.description,
        }
        response = self._request(
            "post",
            self._repo_url(repo, "pullrequests"),
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
        params = {
            "searchCriteria.status": "active",
            "searchCriteria.sourceRefName": f"refs/heads/{source_branch}",
        }
        response = self._request(
            "get",
            self._repo_url(repo, "pullrequests"),
            {200},
            timeout,
            params=params,
        )
        for pr in response.json().get("value", []):
            if pr.get("sourceRefName") == f"refs/heads/{source_branch}":
                return self._to_result(pr, source=source_branch)
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
            "patch",
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
        payload = {
            "status": "completed",
            "completionOptions": {"mergeStrategy": merge_strategy},
        }
        self._request(
            "patch",
            self._repo_url(repo, "pullrequests", pr_id),
            {200},
            timeout,
            json=payload,
        )

    def get_pull_request_diff(self, repo: RepoRef, pr_id: str | int) -> str:
        # Azure serves no unified diff over REST: fetch the latest iteration
        # and summarize its changeEntries (additions/deletions per path).
        response = self._request(
            "get",
            self._repo_url(repo, "pullrequests", pr_id, "iterations"),
            {200},
            15,
        )
        iterations = response.json().get("value", [])
        if not iterations:
            return ""
        last_id = iterations[-1].get("id")
        changes = self._request(
            "get",
            self._repo_url(repo, "pullrequests", pr_id, "iterations", last_id, "changes"),
            {200},
            15,
        )
        summary = []
        for entry in changes.json().get("changeEntries", []):
            item = entry.get("item", {})
            path = item.get("path", "")
            additions = entry.get("additions", 0)
            deletions = entry.get("deletions", 0)
            summary.append(f"{path} (+{additions} -{deletions})")
        return "\n".join(summary)

    def list_open_pull_requests(self, repo: RepoRef) -> list[PullRequestResult]:
        response = self._request(
            "get",
            self._repo_url(repo, "pullrequests"),
            {200},
            15,
            params={"searchCriteria.status": "active"},
        )
        return [self._to_result(pr) for pr in response.json().get("value", [])]

    def add_comment(self, repo: RepoRef, pr_id: str | int, body: str) -> None:
        # Thread comments: commentType 1 = text, status 1 = active thread.
        self._request(
            "post",
            self._repo_url(repo, "pullrequests", pr_id, "threads"),
            {201},
            15,
            json={"comments": [{"content": body, "commentType": 1}], "status": 1},
        )

    # -- issues ----------------------------------------------------------

    def create_issue(self, repo: RepoRef, req: IssueRequest) -> IssueResult:
        # Azure DevOps has work items, not issues — no REST equivalent for the
        # generic issue flow. The UI surfaces the not-supported message.
        raise ScmNotSupportedError(
            self.name,
            "Azure DevOps has no issue API resource. Save the issue locally (F2).",
        )

    # -- connection ------------------------------------------------------

    def test_connection(self, timeout: int = 10) -> bool:
        org = quote(self.extra.get("organization", ""), safe="")
        project = quote(self.extra.get("project", ""), safe="")
        response = self._request(
            "get",
            f"{self.base_url}/{org}/_apis/projects/{project}",
            {200},
            timeout,
        )
        return response.status_code == 200
