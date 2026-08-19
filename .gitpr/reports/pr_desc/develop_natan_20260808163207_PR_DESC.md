# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publishing TUI with auto-commit, lint, and GitHub API integration
```

---

## 🎯 Summary

This feature introduces a complete Pull Request publishing flow, enabling users to review, edit, and submit a PR directly to GitHub from the terminal. It wraps the entire process—from generating a PR description to handling unstaged files, linting, committing, and API interaction—into a single, guided interactive TUI. The goal is to streamline the developer workflow and reduce manual, error-prone steps between code changes and PR creation.

## 🛠️ Technical Changes

- Added `src/github_api.py` to handle PR creation via the GitHub REST API, including network error handling and token-based authentication.
- Added `src/ui/pr_publish_app.py` with a Textual TUI (`PrPublishApp`) for editing PR title/body, saving locally, and publishing. Includes modals for commit confirmation, file staging, lint errors, commit message edition, and an animated progress bar.
- Added `src/ui/pr_publish_help.py` with a help modal explaining TUI shortcuts.
- Extended `src/main.py` with `--no-publish`, `--no-edit`, and `--base` CLI options; default behavior now opens the PR publisher TUI. Implemented auto-commit flow with linter validation and AI-generated commit messages. Integrated unstaged-file staging logic.
- Introduced new CLI helper functions: `_run_auto_commit_cli`, `_get_github_token_for_publish`, and `_publish_pr_directly`.
- Expanded `src/core.py` with `has_uncommitted_changes()`, `get_unstaged_files()`, `stage_files()`, and `execute_git_commit()` to support pre-commit checks and file staging.
- Updated `src/config.py` to include new defaults: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`.
- Updated all language files (es_es, fr_fr, pt_br, pt_pt) with translations for new UI strings.
- Added example metrics CSV/JSON exports under `.gitpr/metrics/export/`.

## ⚠️ Impact/Warnings

- **Environment variables**: New variables `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK` control automation; ensure they are set appropriately for CI environments.
- **Dependencies**: The PR publishing feature relies on `requests` and `textual`. Ensure these are present in the environment (already likely dependencies).
- **GitHub token**: Publishing requires a valid token stored or interactively provided. Token expiration is handled gracefully with re-authentication prompts inside the TUI.
- **Default behavior change**: Running `gitpr` without any flags now opens the interactive PR publisher instead of only generating a markdown file. Users expecting the old behavior should use `--no-publish` to skip the TUI and only produce a local `.md` file.