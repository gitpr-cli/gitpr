# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher TUI with auto-commit and lint
```

---

## 🎯 Summary

This change introduces a fully interactive Terminal User Interface (TUI) for reviewing, editing, and publishing Pull Requests directly to GitHub. It streamlines the entire PR lifecycle—from staging uncommitted files, running the linter, generating AI-based commit messages, and creating the PR via the GitHub API—all within a single terminal session.

## 🛠️ Technical Changes

- New `src/ui/pr_publish_app.py`: A Textual-based TUI with modals for commit confirmation, file staging, commit message editing, linter errors, progress animation, and error handling.
- New `src/github_api.py`: Module for creating PRs through the GitHub REST API with proper error extraction.
- New `src/core.py` helpers: `has_uncommitted_changes()`, `get_unstaged_files()`, `stage_files()`, `execute_git_commit()` to support the auto-commit flow.
- Extended `src/main.py` with new CLI options (`--no-publish`, `--no-edit`, `--base`) and logic to orchestrate TUI launch, auto-commit, and direct publishing.
- Added configuration keys (`PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, etc.) to `src/config.py` and environment-based behavior.
- Updated language files (`langs/es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`) with all new UI strings for Spanish, French, Brazilian Portuguese, and European Portuguese.
- Added initial metrics export files under `.gitpr/metrics/export/` for future telemetry.

## ⚠️ Impact/Warnings

- **New Dependencies**: The TUI now requires the `textual` library. Ensure it is installed (`pip install textual`).
- **Environment Variables**: Behavior can be customized via `.env` file in `~/.gitpr/`: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`.
- **GitHub Token**: The TUI relies on a valid GitHub token. If it expires during publishing, a reauthentication flow is triggered.
- **Linter Integration**: The linter runs automatically before committing. Users can bypass errors by selecting `--no-verify` or aborting.
- **Breaking CLI Change**: The default `gitpr` command now opens the TUI instead of just generating a PR file. To retain the old behavior, use `--no-publish`.