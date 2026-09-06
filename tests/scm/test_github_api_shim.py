"""Tests for the deprecated github_api shim over GitHubProvider.

The shim exists only so external integrations that import github_api directly
keep working: identical signatures, identical legacy (ok, data, http_status)
tuples, and a DeprecationWarning on every call. Internal code no longer uses
this module — the provider tests live in test_github_provider.py.
"""
import unittest
from unittest.mock import patch

import requests

from src.github_api import (
    check_existing_pr,
    create_pull_request,
    _extract_error_message,
    merge_pull_request,
    update_pull_request,
)

REPO = "natanfiuza/gitpr"
TOKEN = "ghp_faketoken"


def _response(status_code, json_data=None, text="", raises=None):
    resp = unittest.mock.MagicMock()
    resp.status_code = status_code
    resp.text = text
    if raises is not None:
        resp.json.side_effect = raises
    else:
        resp.json.return_value = json_data if json_data is not None else {}
    return resp


class TestCreatePullRequestShim(unittest.TestCase):
    def _call(self):
        return create_pull_request(
            REPO, TOKEN, "Title", "Body", "feature", "main"
        )

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_success_delegates_and_returns_legacy_tuple(self, mock_post):
        mock_post.return_value = _response(
            201, {"html_url": "https://github.com/x/y/pull/7", "number": 7}
        )

        ok, data, status = self._call()

        self.assertTrue(ok)
        self.assertEqual(data["url"], "https://github.com/x/y/pull/7")
        self.assertEqual(data["number"], 7)
        self.assertEqual(status, 201)

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_forwards_payload_verbatim(self, mock_post):
        mock_post.return_value = _response(201, {"html_url": "u", "number": 1})

        self._call()

        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0], f"https://api.github.com/repos/{REPO}/pulls"
        )
        self.assertEqual(
            kwargs["json"],
            {"title": "Title", "body": "Body", "head": "feature", "base": "main"},
        )

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_error_maps_back_to_tuple(self, mock_post):
        mock_post.return_value = _response(401, {"message": "Bad credentials"})

        ok, data, status = self._call()

        self.assertFalse(ok)
        self.assertEqual(data["message"], "Bad credentials")
        self.assertEqual(status, 401)

    @patch("src.i18n.TRANSLATIONS", {})
    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_network_failure_maps_to_status_zero(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()

        ok, data, status = self._call()

        self.assertFalse(ok)
        self.assertIn("No internet connection", data["message"])
        self.assertEqual(status, 0)

    def test_raises_deprecation_warning(self):
        with self.assertWarns(DeprecationWarning):
            with patch(
                "src.infrastructure.scm.github_provider.requests.post",
                return_value=_response(201, {"html_url": "u", "number": 1}),
            ):
                self._call()


class TestCheckExistingPrShim(unittest.TestCase):
    def test_raises_deprecation_warning(self):
        with self.assertWarns(DeprecationWarning):
            with patch(
                "src.infrastructure.scm.github_provider.requests.get",
                return_value=_response(200, []),
            ):
                check_existing_pr(REPO, TOKEN, "feature")

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_found_pr_returns_tuple(self, mock_get):
        mock_get.return_value = _response(
            200, [{"html_url": "https://github.com/x/y/pull/3", "number": 3}]
        )

        self.assertEqual(
            check_existing_pr(REPO, TOKEN, "feature"), (True, "https://github.com/x/y/pull/3", 3)
        )

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_no_open_pr_degrades_to_false(self, mock_get):
        mock_get.return_value = _response(200, [])

        self.assertEqual(check_existing_pr(REPO, TOKEN, "feature"), (False, None, None))

    @patch("src.infrastructure.scm.github_provider.requests.get")
    def test_error_degrades_to_false(self, mock_get):
        mock_get.return_value = _response(500, {"message": "boom"})

        self.assertEqual(check_existing_pr(REPO, TOKEN, "feature"), (False, None, None))


class TestUpdatePullRequestShim(unittest.TestCase):
    def test_raises_deprecation_warning(self):
        with self.assertWarns(DeprecationWarning):
            with patch(
                "src.infrastructure.scm.github_provider.requests.patch",
                return_value=_response(200, {"html_url": "u", "number": 3}),
            ):
                update_pull_request(REPO, TOKEN, 3, title="T")

    @patch("src.infrastructure.scm.github_provider.requests.patch")
    def test_success_returns_tuple(self, mock_patch):
        mock_patch.return_value = _response(
            200, {"html_url": "https://github.com/x/y/pull/3", "number": 3}
        )

        ok, data, status = update_pull_request(REPO, TOKEN, 3, title="T")

        self.assertTrue(ok)
        self.assertEqual(data["number"], 3)
        self.assertEqual(status, 200)

    @patch("src.infrastructure.scm.github_provider.requests.patch")
    def test_only_provided_fields_forwarded(self, mock_patch):
        mock_patch.return_value = _response(200, {"html_url": "u", "number": 3})

        update_pull_request(REPO, TOKEN, 3, body="only body")

        self.assertEqual(
            mock_patch.call_args.kwargs["json"], {"body": "only body"}
        )

    @patch("src.infrastructure.scm.github_provider.requests.patch")
    def test_error_maps_back_to_tuple(self, mock_patch):
        mock_patch.return_value = _response(404, {"message": "Not Found"})

        ok, data, status = update_pull_request(REPO, TOKEN, 3, title="T")

        self.assertFalse(ok)
        self.assertEqual(data["message"], "Not Found")
        self.assertEqual(status, 404)


class TestMergePullRequestShim(unittest.TestCase):
    def test_raises_deprecation_warning(self):
        with self.assertWarns(DeprecationWarning):
            with patch(
                "src.infrastructure.scm.github_provider.requests.put",
                return_value=_response(200, {"merged": True}),
            ):
                merge_pull_request(REPO, TOKEN, 3)

    @patch("src.infrastructure.scm.github_provider.requests.put")
    def test_success_returns_legacy_tuple(self, mock_put):
        mock_put.return_value = _response(200, {"merged": True})

        ok, data, status = merge_pull_request(REPO, TOKEN, 3)

        self.assertTrue(ok)
        self.assertTrue(data["merged"])
        self.assertEqual(status, 200)

    @patch("src.infrastructure.scm.github_provider.requests.put")
    def test_conflict_maps_back_to_tuple(self, mock_put):
        mock_put.return_value = _response(405, {"message": "Pull Request is not mergeable"})

        ok, data, status = merge_pull_request(REPO, TOKEN, 3)

        self.assertFalse(ok)
        self.assertIn("not mergeable", data["message"])
        self.assertEqual(status, 405)


class TestExtractErrorMessageReexport(unittest.TestCase):
    def test_module_level_helper_is_importable_from_shim(self):
        """External code may import the helper from either module."""
        from src.infrastructure.scm.github_provider import (
            _extract_error_message as provider_helper,
        )

        self.assertIs(_extract_error_message, provider_helper)

    def test_helper_extracts_field_errors(self):
        resp = _response(
            422,
            {"message": "Validation Failed", "errors": [{"field": "head", "message": "x"}]},
        )
        self.assertEqual(_extract_error_message(resp), "Validation Failed [head: x]")


if __name__ == "__main__":
    unittest.main()
