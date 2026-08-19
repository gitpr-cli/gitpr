# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and lint validation
```

---

## 🎯 Summary

Introduces a rich terminal UI (TUI) for reviewing, editing, and publishing Pull Requests directly to GitHub. Alongside the interactive publisher, the flow now auto-commits pending changes and integrates linter validation, streamlining the entire PR workflow.

## 🛠️ Technical Changes

- Added `src/github_api.py` to communicate with the GitHub REST API (create PR, handle errors).
- Added `src/ui/pr_publish_app.py` implementing the TUI with Textual, supporting commit confirmation, message editing, linter error handling, and PR submission.
- Added `src/ui/pr_publish_help.py` for contextual help modal.
- Extended `src/core.py` with helpers: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- Updated `src/config.py` with new defaults (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, etc.).
- Integrated unstaged file detection and staging flow before PR generation in `src/main.py`.
- Introduced CLI options `--base`, `--no-publish`, `--no-edit`; updated help and documentation.
- Added full localizations (es_es, fr_fr, pt_br, pt_pt) for every new interface string.
- Created metrics files for PR publication events.

## ⚠️ Impact/Warnings

- New environment variables: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`. Review their defaults.
- GitHub token is required for API calls; expired tokens will prompt for re-authentication.
- Default behaviour now opens the TUI; use `--no-publish` to skip it and save locally, or `--no-edit` for direct headless publication with auto-commit.
- Linter integration depends on existing linter configuration; first-time runs may show errors if not set up.
- Requires internet connectivity for PR creation; fallback to local save is automatic when offline.