# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit
```

---

## 🎯 Summary

This feature adds interactive Pull Request publishing directly to GitHub from the GitPR CLI. Users can now generate a PR description, review and edit it in a Textual-based terminal UI, optionally auto-commit pending changes (with linter validation), and publish the PR via GitHub API in a single workflow. This eliminates the need for manual PR creation on the web interface, improving developer efficiency.

## 🛠️ Technical Changes

- Introduced CLI flags `--base`, `--no-publish`, `--no-edit` to control PR publication behavior.
- Added `PrPublishApp` (Textual TUI) for interactive editing and publishing of PRs.
- Integrated GitHub REST API via new `github_api.py` module for PR creation.
- Implemented auto-commit logic (`_run_auto_commit_cli`) with lint validation and user confirmation dialogs.
- Added helpers in `core.py` for managing unstaged files, checking uncommitted changes, and executing commits.
- Added new configuration keys (`GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, etc.) to customize auto-commit behavior.
- Extended localization files (ES, FR, PT) with translations for all new UI strings.
- Added metrics export files for tracking PR publication events.

## ⚠️ Impact/Warnings

- **Breaking change** in default workflow: running `gitpr` without flags now opens the interactive TUI instead of just generating a PR file. Use `--no-publish` to revert to the old file-only behavior or `--no-edit` for headless publishing.
- Requires a valid GitHub token (`gitpr` will prompt via TUI if missing).
- Auto-commit feature may modify the working tree; ensure changes are intended to be committed before proceeding.
- The Textual-based UI needs a modern terminal; older or non-interactive environments may require `--no-edit`.
- New optional dependencies: Textual and its sub-dependencies.
- New configuration options in `~/.gitpr/config.yml` should be reviewed and adjusted as needed.