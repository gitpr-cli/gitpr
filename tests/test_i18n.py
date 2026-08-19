"""Regression tests for the i18n translation files.

Guards against the key-mangling bug introduced by the old sync regex (keys
capturing call-site fragments like fg="red" or count=len(...)) and enforces
parity across the six language files. Pure JSON tests — no network, no
~/.gitpr reads; src.i18n is imported lazily inside the smoke test only
(its module init reads the user .env and may attempt a download).
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

from tests.sync_i18n import PATTERN, _extract_keys

REPO = Path(__file__).resolve().parent.parent
LANGS_DIR = REPO / "langs"
LANG_FILES = ["pt_br.json", "pt_pt.json", "es_es.json", "es.json", "fr_fr.json", "fr.json"]

# Fragments the old regex captured into keys (call-site kwarg spillover).
MANGLED_RE = re.compile(r'",\s*\w+=|\),\s*(?:fg|severity|classes)\s*=|,\s*\w+=len\(')


def _load_repair_script():
    """Imports scripts/fix_mangled_i18n_keys.py (scripts/ is not a package)
    so the clean-key list and constants stay single-sourced."""
    spec = importlib.util.spec_from_file_location(
        "fix_mangled_i18n_keys", REPO / "scripts" / "fix_mangled_i18n_keys.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPAIR = _load_repair_script()
CLEAN_KEYS = set(REPAIR.PT_BR)


def _load_langs():
    return {name: json.loads((LANGS_DIR / name).read_text(encoding="utf-8"))
            for name in LANG_FILES}


class TestLangFileIntegrity(unittest.TestCase):
    """Checks on the six committed JSON files."""

    @classmethod
    def setUpClass(cls):
        cls.langs = _load_langs()

    def test_json_valid_and_str_values(self):
        for name in LANG_FILES:
            data = self.langs[name]
            self.assertIsInstance(data, dict)
            for key, value in data.items():
                self.assertIsInstance(value, str, f"{name}: non-str value for {key!r}")

    def test_no_mangled_keys(self):
        for name in LANG_FILES:
            hits = [k for k in self.langs[name] if MANGLED_RE.search(k)]
            self.assertEqual(hits, [], f"{name}: mangled keys remain")

    def test_key_parity_and_count(self):
        reference = set(self.langs["pt_br.json"])
        self.assertEqual(len(reference), 547)
        for name in LANG_FILES:
            self.assertEqual(set(self.langs[name]), reference, f"{name}: key set differs")

    def test_clean_keys_present_and_translated(self):
        self.assertEqual(len(CLEAN_KEYS), 50)
        for name in LANG_FILES:
            data = self.langs[name]
            self.assertTrue(CLEAN_KEYS.issubset(data), f"{name}: clean keys missing")
            untranslated = [k for k in CLEAN_KEYS if data[k] == k]
            self.assertEqual(untranslated, [], f"{name}: untranslated clean keys")

    def test_truncated_key_absent_full_mcp_key_translated(self):
        for name in LANG_FILES:
            data = self.langs[name]
            self.assertNotIn(REPAIR.TRUNCATED_KEY, data, f"{name}: truncated key remains")
            self.assertIn(REPAIR.FULL_MCP_KEY, data, f"{name}: full MCP key missing")
            self.assertNotEqual(
                data[REPAIR.FULL_MCP_KEY], REPAIR.FULL_MCP_KEY, f"{name}: MCP key untranslated"
            )

    def test_stage_error_key_present_and_translated(self):
        for name in LANG_FILES:
            data = self.langs[name]
            self.assertIn(REPAIR.STAGE_ERROR_KEY, data, f"{name}: stage-error key missing")
            self.assertNotEqual(
                data[REPAIR.STAGE_ERROR_KEY], REPAIR.STAGE_ERROR_KEY,
                f"{name}: stage-error key untranslated",
            )

    def test_linter_modal_keys_present_and_translated(self):
        # Keys rendered by LinterErrorScreen (--no-verify commit flow).
        for name in LANG_FILES:
            data = self.langs[name]
            for key in ("Abort", "Commit with --no-verify"):
                self.assertIn(key, data, f"{name}: {key!r} missing")
                self.assertNotEqual(data[key], key, f"{name}: {key!r} untranslated")

    def test_orphan_keys_absent(self):
        for name in LANG_FILES:
            for orphan in REPAIR.ORPHAN_KEYS:
                self.assertNotIn(orphan, self.langs[name], f"{name}: orphan {orphan!r} remains")

    def test_identity_keys_with_braces_allowlist(self):
        # Deliberately-identical keys: the blame prompt must stay English for the
        # AI, and [OK]/[FAIL] are universal status markers from the MCP installer.
        status_markers = {"  [OK] {editor}: {message}", "  [FAIL] {editor}: {message}"}
        for name in LANG_FILES:
            identity = {k for k, v in self.langs[name].items() if k == v and "{" in k}
            markers = {k for k in identity if "[OK] {" in k or "[FAIL] {" in k}
            self.assertEqual(markers, status_markers, f"{name}: unexpected status markers")
            prompts = identity - markers
            self.assertEqual(
                len(prompts), 1, f"{name}: unexpected identity keys with braces"
            )
            self.assertTrue(prompts.pop().startswith("You are a Software Architect."))


class TestPatternExtraction(unittest.TestCase):
    """Unit tests for the extraction regex shared with tests/sync_i18n.py."""

    def _extract(self, text):
        keys = set()
        _extract_keys(text, keys)
        return keys

    def test_pre_mangled_sample_extracts_clean_literal(self):
        text = 'click.secho(__("📋 Auto-staging {count} file(s)...", count=len(unstaged)), fg="cyan")'
        self.assertEqual(self._extract(text), {"📋 Auto-staging {count} file(s)..."})

    def test_single_quotes_with_inner_double_quotes(self):
        text = "__('He said \"hi\"', x=1)"
        self.assertEqual(self._extract(text), {'He said "hi"'})

    def test_escaped_single_quote(self):
        text = '__("Don\\\'t stop", y=2)'
        self.assertEqual(self._extract(text), {"Don't stop"})

    def test_nested_call_extracts_both_keys(self):
        text = '__("   Current: {current} (from .env)", current=env_version or __("none"))'
        self.assertEqual(self._extract(text), {"   Current: {current} (from .env)", "none"})

    def test_adjacent_literals_yield_first_only(self):
        # Documented limitation: __("a" "b") captures only "a".
        text = '__("a" "b")'
        self.assertEqual(self._extract(text), {"a"})


class TestFormattingSmoke(unittest.TestCase):
    """End-to-end formatting through the real __() function (no network)."""

    def test_pt_br_formatting_with_kwargs(self):
        from src import i18n

        data = json.loads((LANGS_DIR / "pt_br.json").read_text(encoding="utf-8"))
        saved = (i18n.CURRENT_LANG, i18n.TRANSLATIONS)
        try:
            i18n.CURRENT_LANG = "pt_br"
            i18n.TRANSLATIONS = data
            result = i18n.__("📋 Auto-staging {count} file(s)...", count=3)
            self.assertIn("3", result)
            self.assertNotIn("Auto-staging", result)
        finally:
            i18n.CURRENT_LANG, i18n.TRANSLATIONS = saved
