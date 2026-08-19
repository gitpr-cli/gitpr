# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publisher TUI with auto-commit and linter
```

---

## 🎯 Summary

Introduces an interactive terminal UI for reviewing, editing, and publishing Pull Requests directly to GitHub. The new `PrPublishApp` (Textual-based) allows users to review the generated PR title and body, handle unstaged files, auto-commit pending changes with linter validation, and create the PR via the GitHub API. New CLI flags `--base`, `--no-publish`, and `--no-edit` give control over the publication flow. All UI messages are localized for es, fr, pt-br, pt-pt.

## 🛠️ Technical Changes

- **`src/ui/pr_publish_app.py`**: Added the main TUI with modal screens for commit confirmation, unstaged file staging, linter error handling, editable commit message, and progress animation during commit/PR creation.
- **`src/github_api.py`**: New module to create GitHub PRs via REST API with comprehensive error handling.
- **`src/main.py`**: Extended CLI with `--base`, `--no-publish`, `--no-edit` flags. Implemented auto-commit flow (`_run_auto_commit_cli`) and direct PR publishing (`_publish_pr_directly`). Added unstaged file check and TUI launch logic.
- **`src/core.py`**: Added `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, and `execute_git_commit` for git operations needed by the TUI.
- **`src/config.py`**: Extended `DEFAULT_CONFIG` with new keys for PR base branch, auto-commit, skip lint, auto-stage, log controls.
- **Localization**: Added 90+ translation keys to `langs/es_es.json`, `langs/fr_fr.json`, `langs/pt_br.json`, and `langs/pt_pt.json` for all new UI strings.
- **Metrics**: Added sample CSV/JSON exports for internal tracking (`gitpr_metrics_2026-08-07.*`, `gitpr_metrics_2026-08-08.*`).

## ⚠️ Impact/Warnings

- **Default behavior change**: Running `gitpr` without flags now opens the interactive TUI instead of just saving the PR file locally. Use `--no-publish` to restore the previous behavior of only generating the description.
- **GitHub token required**: Publishing requires a valid GitHub personal access token (classic or fine-grained) with appropriate permissions. The TUI will prompt for one if missing or expired.
- **Linter integration**: Commits may be blocked if the linter detects errors (unless `--no-verify` is confirmed). The `GITPR_SKIP_LINT` env variable can bypass the check.
- **Environment variables**: New options available: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.