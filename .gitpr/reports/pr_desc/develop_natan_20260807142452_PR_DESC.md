# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and lint
```

---

## 🎯 Summary

This change introduces the ability to publish Pull Requests directly to GitHub from the CLI. A new interactive TUI (Textual) allows users to review, edit, and publish PRs. Additionally, a `--no-edit` mode automates commit generation (with linter validation) and PR publication without manual intervention. The feature includes environment variables for configuration (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`) and full i18n support (es, fr, pt-br, pt-pt).

## 🛠️ Technical Changes

- **New GitHub API client** (`src/github_api.py`): Implements `create_pull_request` using `requests`, with error message extraction and handling for connection/timeout.
- **New TUI application** (`src/ui/pr_publish_app.py`): Textual-based modal editor for PR title/body, with auto-commit flow (linter check, commit message generation, confirm dialogs) and direct publication.
- **New help screen** (`src/ui/pr_publish_help.py`): Instruction modal for the TUI.
- **CLI integration** (`src/main.py`):
  - New `--base`, `--no-publish`, `--no-edit` options.
  - Default behavior changed to open the interactive publisher.
  - Helper functions for auto-commit (`_run_auto_commit_cli`) and direct publish (`_publish_pr_directly`).
- **Core utilities** (`src/core.py`): Added `has_uncommitted_changes()` and `execute_git_commit()` to support auto-commit logic.
- **Configuration** (`src/config.py`): Added `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, and `GITPR_SKIP_LINT` with defaults.
- **Internationalization** (`langs/*.json`): ~60 new translation keys covering titles, status messages, errors, and UI elements.
- **Metrics export** (new CSV/JSON): Sample metrics dump for telemetry tracking.

## ⚠️ Impact/Warnings

- **Environment variables**: Introduces `PR_DEFAULT_BASE` (target branch), `GITPR_AUTO_COMMIT` (skip commit confirmation), and `GITPR_SKIP_LINT` (bypass linter). Ensure they are set appropriately for automated pipelines.
- **Dependency**: The TUI requires the `textual` library; ensure it is installed.
- **GitHub token**: The interactive flow re‑authenticates on 401 errors; users must have a valid token with repo scope.
- **Auto-commit**: When using `--no-edit`, uncommitted changes are auto-committed with an AI-generated message; review linter results to avoid unintended commits.