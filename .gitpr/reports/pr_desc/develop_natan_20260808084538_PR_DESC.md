# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publishing TUI with GitHub API and auto-commit
```

---

## 🎯 Summary
This PR introduces a new interactive PR publisher feature that allows users to review, edit, and publish Pull Requests directly to GitHub from the terminal, with optional auto-commit of pending changes and lint validation.

## 🛠️ Technical Changes
- Added new files: `src/github_api.py` (GitHub PR creation), `src/ui/pr_publish_app.py` (Textual TUI), `src/ui/pr_publish_help.py` (help modal), and metrics export files
- Updated `src/main.py` to add `--publish`, `--no-publish`, `--no-edit`, and `--base` CLI options, integrating the PR publisher flow
- Added `has_uncommitted_changes` and `execute_git_commit` functions to `src/core.py`
- Extended `src/config.py` with new default configuration keys for PR base branch, auto-commit, lint skipping, auto-stage, and log display
- Added translation entries in `langs/*.json` for all PR publisher-related strings in Spanish, French, and Portuguese

## ⚠️ Impact/Warnings
- Introduces new configuration environment variables: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`
- Requires `requests` library for GitHub API calls (ensure it's added to dependencies if not already present)
- The TUI depends on `Textual` framework; ensure compatible version is installed
- Existing PR generation behavior changes: the default flow now opens the TUI instead of only saving locally; use `--no-publish` to revert to old behavior