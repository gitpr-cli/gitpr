# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and GitHub publishing
```

---

## 🎯 Summary

This PR introduces a brand-new interactive Pull Request publishing feature. Instead of only generating a Markdown file, `gitpr` now opens a terminal-based TUI (via Textual) where users can review, edit, and publish the PR directly to GitHub. The flow includes:
- **Unstaged file handling** – prompts to stage or skip untracked/unstaged files before generation.
- **Auto-commit** – detects uncommitted changes, runs the linter, generates an AI-powered commit message, and commits before publishing.
- **Direct GitHub publishing** – creates the PR via the GitHub REST API, supporting `--no-edit` for non-interactive (CI/CD) scenarios and `--no-publish` for local-only saves.
- **Full localization** – all new UI strings are translated (ES, FR, PT‑BR, PT‑PT).

The feature is controlled by new command-line flags (`--base`, `--no-edit`, `--no-publish`) and environment variables (e.g., `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`).

## 🛠️ Technical Changes

- **`src/main.py`** – integrated the publishing flow: unstaged‑file check, `--base`/`--no-publish`/`--no-edit` handling, and call into the TUI or direct publish logic.
- **`src/ui/pr_publish_app.py`** – new Textual TUI application, including screens for commit confirmation, file staging, progress animation, commit message editing, linter errors, and error handling.
- **`src/ui/pr_publish_help.py`** – help modal for the publisher interface.
- **`src/github_api.py`** – new module with `create_pull_request()` function (REST API, token auth, error extraction).
- **`src/core.py`** – added `has_uncommitted_changes()`, `get_unstaged_files()`, `stage_files()`, and `execute_git_commit()` to support the auto‑commit pipeline.
- **`src/config.py`** – new configuration keys: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`.
- **`langs/*.json`** – added over 90 translated strings for the publisher UI in Spanish, French, Brazilian Portuguese, and European Portuguese.
- **Metric exports** – added sample CSV/JSON files under `.gitpr/metrics/export/` (likely test artifacts).

## ⚠️ Impact/Warnings

- **New dependency**: The TUI uses the [Textual](https://textual.textualize.io/) library – ensure it’s installed (`pip install textual`).
- **GitHub token**: Publishing requires a valid token with `repo` scope; token validation and re‑authentication are built into the TUI.
- **Environment variables**: Six new variables control auto‑commit behaviour, lint skipping, and file staging – check your `~/.gitpr/.env` or export them as needed.
- **Default behaviour change**: Running `gitpr` without options now opens the interactive publisher instead of just saving a file; use `--no-publish` to restore the previous behaviour.