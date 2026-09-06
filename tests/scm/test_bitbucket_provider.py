"""Unit tests for BitbucketProvider (Cloud REST 2.0).

Every HTTP call is mocked — no network, no real token. Error scenarios assert
ScmProviderError (the shared convention): http_status carries the HTTP code,
0 means no HTTP response. TRANSLATIONS is pinned to {} wherever user-facing
English text is asserted, so results are locale-independent.

Wire facts asserted throughout (deliberate deviations documented in ADR-001):
  - auth is Basic with the App Password: auth=(username, token)
  - the username comes from the provider extras (fail-fast at construction)
  - PR bodies nest source/destination as {"branch": {"name": ...}}
  - updates are PUT, merges POST .../merge with {"merge_strategy": ...}
  - list/check answers live in values[] with state "OPEN" (uppercase)
"""
import unittest
from unittest.mock import patch, MagicMock

import requests

from src.infrastructure.scm.base import (
    IssueRequest,
    PullRequestRequest,
    RepoRef,
    ScmProviderError,
)
from src.infrastructure.scm.bitbucket_provider import (
    BitbucketProvider,
    _extract_error_message,
)

TOKEN = "bitbucket_app_password"
USERNAME = "natanfiuza"
API_BASE = "https://api.bitbucket.org/2.0"
REPO_URL = f"{API_BASE}/repositories/myworkspace/repo"


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
    kwargs = dict(username=USERNAME, token=TOKEN)
    kwargs.update(overrides)
    return BitbucketProvider(**kwargs)


def _repo():
    return RepoRef(
        raw="https://bitbucket.org/myworkspace/repo.git",
        workspace="myworkspace",
        name="repo",
        provider="bitbucket",
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
        "id": pr_id,
        "title": "Title",
        "state": "OPEN",
        "source": {"branch": {"name": "feature"}},
        "destination": {"branch": {"name": "main"}},
        "links": {
            "html": {"href": f"https://bitbucket.org/myworkspace/repo/pull-requests/{pr_id}"}
        },
    }
    pr.update(overrides)
    return pr


class TestExtractErrorMessage(unittest.TestCase):
    def test_error_message(self):
        resp = _response(404, {"error": {"message": "repo not found"}})
        self.assertEqual(_extract_error_message(resp), "repo not found")

    def test_field_errors_are_appended(self):
        resp = _response(
            400,
            {
                "error": {
                    "message": "error updating pull request",
                    "fields": {"description": ["may not be empty"]},
                }
            },
        )
        self.assertEqual(
            _extract_error_message(resp),
            "error updating pull request (description: ['may not be empty'])",
        )

    def test_falls_back_to_raw_text(self):
        resp = _response(500, text="<html>gateway</html>", raises=ValueError("no json"))
        self.assertEqual(_extract_error_message(resp), "<html>gateway</html>")


class TestInitFailFast(unittest.TestCase):
    def test_missing_username_names_env_var(self):
        with self.assertRaises(ScmProviderError) as ctx:
            BitbucketProvider(token=TOKEN)
        self.assertEqual(ctx.exception.provider, "bitbucket")
        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("GITPR_SCM_USERNAME", str(ctx.exception.message))
        self.assertIn("Bitbucket", str(ctx.exception.message))

    def test_with_token_keeps_extras(self):
        refreshed = _provider().with_token("new-token")
        self.assertIsInstance(refreshed, BitbucketProvider)
        self.assertEqual(refreshed.token, "new-token")
        self.assertEqual(refreshed.extra["username"], USERNAME)


class TestParseRepoRef(unittest.TestCase):
    def test_https_url(self):
        repo = _provider().parse_repo_ref("https://bitbucket.org/myworkspace/repo.git")
        self.assertEqual(repo.workspace, "myworkspace")
        self.assertEqual(repo.name, "repo")
        self.assertEqual(repo.provider, "bitbucket")

    def test_https_without_git_suffix(self):
        repo = _provider().parse_repo_ref("https://bitbucket.org/myworkspace/repo")
        self.assertEqual(repo.name, "repo")

    def test_ssh_url(self):
        repo = _provider().parse_repo_ref("git@bitbucket.org:myworkspace/repo.git")
        self.assertEqual(repo.workspace, "myworkspace")
        self.assertEqual(repo.name, "repo")

    def test_trailing_slash(self):
        repo = _provider().parse_repo_ref("https://bitbucket.org/myworkspace/repo/")
        self.assertEqual(repo.name, "repo")

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            _provider().parse_repo_ref("https://github.com/owner/repo.git")


class TestCreatePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_success_maps_id_and_links(self, mock_post):
        mock_post.return_value = _response(201, _pr_object(pr_id=7))

        result = _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(result.number, 7)
        self.assertEqual(result.id, 7)
        self.assertEqual(
            result.url, "https://bitbucket.org/myworkspace/repo/pull-requests/7"
        )
        self.assertEqual(result.state, "OPEN")
        self.assertEqual(result.source_branch, "feature")
        self.assertEqual(result.target_branch, "main")
        self.assertEqual(result.provider, "bitbucket")

    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_request_shape_is_correct(self, mock_post):
        mock_post.return_value = _response(201, _pr_object())

        _provider().create_pull_request(_repo(), _pr_request())

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{REPO_URL}/pullrequests")
        self.assertEqual(kwargs["auth"], (USERNAME, TOKEN))
        self.assertEqual(kwargs["headers"]["Accept"], "application/json")
        self.assertEqual(
            kwargs["json"],
            {
                "title": "Title",
                "description": "Body",
                "source": {"branch": {"name": "feature"}},
                "destination": {"branch": {"name": "main"}},
            },
        )
        self.assertEqual(kwargs["timeout"], 30)

    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_draft_sent_only_when_requested(self, mock_post):
        mock_post.return_value = _response(201, _pr_object())

        _provider().create_pull_request(_repo(), _pr_request())
        self.assertNotIn("draft", mock_post.call_args.kwargs["json"])

        _provider().create_pull_request(
            _repo(), _pr_request(title="WIP", draft=True)
        )
        self.assertIs(
            mock_post.call_args.kwargs["json"]["draft"], True
        )

    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_field_error_is_flattened(self, mock_post):
        mock_post.return_value = _response(
            400,
            {
                "error": {
                    "message": "error creating pull request",
                    "fields": {"title": ["may not be empty"]},
                }
            },
        )

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 400)
        self.assertIn("error creating pull request", ctx.exception.message)
        self.assertIn("title", ctx.exception.message)

    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_unauthorized_401_raises(self, mock_post):
        mock_post.return_value = _response(
            401, {"error": {"message": "Unauthorized"}}
        )

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 401)
        self.assertEqual(ctx.exception.provider, "bitbucket")

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_connection_error_raises_status_zero(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("Cannot create the pull request", ctx.exception.message)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_timeout_names_the_provider(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("Bitbucket API timeout", ctx.exception.message)


class TestCheckExistingPr(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_existing_pr_found(self, mock_get):
        mock_get.return_value = _response(200, {"values": [_pr_object(pr_id=3)]})

        result = _provider().check_existing_pull_request(_repo(), "feature")

        self.assertIsNotNone(result)
        self.assertEqual(result.number, 3)
        self.assertEqual(result.source_branch, "feature")
        self.assertEqual(
            result.url, "https://bitbucket.org/myworkspace/repo/pull-requests/3"
        )

    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_no_open_pr_returns_none(self, mock_get):
        mock_get.return_value = _response(200, {"values": []})

        self.assertIsNone(_provider().check_existing_pull_request(_repo(), "feature"))

    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_queries_open_state_uppercase(self, mock_get):
        mock_get.return_value = _response(200, {"values": []})

        _provider().check_existing_pull_request(_repo(), "feature")

        self.assertEqual(
            mock_get.call_args.kwargs["params"], {"state": "OPEN"}
        )

    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_filters_out_other_source_branch(self, mock_get):
        mock_get.return_value = _response(
            200,
            {
                "values": [
                    _pr_object(pr_id=9, source={"branch": {"name": "other"}})
                ]
            },
        )

        self.assertIsNone(_provider().check_existing_pull_request(_repo(), "feature"))

    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_error_raises(self, mock_get):
        mock_get.return_value = _response(404, {"error": {"message": "not found"}})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().check_existing_pull_request(_repo(), "feature")
        self.assertEqual(ctx.exception.http_status, 404)


class TestUpdatePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.put")
    def test_success(self, mock_put):
        mock_put.return_value = _response(
            200, _pr_object(pr_id=3, title="New title")
        )

        result = _provider().update_pull_request(_repo(), 3, title="New title")

        self.assertEqual(result.number, 3)
        args, kwargs = mock_put.call_args
        self.assertEqual(args[0], f"{REPO_URL}/pullrequests/3")
        self.assertEqual(kwargs["json"], {"title": "New title"})
        self.assertEqual(kwargs["auth"], (USERNAME, TOKEN))

    @patch("src.infrastructure.scm.bitbucket_provider.requests.put")
    def test_only_provided_fields_are_sent(self, mock_put):
        mock_put.return_value = _response(200, _pr_object())

        _provider().update_pull_request(_repo(), 3, description="only body")

        self.assertEqual(
            mock_put.call_args.kwargs["json"], {"description": "only body"}
        )

    @patch("src.infrastructure.scm.bitbucket_provider.requests.put")
    def test_error_raises(self, mock_put):
        mock_put.return_value = _response(404, {"error": {"message": "not found"}})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().update_pull_request(_repo(), 3, title="T")
        self.assertEqual(ctx.exception.http_status, 404)


class TestMergePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_default_strategy_maps_merge_to_merge_commit(self, mock_post):
        mock_post.return_value = _response(200, {"state": "MERGED"})

        result = _provider().merge_pull_request(_repo(), 3)

        self.assertIsNone(result)
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{REPO_URL}/pullrequests/3/merge")
        self.assertEqual(kwargs["json"], {"merge_strategy": "merge_commit"})

    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_squash_strategy_is_passed_through(self, mock_post):
        mock_post.return_value = _response(200, {"state": "MERGED"})

        _provider().merge_pull_request(_repo(), 3, strategy="squash")

        self.assertEqual(
            mock_post.call_args.kwargs["json"], {"merge_strategy": "squash"}
        )

    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_conflict_409_raises(self, mock_post):
        mock_post.return_value = _response(
            409, {"error": {"message": "conflict"}}
        )

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().merge_pull_request(_repo(), 3)
        self.assertEqual(ctx.exception.http_status, 409)


class TestGetPullRequestDiff(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_returns_plain_diff_text(self, mock_get):
        mock_get.return_value = _response(
            200, text="diff --git a/x.py b/x.py\n+new\n-old"
        )

        diff = _provider().get_pull_request_diff(_repo(), 3)

        self.assertEqual(diff, "diff --git a/x.py b/x.py\n+new\n-old")
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], f"{REPO_URL}/pullrequests/3/diff")
        # The diff endpoint answers text/plain — the Accept header must allow
        # it (Bitbucket answers 415 if only application/json is accepted).
        self.assertIn("text/plain", kwargs["headers"]["Accept"])


class TestListOpenPullRequests(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_maps_values_list(self, mock_get):
        mock_get.return_value = _response(
            200,
            {
                "values": [
                    _pr_object(pr_id=3),
                    _pr_object(
                        pr_id=5,
                        source={"branch": {"name": "feat/b"}},
                        destination={"branch": {"name": "dev"}},
                    ),
                ]
            },
        )

        results = _provider().list_open_pull_requests(_repo())

        self.assertEqual(len(results), 2)
        self.assertEqual(results[1].number, 5)
        self.assertEqual(results[1].source_branch, "feat/b")
        self.assertEqual(results[1].target_branch, "dev")
        self.assertEqual(mock_get.call_args.kwargs["params"], {"state": "OPEN"})

    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_empty_list(self, mock_get):
        mock_get.return_value = _response(200, {"values": []})

        self.assertEqual(_provider().list_open_pull_requests(_repo()), [])


class TestAddComment(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_posts_raw_content_payload(self, mock_post):
        mock_post.return_value = _response(201, {"id": 42})

        _provider().add_comment(_repo(), 3, "Nice work")

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{REPO_URL}/pullrequests/3/comments")
        self.assertEqual(kwargs["json"], {"content": {"raw": "Nice work"}})
        self.assertEqual(kwargs["auth"], (USERNAME, TOKEN))

    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_error_raises(self, mock_post):
        mock_post.return_value = _response(404, {"error": {"message": "not found"}})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().add_comment(_repo(), 3, "x")
        self.assertEqual(ctx.exception.http_status, 404)


class TestCreateIssue(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = _response(
            201,
            {
                "id": 9,
                "title": "Bug",
                "links": {"html": {"href": "https://bitbucket.org/myworkspace/repo/issues/9"}},
            },
        )

        result = _provider().create_issue(
            _repo(), IssueRequest(title="Bug", description="Details")
        )

        self.assertEqual(result.url, "https://bitbucket.org/myworkspace/repo/issues/9")
        self.assertEqual(result.number, 9)
        self.assertEqual(result.id, 9)
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{REPO_URL}/issues")
        self.assertEqual(
            kwargs["json"], {"title": "Bug", "content": {"raw": "Details"}}
        )

    @patch("src.infrastructure.scm.bitbucket_provider.requests.post")
    def test_tracker_disabled_404_raises(self, mock_post):
        # Without the Issue Tracker feature the API answers 404 and the error
        # must reach the UI as a ScmProviderError (ADR-001 deviation note).
        mock_post.return_value = _response(404, {"error": {"message": "not found"}})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_issue(_repo(), IssueRequest(title="T", description="D"))
        self.assertEqual(ctx.exception.http_status, 404)


class TestTestConnection(unittest.TestCase):
    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_valid_token_returns_true(self, mock_get):
        mock_get.return_value = _response(200, {"username": USERNAME})

        self.assertTrue(_provider().test_connection())

    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_url_auth_and_timeout(self, mock_get):
        mock_get.return_value = _response(200, {"username": USERNAME})

        _provider().test_connection()

        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], f"{API_BASE}/user")
        self.assertEqual(kwargs["auth"], (USERNAME, TOKEN))
        self.assertEqual(kwargs["timeout"], 10)

    @patch("src.infrastructure.scm.bitbucket_provider.requests.get")
    def test_invalid_token_raises(self, mock_get):
        mock_get.return_value = _response(401, {"error": {"message": "Unauthorized"}})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().test_connection()
        self.assertEqual(ctx.exception.http_status, 401)


class TestNoNetworkOrCredentials(unittest.TestCase):
    """Every entry point must fail closed when requests itself blows up."""

    def test_all_endpoints_raise_scm_provider_error(self):
        calls = [
            ("post", lambda: _provider().create_pull_request(_repo(), _pr_request())),
            ("post", lambda: _provider().create_issue(_repo(), IssueRequest("t", "d"))),
            ("post", lambda: _provider().add_comment(_repo(), 1, "c")),
            ("post", lambda: _provider().merge_pull_request(_repo(), 1)),
            ("put", lambda: _provider().update_pull_request(_repo(), 1, title="t")),
            ("get", lambda: _provider().check_existing_pull_request(_repo(), "f")),
            ("get", lambda: _provider().get_pull_request_diff(_repo(), 1)),
            ("get", lambda: _provider().list_open_pull_requests(_repo())),
            ("get", lambda: _provider().test_connection()),
        ]
        for verb, call in calls:
            with patch(
                f"src.infrastructure.scm.bitbucket_provider.requests.{verb}",
                side_effect=Exception("x"),
            ):
                with self.assertRaises(ScmProviderError) as ctx:
                    call()
            self.assertEqual(
                ctx.exception.http_status, 0, f"{verb} should report status 0"
            )


if __name__ == "__main__":
    unittest.main()
