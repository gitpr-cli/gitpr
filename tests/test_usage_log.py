"""Tests for src/usage_log.py — the general usage log.

The log writes into the user's home, so every test here redirects HOME (and
USERPROFILE, which is what expanduser reads on Windows) to a temporary
directory; nothing touches ~/.gitpr/logs for real.
"""
import io
import os
import re
import sys
import tempfile
import unittest
import uuid
from datetime import datetime
from pathlib import Path
from unittest import mock

from src import usage_log

# Imported before any sandbox is applied, on purpose. src.i18n writes
# GITPR_LANG into ~/.gitpr/.env from its module body when the variable is
# unset, so letting it load for the first time inside a redirected HOME would
# make it fail on the missing directory instead.
import src.i18n  # noqa: F401  (imported for its side effect's sake)
import src.updater  # noqa: F401

LINE_RE = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \| (v[^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+)$"
)


class HomeSandbox:
    """Redirects the home directory for the duration of a test."""

    def __init__(self, home):
        self.home = home

    def __enter__(self):
        self._patch = mock.patch.dict(
            os.environ, {"HOME": self.home, "USERPROFILE": self.home}
        )
        self._patch.start()
        return self

    def __exit__(self, *exc):
        self._patch.stop()
        return False


class TestLogPath(unittest.TestCase):
    def test_same_day_maps_to_the_same_file(self):
        self.assertEqual(usage_log._log_path("2026-09-12"), usage_log._log_path("2026-09-12"))

    def test_different_days_map_to_different_files(self):
        self.assertNotEqual(
            usage_log._log_path("2026-09-12"), usage_log._log_path("2026-09-13")
        )

    def test_filename_is_a_uuid_with_a_log_extension(self):
        name = usage_log._log_path("2026-09-12").name
        self.assertTrue(name.endswith(".log"), name)
        # Parses as a real uuid, not just "some string"
        self.assertEqual(str(uuid.UUID(name[: -len(".log")])), name[: -len(".log")])

    def test_lives_in_the_gitpr_logs_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with HomeSandbox(tmp):
                path = usage_log._log_path("2026-09-12")
                self.assertEqual(path.parent, Path(tmp) / ".gitpr" / "logs")


class TestRepoLabel(unittest.TestCase):
    def test_https_remote(self):
        self.assertEqual(
            usage_log._repo_label("https://github.com/natanfiuza/gitpr.git"),
            "natanfiuza/gitpr",
        )

    def test_scp_like_remote(self):
        self.assertEqual(
            usage_log._repo_label("git@github.com:natanfiuza/gitpr.git"),
            "natanfiuza/gitpr",
        )

    def test_ssh_remote_with_port(self):
        self.assertEqual(
            usage_log._repo_label("ssh://git@gitlab.example.com:2222/group/sub/repo.git"),
            "group/sub/repo",
        )

    def test_azure_devops_remote_drops_the_git_marker(self):
        self.assertEqual(
            usage_log._repo_label("https://dev.azure.com/contoso/MyProject/_git/MyRepo"),
            "contoso/MyProject/MyRepo",
        )

    def test_remote_without_the_dot_git_suffix(self):
        self.assertEqual(
            usage_log._repo_label("https://bitbucket.org/team/repo"), "team/repo"
        )

    def test_empty_remote(self):
        self.assertEqual(usage_log._repo_label(""), "")
        self.assertEqual(usage_log._repo_label(None), "")

    def test_a_github_only_helper_would_have_failed_here(self):
        """Guards the reason this function exists instead of core.get_repo_name()."""
        self.assertEqual(
            usage_log._repo_label("git@gitlab.com:grupo/projeto.git"), "grupo/projeto"
        )


class TestEnabledFlag(unittest.TestCase):
    def test_disabled_values(self):
        for value in ("false", "0", "no", "off", "n", "FALSE", " false "):
            with mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": value}):
                self.assertFalse(usage_log._enabled(), value)

    def test_enabled_values(self):
        for value in ("true", "1", "yes", "y", "TRUE"):
            with mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": value}):
                self.assertTrue(usage_log._enabled(), value)

    def test_defaults_to_on_when_unset(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("GITPR_SHOW_LOGS", None)
            self.assertTrue(usage_log._enabled())


class TestCommand(unittest.TestCase):
    def test_program_name_and_flags(self):
        with mock.patch.object(sys, "argv", ["/usr/bin/gitpr", "-c"]):
            self.assertEqual(usage_log._command(), "gitpr -c")

    def test_windows_executable_suffix_is_dropped(self):
        with mock.patch.object(sys, "argv", [r"C:\tools\gitpr.exe", "--status"]):
            self.assertEqual(usage_log._command(), "gitpr --status")

    def test_empty_argv_does_not_raise(self):
        with mock.patch.object(sys, "argv", []):
            self.assertEqual(usage_log._command(), "gitpr")

    def test_embedded_newlines_are_flattened(self):
        with mock.patch.object(sys, "argv", ["gitpr", "-c", "line1\nline2"]):
            self.assertNotIn("\n", usage_log._command())


class TestLogUsage(unittest.TestCase):
    def _sandbox(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return tmp.name

    def test_writes_one_line_per_call_into_the_same_daily_file(self):
        home = self._sandbox()
        with HomeSandbox(home), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "true"}):
            with mock.patch.object(usage_log, "_git_identity", return_value=("me/repo", "Ana <a@x.io>")):
                with mock.patch.object(sys, "argv", ["gitpr", "-c"]):
                    first = usage_log.log_usage()
                    second = usage_log.log_usage()

            self.assertEqual(first, second)
            self.assertTrue(first.exists())

            lines = first.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2, lines)

            match = LINE_RE.match(lines[0])
            self.assertIsNotNone(match, lines[0])
            stamp, version, command, repo, author = match.groups()
            self.assertEqual(command, "gitpr -c")
            self.assertEqual(repo, "me/repo")
            self.assertEqual(author, "Ana <a@x.io>")
            self.assertTrue(version.startswith("v"))
            # The stamp must be a real timestamp, not a placeholder
            datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")

    def test_the_file_is_named_for_today(self):
        home = self._sandbox()
        with HomeSandbox(home), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "true"}):
            with mock.patch.object(usage_log, "_git_identity", return_value=("", "")):
                path = usage_log.log_usage()

        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(path.name, usage_log._log_path(today).name)

    def test_missing_repository_and_author_degrade_to_a_dash(self):
        home = self._sandbox()
        with HomeSandbox(home), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "true"}):
            with mock.patch.object(usage_log, "_git_identity", return_value=("", "")):
                path = usage_log.log_usage()

        line = path.read_text(encoding="utf-8").strip()
        self.assertTrue(line.endswith("| - | -"), line)

    def test_nothing_is_written_when_disabled(self):
        home = self._sandbox()
        with HomeSandbox(home), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "false"}):
            self.assertIsNone(usage_log.log_usage())

        # The logs directory itself is created by nothing else in the project,
        # so its absence proves the entry was never written.
        self.assertFalse((Path(home) / ".gitpr" / "logs").exists())

    def test_git_missing_does_not_raise_and_still_logs(self):
        home = self._sandbox()
        with HomeSandbox(home), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "true"}):
            with mock.patch.object(
                usage_log.subprocess, "run", side_effect=FileNotFoundError("no git")
            ):
                path = usage_log.log_usage()

        self.assertIsNotNone(path)
        self.assertTrue(path.exists())

    def test_git_failure_does_not_raise(self):
        home = self._sandbox()
        failed = mock.Mock(returncode=1, stdout="")
        with HomeSandbox(home), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "true"}):
            with mock.patch.object(usage_log.subprocess, "run", return_value=failed):
                path = usage_log.log_usage()

        self.assertIsNotNone(path)

    def test_unwritable_home_does_not_raise(self):
        """A file where the home directory should be — mkdir cannot succeed."""
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            blocker = handle.name
        self.addCleanup(lambda: os.unlink(blocker))

        with HomeSandbox(blocker), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "true"}):
            self.assertIsNone(usage_log.log_usage())

    def test_empty_argv_does_not_raise(self):
        home = self._sandbox()
        with HomeSandbox(home), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "true"}):
            with mock.patch.object(usage_log, "_git_identity", return_value=("", "")):
                with mock.patch.object(sys, "argv", []):
                    self.assertIsNotNone(usage_log.log_usage())

    def test_never_prints_to_stdout(self):
        """The MCP server would have its JSON-RPC stream corrupted by a print."""
        home = self._sandbox()
        captured = io.StringIO()
        with HomeSandbox(home), mock.patch.dict(os.environ, {"GITPR_SHOW_LOGS": "true"}):
            with mock.patch.object(usage_log, "_git_identity", return_value=("r/r", "A <a@b>")):
                with mock.patch.object(sys, "stdout", captured):
                    usage_log.log_usage()

        self.assertEqual(captured.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
