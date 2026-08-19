# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publication to GitHub with TUI and auto-commit
```

---

## 🎯 Summary

This release introduces a native interactive pull request publication flow to GitHub. Users can now generate a PR description, review/edit it in a Textual TUI, handle unstaged files, have linter checks before auto-committing, and publish the PR directly via the GitHub API—all from the terminal. Two new flags control bypass: `--no-publish` (save locally only) and `--no-edit` (auto-commit + publish without TUI).

## 🛠️ Technical Changes

- **New GitHub API module** (`src/github_api.py`): Handles PR creation via REST API with error extraction, connection/timeout handling, and i18n messages.
- **Interactive TUI app** (`src/ui/pr_publish_app.py`): Full Textual interface with title, body editing, save local, publish, help screen, and modals for commit confirmation, file staging, progress animation, message editing, linter errors, and general errors.
- **Help screen** (`src/ui/pr_publish_help.py`): Displays keyboard shortcuts and documentation link.
- **Core utilities additions** (`src/core.py`): Functions `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit` for auto-commit and staging workflows.
- **Main CLI enhancements** (`src/main.py`):
  - Added `--base`, `--no-publish`, `--no-edit` flags.
  - Default mode now opens the TUI publisher after PR generation.
  - Auto-commit flow for `--no-edit` with lint validation, AI-generated commit message, and optional --no-verify.
  - Unstaged files detection with auto-staging or interactive selection.
  - Updated help map and banner text.
- **Configuration** (`src/config.py`): New defaults: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.
- **Localization**: ~90 new strings added for Spanish, French, Brazilian Portuguese, and European Portuguese covering all new UI messages.
- **Metrics export files** added (sample CSVs and JSONs) for telemetry.

## ⚠️ Impact/Warnings

- **Default behavior change**: Running `gitpr` without flags now opens the interactive TUI publisher. To skip, use `--no-publish` (save locally) or `--no-edit` (auto-publish).
- **Token requirement**: Publishing requires a valid GitHub personal access token. The tool will prompt for one if not configured.
- **New dependencies**: The `requests` library was already used; no new external dependencies.
- **Environment variables**: Several new variables introduced to control auto-commit, lint, staging, and logging behavior (see `src/config.py`).
- **Linter integration**: If a linter is configured, it will run before auto-commit. Errors block the commit unless `--no-verify` is chosen.
- **File selection modal**: When unstaged files exist, an interactive selection appears (can be bypassed with `GITPR_AUTO_STAGE=true` or `GITPR_SKIP_UNSTAGED_CHECK=true`).