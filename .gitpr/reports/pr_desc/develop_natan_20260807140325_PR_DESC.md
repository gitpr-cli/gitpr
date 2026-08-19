# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR publishing to GitHub via API and TUI
```

---

## 🎯 Summary

This PR introduces the ability to publish Pull Requests directly to GitHub from the command-line tool, eliminating the need to switch to the web interface. Users can now generate, review, edit, and publish PRs through an interactive terminal UI (TUI) or via quick command-line flags (`--no-publish`, `--no-edit`). The flow also includes automatic lint validation and an optional auto-commit step, making the end-to-end PR creation a seamless developer experience.

## 🛠️ Technical Changes

- Added new `github_api.py` module with `create_pull_request()` function to interact with the GitHub REST API.
- Added `pr_publish_app.py` and `pr_publish_help.py` for the TUI interface (F1 help, F2 save local, F3 publish).
- Extended the main CLI with `--base`, `--no-publish`, and `--no-edit` flags to support direct publishing.
- Implemented an auto-commit flow that generates a commit message through AI, runs the linter, handles `--no-verify` on demand, and commits before publishing.
- Added new configuration keys: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, and `GITPR_SKIP_LINT` to control default behavior.
- Extended translation files (es_es, fr_fr, pt_br, pt_pt) with all new UI messages.
- Updated `core.py` with helpers (`has_uncommitted_changes`, `execute_git_commit`) to support the new workflows.

## ⚠️ Impact/Warnings

- Requires a valid GitHub token for authentication; expired tokens are handled interactively.
- The new TUI is launched by default when no other command is supplied (`gitpr` without options).
- Introduces new environment variables (`GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`) that may affect existing CI/CD setups if configured.
- No database or external dependency changes beyond the existing `requests` library.