# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publishing workflow with TUI and auto-commit
```

---

## 🎯 Summary
Introduce a complete PR publishing workflow that includes an interactive TUI, automatic commit generation and staging, linter validation, and direct GitHub API integration. This simplifies the PR creation process by handling local changes automatically and providing a user-friendly interface.

## 🛠️ Technical Changes
- Added PR publisher TUI (`src/ui/pr_publish_app.py`) with modals for commit confirmation, file staging, progress animation, linter error handling, and error screens.
- Implemented auto-commit flow with optional linter check and AI-generated commit message.
- Added GitHub API module (`src/github_api.py`) for creating pull requests via REST.
- Integrated auto-staging of unstaged files with selection TUI.
- Added configuration options: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, etc.
- Extended CLI with `--base`, `--no-publish`, `--no-edit` flags.
- Updated translations for `es_es`, `fr_fr`, `pt_br`, `pt_pt` with new UI strings.
- Added metrics export files for 2026-08-07 and 2026-08-08.

## ⚠️ Impact/Warnings
- **New dependencies**: `textual`, `requests` must be installed.
- **Environment variables**: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, etc. may alter behavior; ensure they are documented.
- **Default behavior changed**: Now opens interactive TUI by default instead of just saving locally. Use `--no-publish` to restore previous behavior.
- The `--no-edit` flag is new and triggers auto-publish mode; does not break existing usage (previously flag did not exist).
- **Security**: GitHub token validation and reauthentication loops are added; ensure secure token handling.


close #90