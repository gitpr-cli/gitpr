# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
fix: repair mangled i18n keys across language files
```

---

🎯 Summary
Corrects a translation lookup bug where the legacy i18n extraction regex captured call-site keyword arguments (e.g. `fg="cyan"`, `count=len(...)`) into translation keys. Mangled keys always failed runtime lookups, so non-English users saw English fallbacks. This change rebuilds all six language JSON files with clean keys and actual translations, adds a one-off repair script and regression test, improves the extraction regex, and bumps the language dictionary version.

🛠️ Technical Changes
- Added `scripts/fix_mangled_i18n_keys.py` to detect and replace 51 mangled identity keys with 50 clean keys across pt_BR/pt_PT/es/es_ES/fr/fr_FR, complete the truncated MCP key, prune orphan keys, and restore missing stage-error key in es/fr.
- Updated `langs/*.json` with proper translations for affected strings, maintaining 529 identical keys per file.
- Rewrote `tests/sync_i18n.py` regex to parse only the string literal of `__()` calls, avoiding call-site fragment capture; handles source escape sequences via `ast.literal_eval`.
- Added `tests/test_i18n.py` with parity, mangling, truncation, orphan, and formatting smoke tests.
- Adjusted `src/mcp_server.py` prompt string into a single literal (no string concatenation) to match extraction.
- Bumped `__lang_version__` to `v0.0.16` in `src/updater.py`.

⚠️ Impact/Warnings
- No database, environment variable, or external dependency changes.
- Language dictionary version changed to `v0.0.16`; local caches/translations should refresh via normal update flow.
- Key sets are now identical across all six language files (529 keys); future sync should preserve parity.