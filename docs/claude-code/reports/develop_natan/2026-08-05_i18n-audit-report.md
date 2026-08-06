# i18n Audit Report

**Date:** 2026-08-05
**Audited files:** `src/core.py`, `src/updater.py`
**Language files:** `langs/pt_br.json`, `langs/pt_pt.json`, `langs/fr.json`, `langs/es.json`

---

## Executive Summary

- **Total unique i18n keys from audited scope:** 89 (82 from core.py, 10 from updater.py, 3 overlap)
- **Language files checked:** 4 (en uses keys as-is, no file needed)
- **Status of audited keys:** ✅ All 89 keys present in all 4 language files
- **New files created:** `langs/fr.json`, `langs/es.json`
- **Keys added to existing files:** 8 new keys added to `pt_br.json` and `pt_pt.json`
- **Total keys per file:** 595 (all files have identical key counts)

---

## Per-Language Status

| Language | File | Status | Missing (audited) | Extra keys* | Notes |
|----------|------|--------|-------------------|-------------|-------|
| English (en) | *(no file)* | ✅ Complete | 0 | N/A | English is the default/fallback — keys in code ARE the English text |
| Portuguese BR (pt_br) | `langs/pt_br.json` | ✅ Complete | 0 | 506 | 8 new hooks versioning keys added |
| Portuguese PT (pt_pt) | `langs/pt_pt.json` | ✅ Complete | 0 | 506 | 8 new hooks versioning keys added |
| French (fr) | `langs/fr.json` | ✅ Created | 0 | 506 | New file — 89 audited keys translated, remaining use English fallback |
| Spanish (es) | `langs/es.json` | ✅ Created | 0 | 506 | New file — 89 audited keys translated, remaining use English fallback |

*Extra keys are from source files outside the audit scope (main.py, blame_engine.py, chat_app.py, config.py, etc.) — all legitimate and kept as-is per the "never remove keys" rule.

---

## New Keys Added (2026-08-05)

These 8 keys were added during the audit — they were introduced by the hooks versioning feature but not yet present in language files:

| Key | pt_br | pt_pt | fr | es |
|-----|-------|-------|----|----|
| `🔍 Checking hook scripts version...` | ✅ | ✅ | ✅ | ✅ |
| `   Current: {current} (from .env)` | ✅ | ✅ | ✅ | ✅ |
| `   Latest: {latest} (from code)` | ✅ | ✅ | ✅ | ✅ |
| `📦 Updating scripts to {version}...` | ✅ | ✅ | ✅ | ✅ |
| `   Detected language: {lang}` | ✅ | ✅ | ✅ | ✅ |
| `⚠️ Failed to install {hook_name}: HTTP {code}` | ✅ | ✅ | ✅ | ✅ |
| `✅ Scripts synced successfully!` | ✅ | ✅ | ✅ | ✅ |
| `none` | ✅ | ✅ | ✅ | ✅ |

---

## Hardcoded String Analysis

2 lines flagged by the automated scanner — both are **false positives**:

| File | Line | Text | Verdict |
|------|------|------|---------|
| `src/core.py` | 138 | `"- {file}"` | False positive — inside an f-string loop iterating `untracked_files`, the `{file}` is an f-string variable, not a user-facing literal |
| `src/core.py` | 730 | `"{get_doc_url('install-wizard.md')}"` | False positive — this is an f-string embedding a function call result, the actual path is dynamic |

**Conclusion:** No hardcoded user-facing strings found. All user-facing output in `core.py` and `updater.py` properly uses `__()`.

---

## Placeholder Validation

All placeholders (`{error}`, `{version}`, `{lang}`, `{hook_name}`, `{code}`, etc.) are correctly preserved across all 4 language files. No placeholder errors detected.

---

## New Files Created

### `scripts/validate_i18n.py`
Automated validation script that:
- Extracts all `__()` calls from specified source files
- Compares against language JSON files
- Reports missing keys, extra keys, and placeholder errors
- Flags potential hardcoded strings

Usage:
```bash
python scripts/validate_i18n.py
```

### `scripts/generate_lang_files.py`
Generator script used to create initial `fr.json` and `es.json` from the `pt_br.json` key structure with proper translations for the audited scope.

---

## Future Recommendations

1. **Expand audit scope:** Run the validation script against all source files (`src/*.py`, `src/ui/*.py`) to ensure complete coverage
2. **Complete fr.json and es.json:** The 506 extra keys currently use English fallback values — they should be properly translated to French and Spanish
3. **CI/CD integration:** Add `scripts/validate_i18n.py` to the CI pipeline to catch missing keys on every PR
4. **Add en.json reference file:** Even though English uses keys directly, a reference `langs/en.json` would make the key count comparison simpler
5. **Document the i18n workflow** in `CONTRIBUTING.md` so contributors know to update all language files when adding new `__()` calls
