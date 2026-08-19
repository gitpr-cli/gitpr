# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publisher TUI with auto-commit and GitHub integration
```

---

## 🎯 Summary

Implements a complete Pull Request publishing pipeline directly from the terminal. Users can now review and edit the generated PR title/body in an interactive TUI before publishing to GitHub, with optional auto-commit of pending changes (including lint validation) and handling of unstaged files. This replaces the previous behavior of only saving a local markdown file, greatly streamlining the PR workflow.

## 🛠️ Technical Changes

- Added `src/github_api.py` – REST API wrapper to create pull requests on GitHub.
- Added `src/ui/pr_publish_app.py` and `src/ui/pr_publish_help.py` – Textual-based TUI for interactive PR editing and submission, including progress screens and modals for commit confirmation, linter errors, and file staging.
- Extended `src/core.py` with git helper functions: `has_uncommitted_changes()`, `get_unstaged_files()`, `stage_files()`, `execute_git_commit()`.
- Integrated PR publishing flow into `src/main.py`: new `--publish`, `--no-edit`, and `--base` options; auto-commit with AI-generated messages and optional linting; handling of unstaged files before PR generation.
- Added configuration defaults for new environment variables (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`) in `src/config.py`.
- Updated localization files (`es_es`, `fr_fr`, `pt_br`, `pt_pt`) with 90+ new UI strings covering PR publisher dialogs and actions.
- Added sample metrics export files for testing.

## ⚠️ Impact/Warnings

- **Default behavior changed**: Running `gitpr` without flags now opens the interactive PR publisher TUI instead of only saving a local file. Use `--no-publish` to restore the previous behavior.
- **New environment variables**: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG` affect commit and staging automation. Review your configuration if you previously relied on implicit defaults.
- **Network requirement**: Publishing a PR requires a valid GitHub token and internet connectivity.
- **Dependencies**: No new Python packages beyond those already in use (Textual, requests).