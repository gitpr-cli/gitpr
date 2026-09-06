"""Unit tests for GitLabProvider (REST API v4).

Every HTTP call is mocked — no network, no real token. Error scenarios assert
ScmProviderError (the shared convention): http_status carries the HTTP code,
0 means no HTTP response. TRANSLATIONS is pinned to {} wherever user-facing
English text is asserted, so results are locale-independent.
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
from src.infrastructure.scm.gitlab_provider import GitLabProvider, _extract_error_message

TOKEN = "glpat_faketoken"
ENCODED_PROJECT = "group%2Fsubgroup%2Fproject"


def _response(status_code, json_data=None, text="", raises=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if raises is not None:
        resp.json.side_effect = raises
    else:
        resp.json.return_value = json_data if json_data is not None else {}
    return resp


def _provider():
    return GitLabProvider(token=TOKEN)


def _repo():
    return RepoRef(
        raw="https://gitlab.com/group/subgroup/project.git",
        workspace="group/subgroup",
        name="project",
        provider="gitlab",
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


def _mr_object(iid=3, **overrides):
    mr = {
        "id": 1000,
        "iid": iid,
        "web_url": f"https://gitlab.com/group/subgroup/-/merge_requests/{iid}",
        "state": "opened",
        "source_branch": "feature",
        "target_branch": "main",
        "title": "Title",
    }
    mr.update(overrides)
    return mr


class TestExtractErrorMessage(unittest.TestCase):
    def test_plain_string_message(self):
        resp = _response(401, {"message": "401 Unauthorized"})
        self.assertEqual(_extract_error_message(resp), "401 Unauthorized")

    def test_field_error_dict_is_flattened(self):
        resp = _response(422, {"message": {"title": ["has already been taken"]}})
        self.assertEqual(_extract_error_message(resp), "title: has already been taken")

    def test_falls_back_to_raw_text(self):
        resp = _response(500, text="<html>gateway</html>", raises=ValueError("no json"))
        self.assertEqual(_extract_error_message(resp), "<html>gateway</html>")


class TestParseRepoRef(unittest.TestCase):
    def test_subgroups_url(self):
        repo = _provider().parse_repo_ref("https://gitlab.com/group/subgroup/project.git")
        self.assertEqual(repo.workspace, "group/subgroup")
        self.assertEqual(repo.name, "project")
        self.assertEqual(repo.provider, "gitlab")

    def test_plain_namespace(self):
        repo = _provider().parse_repo_ref("https://gitlab.com/owner/repo")
        self.assertEqual(repo.workspace, "owner")
        self.assertEqual(repo.name, "repo")

    def test_ssh_url_with_subgroups(self):
        repo = _provider().parse_repo_ref("git@gitlab.com:group/sub/proj.git")
        self.assertEqual(repo.workspace, "group/sub")
        self.assertEqual(repo.name, "proj")

    def test_self_managed_with_port(self):
        repo = _provider().parse_repo_ref(
            "https://gitlab.empresa.com:8443/grupo/projeto.git"
        )
        self.assertEqual(repo.workspace, "grupo")
        self.assertEqual(repo.name, "projeto")

    def test_trailing_slash(self):
        repo = _provider().parse_repo_ref("https://gitlab.com/group/proj/")
        self.assertEqual(repo.name, "proj")

    def test_single_segment_raises(self):
        with self.assertRaises(ValueError):
            _provider().parse_repo_ref("https://gitlab.com/no_namespace")

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            _provider().parse_repo_ref("not-a-remote-url")


class TestCreatePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_success_maps_iid_and_web_url(self, mock_post):
        mock_post.return_value = _response(201, _mr_object(iid=7))

        result = _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(result.url, "https://gitlab.com/group/subgroup/-/merge_requests/7")
        self.assertEqual(result.number, 7)
        self.assertEqual(result.id, 7)  # iid, never the global id (1000)
        self.assertEqual(result.source_branch, "feature")
        self.assertEqual(result.provider, "gitlab")

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_request_shape_is_correct(self, mock_post):
        mock_post.return_value = _response(201, _mr_object())

        _provider().create_pull_request(_repo(), _pr_request())

        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0],
            f"https://gitlab.com/api/v4/projects/{ENCODED_PROJECT}/merge_requests",
        )
        self.assertEqual(kwargs["headers"]["PRIVATE-TOKEN"], TOKEN)
        self.assertEqual(
            kwargs["json"],
            {
                "title": "Title",
                "description": "Body",
                "source_branch": "feature",
                "target_branch": "main",
            },
        )
        self.assertEqual(kwargs["timeout"], 30)

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_draft_becomes_title_prefix(self, mock_post):
        mock_post.return_value = _response(201, _mr_object())

        _provider().create_pull_request(
            _repo(), _pr_request(title="WIP thing", draft=True)
        )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["title"], "Draft: WIP thing")
        self.assertNotIn("draft", payload)

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_validation_error_422_is_flattened(self, mock_post):
        mock_post.return_value = _response(
            422, {"message": {"title": ["has already been taken"]}}
        )

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 422)
        self.assertIn("title", ctx.exception.message)

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_unauthorized_401_raises(self, mock_post):
        mock_post.return_value = _response(401, {"message": "401 Unauthorized"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 401)
        self.assertEqual(ctx.exception.message, "401 Unauthorized")
        self.assertEqual(ctx.exception.provider, "gitlab")

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_connection_error_raises_status_zero(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("No internet connection", ctx.exception.message)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_timeout_names_the_provider(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("GitLab API timeout", ctx.exception.message)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_unexpected_exception_is_contained(self, mock_post):
        mock_post.side_effect = RuntimeError("boom")

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_pull_request(_repo(), _pr_request())

        self.assertEqual(ctx.exception.http_status, 0)
        self.assertIn("GitLab", ctx.exception.message)
        self.assertIn("boom", ctx.exception.message)


class TestCheckExistingPr(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_existing_mr_found(self, mock_get):
        mock_get.return_value = _response(200, [_mr_object(iid=3)])

        result = _provider().check_existing_pull_request(_repo(), "feature")

        self.assertIsNotNone(result)
        self.assertEqual(result.number, 3)
        self.assertEqual(result.source_branch, "feature")
        self.assertEqual(result.url, "https://gitlab.com/group/subgroup/-/merge_requests/3")

    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_no_open_mr_returns_none(self, mock_get):
        mock_get.return_value = _response(200, [])

        self.assertIsNone(_provider().check_existing_pull_request(_repo(), "feature"))

    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_filters_opened_by_source_branch(self, mock_get):
        mock_get.return_value = _response(200, [])

        _provider().check_existing_pull_request(_repo(), "feat/novo")

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {"state": "opened", "source_branch": "feat/novo"},
        )

    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_error_raises(self, mock_get):
        mock_get.return_value = _response(404, {"message": "404 Project Not Found"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().check_existing_pull_request(_repo(), "feature")
        self.assertEqual(ctx.exception.http_status, 404)


class TestUpdatePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.put")
    def test_success(self, mock_put):
        mock_put.return_value = _response(200, _mr_object(iid=3, title="New title"))

        result = _provider().update_pull_request(_repo(), 3, title="New title")

        self.assertEqual(result.number, 3)
        args, kwargs = mock_put.call_args
        self.assertEqual(
            args[0],
            f"https://gitlab.com/api/v4/projects/{ENCODED_PROJECT}/merge_requests/3",
        )
        self.assertEqual(kwargs["json"], {"title": "New title"})

    @patch("src.infrastructure.scm.gitlab_provider.requests.put")
    def test_only_provided_fields_are_sent(self, mock_put):
        mock_put.return_value = _response(200, _mr_object())

        _provider().update_pull_request(_repo(), 3, description="only body")

        self.assertEqual(mock_put.call_args.kwargs["json"], {"description": "only body"})

    @patch("src.infrastructure.scm.gitlab_provider.requests.put")
    def test_error_raises(self, mock_put):
        mock_put.return_value = _response(404, {"message": "404 Not found"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().update_pull_request(_repo(), 3, title="T")
        self.assertEqual(ctx.exception.http_status, 404)


class TestMergePullRequest(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.put")
    def test_merge_success_hits_merge_endpoint(self, mock_put):
        mock_put.return_value = _response(200, {"state": "merged"})

        result = _provider().merge_pull_request(_repo(), 3)

        self.assertIsNone(result)
        self.assertEqual(
            mock_put.call_args[0][0],
            f"https://gitlab.com/api/v4/projects/{ENCODED_PROJECT}/merge_requests/3/merge",
        )
        self.assertNotIn("json", mock_put.call_args.kwargs)

    @patch("src.infrastructure.scm.gitlab_provider.requests.put")
    def test_conflict_405_raises(self, mock_put):
        mock_put.return_value = _response(405, {"message": "405 Method Not Allowed"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().merge_pull_request(_repo(), 3)
        self.assertEqual(ctx.exception.http_status, 405)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.gitlab_provider.requests.put")
    def test_connection_error_raises_status_zero(self, mock_put):
        mock_put.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().merge_pull_request(_repo(), 3)
        self.assertEqual(ctx.exception.http_status, 0)


class TestGetPullRequestDiff(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_concatenates_change_diffs(self, mock_get):
        mock_get.return_value = _response(
            200,
            {
                "changes": [
                    {"diff": "diff --git a/x.py b/x.py\n+new"},
                    {"diff": "diff --git a/y.py b/y.py\n-old"},
                ]
            },
        )

        diff = _provider().get_pull_request_diff(_repo(), 3)

        self.assertEqual(diff, "diff --git a/x.py b/x.py\n+new\ndiff --git a/y.py b/y.py\n-old")
        self.assertEqual(
            mock_get.call_args[0][0],
            f"https://gitlab.com/api/v4/projects/{ENCODED_PROJECT}/merge_requests/3/changes",
        )

    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_empty_changes_yield_empty_string(self, mock_get):
        mock_get.return_value = _response(200, {"changes": []})

        self.assertEqual(_provider().get_pull_request_diff(_repo(), 3), "")


class TestListOpenPullRequests(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_maps_iid_and_branches(self, mock_get):
        mock_get.return_value = _response(
            200,
            [
                _mr_object(iid=3),
                _mr_object(iid=5, source_branch="feat/b", target_branch="dev"),
            ],
        )

        results = _provider().list_open_pull_requests(_repo())

        self.assertEqual(len(results), 2)
        self.assertEqual(results[1].number, 5)
        self.assertEqual(results[1].source_branch, "feat/b")
        self.assertEqual(results[1].target_branch, "dev")
        self.assertEqual(mock_get.call_args.kwargs["params"], {"state": "opened"})

    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_empty_list(self, mock_get):
        mock_get.return_value = _response(200, [])

        self.assertEqual(_provider().list_open_pull_requests(_repo()), [])


class TestAddComment(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_posts_note_body(self, mock_post):
        mock_post.return_value = _response(201, {"id": 42, "body": "Nice work"})

        _provider().add_comment(_repo(), 3, "Nice work")

        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0],
            f"https://gitlab.com/api/v4/projects/{ENCODED_PROJECT}/merge_requests/3/notes",
        )
        self.assertEqual(kwargs["json"], {"body": "Nice work"})

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_error_raises(self, mock_post):
        mock_post.return_value = _response(404, {"message": "404 Not found"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().add_comment(_repo(), 3, "x")
        self.assertEqual(ctx.exception.http_status, 404)


class TestCreateIssue(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = _response(
            201, {"iid": 9, "web_url": "https://gitlab.com/group/subgroup/-/issues/9"}
        )

        result = _provider().create_issue(
            _repo(), IssueRequest(title="Bug", description="Details")
        )

        self.assertEqual(result.url, "https://gitlab.com/group/subgroup/-/issues/9")
        self.assertEqual(result.number, 9)
        self.assertEqual(result.id, 9)
        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0],
            f"https://gitlab.com/api/v4/projects/{ENCODED_PROJECT}/issues",
        )
        self.assertEqual(kwargs["json"], {"title": "Bug", "description": "Details"})

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_unauthorized_raises(self, mock_post):
        mock_post.return_value = _response(401, {"message": "401 Unauthorized"})

        with self.assertRaises(ScmProviderError) as ctx:
            _provider().create_issue(_repo(), IssueRequest(title="T", description="D"))
        self.assertEqual(ctx.exception.http_status, 401)


class TestTestConnection(unittest.TestCase):
    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_valid_token_returns_true(self, mock_get):
        mock_get.return_value = _response(200, {"username": "natanfiuza"})

        self.assertTrue(_provider().test_connection())

    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_url_timeout_and_header(self, mock_get):
        mock_get.return_value = _response(200, {"username": "natanfiuza"})

        _provider().test_connection()

        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://gitlab.com/api/v4/user")
        self.assertEqual(kwargs["timeout"], 10)
        self.assertEqual(kwargs["headers"]["PRIVATE-TOKEN"], TOKEN)

    @patch("src.infrastructure.scm.gitlab_provider.requests.get")
    def test_invalid_token_raises(self, mock_get):
        mock_get.return_value = _response(401, {"message": "401 Unauthorized"})

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
            ("put", lambda: _provider().merge_pull_request(_repo(), 1)),
            ("get", lambda: _provider().check_existing_pull_request(_repo(), "f")),
            ("get", lambda: _provider().get_pull_request_diff(_repo(), 1)),
            ("get", lambda: _provider().list_open_pull_requests(_repo())),
            ("get", lambda: _provider().test_connection()),
        ]
        for verb, call in calls:
            with patch(
                f"src.infrastructure.scm.gitlab_provider.requests.{verb}",
                side_effect=Exception("x"),
            ):
                with self.assertRaises(ScmProviderError) as ctx:
                    call()
            self.assertEqual(
                ctx.exception.http_status, 0, f"{verb} should report status 0"
            )


if __name__ == "__main__":
    unittest.main()
