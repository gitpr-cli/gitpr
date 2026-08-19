# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publishing with TUI and auto-commit
```

---

## 🎯 Summary

Introduce a new interactive Terminal User Interface (TUI) for publishing Pull Requests directly to GitHub via API. This feature supports auto-committing uncommitted changes, linter validation, file staging, and provides a full workflow for reviewing and editing PR titles and descriptions before publication. Added comprehensive localization for UI strings in Spanish, French, Brazilian Portuguese, and European Portuguese. Added new environment configuration options to customize default base branch, auto-commit, skip lint, auto-stage, and show logs.

## 🛠️ Technical Changes

- Added `src/ui/pr_publish_app.py`: Main TUI app with modals for commit confirmation, file staging, commit progress, message editing, and linter errors.
- Added `src/ui/pr_publish_help.py`: Help modal for PR publisher.
- Added `src/github_api.py`: REST API integration for creating GitHub Pull Requests.
- Updated `src/main.py`: Integrated --publish, --no-publish, --no-edit CLI flags and auto-commit logic.
- Updated `src/core.py`: Added helper functions `has_uncommitted_changes` and `execute_git_commit`.
- Updated `src/config.py`: Added `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS` default settings.
- Added localization keys for UI strings across four language files.
- Added example metrics export files.

## ⚠️ Impact/Warnings

- New dependency: requires `requests` library for GitHub API calls.
- New environment variables: PR_DEFAULT_BASE, GITPR_AUTO_COMMIT, GITPR_SKIP_LINT, GITPR_AUTO_STAGE, GITPR_SHOW_LOGS - may affect existing workflows if not set.
- The default behavior of the CLI now opens the TUI publisher; users who relied on the previous file-only generation may need to use `--no-publish` flag.
- The new feature introduces potential security implications with GitHub tokens; ensure tokens are stored securely.
- No database changes, but new files are created in `.gitpr/metrics/export/` (can be ignored in .gitignore).