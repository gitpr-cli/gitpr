## Completion Report — i18n Mangified Keys Cleanup

### What was done
- Created and ran the one-off repair script `scripts/fix_mangled_i18n_keys.py`: detected 51 mangled keys per file (identity keys whose text captured call-site fragments like `fg="cyan"` or `count=len(...)`), derived the 50 clean runtime keys, and replaced them with full translations in all 6 files of `langs/` (pt_br, pt_pt, es_es, es, fr_fr, fr)
- The mangled keys stored newlines double-escaped (literal backslash-n) while the runtime strings contain real newlines — the script now unescapes when deriving clean keys (bug found and fixed on first run)
- Restored parity: all 6 files now have exactly 529 keys with identical key sets (es/fr gained the missing `❌ Failed to stage files: {error}` key, mirrored from es_es/fr_fr)
- Pruned 2 orphan keys per file (`No files selected for staging.` and `❌ Failed to stage files`, dead after the FileStageScreen removal)
- Repaired the truncated MCP prompt key: refactored the call site in `src/mcp_server.py` from adjacent literals to a single literal, then added the full runtime key `Generate a Conventional Commits message (e.g., 'feat: add user auth') from the current uncommitted changes.` translated in all 6 languages
- Bumped `__lang_version__` from v0.0.15 to v0.0.16 in `src/updater.py` so the OTA download picks up the corrected files (invariant: JSONs + bump land on `main` in the same PR)
- Fixed the root cause in `tests/sync_i18n.py`: the old regex required a closing `)` after the literal quote, which ran the match past kwargs and mangled keys. The new `PATTERN` stops at the literal's own quote and parses the captured literal with `ast.literal_eval`, so escape sequences resolve to the exact runtime string. The script was refactored into an importable module (`scan_file` / `scan_dir` / `scan` / `_extract_keys`, constants `SRC_DIRS` / `LANG_FILES` / `PATTERN`, `__main__` guard)
- Hardened the sync rebuild loop: lookups now go through a `_live_key()` unescaping index so legacy double-escaped entries migrate to their live keys instead of being dropped, and the script refuses to write anything when the scan extracts zero keys (guard added after a first-run incident where an empty scan overwrote the 6 JSONs)
- Created `tests/test_i18n.py` with 14 regression tests: JSON validity, no mangled-key patterns, key parity + 529 count, the 50 clean keys translated, truncated/orphan keys pruned, stage-error key restored, identity-key allowlist, extraction-regex unit tests, and a formatting smoke through the real `__()` function
- Verified the dry-run of the fixed sync: the new regex extracts 628 runtime keys and covers the live form of all 529 committed keys (zero loss); the resulting rewrite was analyzed and reverted per the plan's fallback (details in Next steps)

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| langs/pt_br.json | fix | 51 mangled keys → 50 clean translated keys, 2 orphans pruned, MCP key completed (532 → 529) |
| langs/pt_pt.json | fix | Same repair with pt_pt regional variants (e.g. `ficheiros`) |
| langs/es_es.json | fix | Same repair; FR/ES translations mined from sync_all_langs.py dicts + fresh-authored |
| langs/es.json | fix | Same repair + stage-error key restored (531 → 529) |
| langs/fr_fr.json | fix | Same repair |
| langs/fr.json | fix | Same repair + stage-error key restored (531 → 529) |
| scripts/fix_mangled_i18n_keys.py | feat | One-off repair script: detection, derivation, translation tables, asserts, in-place rewrite preserving key order |
| src/mcp_server.py | refactor | MCP prompt description from adjacent literals to a single literal (extractable by the sync) |
| src/updater.py | chore | `__lang_version__` v0.0.15 → v0.0.16 |
| tests/sync_i18n.py | fix | New `PATTERN` (no trailing `)` requirement), importable module structure, `_live_key()` fuzzy lookup, empty-scan guard, trailing newline preserved on write |
| tests/test_i18n.py | test | 14 regression tests guarding against mangled keys and enforcing language parity |
| docs/plans/2026-08-15_i18n_mangled_keys_cleanup.md | docs | Detailed plan for this task (previously untracked, committed here) |
| docs/claude-code/reports/develop_natan/2026-08-15_i18n_mangled_keys_cleanup.md | docs | This completion report |

### Impact
- **Functionality:** ~50 messages that always fell back to English (even with the language installed) are now fully translated in the 6 supported languages, including all AI prompt templates and the MCP prompt description. The static linter, blame engine, updater, hooks installer, staging and metrics flows are the main beneficiaries.
- **Performance:** N/A (dictionary lookups unchanged; 529 keys per file, 3 fewer than before)
- **Compatibility:** No API breaks. Language files need the `__lang_version__` bump to reach users via OTA — JSONs and bump are in the same PR by design. The sync script behavior changed (extraction now yields runtime keys; rebuild preserves legacy translations), but it is a maintenance tool, not shipped runtime code.

### Next steps (if applicable)
- **Second dead-key family (discovered via sync dry-run):** the JSONs still contain 57 identity keys double-escaped with literal `\n` (e.g. `"\\nStep 2 of 4: Git Hooks"`) that never match runtime strings — a sibling of the repaired family, but without call-site fragments. The sync's `_live_key()` index already migrates them; a follow-up can promote them to live keys in the JSONs themselves (all 57 are identity keys, so no translation loss).
- **~99 missing runtime keys:** the sync extracts 628 keys vs 529 in the files. Beyond the 57 restorations, ~69 single-line keys were never synced (e.g. `No API key found for {provider}.`, `\r⚠️ API instability (...). Retrying (...)` in ai_providers.py, `File not found: {file_path}`) and should be added with translations; ~30 are truncated prefixes of multi-line MCP descriptions (documented PATTERN limitation — dead-on-arrival if added, and the main reason the dry-run output was reverted rather than kept).
- **Nested key untranslated:** the nested `none` key in `core.py:1317` (`__("   Current: {current} (from .env)", current=env_version or __("none"))`) remains English by design — the outer key is translated, the inner is a parameter value.
- **English-by-design keys:** `ORIGIN` / `REFACTORING` (blame_engine.py:242) are protocol values, intentionally not translated; `You are a Software Architect...` is an LLM prompt kept as English identity (allowlisted by test 8).
- **Legacy scripts:** `scripts/` one-offs (`fix_pt_br.py`, `fix_pt_br_pass2.py`, `final_fix.py`, `_temp_check_i18n.py`, `generate_lang_files.py`) still contain inert mangled-key tables and are candidates for deletion or archival.
- **Pre-existing test failures:** `tests/test_external_linters.py::TestGenerateLinterReportContent` (2 tests) fail on this machine because the OS locale resolves to pt_br while the tests expect English output — confirmed failing on clean HEAD before this work; fix by forcing `GITPR_LANG=en_us` in those tests.
