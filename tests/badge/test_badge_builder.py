"""What the badge says, how it is coloured, and how the URL is encoded.

The expected URLs are written out in full rather than assembled from the
module's own pieces: a test that rebuilds the string the same way the code does
would agree with a broken escaping rule.
"""

from src.branding.badge_builder import (
    BRAND_URL,
    DEFAULT_STYLE,
    VALID_STYLES,
    build_pr_badge,
    build_readme_badge,
    normalize_style,
)
from src.branding.badge_data import BadgeCounts

PR_PREFIX = "[![GitPR](https://img.shields.io/badge/GitPR-"
PR_SUFFIX = f")]({BRAND_URL})"


class TestTheColourRule:
    """An error is red, advice is yellow, a clean diff is green."""

    def test_an_error_is_red(self):
        badge = build_pr_badge(BadgeCounts(errors=1, warnings=0))

        assert badge == f"{PR_PREFIX}1_error_%C2%B7_0_warnings-red{PR_SUFFIX}"

    def test_warnings_alone_are_yellow(self):
        badge = build_pr_badge(BadgeCounts(errors=0, warnings=2))

        assert badge == f"{PR_PREFIX}0_errors_%C2%B7_2_warnings-yellow{PR_SUFFIX}"

    def test_a_clean_diff_is_green(self):
        badge = build_pr_badge(BadgeCounts(errors=0, warnings=0))

        assert badge == f"{PR_PREFIX}no_issues-brightgreen{PR_SUFFIX}"

    def test_errors_win_over_warnings(self):
        """A blocking finding is never softened by a lesser one next to it."""
        badge = build_pr_badge(BadgeCounts(errors=3, warnings=9))

        assert badge.endswith("-red" + PR_SUFFIX)


class TestTheMessage:
    """The counts are printed as they were measured."""

    def test_both_counts_are_shown_even_when_one_is_zero(self):
        badge = build_pr_badge(BadgeCounts(errors=0, warnings=1))

        assert "0_errors" in badge
        assert "1_warning" in badge

    def test_each_count_pluralises_on_its_own(self):
        badge = build_pr_badge(BadgeCounts(errors=1, warnings=1))

        assert "1_error_%C2%B7_1_warning-" in badge

    def test_a_clean_diff_does_not_say_0_errors(self):
        """"0 errors · 0 warnings" reads as noise; the badge says it plainly."""
        badge = build_pr_badge(BadgeCounts(errors=0, warnings=0))

        assert "0_errors" not in badge


class TestTheLink:
    """The image is clickable, and the target is the documentation site."""

    def test_the_pr_badge_links_to_the_docs_site(self):
        badge = build_pr_badge(BadgeCounts(errors=0, warnings=1))

        assert badge.endswith(f"]({BRAND_URL})")

    def test_the_readme_badge_links_to_the_docs_site(self):
        assert build_readme_badge().endswith(f"]({BRAND_URL})")

    def test_the_readme_badge_shows_the_product_and_a_modest_claim(self):
        assert build_readme_badge().startswith(
            "[![GitPR](https://img.shields.io/badge/GitPR-quality--checked-blue"
        )


class TestTheEscaping:
    """shields.io reads the segments itself, so they have to be written its way."""

    def test_the_middle_dot_reaches_the_url_as_ascii(self):
        """The separator between the counts is not ASCII in the message."""
        badge = build_pr_badge(BadgeCounts(errors=2, warnings=2))

        assert "%C2%B7" in badge
        assert "·" not in badge

    def test_a_space_becomes_an_underscore_and_a_dash_is_doubled(self):
        """The README message carries both, and neither is a separator."""
        badge = build_readme_badge()

        assert "quality--checked" in badge

    def test_the_whole_url_is_ascii(self):
        badge = build_pr_badge(BadgeCounts(errors=1, warnings=1))

        assert badge.isascii()


class TestTheStyle:
    """`--style` reaches the URL, and an unknown one falls back."""

    def test_each_valid_style_is_accepted(self):
        for style in VALID_STYLES:
            assert normalize_style(style) == style

    def test_the_default_style_is_flat(self):
        assert DEFAULT_STYLE == "flat"

    def test_the_readme_badge_carries_the_style(self):
        assert "?style=for-the-badge" in build_readme_badge("for-the-badge")

    def test_an_unknown_style_falls_back_to_the_default(self):
        assert normalize_style("neon") == DEFAULT_STYLE
        assert f"?style={DEFAULT_STYLE}" in build_readme_badge("neon")

    def test_the_pr_badge_does_not_carry_a_style(self):
        """It is always the default one — nothing on the PR path configures it."""
        badge = build_pr_badge(BadgeCounts(errors=0, warnings=1))

        assert "?style=" not in badge


class TestNoCounts:
    """Nothing measured means nothing to say."""

    def test_no_counts_produces_no_badge(self):
        assert build_pr_badge(None) == ""
