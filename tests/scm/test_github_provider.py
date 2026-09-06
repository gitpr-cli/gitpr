"""Unit tests for GitHubProvider — migrated 1:1 from tests/test_github_api.py.

Convention change (approved in the multi-forge design): HTTP/network failures
RAISE ScmProviderError instead of the legacy (ok, data, status) tuples, so the
old "returns False" scenarios assert on the raised error instead. The legacy
tuple surface is preserved only by src/github_api.py (deprecated shim, covered
in test_github_api_shim.py).

Every HTTP call is mocked: no test here touches the network or needs a real
Personal Access Token. TRANSLATIONS is pinned to {} where a test asserts on
user-facing English text, so results do not depend on the machine's locale.
"""
import unittest
from unittest.mock import patch, MagicMock

import requests

from src.infrastructure.scm.base import (
    PullRequestRequest,
    PullRequestResult,
    RepoRef,
    ScmProviderError,
)
from src.infrastructure.scm.github_provider import (
    GitHubProvider,
    _extract_error_message,
)

REPO = "natanfiuza/gitpr"
TOKEN = "ghp_faketoken"


def _response(status_code, json_data=None, text="", raises=None):
    """Builds a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if raises is not None:
        resp.json.side_effect = raises
    else:
        resp.json.return_value = json_data if json_data is not None else {}
    return resp


def _provider(token=TOKEN):
    return GitHubProvider(token=token)


def _repo():
    return RepoRef(raw=REPO, workspace="natanfiuza", name="gitpr", provider="github")


def _pr_request(title="Title", description="Body"):
    return PullRequestRequest(
        title=title,
        description=description,
        source_branch="feature",
        target_branch="main",
    )


class TestExtractErrorMessage(unittest.TestCase):
    """GitHub packs the useful detail into message + errors[]."""

    def test_message_only(self):
        resp = _response(422, {"message": "Validation Failed"})
        self.assertEqual(_extract_error_message(resp), "Validation Failed")

    def test_message_with_field_errors(self):
        resp = _response(
            422,
            {
                "message": "Validation Failed",
                "errors": [{"field": "head", "message": "invalid"}],
            },
        )
        self.assertEqual(
            _extract_error_message(resp), "Validation Failed [head: invalid]"
        )

    def test_error_without_field_is_appended_plain(self):
        resp = _response(
            422,
            {"message": "Bad", "errors": [{"message": "No commits between branches"}]},
        )
        self.assertEqual(
            _extract_error_message(resp), "Bad No commits between branches"
        )

    def test_falls_back_to_raw_text_on_unparseable_body(self):
        resp = _response(500, text="<html>gateway</html>", raises=ValueError("no json"))
        self.assertEqual(_extract_error_message(resp), "<html>gateway</html>")

    def test_empty_payload_falls_back_to_text(self):
        resp = _response(500, {}, text="Server Error")
        self.assertEqual(_extract_error_message(resp), "Server Error")


class TestCreatePullRequest(unittest.TestCase):
    """Tests for PR creation, the happy path and each documented failure."""

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_success_returns_url_and_number(self, mock_post):
        mock_post.return_value = _response(
            201, {"html_url": "https://github.com/x/y/pull/7", "number": 7}
        )

        result = _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(result.url, "https://github.com/x/y/pull/7")
        self.assertEqual(result.number, 7)
        self.assertEqual(result.id, 7)
        self.assertEqual(result.provider, "github")

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_request_shape_is_correct(self, mock_post):
        mock_post.return_value = _response(201, {"html_url": "u", "number": 1})

        _provider().create_pull_request(_repo(), _pr_request())

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"https://api.github.com/repos/{REPO}/pulls")
        self.assertEqual(kwargs["headers"]["Authorization"], f"token {TOKEN}")
        self.assertEqual(
            kwargs["json"],
            {"title": "Title", "body": "Body", "head": "feature", "base": "main"},
        )
        self.assertEqual(kwargs["timeout"], 30)

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_draft_flag_only_when_requested(self, mock_post):
        mock_post.return_value = _response(201, {"html_url": "u", "number": 1})

        _provider().create_pull_request(
            _repo(), _pr_request(title="Draft title", description="")
        )
        _provider().create_pull_request(
            _repo(),
            PullRequestRequest(
                title="D", description="", source_branch="f", target_branch="m", draft=True
            ),
        )

        self.assertNotIn("draft", mock_post.call_args_list[0].kwargs["json"])
        self.assertTrue(mock_post.call_args_list[1].kwargs["json"]["draft"])

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_auth_failure_401_is_reported(self, mock_post):
        mock_post.return_value = _response(401, {"message": "Bad credentials"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 401)
        self.assertEqual(ctx.exception.message, "Bad credentials")
        self.assertEqual(ctx.exception.provider, "github")

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_forbidden_403_is_reported(self, mock_post):
        mock_post.return_value = _response(
            403, {"message": "Resource not accessible by personal access token"}
        )

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 403)
        self.assertIn("not accessible", ctx.exception.message)

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_rate_limit_403_surfaces_github_message(self, mock_post):
        """Rate limiting arrives as 403 with an explanatory message."""
        mock_post.return_value = _response(
            403, {"message": "API rate limit exceeded for user ID 1."}
        )

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 403)
        self.assertIn("rate limit exceeded", ctx.exception.message)

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_validation_422_includes_field_detail(self, mock_post):
        mock_post.return_value = _response(
            422,
            {
                "message": "Validation Failed",
                "errors": [{"field": "head", "message": "No commits between"}],
            },
        )

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 422)
        self.assertIn("head", ctx.exception.message)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_connection_error_raises_status_zero(self, mock_post):
        """http_status 0 is the documented 'no HTTP response' sentinel."""
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("No internet connection", ctx.exception.message)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_timeout_raises_status_zero(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("timeout", ctx.exception.message.lower())

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_unexpected_exception_is_contained(self, mock_post):
        """An unforeseen error must never escape as a traceback into the TUI."""
        mock_post.side_effect = RuntimeError("boom")

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("boom", ctx.exception.message)


class TestCheckExistingPr(unittest.TestCase):
    """Tests for the pre-push duplicate-PR probe.

    Convention change vs the legacy module: HTTP/network failures now raise
    ScmProviderError — swallowing is the UI seam's job (pr_publish_app's
    _check_existing_pull_request wrapper), so a failed probe still degrades to
    "no existing PR" without blocking publishing.
    """

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_existing_pr_found(self, mock_get):
        mock_get.return_value = _response(
            200,
            [
                {
                    "html_url": "https://github.com/x/y/pull/3",
                    "number": 3,
                    "head": {"ref": "feature"},
                    "base": {"ref": "main"},
                }
            ],
        )

        result = _provider().check_existing_pull_request(_repo(), "feature")

        self.assertIsNotNone(result)
        self.assertEqual(result.url, "https://github.com/x/y/pull/3")
        self.assertEqual(result.number, 3)

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_no_open_pr_returns_none(self, mock_get):
        mock_get.return_value = _response(200, [])

        self.assertIsNone(
            _provider().check_existing_pull_request(_repo(), "feature")
        )

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_head_param_is_namespaced_by_owner(self, mock_get):
        mock_get.return_value = _response(200, [])

        _provider().check_existing_pull_request(_repo(), "feature")

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {"head": "natanfiuza:feature", "state": "open"},
        )

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_non_200_raises(self, mock_get):
        mock_get.return_value = _response(404, {"message": "Not Found"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().check_existing_pull_request(_repo(), "feature")
        self.assertEqual(ctx.exception.http_status, 404)

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_network_failure_raises(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().check_existing_pull_request(_repo(), "feature")
        self.assertEqual(ctx.exception.http_status, 0)


class TestUpdatePullRequest(unittest.TestCase):
    """Tests for updating an existing PR's title/body."""

    @patch("src.infrastructure.scm.github_provider.requests.patch")
    def test_success(self, mock_patch):
        mock_patch.return_value = _response(
            200, {"html_url": "https://github.com/x/y/pull/3", "number": 3}
        )

        result = _provider().update_pull_request(_repo(), 3, title="T", description="B")

        self.assertEqual(result.number, 3)
        self.assertEqual(result.url, "https://github.com/x/y/pull/3")

    @patch("src.infrastructure.scm.github_provider.requests.patch")
    def test_only_provided_fields_are_sent(self, mock_patch):
        """Omitted fields must not be blanked out on GitHub."""
        mock_patch.return_value = _response(200, {"html_url": "u", "number": 3})

        _provider().update_pull_request(_repo(), 3, description="only body")

        self.assertEqual(mock_patch.call_args.kwargs["json"], {"body": "only body"})

    @patch("src.infrastructure.scm.github_provider.requests.patch")
    def test_url_targets_the_pr_number(self, mock_patch):
        mock_patch.return_value = _response(200, {"html_url": "u", "number": 42})

        _provider().update_pull_request(_repo(), 42, title="T")

        self.assertEqual(
            mock_patch.call_args[0][0],
            f"https://api.github.com/repos/{REPO}/pulls/42",
        )

    @patch("src.infrastructure.scm.github_provider.requests.patch")
    def test_error_status_raises(self, mock_patch):
        mock_patch.return_value = _response(404, {"message": "Not Found"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().update_pull_request(_repo(), 3, title="T")
        self.assertEqual(ctx.exception.http_status, 404)
        self.assertEqual(ctx.exception.message, "Not Found")

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.github_provider.requests.patch")
    def test_connection_error_raises_status_zero(self, mock_patch):
        mock_patch.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().update_pull_request(_repo(), 3, title="T")
        self.assertEqual(ctx.exception.http_status, 0)


class TestMergePullRequest(unittest.TestCase):
    """Tests for the merge call, including the conflict path."""

    @patch("src.infrastructure.scm.github_provider.requests.put")
    def test_merge_success(self, mock_put):
        mock_put.return_value = _response(
            200, {"merged": True, "message": "Pull Request successfully merged"}
        )

        result = _provider().merge_pull_request(_repo(), 3)

        self.assertIsNone(result)

    @patch("src.infrastructure.scm.github_provider.requests.put")
    def test_merge_conflict_405_is_reported(self, mock_put):
        """405 is what GitHub returns when the PR is not mergeable."""
        mock_put.return_value = _response(405, {"message": "Pull Request is not mergeable"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().merge_pull_request(_repo(), 3)
        self.assertEqual(ctx.exception.http_status, 405)
        self.assertIn("not mergeable", ctx.exception.message)

    @patch("src.infrastructure.scm.github_provider.requests.put")
    def test_sha_mismatch_409_is_reported(self, mock_put):
        mock_put.return_value = _response(409, {"message": "Head branch was modified"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().merge_pull_request(_repo(), 3)
        self.assertEqual(ctx.exception.http_status, 409)

    @patch("src.infrastructure.scm.github_provider.requests.put")
    def test_merge_url_is_correct(self, mock_put):
        mock_put.return_value = _response(200, {"merged": True})

        _provider().merge_pull_request(_repo(), 9)

        self.assertEqual(
            mock_put.call_args[0][0],
            f"https://api.github.com/repos/{REPO}/pulls/9/merge",
        )
        self.assertEqual(mock_put.call_args.kwargs["json"], {})

    @patch("src.infrastructure.scm.github_provider.requests.put")
    def test_custom_merge_strategy_sends_merge_method(self, mock_put):
        mock_put.return_value = _response(200, {"merged": True})

        _provider().merge_pull_request(_repo(), 9, strategy="squash")

        self.assertEqual(
            mock_put.call_args.kwargs["json"], {"merge_method": "squash"}
        )

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.github_provider.requests.put")
    def test_connection_error_raises_status_zero(self, mock_put):
        mock_put.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().merge_pull_request(_repo(), 3)
        self.assertEqual(ctx.exception.http_status, 0)


class TestNoNetworkOrCredentials(unittest.TestCase):
    """Every entry point must fail closed when requests itself blows up."""

    def test_all_endpoints_raise_scm_provider_error(self):
        calls = [
            ("post", lambda: _provider().create_pull_request(_repo(), _pr_request())),
            ("patch", lambda: _provider().update_pull_request(_repo(), 1, title="T")),
            ("put", lambda: _provider().merge_pull_request(_repo(), 1)),
        ]
        for verb, call in calls:
            with patch(
                f"src.infrastructure.scm.github_provider.requests.{verb}",
                side_effect=Exception("x"),
            ):
                with patch("src.i18n.TRANSLATIONS", {}):
                    with self.assertRaises(ScmProviderError) as ctx:
                        call()
            self.assertEqual(
                ctx.exception.http_status, 0, f"{verb} should report status 0"
            )


class TestParseRepoRef(unittest.TestCase):
    def test_https_url(self):
        repo = _provider().parse_repo_ref("https://github.com/owner/repo")
        self.assertEqual(repo.workspace, "owner")
        self.assertEqual(repo.name, "repo")
        self.assertEqual(repo.provider, "github")

    def test_https_url_with_git_suffix(self):
        repo = _provider().parse_repo_ref("https://github.com/owner/repo.git")
        self.assertEqual(repo.name, "repo")

    def test_ssh_url(self):
        repo = _provider().parse_repo_ref("git@github.com:owner/repo.git")
        self.assertEqual(repo.workspace, "owner")
        self.assertEqual(repo.name, "repo")

    def test_trailing_slash(self):
        repo = _provider().parse_repo_ref("https://github.com/owner/repo/")
        self.assertEqual(repo.name, "repo")

    def test_non_github_url_raises(self):
        with self.assertRaises(ValueError):
            _provider().parse_repo_ref("https://gitlab.com/group/proj.git")

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            _provider().parse_repo_ref("not-a-remote-url")


class TestWithToken(unittest.TestCase):
    def test_with_token_rebuilds_instance(self):
        provider = _provider()
        refreshed = provider.with_token("new-token")
        self.assertIs(type(refreshed), GitHubProvider)
        self.assertEqual(refreshed.token, "new-token")
        self.assertEqual(refreshed.base_url, "https://api.github.com")


class TestCreateIssue(unittest.TestCase):
    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = _response(
            201, {"html_url": "https://github.com/x/y/issues/9", "number": 9}
        )

        from src.infrastructure.scm.base import IssueRequest

        result = _provider().create_issue(
            _repo(), IssueRequest(title="Bug", description="Details")
        )

        self.assertEqual(result.url, "https://github.com/x/y/issues/9")
        self.assertEqual(result.number, 9)
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"https://api.github.com/repos/{REPO}/issues")
        self.assertEqual(kwargs["json"], {"title": "Bug", "body": "Details"})

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_unauthorized_raises(self, mock_post):
        from src.infrastructure.scm.base import IssueRequest

        mock_post.return_value = _response(401, {"message": "Bad credentials"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_issue(_repo(), IssueRequest(title="T", description="D"))
        self.assertEqual(ctx.exception.http_status, 401)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_network_failure_raises_status_zero(self, mock_post):
        from src.infrastructure.scm.base import IssueRequest

        mock_post.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_issue(_repo(), IssueRequest(title="T", description="D"))
        self.assertEqual(ctx.exception.http_status, 0)


class TestTestConnection(unittest.TestCase):
    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_valid_token_returns_true(self, mock_get):
        mock_get.return_value = _response(200, {"login": "natanfiuza"})

        self.assertTrue(_provider().test_connection())

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_invalid_token_raises(self, mock_get):
        mock_get.return_value = _response(401, {"message": "Bad credentials"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().test_connection()
        self.assertEqual(ctx.exception.http_status, 401)

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_connection_url_and_timeout(self, mock_get):
        mock_get.return_value = _response(200, {"login": "natanfiuza"})

        _provider().test_connection()

        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://api.github.com/user")
        self.assertEqual(kwargs["timeout"], 10)
        self.assertEqual(
            kwargs["headers"]["Authorization"], f"token {TOKEN}"
        )


class TestListAndCommentAndDiff(unittest.TestCase):
    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_list_open_pull_requests(self, mock_get):
        mock_get.return_value = _response(
            200,
            [
                {
                    "number": 3,
                    "html_url": "https://github.com/x/y/pull/3",
                    "state": "open",
                    "head": {"ref": "feat/a"},
                    "base": {"ref": "main"},
                }
            ],
        )

        results = _provider().list_open_pull_requests(_repo())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].number, 3)
        self.assertEqual(results[0].source_branch, "feat/a")
        self.assertEqual(mock_get.call_args.kwargs["params"], {"state": "open"})

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_add_comment_posts_to_issue_comments(self, mock_post):
        mock_post.return_value = _response(201, {"id": 1})

        _provider().add_comment(_repo(), 3, "Nice work")

        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0], f"https://api.github.com/repos/{REPO}/issues/3/comments"
        )
        self.assertEqual(kwargs["json"], {"body": "Nice work"})

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_get_pull_request_diff_uses_diff_accept_header(self, mock_get):
        mock_get.return_value = _response(200, text="diff --git a/x.py b/x.py")

        diff = _provider().get_pull_request_diff(_repo(), 3)

        self.assertIn("diff --git", diff)
        self.assertEqual(
            mock_get.call_args.kwargs["headers"]["Accept"],
            "application/vnd.github.v3.diff",
        )


if __name__ == "__main__":
    unittest.main()
