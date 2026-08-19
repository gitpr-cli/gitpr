# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher with auto-commit and API integration
```

---

🎯 **Summary**

Implements a complete interactive Pull Request publication flow, enabling users to review, edit, auto-commit changes (with lint validation), and publish PRs directly to GitHub via API – all from a terminal UI. The feature supports both local-only saving and direct one-shot publishing without the TUI.

🛠️ **Technical Changes**
- New `src/github_api.py`: `create_pull_request()` function to call GitHub REST API.
- New `src/ui/pr_publish_app.py`: Textual-based TUI with screens for commit confirmation, file staging, progress, commit message editing, linter errors, and error handling.
- New `src/ui/pr_publish_help.py`: help screen modal.
- Extended `src/core.py` with `has_uncommitted_changes()`, `get_unstaged_files()`, `stage_files()`, and `execute_git_commit()`.
- Updated `src/main.py`: new CLI flags `--base`, `--no-publish`, `--no-edit`; full PR publisher orchestration (unstaged check, auto-commit, direct publish, TUI launch).
- Added ~90 translation keys for the PR publisher UI across `es_es`, `fr_fr`, `pt_br`, `pt_pt`.
- New `.env` defaults: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.
- Metric export files for internal tracking.

⚠️ **Impact/Warnings**
- Requires `textual` and `requests` packages (verify dependencies).
- GitHub token must be valid for API calls; expired tokens trigger interactive re-authentication.
- New environment variables control auto-commit, lint, and staging; review defaults before use.
- All new UI strings need to be fully translated in all supported language files.