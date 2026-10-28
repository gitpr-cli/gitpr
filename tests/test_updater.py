"""Tests for the PyPI-only auto-updater and the mandatory update gate.

GitPR is distributed exclusively through PyPI, so a published newer version
blocks execution until the user runs `pip install --upgrade gitpr-cli`.
"""

import json
import os
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from unittest import mock

from click.testing import CliRunner

from src.i18n import CURRENT_LANG, set_lang
from src.main import cli
from src.updater import (
    UPDATE_CACHE_TTL_SECONDS,
    __version__,
    check_and_update,
    enforce_update_required,
    get_latest_remote_version,
    is_update_check_disabled,
    parse_version,
)

SKIP_ENV = "GITPR_SKIP_UPDATE_CHECK"


class UpdaterTestCase(unittest.TestCase):
    """Isolates the update cache and the skip switch for every test."""

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
        self.tmp_dir = tmp.name
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

    def write_cache(self, version, checked_at=None):
        """Seeds the cache the way a successful live fetch would."""
        stamp = datetime.now() if checked_at is None else checked_at
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump({"checked_at": stamp.isoformat(), "version": version}, f)

    def write_raw_cache(self, payload):
        """Seeds the cache with an arbitrary document (legacy or corrupt)."""
        text = payload if isinstance(payload, str) else json.dumps(payload)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            f.write(text)

    def read_cache(self):
        with open(self.cache_file, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _pypi_payload(version):
        """Bytes shaped like the PyPI JSON API response."""
        return json.dumps({"info": {"version": version}}).encode()


class TestParseVersion(UpdaterTestCase):
    def test_parses_with_and_without_prefix(self):
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("V1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))

    def test_pep440_suffixes_keep_the_release_tuple(self):
        for value in ("1.2.3rc1", "1.2.3.post1", "1.2.3.dev0", "1.2.3-dev", "1.2.3+local"):
            self.assertEqual(parse_version(value), (1, 2, 3), value)

    def test_invalid_version_falls_back_to_zero(self):
        for value in ("not-a-version", None, 1.5):
            self.assertEqual(parse_version(value), (0, 0, 0), value)


class TestUpdateCheckSwitch(UpdaterTestCase):
    def test_disabled_when_env_is_set(self):
        with mock.patch.dict(os.environ, {SKIP_ENV: "true"}):
            self.assertTrue(is_update_check_disabled())

    def test_enabled_when_env_is_empty(self):
        self.assertFalse(is_update_check_disabled())

    def test_truthy_values_disable_the_check(self):
        for value in ("1", "true", "TRUE", " yes ", "on", "y"):
            with mock.patch.dict(os.environ, {SKIP_ENV: value}):
                self.assertTrue(is_update_check_disabled(), value)

    def test_falsey_values_keep_the_check_enabled(self):
        for value in ("0", "false", "no", "off", "n", "banana", " "):
            with mock.patch.dict(os.environ, {SKIP_ENV: value}):
                self.assertFalse(is_update_check_disabled(), value)


class TestGetLatestRemoteVersion(UpdaterTestCase):
    def test_uses_a_fresh_cache_without_touching_the_network(self):
        self.write_cache("9.9.9")

        with mock.patch("src.updater.bounded_urlopen") as fetch:
            self.assertEqual(get_latest_remote_version(), "9.9.9")

        fetch.assert_not_called()

    def test_cache_just_under_the_ttl_is_fresh(self):
        self.write_cache(
            "9.9.9", datetime.now() - timedelta(seconds=UPDATE_CACHE_TTL_SECONDS - 1)
        )

        with mock.patch("src.updater.bounded_urlopen") as fetch:
            self.assertEqual(get_latest_remote_version(), "9.9.9")

        fetch.assert_not_called()

    def test_cache_at_the_ttl_is_stale(self):
        self.write_cache(
            "9.9.9", datetime.now() - timedelta(seconds=UPDATE_CACHE_TTL_SECONDS)
        )

        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ):
            self.assertEqual(get_latest_remote_version(), "2.0.0")

    def test_cache_with_a_future_timestamp_is_stale(self):
        """A clock moved backwards must never freeze the cache indefinitely."""
        self.write_cache("9.9.9", datetime.now() + timedelta(minutes=10))

        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ):
            self.assertEqual(get_latest_remote_version(), "2.0.0")

    def test_legacy_date_cache_is_ignored_and_rewritten(self):
        self.write_raw_cache({"date": "2026-10-27", "version": "9.9.9"})

        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ):
            self.assertEqual(get_latest_remote_version(), "2.0.0")

        cached = self.read_cache()
        self.assertEqual(cached["version"], "2.0.0")
        self.assertIn("checked_at", cached)
        self.assertNotIn("date", cached)

    def test_legacy_date_cache_is_not_used_offline(self):
        self.write_raw_cache({"date": "2026-10-27", "version": "9.9.9"})

        with mock.patch("src.updater.bounded_urlopen", return_value=None):
            self.assertEqual(get_latest_remote_version(), "")

    def test_corrupt_cache_is_ignored(self):
        self.write_raw_cache("{not json")

        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ):
            self.assertEqual(get_latest_remote_version(), "2.0.0")

    def test_invalid_checked_at_is_stale(self):
        for stamp in ("yesterday", 12345, None, "2026-10-27T12:00:00+00:00"):
            self.write_raw_cache({"checked_at": stamp, "version": "9.9.9"})

            with mock.patch(
                "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
            ):
                self.assertEqual(get_latest_remote_version(), "2.0.0", stamp)

    def test_non_string_cached_version_is_ignored(self):
        for version in (1.5, None, ["1.4.3"], {}):
            self.write_cache(version)

            with mock.patch(
                "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
            ):
                self.assertEqual(get_latest_remote_version(), "2.0.0", version)

    def test_empty_cached_version_is_ignored(self):
        self.write_cache("   ")

        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ):
            self.assertEqual(get_latest_remote_version(), "2.0.0")

    def test_fetches_from_pypi_and_caches_the_new_schema(self):
        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ):
            self.assertEqual(get_latest_remote_version(), "2.0.0")

        cached = self.read_cache()
        self.assertEqual(cached["version"], "2.0.0")
        datetime.fromisoformat(cached["checked_at"])
        self.assertNotIn("download_url", cached)

    def test_force_bypasses_a_fresh_cache(self):
        self.write_cache("9.9.9")

        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ) as fetch:
            self.assertEqual(get_latest_remote_version(force=True), "2.0.0")

        fetch.assert_called_once()
        self.assertEqual(self.read_cache()["version"], "2.0.0")

    def test_fetch_uses_bounded_urlopen_with_the_repo_headers(self):
        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ) as fetch:
            get_latest_remote_version()

        args, kwargs = fetch.call_args
        self.assertEqual(args[0], "https://pypi.org/pypi/gitpr-cli/json")
        self.assertEqual(kwargs["timeout"], 3)
        self.assertEqual(kwargs["hard_timeout"], 3)
        self.assertEqual(kwargs["headers"], {"User-Agent": "GitPR-Updater"})

    def test_returns_empty_string_when_offline(self):
        with mock.patch("src.updater.bounded_urlopen", return_value=None):
            self.assertEqual(get_latest_remote_version(), "")

    def test_non_json_body_returns_empty(self):
        with mock.patch("src.updater.bounded_urlopen", return_value=b"<html>"):
            self.assertEqual(get_latest_remote_version(), "")

    def test_body_without_a_version_returns_empty(self):
        with mock.patch("src.updater.bounded_urlopen", return_value=b'{"info": {}}'):
            self.assertEqual(get_latest_remote_version(), "")

    def test_invalid_remote_version_is_not_cached(self):
        with mock.patch(
            "src.updater.bounded_urlopen",
            return_value=self._pypi_payload("not-a-version"),
        ):
            self.assertEqual(get_latest_remote_version(), "")

        self.assertFalse(os.path.exists(self.cache_file))

    def test_cache_write_failure_still_returns_the_fetched_version(self):
        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ):
            with mock.patch("src.updater.os.replace", side_effect=OSError("locked")):
                self.assertEqual(get_latest_remote_version(), "2.0.0")

    def test_cache_write_leaves_no_temporary_file(self):
        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ):
            get_latest_remote_version()

        leftovers = [name for name in os.listdir(self.tmp_dir) if name.endswith(".tmp")]
        self.assertEqual(leftovers, [])


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

    def test_orders_versions_by_pep440(self):
        """1.4.10 is newer than 1.4.9 — the tuple comparison got this right too."""
        with mock.patch("src.updater.get_latest_remote_version", return_value="1.4.10"):
            self.assertTrue(enforce_update_required())

    def test_ignores_a_remote_prerelease_for_a_stable_install(self):
        """pip will not install a pre-release without --pre, so blocking is a dead end."""
        with mock.patch(
            "src.updater.get_latest_remote_version", return_value="9.9.9rc1"
        ):
            self.assertFalse(enforce_update_required())

    def test_blocks_a_remote_prerelease_for_a_prerelease_install(self):
        with mock.patch("src.updater.__version__", "9.9.9rc0"):
            with mock.patch(
                "src.updater.get_latest_remote_version", return_value="9.9.9rc1"
            ):
                self.assertTrue(enforce_update_required())

    def test_blocks_a_post_release(self):
        with mock.patch(
            "src.updater.get_latest_remote_version", return_value="9.9.9.post1"
        ):
            self.assertTrue(enforce_update_required())

    def test_does_not_block_on_an_invalid_remote_version(self):
        for value in ("not-a-version", 1.5, None):
            with mock.patch("src.updater.get_latest_remote_version", return_value=value):
                self.assertFalse(enforce_update_required(), value)


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

    def test_update_forces_the_network_despite_a_fresh_cache(self):
        self.write_cache("9.9.9")

        with mock.patch(
            "src.updater.bounded_urlopen", return_value=self._pypi_payload("2.0.0")
        ) as fetch:
            with mock.patch("click.secho") as secho:
                check_and_update()

        fetch.assert_called_once()
        printed = " ".join(str(call.args[0]) for call in secho.call_args_list)
        self.assertIn("2.0.0", printed)
        self.assertEqual(self.read_cache()["version"], "2.0.0")

    def test_update_reports_failure_offline_even_with_a_fresh_cache(self):
        self.write_cache("9.9.9")

        with mock.patch("src.updater.bounded_urlopen", return_value=None):
            with mock.patch("click.secho") as secho:
                check_and_update()

        printed = " ".join(str(call.args[0]) for call in secho.call_args_list)
        self.assertIn("Could not check for updates", printed)


class TestCliUpdateGate(UpdaterTestCase):
    """Wiring between cli() and the root gate, driven through Click."""

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


class TestCliSubcommandGate(UpdaterTestCase):
    """The same gate in front of subcommands, interactive runs only."""

    def prepare(self, argv, may_ask=True):
        """Pins the terminal answer and keeps the ledger off the real home."""
        stack = ExitStack()
        stack.enter_context(
            mock.patch("src.main._may_ask_the_user", return_value=may_ask)
        )
        stack.enter_context(mock.patch("src.ledger.configure_terminal"))
        stack.enter_context(mock.patch("src.ledger.ensure_ledger"))
        stack.enter_context(mock.patch("src.main.sys.argv", argv))
        self.addCleanup(stack.close)

    def test_blocks_an_interactive_subcommand(self):
        self.prepare(["gitpr", "badge", "--readme"])

        with mock.patch(
            "src.main.enforce_update_required", return_value=True
        ) as gate:
            result = CliRunner().invoke(cli, ["badge", "--readme"])

        self.assertEqual(result.exit_code, 1)
        gate.assert_called_once()

    def test_prints_the_pip_command_when_outdated(self):
        self.prepare(["gitpr", "badge", "--readme"])

        with mock.patch("src.updater.get_latest_remote_version", return_value="9.9.9"):
            result = CliRunner().invoke(cli, ["badge", "--readme"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("pip install --upgrade gitpr-cli", result.output)

    def test_runs_when_the_version_is_current(self):
        self.prepare(["gitpr", "badge", "--readme"])

        with mock.patch(
            "src.updater.get_latest_remote_version", return_value=__version__
        ):
            result = CliRunner().invoke(cli, ["badge", "--readme"])

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("must be updated", result.output)

    def test_subcommand_is_exempt_without_a_terminal(self):
        """CliRunner streams are not TTYs, so the real helper answers False."""
        with mock.patch("src.main.enforce_update_required") as gate:
            result = CliRunner().invoke(cli, ["badge", "--readme"])

        self.assertEqual(result.exit_code, 0)
        gate.assert_not_called()

    def test_subcommand_help_is_exempt_in_an_interactive_run(self):
        self.prepare(["gitpr", "badge", "-h"])

        with mock.patch("src.main.enforce_update_required") as gate:
            result = CliRunner().invoke(cli, ["badge", "-h"])

        self.assertEqual(result.exit_code, 0)
        gate.assert_not_called()

    def test_update_flag_with_a_subcommand_is_exempt(self):
        self.prepare(["gitpr", "--update", "badge"])

        with mock.patch("src.main.enforce_update_required") as gate:
            CliRunner().invoke(cli, ["--update", "badge"])

        gate.assert_not_called()

    def test_help_tokens_are_detected_in_the_raw_argv(self):
        from src.main import _subcommand_help_in_argv

        self.assertTrue(_subcommand_help_in_argv(["gitpr", "release", "-h"]))
        self.assertTrue(_subcommand_help_in_argv(["gitpr", "release", "--help"]))
        self.assertFalse(_subcommand_help_in_argv(["gitpr", "release", "--h"]))
        self.assertFalse(_subcommand_help_in_argv(["gitpr", "release"]))
