"""Unit tests for the pure Conventional Commits classifier (spec section 8.1/8.3)."""

import unittest

from src.changelog_builder import ChangeCategory
from src.commit_classifier import classify_commit, classify_commits


def _commit(subject, body="", **overrides):
    """Builds a classified commit with sensible defaults for testing."""
    defaults = {
        "commit_hash": "a" * 40,
        "short_hash": "aaaaaaa",
        "author_name": "Ada Lovelace",
        "author_email": "ada@example.com",
        "date": "2026-09-01T10:00:00+00:00",
    }
    defaults.update(overrides)
    return classify_commit(subject=subject, body=body, **defaults)


class TestHeaderTypes(unittest.TestCase):
    """Canonical Conventional Commits types map to the right categories."""

    def test_all_supported_types(self):
        expected = {
            "feat: add widget": ChangeCategory.FEATURE,
            "fix: repair widget": ChangeCategory.FIX,
            "perf: speed up widget": ChangeCategory.PERFORMANCE,
            "docs: explain widget": ChangeCategory.DOCS,
            "refactor: tidy widget": ChangeCategory.REFACTOR,
            "chore: bump deps": ChangeCategory.CHORE,
        }
        for subject, category in expected.items():
            commit = _commit(subject)
            self.assertEqual(commit.category, category, subject)
            self.assertFalse(commit.breaking)
            self.assertIsNone(commit.scope)
            self.assertIsNone(commit.pr_number)

    def test_unknown_type_falls_back_to_other(self):
        commit = _commit("test: cover the widget")
        self.assertEqual(commit.category, ChangeCategory.OTHER)
        # Still a Conventional Commits header: the original prefix is kept.
        self.assertEqual(commit.raw_type, "test")

    def test_type_is_case_insensitive(self):
        commit = _commit("FIX: repair widget")
        self.assertEqual(commit.category, ChangeCategory.FIX)

    def test_subject_is_cleaned(self):
        commit = _commit("  feat: add widget  ")
        self.assertEqual(commit.subject, "add widget")


class TestScope(unittest.TestCase):
    def test_scope_extracted(self):
        commit = _commit("feat(linter): add yaml rule")
        self.assertEqual(commit.scope, "linter")

    def test_scope_missing_is_none(self):
        self.assertIsNone(_commit("feat: add widget").scope)

    def test_hyphen_scope_allowed(self):
        self.assertEqual(_commit("fix(core-api): retry").scope, "core-api")

    def test_empty_scope_is_none(self):
        commit = _commit("feat(): add widget")
        self.assertIsNone(commit.scope)


class TestBreaking(unittest.TestCase):
    def test_bang_after_type(self):
        self.assertTrue(_commit("feat!: drop python 2").breaking)

    def test_bang_after_scope(self):
        self.assertTrue(_commit("feat(api)!: rename endpoint").breaking)

    def test_breaking_change_in_body(self):
        commit = _commit(
            "feat: replace config engine",
            body="Legacy keys stop working.\n\nBREAKING CHANGE: config moved to dotenv.",
        )
        self.assertTrue(commit.breaking)

    def test_breaking_change_dash_and_case_variants(self):
        self.assertTrue(
            _commit("fix: x", body="breaking-change: nope").breaking
        )
        self.assertTrue(
            _commit("fix: x", body="Breaking Change: nope").breaking
        )

    def test_plain_commit_is_not_breaking(self):
        self.assertFalse(_commit("feat: add widget", body="Nothing else.").breaking)

    def test_non_conventional_with_breaking_marker(self):
        # No conventional header, but the body marks a breaking change.
        commit = _commit("Upgrade everything", body="BREAKING CHANGE: new layout")
        self.assertTrue(commit.breaking)
        self.assertEqual(commit.category, ChangeCategory.OTHER)
        self.assertEqual(commit.raw_type, "")


class TestPrNumber(unittest.TestCase):
    def test_squash_subject_extracts_pr(self):
        commit = _commit("fix: crash on windows (#42)")
        self.assertEqual(commit.pr_number, 42)
        self.assertEqual(commit.subject, "crash on windows (#42)")

    def test_no_pr_number_is_none(self):
        self.assertIsNone(_commit("fix: crash on windows").pr_number)

    def test_double_digit_pr(self):
        self.assertEqual(_commit("feat: big feature (#1234)").pr_number, 1234)


class TestNonConventional(unittest.TestCase):
    """Commits outside the standard land in OTHER without raising."""

    def test_merge_style_subject(self):
        commit = _commit("Merge branch 'main' into feature/x")
        self.assertEqual(commit.category, ChangeCategory.OTHER)
        self.assertEqual(commit.raw_type, "")
        self.assertEqual(commit.scope, None)

    def test_plain_sentence_subject(self):
        commit = _commit("Improves the whole thing")
        self.assertEqual(commit.category, ChangeCategory.OTHER)
        self.assertEqual(commit.raw_type, "")

    def test_colon_without_type(self):
        commit = _commit("Rename: everything moved around")
        self.assertEqual(commit.category, ChangeCategory.OTHER)

    def test_no_subject_at_all(self):
        commit = _commit("")
        self.assertEqual(commit.category, ChangeCategory.OTHER)
        self.assertEqual(commit.raw_type, "")

    def test_metadata_always_present(self):
        commit = classify_commit(
            commit_hash="abc123",
            short_hash="abc1234",
            author_name="Grace",
            author_email="grace@example.com",
            date="2026-09-01T00:00:00Z",
            subject="totally free text",
            body="",
        )
        self.assertEqual(commit.hash, "abc123")
        self.assertEqual(commit.author_email, "grace@example.com")


class TestClassifyBatch(unittest.TestCase):
    def test_batch_preserves_order_and_counts(self):
        raw = [
            {"hash": "1", "short_hash": "1111111", "subject": "feat: one",
             "author_name": "A", "author_email": "a@x.com", "date": "d", "body": ""},
            {"hash": "2", "short_hash": "2222222", "subject": "random text",
             "author_name": "A", "author_email": "a@x.com", "date": "d", "body": ""},
            {"hash": "3", "short_hash": "3333333", "subject": "fix: two",
             "author_name": "B", "author_email": "b@x.com", "date": "d", "body": ""},
        ]
        commits = classify_commits(raw)
        self.assertEqual(len(commits), 3)
        self.assertEqual(commits[0].category, ChangeCategory.FEATURE)
        self.assertEqual(commits[1].category, ChangeCategory.OTHER)
        self.assertEqual(commits[2].category, ChangeCategory.FIX)
        self.assertEqual([c.hash for c in commits], ["1", "2", "3"])


if __name__ == "__main__":
    unittest.main()
