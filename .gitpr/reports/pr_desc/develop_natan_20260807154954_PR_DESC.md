# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with TUI and auto-commit
```

---

## 🎯 Summary

This change introduces a new **PR Publisher** feature, allowing developers to review, edit, and publish Pull Requests directly to GitHub from the terminal. It replaces the previous static markdown generation with a fully interactive Textual-based TUI. The publisher supports auto-committing pending changes with AI-generated commit messages, lint validation, and direct publishing via the GitHub REST API. The goal is to streamline the PR workflow by integrating description editing, commit creation, and publishing into a single cohesive experience.

## 🛠️ Technical Changes

- **New `src/github_api.py`**: REST API client for creating GitHub Pull Requests, handling network errors and response parsing.
- **New `src/ui/pr_publish_app.py`**: Textual TUI for reviewing, editing, and publishing PRs. Supports save locally, auto-commit flow, and publish to GitHub with modals for commit confirmation and linter errors.
- **New `src/ui/pr_publish_help.py`**: Help screen for the publisher interface.
- **Updated `src/core.py`**: Added `has_uncommitted_changes()` and `execute_git_commit()` utility functions.
- **Updated `src/config.py`**: Added new configuration keys `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, and `GITPR_SKIP_LINT` with defaults.
- **Updated `src/main.py`**: Introduced `--base`, `--no-publish`, and `--no-edit` CLI options. Implemented the interactive flow, auto-commit logic, and direct publishing path. Modified docstring and help text.
- **Updated language files (`es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`)**: Added translations for all new PR publisher UI strings.
- **Added metrics export examples** (CSV and JSON) under `.gitpr/metrics/export/`.

## ⚠️ Impact/Warnings

- **Environment variables**: New optional settings `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, and `GITPR_SKIP_LINT` control publishing behavior. Ensure they are set if auto-commit or skipping lint is desired.
- **GitHub token**: Publishing requires a valid GitHub token. If the token is invalid or expired, the user will be prompted to re-authenticate within the TUI.
- **Lint integration**: By default, auto-commit runs the configured linter. If errors exist, the commit is aborted unless `--no-verify` is chosen. This may block publishing if the codebase has pre-existing lint issues.
- **Dependency**: The TUI depends on the `textual` library. Make sure it is installed.
- **File output**: The default behavior has changed from saving a local `.md` file to opening the interactive publisher. Use `--no-publish` to retain the old save-only behavior.