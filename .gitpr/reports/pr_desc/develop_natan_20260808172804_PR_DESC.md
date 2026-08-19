# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publisher with TUI, direct mode, and auto-commit
```

---

## 🎯 Summary

Introduces a complete PR publishing flow to GitPR, allowing users to review, edit, and publish Pull Requests directly from the terminal. Supports an interactive TUI (Textual-based), a direct CLI mode with `--no-edit`, and a local save-only mode with `--no-publish`. The flow includes auto-commit of pending changes with lint validation, unstaged file handling, and GitHub API integration.

## 🛠️ Technical Changes

- **New modules:**
  - `src/github_api.py`: GitHub REST API client (create_pull_request).
  - `src/ui/pr_publish_app.py`: Textual TUI for the PR publisher.
  - `src/ui/pr_publish_help.py`: Help modal screen.
- **Core changes:**
  - Added helper functions in `core.py`: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
  - Extended `config.py` with new defaults: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`.
- **CLI enhancements (main.py):**
  - New flags: `--base`, `--no-publish`, `--no-edit`.
  - `--no-publish` skips the TUI and saves the PR locally.
  - `--no-edit` auto-commits pending changes (with lint) and publishes directly.
  - Unstaged files check: auto-stage or interactive selection before PR generation.
  - Integration with `github_api.py` for PR creation.
- **i18n:**
  - Added 80+ translations across `es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json` for all new UI strings.
- **Metrics:**
  - Added sample metrics export files in `.gitpr/metrics/export/` for tracking.

## ⚠️ Impact/Warnings

- **New environment variables:** The behavior is controlled by `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`. Ensure they are set as needed.
- **GitHub token:** PR publishing requires a valid GitHub token. Expired tokens will prompt re-authentication.
- **Dependencies:** The `requests` library is used by the new `github_api.py`; it is already a GitPR dependency, but if missing, the API calls will fail.
- **Metrics directory:** The `.gitpr/metrics/export/` folder now contains sample CSV/JSON files. They are informational and do not affect functionality.