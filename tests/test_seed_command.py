"""Tests for the seed command and project-local configuration seeding."""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src import ledger
from src.core import _seed_local_smart_excludes, seed_project_configuration
from src.main import cli


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Ensure tests run in an isolated environment without writing to real user config."""
    home_dir = tmp_path / "home"
    (home_dir / ".gitpr").mkdir(parents=True)
    test_env_file = home_dir / ".gitpr" / ".env"
    test_env_file.write_text("GITPR_LANG=en_us\n", encoding="utf-8")

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home_dir))
    monkeypatch.setattr("src.config.ENV_FILE", str(test_env_file))
    monkeypatch.setenv("GITPR_SKIP_PROJECT_CONFIG_SEED", "1")
    monkeypatch.setenv("GITPR_SKIP_UPDATE_CHECK", "true")
    monkeypatch.setenv("GITPR_LANG", "en_us")
    ledger.configure_terminal(interactive=False, quiet=True)
    yield tmp_path


class TestSeedProjectConfiguration:
    """Unit tests for seed_project_configuration."""

    @pytest.fixture(autouse=True)
    def _setup_repo(self, tmp_path, monkeypatch):
        """Run tests inside an isolated directory with an initialized git repo."""
        self.repo_dir = tmp_path / "repo"
        self.repo_dir.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.repo_dir, check=True)
        monkeypatch.setattr("os.getcwd", lambda: str(self.repo_dir))
        monkeypatch.setattr("src.core.os.getcwd", lambda: str(self.repo_dir))
        monkeypatch.setattr("src.config.os.getcwd", lambda: str(self.repo_dir))
        monkeypatch.setattr("src.project_config.os.getcwd", lambda: str(self.repo_dir))

    def test_seed_creates_expected_files(self):
        """Initial seed creates gitpr.config.yml, smart-excludes, and linter."""
        fake_content = b"# Linter rule content"
        mock_response = MagicMock()
        mock_response.read.return_value = fake_content
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=mock_response):
            summary = seed_project_configuration(project_root=str(self.repo_dir), quiet=True)

        config_file = self.repo_dir / ".gitpr" / "conf" / "gitpr.config.yml"
        smart_file = self.repo_dir / ".gitpr" / "conf" / "gitpr.smart-excludes.json"
        linter_file = self.repo_dir / ".gitpr" / "skill" / ".gitpr.linter.yml"

        assert config_file.exists()
        assert smart_file.exists()
        assert linter_file.exists()

        assert summary["config"].created is True
        assert summary["smart_excludes"]["created"] is True
        assert summary["linter"]["created"] is True

        # Check smart-excludes content
        with open(smart_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "_comment" in data
            assert data["excludes"] == []

    def test_seed_idempotency_preserves_existing(self):
        """Running seed when files already exist preserves user changes and reports them."""
        conf_dir = self.repo_dir / ".gitpr" / "conf"
        conf_dir.mkdir(parents=True)
        smart_file = conf_dir / "gitpr.smart-excludes.json"
        smart_file.write_text('{"_comment": "custom", "excludes": ["custom/*.pyc"]}', encoding="utf-8")

        summary = seed_project_configuration(project_root=str(self.repo_dir), force=False, quiet=True)

        assert summary["smart_excludes"]["already_existed"] is True
        assert summary["smart_excludes"]["created"] is False
        assert json.loads(smart_file.read_text(encoding="utf-8"))["excludes"] == ["custom/*.pyc"]

    def test_seed_force_overwrites_existing(self):
        """Running seed with force=True re-creates default template files."""
        conf_dir = self.repo_dir / ".gitpr" / "conf"
        conf_dir.mkdir(parents=True)
        smart_file = conf_dir / "gitpr.smart-excludes.json"
        smart_file.write_text('{"custom": true}', encoding="utf-8")

        fake_content = b"# New linter content"
        mock_response = MagicMock()
        mock_response.read.return_value = fake_content
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=mock_response):
            summary = seed_project_configuration(project_root=str(self.repo_dir), force=True, quiet=True)

        assert summary["smart_excludes"]["created"] is True
        data = json.loads(smart_file.read_text(encoding="utf-8"))
        assert data["excludes"] == []

    def test_seed_include_all_skills(self):
        """seed with include_all_skills=True invokes generate_skill_template."""
        with patch("src.core.generate_skill_template") as mock_gen, \
             patch("src.core.download_skill_file", return_value=True):
            seed_project_configuration(
                project_root=str(self.repo_dir),
                include_all_skills=True,
                quiet=True,
            )
            mock_gen.assert_called_once()

    def test_skill_command_seeds_smart_excludes(self):
        """generate_skill_template automatically seeds .gitpr/conf/gitpr.smart-excludes.json."""
        from src.core import generate_skill_template

        fake_content = b"# Template"
        mock_response = MagicMock()
        mock_response.read.return_value = fake_content
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=mock_response):
            generate_skill_template()

        smart_file = self.repo_dir / ".gitpr" / "conf" / "gitpr.smart-excludes.json"
        assert smart_file.exists()


class TestSeedCLI:
    """CLI integration tests for `gitpr seed` and `--seed`."""

    def test_subcommand_seed(self, tmp_path, monkeypatch):
        """gitpr seed executes seed_project_configuration and logs command metric."""
        runner = CliRunner()
        repo = tmp_path / "repo"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        monkeypatch.setattr("os.getcwd", lambda: str(repo))

        with patch("src.main.seed_project_configuration") as mock_seed, \
             patch("src.metrics.log_command_metric") as mock_metric:
            result = runner.invoke(cli, ["seed"])
            assert result.exit_code == 0, f"Output was: {result.output}\nException: {result.exception}"
            mock_seed.assert_called_once_with(force=False, include_all_skills=False, quiet=False)
            mock_metric.assert_called_once_with(command="seed", status="success", provider="local")

    def test_subcommand_seed_with_force_and_all(self, tmp_path, monkeypatch):
        """gitpr seed --force --all passes flags correctly."""
        runner = CliRunner()
        repo = tmp_path / "repo"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        monkeypatch.setattr("os.getcwd", lambda: str(repo))

        with patch("src.main.seed_project_configuration") as mock_seed, \
             patch("src.metrics.log_command_metric") as mock_metric:
            result = runner.invoke(cli, ["seed", "--force", "--all"])
            assert result.exit_code == 0, f"Output was: {result.output}\nException: {result.exception}"
            mock_seed.assert_called_once_with(force=True, include_all_skills=True, quiet=False)
            mock_metric.assert_called_once_with(command="seed", status="success", provider="local")

    def test_flag_seed(self, tmp_path, monkeypatch):
        """gitpr --seed executes seed_project_configuration."""
        runner = CliRunner()
        repo = tmp_path / "repo"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        monkeypatch.setattr("os.getcwd", lambda: str(repo))

        with patch("src.main.seed_project_configuration") as mock_seed, \
             patch("src.main.check_internet_connection", return_value=True), \
             patch("src.main.check_and_update_hooks_scripts"), \
             patch("src.metrics.log_command_metric") as mock_metric:
            result = runner.invoke(cli, ["--seed"])
            assert result.exit_code == 0, f"Output was: {result.output}\nException: {result.exception}"
            mock_seed.assert_called_once()
            mock_metric.assert_called_once_with(command="seed", status="success", provider="local")
