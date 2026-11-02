"""Tests for the local issue record (T1).

Everything runs against a temporary directory; the two git-repository tests
run ``git init`` there and never touch the checkout.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.issue_autoclose.issue_registry import (
    GITIGNORE_ENTRY,
    SCHEMA_VERSION,
    IssueRegistry,
    IssueRegistryError,
    RegisteredIssue,
    registry_path,
)

ISSUE = RegisteredIssue(
    repo="owner/name",
    number=123,
    title="Fix the thing",
    url="https://github.com/owner/name/issues/123",
    created_at="2026-11-01T09:00:00-03:00",
    branch="main",
)


def _git_init(root):
    subprocess.run(
        ["git", "init", "-q"],
        cwd=str(root),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


class RegistryRoundTripTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.registry = IssueRegistry(path=self.root / ".gitpr" / "conf" / "github.yml")

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_file_is_not_an_error(self):
        loaded = self.registry.load()
        self.assertIsNone(loaded.issue)
        self.assertEqual(loaded.error, "")

    def test_record_then_load_roundtrip(self):
        result = self.registry.record(ISSUE)
        self.assertTrue(result.path.exists())

        loaded = self.registry.load()
        self.assertEqual(loaded.error, "")
        self.assertEqual(loaded.issue, ISSUE)

    def test_record_writes_the_documented_schema(self):
        self.registry.record(ISSUE)
        text = self.registry.path.read_text(encoding="utf-8", errors="replace")
        self.assertIn(f"schema_version: {SCHEMA_VERSION}", text)
        self.assertIn("last_issue:", text)
        # No secret ever reaches the record: the fields are the contract.
        import yaml

        data = yaml.safe_load(text)
        self.assertEqual(
            set(data["last_issue"]),
            {"repo", "number", "title", "url", "created_at", "branch"},
        )

    def test_clear_removes_the_record(self):
        self.registry.record(ISSUE)
        self.assertTrue(self.registry.clear())
        self.assertFalse(self.registry.path.exists())
        self.assertIsNone(self.registry.load().issue)

    def test_clear_without_record_returns_false(self):
        self.assertFalse(self.registry.clear())

    def test_last_record_wins(self):
        self.registry.record(ISSUE)
        second = RegisteredIssue(
            repo=ISSUE.repo, number=456, title="Second", url=ISSUE.url,
            created_at=ISSUE.created_at, branch="main",
        )
        self.registry.record(second)
        self.assertEqual(self.registry.load().issue.number, 456)

    def test_matches_repo_is_case_insensitive(self):
        self.registry.record(ISSUE)
        self.assertTrue(self.registry.matches_repo("Owner/Name"))
        self.assertFalse(self.registry.matches_repo("owner/other"))
        self.assertFalse(self.registry.matches_repo(""))

    def test_matches_repo_without_record(self):
        self.assertFalse(self.registry.matches_repo("owner/name"))

    def test_record_requires_the_contract_type(self):
        with self.assertRaises(TypeError):
            self.registry.record({"repo": "owner/name"})


class CorruptFileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.path = self.root / "github.yml"
        self.registry = IssueRegistry(path=self.path)

    def tearDown(self):
        self._tmp.cleanup()

    def _assert_corrupt(self, body):
        self.path.write_text(body, encoding="utf-8")
        loaded = self.registry.load()
        self.assertIsNone(loaded.issue)
        self.assertNotEqual(loaded.error, "")

    def test_not_yaml(self):
        self._assert_corrupt("{{{{")

    def test_not_a_mapping(self):
        self._assert_corrupt("- one\n- two\n")

    def test_missing_schema_version(self):
        self._assert_corrupt("last_issue:\n  repo: owner/name\n")

    def test_unsupported_schema_version(self):
        self._assert_corrupt("schema_version: 2\nlast_issue:\n  repo: owner/name\n")

    def test_missing_fields(self):
        self._assert_corrupt(
            "schema_version: 1\nlast_issue:\n  repo: owner/name\n  number: 1\n"
        )

    def test_invalid_number(self):
        for number in ("123", 0, -1, True, 1.5):
            body = (
                "schema_version: 1\n"
                "last_issue:\n"
                "  repo: owner/name\n"
                f"  number: {number!r}\n"
                "  title: T\n"
                "  url: https://example/issues/1\n"
                "  created_at: '2026-11-01T09:00:00'\n"
            )
            with self.subTest(number=number):
                self._assert_corrupt(body)

    def test_next_record_overwrites_a_corrupt_file(self):
        self.path.write_text("{{{{", encoding="utf-8")
        self.registry.record(ISSUE)
        self.assertEqual(self.registry.load().issue, ISSUE)


class AtomicWriteTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.path = self.root / "github.yml"
        self.registry = IssueRegistry(path=self.path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_failed_replace_keeps_the_previous_record(self):
        self.registry.record(ISSUE)
        before = self.path.read_text(encoding="utf-8", errors="replace")

        second = RegisteredIssue(
            repo=ISSUE.repo, number=999, title="Second", url=ISSUE.url,
            created_at=ISSUE.created_at,
        )
        with patch(
            "src.issue_autoclose.issue_registry.os.replace",
            side_effect=OSError("disk full"),
        ):
            with self.assertRaises(IssueRegistryError):
                self.registry.record(second)

        self.assertEqual(
            self.path.read_text(encoding="utf-8", errors="replace"), before
        )
        self.assertEqual(list(self.root.glob(".gitpr-issue-*.tmp")), [])


class GitignoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git_init(self.root)
        self.gitignore = self.root / ".gitignore"
        self.registry = IssueRegistry(
            path=self.root / ".gitpr" / "conf" / "github.yml"
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_entry_added_once(self):
        self.gitignore.write_text("*.log\n", encoding="utf-8")

        first = self.registry.record(ISSUE)
        self.assertTrue(first.gitignore_updated)
        content = self.gitignore.read_text(encoding="utf-8", errors="replace")
        self.assertTrue(content.endswith(f"\n{GITIGNORE_ENTRY}\n"))
        self.assertEqual(content.count(GITIGNORE_ENTRY), 1)

        second = self.registry.record(ISSUE)
        self.assertFalse(second.gitignore_updated)
        self.assertEqual(
            self.gitignore.read_text(encoding="utf-8", errors="replace"), content
        )

    def test_missing_final_newline_is_respected(self):
        self.gitignore.write_text("*.log", encoding="utf-8")
        self.registry.record(ISSUE)
        content = self.gitignore.read_text(encoding="utf-8", errors="replace")
        self.assertEqual(content, f"*.log\n{GITIGNORE_ENTRY}\n")

    def test_creates_gitignore_when_absent(self):
        self.registry.record(ISSUE)
        self.assertEqual(
            self.gitignore.read_text(encoding="utf-8", errors="replace"),
            f"{GITIGNORE_ENTRY}\n",
        )

    def test_already_ignored_by_a_broader_rule(self):
        self.gitignore.write_text(".gitpr/conf/\n", encoding="utf-8")
        result = self.registry.record(ISSUE)
        self.assertFalse(result.gitignore_updated)
        self.assertEqual(
            self.gitignore.read_text(encoding="utf-8", errors="replace"),
            ".gitpr/conf/\n",
        )

    def test_outside_a_repository_nothing_is_added(self):
        self._tmp.cleanup()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.registry = IssueRegistry(path=root / ".gitpr" / "conf" / "github.yml")

        result = self.registry.record(ISSUE)
        self.assertFalse(result.gitignore_updated)
        self.assertFalse((root / ".gitignore").exists())
        self.assertTrue(result.path.exists())

    def test_registry_path_is_anchored_at_the_repository_root(self):
        nested = self.root / "src" / "feature"
        nested.mkdir(parents=True)
        expected = self.root / ".gitpr" / "conf" / "github.yml"
        self.assertEqual(registry_path(nested), expected)


if __name__ == "__main__":
    unittest.main()
