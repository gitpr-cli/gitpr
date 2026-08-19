# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with TUI and direct publish options
```

---

## 🎯 Summary

This PR introduces a complete Pull Request Publisher feature, enabling users to review, edit, and publish Pull Requests directly to GitHub via an interactive terminal UI (TUI). It supports both interactive and direct (--no-edit) workflows, including auto‑commit, linter validation, file staging, and AI‑generated commit messages. The feature is fully internationalized (es, fr, pt‑br, pt‑pt) and integrates with GitHub API for seamless PR creation.

## 🛠️ Technical Changes

- **New module `github_api.py`**: Implements `create_pull_request()` with REST API call, error extraction, and i18n messages for network failures.
- **New UI components**:
  - `PrPublishApp` (Textual app) with interactive PR editor, auto‑commit flow, linter integration, file staging, and publish confirmation.
  - `PrPublishHelpScreen` for keybindings help.
  - Modal screens: `CommitConfirmScreen`, `FileStageScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`.
- **New CLI options**:
  - `--base` to specify target base branch.
  - `--no-publish` to save PR locally without TUI.
  - `--no-edit` for direct publish with auto‑commit, linter, and PR creation.
- **Auto‑commit flow**: 
  - `_run_auto_commit_cli()` in `main.py` handles linter checks, AI commit message generation, user confirmation, and git commit execution.
  - Respects `GITPR_SKIP_LINT`, `GITPR_AUTO_COMMIT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS` environment variables.
- **Core utilities**:
  - `has_uncommitted_changes()` and `execute_git_commit()` added to `core.py`.
- **Internationalization**: 75+ new translation strings added to `es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`.
- **Metrics**: Generated CSV/JSON export files for local telemetry.
- **Configuration**: New default keys `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS` in `config.py`.
- **Documentation**: Updated READMEs and new multi-language PR publication guides (`docs/pull-request-publication.*.md`).

## ⚠️ Impact/Warnings

- **Dependencies**: Requires `requests` and `textual` Python packages. Ensure they are installed.
- **GitHub Token**: Publishing requires a valid GitHub token with repo scope. The interactive flow guides users through token creation if missing or expired (via `tui_issue`).
- **Environment Variables**: New optional config flags (`GITPR_AUTO_COMMIT`, etc.) can alter behavior; document these for users.
- **Metrics Files**: New `.gitpr/metrics/export/` directory is created; add to `.gitignore` if not desired in repository.
- **Default Base Branch**: Now defaults to `main` or `master`; override with `--base` or `PR_DEFAULT_BASE`.
- **Breaking Change?** No, but the default behavior when running `gitpr` without options changes: it now opens the interactive TUI instead of just generating a file. Use `--no-publish` for the old behavior.