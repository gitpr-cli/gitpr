# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and TUI
```

---

## 🎯 Summary

This PR introduces a full-featured interactive Pull Request publisher (TUI) to GitPR, enabling users to review, edit, auto-commit pending changes (with lint validation), and publish PRs directly to GitHub without leaving the terminal. It also adds new CLI flags (`--no-publish`, `--no-edit`, `--base`) and environment variables for customisation.

## 🛠️ Technical Changes

- Added `StageFilesApp` modal to select unstaged files before PR generation.
- Implemented `PrPublishApp` (Textual TUI) with:
  - Editable title and body fields.
  - Auto‑commit flow (lint, commit message generation, commit execution).
  - Direct PR creation via GitHub REST API.
  - Modal screens for commit confirmation, progress, message editing, and error handling.
- New `github_api.py` module with `create_pull_request()` (handles auth, error extraction, timeouts).
- Extended `core.py` with helpers: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- Updated `config.py` with new settings: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.
- Extended `main.py` to integrate the publisher flow, add `--base`, `--no-publish`, `--no-edit` flags, and `_run_auto_commit_cli` helper.
- Added full translations (es_es, fr_fr, pt_br, pt_pt) for all new UI strings.
- Included sample metrics export files (CSV/JSON) for testing.

## ⚠️ Impact/Warnings

- **Default behaviour change**: Running `gitpr` with no flags now opens the interactive PR publisher instead of only saving an MD file. Existing scripts that rely on the old behaviour should use the `--no-publish` flag. Backward compatibility is preserved with `--no-publish`.
- **New environment variables** (all optional, documented in the code):
  - `PR_DEFAULT_BASE`: default target branch for the PR.
  - `GITPR_AUTO_COMMIT`: skips commit confirmation when set to `true`.
  - `GITPR_SKIP_LINT`: bypasses lint checking before commit.
  - `GITPR_AUTO_STAGE`: automatically stages all unstaged files (no prompt).
  - `GITPR_SKIP_UNSTAGED_CHECK`: disables the unstaged files check entirely.
  - `PR_PUBLISH_LOG`: enables/disables the PR publish log.
- **New CLI flags**: `--base`, `--no-publish`, `--no-edit`.
- No database or dependency changes (uses existing `requests` library).
- Ensure a valid GitHub token is set (via `gitpr` interactive auth) before using `--no-edit` or the TUI.