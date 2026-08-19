# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publishing to GitHub via TUI and auto-commit
```

---

## 🎯 Summary

This change transforms GitPR from a local PR description generator into a full-circle tool that also publishes pull requests directly to GitHub. A new interactive TUI lets users review, edit, and publish PRs; an auto-commit flow handles staging, linting, AI-generated commit messages, and the commit itself. New CLI flags (`--no-publish`, `--no-edit`) control the workflow, and comprehensive translations and environment variables support a global audience. The goal is to eliminate the manual step of copying a local description into GitHub's web interface.

## 🛠️ Technical Changes

- **New GitHub API module** (`src/github_api.py`): Implements `create_pull_request()` with HTTP error handling (401, 422, timeout, connection errors) and token management.
- **Interactive TUI** (`src/ui/pr_publish_app.py`): A Textual app that displays title, body, and target branch; provides F2 (save locally) and F3 (auto-commit + publish) actions. Includes modal screens for commit confirmation, file staging, linter errors, progress animation, and commit message editing.
- **Help screen** (`src/ui/pr_publish_help.py`): A modal with keyboard shortcut reference and links to documentation.
- **CLI extensions** in `src/main.py`:
  - New flags: `--no-publish` (save locally, skip TUI), `--no-edit` (auto-commit + direct publish), `--base` (override target branch).
  - Default behavior changed: now opens the TUI after generating the PR description.
  - `_run_auto_commit_cli()`: Orchestrates auto-commit flow (check changes → linter → AI message → commit) for `--no-edit` mode.
  - `_publish_pr_directly()`: Creates the PR via GitHub API without the TUI.
- **Core utilities** (`src/core.py`): `has_uncommitted_changes()` and `execute_git_commit()` to support auto-commit.
- **Configuration** (`src/config.py`): New environment variable keys: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`.
- **Internationalization**: Added 75+ translation entries across `es_es`, `fr_fr`, `pt_br`, `pt_pt` for all new UI strings.
- **Metrics export**: Example CSV/JSON files for PR publishing events.

## ⚠️ Impact/Warnings

- **Behavioral change**: Running `gitpr` without arguments now opens a TUI instead of only saving a local file. Existing scripts that parse the output should add `--no-publish` to restore the old behavior.
- **Network dependency**: PR publishing via API requires internet access and a valid GitHub token (with `repo` scope). Offline usage still works for local save (`--no-publish`).
- **Auto-commit risks**: The `--no-edit` mode will automatically generate a commit message, stage changes (if enabled), execute a commit, and push it before creating the PR. Ensure you have configured `GITPR_AUTO_COMMIT` and `GITPR_SKIP_LINT` according to your workflow.
- **Environment variables**: New variables must be documented; `PR_DEFAULT_BASE` overrides the base branch per project; `GITPR_AUTO_STAGE` controls whether the auto-commit stages files automatically.
- **Token expiration**: The TUI and CLI handle 401 errors by prompting for re-authentication (or exiting with a message in `--no-edit`).