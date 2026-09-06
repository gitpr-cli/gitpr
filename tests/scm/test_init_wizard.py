"""Tests for core.run_scm_init_wizard() — the 'gitpr --init' SCM forge wizard.

The wizard does its imports lazily inside the function body, so the patch
targets are the package/module attributes it re-imports at call time:
  - src.infrastructure.scm.{detect_provider_from_remote, resolve_scm_provider,
    provider_display_name, provider_is_github}
  - src.tui_issue.{_show_auth_instructions, _error_message,
    _no_longer_valid_message}
  - src.core.{get_origin_remote_url, describe_repo, set_key, encrypt_data}
  - src.core.click.* (echo/secho/confirm/prompt)

A FakeProvider stands in for the real providers: with_token() returns itself,
test_connection() raises ScmProviderError when error_status is set, and
default_base_url() reports the cloud default per forge. Nothing real is
persisted: set_key and encrypt_data are mocked, and every test asserts that
NOTHING is written when validation fails ("persist only on success").
"""

import unittest
from unittest import mock

from src import core
from src.infrastructure.scm import ScmProviderError

# Cloud default base URLs per forge — mirrors the real providers.
_DEFAULT_BASE_URLS = {
    "github": "https://api.github.com",
    "gitlab": "https://gitlab.com/api/v4",
    "bitbucket": "https://api.bitbucket.org/2.0",
    "azure_devops": "https://dev.azure.com",
}

_DISPLAY_NAMES = {
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "azure_devops": "Azure DevOps",
}


class FakeProvider:
    """Minimal provider double: token re-auth, connection result, parse."""

    def __init__(self, name="github", base_url=None, error_status=None, **kwargs):
        self.name = name
        self.base_url = base_url or _DEFAULT_BASE_URLS[name]
        self.error_status = error_status
        self.extra = dict(kwargs)
        self.token = ""
        self.connection_calls = 0

    def default_base_url(self) -> str:
        return self.base_url

    def with_token(self, token):
        self.token = token
        return self

    def test_connection(self, timeout: int = 10) -> bool:
        self.connection_calls += 1
        if self.error_status is not None:
            raise ScmProviderError(self.name, self.error_status, "simulated failure")
        return True

    def parse_repo_ref(self, raw_remote):
        # Consumed only by describe_repo(), which is patched in every test.
        return raw_remote


def _provider_factory(error_status=None):
    """Builds the side_effect for resolve_scm_provider from its config dict."""

    def build(config):
        return FakeProvider(
            name=config.get("provider", "github"),
            base_url=config.get("base_url"),
            error_status=error_status,
            **{
                key: value
                for key, value in config.items()
                if key in ("organization", "project", "username")
            },
        )

    return build


class TestScmInitWizard(unittest.TestCase):
    """run_scm_init_wizard flow: detect, extras, token, persist-only-on-success."""

    def setUp(self):
        self.secho = mock.patch.object(core.click, "secho").start()
        self.echo = mock.patch.object(core.click, "echo").start()
        self.confirm = mock.patch.object(core.click, "confirm", return_value=True).start()
        self.prompt = mock.patch.object(core.click, "prompt").start()
        self.origin = mock.patch(
            "src.core.get_origin_remote_url",
            return_value="https://github.com/owner/repo.git",
        ).start()
        self.describe_repo = mock.patch(
            "src.core.describe_repo", return_value="owner/repo"
        ).start()
        self.set_key = mock.patch("src.core.set_key").start()
        self.encrypt = mock.patch(
            "src.core.encrypt_data", side_effect=lambda raw: f"enc:{raw}"
        ).start()
        self.detect = mock.patch(
            "src.infrastructure.scm.detect_provider_from_remote", return_value="github"
        ).start()
        self.resolve = mock.patch("src.infrastructure.scm.resolve_scm_provider").start()
        self.display = mock.patch(
            "src.infrastructure.scm.provider_display_name",
            side_effect=lambda key: _DISPLAY_NAMES.get(key, str(key)),
        ).start()
        self.is_github = mock.patch(
            "src.infrastructure.scm.provider_is_github",
            side_effect=lambda provider: provider.name == "github",
        ).start()
        self.instructions = mock.patch("src.tui_issue._show_auth_instructions").start()
        self.error_message = mock.patch(
            "src.tui_issue._error_message", return_value="simulated failure"
        ).start()
        self.no_longer = mock.patch(
            "src.tui_issue._no_longer_valid_message", return_value="token no longer valid"
        ).start()
        self.translations = mock.patch("src.i18n.TRANSLATIONS", {}).start()
        self.addCleanup(mock.patch.stopall)

    def _run_github_success(self, tokens=("ghp_token123",)):
        self.resolve.side_effect = _provider_factory()
        self.prompt.side_effect = list(tokens)
        core.run_scm_init_wizard()

    # -- no remote -------------------------------------------------------

    def test_no_origin_remote_aborts_without_prompting(self):
        self.origin.return_value = ""
        core.run_scm_init_wizard()
        self.secho.assert_any_call(
            "❌ No origin remote repository identified. Run 'gitpr --init' inside a repository that has a configured remote.",
            fg="red",
        )
        self.prompt.assert_not_called()
        self.confirm.assert_not_called()
        self.set_key.assert_not_called()

    # -- github success path ---------------------------------------------

    def test_github_flow_success_persists_provider_and_encrypted_token(self):
        self._run_github_success()
        # Banner + explanation + repository line.
        self.secho.assert_any_call(
            "\n🔧 Starting GitPR SCM Forge Configuration Wizard...", fg="cyan", bold=True
        )
        self.echo.assert_any_call(
            "Repository: https://github.com/owner/repo.git"
        )
        # Detection confirmation shown with the display name.
        self.confirm.assert_called_once_with(
            "Detected forge: GitHub. Configure GitPR to use it for pull requests and issues?",
            default=True,
        )
        # Github: no base URL prompt; single hidden token prompt.
        self.prompt.assert_called_once_with("Paste your Token (PAT) here", hide_input=True)
        # Auth instructions carried the parsed repo display.
        self.instructions.assert_called_once()
        provider_arg, repo_display = self.instructions.call_args[0]
        self.assertEqual(provider_arg.name, "github")
        self.assertEqual(repo_display, "owner/repo")
        # Persisted exactly: provider key + encrypted token (no extras).
        self.set_key.assert_any_call(mock.ANY, "GITPR_SCM_PROVIDER", "github")
        self.set_key.assert_any_call(
            mock.ANY, "GITPR_SCM_TOKEN_ENCRYPTED", "enc:ghp_token123"
        )
        self.assertEqual(self.set_key.call_count, 2)
        self.secho.assert_any_call(
            "✅ SCM forge configured: GitHub! Pull requests and issues will use it from now on.\n",
            fg="green",
            bold=True,
        )

    # -- declined detection / manual forge key ---------------------------

    def test_declined_detection_prompts_forge_key_and_keeps_default_base_url(self):
        self.confirm.return_value = False
        self.resolve.side_effect = _provider_factory()
        self.prompt.side_effect = ["gitlab", "", "gl_token"]
        core.run_scm_init_wizard()
        # Forge key asked with the full registry; base URL default not persisted.
        self.prompt.assert_any_call(
            "Enter the forge key (github, gitlab, bitbucket, azure_devops):"
        )
        self.resolve.assert_called_once_with({"provider": "gitlab"})
        self.set_key.assert_any_call(mock.ANY, "GITPR_SCM_PROVIDER", "gitlab")
        self.assertNotIn(
            "GITPR_SCM_BASE_URL",
            [call.args[1] for call in self.set_key.call_args_list],
        )
        self.prompt.assert_any_call("Paste your GitLab token here", hide_input=True)

    def test_invalid_forge_key_reprompts_until_valid(self):
        self.confirm.return_value = False
        self.resolve.side_effect = _provider_factory()
        self.prompt.side_effect = ["frobozz", "gitlab", "", "gl_token"]
        core.run_scm_init_wizard()
        forge_prompts = [
            call
            for call in self.prompt.call_args_list
            if call.args[0].startswith("Enter the forge key")
        ]
        self.assertEqual(len(forge_prompts), 2)
        self.set_key.assert_any_call(mock.ANY, "GITPR_SCM_PROVIDER", "gitlab")

    # -- base URL handling -----------------------------------------------

    def test_custom_base_url_is_persisted(self):
        self.detect.return_value = "gitlab"
        self.resolve.side_effect = _provider_factory()
        self.prompt.side_effect = ["https://gitlab.example.com/api/v4", "gl_token"]
        core.run_scm_init_wizard()
        # Default pre-filled in the prompt; the rebuild carries the custom URL.
        self.prompt.assert_any_call(
            "API base URL:", default="https://gitlab.com/api/v4"
        )
        self.assertEqual(self.resolve.call_count, 2)
        self.resolve.assert_any_call({"provider": "gitlab"})
        self.resolve.assert_any_call(
            {"provider": "gitlab", "base_url": "https://gitlab.example.com/api/v4"}
        )
        self.set_key.assert_any_call(
            mock.ANY, "GITPR_SCM_BASE_URL", "https://gitlab.example.com/api/v4"
        )
        self.assertEqual(self.set_key.call_count, 3)  # provider + token + base URL

    def test_github_never_asks_for_base_url(self):
        self._run_github_success()
        self.assertFalse(
            any(
                call.args[0] == "API base URL:"
                for call in self.prompt.call_args_list
            )
        )

    # -- provider extras -------------------------------------------------

    def test_azure_devops_asks_organization_and_project(self):
        self.detect.return_value = "azure_devops"
        self.resolve.side_effect = _provider_factory()
        self.prompt.side_effect = ["northwind", "webapp", "", "az_token"]
        core.run_scm_init_wizard()
        self.prompt.assert_any_call("Organization name:")
        self.prompt.assert_any_call("Project name:")
        self.resolve.assert_called_once_with(
            {
                "provider": "azure_devops",
                "organization": "northwind",
                "project": "webapp",
            }
        )
        self.set_key.assert_any_call(mock.ANY, "GITPR_SCM_ORGANIZATION", "northwind")
        self.set_key.assert_any_call(mock.ANY, "GITPR_SCM_PROJECT", "webapp")
        self.set_key.assert_any_call(mock.ANY, "GITPR_SCM_PROVIDER", "azure_devops")
        self.set_key.assert_any_call(
            mock.ANY, "GITPR_SCM_TOKEN_ENCRYPTED", "enc:az_token"
        )
        self.prompt.assert_any_call("Paste your Azure DevOps token here", hide_input=True)

    def test_bitbucket_asks_username(self):
        self.detect.return_value = "bitbucket"
        self.resolve.side_effect = _provider_factory()
        self.prompt.side_effect = ["bob", "", "bb_token"]
        core.run_scm_init_wizard()
        self.prompt.assert_any_call("Username:")
        self.resolve.assert_called_once_with(
            {"provider": "bitbucket", "username": "bob"}
        )
        self.set_key.assert_any_call(mock.ANY, "GITPR_SCM_USERNAME", "bob")
        self.set_key.assert_any_call(mock.ANY, "GITPR_SCM_PROVIDER", "bitbucket")
        self.prompt.assert_any_call("Paste your Bitbucket token here", hide_input=True)

    # -- validation failures: nothing persisted --------------------------

    def test_401_token_rejected_reprompts_then_gives_up(self):
        self.resolve.side_effect = _provider_factory(error_status=401)
        self.prompt.side_effect = ["t1", "t2", "t3"]
        core.run_scm_init_wizard()
        # One initial prompt + two re-prompts (attempts 1 and 2 fail 401).
        self.assertEqual(self.prompt.call_count, 3)
        warnings = [
            call
            for call in self.secho.call_args_list
            if call.args[0] == "token no longer valid" and call.kwargs.get("fg") == "yellow"
        ]
        # Every rejected attempt warns; the last one then also exits in red.
        self.assertEqual(len(warnings), 3)
        self.secho.assert_any_call(
            "❌ Could not validate the GitHub token after 3 attempts. Run 'gitpr --init' again with a valid token.",
            fg="red",
        )
        self.set_key.assert_not_called()

    def test_network_failure_aborts_without_retry_or_persist(self):
        self.resolve.side_effect = _provider_factory(error_status=0)
        self.prompt.side_effect = ["t1"]
        core.run_scm_init_wizard()
        # Network/server-side errors are not fixed by re-prompting.
        self.assertEqual(self.prompt.call_count, 1)
        self.secho.assert_any_call(
            "❌ GitHub configuration failed: simulated failure",
            fg="red",
        )
        self.set_key.assert_not_called()


if __name__ == "__main__":
    unittest.main()
