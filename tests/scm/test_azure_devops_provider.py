"""Unit tests for AzureDevOpsProvider (REST api-version 7.1).

Every HTTP call is mocked — no network, no real token. Error scenarios assert
ScmProviderError (the shared convention): http_status carries the HTTP code,
0 means no HTTP response. TRANSLATIONS is pinned to {} wherever user-facing
English text is asserted, so results are locale-independent.

Wire facts asserted throughout (deliberate deviations documented in ADR-001):
  - org/project come from the provider extras, never from RepoRef
  - auth is Basic with an empty user: auth=("", token)
  - every call carries ?api-version=7.1
  - branches travel as refs/heads/...
  - the diff is a textual summary of the latest iteration's changeEntries
"""
import unittest
from unittest.mock import patch, MagicMock

import requests

from src.infrastructure.scm.azure_devops_provider import (
    AzureDevOpsProvider,
    _extract_error_message,
)
from src.infrastructure.scm.base import (
    IssueRequest,
    PullRequestRequest,
    RepoRef,
    ScmNotSupportedError,
    ScmProviderError,
)

TOKEN = "azurepat"
ORG = "org"
PROJECT = "proj"
API_BASE = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/git/repositories/repo"


def _response(status_code, json_data=None, text="", raises=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if raises is not None:
        resp.json.side_effect = raises
    else:
        resp.json.return_value = json_data if json_data is not None else {}
    return resp


def _provider(**overrides):
    kwargs = dict(organization=ORG, project=PROJECT, token=TOKEN)
    kwargs.update(overrides)
    return AzureDevOpsProvider(**kwargs)


def _repo(name="repo"):
    return RepoRef(
        raw=f"https://dev.azure.com/{ORG}/{PROJECT}/_git/{name}",
        workspace=f"{ORG}/{PROJECT}",
        name=name,
        provider="azure_devops",
    )


def _pr_request(**overrides):
    defaults = dict(
        title="Title",
        description="Body",
        source_branch="feature",
        target_branch="main",
    )
    defaults.update(overrides)
    return PullRequestRequest(**defaults)


def _pr_object(pr_id=3, **overrides):
    pr = {
        "repository": {"id": "guid-123", "name": "repo"},
        "pullRequestId": pr_id,
        "status": "active",
        "sourceRefName": "refs/heads/feature",
        "targetRefName": "refs/heads/main",
        "title": "Title",
        "url": f"{API_BASE}/pullRequests/{pr_id}",
    }
    pr.update(overrides)
    return pr


class TestExtractErrorMessage(unittest.TestCase):
    def test_plain_message(self):
        resp = _response(400, {"message": "TF401027: need CreateBranch permission"})
        self.assertEqual(
            _extract_error_message(resp), "TF401027: need CreateBranch permission"
        )

    def test_inner_exception_is_used(self):
        resp = _response(
            500,
            {"$id": "1", "innerException": {"message": "inner boom"}},
        )
        self.assertEqual(_extract_error_message(resp), "inner boom")

    def test_falls_back_to_raw_text(self):
        resp = _response(500, text="<html>gateway</html>", raises=ValueError("no json"))
        self.assertEqual(_extract_error_message(resp), "<html>gateway</html>")


class TestInitFailFast(unittest.TestCase):
    """org/project are provider extras — both must exist at construction."""

    def test_missing_organization_names_env_var(self):
        with self.assertRaises(ScmProviderError) as ctx:
            AzureDevOpsProvider(token=TOKEN, project=PROJECT)
        self.assertEqual(ctx.exception.provider, "azure_devops")
        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("GITPR_SCM_ORGANIZATION", str(ctx.exception.message))
        self.assertNotIn("GITPR_SCM_PROJECT", str(ctx.exception.message))

    def test_missing_project_names_env_var(self):
        with self.assertRaises(ScmProviderError) as ctx:
            AzureDevOpsProvider(token=TOKEN, organization=ORG)
        self.assertIn("GITPR_SCM_PROJECT", str(ctx.exception.message))

    def test_missing_both_names_both_env_vars(self):
        with self.assertRaises(ScmProviderError) as ctx:
            AzureDevOpsProvider(token=TOKEN)
        message = str(ctx.exception.message)
        self.assertIn("GITPR_SCM_ORGANIZATION", message)
        self.assertIn("GITPR_SCM_PROJECT", message)
        self.assertIn("Azure DevOps", message)

    def test_with_token_keeps_extras(self):
        refreshed = _provider().with_token("new-token")
        self.assertIsInstance(refreshed, AzureDevOpsProvider)
        self.assertEqual(refreshed.token, "new-token")
        self.assertEqual(refreshed.extra["organization"], ORG)
        self.assertEqual(refreshed.extra["project"], PROJECT)


class TestParseRepoRef(unittest.TestCase):
    def test_https_url(self):
        repo = _provider().parse_repo_ref("https://dev.azure.com/org/proj/_git/repo")
        self.assertEqual(repo.workspace, "org/proj")
        self.assertEqual(repo.name, "repo")
        self.assertEqual(repo.provider, "azure_devops")

    def test_https_with_git_suffix(self):
        repo = _provider().parse_repo_ref(
            "https://dev.azure.com/org/proj/_git/repo.git"
        )
        self.assertEqual(repo.name, "repo")

    def test_ssh_v3_url(self):
        repo = _provider().parse_repo_ref(
            "git@ssh.dev.azure.com:v3/org/proj/repo"
        )
        self.assertEqual(repo.workspace, "org/proj")
        self.assertEqual(repo.name, "repo")

    def test_legacy_visualstudio_url(self):
        repo = _provider().parse_repo_ref(
            "https://org.visualstudio.com/proj/_git/repo"
        )
        self.assertEqual(repo.workspace, "org/proj")
        self.assertEqual(repo.name, "repo")

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            _provider().parse_repo_ref("not-a-remote-url")


class TestCreatePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_success_maps_azure_fields(self, mock_post):
        mock_post.return_value = _response(201, _pr_object(pr_id=7))

        result = _provider().create_pull_request(_repo(), _pr_request())

        # The browser URL is derived (the API "url" field is an _apis URL).
        self.assertEqual(
            result.url, "https://dev.azure.com/org/proj/_git/repo/pullrequest/7"
        )
        self.assertEqual(result.number, 7)
        self.assertEqual(result.id, 7)
        self.assertEqual(result.state, "active")
        self.assertEqual(result.source_branch, "feature")
        self.assertEqual(result.target_branch, "main")
        self.assertEqual(result.provider, "azure_devops")

    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_request_shape_is_correct(self, mock_post):
        mock_post.return_value = _response(201, _pr_object())

        _provider().create_pull_request(_repo(), _pr_request())

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{API_BASE}/pullrequests")
        self.assertEqual(kwargs["auth"], ("", TOKEN))
        self.assertEqual(kwargs["headers"]["Accept"], "application/json")
        self.assertEqual(kwargs["params"], {"api-version": "7.1"})
        self.assertEqual(
            kwargs["json"],
            {
                "sourceRefName": "refs/heads/feature",
                "targetRefName": "refs/heads/main",
                "title": "Title",
                "description": "Body",
            },
        )
        self.assertEqual(kwargs["timeout"], 30)

    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_repo_name_is_quoted(self, mock_post):
        mock_post.return_value = _response(201, _pr_object())

        _provider().create_pull_request(_repo(name="my repo"), _pr_request())

        args, kwargs = mock_post.call_args
        self.assertIn("repositories/my%20repo/pullrequests", args[0])

    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_error_message_is_flattened(self, mock_post):
        mock_post.return_value = _response(
            400, {"message": "TF401027: permission denied"}
        )

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 400)
        self.assertEqual(ctx.exception.message, "TF401027: permission denied")

    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_unauthorized_401_raises(self, mock_post):
        mock_post.return_value = _response(401, {"message": "TF400813: unauthorized"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 401)
        self.assertEqual(ctx.exception.provider, "azure_devops")

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_connection_error_raises_status_zero(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("Cannot create the pull request", ctx.exception.message)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_timeout_names_the_provider(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("Azure DevOps API timeout", ctx.exception.message)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_unexpected_exception_is_contained(self, mock_post):
        mock_post.side_effect = RuntimeError("boom")

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("Azure DevOps", ctx.exception.message)
        self.assertIn("boom", ctx.exception.message)


class TestCheckExistingPr(unittest.TestCase):
    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_existing_pr_found(self, mock_get):
        mock_get.return_value = _response(200, {"value": [_pr_object(pr_id=3)]})

        result = _provider().check_existing_pull_request(_repo(), "feature")

        self.assertIsNotNone(result)
        self.assertEqual(result.number, 3)
        self.assertEqual(result.source_branch, "feature")
        self.assertEqual(
            result.url, "https://dev.azure.com/org/proj/_git/repo/pullrequest/3"
        )

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_no_open_pr_returns_none(self, mock_get):
        mock_get.return_value = _response(200, {"value": []})

        self.assertIsNone(_provider().check_existing_pull_request(_repo(), "feature"))

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_queries_active_status_and_source_branch(self, mock_get):
        mock_get.return_value = _response(200, {"value": []})

        _provider().check_existing_pull_request(_repo(), "feat/novo")

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {
                "searchCriteria.status": "active",
                "searchCriteria.sourceRefName": "refs/heads/feat/novo",
                "api-version": "7.1",
            },
        )

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_filters_out_other_source_branch(self, mock_get):
        mock_get.return_value = _response(
            200, {"value": [_pr_object(pr_id=9, sourceRefName="refs/heads/other")]}
        )

        self.assertIsNone(_provider().check_existing_pull_request(_repo(), "feature"))

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_error_raises(self, mock_get):
        mock_get.return_value = _response(404, {"message": "repo not found"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().check_existing_pull_request(_repo(), "feature")
        self.assertEqual(ctx.exception.http_status, 404)


class TestUpdatePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.azure_devops_provider.requests.patch")
    def test_success(self, mock_patch):
        mock_patch.return_value = _response(
            200, _pr_object(pr_id=3, title="New title")
        )

        result = _provider().update_pull_request(_repo(), 3, title="New title")

        self.assertEqual(result.number, 3)
        args, kwargs = mock_patch.call_args
        self.assertEqual(args[0], f"{API_BASE}/pullrequests/3")
        self.assertEqual(kwargs["json"], {"title": "New title"})
        self.assertEqual(kwargs["auth"], ("", TOKEN))

    @patch("src.infrastructure.scm.azure_devops_provider.requests.patch")
    def test_only_provided_fields_are_sent(self, mock_patch):
        mock_patch.return_value = _response(200, _pr_object())

        _provider().update_pull_request(_repo(), 3, description="only body")

        self.assertEqual(
            mock_patch.call_args.kwargs["json"], {"description": "only body"}
        )

    @patch("src.infrastructure.scm.azure_devops_provider.requests.patch")
    def test_error_raises(self, mock_patch):
        mock_patch.return_value = _response(404, {"message": "PR not found"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().update_pull_request(_repo(), 3, title="T")
        self.assertEqual(ctx.exception.http_status, 404)


class TestMergePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.azure_devops_provider.requests.patch")
    def test_default_strategy_maps_merge_to_no_fast_forward(self, mock_patch):
        mock_patch.return_value = _response(200, {"status": "completed"})

        result = _provider().merge_pull_request(_repo(), 3)

        self.assertIsNone(result)
        args, kwargs = mock_patch.call_args
        self.assertEqual(args[0], f"{API_BASE}/pullrequests/3")
        self.assertEqual(
            kwargs["json"],
            {
                "status": "completed",
                "completionOptions": {"mergeStrategy": "noFastForward"},
            },
        )

    @patch("src.infrastructure.scm.azure_devops_provider.requests.patch")
    def test_squash_strategy_is_passed_through(self, mock_patch):
        mock_patch.return_value = _response(200, {"status": "completed"})

        _provider().merge_pull_request(_repo(), 3, strategy="squash")

        self.assertEqual(
            mock_patch.call_args.kwargs["json"]["completionOptions"]["mergeStrategy"],
            "squash",
        )

    @patch("src.infrastructure.scm.azure_devops_provider.requests.patch")
    def test_conflict_405_raises(self, mock_patch):
        mock_patch.return_value = _response(405, {"message": "conflict"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().merge_pull_request(_repo(), 3)
        self.assertEqual(ctx.exception.http_status, 405)


class TestGetPullRequestDiff(unittest.TestCase):
    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_no_iterations_returns_empty_string(self, mock_get):
        mock_get.return_value = _response(200, {"value": []})

        self.assertEqual(_provider().get_pull_request_diff(_repo(), 3), "")

        # Only the iterations listing is fetched — never the changes endpoint.
        self.assertEqual(mock_get.call_count, 1)
        self.assertTrue(mock_get.call_args[0][0].endswith("/pullrequests/3/iterations"))

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_summarizes_last_iteration_changes(self, mock_get):
        mock_get.side_effect = [
            _response(200, {"value": [{"id": 1}, {"id": 2}]}),
            _response(
                200,
                {
                    "changeEntries": [
                        {"item": {"path": "/x.py"}, "additions": 5, "deletions": 2},
                        {"item": {"path": "/y.py"}, "additions": 0, "deletions": 3},
                    ]
                },
            ),
        ]

        diff = _provider().get_pull_request_diff(_repo(), 3)

        self.assertEqual(diff, "/x.py (+5 -2)\n/y.py (+0 -3)")
        # The changes call targets the LATEST iteration (id 2).
        changes_url = mock_get.call_args_list[1][0][0]
        self.assertTrue(changes_url.endswith("/pullrequests/3/iterations/2/changes"))

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_empty_change_entries(self, mock_get):
        mock_get.side_effect = [
            _response(200, {"value": [{"id": 1}]}),
            _response(200, {"changeEntries": []}),
        ]

        self.assertEqual(_provider().get_pull_request_diff(_repo(), 3), "")


class TestListOpenPullRequests(unittest.TestCase):
    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_maps_value_list(self, mock_get):
        mock_get.return_value = _response(
            200,
            {
                "value": [
                    _pr_object(pr_id=3),
                    _pr_object(
                        pr_id=5,
                        sourceRefName="refs/heads/feat/b",
                        targetRefName="refs/heads/dev",
                    ),
                ]
            },
        )

        results = _provider().list_open_pull_requests(_repo())

        self.assertEqual(len(results), 2)
        self.assertEqual(results[1].number, 5)
        self.assertEqual(results[1].source_branch, "feat/b")
        self.assertEqual(results[1].target_branch, "dev")
        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {"searchCriteria.status": "active", "api-version": "7.1"},
        )

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_empty_list(self, mock_get):
        mock_get.return_value = _response(200, {"value": []})

        self.assertEqual(_provider().list_open_pull_requests(_repo()), [])


class TestAddComment(unittest.TestCase):
    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_posts_thread_payload(self, mock_post):
        mock_post.return_value = _response(201, {"id": 42})

        _provider().add_comment(_repo(), 3, "Nice work")

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{API_BASE}/pullrequests/3/threads")
        self.assertEqual(
            kwargs["json"],
            {"comments": [{"content": "Nice work", "commentType": 1}], "status": 1},
        )
        self.assertEqual(kwargs["auth"], ("", TOKEN))

    @patch("src.infrastructure.scm.azure_devops_provider.requests.post")
    def test_error_raises(self, mock_post):
        mock_post.return_value = _response(404, {"message": "not found"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().add_comment(_repo(), 3, "x")
        self.assertEqual(ctx.exception.http_status, 404)


class TestCreateIssue(unittest.TestCase):
    def test_raises_not_supported(self):
        # Azure DevOps has work items, not issues — the UI saves the draft
        # locally (F2) and the user opens it on the website.
        with self.assertRaises(ScmNotSupportedError) as ctx:
            _provider().create_issue(_repo(), IssueRequest(title="T", description="D"))
        self.assertEqual(ctx.exception.provider, "azure_devops")
        self.assertEqual(ctx.exception.http_status, 0)


class TestTestConnection(unittest.TestCase):
    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_valid_token_returns_true(self, mock_get):
        mock_get.return_value = _response(200, {"id": "guid", "name": PROJECT})

        self.assertTrue(_provider().test_connection())

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_url_auth_params_and_timeout(self, mock_get):
        mock_get.return_value = _response(200, {"id": "guid", "name": PROJECT})

        _provider().test_connection()

        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://dev.azure.com/org/_apis/projects/proj")
        self.assertEqual(kwargs["params"], {"api-version": "7.1"})
        self.assertEqual(kwargs["auth"], ("", TOKEN))
        self.assertEqual(kwargs["timeout"], 10)

    @patch("src.infrastructure.scm.azure_devops_provider.requests.get")
    def test_invalid_token_raises(self, mock_get):
        mock_get.return_value = _response(401, {"message": "TF400813: unauthorized"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().test_connection()
        self.assertEqual(ctx.exception.http_status, 401)


class TestNoNetworkOrCredentials(unittest.TestCase):
    """Every entry point must fail closed when requests itself blows up.

    create_issue is absent on purpose: it raises ScmNotSupportedError before
    any request is attempted.
    """

    def test_all_endpoints_raise_scm_provider_error(self):
        calls = [
            ("post", lambda: _provider().create_pull_request(_repo(), _pr_request())),
            ("post", lambda: _provider().add_comment(_repo(), 1, "c")),
            ("patch", lambda: _provider().update_pull_request(_repo(), 1, title="t")),
            ("patch", lambda: _provider().merge_pull_request(_repo(), 1)),
            ("get", lambda: _provider().check_existing_pull_request(_repo(), "f")),
            ("get", lambda: _provider().get_pull_request_diff(_repo(), 1)),
            ("get", lambda: _provider().list_open_pull_requests(_repo())),
            ("get", lambda: _provider().test_connection()),
        ]
        for verb, call in calls:
            with patch(
                f"src.infrastructure.scm.azure_devops_provider.requests.{verb}",
                side_effect=Exception("x"),
            ):
                with self.assertRaises(ScmProviderError) as ctx:
                    call()
            self.assertEqual(
                ctx.exception.http_status, 0, f"{verb} should report status 0"
            )


if __name__ == "__main__":
    unittest.main()
