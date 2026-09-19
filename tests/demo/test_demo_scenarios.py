"""Scenario registry: names, language resolution and fixture integrity.

The diffs are displayed by the tour and never parsed, so nothing in the product
would fail if a hunk header drifted away from its body. The arithmetic check at
the bottom of this file is the only thing standing between a plausible-looking
example and one a reader who knows diffs will spot as wrong.
"""

import re

import pytest

from src.demo.scenarios import (
    DEFAULT_SCENARIO,
    SCENARIO_NAMES,
    DemoScenario,
    DemoScenarioError,
    _resolve_lang,
    load_scenario,
)
from src.demo.scenarios import laravel_bug_fix, security_issue

SCENARIO_MODULES = (laravel_bug_fix, security_issue)
REQUIRED_FIELDS = (
    "title",
    "description",
    "commit_message",
    "review",
    "linter",
    "pr_description",
)
HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _hunk_totals(diff):
    """Pair each hunk header's claim with the line counts its body carries.

    An empty line inside a hunk counts as context: the scenario fixtures cannot
    keep the single-space context marker in source (no editor in the toolchain
    preserves trailing whitespace), so that is the convention they are written
    to. See the registry module docstring.
    """
    lines = diff.rstrip("\n").split("\n")
    hunks = []
    index = 0

    while index < len(lines):
        match = HUNK_HEADER.match(lines[index])
        if match is None:
            index += 1
            continue

        claimed = (
            int(match.group(2)) if match.group(2) is not None else 1,
            int(match.group(4)) if match.group(4) is not None else 1,
        )
        index += 1
        old = new = 0

        while index < len(lines) and not lines[index].startswith(("@@ ", "diff --git ")):
            line = lines[index]
            if line.startswith("+"):
                new += 1
            elif line.startswith("-"):
                old += 1
            else:
                old += 1
                new += 1
            index += 1

        hunks.append((claimed, (old, new)))

    return hunks


class TestRegistry:
    """The registry's public surface, which the CLI depends on."""

    def test_names_are_stable(self):
        """--scenario values are a user-facing contract; reordering breaks it."""
        assert SCENARIO_NAMES == ("laravel-bug-fix", "security-issue")

    def test_default_is_the_first_registered(self):
        assert DEFAULT_SCENARIO == SCENARIO_NAMES[0]

    def test_every_registered_name_loads(self):
        for name in SCENARIO_NAMES:
            assert load_scenario(name).name == name

    def test_module_name_matches_its_registry_key(self):
        for module in SCENARIO_MODULES:
            assert module.NAME in SCENARIO_NAMES


class TestLoadScenario:
    """Name and language resolution."""

    def test_omitted_name_returns_the_default(self):
        assert load_scenario().name == DEFAULT_SCENARIO

    def test_explicit_name_is_honoured(self):
        assert load_scenario("security-issue").name == "security-issue"

    def test_name_is_case_insensitive(self):
        assert load_scenario("Laravel-Bug-Fix").name == "laravel-bug-fix"

    def test_returns_the_documented_contract(self):
        scenario = load_scenario("laravel-bug-fix", "en")
        assert isinstance(scenario, DemoScenario)

    def test_explicit_language_selects_its_prose(self):
        scenario = load_scenario("laravel-bug-fix", "pt_br")
        assert scenario.lang == "pt_br"
        assert scenario.title == laravel_bug_fix.TEXT["pt_br"]["title"]

    @pytest.mark.parametrize(
        "alias, expected",
        [
            ("en", "en"),
            ("en_us", "en"),
            ("en_gb", "en"),
            ("pt", "pt_br"),
            ("pt_br", "pt_br"),
            ("pt-BR", "pt_br"),
            ("pt_pt", "pt_pt"),
            ("es", "es_es"),
            ("es_es", "es_es"),
            ("fr", "fr_fr"),
            ("fr_fr", "fr_fr"),
            ("de", "en"),
        ],
    )
    def test_language_codes_map_onto_scenario_text_keys(self, alias, expected):
        """The whole table, including the codes with no translation yet.

        Asserted against the mapping itself: a scenario's ``lang`` reports the
        language actually used, so a code whose translation has not been
        written yet reports ``en`` and would hide a broken mapping.
        """
        assert _resolve_lang(alias) == expected

    def test_an_alias_reaches_the_same_prose_as_its_canonical_code(self):
        aliased = load_scenario("laravel-bug-fix", "pt")
        canonical = load_scenario("laravel-bug-fix", "pt_br")

        assert aliased.lang == canonical.lang == "pt_br"
        assert aliased.title == canonical.title

    def test_missing_translation_falls_back_to_english(self):
        """A scenario stays usable while its translation is still being written."""
        scenario = load_scenario("laravel-bug-fix", "de")
        assert scenario.lang == "en"
        assert scenario.title == laravel_bug_fix.TEXT["en"]["title"]

    def test_omitted_language_follows_the_interface(self, monkeypatch):
        """--lang calls i18n.set_lang() first, so the tour follows it."""
        monkeypatch.setattr("src.i18n.CURRENT_LANG", "pt_br")
        assert load_scenario("laravel-bug-fix").lang == "pt_br"

    def test_diff_is_identical_in_every_language(self):
        """The diff is repository code: translated prose must not touch it."""
        english = load_scenario("laravel-bug-fix", "en").diff
        assert load_scenario("laravel-bug-fix", "pt_br").diff == english

    def test_other_scenarios_never_contains_itself(self):
        scenario = load_scenario("laravel-bug-fix")
        assert scenario.name not in scenario.other_scenarios
        assert set(scenario.other_scenarios) == set(SCENARIO_NAMES) - {scenario.name}

    def test_unknown_scenario_raises_a_scenario_error(self):
        with pytest.raises(DemoScenarioError):
            load_scenario("nao-existe")

    def test_unknown_scenario_message_lists_the_available_ones(self):
        """The spec asks for a clear listing, not a generic exception."""
        with pytest.raises(DemoScenarioError) as raised:
            load_scenario("nao-existe")

        message = str(raised.value)
        assert "nao-existe" in message
        for name in SCENARIO_NAMES:
            assert name in message


class TestScenarioContent:
    """Every scenario must be complete in every language it claims to carry."""

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_english_is_always_present(self, module):
        assert "en" in module.TEXT

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_no_language_field_is_empty(self, module):
        for lang, text in module.TEXT.items():
            assert set(text) == set(REQUIRED_FIELDS), lang

            for field in ("title", "description", "commit_message", "review", "pr_description"):
                assert isinstance(text[field], str), f"{lang}.{field}"
                assert text[field].strip(), f"{lang}.{field}"

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_linter_block_has_the_shape_render_expects(self, module):
        """compose_review_content() concatenates errors + warnings."""
        for lang, text in module.TEXT.items():
            linter = text["linter"]

            assert set(linter) == {"errors", "warnings"}, lang

            for severity in ("errors", "warnings"):
                assert isinstance(linter[severity], list), f"{lang}.{severity}"
                for alert in linter[severity]:
                    assert isinstance(alert, str), f"{lang}.{severity}"
                    assert alert.strip(), f"{lang}.{severity}"

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_translations_are_not_copies_of_english(self, module):
        """Guards against a language block pasted from the English one."""
        english = module.TEXT["en"]

        for lang, text in module.TEXT.items():
            if lang == "en":
                continue

            for field in ("title", "description", "commit_message", "review", "pr_description"):
                assert text[field] != english[field], f"{lang}.{field}"

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_loaded_scenario_carries_every_field(self, module):
        scenario = load_scenario(module.NAME)

        for field in REQUIRED_FIELDS:
            assert getattr(scenario, field), field
        assert scenario.diff.strip()


class TestDiffIntegrity:
    """The diff is the centrepiece of the tour; it has to look like a real one."""

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_ends_with_a_newline(self, module):
        assert module.DIFF.endswith("\n")

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_starts_with_a_git_header(self, module):
        assert module.DIFF.startswith("diff --git ")

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_every_file_section_has_both_markers(self, module):
        """A hunk without ---/+++ is not a diff, it is a note."""
        files = [block for block in module.DIFF.split("diff --git ") if block.strip()]

        assert files
        for block in files:
            assert any(line.startswith("--- ") for line in block.splitlines())
            assert any(line.startswith("+++ ") for line in block.splitlines())
            assert any(line.startswith("@@ ") for line in block.splitlines())

    @pytest.mark.parametrize("module", SCENARIO_MODULES, ids=lambda m: m.NAME)
    def test_hunk_headers_match_their_bodies(self, module):
        """Catches a header that drifted from the body it claims to describe."""
        hunks = _hunk_totals(module.DIFF)

        assert hunks, "no hunk found in the diff"

        for number, (claimed, counted) in enumerate(hunks, start=1):
            assert claimed == counted, f"hunk {number}: header {claimed} vs body {counted}"

    def test_both_scenarios_are_about_different_languages(self):
        """Two scenarios that look alike make --scenario pointless."""
        assert security_issue.DIFF != laravel_bug_fix.DIFF
        assert security_issue.TEXT["en"]["review"] != laravel_bug_fix.TEXT["en"]["review"]
