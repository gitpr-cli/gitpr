"""Tests for the PyPI-only auto-updater and the mandatory update gate.

GitPR is distributed exclusively through PyPI, so a published newer version
blocks execution until the user runs `pip install --upgrade gitpr-cli`.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from click.testing import CliRunner

from src.i18n import CURRENT_LANG, set_lang
from src.main import cli
from src.updater import (
    __version__,
    check_and_update,
    enforce_update_required,
    get_latest_remote_version,
    is_update_check_disabled,
    parse_version,
)

SKIP_ENV = "GITPR_SKIP_UPDATE_CHECK"


class UpdaterTestCase(unittest.TestCase):
    """Isolates the daily update cache and the skip switch for every test."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.cache_file = os.path.join(tmp.name, "update_cache.json")

        cache_patcher = mock.patch(
            "src.updater.get_update_cache_file", return_value=self.cache_file
        )
        cache_patcher.start()
        self.addCleanup(cache_patcher.stop)

        # conftest mutes the gate globally; each test must opt back in.
        env_patcher = mock.patch.dict(os.environ, {SKIP_ENV: ""})
        env_patcher.start()
        self.addCleanup(env_patcher.stop)

    def write_cache(self, version, date=None):
        """Seeds the daily cache the way a successful live fetch would."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump({"date": date or datetime.now().strftime("%Y-%m-%d"), "version": version}, f)


class TestParseVersion(UpdaterTestCase):
    def test_parses_with_and_without_prefix(self):
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))

    def test_invalid_version_falls_back_to_zero(self):
        self.assertEqual(parse_version("not-a-version"), (0, 0, 0))


class TestUpdateCheckSwitch(UpdaterTestCase):
    def test_disabled_when_env_is_set(self):
        with mock.patch.dict(os.environ, {SKIP_ENV: "true"}):
            self.assertTrue(is_update_check_disabled())

    def test_enabled_when_env_is_empty(self):
        self.assertFalse(is_update_check_disabled())


class TestGetLatestRemoteVersion(UpdaterTestCase):
    def test_uses_the_daily_cache_without_touching_the_network(self):
        self.write_cache("9.9.9")

        with mock.patch("src.updater.urllib.request.urlopen") as urlopen:
            self.assertEqual(get_latest_remote_version(), "9.9.9")

        urlopen.assert_not_called()

    def test_ignores_a_cache_from_another_day(self):
        self.write_cache("9.9.9", date="2000-01-01")
        response = self._pypi_response("2.0.0")

        with mock.patch("src.updater.urllib.request.urlopen", return_value=response):
            self.assertEqual(get_latest_remote_version(), "2.0.0")

    def test_fetches_from_pypi_and_caches_without_a_download_url(self):
        response = self._pypi_response("2.0.0")

        with mock.patch("src.updater.urllib.request.urlopen", return_value=response):
            self.assertEqual(get_latest_remote_version(), "2.0.0")

        with open(self.cache_file, encoding="utf-8") as f:
            cached = json.load(f)
        self.assertEqual(cached["version"], "2.0.0")
        self.assertNotIn("download_url", cached)

    def test_returns_empty_string_when_offline(self):
        with mock.patch(
            "src.updater.urllib.request.urlopen", side_effect=OSError("offline")
        ):
            self.assertEqual(get_latest_remote_version(), "")

    @staticmethod
    def _pypi_response(version):
        """Builds a urlopen stand-in shaped like the PyPI JSON API."""
        response = mock.MagicMock()
        response.read.return_value = json.dumps({"info": {"version": version}}).encode()
        response.__enter__ = mock.MagicMock(return_value=response)
        response.__exit__ = mock.MagicMock(return_value=False)
        return response


class TestEnforceUpdateRequired(UpdaterTestCase):
    def test_blocks_when_a_newer_version_is_published(self):
        with mock.patch("src.updater.get_latest_remote_version", return_value="9.9.9"):
            self.assertTrue(enforce_update_required())

    def test_prints_the_pip_upgrade_command(self):
        with mock.patch("src.updater.get_latest_remote_version", return_value="9.9.9"):
            with mock.patch("click.secho") as secho:
                enforce_update_required()

        printed = " ".join(str(call.args[0]) for call in secho.call_args_list)
        self.assertIn("pip install --upgrade gitpr-cli", printed)

    def test_does_not_block_when_running_the_latest(self):
        with mock.patch(
            "src.updater.get_latest_remote_version", return_value=__version__
        ):
            self.assertFalse(enforce_update_required())

    def test_does_not_block_when_the_remote_version_is_older(self):
        with mock.patch("src.updater.get_latest_remote_version", return_value="0.0.1"):
            self.assertFalse(enforce_update_required())

    def test_does_not_block_when_the_version_is_unknown(self):
        """Offline must never lock the user into a command they cannot run."""
        with mock.patch("src.updater.get_latest_remote_version", return_value=""):
            self.assertFalse(enforce_update_required())

    def test_does_not_block_when_the_check_is_disabled(self):
        with mock.patch.dict(os.environ, {SKIP_ENV: "true"}):
            with mock.patch("src.updater.get_latest_remote_version") as remote:
                self.assertFalse(enforce_update_required())

        remote.assert_not_called()


class TestCheckAndUpdate(UpdaterTestCase):
    def test_prints_the_pip_command_when_a_newer_version_exists(self):
        with mock.patch("src.updater.get_latest_remote_version", return_value="9.9.9"):
            with mock.patch("click.secho") as secho:
                check_and_update()

        printed = " ".join(str(call.args[0]) for call in secho.call_args_list)
        self.assertIn("pip install --upgrade gitpr-cli", printed)

    def test_reports_when_already_up_to_date(self):
        with mock.patch(
            "src.updater.get_latest_remote_version", return_value=__version__
        ):
            with mock.patch("click.secho") as secho:
                check_and_update()

        printed = " ".join(str(call.args[0]) for call in secho.call_args_list)
        self.assertIn("already using the latest version", printed)

    def test_reports_failure_when_the_version_is_unknown(self):
        with mock.patch("src.updater.get_latest_remote_version", return_value=""):
            with mock.patch("click.secho") as secho:
                check_and_update()

        printed = " ".join(str(call.args[0]) for call in secho.call_args_list)
        self.assertIn("Could not check for updates", printed)


class TestCliUpdateGate(UpdaterTestCase):
    """Wiring between cli() and the gate, driven through Click."""

    def invoke(self, args, remote_version="9.9.9"):
        with mock.patch(
            "src.updater.get_latest_remote_version", return_value=remote_version
        ):
            return CliRunner().invoke(cli, args)

    def test_outdated_cli_exits_nonzero_with_upgrade_instructions(self):
        result = self.invoke(["--status"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("pip install --upgrade gitpr-cli", result.output)

    def test_contextual_help_is_never_blocked(self):
        result = self.invoke(["-h", "--update"])

        self.assertEqual(result.exit_code, 0)

    def test_update_flag_is_never_blocked(self):
        """`gitpr --update` is the command that explains how to upgrade."""
        with mock.patch("src.main.check_internet_connection"):
            result = self.invoke(["--update"])

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("must be updated before it can run", result.output)

    def test_quiet_mode_is_never_blocked(self):
        result = self.invoke(["--quiet", "--status"])

        self.assertNotEqual(result.exit_code, 1)

    def test_gate_is_skipped_when_the_switch_is_set(self):
        with mock.patch.dict(os.environ, {SKIP_ENV: "true"}):
            result = self.invoke(["--status"])

        self.assertNotEqual(result.exit_code, 1)

    def test_current_version_runs_normally(self):
        result = self.invoke(["--status"], remote_version=__version__)

        self.assertNotEqual(result.exit_code, 1)
