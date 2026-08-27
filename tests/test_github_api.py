"""Unit tests for src/github_api.py — the GitHub REST layer.

Every HTTP call is mocked: no test here touches the network or needs a real
Personal Access Token. TRANSLATIONS is pinned to {} where a test asserts on
user-facing English text, so results do not depend on the machine's locale.
"""
import unittest
from unittest.mock import patch, MagicMock

import requests

from src.github_api import (
    _extract_error_message,
    check_existing_pr,
    create_pull_request,
    merge_pull_request,
    update_pull_request,
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

    @patch("src.github_api.requests.post")
    def test_success_returns_url_and_number(self, mock_post):
        mock_post.return_value = _response(
            201, {"html_url": "https://github.com/x/y/pull/7", "number": 7}
        )

        ok, data, status = create_pull_request(
            REPO, TOKEN, "Title", "Body", "feature", "main"
        )

        self.assertTrue(ok)
        self.assertEqual(status, 201)
        self.assertEqual(data, {"url": "https://github.com/x/y/pull/7", "number": 7})

    @patch("src.github_api.requests.post")
    def test_request_shape_is_correct(self, mock_post):
        mock_post.return_value = _response(201, {"html_url": "u", "number": 1})

        create_pull_request(REPO, TOKEN, "Title", "Body", "feature", "main")

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"https://api.github.com/repos/{REPO}/pulls")
        self.assertEqual(kwargs["headers"]["Authorization"], f"token {TOKEN}")
        self.assertEqual(
            kwargs["json"],
            {"title": "Title", "body": "Body", "head": "feature", "base": "main"},
        )
        self.assertEqual(kwargs["timeout"], 30)

    @patch("src.github_api.requests.post")
    def test_auth_failure_401_is_reported(self, mock_post):
        mock_post.return_value = _response(401, {"message": "Bad credentials"})

        ok, data, status = create_pull_request(
            REPO, TOKEN, "T", "B", "feature", "main"
        )

        self.assertFalse(ok)
        self.assertEqual(status, 401)
        self.assertEqual(data["message"], "Bad credentials")

    @patch("src.github_api.requests.post")
    def test_forbidden_403_is_reported(self, mock_post):
        mock_post.return_value = _response(
            403, {"message": "Resource not accessible by personal access token"}
        )

        ok, data, status = create_pull_request(
            REPO, TOKEN, "T", "B", "feature", "main"
        )

        self.assertFalse(ok)
        self.assertEqual(status, 403)
        self.assertIn("not accessible", data["message"])

    @patch("src.github_api.requests.post")
    def test_rate_limit_403_surfaces_github_message(self, mock_post):
        """Rate limiting arrives as 403 with an explanatory message."""
        mock_post.return_value = _response(
            403, {"message": "API rate limit exceeded for user ID 1."}
        )

        ok, data, status = create_pull_request(
            REPO, TOKEN, "T", "B", "feature", "main"
        )

        self.assertFalse(ok)
        self.assertEqual(status, 403)
        self.assertIn("rate limit exceeded", data["message"])

    @patch("src.github_api.requests.post")
    def test_validation_422_includes_field_detail(self, mock_post):
        mock_post.return_value = _response(
            422,
            {
                "message": "Validation Failed",
                "errors": [{"field": "head", "message": "No commits between"}],
            },
        )

        ok, data, status = create_pull_request(
            REPO, TOKEN, "T", "B", "feature", "main"
        )

        self.assertFalse(ok)
        self.assertEqual(status, 422)
        self.assertIn("head", data["message"])

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.github_api.requests.post")
    def test_connection_error_returns_status_zero(self, mock_post):
        """status 0 is the documented 'no HTTP response' sentinel."""
        mock_post.side_effect = requests.exceptions.ConnectionError()

        ok, data, status = create_pull_request(
            REPO, TOKEN, "T", "B", "feature", "main"
        )

        self.assertFalse(ok)
        self.assertEqual(status, 0)
        self.assertIn("No internet connection", data["message"])

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.github_api.requests.post")
    def test_timeout_returns_status_zero(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()

        ok, data, status = create_pull_request(
            REPO, TOKEN, "T", "B", "feature", "main"
        )

        self.assertFalse(ok)
        self.assertEqual(status, 0)
        self.assertIn("timeout", data["message"].lower())

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.github_api.requests.post")
    def test_unexpected_exception_is_contained(self, mock_post):
        """An unforeseen error must never escape as a traceback into the TUI."""
        mock_post.side_effect = RuntimeError("boom")

        ok, data, status = create_pull_request(
            REPO, TOKEN, "T", "B", "feature", "main"
        )

        self.assertFalse(ok)
        self.assertEqual(status, 0)
        self.assertIn("boom", data["message"])


class TestCheckExistingPr(unittest.TestCase):
    """Tests for the pre-push duplicate-PR probe."""

    @patch("src.github_api.requests.get")
    def test_existing_pr_found(self, mock_get):
        mock_get.return_value = _response(
            200, [{"html_url": "https://github.com/x/y/pull/3", "number": 3}]
        )

        exists, url, number = check_existing_pr(REPO, TOKEN, "feature")

        self.assertTrue(exists)
        self.assertEqual(url, "https://github.com/x/y/pull/3")
        self.assertEqual(number, 3)

    @patch("src.github_api.requests.get")
    def test_no_open_pr_returns_false(self, mock_get):
        mock_get.return_value = _response(200, [])

        self.assertEqual(check_existing_pr(REPO, TOKEN, "feature"), (False, None, None))

    @patch("src.github_api.requests.get")
    def test_head_param_is_namespaced_by_owner(self, mock_get):
        mock_get.return_value = _response(200, [])

        check_existing_pr(REPO, TOKEN, "feature")

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {"head": "natanfiuza:feature", "state": "open"},
        )

    @patch("src.github_api.requests.get")
    def test_non_200_returns_false(self, mock_get):
        mock_get.return_value = _response(404, {"message": "Not Found"})

        self.assertEqual(check_existing_pr(REPO, TOKEN, "feature"), (False, None, None))

    @patch("src.github_api.requests.get")
    def test_network_failure_degrades_to_false(self, mock_get):
        """A failed probe must not block publishing — it degrades to 'no PR'."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        self.assertEqual(check_existing_pr(REPO, TOKEN, "feature"), (False, None, None))


class TestUpdatePullRequest(unittest.TestCase):
    """Tests for updating an existing PR's title/body."""

    @patch("src.github_api.requests.patch")
    def test_success(self, mock_patch):
        mock_patch.return_value = _response(
            200, {"html_url": "https://github.com/x/y/pull/3", "number": 3}
        )

        ok, data, status = update_pull_request(REPO, TOKEN, 3, title="T", body="B")

        self.assertTrue(ok)
        self.assertEqual(status, 200)
        self.assertEqual(data["number"], 3)

    @patch("src.github_api.requests.patch")
    def test_only_provided_fields_are_sent(self, mock_patch):
        """Omitted fields must not be blanked out on GitHub."""
        mock_patch.return_value = _response(200, {"html_url": "u", "number": 3})

        update_pull_request(REPO, TOKEN, 3, body="only body")

        self.assertEqual(mock_patch.call_args.kwargs["json"], {"body": "only body"})

    @patch("src.github_api.requests.patch")
    def test_url_targets_the_pr_number(self, mock_patch):
        mock_patch.return_value = _response(200, {"html_url": "u", "number": 42})

        update_pull_request(REPO, TOKEN, 42, title="T")

        self.assertEqual(
            mock_patch.call_args[0][0],
            f"https://api.github.com/repos/{REPO}/pulls/42",
        )

    @patch("src.github_api.requests.patch")
    def test_error_status_is_propagated(self, mock_patch):
        mock_patch.return_value = _response(404, {"message": "Not Found"})

        ok, data, status = update_pull_request(REPO, TOKEN, 3, title="T")

        self.assertFalse(ok)
        self.assertEqual(status, 404)
        self.assertEqual(data["message"], "Not Found")

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.github_api.requests.patch")
    def test_connection_error_returns_status_zero(self, mock_patch):
        mock_patch.side_effect = requests.exceptions.ConnectionError()

        ok, data, status = update_pull_request(REPO, TOKEN, 3, title="T")

        self.assertFalse(ok)
        self.assertEqual(status, 0)


class TestMergePullRequest(unittest.TestCase):
    """Tests for the merge call, including the conflict path."""

    @patch("src.github_api.requests.put")
    def test_merge_success(self, mock_put):
        mock_put.return_value = _response(
            200, {"merged": True, "message": "Pull Request successfully merged"}
        )

        ok, data, status = merge_pull_request(REPO, TOKEN, 3)

        self.assertTrue(ok)
        self.assertEqual(status, 200)
        self.assertTrue(data["merged"])

    @patch("src.github_api.requests.put")
    def test_merge_conflict_405_is_reported(self, mock_put):
        """405 is what GitHub returns when the PR is not mergeable."""
        mock_put.return_value = _response(405, {"message": "Pull Request is not mergeable"})

        ok, data, status = merge_pull_request(REPO, TOKEN, 3)

        self.assertFalse(ok)
        self.assertEqual(status, 405)
        self.assertIn("not mergeable", data["message"])

    @patch("src.github_api.requests.put")
    def test_sha_mismatch_409_is_reported(self, mock_put):
        mock_put.return_value = _response(409, {"message": "Head branch was modified"})

        ok, data, status = merge_pull_request(REPO, TOKEN, 3)

        self.assertFalse(ok)
        self.assertEqual(status, 409)

    @patch("src.github_api.requests.put")
    def test_merge_url_is_correct(self, mock_put):
        mock_put.return_value = _response(200, {"merged": True})

        merge_pull_request(REPO, TOKEN, 9)

        self.assertEqual(
            mock_put.call_args[0][0],
            f"https://api.github.com/repos/{REPO}/pulls/9/merge",
        )

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.github_api.requests.put")
    def test_connection_error_returns_status_zero(self, mock_put):
        mock_put.side_effect = requests.exceptions.ConnectionError()

        ok, data, status = merge_pull_request(REPO, TOKEN, 3)

        self.assertFalse(ok)
        self.assertEqual(status, 0)


class TestNoNetworkOrCredentials(unittest.TestCase):
    """Every entry point must fail closed when requests itself blows up."""

    def test_all_endpoints_contain_exceptions(self):
        calls = [
            ("post", lambda: create_pull_request(REPO, TOKEN, "T", "B", "h", "b")),
            ("patch", lambda: update_pull_request(REPO, TOKEN, 1, title="T")),
            ("put", lambda: merge_pull_request(REPO, TOKEN, 1)),
        ]
        for verb, call in calls:
            with patch(f"src.github_api.requests.{verb}", side_effect=Exception("x")):
                with patch("src.i18n.TRANSLATIONS", {}):
                    ok, data, status = call()
            self.assertFalse(ok, f"{verb} should fail closed")
            self.assertEqual(status, 0, f"{verb} should report status 0")
            self.assertIn("message", data)


if __name__ == "__main__":
    unittest.main()
