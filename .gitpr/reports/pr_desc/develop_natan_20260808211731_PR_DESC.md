# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with staging, lint, and GitHub API
```

---

## 🎯 Summary

Introduces a complete interactive Pull Request publication workflow, enabling users to review, edit, and publish PRs directly from the terminal. The flow handles unstaged file staging, lint validation, AI-generated commit messages, and direct GitHub API integration. This eliminates the need to manually switch between tools and ensures a consistent, step-by-step PR creation process.

## 🛠️ Technical Changes

- Added `StageFilesApp` and `PrPublishApp` TUI (Textual) for file staging and PR editing/publishing.
- Implemented automatic commit generation with linter checking (`CommitProgressScreen`, `LinterErrorScreen`).
- Integrated GitHub REST API via new `src/github_api.py` module, supporting token validation and PR creation.
- Extended CLI with `--no-publish`, `--no-edit`, `--base` options for flexible automation.
- Added configuration keys (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, etc.) for behavior customization.
- Updated `src/core.py` with git helpers (`has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`).
- Expanded localization files (es_es, fr_fr, pt_br, pt_pt) with 90+ new strings for the PR publisher.
- Added metric export files and PR publish logging for diagnostics.

## ⚠️ Impact/Warnings

- **Dependencies**: Requires Textual library (if not already present).
- **Environment**: New `.env` variables introduced; existing setups may need adjustment.
- **Behavior change**: Default `gitpr` execution now opens the interactive publisher instead of just saving a file. Use `--no-publish` to restore previous behavior.
- **GitHub token**: Must be configured for API publication; re-authentication flow is built into the TUI.