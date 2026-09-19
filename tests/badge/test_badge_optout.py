"""The opt-out, in both directions.

The badge is on by default and ``GITPR_BADGE=false`` is how a user says no. Both
halves are asserted here: an opt-out that quietly does nothing is worse than no
opt-out at all, and a badge that only appears after setting a variable is a
feature nobody ever sees.

The gate is exercised where the product exercises it — ``attach_pr_badge`` reads
the flag through ``badge_enabled()``, the same call the CLI makes before either
publisher runs. ``~/.gitpr/.env`` is redirected so a developer who set the
variable in their own profile gets the same result as CI.
"""

import pytest

from src.branding.badge_builder import BRAND_URL, attach_pr_badge

RULES = """
rules:
  - name: "check-js-console"
    level: "error"
    extensions: ["js"]
    regex: 'console\\.(log|debug)\\s*\\('
    message: "console.log in {file_name} (Line {line_number})."
    ignore_comments: true
"""

DIFF = (
    "diff --git a/app.js b/app.js\n"
    "index 1111111..2222222 100644\n"
    "--- a/app.js\n"
    "+++ b/app.js\n"
    "@@ -1,2 +1,3 @@\n"
    " const keep = 1;\n"
    "+console.log('debug');\n"
)

BODY = "## Summary\n\nAdds the ownership check."

# Every spelling `badge_enabled()` accepts, plus the spacing and case a hand
# edited `.env` file tends to carry.
OFF_VALUES = ("false", "FALSE", " false ", "0", "no", "NO", "off", "n")

# Anything else is on: the variable is an opt-*out*, so unknown text cannot
# turn the badge off by accident.
ON_VALUES = ("true", "1", "yes", "on", "whatever")


@pytest.fixture(autouse=True)
def private_profile(tmp_path, monkeypatch):
    """Keep the developer's own ``~/.gitpr/.env`` out of these results."""
    monkeypatch.setattr("src.config.ENV_FILE", str(tmp_path / "profile.env"))
    monkeypatch.delenv("GITPR_BADGE", raising=False)


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A checkout with linter rules, so there is a badge to withhold."""
    skill_dir = tmp_path / ".gitpr" / "skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / ".gitpr.linter.yml").write_text(RULES, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    # Rules also load from the developer's ~/.gitpr/plugins — pinned empty so
    # this fixture describes the counts and nothing else.
    monkeypatch.setattr("src.config.get_linter_plugins", lambda: [])


@pytest.fixture
def pr_data():
    return {"commit_message": "feat: add thing", "pr_description": BODY}


class TestSwitchedOff:
    @pytest.mark.parametrize("value", OFF_VALUES)
    def test_the_body_is_left_exactly_as_it_was(self, project, pr_data, monkeypatch, value):
        monkeypatch.setenv("GITPR_BADGE", value)

        attach_pr_badge(pr_data, DIFF)

        assert pr_data["pr_description"] == BODY


class TestSwitchedOnByDefault:
    """The other half: without the variable, the badge is there."""

    @pytest.mark.parametrize("value", ON_VALUES)
    def test_any_other_value_keeps_the_badge(self, project, pr_data, monkeypatch, value):
        monkeypatch.setenv("GITPR_BADGE", value)

        attach_pr_badge(pr_data, DIFF)

        assert "img.shields.io" in pr_data["pr_description"]

    def test_an_absent_variable_keeps_the_badge(self, project, pr_data):
        attach_pr_badge(pr_data, DIFF)

        assert BRAND_URL in pr_data["pr_description"]

    def test_the_body_is_still_the_body(self, project, pr_data):
        """The badge is a footer — opting out is not the only way to keep one off."""
        attach_pr_badge(pr_data, DIFF)

        assert pr_data["pr_description"].startswith(BODY)

    def test_nothing_else_in_the_payload_is_touched(self, project, pr_data):
        attach_pr_badge(pr_data, DIFF)

        assert pr_data["commit_message"] == "feat: add thing"


class TestTheOtherReasonABodyStaysClean:
    """A body without a badge is not always an opt-out.

    Without rules the linter reports nothing without checking anything, and the
    badge is withheld for that reason instead. Tested next to the opt-out so a
    green run above cannot be explained by the badge being broken.
    """

    def test_no_rules_means_no_badge_even_with_the_flag_on(
        self, tmp_path, pr_data, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("src.config.get_linter_plugins", lambda: [])

        attach_pr_badge(pr_data, DIFF)

        assert pr_data["pr_description"] == BODY
