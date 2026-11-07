"""Tests for the forge token dialogue in src/tui_issue.py (ADR-016).

Two contracts are covered:
  - the credential is saved in the slot of its own forge, never in a shared
    one (GITLAB_TOKEN_ENCRYPTED for a GitLab repository);
  - ``allow_prompt=False`` — hooks, MCP and CI — never asks and never deletes
    what is stored; it points at ``gitpr --init`` instead.
"""

import unittest
from unittest import mock

from src import tui_issue
from src.infrastructure.scm import ScmProviderError

_TOKEN_KEYS = {
    "github": "GITHUB_TOKEN_ENCRYPTED",
    "gitlab": "GITLAB_TOKEN_ENCRYPTED",
    "bitbucket": "BITBUCKET_TOKEN_ENCRYPTED",
    "azure_devops": "AZURE_DEVOPS_TOKEN_ENCRYPTED",
}

_DISPLAY_NAMES = {
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "azure_devops": "Azure DevOps",
}


class FakeProvider:
    def __init__(self, name="gitlab", token="", error_status=None):
        self.name = name
        self.token = token
        self.error_status = error_status
        self.saved_tokens = []

    def with_token(self, token):
        # A freshly pasted token is accepted by the forge: the double carries
        # no failure forward, so a successful re-prompt can be observed.
        self.saved_tokens.append(token)
        return FakeProvider(self.name, token)

    def test_connection(self):
        if self.error_status is not None:
            raise ScmProviderError(self.name, self.error_status, "simulated failure")
        return True


class TokenTestCase(unittest.TestCase):
    def setUp(self):
        for patcher in (
            mock.patch.object(tui_issue, "provider_display_name",
                              side_effect=lambda p: _DISPLAY_NAMES.get(p.name, p.name)),
            mock.patch.object(tui_issue, "provider_is_github",
                              side_effect=lambda p: p.name == "github"),
            mock.patch.object(tui_issue, "_show_auth_instructions"),
            mock.patch.object(tui_issue, "_error_message", return_value="expired"),
            mock.patch.object(tui_issue, "_no_longer_valid_message",
                              return_value="no longer valid"),
            mock.patch.object(tui_issue, "_valid_token_message",
                              return_value="valid"),
            mock.patch.object(tui_issue, "encrypt_data",
                              side_effect=lambda raw: f"enc:{raw}"),
            mock.patch.object(tui_issue, "set_key"),
            mock.patch.object(tui_issue, "ENV_FILE", "/home/tester/.gitpr/.env"),
            mock.patch.object(tui_issue.click, "secho"),
            mock.patch.object(tui_issue.click, "echo"),
        ):
            self.mock = patcher.start()
            self.addCleanup(patcher.stop)


class TestTokenSlot(TokenTestCase):
    def test_the_token_env_var_follows_the_forge(self):
        for name, key in _TOKEN_KEYS.items():
            with self.subTest(forge=name):
                self.assertEqual(tui_issue._token_env_var(FakeProvider(name)), key)

    def test_a_provider_without_a_name_uses_the_github_slot(self):
        self.assertEqual(
            tui_issue._token_env_var(object()), "GITHUB_TOKEN_ENCRYPTED"
        )

    def test_an_interactive_prompt_saves_the_token_in_the_forge_slot(self):
        prompt = mock.patch.object(
            tui_issue.click, "prompt", return_value="glpat_x"
        ).start()
        self.addCleanup(prompt.stop)

        token, provider = tui_issue.validate_or_request_scm_token(
            FakeProvider("gitlab"), "group/proj"
        )

        self.assertEqual(token, "glpat_x")
        self.assertEqual(provider.token, "glpat_x")
        tui_issue.set_key.assert_called_once_with(
            "/home/tester/.gitpr/.env", "GITLAB_TOKEN_ENCRYPTED", "enc:glpat_x"
        )

    def test_a_token_that_cannot_be_saved_still_works_for_the_run(self):
        prompt = mock.patch.object(
            tui_issue.click, "prompt", return_value="glpat_x"
        ).start()
        self.addCleanup(prompt.stop)
        tui_issue.set_key.side_effect = PermissionError("read-only HOME")

        token, provider = tui_issue.validate_or_request_scm_token(
            FakeProvider("gitlab"), "group/proj"
        )

        self.assertEqual(token, "glpat_x")
        self.assertEqual(provider.token, "glpat_x")


class TestNonInteractive(TokenTestCase):
    """allow_prompt=False: no question, no deletion, a pointer to --init."""

    def setUp(self):
        super().setUp()
        prompt = mock.patch.object(tui_issue.click, "prompt")
        self.prompt = prompt.start()
        self.addCleanup(prompt.stop)
        remove = mock.patch.object(tui_issue, "_remove_expired_token")
        self.remove = remove.start()
        self.addCleanup(remove.stop)

    def test_a_missing_token_is_not_requested(self):
        token, provider = tui_issue.validate_or_request_scm_token(
            FakeProvider("gitlab"), "group/proj", allow_prompt=False
        )

        self.assertIsNone(token)
        self.assertEqual(provider.name, "gitlab")
        self.prompt.assert_not_called()
        tui_issue.set_key.assert_not_called()
        tui_issue.click.secho.assert_any_call(
            "🔐 No valid GitLab token is configured for this repository. "
            "Run 'gitpr --init' here to add one.",
            fg="yellow",
        )

    def test_a_rejected_token_is_not_deleted(self):
        token, provider = tui_issue.validate_or_request_scm_token(
            FakeProvider("gitlab", token="glpat_old", error_status=401),
            "group/proj",
            allow_prompt=False,
        )

        self.assertIsNone(token)
        self.remove.assert_not_called()
        self.prompt.assert_not_called()

    def test_a_valid_token_is_used_without_asking(self):
        token, provider = tui_issue.validate_or_request_scm_token(
            FakeProvider("gitlab", token="glpat_ok"), "group/proj", allow_prompt=False
        )

        self.assertEqual(token, "glpat_ok")
        self.prompt.assert_not_called()


class TestInteractiveRetry(TokenTestCase):
    def setUp(self):
        super().setUp()
        remove = mock.patch.object(tui_issue, "_remove_expired_token")
        self.remove = remove.start()
        self.addCleanup(remove.stop)

    def test_an_expired_token_is_removed_from_its_own_slot_and_replaced(self):
        prompt = mock.patch.object(
            tui_issue.click, "prompt", return_value="glpat_new"
        ).start()
        self.addCleanup(prompt.stop)

        token, provider = tui_issue.validate_or_request_scm_token(
            FakeProvider("gitlab", token="glpat_old", error_status=401),
            "group/proj",
        )

        self.assertEqual(token, "glpat_new")
        self.remove.assert_called_once_with("GITLAB_TOKEN_ENCRYPTED")
        tui_issue.set_key.assert_called_once_with(
            mock.ANY, "GITLAB_TOKEN_ENCRYPTED", "enc:glpat_new"
        )


if __name__ == "__main__":
    unittest.main()
