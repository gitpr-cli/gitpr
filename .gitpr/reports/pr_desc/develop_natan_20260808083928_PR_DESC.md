# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publisher TUI and auto-commit with GitHub API
```

---

# 🎯 Summary
This introduces a fully interactive Terminal User Interface (TUI) for reviewing, editing, and publishing Pull Requests directly to GitHub via the REST API. Users can now generate a PR description, auto-commit unstaged changes (with lint validation), and publish the PR in one seamless flow. The feature includes new CLI flags (`--base`, `--no-publish`, `--no-edit`), localization support for six languages, and automatic metrics logging.

# 🛠️ Technical Changes
- Added `PrPublishApp` (Textual TUI) for interactive PR publishing with title/body editing, help modal, and multi-step commit workflow (file staging, linter, AI-generated commit message confirmation).
- Integrated GitHub REST API client (`src/github_api.py`) to create PRs via `POST /repos/{owner}/{repo}/pulls`.
- Implemented auto-commit logic in `main.py` for `--no-edit` mode, including linter enforcement, AI commit message generation, and staging of unstaged files.
- Extended CLI with `--base` (target branch), `--no-publish` (save locally), and `--no-edit` (direct publish with auto-commit).
- Added localization keys for all new UI strings in Spanish, French, Brazilian Portuguese, and European Portuguese.
- Added new configuration options: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`.
- Included metrics export files (CSV/JSON) for tracking PR publication events.
- Added helper functions `has_uncommitted_changes()` and `execute_git_commit()` to `core.py`.

# ⚠️ Impact/Warnings
- **New dependency**: The TUI relies on the `textual` Python library; ensure it's installed.
- **Environment variables**: New `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS` control behavior; defaults are safe.
- **GitHub token**: Publishing requires a valid GitHub PAT with repo scope. Expired/invalid tokens are handled gracefully with re-authentication prompts.
- **Data privacy**: Metrics files are stored locally (`.gitpr/metrics/export/`). Ensure they are not committed if sensitive.
- **Backward compatibility**: The default behavior now opens the TUI instead of just generating a file. Users who want the old behavior can use `--no-publish` or set appropriate config.