"""Tests for the SCM factory: registry, resolution and remote detection.

Resolution never touches the network (providers are constructed, not called).
The GitHub legacy-token fallback is tested with config.get_github_token
mocked — the factory imports it lazily, so patching src.config works.
"""
import unittest
from unittest.mock import patch

from src.infrastructure.scm.base import ScmProvider
from src.infrastructure.scm.factory import (
    _REGISTRY,
    detect_provider_from_remote,
    resolve_scm_provider,
)
from src.infrastructure.scm.github_provider import GitHubProvider
from src.infrastructure.scm.gitlab_provider import GitLabProvider


class TestRegistry(unittest.TestCase):
    def test_github_and_gitlab_registered(self):
        self.assertEqual(_REGISTRY["github"], GitHubProvider)
        self.assertEqual(_REGISTRY["gitlab"], GitLabProvider)

    def test_registry_entries_are_concrete_providers(self):
        for cls in _REGISTRY.values():
            self.assertTrue(issubclass(cls, ScmProvider))


class TestResolve(unittest.TestCase):
    @patch("src.config.get_github_token", return_value="legacy-token")
    def test_default_provider_is_github_without_config(self, mock_token):
        provider = resolve_scm_provider({})

        self.assertIsInstance(provider, GitHubProvider)
        # Default github keeps using the legacy GITHUB_TOKEN_* store.
        self.assertEqual(provider.token, "legacy-token")
        self.assertEqual(provider.base_url, "https://api.github.com")

    @patch("src.config.get_github_token", return_value="")
    def test_explicit_github_token_wins_over_fallback(self, mock_token):
        provider = resolve_scm_provider({"provider": "github", "token": "ghp_x"})
        self.assertEqual(provider.token, "ghp_x")
        mock_token.assert_not_called()

    @patch("src.config.get_github_token", return_value="legacy-token")
    def test_gitlab_never_uses_github_token_fallback(self, mock_token):
        provider = resolve_scm_provider({"provider": "gitlab", "token": "glpat_x"})
        self.assertIsInstance(provider, GitLabProvider)
        self.assertEqual(provider.token, "glpat_x")
        mock_token.assert_not_called()

    def test_custom_base_url_is_forwarded(self):
        provider = resolve_scm_provider(
            {"provider": "gitlab", "token": "t", "base_url": "https://git.empresa.com/api/v4"}
        )
        self.assertEqual(provider.base_url, "https://git.empresa.com/api/v4")

    def test_provider_key_is_normalized(self):
        with patch("src.config.get_github_token", return_value=""):
            provider = resolve_scm_provider({"provider": " GitHub ", "token": "t"})
        self.assertIsInstance(provider, GitHubProvider)

    def test_unknown_provider_lists_valid_ones(self):
        with patch("src.i18n.TRANSLATIONS", {}):
            with self.assertRaises(ValueError) as ctx:
                resolve_scm_provider({"provider": "svn"})
        message = str(ctx.exception)
        self.assertIn("svn", message)
        self.assertIn("github", message)
        self.assertIn("gitlab", message)

    def test_extra_kwargs_are_forwarded(self):
        provider = resolve_scm_provider(
            {
                "provider": "gitlab",
                "token": "t",
                "organization": "org",
                "project": "proj",
                "username": "user",
            }
        )
        self.assertEqual(provider.extra["organization"], "org")
        self.assertEqual(provider.extra["project"], "proj")
        self.assertEqual(provider.extra["username"], "user")


class TestDetectProviderFromRemote(unittest.TestCase):
    CASES = [
        # (remote_url, expected)
        ("https://github.com/owner/repo.git", "github"),
        ("git@github.com:owner/repo.git", "github"),
        ("https://github.com/owner/repo", "github"),
        ("https://gitlab.com/group/proj.git", "gitlab"),
        ("git@gitlab.com:group/sub/proj.git", "gitlab"),
        ("https://gitlab.empresa.com/grupo/proj.git", "gitlab"),
        ("https://bitbucket.org/workspace/repo.git", "bitbucket"),
        ("git@bitbucket.org:workspace/repo.git", "bitbucket"),
        ("https://dev.azure.com/org/proj/_git/repo", "azure_devops"),
        ("https://org.visualstudio.com/proj/_git/repo", "azure_devops"),
        # Anything unrecognized defaults to github (current GitPR behavior).
        ("https://example.com/junk/repo.git", "github"),
        ("", "github"),
    ]

    def test_detection_table(self):
        for url, expected in self.CASES:
            with self.subTest(url=url):
                self.assertEqual(detect_provider_from_remote(url), expected)

    def test_case_insensitive(self):
        self.assertEqual(detect_provider_from_remote("HTTPS://GITLAB.COM/G/P.GIT"), "gitlab")


if __name__ == "__main__":
    unittest.main()
