# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add i18n validation and sync scripts, update translations
```

---

🎯 Summary

This PR enhances the internationalization (i18n) system by adding scripts to validate translations and synchronize language keys, while also updating all translation files with new keys, removing obsolete ones, and translating documentation into multiple languages. It also fixes a critical circular import in the i18n module and ensures proper UTF-8 encoding on Windows systems.

🛠️ Technical Changes

- Added `check_i18n.py` script to validate i18n usage and output a report.
- Added `sync_i18n.py` script to scan source code for translation calls, add missing keys, and remove obsolete keys from all language JSON files automatically.
- Translated GitHub CI Linter, GitPR Issue Option, and Regex Guide documentation into English and other languages, with localized markdown files.
- Updated all language files (`langs/*.json`) with new translation keys and removed obsolete ones based on script sync.
- Fixed circular import in `i18n.py` by deferring `__lang_version__` import and delaying cache initialization.
- Added `sys.stdout.reconfigure(encoding='utf-8')` in `main.py` for proper UTF-8 output on Windows.
- Added `pyright` configuration to `pyproject.toml`.
- Updated `updater.py` to import `__` for translation support.

⚠️ Impact/Warnings

- Language JSON files have been modified; any custom translations should be reconciled with the updated keys.
- The circular import fix affects the initialization order of the i18n module, but should be transparent.
- Windows users may experience improved UTF-8 output; test thoroughly.
- Pyright configuration may alter type checking behavior.