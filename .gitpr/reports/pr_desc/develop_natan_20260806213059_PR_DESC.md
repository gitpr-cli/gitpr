# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher TUI with GitHub API integration
```

---

🎯 Summary
Introduces an interactive terminal UI (TUI) that allows users to review, edit, and publish Pull Requests directly to GitHub via the REST API, eliminating the need to leave the CLI.

🛠️ Technical Changes
- Added `src/github_api.py` – robust client for creating PRs via GitHub API with detailed error handling (422, 401, network issues).
- Added `src/ui/pr_publish_app.py` – Textual-based TUI for editing PR title, commit message, body, and base branch, with save-local and publish actions.
- Added `src/ui/pr_publish_help.py` – modal help screen for the publishing TUI.
- Extended `src/config.py` with `PR_DEFAULT_BASE` and `PR_AUTO_PUBLISH` environment variables and a `get_pr_auto_publish()` helper.
- Enhanced `src/main.py` with `--publish`, `--base`, and `--no-edit` flags, including direct publish mode and interactive publish flow with token reauthentication.
- Updated internationalisation (`es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`) with 31 new keys for the publisher UI and messages.

⚠️ Impact/Warnings
- Requires a valid `GITHUB_TOKEN`; expired tokens will trigger an interactive reauthentication loop.
- Network-dependent features: offline mode gracefully reports connectivity issues.
- New optional config variables `PR_DEFAULT_BASE` and `PR_AUTO_PUBLISH` may need documentation for advanced users.
- The `--no-edit` flag is ignored unless combined with `--publish` or `PR_AUTO_PUBLISH=true`; a warning is shown otherwise.