# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publication with interactive TUI and auto-commit
```

---

## 🎯 Summary
This update introduces a complete Pull Request publication flow. Users can now generate PR descriptions, review/edit them in an interactive TUI, optionally stage unstaged files, auto-commit pending changes with linter validation, and publish directly to GitHub via the REST API. The feature supports multiple languages (ES, FR, PT-BR, PT-PT) and adds new CLI flags (`--base`, `--no-publish`, `--no-edit`) for flexible workflows.

## 🛠️ Technical Changes
- Added `src/github_api.py` module to handle PR creation via GitHub REST API.
- Added `src/ui/pr_publish_app.py` and `src/ui/pr_publish_help.py` for the interactive TUI with auto-commit, lint checks, and progress tracking.
- Extended `src/main.py` with new CLI options (`--base`, `--no-publish`, `--no-edit`) and integrated PR publication logic, including unstaged file handling.
- Added helper functions to `src/core.py`: `has_uncommitted_changes()`, `get_unstaged_files()`, `stage_files()`, `execute_git_commit()`.
- Updated `src/config.py` with new environment variables: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.
- Added localization strings for the PR publication UI in `langs/es_es.json`, `langs/fr_fr.json`, `langs/pt_br.json`, `langs/pt_pt.json`.
- Added metrics export files for local telemetry (`.gitpr/metrics/export/`).

## ⚠️ Impact/Warnings
- **New feature** – no breaking changes to existing functionality.
- Requires a valid GitHub token with `repo` scope for API publishing.
- Users must configure the new environment variables if they want to customize auto-commit, skip lint, auto-stage files, or set a default base branch.
- The interactive TUI uses Textual; ensure the terminal supports it.
- Localized messages are fully translated for the published UI.