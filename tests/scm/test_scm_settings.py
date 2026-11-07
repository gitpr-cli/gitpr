"""Tests for src.scm_settings — the repository-scoped forge resolver (ADR-016).

Everything that talks to the machine is doubled: the dotenv layer
(src.config), the project file (read_project_config), the origin remote
(origin_remote_url) and decryption. What is left is the logic under test —
precedence, per-forge credentials and the one-shot migration.
"""

import os
import unittest
from pathlib import Path
from unittest import mock

from src import scm_settings
from src.project_config import ProjectConfig

_PROJECT_PATH = Path("/repo/.gitpr/conf/gitpr.config.yml")
_ENV_FILE = "/home/tester/.gitpr/.env"

_ALL_KEYS = (
    list(scm_settings.TOKEN_KEYS.values())
    + list(scm_settings.BASE_URL_KEYS.values())
    + list(scm_settings.EXTRA_ENV_KEYS.values())
    + [
        scm_settings.RAW_TOKEN_KEY,
        scm_settings.LEGACY_PROVIDER_KEY,
        scm_settings.LEGACY_TOKEN_KEY,
        scm_settings.LEGACY_BASE_URL_KEY,
    ]
)


def _decrypt(value):
    """Stands in for Fernet: 'enc:secret' -> 'secret', garbage -> ''."""
    return value[4:] if value.startswith("enc:") else ""


class ScmSettingsTestCase(unittest.TestCase):
    """A fake dotenv file, a fake project file and a fake origin remote."""

    project_provider = ""
    project_error = ""
    remote = "https://github.com/owner/repo.git"

    def setUp(self):
        self.file_values = {}
        self.saved = []
        self.removed = []

        # Start from a clean environment: the developer's own machine-wide
        # configuration must not decide what these tests see.
        environ = os.environ.copy()
        self.addCleanup(self._restore_environ, environ)
        for key in _ALL_KEYS:
            os.environ[key] = ""

        scm_settings._MIGRATION_STATE["done"] = False
        scm_settings._MIGRATION_STATE["result"] = None
        self.addCleanup(scm_settings._MIGRATION_STATE.update, {"done": False})

        for patcher in (
            mock.patch("src.scm_settings._load_env"),
            mock.patch(
                "src.scm_settings.config_module.ENV_FILE", _ENV_FILE
            ),
            mock.patch(
                "src.scm_settings.config_module.read_env_file_values",
                side_effect=lambda: dict(self.file_values),
            ),
            mock.patch(
                "src.scm_settings.config_module.remove_config_value",
                side_effect=self._remove_value,
            ),
            mock.patch(
                "src.scm_settings.config_module.save_config_values",
                side_effect=self._save_values,
            ),
            mock.patch(
                "src.scm_settings.decrypt_data", side_effect=_decrypt
            ),
            mock.patch(
                "src.scm_settings.origin_remote_url",
                side_effect=lambda start_dir=None: self.remote,
            ),
            mock.patch(
                "src.scm_settings.read_project_config",
                side_effect=self._read_project,
            ),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def _restore_environ(snapshot):
        os.environ.clear()
        os.environ.update(snapshot)

    def _remove_value(self, key):
        if key in self.file_values:
            del self.file_values[key]
            self.removed.append(key)
            return True
        return False

    def _save_values(self, values):
        self.saved.append(dict(values))
        self.file_values.update(values)

    def _read_project(self, path=None, start_dir=None):
        return ProjectConfig(
            path=_PROJECT_PATH,
            provider=self.project_provider,
            error=self.project_error,
        )


class TestPrecedence(ScmSettingsTestCase):
    """Project override -> origin remote -> github."""

    def test_the_remote_decides_when_the_file_is_silent(self):
        self.remote = "https://gitlab.com/group/proj.git"

        settings = scm_settings.resolve_scm_settings()

        self.assertEqual(settings.provider, "gitlab")
        self.assertEqual(settings.source, scm_settings.SOURCE_REMOTE)

    def test_the_project_override_beats_the_remote(self):
        self.project_provider = "bitbucket"
        self.remote = "https://github.com/owner/repo.git"

        settings = scm_settings.resolve_scm_settings()

        self.assertEqual(settings.provider, "bitbucket")
        self.assertEqual(settings.source, scm_settings.SOURCE_PROJECT)

    def test_an_unrecognised_remote_falls_back_to_github(self):
        self.remote = "https://git.example.invalid/owner/repo.git"

        settings = scm_settings.resolve_scm_settings()

        self.assertEqual(settings.provider, "github")
        self.assertEqual(settings.source, scm_settings.SOURCE_DEFAULT)

    def test_a_missing_remote_falls_back_to_github(self):
        self.remote = None

        settings = scm_settings.resolve_scm_settings()

        self.assertEqual(settings.provider, "github")
        self.assertEqual(settings.source, scm_settings.SOURCE_DEFAULT)

    def test_an_unknown_project_value_is_ignored_with_a_warning(self):
        self.project_provider = "svn"
        self.remote = "https://gitlab.com/group/proj.git"
        warnings = []

        settings = scm_settings.resolve_scm_settings(warnings=warnings)

        self.assertEqual(settings.provider, "gitlab")
        self.assertEqual(settings.source, scm_settings.SOURCE_REMOTE)
        self.assertEqual(settings.configured_provider, "svn")
        self.assertEqual(len(warnings), 1)
        self.assertIn("svn", warnings[0])

    def test_a_malformed_project_file_warns_and_keeps_going(self):
        self.project_error = "invalid YAML"
        self.remote = "https://gitlab.com/group/proj.git"
        warnings = []

        settings = scm_settings.resolve_scm_settings(warnings=warnings)

        self.assertEqual(settings.provider, "gitlab")
        self.assertTrue(any("invalid YAML" in warning for warning in warnings))

    def test_the_caller_can_hand_the_remote_it_already_read(self):
        self.remote = "https://gitlab.com/group/proj.git"

        settings = scm_settings.resolve_scm_settings(
            remote_url="https://bitbucket.org/workspace/repo.git"
        )

        self.assertEqual(settings.provider, "bitbucket")
        self.assertEqual(
            settings.remote_url, "https://bitbucket.org/workspace/repo.git"
        )


class TestCredentials(ScmSettingsTestCase):
    """One slot per forge; nothing answers on behalf of another."""

    def test_each_forge_reads_its_own_slot(self):
        os.environ["GITHUB_TOKEN_ENCRYPTED"] = "enc:gh"
        os.environ["GITLAB_TOKEN_ENCRYPTED"] = "enc:gl"

        self.assertEqual(scm_settings.provider_token("github"), "gh")
        self.assertEqual(scm_settings.provider_token("gitlab"), "gl")
        self.assertEqual(scm_settings.provider_token("bitbucket"), "")

    def test_a_gitlab_token_never_answers_for_github(self):
        os.environ["GITLAB_TOKEN_ENCRYPTED"] = "enc:gl"
        self.remote = "https://github.com/owner/repo.git"

        settings = scm_settings.resolve_scm_settings()

        self.assertEqual(settings.provider, "github")
        self.assertEqual(settings.token, "")
        self.assertEqual(settings.token_source, "")

    def test_the_raw_ci_token_wins_for_every_forge(self):
        os.environ[scm_settings.RAW_TOKEN_KEY] = "ci-token"
        os.environ["GITLAB_TOKEN_ENCRYPTED"] = "enc:gl"
        self.remote = "https://gitlab.com/group/proj.git"

        settings = scm_settings.resolve_scm_settings()

        self.assertEqual(settings.token, "ci-token")
        self.assertEqual(settings.token_source, scm_settings.TOKEN_SOURCE_RAW)

    def test_a_stored_token_is_reported_as_stored(self):
        os.environ["GITLAB_TOKEN_ENCRYPTED"] = "enc:gl"
        self.remote = "https://gitlab.com/group/proj.git"

        settings = scm_settings.resolve_scm_settings()

        self.assertEqual(settings.token, "gl")
        self.assertEqual(settings.token_source, scm_settings.TOKEN_SOURCE_STORED)

    def test_a_base_url_of_one_forge_does_not_leak_to_another(self):
        os.environ["GITLAB_BASE_URL"] = "https://gitlab.example.com/api/v4"

        self.assertEqual(
            scm_settings.provider_base_url("gitlab"),
            "https://gitlab.example.com/api/v4",
        )
        self.assertIsNone(scm_settings.provider_base_url("github"))

    def test_an_empty_base_url_reads_as_the_provider_default(self):
        os.environ["GITHUB_BASE_URL"] = ""

        self.assertIsNone(scm_settings.provider_base_url("github"))

    def test_extras_are_only_the_ones_that_are_set(self):
        os.environ["GITPR_SCM_USERNAME"] = "bob"

        self.assertEqual(scm_settings.provider_extras(), {"username": "bob"})


class TestFlatSettings(ScmSettingsTestCase):
    """get_scm_settings() is the dict resolve_scm_provider() already consumes."""

    def test_empty_values_are_dropped(self):
        self.remote = "https://gitlab.com/group/proj.git"

        flat = scm_settings.get_scm_settings()

        self.assertEqual(flat, {"provider": "gitlab"})

    def test_the_credential_and_extras_travel_together(self):
        os.environ["GITLAB_TOKEN_ENCRYPTED"] = "enc:gl"
        os.environ["GITLAB_BASE_URL"] = "https://gitlab.example.com/api/v4"
        self.remote = "https://gitlab.com/group/proj.git"

        flat = scm_settings.get_scm_settings()

        self.assertEqual(flat["provider"], "gitlab")
        self.assertEqual(flat["token"], "gl")
        self.assertEqual(flat["base_url"], "https://gitlab.example.com/api/v4")


class TestLegacyMigration(ScmSettingsTestCase):
    """The one-shot move out of the global GITPR_SCM_* keys."""

    def _set_legacy(self, provider="gitlab", token="enc:gl", base_url=""):
        self.file_values[scm_settings.LEGACY_PROVIDER_KEY] = provider
        self.file_values[scm_settings.LEGACY_TOKEN_KEY] = token
        if base_url:
            self.file_values[scm_settings.LEGACY_BASE_URL_KEY] = base_url
        os.environ[scm_settings.LEGACY_PROVIDER_KEY] = provider
        os.environ[scm_settings.LEGACY_TOKEN_KEY] = token
        os.environ[scm_settings.LEGACY_BASE_URL_KEY] = base_url

    def test_the_legacy_pair_moves_to_the_forge_slot(self):
        self._set_legacy(base_url="https://gitlab.example.com/api/v4")

        result = scm_settings.migrate_legacy_scm_config()

        self.assertTrue(result.migrated)
        self.assertEqual(result.provider, "gitlab")
        self.assertEqual(
            self.saved,
            [
                {
                    "GITLAB_TOKEN_ENCRYPTED": "enc:gl",
                    "GITLAB_BASE_URL": "https://gitlab.example.com/api/v4",
                }
            ],
        )
        self.assertEqual(
            self.removed,
            [
                scm_settings.LEGACY_PROVIDER_KEY,
                scm_settings.LEGACY_TOKEN_KEY,
                scm_settings.LEGACY_BASE_URL_KEY,
            ],
        )
        self.assertEqual(os.environ["GITLAB_TOKEN_ENCRYPTED"], "enc:gl")
        self.assertNotIn(scm_settings.LEGACY_PROVIDER_KEY, os.environ)

    def test_an_existing_forge_token_is_never_overwritten(self):
        self._set_legacy()
        self.file_values["GITLAB_TOKEN_ENCRYPTED"] = "enc:newer"
        os.environ["GITLAB_TOKEN_ENCRYPTED"] = "enc:newer"

        result = scm_settings.migrate_legacy_scm_config()

        self.assertFalse(result.migrated)
        self.assertEqual(self.saved, [])
        self.assertIn(scm_settings.LEGACY_PROVIDER_KEY, self.removed)
        # The forge keeps the token it had, and the process sees it.
        self.assertEqual(scm_settings.provider_token("gitlab"), "newer")

    def test_a_token_without_a_forge_is_left_alone(self):
        self._set_legacy(provider="")

        result = scm_settings.migrate_legacy_scm_config()

        self.assertFalse(result.migrated)
        self.assertTrue(result.warning)
        self.assertEqual(self.saved, [])
        self.assertEqual(os.environ["GITPR_SCM_TOKEN_ENCRYPTED"], "enc:gl")

    def test_an_unknown_forge_is_left_alone(self):
        self._set_legacy(provider="svn")

        result = scm_settings.migrate_legacy_scm_config()

        self.assertFalse(result.migrated)
        self.assertIn("svn", result.warning)
        self.assertEqual(self.saved, [])

    def test_seeded_empty_lines_are_removed_without_a_migration(self):
        self._set_legacy(provider="", token="")

        result = scm_settings.migrate_legacy_scm_config()

        self.assertFalse(result.migrated)
        self.assertFalse(result.warning)
        self.assertEqual(self.saved, [])
        self.assertIn(scm_settings.LEGACY_PROVIDER_KEY, self.removed)

    def test_the_migration_runs_once(self):
        self._set_legacy()
        scm_settings.migrate_legacy_scm_config()

        scm_settings.migrate_legacy_scm_config()

        self.assertEqual(len(self.saved), 1)

    def test_a_read_only_home_keeps_the_value_for_this_run(self):
        self._set_legacy()

        with mock.patch(
            "src.scm_settings.config_module.save_config_values",
            side_effect=PermissionError("read-only HOME"),
        ):
            result = scm_settings.migrate_legacy_scm_config()

        self.assertFalse(result.persisted)
        self.assertIn("read-only HOME", result.warning)
        # The command keeps working: no reader below looks at the legacy keys.
        self.assertEqual(scm_settings.provider_token("gitlab"), "gl")

    def test_the_resolver_migrates_before_it_reads(self):
        self._set_legacy()
        self.remote = "https://gitlab.com/group/proj.git"

        settings = scm_settings.resolve_scm_settings()

        self.assertEqual(settings.provider, "gitlab")
        self.assertEqual(settings.token, "gl")
        self.assertEqual(len(self.saved), 1)


if __name__ == "__main__":
    unittest.main()
