"""Unit tests for the remote diff's normalization and filtering.

A diff from a forge API is not a diff from git: it may carry CRLF, it may be a
file summary wearing a diff's name (Azure), and it is the one diff git's own
``:(exclude)`` pathspecs never filtered. Each of the three functions below
covers one of those, and the sections they split are the ones
``diff_parser.split_patch_sections`` reports — so the GitLab header synthesis is
exercised here too, by feeding the shapes GitLab actually serves.
"""
import unittest

from src.review.diff_normalizer import (
    filter_excluded_sections,
    is_reviewable_diff,
    normalize_newlines,
)

PATCH = (
    "diff --git a/src/app.py b/src/app.py\n"
    "--- a/src/app.py\n"
    "+++ b/src/app.py\n"
    "@@ -1,2 +1,2 @@\n"
    " def greet(name):\n"
    "-    return 'Hello'\n"
    "+    return f'Hello, {name}'\n"
)

LOCK = (
    "diff --git a/poetry.lock b/poetry.lock\n"
    "--- a/poetry.lock\n"
    "+++ b/poetry.lock\n"
    "@@ -1 +1 @@\n"
    "-old\n"
    "+new\n"
)


class TestNormalizeNewlines(unittest.TestCase):
    def test_lf_is_returned_untouched(self):
        """The same object, not a copy: the common case costs nothing."""
        self.assertIs(normalize_newlines(PATCH), PATCH)

    def test_crlf_becomes_lf(self):
        self.assertEqual(normalize_newlines(PATCH.replace("\n", "\r\n")), PATCH)

    def test_a_lone_cr_becomes_lf(self):
        self.assertEqual(normalize_newlines("a\rb"), "a\nb")

    def test_an_empty_diff_survives(self):
        self.assertEqual(normalize_newlines(""), "")


class TestIsReviewableDiff(unittest.TestCase):
    def test_a_real_patch_is_reviewable(self):
        self.assertTrue(is_reviewable_diff(PATCH))

    def test_a_patch_without_the_git_header_is_still_reviewable(self):
        """An AI-shaped patch has hunks only — the chunker accepts those too."""
        self.assertTrue(is_reviewable_diff("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n"))

    def test_azure_file_summary_is_not_reviewable(self):
        """What Azure DevOps answers with instead of a diff."""
        summary = (
            "/src/app.py (+12 -3)\n"
            "/src/other.py (+1 -0)\n"
        )
        self.assertFalse(is_reviewable_diff(summary))

    def test_prose_is_not_reviewable(self):
        self.assertFalse(is_reviewable_diff("This merge request changes three files."))

    def test_an_empty_diff_is_not_reviewable(self):
        self.assertFalse(is_reviewable_diff(""))

    def test_a_crlf_patch_is_reviewable(self):
        """The forge may serve CRLF; the CR is stripped before the prefix check."""
        self.assertTrue(is_reviewable_diff(PATCH.replace("\n", "\r\n")))

    def test_a_mention_inside_a_hunk_does_not_make_prose_reviewable(self):
        """The prefix has to start the line — a hunk's content cannot vouch for it."""
        self.assertFalse(is_reviewable_diff("see the diff --git section above"))


class TestFilterExcludedSections(unittest.TestCase):
    def test_without_patterns_the_diff_is_returned_untouched(self):
        filtered, dropped = filter_excluded_sections(PATCH + LOCK, [])
        self.assertEqual(filtered, PATCH + LOCK)
        self.assertEqual(dropped, [])

    def test_a_matching_file_is_dropped_and_named(self):
        filtered, dropped = filter_excluded_sections(PATCH + LOCK, ["*.lock"])

        self.assertNotIn("poetry.lock", filtered)
        self.assertIn("src/app.py", filtered)
        self.assertEqual(dropped, ["poetry.lock"])

    def test_a_star_crosses_directories(self):
        """fnmatch's '*' spans '/', so a basename pattern matches a nested path."""
        nested = LOCK.replace("a/poetry.lock", "a/vendor/deep/poetry.lock").replace(
            "b/poetry.lock", "b/vendor/deep/poetry.lock"
        )
        _filtered, dropped = filter_excluded_sections(nested, ["*.lock"])
        self.assertEqual(dropped, ["vendor/deep/poetry.lock"])

    def test_a_dropped_file_keeps_the_others_intact(self):
        """What is kept is byte-for-byte the section git would have produced."""
        filtered, _dropped = filter_excluded_sections(PATCH + LOCK, ["*.lock"])
        self.assertEqual(filtered, PATCH.rstrip("\n"))

    def test_every_file_matching_leaves_an_empty_diff(self):
        filtered, dropped = filter_excluded_sections(LOCK, ["*.lock"])
        self.assertEqual(filtered.strip(), "")
        self.assertEqual(dropped, ["poetry.lock"])

    def test_nothing_matching_reports_nothing_dropped(self):
        filtered, dropped = filter_excluded_sections(PATCH, ["*.lock"])
        self.assertEqual(filtered, PATCH)
        self.assertEqual(dropped, [])

    def test_a_diff_without_sections_is_returned_untouched(self):
        """Prose never reaches here, but the filter must not eat it if it does."""
        filtered, dropped = filter_excluded_sections("not a diff", ["*.lock"])
        self.assertEqual(filtered, "not a diff")
        self.assertEqual(dropped, [])

    def test_a_synthesized_gitlab_section_is_filtered_by_its_path(self):
        """The path a filter matches on comes from GitLab's own headers."""
        synthesized = (
            "diff --git a/node_modules/pkg/index.js b/node_modules/pkg/index.js\n"
            "--- a/node_modules/pkg/index.js\n"
            "+++ b/node_modules/pkg/index.js\n"
            "@@ -1 +1 @@\n-a\n+b\n"
        )
        _filtered, dropped = filter_excluded_sections(
            PATCH + synthesized, ["node_modules/*"]
        )
        self.assertEqual(dropped, ["node_modules/pkg/index.js"])

    def test_a_deletion_is_filtered_by_its_path_too(self):
        """A deleted file reports '+++ /dev/null' — the path comes from elsewhere."""
        deletion = (
            "diff --git a/poetry.lock b/poetry.lock\n"
            "--- a/poetry.lock\n"
            "+++ /dev/null\n"
            "@@ -1 +0,0 @@\n-old\n"
        )
        _filtered, dropped = filter_excluded_sections(deletion, ["*.lock"])
        self.assertEqual(dropped, ["poetry.lock"])


if __name__ == "__main__":
    unittest.main()
