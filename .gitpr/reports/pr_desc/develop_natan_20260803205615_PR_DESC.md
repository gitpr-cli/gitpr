# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add i18n, sync translations, fix encoding and imports
```

---

## 🎯 Summary
This PR introduces internationalization (i18n) support by translating core documentation into English and adding localized versions for Portuguese (Brazil and Portugal), Spanish, and French. It also resolves critical project issues: a circular import in i18n.py, Windows terminal encoding for emojis, and missing type checking configuration. A new script automates translation key synchronization.

## 🛠️ Technical Changes
- Translated main documentation to English and created localized versions for pt_BR, pt_PT, es, and fr.
- Updated language files for Spanish (es_es) and French (fr_fr).
- Fixed circular import in i18n.py: moved `__lang_version__` import inside function and deferred cache initialization to end of module.
- Configured stdout to UTF-8 in main.py to prevent emoji-related crashes on Windows.
- Added internationalization support to updater.py by importing the `__` function.
- Included Pyright configuration in pyproject.toml for static type checking.
- Created sync_i18n.py script to scan the codebase for translation keys and automatically update all language JSON files.

## ⚠️ Impact/Warnings
- The new `sync_i18n.py` script should be executed whenever user-facing strings are added or removed to keep translations consistent.
- The change in i18n.py cache initialization order may affect modules importing it early; ensure no side effects during startup.
- Forcing stdout to UTF-8 on Windows resolves emoji display issues but may override existing encoding settings for some users.