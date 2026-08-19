# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit
```

---

## 🎯 Summary

This feature introduces a comprehensive Pull Request publishing workflow, including an interactive Terminal User Interface (TUI) for reviewing/editing PR content, automatic commit with lint verification, and direct publication to GitHub via API. Localization for four languages, new environment variables for customizing behavior, and metrics export for logging are also added.

## 🛠️ Technical Changes

- Added `src/github_api.py` for GitHub REST API PR creation with error handling.
- Added `src/ui/pr_publish_app.py` implementing the TUI using Textual with commit process, linter integration, file staging, and progress modal.
- Added `src/ui/pr_publish_help.py` for help modal.
- Added `--no-publish`, `--no-edit`, and `--base` CLI options to `src/main.py`.
- Added `has_uncommitted_changes()` and `execute_git_commit()` helper functions to `src/core.py`.
- Added new default environment variables to `src/config.py` (PR_DEFAULT_BASE, GITPR_AUTO_COMMIT, GITPR_SKIP_LINT, GITPR_AUTO_STAGE, GITPR_SHOW_LOGS).
- Extended localization files (`es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`) with over 70 new translation keys for the publishing interface.
- Added metrics export files for testing.

## ⚠️ Impact/Warnings

- Requires the `textual` Python library for TUI (new dependency).
- New environment variables control commit and lint behavior; defaults are off (false).
- Users must have a valid GitHub token to publish via API; token expired handling is implemented with re-authentication flow.
- No database schema changes.