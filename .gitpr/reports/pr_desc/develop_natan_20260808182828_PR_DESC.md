# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and GitHub API integration
```

---

## 🎯 Summary

This PR introduces an interactive Pull Request publisher that streamlines the entire PR creation workflow. Users can now review, edit, and publish PRs directly from the terminal, with optional auto-commit, lint validation, and GitHub API integration. The feature is accessible via new CLI flags (`--base`, `--no-publish`, `--no-edit`) and defaults to an interactive TUI when no special flags are provided.

## 🛠️ Technical Changes

- Added a Textual-based TUI (`src/ui/pr_publish_app.py`) with modals for unstaged file staging, commit confirmation, progress animation, commit message editing, linter errors, and generic error handling.
- Implemented GitHub API client (`src/github_api.py`) to create pull requests programmatically.
- Extended `src/core.py` with helper functions: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- Updated `src/main.py`:
  - New CLI options: `--base` (target branch), `--no-publish` (save locally only), `--no-edit` (auto-commit + publish).
  - Integrated unstaged file check, PR generation, and TUI/direct publish flows.
  - Added `_run_auto_commit_cli` and `_publish_pr_directly` for `--no-edit` mode.
- New configuration defaults (`src/config.py`) for environment variables like `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, etc.
- Localization: updated `langs/es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json` with all new UI strings.
- Added local metrics export files (`.gitpr/metrics/export/gitpr_metrics_*.csv|json`) for command usage tracking.
- Updated help text and contextual help to include the new publish-related flags.

## ⚠️ Impact/Warnings

- No breaking changes to existing functionality; all previous commands remain unchanged.
- Users must have a valid GitHub token configured for publishing via API.
- New environment variables allow customizing behavior (auto-commit, lint skipping, etc.). Please review the documentation for details.
- The interactive TUI requires a terminal that supports Textual (modern terminals).