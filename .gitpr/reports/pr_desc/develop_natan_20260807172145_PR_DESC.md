# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with GitHub API integration
```

---

## 🎯 Summary
This PR introduces a complete Pull Request publication workflow directly from GitPR to GitHub, replacing the previous local-only flow. It adds an interactive TUI for reviewing and editing PR details, automatic commit handling, linter validation, and GitHub API integration.

## 🛠️ Technical Changes
- New `src/github_api.py` module to create PRs via GitHub REST API.
- Updated `main.py` with new CLI flags: `--base`, `--no-publish`, `--no-edit` to control publishing behavior.
- Introduced `PrPublishApp` TUI (Textual) in `src/ui/pr_publish_app.py` with modals for commit confirmation, file staging, linter errors, progress, and commit message editing.
- Added `PrPublishHelpScreen` for TUI help.
- Localization strings for all supported languages (pt_BR, es_ES, fr_FR, pt_PT) covering the new interface messages.
- New config defaults in `config.py` for `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`.
- Helper functions in `core.py`: `has_uncommitted_changes()` and `execute_git_commit()`.
- Metrics export files added to `.gitpr/metrics/export/` (sample data).

## ⚠️ Impact/Warnings
- Environment variables `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS` are now read from config; ensure they are set if needed.
- Requires valid GitHub token for publishing (configured via GitPR's authentication flow).
- No database changes, but new dependencies (e.g., `requests` must be installed; likely already present).
- The default behavior changed: running without flags now opens the TUI instead of just saving locally (unless `--no-publish` is used).