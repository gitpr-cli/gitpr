# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR Publisher TUI for direct GitHub publication
```

---

## 🎯 Summary

This PR introduces an interactive Terminal UI (TUI) that allows users to review, edit, and publish Pull Requests directly to GitHub via the REST API. Previously, the tool only generated a local Markdown file; now it offers a guided publication flow with live editing, local backup, and error handling.

## 🛠️ Technical Changes

- Added `github_api.py` module to encapsulate GitHub Pull Request creation logic (POST /repos/{owner}/{repo}/pulls) with robust error message extraction and connection/timeout handling.
- Added `pr_publish_app.py` (Textual-based TUI) with F1–F3 bindings for help, local save, and publish actions. Includes re-authentication loop for expired tokens.
- Added `pr_publish_help.py` modal screen for in-app usage instructions.
- Modified `main.py`: integrated the TUI into the default flow, added `--base` CLI option to override the target branch, and implemented the interactive publish loop.
- Updated `config.py` with new `PR_DEFAULT_BASE` environment variable.
- Added 31 new translation keys (English, Spanish, French, Portuguese) covering all UI labels, error messages, and help text.

## ⚠️ Impact/Warnings

- **Breaking behavioral change**: the default execution now opens the interactive TUI after generating the PR description. Users who relied on the old non-interactive flow may need to adjust scripts or use `--no-edit` (if applicable).
- **Dependency**: The new TUI uses Textual (already a project dependency).
- **New environment variable**: `PR_DEFAULT_BASE` can be set to define a default base branch; overridden by `--base`.
- **GitHub token**: required for publication. Invalid tokens trigger an in-app re-authentication prompt.
- **Network calls**: Publication requires internet connectivity; connection errors are handled gracefully with user-friendly messages.