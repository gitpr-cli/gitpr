# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add document translations and localization synchronization
```

---

## 🎯 Summary
This PR significantly enhances the project's internationalization (i18n) and localization (l10n) capabilities, making the system accessible to a broader audience. It translates core documentation into English and adds localized versions in Portuguese (Brazil and Portugal), French, and Spanish. The interface localization files have been expanded and reorganized for completeness. Additionally, a new synchronization script ensures translation files stay in sync with code changes, and several technical improvements (circular import fix, Windows UTF-8 encoding) have been implemented to support these features.

## 🛠️ Technical Changes
- Translated main documentation (`github-ci-linter`, `guia-regex-gitpr`, `gitpr-issue-option`) from Portuguese to English and created localized versions for `pt_BR`, `pt_PT`, `fr_FR`, and `es_ES`.
- Expanded and reorganized UI localization files (`es_ES.json`, `fr_FR.json`, `pt_BR.json`, `pt_PT.json`) with numerous new translated keys.
- Added completion reports for translation tasks in `docs/gemini/reports`.
- Updated metrics cache with new prompt entries for commit, issue, and PR description.
- Added Pyright configuration in `pyproject.toml` to enforce type checking.
- Refactored `i18n.py` to avoid circular import by moving `__lang_version__` import inside `get_translations` and relocating session variable initialization.
- Reconfigured `stdout` to UTF-8 encoding on Windows in `main.py` for correct character display.
- Modified `updater.py` to import the translation function `__`.
- Added `tests/sync_i18n.py` script to automatically synchronize translation JSON files with the keys found in the source code.

## ⚠️ Impact/Warnings
- New locale files and directories must be included in deployment artifacts.
- Windows environments now enforce UTF‑8 output; this may affect legacy terminals that do not support UTF‑8. Ensure compatibility.
- Translations may still be incomplete; the new `sync_i18n.py` script helps identify missing keys and should be run after adding new translatable strings.
- The refactoring in `i18n.py` moves imports inside functions; confirm that all callers still receive the correct translations early enough.

close #76