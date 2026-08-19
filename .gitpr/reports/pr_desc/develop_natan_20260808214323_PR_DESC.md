# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with GitHub API
```

---

## 🎯 Summary

This pull request introduces a complete interactive Pull Request publishing workflow, enabling users to review, edit, auto-commit pending changes (with optional linter validation), and publish directly to GitHub via the API—all from a rich Textual-based TUI. It supports multiple languages and configurable options like `--base`, `--no-publish`, and `--no-edit` for streamlined automation.

## 🛠️ Technical Changes

- Added `src/github_api.py` module to create pull requests via GitHub REST API (handles auth, error extraction, timeout).
- Added `src/ui/pr_publish_app.py` with a full TUI (`PrPublishApp`) for editing title/body, saving locally, and publishing. Includes sub-screens for commit confirmation, file staging, progress animation, commit message editing, and linter error handling.
- Added `src/ui/pr_publish_help.py` with a help modal for the publisher interface.
- Extended `src/core.py` with helper functions: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- Updated `src/main.py` to integrate the PR publisher: added CLI options `--base`, `--no-publish`, `--no-edit`. Default behavior now opens the TUI; `--no-publish` saves locally; `--no-edit` does auto‑commit + direct API publish.
- Added new configuration variables in `src/config.py`: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.
- Updated language files (`es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`) with all new UI strings for the publisher (over 90 new translations).
- Added sample metric export files for 2026-08-07 and 2026-08-08 (CSV/JSON) to `.gitpr/metrics/export/` (likely for testing/documentation).

## ⚠️ Impact/Warnings

- **New environment variables** have been introduced (see `src/config.py`). Ensure any existing `.env` files are updated if default behavior is not desired.
- The `--no-edit` flag now triggers an auto‑commit (with AI‑generated message and optional linter) **before** publishing—be cautious when using it on branches with uncommitted work.
- GitHub token validation is mandatory for any publishing action; expired tokens will prompt a re‑auth loop inside the TUI.
- The TUI requires a terminal that supports rich text; non‑TTY environments may fall back to the `--no‑publish` or `--no‑edit` modes.
- Metric export files are sample data and may be removed in the future; they are not required for operation.