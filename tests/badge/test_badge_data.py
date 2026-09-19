"""Where the numbers come from, and when there are none to show.

The distinction this file protects is the whole point of the feature: a diff
the rules found clean and a diff no rule ever looked at both come back from the
linter as empty lists, and only one of them may reach a public pull request.
"""

import pytest

from src.branding.badge_data import BadgeCounts, collect_linter_counts

RULES = """
rules:
  - name: "check-js-console"
    level: "error"
    extensions: ["js"]
    regex: 'console\\.(log|debug)\\s*\\('
    message: "console.log in {file_name} (Line {line_number})."
    ignore_comments: true

  - name: "check-deferred-value"
    level: "warning"
    extensions: ["js"]
    regex: '\\blater\\b'
    message: "Deferred value in {file_name} (Line {line_number})."
    ignore_comments: true
"""

DIFF = (
    "diff --git a/app.js b/app.js\n"
    "index 1111111..2222222 100644\n"
    "--- a/app.js\n"
    "+++ b/app.js\n"
    "@@ -1,2 +1,4 @@\n"
    " const keep = 1;\n"
    "+console.log('debug');\n"
    "+const later = 2;\n"
)

CLEAN_DIFF = (
    "diff --git a/app.js b/app.js\n"
    "index 1111111..2222222 100644\n"
    "--- a/app.js\n"
    "+++ b/app.js\n"
    "@@ -1,2 +1,3 @@\n"
    " const keep = 1;\n"
    "+const other = 2;\n"
)


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A checkout that has linter rules and a diff that breaks two of them."""
    skill_dir = tmp_path / ".gitpr" / "skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / ".gitpr.linter.yml").write_text(RULES, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    # Rules also load from the developer's ~/.gitpr/plugins — pinned empty so
    # the counts below describe this fixture and nothing else.
    monkeypatch.setattr("src.config.get_linter_plugins", lambda: [])

    return tmp_path


class TestRealCounts:
    def test_it_counts_what_the_rules_found(self, project):
        assert collect_linter_counts(DIFF) == BadgeCounts(errors=1, warnings=1)

    def test_a_clean_diff_is_a_measurement_and_not_an_absence(self, project):
        """Rules ran and found nothing — that is a ``no issues`` badge."""
        assert collect_linter_counts(CLEAN_DIFF) == BadgeCounts(errors=0, warnings=0)

    def test_the_external_bridge_is_skipped(self, project, monkeypatch):
        """It runs binaries against files on disk, which is not this revision."""
        seen = {}

        def recorder(diff_text, **kwargs):
            seen.update(kwargs)
            return {"errors": [], "warnings": []}

        monkeypatch.setattr("src.branding.badge_data.parse_diff_and_lint", recorder)

        collect_linter_counts(DIFF)

        assert seen.get("skip_external") is True


class TestNoRules:
    """No rules configured: the linter would report empty without checking."""

    def test_no_rules_means_no_counts(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("src.config.get_linter_plugins", lambda: [])

        assert collect_linter_counts(DIFF) is None

    def test_a_diff_the_rules_ignore_still_counts_when_rules_exist(self, project):
        """The opposite case, so the test above is not passing for free."""
        assert collect_linter_counts(CLEAN_DIFF) is not None


class TestTheBadgeNeverBlocksAPublish:
    """Every failure path ends in ``None``, never in an exception."""

    def test_a_linter_that_raises_produces_no_counts(self, project, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("linter exploded")

        monkeypatch.setattr("src.branding.badge_data.parse_diff_and_lint", explode)

        assert collect_linter_counts(DIFF) is None

    def test_rules_that_cannot_be_read_produce_no_counts(self, project, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("rules exploded")

        monkeypatch.setattr("src.branding.badge_data.load_linter_rules", explode)

        assert collect_linter_counts(DIFF) is None
