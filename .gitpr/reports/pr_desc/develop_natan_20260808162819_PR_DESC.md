# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and lint
```

---

## 🎯 Summary

Running `gitpr` without flags now opens an interactive TUI (Terminal User Interface) where users can review, edit, and publish Pull Requests directly to GitHub. This PR introduces a complete publication workflow with optional auto-commit, linter validation, unstaged file staging, and error recovery via re-authentication.

## 🛠️ Technical Changes
- Added `src/ui/pr_publish_app.py` with the main `PrPublishApp` TUI, modal screens for commit confirmation, file staging, linter errors, and animated progress.
- Added `src/github_api.py` to create PRs via GitHub REST API with connection/timeout handling and error message extraction.
- Extended `src/core.py` with helper functions: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- Updated `src/main.py` to support new flags (`--no-publish`, `--no-edit`, `--base`) and to trigger the publication flow, including auto-commit logic and direct publish mode.
- Added new configuration options in `src/config.py`: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `GITPR_SHOW_LOGS`.
- Added complete i18n translations for the new UI and workflow strings in ES, FR, PT_BR, PT_PT.
- Added sample metric export files (CSV and JSON) under `.gitpr/metrics/export/`.

## ⚠️ Impact/Warnings
- **Default behavior changes**: `gitpr` now launches an interactive TUI for PR publishing. Use `gitpr --no-publish` to generate the PR file only, or `gitpr --no-edit` for a headless auto-commit + publish.
- **GitHub token required**: The publication flow requires a valid GitHub token with repo scope. Token can be configured via `GITPR_GITHUB_TOKEN` env var or will be prompted.
- **New dependencies**: The TUI relies on the `textual` library (already present) and introduces `requests` for GitHub API calls (should already be a dependency).
- **Linter integration**: If not skipped (`GITPR_SKIP_LINT`), the linter runs automatically before commit; errors can be bypassed with `--no-verify`.
- **Auto-staging**: Unstaged files are handled based on `GITPR_AUTO_STAGE` (auto-add) or via interactive selection unless `GITPR_SKIP_UNSTAGED_CHECK` is set.