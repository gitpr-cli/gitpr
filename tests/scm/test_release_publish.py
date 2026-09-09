"""create_release tests per provider (spec section 8.7).

GitHub and GitLab must hit the correct endpoint with the correct payload
(mocked HTTP); Bitbucket and Azure inherit the non-abstract default that
raises ScmNotSupportedError, without breaking the local changelog flow.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.infrastructure.scm.base import (
    RepoRef,
    ScmNotSupportedError,
    ScmProviderError,
)
from src.infrastructure.scm.azure_devops_provider import AzureDevOpsProvider
from src.infrastructure.scm.bitbucket_provider import BitbucketProvider
from src.infrastructure.scm.github_provider import GitHubProvider
from src.infrastructure.scm.gitlab_provider import GitLabProvider

REPO = "natanfiuza/gitpr"
TOKEN = "fake_token_for_tests"


def _response(status_code, json_data=None, text=""):
    """Builds a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


def _repo(workspace="natanfiuza", name="gitpr"):
    return RepoRef(raw=f"{workspace}/{name}", workspace=workspace, name=name,
                   provider="x")


class TestGitHubCreateRelease(unittest.TestCase):
    def _provider(self):
        return GitHubProvider(token=TOKEN)

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_posts_to_releases_endpoint_with_payload(self, mock_post):
        mock_post.return_value = _response(
            201, {"html_url": "https://github.com/natanfiuza/gitpr/releases/tag/v1.2.0"}
        )

        url = self._provider().create_release(
            _repo(), tag="v1.2.0", title="v1.2.0", body="Body text", draft=True
        )

        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0], f"https://api.github.com/repos/{REPO}/releases"
        )
        self.assertEqual(kwargs["headers"]["Authorization"], f"token {TOKEN}")
        self.assertEqual(
            kwargs["json"],
            {
                "tag_name": "v1.2.0",
                "name": "v1.2.0",
                "body": "Body text",
                "draft": True,
            },
        )
        self.assertEqual(kwargs["timeout"], 30)
        self.assertEqual(
            url, "https://github.com/natanfiuza/gitpr/releases/tag/v1.2.0"
        )

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_no_draft_by_default(self, mock_post):
        mock_post.return_value = _response(201, {"html_url": "u"})
        self._provider().create_release(
            _repo(), tag="1.0.0", title="1.0.0", body="", draft=False
        )
        self.assertFalse(mock_post.call_args.kwargs["json"]["draft"])

    @patch("src.infrastructure.scm.github_provider.requests.post")
    def test_api_failure_raises_scm_error(self, mock_post):
        mock_post.return_value = _response(404, {"message": "Not Found"})
        with self.assertRaises(ScmProviderError) as ctx:
            self._provider().create_release(
                _repo(), tag="x", title="x", body="", draft=False
            )
        self.assertEqual(ctx.exception.http_status, 404)


class TestGitLabCreateRelease(unittest.TestCase):
    def _provider(self):
        return GitLabProvider(token=TOKEN)

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_posts_to_project_releases_with_payload(self, mock_post):
        mock_post.return_value = _response(
            201,
            {
                "tag_name": "v1.2.0",
                "_links": {"self": "https://gitlab.com/api/v4/projects/9/releases/v1.2.0"},
            },
        )

        url = self._provider().create_release(
            _repo(workspace="natan/group", name="proj"),
            tag="v1.2.0",
            title="v1.2.0",
            body="Body text",
        )

        args, kwargs = mock_post.call_args
        # The full namespace is URL-encoded as one path segment.
        self.assertEqual(
            args[0],
            "https://gitlab.com/api/v4/projects/natan%2Fgroup%2Fproj/releases",
        )
        self.assertEqual(kwargs["headers"]["PRIVATE-TOKEN"], TOKEN)
        self.assertEqual(
            kwargs["json"],
            {"tag_name": "v1.2.0", "name": "v1.2.0", "description": "Body text"},
        )
        self.assertNotIn("draft", kwargs["json"])
        self.assertEqual(url, "https://gitlab.com/api/v4/projects/9/releases/v1.2.0")

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_fallback_url_when_no_links(self, mock_post):
        mock_post.return_value = _response(201, {"tag_name": "v1.2.0"})
        url = self._provider().create_release(
            _repo(), tag="v1.2.0", title="t", body="b"
        )
        self.assertEqual(
            url, "https://gitlab.com/natanfiuza/gitpr/-/releases/v1.2.0"
        )

    @patch("src.infrastructure.scm.gitlab_provider.requests.post")
    def test_missing_tag_404_surfaces(self, mock_post):
        mock_post.return_value = _response(
            404, {"message": "Release does not exist"}
        )
        with self.assertRaises(ScmProviderError) as ctx:
            self._provider().create_release(
                _repo(), tag="nope", title="t", body="b"
            )
        self.assertEqual(ctx.exception.http_status, 404)


class TestUnsupportedForgeDefaults(unittest.TestCase):
    """Bitbucket/Azure inherit the base default that raises ScmNotSupportedError."""

    def test_bitbucket_raises_not_supported(self):
        # Bitbucket validates its username extra at construction time.
        provider = BitbucketProvider(token=TOKEN, username="natanfiuza")
        with self.assertRaises(ScmNotSupportedError) as ctx:
            provider.create_release(_repo(), tag="1.0.0", title="t", body="b")
        self.assertEqual(ctx.exception.provider, "bitbucket")
        self.assertEqual(ctx.exception.http_status, 0)

    def test_azure_raises_not_supported(self):
        provider = AzureDevOpsProvider(
            token=TOKEN, organization="org", project="proj"
        )
        with self.assertRaises(ScmNotSupportedError) as ctx:
            provider.create_release(_repo(), tag="1.0.0", title="t", body="b")
        self.assertEqual(ctx.exception.provider, "azure_devops")


if __name__ == "__main__":
    unittest.main()
