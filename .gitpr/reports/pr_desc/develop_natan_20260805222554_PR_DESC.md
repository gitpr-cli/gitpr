# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add i18n hooks, versioning, and auto-sync with comprehensive docs
```

---

## 🎯 Summary
This PR introduces full internationalization for GitPR's hook scripts, allowing them to be automatically translated into Portuguese (Brazil and Portugal), Spanish, and French. It also implements an independent versioning system and an automatic synchronization mechanism that updates hooks to the correct language and version on every GitPR execution. Extensive documentation in 5 languages explains the new system, and maintenance scripts are provided to manage translations and language files.

## 🛠️ Technical Changes
- Created language-specific hook scripts (`pre-commit`, `prepare-commit-msg`, etc.) in `pt_br`, `pt_pt`, `fr`, and `es`.
- Implemented `check_and_update_hooks_scripts()` to auto-detect system language and download the appropriate hook scripts on GitPR startup.
- Added versioning to hook scripts with `__scripts_version__` and automatic version stamping in `.env`.
- Developed `final_fix.py` to clean up corrupted translation keys, remove smart quotes, and synchronize language pairs.
- Added new language files (`fr.json`, `pt_br.json`, `pt_pt.json`, `es.json`) and updated existing ones with corrected translations.
- Created maintenance scripts: `fix_pt_br`, `sync_all_langs`, `validate_i18n`, and `generate_lang_files` to assist with translation management.
- Updated README files in 5 languages with a new section on hook versioning and links to technical documentation.
- Produced detailed technical documentation in 5 languages covering hooks versioning, auto-sync, and i18n architecture.
- Included development plans and i18n audit reports to track translation completeness and quality.

## ⚠️ Impact/Warnings
- On the next GitPR run, your existing hooks will be replaced by versioned, language-specific scripts. Any custom modifications to hook scripts should be backed up.
- The `.env` file will receive a `HOOKS_VERSION` entry after installation; manually altering it may break the auto-sync feature.
- Language files are now automatically validated; corrupted keys or smart quotes will be cleaned up by `final_fix.py`. Ensure that translation teams are aware of the new key structure.
- The auto-sync process downloads hooks from the repository, so network connectivity is required during the first run after an update.

close #82