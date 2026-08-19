# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and TUI
```

---

## 🎯 Summary
This PR introduces a fully interactive Terminal User Interface (TUI) for reviewing, editing, and publishing Pull Requests directly to GitHub. It adds automatic staging of unstaged files, auto-commit with linter validation, and GitHub REST API integration. New command-line flags (`--no-publish`, `--no-edit`) allow skipping the TUI or publishing directly. Configuration options and multi-language support (es_es, fr_fr, pt_br, pt_pt) are expanded accordingly.

## 🛠️ Technical Changes
- New interactive TUI (Textual-based) for PR publishing (`src/ui/pr_publish_app.py`, `src/ui/pr_publish_help.py`).
- GitHub API module (`src/github_api.py`) with `create_pull_request` function using `requests`.
- Auto-commit flow with linter validation, commit message generation, and user confirmation via modal dialogs.
- Handling of unstaged files: detection, selection, and staging (`has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit` in `src/core.py`).
- New CLI flags: `--no-publish` (save locally without TUI), `--no-edit` (auto-commit and direct publish), `--base` (target branch override).
- Configuration entries added to `src/config.py`: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`.
- Multi-language support: over 80 new translation keys added for es_es, fr_fr, pt_br, pt_pt.
- Default `gitpr` behavior now opens the interactive publisher TUI instead of just saving a local .md file.

## ⚠️ Impact/Warnings
- **Behavioral change**: Running `gitpr` without flags now launches the TUI; previously it only generated a local description file. Use `--no-publish` to retain the old behavior.
- **New environment variables**: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK` (all in `~/.gitpr/.env`).
- **Dependencies**: The GitHub API integration uses the `requests` library (should already be available).
- **Authentication**: Requires a valid GitHub token (stored/requested via `--publish` flow). Token expiration triggers interactive reauthorization.
- **TUI framework**: Relies on Textual, which is already a project dependency.
- No database schema changes.