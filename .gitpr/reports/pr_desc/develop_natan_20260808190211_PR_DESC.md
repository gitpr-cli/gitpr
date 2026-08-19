# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and lint integration
```

---

🎯 Summary

Introduces an interactive TUI (Textual) for reviewing, editing, and publishing Pull Requests directly to GitHub. Includes auto-commit of uncommitted changes with linter validation, support for `--no-publish` (save locally) and `--no-edit` (direct publish). Adds new configuration options for base branch, auto-commit, lint skipping, auto-staging, and telemetry logging. Localizes UI to Spanish, French, Brazilian Portuguese, and European Portuguese.

🛠️ Technical Changes

- New Textual app `PrPublishApp` with helper screens (CommitConfirm, StageFiles, CommitProgress, CommitMessage, LinterError, Error).
- Added `--base`, `--no-publish`, `--no-edit` CLI flags.
- New `src/github_api.py` module for GitHub REST API integration (`create_pull_request`).
- New helper functions in `core.py`: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- Extended language files (`es_es`, `fr_fr`, `pt_br`, `pt_pt`) with 90+ new translation keys.
- Added default configurations to `config.py` for PR publication behavior.

⚠️ Impact/Warnings

- Environment variables: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.
- New dependency on `requests` for GitHub API calls (ensure it's present).
- Requires a valid GitHub token for API publication.
- The TUI overwrites PR descriptions; review before publishing.