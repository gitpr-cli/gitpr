# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publisher TUI and direct GitHub publishing
```

---

## 🎯 Summary

This change introduces a new feature that enables users to publish Pull Requests directly from GitPR to GitHub. It provides an interactive terminal UI (TUI) for reviewing, editing, and publishing PRs, as well as a direct publish mode via the `--no-edit` flag. The workflow includes automatic commit generation, lint validation, and file staging. The feature aims to streamline the PR creation process, reducing the need to switch between tools and manual steps.

## 🛠️ Technical Changes
- Added `src/github_api.py` with `create_pull_request` function using GitHub REST API
- Added `src/ui/pr_publish_app.py` with a Textual-based TUI for PR publishing (includes modal screens for commit confirm, file staging, progress, message editing, and linter errors)
- Added `src/ui/pr_publish_help.py` for the TUI help modal
- Extended `src/core.py` with `has_uncommitted_changes()` and `execute_git_commit()`
- Updated `src/config.py` with new defaults: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`
- Enhanced `src/main.py` with new CLI options `--base`, `--no-publish`, `--no-edit`, and integrated the publishing logic
- Added comprehensive translations for all new UI strings in `es_es`, `fr_fr`, `pt_br`, and `pt_pt` JSON files
- Included sample metrics export files for demonstration

## ⚠️ Impact/Warnings
- Requires a valid GitHub personal access token configured for API access
- Dependencies `requests` and `textual` must be present; ensure they are installed via the project's requirements
- The new auto-commit and publishing behavior is opt-in; using `--no-edit` will bypass the interactive TUI
- Lint checks are now integrated into the commit workflow; set `GITPR_SKIP_LINT=true` to disable if needed
- No database or environment variable changes beyond the new configuration defaults