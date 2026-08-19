# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publishing to GitHub with TUI and auto-commit
```

---

## 🎯 Summary

This feature enables publishing Pull Requests directly to GitHub via REST API from an interactive TUI (Textual). It also introduces an auto-commit flow, linter integration, and support for multiple languages. Users can now review, edit, and publish PRs without leaving the terminal.

## 🛠️ Technical Changes

- **New module `src/github_api.py`**: Implements `create_pull_request()` using `requests`, with error parsing and connection handling.
- **Extended `src/core.py`**: Added `has_uncommitted_changes()` and `execute_git_commit()` to support automatic commits.
- **Enhanced CLI (`src/main.py`)**:
  - New options: `--base`, `--no-publish`, `--no-edit`.
  - Integrated PR publisher logic, including direct publish mode (`--no-edit`) and TUI mode (default).
  - Auto-commit flow with linter validation (`_run_auto_commit_cli()`).
  - Direct publishing helper (`_publish_pr_directly()`).
- **Textual TUI app (`src/ui/pr_publish_app.py`)**:
  - `PrPublishApp`: main interface for title/body editing, file staging, commit with progress/log display, linter modal, and PR creation.
  - `CommitConfirmScreen`, `FileStageScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`: modal screens for a polished user experience.
- **Help screen (`src/ui/pr_publish_help.py`)**: In-app documentation for publisher shortcuts.
- **Configuration (`src/config.py`)**: Added default keys: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`.
- **Localization**: Added ~75 new translation strings across all supported languages (es_es, fr_fr, pt_br, pt_pt).
- **Metrics export**: Included example metric files (CSV/JSON) under `.gitpr/metrics/export/` (development artifacts).

## ⚠️ Impact/Warnings

- **New dependencies**: The `requests` library is required for GitHub API calls.
- **Environment variables**: Introduces new configuration options for PR publication behavior (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, etc.). Ensure backward compatibility – all default to safe values.
- **CLI interface**: The default behavior now opens an interactive TUI after PR generation. Users expecting only a local file will need to use `--no-publish`.
- **GitHub token**: A valid GitHub token is mandatory for publishing. The TUI handles re-authentication on 401 errors.
- **Linter integration**: Linting is enabled by default during auto-commit; can be skipped with `GITPR_SKIP_LINT=true`.
- **File changes**: Extensive additions to language files; no existing translations modified except to add new keys.