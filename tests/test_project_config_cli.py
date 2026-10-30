"""CLI wiring of the project configuration seed.

cli() seeds .gitpr/conf/gitpr.config.yml on every invocation inside a git
repository — subcommands included — and announces it only on the interactive
root path. The tests run the real CLI against a temporary repository: the
paths a seed must never touch are the ones a mock would hide.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from src.main import cli

SKIP_ENV = "GITPR_SKIP_PROJECT_CONFIG_SEED"


class SeedCliTestCase(unittest.TestCase):
    def setUp(self):
        # tests/conftest.py turns the seed off for the whole suite; this class
        # is the one place that exercises it, so the switch is cleared here.
        patcher = patch.dict(os.environ, {SKIP_ENV: ""})
        patcher.start()
        self.addCleanup(patcher.stop)
        # The seeded branch comes from PR_DEFAULT_BASE; an exported one would
        # make these tests describe the machine instead of the code.
        os.environ.pop("PR_DEFAULT_BASE", None)

        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        # Registered after the directory, so it is the first cleanup to run:
        # Windows refuses to delete the current working directory.
        self._previous_cwd = os.getcwd()
        self.addCleanup(os.chdir, self._previous_cwd)
        self.root = Path(self._tmpdir.name)

        env_file_patcher = patch(
            "src.config.ENV_FILE", str(self.root / "gitpr.env")
        )
        env_file_patcher.start()
        self.addCleanup(env_file_patcher.stop)

    def make_repo(self):
        repo = self.root / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "-q"], cwd=repo, check=True, capture_output=True
        )
        os.chdir(repo)
        return repo

    def test_an_interactive_run_creates_and_announces_the_file(self):
        repo = self.make_repo()
        self.config = repo / ".gitpr" / "conf" / "gitpr.config.yml"

        result = CliRunner().invoke(cli, ["--status"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(self.config.exists())
        self.assertIn("Project configuration created", result.output)

    def test_the_seed_uses_the_global_default_from_the_configuration_file(self):
        repo = self.make_repo()
        self.config = repo / ".gitpr" / "conf" / "gitpr.config.yml"
        env_file = self.root / "gitpr.env"
        env_file.write_text("PR_DEFAULT_BASE=release\n", encoding="utf-8")

        with patch("src.config.ENV_FILE", str(env_file)):
            result = CliRunner().invoke(cli, ["--status"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(
            "base_branch: release", self.config.read_text(encoding="utf-8")
        )

    def test_a_subcommand_seeds_without_printing(self):
        repo = self.make_repo()
        self.config = repo / ".gitpr" / "conf" / "gitpr.config.yml"

        with patch("src.ui.config_app.launch_config_app"):
            result = CliRunner().invoke(cli, ["config"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(self.config.exists())
        self.assertNotIn("Project configuration created", result.output)

    def test_help_never_writes_the_file(self):
        repo = self.make_repo()
        self.config = repo / ".gitpr" / "conf" / "gitpr.config.yml"

        result = CliRunner().invoke(cli, ["-h"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertFalse(self.config.exists())

    def test_quiet_still_seeds_but_stays_silent(self):
        repo = self.make_repo()
        self.config = repo / ".gitpr" / "conf" / "gitpr.config.yml"

        result = CliRunner().invoke(cli, ["--quiet", "--status"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(self.config.exists())
        self.assertNotIn("Project configuration created", result.output)

    def test_outside_a_repository_nothing_is_written(self):
        os.chdir(self.root)
        self.config = self.root / ".gitpr" / "conf" / "gitpr.config.yml"

        with patch("src.ui.config_app.launch_config_app"):
            result = CliRunner().invoke(cli, ["config"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertFalse(self.config.exists())

    def test_an_existing_file_is_left_untouched(self):
        repo = self.make_repo()
        self.config = repo / ".gitpr" / "conf" / "gitpr.config.yml"
        self.config.parent.mkdir(parents=True)
        self.config.write_text(
            "pull_request:\n  base_branch: develop\n", encoding="utf-8"
        )

        result = CliRunner().invoke(cli, ["--status"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(
            "base_branch: develop", self.config.read_text(encoding="utf-8")
        )
        self.assertNotIn("Project configuration created", result.output)


if __name__ == "__main__":
    unittest.main()
