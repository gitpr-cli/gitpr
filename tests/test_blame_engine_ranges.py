"""Tests for the fine-grained porcelain blame reader (get_blame_for_range).

The archaeology engine (execute_git_blame / run_blame_analysis) is untouched;
this file only covers the new range/porcelain function.
"""
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.blame_engine import get_blame_for_range, _parse_blame_porcelain

PORCELAIN_SAMPLE = (
    "0e0e6bd84a05a2f3deadbeefcafe000011112222 1 1 1\n"
    "author Ana Silva\n"
    "author-mail <ana@example.com>\n"
    "author-time 1700000000\n"
    "author-tz -0300\n"
    "committer Ana Silva\n"
    "committer-mail <ana@example.com>\n"
    "committer-time 1700000000\n"
    "committer-tz -0300\n"
    "summary feat: add a thing\n"
    "filename a.py\n"
    "\tdef hello():\n"
    "0000000000000000000000000000000000000000 2 2 1\n"
    "author Bob Lima\n"
    "author-mail <bob@example.com>\n"
    "author-time 0\n"
    "author-tz +0000\n"
    "committer Bob Lima\n"
    "committer-mail <bob@example.com>\n"
    "committer-time 0\n"
    "committer-tz +0000\n"
    "summary wip\n"
    "filename a.py\n"
    "\treturn 1\n"
    "^11223344556677889900aabbccddeeff00112233 3 3 1\n"
    "author Carla Reis\n"
    "author-mail <carla@example.com>\n"
    "author-time 1600000000\n"
    "author-tz +0000\n"
    "committer Carla Reis\n"
    "committer-mail <carla@example.com>\n"
    "committer-time 1600000000\n"
    "committer-tz +0000\n"
    "summary boundary root commit\n"
    "filename a.py\n"
    "\treturn 2\n"
)


class TestGetBlameForRangeCommand(unittest.TestCase):
    @patch("src.blame_engine.subprocess.run")
    def test_builds_porcelain_command_and_parses(self, mock_run):
        mock_run.return_value = SimpleNamespace(stdout=PORCELAIN_SAMPLE)
        hits = get_blame_for_range("src/a.py", 10, 25, repo_path=r"C:\repo")

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertEqual(cmd[:3], ["git", "blame", "--line-porcelain"])
        self.assertIn("-L", cmd)
        self.assertEqual(cmd[cmd.index("-L") + 1], "10,25")
        self.assertEqual(cmd[-2:], ["--", "src/a.py"])
        self.assertEqual(kwargs["cwd"], r"C:\repo")
        self.assertEqual(kwargs["encoding"], "utf-8")
        self.assertEqual(kwargs["errors"], "replace")
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertTrue(kwargs["check"])

        # 40-zero "Not Committed Yet" block is skipped; boundary is accepted.
        self.assertEqual(len(hits), 2)
        first = hits[0]
        self.assertEqual(first.file_path, "src/a.py")
        self.assertEqual(first.line_number, 1)
        self.assertEqual(first.author_name, "Ana Silva")
        self.assertEqual(first.author_email, "ana@example.com")
        self.assertEqual(first.commit_hash, "0e0e6bd84a05a2f3deadbeefcafe000011112222")
        # author-time 1700000000 == 2023-11-14T22:13:20Z.
        self.assertEqual(first.commit_date, "2023-11-14")

    @patch("src.blame_engine.subprocess.run")
    def test_missing_repo_path_defaults_to_process_cwd(self, mock_run):
        mock_run.return_value = SimpleNamespace(stdout="")
        get_blame_for_range("a.txt", 1, 5)
        _, kwargs = mock_run.call_args
        self.assertIsNone(kwargs["cwd"])

    @patch("src.blame_engine.subprocess.run")
    def test_errors_return_empty_list(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(128, "git blame")
        self.assertEqual(get_blame_for_range("a.txt", 1, 5), [])

        mock_run.side_effect = FileNotFoundError("git")
        self.assertEqual(get_blame_for_range("a.txt", 1, 5), [])


class TestParseBlamePorcelain(unittest.TestCase):
    def test_returns_empty_for_empty_output(self):
        self.assertEqual(_parse_blame_porcelain("", "a.py"), [])

    def test_missing_email_is_tolerated(self):
        raw = (
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 1 1 1\n"
            "author Some One\n"
            "author-time 1600000000\n"
            "\tcontent\n"
        )
        hits = _parse_blame_porcelain(raw, "a.py")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].author_email, "")
        self.assertEqual(hits[0].author_name, "Some One")

    def test_invalid_author_time_yields_empty_date(self):
        raw = (
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 1 1 1\n"
            "author Some One\n"
            "author-mail <s@example.com>\n"
            "author-time banana\n"
            "\tcontent\n"
        )
        hits = _parse_blame_porcelain(raw, "a.py")
        self.assertEqual(hits[0].commit_date, "")

    def test_non_ascii_content_does_not_break_parsing(self):
        raw = (
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 1 1 1\n"
            "author Jo\u00e3o\n"
            "author-mail <joao@example.com>\n"
            "author-time 1600000000\n"
            "\tlinha com acentua\u00e7\u00e3o \u2014 ok\n"
        )
        hits = _parse_blame_porcelain(raw, "a.py")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].author_name, "Jo\u00e3o")


if __name__ == "__main__":
    unittest.main()
