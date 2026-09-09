"""Unit tests for the pure semver bump decision (spec section 8.2, matrix)."""

import unittest

from src.changelog_builder import ChangeCategory, ClassifiedCommit
from src.version_bump import (
    apply_bump,
    format_semver,
    parse_semver_tag,
    suggest_next_version,
)


def _commit(category, breaking=False):
    """Builds a minimal classified commit carrying only the bump-relevant fields."""
    return ClassifiedCommit(
        hash="h",
        short_hash="hhhhhhh",
        author_name="A",
        author_email="a@x.com",
        date="d",
        subject="s",
        body="",
        category=category,
        scope=None,
        breaking=breaking,
        pr_number=None,
        raw_type="",
    )


class TestParseSemverTag(unittest.TestCase):
    def test_full_version(self):
        self.assertEqual(parse_semver_tag("v1.2.3"), ("v", 1, 2, 3))

    def test_without_prefix(self):
        self.assertEqual(parse_semver_tag("1.2.3"), ("", 1, 2, 3))

    def test_partial_segments_default_to_zero(self):
        self.assertEqual(parse_semver_tag("v1"), ("v", 1, 0, 0))
        self.assertEqual(parse_semver_tag("2.5"), ("", 2, 5, 0))

    def test_prerelease_suffix_parses(self):
        self.assertEqual(parse_semver_tag("1.2.3-rc.1"), ("", 1, 2, 3))

    def test_non_version_tag_is_none(self):
        for tag in (None, "", "release-2026", "stable", "v1.x", "v.1.2", "v1.2.3.4"):
            self.assertIsNone(parse_semver_tag(tag), tag)


class TestApplyBump(unittest.TestCase):
    def test_major_resets_minor_and_patch(self):
        self.assertEqual(apply_bump(("v", 1, 2, 3), "major"), "v2.0.0")

    def test_minor_resets_patch_and_keeps_major(self):
        self.assertEqual(apply_bump(("v", 1, 2, 3), "minor"), "v1.3.0")

    def test_patch_increments_patch(self):
        self.assertEqual(apply_bump(("", 1, 2, 3), "patch"), "1.2.4")

    def test_format_semver_roundtrip(self):
        self.assertEqual(format_semver(("v", 3, 0, 0)), "v3.0.0")


class TestSuggestNextVersion(unittest.TestCase):
    """Full decision matrix from the spec: fixes -> PATCH, feature -> MINOR,
    any breaking -> MAJOR regardless of the rest of the range."""

    def _suggest(self, commits, previous_tag):
        return suggest_next_version(commits, previous_tag)

    def test_only_fixes_go_to_patch(self):
        commits = [
            _commit(ChangeCategory.FIX),
            _commit(ChangeCategory.CHORE),
            _commit(ChangeCategory.DOCS),
            _commit(ChangeCategory.REFACTOR),
        ]
        self.assertEqual(self._suggest(commits, "v1.2.3"), "v1.2.4")

    def test_feature_without_breaking_goes_to_minor(self):
        commits = [
            _commit(ChangeCategory.FEATURE),
            _commit(ChangeCategory.FIX),
            _commit(ChangeCategory.CHORE),
        ]
        self.assertEqual(self._suggest(commits, "v1.2.3"), "v1.3.0")

    def test_any_breaking_goes_to_major(self):
        commits = [
            _commit(ChangeCategory.FIX),
            _commit(ChangeCategory.FEATURE),
            _commit(ChangeCategory.FEATURE, breaking=True),
        ]
        self.assertEqual(self._suggest(commits, "v1.2.3"), "v2.0.0")

    def test_breaking_in_other_category_still_major(self):
        # A non-conventional commit flagged breaking still forces MAJOR.
        commits = [
            _commit(ChangeCategory.OTHER, breaking=True),
            _commit(ChangeCategory.FIX),
        ]
        self.assertEqual(self._suggest(commits, "1.2.3"), "2.0.0")

    def test_prefix_is_preserved(self):
        self.assertEqual(self._suggest([_commit(ChangeCategory.FIX)], "1.2.3"), "1.2.4")
        self.assertEqual(self._suggest([_commit(ChangeCategory.FIX)], "v1.2.3"), "v1.2.4")

    def test_no_previous_tag_suggests_nothing(self):
        self.assertIsNone(self._suggest([_commit(ChangeCategory.FEATURE)], None))

    def test_non_version_previous_tag_suggests_nothing(self):
        self.assertIsNone(self._suggest([_commit(ChangeCategory.FEATURE)], "release-1"))

    def test_empty_range_still_patches(self):
        # Nothing merged since the last tag is still a valid (no-op) patch base.
        self.assertEqual(self._suggest([], "v1.2.3"), "v1.2.4")


if __name__ == "__main__":
    unittest.main()
