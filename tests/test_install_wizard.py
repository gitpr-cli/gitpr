"""Tests for the --install wizard (run_install_wizard)."""

import unittest
from unittest.mock import patch


class TestInstallWizard(unittest.TestCase):
    """Tests for the interactive install wizard."""

    def setUp(self):
        """Set up mocks that are common across tests."""
        # Patch click.confirm to auto-confirm all steps
        self._confirm_patcher = patch("click.confirm", return_value=True)
        self.mock_confirm = self._confirm_patcher.start()

        # Patch click.echo and click.secho to suppress output during tests
        self._echo_patcher = patch("click.echo")
        self._secho_patcher = patch("click.secho")
        self.mock_echo = self._echo_patcher.start()
        self.mock_secho = self._secho_patcher.start()

    def tearDown(self):
        """Stop all patchers."""
        self._confirm_patcher.stop()
        self._echo_patcher.stop()
        self._secho_patcher.stop()

    @patch("src.core.generate_skill_template")
    @patch("src.core.install_git_hooks")
    @patch("src.core.get_ai_provider")
    @patch("src.core.get_api_key")
    def test_wizard_runs_all_steps(
        self,
        mock_get_key,
        mock_get_provider,
        mock_install_hooks,
        mock_skill,
    ):
        """All four steps execute when user confirms and API key exists."""
        from src.core import run_install_wizard

        mock_get_provider.return_value = "gemini"
        mock_get_key.return_value = "fake-key"

        with patch("src.mcp_server._run_install") as mock_mcp_install:
            run_install_wizard()
            mock_mcp_install.assert_called_once_with("auto")

        mock_skill.assert_called_once()
        mock_install_hooks.assert_called_once()

    @patch("src.core.generate_skill_template")
    @patch("src.core.install_git_hooks")
    @patch("src.core.get_ai_provider")
    @patch("src.core.get_api_key")
    def test_wizard_skips_configured_api_key(
        self,
        mock_get_key,
        mock_get_provider,
        mock_install_hooks,
        mock_skill,
    ):
        """Step 4 does NOT call setup_environment when key already exists."""
        from src.core import run_install_wizard

        mock_get_provider.return_value = "gemini"
        mock_get_key.return_value = "fake-key"

        with patch("src.core.setup_environment") as mock_setup, \
             patch("src.mcp_server._run_install"):
            run_install_wizard()
            mock_setup.assert_not_called()

    @patch("src.core.generate_skill_template")
    @patch("src.core.install_git_hooks")
    @patch("src.core.get_ai_provider")
    @patch("src.core.get_api_key")
    def test_wizard_prompts_for_missing_api_key(
        self,
        mock_get_key,
        mock_get_provider,
        mock_install_hooks,
        mock_skill,
    ):
        """Step 4 calls setup_environment when key is missing and user confirms."""
        from src.core import run_install_wizard

        mock_get_provider.return_value = "gemini"
        mock_get_key.return_value = None

        with patch("src.core.setup_environment") as mock_setup, \
             patch("src.mcp_server._run_install"):
            run_install_wizard()
            mock_setup.assert_called_once()


if __name__ == "__main__":
    unittest.main()
