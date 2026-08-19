# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with GitHub API integration and auto-commit
```

---

## 🎯 Summary

Implements a complete Pull Request publication workflow: an interactive Textual TUI for reviewing and editing PR content, automatic commit of pending changes with linter validation, and direct API-based creation of pull requests on GitHub.

## 🛠️ Technical Changes

- **New GitHub API module** (`src/github_api.py`): creates PRs via REST API with error handling for authentication, API errors, and network issues.
- **Extended core Git helpers** (`src/core.py`): added `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, and `execute_git_commit` to support the automated commit flow.
- **New TUI** (`src/ui/pr_publish_app.py`): interactive screen for editing title/body, commit confirmation, linter integration, progress animation, and GitHub publishing.
- **Help screen** (`src/ui/pr_publish_help.py`): modal with key bindings and documentation link.
- **Updated main CLI** (`src/main.py`): new options `--base`, `--no-publish`, `--no-edit`; default behavior now opens the TUI; helper functions for auto-commit and direct publish.
- **Localization** (`langs/es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`): added translations for all PR publisher strings, commit flow messages, and error handling.
- **Configuration** (`src/config.py`): introduced new environment variables (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`) to customize behavior.
- **Metrics exports**: added sample CSV/JSON files under `.gitpr/metrics/export/`.

## ⚠️ Impact/Warnings

- **New default behavior**: running `gitpr` without any option now opens an interactive TUI for PR review and publication.
- **Environment variables**: several new vars control auto-staging, auto-commit, lint behavior, and logging; ensure they are set intentionally.
- **GitHub token required**: publishing a PR via the TUI or `--no-edit` requires a valid GitHub token (obtained interactively during the flow).
- **Dependency**: Python `requests` library is now required for the GitHub API module.
- **File changes**: new files `src/github_api.py`, `src/ui/pr_publish_app.py`, `src/ui/pr_publish_help.py`; modified `src/main.py`, `src/core.py`, `src/config.py` and all language JSON files.