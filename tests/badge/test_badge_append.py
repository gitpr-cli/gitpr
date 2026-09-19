"""Placing the badge in a body, once."""

from src.branding.badge_builder import append_badge

BADGE = "[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](x)"

BODY = "## Summary\n\nAdds the ownership check."


class TestPlacement:
    def test_the_badge_lands_at_the_end(self):
        result = append_badge(BODY, BADGE)

        assert result.startswith(BODY)
        assert result.endswith(BADGE)

    def test_the_badge_is_separated_from_the_body(self):
        """A horizontal rule, so it reads as a footer and not as prose."""
        assert append_badge(BODY, BADGE) == f"{BODY}\n\n---\n\n{BADGE}"

    def test_trailing_whitespace_does_not_grow_a_gap(self):
        result = append_badge(BODY + "\n\n\n", BADGE)

        assert result == f"{BODY}\n\n---\n\n{BADGE}"

    def test_a_body_that_is_only_the_badge_stays_that_way(self):
        assert append_badge("", BADGE) == BADGE


class TestItDoesNotStack:
    """Republishing sends the body again, and must not add a second badge."""

    def test_appending_twice_changes_nothing_the_second_time(self):
        once = append_badge(BODY, BADGE)

        assert append_badge(once, BADGE) == once

    def test_a_badge_the_user_moved_is_left_where_it_is(self):
        """It is editable, so it can be anywhere — that is not a reason to add one."""
        moved = f"{BADGE}\n\n{BODY}"

        assert append_badge(moved, BADGE) == moved

    def test_a_different_badge_does_not_count_as_ours(self):
        somebody_else = "[![Build](https://img.shields.io/badge/build-passing-green)](x)"

        assert append_badge(BODY, somebody_else) == f"{BODY}\n\n---\n\n{somebody_else}"


class TestNothingToAdd:
    def test_an_empty_badge_leaves_the_body_untouched(self):
        assert append_badge(BODY, "") == BODY

    def test_an_empty_badge_does_not_add_a_rule(self):
        assert "---" not in append_badge(BODY, "")
