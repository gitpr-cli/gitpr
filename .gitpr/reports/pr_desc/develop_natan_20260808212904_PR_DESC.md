# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and API integration
```

---

## 🎯 Summary

Introduce a new interactive Terminal UI (TUI) flow for reviewing, editing, and publishing Pull Requests directly to GitHub via the REST API. This replaces the previous default behavior (which only saved a local `.md` file) with a full-featured publisher that supports auto-commit of uncommitted changes, staged/unstaged file management, linter integration, and direct API creation of PRs.

## 🛠️ Technical Changes

- **New `github_api.py` module**: Encapsulates GitHub PR creation with error extraction and connection/timeout handling.
- **New `pr_publish_app.py`**: Textual-based TUI with title/body editing, save-local (`F2`), publish-to-GitHub (`F3`) actions, commit confirmation, linter error modal, unstaged file staging modal, and progress animation.
- **New `pr_publish_help.py`**: Help modal for TUI keybindings.
- **Extended `core.py`**: Added `has_uncommitted_changes()`, `get_unstaged_files()`, `stage_files()`, and `execute_git_commit()` to support the auto-commit flow.
- **Updated `main.py`**: 
  - Default behavior now opens the interactive publisher (TUI) instead of just saving a local file.
  - Added `--publish` flag (implicit default), `--no-publish` (save locally only), `--no-edit` (auto-commit + direct publish).
  - Introduced unstaged file check before PR generation with auto-staging or interactive selection.
  - Integrated `_run_auto_commit_cli()` for `--no-edit` mode and `_publish_pr_directly()` for direct API publishing.
- **Expanded i18n**: Added +90 translation keys across `es_es`, `fr_fr`, `pt_br`, `pt_pt` for all new UI strings.
- **New config defaults**: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.
- **Sample metrics files** (`gitpr_metrics_2026-08-07.csv/.json`, `gitpr_metrics_2026-08-08.csv/.json`) added for testing.

## ⚠️ Impact/Warnings

- **Default behavior changed**: Running `gitpr` without flags now opens the interactive publisher instead of only saving a local file. Use `--no-publish` for the old behavior.
- **New environment variables**: Review the new config keys in `~/.gitpr/.env` to customize auto-commit, lint skipping, auto-staging, and logging behavior.
- **GitHub token required**: The publisher requires a valid GitHub token (stored via `gitpr --install`). Expired tokens trigger a re-authentication loop within the TUI.
- **Linter integration**: Lint errors block commit by default; users can override with `--no-verify` in the TUI or skip lint entirely via `GITPR_SKIP_LINT=true`.
- **Auto-commit feature**: When enabled (`GITPR_AUTO_COMMIT=true` or `--no-edit`), pending changes are committed automatically with an AI-generated message after lint checks.
- **Unstaged file handling**: By default, the app prompts to stage untracked/unstaged files. Set `GITPR_SKIP_UNSTAGED_CHECK=true` to bypass this step.
- **Dependencies**: No new external dependencies introduced; relies on existing `requests` and `textual` packages.
- **Localization**: Extensive new translations added for 4 languages; all UI strings are now fully localized.