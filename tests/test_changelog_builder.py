"""Unit tests for the changelog Markdown builder and its pure helpers."""

import unittest

from src.changelog_builder import (
    ChangeCategory,
    ClassifiedCommit,
    build_release_section,
    normalize_contributors,
    organize_commits,
    release_body,
)
from src.i18n import CURRENT_LANG, set_lang


def _commit(
    category,
    subject="changed something",
    scope=None,
    breaking=False,
    author_name="Ada Lovelace",
    author_email="ada@example.com",
    short_hash="abc1234",
):
    return ClassifiedCommit(
        hash=short_hash * 5,
        short_hash=short_hash,
        author_name=author_name,
        author_email=author_email,
        date="2026-09-01T10:00:00+00:00",
        subject=subject,
        body="",
        category=category,
        scope=scope,
        breaking=breaking,
        pr_number=None,
        raw_type="feat" if category is ChangeCategory.FEATURE else "",
    )


class BuilderTestCase(unittest.TestCase):
    """Pins the interface language to English for deterministic assertions."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)


class TestBuildReleaseSection(BuilderTestCase):
    def _render(self, sections=None, breaking=None, summary="A great release.",
                contributors=None):
        return build_release_section(
            version="1.2.0",
            generated_at="2026-09-07T12:00:00+00:00",
            summary=summary,
            sections=sections or {},
            breaking_changes=breaking or [],
            contributors=contributors or [],
        )

    def test_heading_contains_version_and_date(self):
        markdown = self._render(summary="")
        self.assertIn("## [1.2.0] - 2026-09-07", markdown)
        self.assertTrue(markdown.startswith("## [1.2.0] - 2026-09-07"))

    def test_summary_subsection_rendered_only_when_present(self):
        markdown = self._render(
            sections={ChangeCategory.FIX: [_commit(ChangeCategory.FIX)]},
            summary="Fixed everything.",
        )
        self.assertIn("### Summary\nFixed everything.", markdown)
        markdown_no_summary = self._render(
            sections={ChangeCategory.FIX: [_commit(ChangeCategory.FIX)]}, summary=""
        )
        self.assertNotIn("### Summary", markdown_no_summary)

    def test_category_section_with_scope(self):
        markdown = self._render(
            sections={
                ChangeCategory.FEATURE: [
                    _commit(ChangeCategory.FEATURE, "add linter", scope="linter")
                ]
            },
            summary="",
        )
        self.assertIn("### ✨ Features\n- add linter (abc1234) — linter", markdown)

    def test_category_section_without_scope(self):
        markdown = self._render(
            sections={ChangeCategory.FIX: [_commit(ChangeCategory.FIX, "repair")]},
            summary="",
        )
        self.assertIn("### 🐛 Fixes\n- repair (abc1234)", markdown)

    def test_breaking_changes_section_and_dedup(self):
        breaking_feat = _commit(
            ChangeCategory.FEATURE, "drop old api", breaking=True
        )
        fix = _commit(ChangeCategory.FIX, "repair")
        sections, breaking = organize_commits([breaking_feat, fix])
        markdown = self._render(sections=sections, breaking=breaking, summary="")
        # Breaking commit appears under the Breaking heading...
        self.assertIn("### ⚠️ Breaking Changes\n- drop old api (abc1234)", markdown)
        # ...and is NOT duplicated inside Features.
        self.assertNotIn("### ✨ Features", markdown)
        self.assertIn("### 🐛 Fixes\n- repair (abc1234)", markdown)

    def test_empty_categories_are_skipped(self):
        markdown = self._render(
            sections={ChangeCategory.FEATURE: [_commit(ChangeCategory.FEATURE)]},
            summary="",
        )
        self.assertNotIn("### 📚 Docs", markdown)
        self.assertNotIn("### ♻️ Refactoring", markdown)
        self.assertNotIn("### 🔧 Chores", markdown)
        self.assertNotIn("### 📦 Other Changes", markdown)

    def test_other_category_rendered(self):
        markdown = self._render(
            sections={ChangeCategory.OTHER: [_commit(ChangeCategory.OTHER, "junk")]},
            summary="",
        )
        self.assertIn("### 📦 Other Changes\n- junk (abc1234)", markdown)

    def test_contributors_footer(self):
        markdown = self._render(summary="", contributors=["Ada Lovelace", "Grace Hopper"])
        self.assertIn("**Contributors:** Ada Lovelace, Grace Hopper", markdown)

    def test_no_footer_without_contributors(self):
        markdown = self._render(summary="", contributors=[])
        self.assertNotIn("Contributors", markdown)


class TestOrganizeCommits(unittest.TestCase):
    def test_splits_categories_and_breaking(self):
        commits = [
            _commit(ChangeCategory.FEATURE, "a"),
            _commit(ChangeCategory.FEATURE, "b", breaking=True),
            _commit(ChangeCategory.OTHER, "c"),
            _commit(ChangeCategory.CHORE, "d"),
        ]
        sections, breaking = organize_commits(commits)
        self.assertEqual(
            [c.subject for c in sections[ChangeCategory.FEATURE]], ["a"]
        )
        self.assertEqual([c.subject for c in sections[ChangeCategory.OTHER]], ["c"])
        self.assertEqual([c.subject for c in sections[ChangeCategory.CHORE]], ["d"])
        self.assertEqual([c.subject for c in breaking], ["b"])

    def test_empty_input(self):
        sections, breaking = organize_commits([])
        self.assertEqual(sections, {})
        self.assertEqual(breaking, [])


class TestNormalizeContributors(unittest.TestCase):
    def test_dedupes_by_email_and_sorts(self):
        commits = [
            _commit(ChangeCategory.FIX, author_name="Zed", author_email="z@x.com"),
            _commit(ChangeCategory.FEATURE, author_name="Ada", author_email="a@x.com"),
            # Same email, later name must not override the first seen name.
            _commit(ChangeCategory.CHORE, author_name="Renamed", author_email="z@x.com"),
        ]
        self.assertEqual(normalize_contributors(commits), ["Ada", "Zed"])

    def test_empty_input(self):
        self.assertEqual(normalize_contributors([]), [])


class TestReleaseBody(unittest.TestCase):
    def test_heading_is_stripped(self):
        markdown = "## [1.2.0] - 2026-09-07\n\n### Summary\nHi\n"
        self.assertEqual(release_body(markdown), "### Summary\nHi")

    def test_without_heading_returns_content(self):
        self.assertEqual(release_body("plain"), "plain")


if __name__ == "__main__":
    unittest.main()
