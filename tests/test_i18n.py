"""Regression tests for the i18n translation files.

Guards against the key-mangling bug introduced by the old sync regex (keys
capturing call-site fragments like fg="red" or count=len(...)) and enforces
parity across the six language files. Pure JSON tests — no network, no
~/.gitpr reads; src.i18n is imported lazily inside the smoke test only
(its module init reads the user .env and may attempt a download).
"""
import ast
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

# Sources scanned for live __() calls.
SCAN_ROOTS = [REPO / "src", REPO / "run.py"]

# Keys that are deliberately identical to their English text because they are
# AI prompt fragments, not UI: they are concatenated into the model's system
# instruction / context, where translating them would change model behaviour.
# Anything NOT matching one of these prefixes is user-facing debt.
AI_PROMPT_PREFIXES = (
    "You are a Software Architect.",
    "You are a Senior Software Engineer",
    "Analyze the diff of commit {commit_hash}",
    "Generate ONLY a JSON object in the format {json_format}",
    "Generate the requested JSON object following the system instructions",
    "Repository: {repo_name}",
    # Blame timeline rows, assembled into the issue prompt at main.py:1032-1037
    # ("Translate the dictionary list into AI-readable text").
    "[{date}] Commit {hash} by {author}:",
    "Action: {status}",
    "AI Reason: {reason}",
)


def _extract_keys_ast(path, keys):
    """Collects every __("literal") key in *path* using the AST.

    Preferred over the regex in tests/sync_i18n.py for verification because the
    parser folds implicit concatenation — __("a " "b") and multi-line literals
    arrive as ONE Constant, matching the string the runtime lookup actually
    builds. The regex captures only the first fragment, which made 21 real keys
    look "missing" while their full forms looked like orphans.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id != "__" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            keys.add(first.value)


def _keys_used_in_code():
    """Every statically-resolvable __() key across src/ and run.py."""
    keys = set()
    for root in SCAN_ROOTS:
        if root.is_file():
            _extract_keys_ast(root, keys)
        elif root.is_dir():
            for path in root.rglob("*.py"):
                _extract_keys_ast(path, keys)
    return keys


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
        """Every language file must expose the exact same key set.

        Parity is the real invariant. The previous hard-coded total (547) went
        stale the moment 91 legitimate keys landed in 9a9affb, failing with a
        number that said nothing about correctness. A floor still catches a
        truncating write that wipes most of a file.
        """
        reference = set(self.langs["pt_br.json"])
        self.assertGreater(len(reference), 500, "lang files look truncated")
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
        """Untranslated keys are only tolerated for AI prompts and status markers.

        [OK]/[FAIL] are universal markers from the MCP installer. Everything else
        must be an AI prompt fragment (see AI_PROMPT_PREFIXES) — those feed the
        model's instructions, so translating them would change its behaviour.
        A new identity key that is NOT a prompt is user-facing untranslated debt
        and fails here by name.
        """
        status_markers = {"  [OK] {editor}: {message}", "  [FAIL] {editor}: {message}"}
        for name in LANG_FILES:
            identity = {k for k, v in self.langs[name].items() if k == v and "{" in k}
            markers = {k for k in identity if "[OK] {" in k or "[FAIL] {" in k}
            self.assertEqual(markers, status_markers, f"{name}: unexpected status markers")

            unexplained = [
                key
                for key in identity - markers
                if not key.startswith(AI_PROMPT_PREFIXES)
            ]
            self.assertEqual(
                unexplained,
                [],
                f"{name}: untranslated user-facing key(s) — translate them, or add "
                f"the prefix to AI_PROMPT_PREFIXES if they are AI prompts: {unexplained}",
            )


class TestNoMissingKeys(unittest.TestCase):
    """Guards that every __() call in the source has a dictionary entry.

    This is the `missing == 0` condition: previously the suite only checked
    parity, mangled keys and identity keys, so a NEW __() call with no entry
    slipped through silently and fell back to English at runtime.
    """

    @classmethod
    def setUpClass(cls):
        cls.langs = _load_langs()
        cls.code_keys = _keys_used_in_code()

    def test_extraction_found_keys(self):
        """Sanity: a broken extractor must fail loudly, not vacuously pass."""
        self.assertGreater(len(self.code_keys), 400, "AST extraction found too few keys")

    def test_no_missing_keys(self):
        for name in LANG_FILES:
            data = self.langs[name]
            missing = sorted(k for k in self.code_keys if k not in data)
            self.assertEqual(
                missing,
                [],
                f"{name}: {len(missing)} __() key(s) have no entry — "
                f"run `python tests/sync_i18n.py` and translate them: "
                f"{[k[:70] for k in missing[:5]]}",
            )

    def test_no_orphan_keys(self):
        """Keys no __() call references any more are dead weight — drop them."""
        for name in LANG_FILES:
            orphans = sorted(k for k in self.langs[name] if k not in self.code_keys)
            self.assertEqual(
                orphans,
                [],
                f"{name}: {len(orphans)} orphan key(s) no longer used in code: "
                f"{[k[:70] for k in orphans[:5]]}",
            )

    def test_missing_key_is_detected(self):
        """The guard's comparison must actually fire on an unknown key.

        Kept isolated from the real dictionaries so it asserts the detection
        logic itself, not the repository's current translation state.
        """
        fake = "__GITPR_TEST_KEY_THAT_DOES_NOT_EXIST__ {x}"
        data = {"known key": "chave conhecida"}
        code_keys = {"known key", fake}

        missing = sorted(k for k in code_keys if k not in data)
        self.assertEqual(missing, [fake])

    def test_ast_extractor_joins_implicit_concatenation(self):
        """Adjacent/multi-line literals must resolve to the full runtime key.

        The regex in tests/sync_i18n.py stops at the first fragment, which is
        why 21 keys looked missing before this extractor replaced it here.
        """
        import tempfile

        source = 'from src.i18n import __\n__("part one " "and part two {n}", n=1)\n'
        with tempfile.TemporaryDirectory() as tmp:
            probe = Path(tmp) / "probe.py"
            probe.write_text(source, encoding="utf-8")
            keys = set()
            _extract_keys_ast(probe, keys)

        self.assertEqual(keys, {"part one and part two {n}"})


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
