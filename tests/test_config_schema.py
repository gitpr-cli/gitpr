"""Synchronisation tests between the configuration schema and DEFAULT_CONFIG.

The schema in src/config_schema.py is the UI's source of truth while
src/config.py keeps DEFAULT_CONFIG as the seeding source. The two lists are
hand-maintained, so these tests are what stop them from drifting: a new key
added to DEFAULT_CONFIG fails here until someone classifies it as either an
editable field or a deliberate omission.
"""
import unittest

from src.config import DEFAULT_CONFIG, SKILL_FILES_BY_TYPE, SKILL_TYPES
from src.config_schema import (
    ACTION_DOWNLOAD,
    ACTION_DOWNLOAD_WORDS,
    ACTIONS,
    CATEGORIES,
    CATEGORIES_BY_ID,
    CATEGORY_ORDER,
    FIELDS,
    FIELDS_BY_KEY,
    GROUPS_BY_ID,
    KINDS,
    SKILL_LABELS,
    TEMPLATE_PLACEHOLDERS,
    TEMPLATE_REQUIRED,
    VALIDATOR_AI_KEY,
    VALIDATOR_SCM_TOKEN,
    VERSION_SOURCES,
    VISIBILITY_CONTROLLERS,
    category_has_fields,
    fields_of,
)

# Keys that exist in ~/.gitpr/.env but are deliberately NOT editable from the
# TUI, mapped to the reason. Every entry needs a reason — this is not a dumping
# ground. Empty by design: with GITPR_SCM_TOKEN promoted to a read-only field,
# every key the file can hold now has a row on the screen. A new entry here is
# a decision to hide something, and it must be argued for in the comment.
DELIBERATELY_HIDDEN = {}


class TestSchemaCoversDefaults(unittest.TestCase):
    def test_every_default_key_is_classified(self):
        """No DEFAULT_CONFIG key may be silently absent from the schema."""
        unclassified = sorted(
            key
            for key in DEFAULT_CONFIG
            if key not in FIELDS_BY_KEY and key not in DELIBERATELY_HIDDEN
        )
        self.assertEqual(
            unclassified,
            [],
            f"DEFAULT_CONFIG key(s) neither in the schema nor in "
            f"DELIBERATELY_HIDDEN: {unclassified}",
        )

    def test_schema_defaults_match_default_config(self):
        """Where both define a key, the default must be the same string."""
        mismatched = {
            key: (DEFAULT_CONFIG[key], FIELDS_BY_KEY[key].default)
            for key in DEFAULT_CONFIG
            if key in FIELDS_BY_KEY and DEFAULT_CONFIG[key] != FIELDS_BY_KEY[key].default
        }
        self.assertEqual(
            mismatched,
            {},
            f"schema default differs from DEFAULT_CONFIG (key: (config, schema)): "
            f"{mismatched}",
        )

    def test_hidden_keys_are_really_absent_from_the_schema(self):
        for key in DELIBERATELY_HIDDEN:
            self.assertNotIn(key, FIELDS_BY_KEY, f"{key} must stay out of the TUI")


class TestFieldIntegrity(unittest.TestCase):
    def test_no_duplicate_keys(self):
        keys = [field.key for field in FIELDS]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        self.assertEqual(duplicates, [], f"duplicated field keys: {duplicates}")

    def test_every_category_resolves(self):
        unknown = sorted(
            {field.category for field in FIELDS} - set(CATEGORIES_BY_ID)
        )
        self.assertEqual(unknown, [], f"field(s) point to unknown category: {unknown}")

    def test_every_kind_is_known(self):
        unknown = sorted({field.kind for field in FIELDS} - set(KINDS))
        self.assertEqual(unknown, [], f"unknown kind(s): {unknown}")

    def test_every_category_has_at_least_one_field(self):
        """An empty category would render as a dead sidebar entry."""
        empty = [
            category.id
            for category in CATEGORIES
            if not category_has_fields(category.id, include_advanced=True)
        ]
        self.assertEqual(empty, [], f"category(ies) with no field: {empty}")

    def test_advanced_fields_live_in_the_advanced_category(self):
        """The advanced toggle hides fields; it must not split a category."""
        stray = sorted(
            field.key
            for field in FIELDS
            if field.advanced and field.category != "advanced"
        )
        self.assertEqual(stray, [], f"advanced field(s) outside 'advanced': {stray}")

    def test_labels_and_descriptions_are_not_empty(self):
        empty = sorted(
            field.key for field in FIELDS if not field.label or not field.description
        )
        self.assertEqual(empty, [], f"field(s) missing label or description: {empty}")


class TestFieldValidationRules(unittest.TestCase):
    def test_enum_fields_declare_choices_and_default_is_valid(self):
        for field in FIELDS:
            if field.kind != "enum":
                continue
            self.assertTrue(field.choices, f"{field.key}: enum without choices")
            self.assertIn(
                field.default,
                field.choices,
                f"{field.key}: default {field.default!r} not among {field.choices}",
            )

    def test_choices_only_on_enum_fields(self):
        stray = sorted(
            field.key for field in FIELDS if field.choices and field.kind != "enum"
        )
        self.assertEqual(stray, [], f"choices declared on non-enum field(s): {stray}")

    def test_secret_fields_declare_a_validator(self):
        """A validator proves the value about to be WRITTEN. A read-only secret
        is never written — the screen only ever displays it — so it is exempt."""
        validators = {VALIDATOR_AI_KEY, VALIDATOR_SCM_TOKEN}
        for field in FIELDS:
            if field.kind != "secret" or field.read_only:
                continue
            self.assertIn(
                field.validator,
                validators,
                f"{field.key}: writable secret without a validator",
            )

    def test_template_defaults_are_usable(self):
        """resolve_output_path() does .format(branch=, datetime=) — a default
        with an unknown placeholder would crash every command on first run."""
        import string

        for field in FIELDS:
            if field.kind != "template":
                continue
            used = {
                name
                for _, name, _, _ in string.Formatter().parse(field.default)
                if name
            }
            self.assertFalse(
                used - set(TEMPLATE_PLACEHOLDERS),
                f"{field.key}: default uses unknown placeholder(s) "
                f"{sorted(used - set(TEMPLATE_PLACEHOLDERS))}",
            )
            for required in TEMPLATE_REQUIRED:
                self.assertIn(
                    required,
                    used,
                    f"{field.key}: default must keep {{{required}}}",
                )


class TestGrouping(unittest.TestCase):
    """The themed sub-headers of the right pane. A group is rendered as one
    Static mounted right before its first field, so the schema has to guarantee
    that a group is used in one place only and never reopens further down."""

    def test_every_group_resolves(self):
        unknown = sorted(
            {field.group for field in FIELDS if field.group} - set(GROUPS_BY_ID)
        )
        self.assertEqual(unknown, [], f"field(s) in unknown group: {unknown}")

    def test_a_group_belongs_to_one_category_only(self):
        """The header widget id is derived from the group id, so a group used
        in two categories would render both headers from one Static."""
        owners = {}
        for field in FIELDS:
            if field.group:
                owners.setdefault(field.group, set()).add(field.category)
        shared = {group: sorted(cats) for group, cats in owners.items() if len(cats) > 1}
        self.assertEqual(shared, {}, f"group(s) spanning categories: {shared}")

    def test_group_fields_are_contiguous(self):
        """A group that reopens after another one would need a second header,
        and _mount_rows mounts exactly one per group."""
        seen = {}
        for field in FIELDS:
            if not field.group:
                continue
            previous = seen.get(field.category)
            if previous is not None and previous != field.group:
                self.assertNotIn(
                    field.group,
                    seen,
                    f"{field.category}: group {field.group!r} reopens after "
                    f"{previous!r} — order the fields so it stays contiguous",
                )
            seen[field.category] = field.group

    def test_advanced_grouped_fields_are_ordered_inside_their_group(self):
        """Regression for the 'Spinner Words Version right below Spinner Words'
        request: the version marker must not drift away from the list it
        describes."""
        keys = [field.key for field in FIELDS if field.category == "advanced"]
        self.assertLess(
            keys.index("SPINNER_THINKING_WORDS"),
            keys.index("THINKING_WORDS_VERSION"),
            "Spinner Words Version must come after Spinner Words",
        )


class TestVisibilityGating(unittest.TestCase):
    """show_if drives the provider/forge filter of the right pane. Every rule
    below exists to turn a silent no-op (a typo'd value never matches, so the
    field is simply never shown) into a failing test."""

    def test_controllers_resolve_to_enum_fields(self):
        for field in FIELDS:
            for key, _allowed in field.show_if:
                self.assertIn(key, FIELDS_BY_KEY, f"{field.key}: unknown controller {key}")
                controller = FIELDS_BY_KEY[key]
                self.assertEqual(
                    controller.kind,
                    "enum",
                    f"{field.key}: controller {key} is {controller.kind}, not enum",
                )

    def test_allowed_values_exist_in_the_controller_choices(self):
        for field in FIELDS:
            for key, allowed in field.show_if:
                choices = FIELDS_BY_KEY[key].choices
                stray = sorted(set(allowed) - set(choices))
                self.assertEqual(
                    stray,
                    [],
                    f"{field.key}: show_if accepts {stray}, absent from "
                    f"{key}.choices {choices}",
                )

    def test_a_field_is_never_gated_on_itself(self):
        for field in FIELDS:
            self.assertNotIn(
                field.key,
                [key for key, _ in field.show_if],
                f"{field.key} gates itself — it could never be shown",
            )

    def test_visibility_controllers_match_the_schema(self):
        """The screen re-filters only when a controller changes, so the derived
        set is what keeps a new gate from being inert until the next save."""
        declared = {
            key for field in FIELDS for key, _allowed in field.show_if
        }
        self.assertEqual(VISIBILITY_CONTROLLERS, frozenset(declared))

    def test_the_default_state_never_hides_every_gated_field(self):
        """On a fresh install a controller sits at its declared default. If no
        gated field accepted that value, the whole sub-section would be missing
        from the screen with nothing left to explain why.

        Note that "" does NOT have to appear in every gate: the empty SCM
        provider means GitHub, so the Bitbucket group is correctly invisible
        until the user picks Bitbucket — only the GitHub group has to answer
        for the default."""
        by_controller = {}
        for field in FIELDS:
            for key, allowed in field.show_if:
                by_controller.setdefault(key, []).append((field.key, allowed))
        for key, gates in by_controller.items():
            default = FIELDS_BY_KEY[key].default
            self.assertTrue(
                any(default in allowed for _field, allowed in gates),
                f"{key} defaults to {default!r}, which hides every field it "
                f"gates: {sorted(f for f, _a in gates)}",
            )

    def test_the_empty_scm_provider_is_github(self):
        """The gate that carries the rule above: "" and "github" are the same
        forge, which is why the legacy GitHub token is reachable without ever
        running --init."""
        github = [
            field
            for field in FIELDS
            if field.group == "github" and field.show_if
        ]
        self.assertTrue(github, "no field is gated on the GitHub group")
        for field in github:
            self.assertIn(
                "",
                field.show_if[0][1],
                f"{field.key}: '' does not reach the GitHub group",
            )


class TestVersionMarkers(unittest.TestCase):
    """KIND_VERSION fields show the marker stored in the file, falling back to
    a constant of the code when the marker is absent (the empty box reported on
    Linter Presets Version)."""

    def test_version_fields_declare_a_known_source(self):
        for field in FIELDS:
            if field.kind != "version":
                continue
            self.assertIn(
                field.version_source,
                VERSION_SOURCES,
                f"{field.key}: version field without a known source",
            )

    def test_version_source_only_on_version_fields(self):
        stray = sorted(
            field.key
            for field in FIELDS
            if field.version_source and field.kind != "version"
        )
        self.assertEqual(stray, [], f"version_source on non-version field(s): {stray}")

    def test_version_fields_are_read_only(self):
        """They are stamps written by the loaders, never typed by hand."""
        writable = sorted(
            field.key
            for field in FIELDS
            if field.kind == "version" and not field.read_only
        )
        self.assertEqual(writable, [], f"writable version field(s): {writable}")


class TestActionButtons(unittest.TestCase):
    def test_every_action_is_known(self):
        unknown = sorted({field.action for field in FIELDS if field.action} - set(ACTIONS))
        self.assertEqual(unknown, [], f"unknown action(s): {unknown}")

    def test_actions_match_their_kind(self):
        expected = {
            ACTION_DOWNLOAD: "version",
            ACTION_DOWNLOAD_WORDS: "words",
        }
        for field in FIELDS:
            if not field.action:
                continue
            self.assertEqual(
                field.kind,
                expected[field.action],
                f"{field.key}: action {field.action!r} on a {field.kind} field",
            )

    def test_action_fields_are_read_only(self):
        """The button writes the value; the control exists to display it."""
        writable = sorted(
            field.key for field in FIELDS if field.action and not field.read_only
        )
        self.assertEqual(writable, [], f"action field(s) not read-only: {writable}")

    def test_the_word_list_is_a_read_only_words_field_with_a_download(self):
        words = [field for field in FIELDS if field.kind == "words"]
        self.assertTrue(words, "no words field in the schema")
        for field in words:
            self.assertTrue(field.read_only, f"{field.key}: words field is writable")
            self.assertEqual(
                field.action,
                ACTION_DOWNLOAD_WORDS,
                f"{field.key}: words field without its download action",
            )


class TestDocumentationLinks(unittest.TestCase):
    def test_every_category_links_to_a_markdown_page(self):
        for category in CATEGORIES:
            self.assertTrue(category.doc, f"{category.id}: category without a doc")
            self.assertTrue(
                category.doc.endswith(".md"),
                f"{category.id}: doc {category.doc!r} is not a Markdown file",
            )

    def test_doc_links_are_unique(self):
        """Two sections pointing at one page is allowed (the filters list is
        documented with the diff filters), but a copy-paste slip is not: every
        doc must at least exist in docs/."""
        import os

        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
        missing = sorted(
            {category.doc for category in CATEGORIES}
            - {
                name
                for name in os.listdir(docs_dir)
                if name.endswith(".md")
            }
        )
        self.assertEqual(missing, [], f"doc page(s) not found in docs/: {missing}")


class TestCategoryHelpers(unittest.TestCase):
    def test_category_order_matches_categories(self):
        self.assertEqual(CATEGORY_ORDER, tuple(c.id for c in CATEGORIES))

    def test_general_is_first(self):
        """The screen must land on a populated category."""
        self.assertEqual(CATEGORY_ORDER[0], "general")

    def test_advanced_toggle_filters_fields(self):
        hidden = fields_of("advanced", include_advanced=False)
        shown = fields_of("advanced", include_advanced=True)
        self.assertEqual(hidden, ())
        self.assertTrue(shown)

    def test_non_advanced_categories_are_unaffected_by_the_toggle(self):
        self.assertEqual(fields_of("pr", False), fields_of("pr", True))

    def test_advanced_is_last(self):
        """The advanced entry is pinned to the bottom of the sidebar, and only
        the indices of 'general' (0), 'ai' (1) and 'pr' (2) are relied on by
        test_config_app.py — so a new section is free to land anywhere above."""
        self.assertEqual(CATEGORY_ORDER[-1], "advanced")


class TestSkillsSection(unittest.TestCase):
    """The Skills section lists the registry, not the folder it reads."""

    def test_the_labels_cover_the_registry_exactly(self):
        """A missing label renders blank in the sidebar; an extra one is a type
        the screen can never reach."""
        self.assertEqual(set(SKILL_LABELS), set(SKILL_FILES_BY_TYPE))
        self.assertEqual(set(SKILL_LABELS), set(SKILL_TYPES))

    def test_the_labels_follow_the_registry_order(self):
        self.assertEqual(tuple(SKILL_LABELS), SKILL_TYPES)

    def test_every_label_is_translated_text(self):
        for skill_type, label in SKILL_LABELS.items():
            self.assertTrue(label, f"{skill_type}: empty label")

    def test_the_section_has_a_read_only_folder_field(self):
        """The skills are files, not .env keys, so the section holds a single
        sentinel row: the folder they are read from."""
        fields = fields_of("skills", include_advanced=True)
        self.assertEqual([field.key for field in fields], ["SKILLS_FOLDER"])
        self.assertTrue(fields[0].read_only)

    def test_the_folder_field_is_not_a_config_default(self):
        """It is resolved from the working directory at render time; a default
        in DEFAULT_CONFIG would freeze it to the first folder it saw."""
        self.assertNotIn("SKILLS_FOLDER", DEFAULT_CONFIG)


if __name__ == "__main__":
    unittest.main()
