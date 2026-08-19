# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publisher TUI with auto-commit and GitHub API integration
```

---

## 🎯 Summary

This PR introduces a full Pull Request publishing workflow to GitPR. Users can now review, edit, and publish PRs directly to GitHub without leaving the terminal. The feature includes an interactive Textual-based TUI, an auto-commit mode that lints and commits uncommitted changes, and direct API publication via the `--no-edit` flag.

## 🛠️ Technical Changes

- Added `src/github_api.py` module for GitHub REST API interactions (create PR, error handling).
- Added `src/ui/pr_publish_app.py` containing the `PrPublishApp` TUI with forms, progress screens, and modal dialogs for unstaged file staging, commit confirmation, linter errors, and publication errors.
- Added `src/ui/pr_publish_help.py` for the in-app help modal.
- Extended `src/main.py` with new CLI options (`--publish`, `--base`, `--no-publish`, `--no-edit`) and the complete PR publisher orchestration logic.
- Extended `src/core.py` with helper functions: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- Extended `src/config.py` with new default configuration options for auto-commit, skip lint, auto-stage, show logs, skip unstaged check, and PR publish log.
- Added comprehensive translations for all new UI strings in `langs/es_es.json`, `langs/fr_fr.json`, `langs/pt_br.json`, `langs/pt_pt.json`.
- Added initial metrics export files for telemetry (`gitpr_metrics_*.csv` and `*.json`).

## ⚠️ Impact/Warnings

- **Environment Variables**: New configuration variables are introduced:
  - `PR_DEFAULT_BASE` – set default base branch for PRs.
  - `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG` – control auto-commit and linting behavior.
- **Dependencies**: The `requests` library is used for GitHub API calls (assumed already present; no new dependency listed).
- **GitHub Token**: Requires a valid GitHub token for API access; the token is validated interactively or via environment variable.
- **Workflow Change**: The default PR generation now opens the TUI publisher. Use `--no-publish` to only save locally as before. The old behavior can be preserved by setting appropriate environment variables.