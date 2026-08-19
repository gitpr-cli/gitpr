# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publishing with auto-commit and linter
```

---

🎯 Summary
This change introduces a fully interactive Pull Request publishing workflow. Users can now review, edit, and publish PRs directly from the terminal via a Textual TUI. The flow includes automatic staging of unstaged files, AI‑generated commit messages, linter validation, and GitHub API integration. New CLI flags `--no‑publish` (save locally) and `--no‑edit` (auto‑commit + publish) allow non‑interactive use. All new strings are translated to Spanish, French, Portuguese (Brazil and Portugal).

🛠️ Technical Changes
- Added `pr_publish_app.py` and `pr_publish_help.py` (Textual TUI) for interactive review, edit, and publish.
- Added `github_api.py` with `create_pull_request()` using GitHub REST API.
- Added `has_uncommitted_changes()` and `execute_git_commit()` to `src/core.py`.
- Integrated auto‑commit flow with linter (`src/linter_engine`), staging, and commit message generation.
- Updated `cli()` in `main.py` to run the interactive publisher by default; added `--no‑publish`, `--no‑edit`, and `--base` flags.
- Added helper functions `_run_auto_commit_cli`, `_get_github_token_for_publish`, `_publish_pr_directly`.
- Extended language files (`es_es`, `fr_fr`, `pt_br`, `pt_pt`) with ~70 new keys for the PR publisher.
- Added new config keys: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`.
- Added metric files for PR publish events (`gitpr_metrics_*.csv/json`).
- Updated help system with entries for `--no‑publish` and `--no‑edit`.

⚠️ Impact/Warnings
- **Default behavior change**: Running `gitpr` without flags now opens the interactive TUI instead of just saving a local Markdown file.
- **New environment variables**: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS` control the new workflows.
- **GitHub token required**: Users must have a valid GitHub token configured to publish PRs.
- **Dependency**: The new TUI uses the `textual` library; ensure it is installed.
- **Telemetry**: PR publication events are now tracked in `~/.gitpr/metrics/`.
- **Documentation**: Users should consult the updated `pull-request-publication` guide for the new flags and workflows.