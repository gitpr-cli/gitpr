# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: add i18n translations for MCP installer output
```

---

## 🎯 Summary
This change completes localization efforts by translating the MCP installer messages into Spanish, French, and Portuguese, fixing escaped newline character issues in language dictionaries, and updating the language version to v0.0.19. It also introduces metric export files for the current date.

## 🛠️  Technical Changes
- Internationalized MCP server installer output using the `__()` translation function.
- Updated `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt` dictionaries with new translations and corrected `\n` escaping.
- Bumped `__lang_version__` from v0.0.17 to v0.0.19.
- Adjusted `tests/test_i18n.py` to reflect 547 keys and allow status markers as identity keys.
- Patched `TRANSLATIONS` to empty dict in `tests/test_external_linters.py` to ensure deterministic test reports.
- Added `.gitpr/metrics/export/gitpr_metrics_2026-08-19.csv` and `.json`.

## ⚠️  Impact/Warnings
- No database, environment variable, or dependency changes.
- Translation version bump may require updating language packs; this PR includes the updated dictionaries.

close #135