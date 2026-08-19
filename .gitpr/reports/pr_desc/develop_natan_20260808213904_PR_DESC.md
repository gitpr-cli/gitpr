# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive TUI for PR publishing with auto-commit
```

---

## 🎯 Summary

Introduces a complete interactive Terminal User Interface (TUI) for publishing Pull Requests directly to GitHub from the terminal. This includes auto-commit of uncommitted changes, integrated linter validation, optional file staging, and full i18n support for four new languages.

## 🛠️ Technical Changes

- New **TUI application** (`PrPublishApp`) with modals for commit confirmation, file staging, linter errors, error handling, and progress animation.
- New **CLI flags**: `--base` (target branch), `--no-publish` (save locally only), `--no-edit` (auto-commit + publish without TUI).
- New **github_api.py** module for REST API calls to create PRs on GitHub.
- New utility functions in **core.py**: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- **Configuration defaults** added for `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, and `PR_PUBLISH_LOG`.
- **i18n strings** added for Spanish, French, Brazilian Portuguese, and European Portuguese in `langs/*.json`.
- Default behavior changed: running `gitpr` without flags now opens the interactive TUI instead of only saving a local Markdown file.

## ⚠️ Impact/Warnings

- **Breaking change**: The default action now launches an interactive TUI. To restore previous behavior (save locally only), use the `--no-publish` flag.
- **Environment variables**: New optional vars (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, etc.) can override defaults.
- **GitHub token**: Required for publishing via the TUI or `--no-edit`. Token is validated interactively if missing.
- No database migrations or dependency changes.