# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publisher TUI and auto-commit to GitHub via API
```

---

## 🎯 Summary

Introduces a new Pull Request publication workflow that enables users to review, edit, and publish PRs directly to GitHub through an interactive TUI or via CLI flags. Supports auto-committing uncommitted changes, lint validation, unstaged file handling, and AI-generated commit messages—streamlining the entire PR creation process without leaving the terminal.

## 🛠️ Technical Changes

- Added `src/github_api.py` module to create GitHub Pull Requests via REST API
- Implemented interactive TUI (`src/ui/pr_publish_app.py`) with PR editing, local save, and direct publish actions
- Introduced CLI flags `--no-publish` (save locally) and `--no-edit` (auto-commit + publish)
- Integrated auto-commit flow with linter validation and unstaged file staging UI
- Extended `src/core.py` with helper functions: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`
- Updated `src/config.py` with new PR-related configuration options (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, etc.)
- Added comprehensive i18n translations (ES, FR, PT-BR, PT-PT) for new UI strings
- Added local metrics export files (`gitpr_metrics_*.csv` and `.json`) for telemetry tracking

## ⚠️ Impact/Warnings

- Requires a valid GitHub token configured for direct API publishing; token expiration triggers re-authentication flow
- New environment variables introduced: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`
- Linter errors may block automatic commits unless `--no-verify` is explicitly selected or `GITPR_SKIP_LINT` is set
- Generated metrics files in `.gitpr/metrics/export/` are auto-created; ensure they are excluded from shared repositories if sensitive
- The new workflow changes default `gitpr` behavior: it now opens the interactive TUI instead of just generating a PR description file

close #90