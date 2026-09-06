# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
chore: update repository URLs and localize issue prompts
```

---

🎯 Summary

User-facing help, documentation links, and issue-flow instructions still referenced the old `natanfiuza/gitpr` location. This PR updates all repository references to `gitpr-cli/gitpr.git` and completes the localization of the AI/issue prompt strings so users no longer receive mixed-language instructions.

🛠️ Technical Changes

- Replaced the repository URL in the CLI footer (`src/main.py`), issue TUI instructions (`src/tui_issue.py`), chat help (`src/ui/chat_app.py`), and help screen (`src/ui/help_screen.py`).
- Updated the matching URL entries in the Spanish, French, and Portuguese language files (`langs/es*.json`, `langs/fr*.json`, `langs/pt*.json`).
- Localized the previously untranslated `Changed documentation...` label and the JSON-generation instruction prompts for ES, FR, and PT locales.
- Refreshed the source dictionaries in `scripts/sync_all_langs.py` so future syncs keep the new URL and translated entries.
- Adjusted `tests/test_i18n.py` by removing the now-localized AI prompt prefixes from the allowed `AI_PROMPT_PREFIXES` list and documenting why they must remain translated.

⚠️ Impact/Warnings
- No database, environment variable, or dependency changes.
- Repository links shown in help, docs, and issue flows now point to `https://github.com/gitpr-cli/gitpr.git`; consumers should verify no stale `natanfiuza/gitpr` references remain.
- i18n validation is stricter for the AI instruction strings, so future locales must provide translations for those entries.


close #151