# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and GitHub API
```

---

## 🎯 Summary

This change introduces a fully interactive terminal UI (TUI) that allows users to review, edit, and publish Pull Requests directly to GitHub via the REST API. Previously, the tool only generated a local markdown file. Now, after generating the PR description, the user can optionally auto-commit pending changes (with lint validation) and create the PR on GitHub in one seamless flow.

## 🛠️ Technical Changes

- Added new TUI screens (`PrPublishApp`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen`, `StageFilesScreen`) for a guided publication workflow
- Integrated `create_pull_request()` in `github_api.py` to interact with the GitHub REST API
- Extended `core.py` with `has_uncommitted_changes()`, `get_unstaged_files()`, `stage_files()`, and `execute_git_commit()` to support auto-commit and unstaged file handling
- Introduced `--no-publish`, `--no-edit`, and `--base` CLI flags to control publication behavior
- Added new configuration keys (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, etc.) for customizable automatic workflows
- Localised the entire PR publisher interface for Spanish, French, and Portuguese (BR/PT)
- Included example metrics exports to document infrastructure usage

## ⚠️ Impact/Warnings

- **New dependencies:** The publication flow now requires a valid GitHub token with repo scope; the TUI uses Textual for rendering
- **Environment variables:** Several new `.env` keys control automation (e.g., `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`); default behavior is still interactive
- **Backward compatibility:** The default CLI behavior now opens the interactive publisher after generating the PR; use `--no-publish` to revert to the old file-only output