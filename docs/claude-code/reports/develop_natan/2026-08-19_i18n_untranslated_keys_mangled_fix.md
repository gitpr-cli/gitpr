# Completion Report — i18n: Translate All Untranslated Keys + Repair Mangled Dictionary Keys

## What was done
- Executed the next steps of the previous task report (2026-08-19_i18n_install_wizard): translate the pre-existing untranslated keys and fix the 2 locale-dependent test failures.
- Full-codebase AST audit (all modules in `src/`, including `src/ui/`): the untranslated-key set was larger than the 19 keys found by the install-flow audit — 28 in pt_br and up to 110 in es/fr.
- Repaired 36 mangled keys per language file: keys captured by the old sync regex with literal `\n` instead of real newlines (and one key with literal `\'` instead of an apostrophe) were unreachable — `__()` never matched them. Repaired keys and values; 16 per file were exact duplicates of correct keys added in the previous task and were dropped. Result: 563 → 547 keys per file.
- Translated all remaining untranslated keys (value == key) in all 6 languages: 438 hand-written translations applied (pt_br 28+, pt_pt 44+, es 110, fr 108), plus 132 values cross-filled between the duplicate dictionaries (es_es → es and fr_fr → fr, same language family).
- Kept 11 keys intentionally in English (documented in the sync script): AI prompts/context sections (`=== AI PR HISTORY ===`, `=== REGISTERED COMMITS ===`, blame summary instruction, architect prompt), universal status markers (`[OK]`/`[FAIL]`), and universal tech terms (`Tokens`, `Auto-Patch`).
- Fixed the 2 locale-dependent tests in `tests/test_external_linters.py` by pinning `src.i18n.TRANSLATIONS` to `{}` (English) via `mock.patch` — the assertions no longer depend on the machine's OS locale.
- Updated `tests/test_i18n.py` for the new dictionary size (563 → 547).
- Bumped `__lang_version__` (v0.0.18 → v0.0.19) in `src/updater.py` so users re-download the repaired dictionaries OTA on the next run.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| langs/pt_br.json | fix | 36 mangled keys repaired (literal `\n`/`\'` → real); 16 dead duplicates dropped; all untranslated keys translated (547 keys) |
| langs/pt_pt.json | fix | Same repair + translations (European Portuguese style) |
| langs/es.json | fix | Same repair + translations; 66 values filled from es_es |
| langs/es_es.json | fix | Same repair + translations |
| langs/fr.json | fix | Same repair + translations; 66 values filled from fr_fr |
| langs/fr_fr.json | fix | Same repair + translations |
| src/updater.py | feat | `__lang_version__` v0.0.18 → v0.0.19 (OTA re-download trigger) |
| tests/test_external_linters.py | test | 2 report-content tests pinned to English translations via `mock.patch` (locale-independent) |
| tests/test_i18n.py | test | Key count 563 → 547 |

## Impact
- **Functionality:** All dictionaries now have **0 untranslated keys and 0 mangled (unreachable) keys** in all 6 languages — verified by an authoritative AST audit against 638 keys used in code. Every user-facing message that has a dictionary entry is translated; the previously-dead entries (e.g. `# Timeline of the investigated rule`, PR publisher buttons, `--status` messages) are reachable and translated. The 2 external-linter tests now pass on any locale.
- **Performance:** None — translation lookup is an in-memory dict read.
- **Compatibility:** No API breaks. Dictionaries self-update via the `__lang_version__` bump. 11 intentional-identity keys are kept English by design (AI prompt content and universal markers). Key sets remain identical across the 6 files.

## Test results
- `pytest tests/ -q`: **259 passed, 0 failed** — the entire suite is green for the first time on this pt-BR machine (the 2 pre-existing locale failures are fixed).
- Authoritative audit (file-based, escape-safe): `mangled=0`, `untranslated=0`, `missing=91` per language (see next steps).
- `tests/test_i18n.py`: 14/14 passed (parity, count, mangled-keys guard, identity allowlist).

## Next steps (if applicable)
- **91 keys are still missing from all dictionaries** (used in code via `__()` but absent from the JSONs). They fall back to English. They include: MCP tool descriptions (`Get current branch info...`, `Run the static linter...`), TUI strings (`❌ Merge Conflict`, `✅ PR saved locally: {output_filename}`), updater/ai_providers/github_api messages, and blame-engine report lines. A follow-up task should add them; AI-prompt-shaped keys (e.g. the Pair Programmer system prompt, `Analyze the diff of commit {commit_hash}...`) should stay English by design.
- The escaped-apostrophe repair (`\'` → `'`) applied to 1 key per file; a broader scan for other escape artifacts (e.g. `\t`, `\"`) could be run in the same follow-up.
- Consider extending `tests/test_i18n.py` with a guard asserting `missing == 0`-class checks (currently it only guards parity, mangled keys and identity keys), so new `__()` calls without dictionary entries fail CI.
