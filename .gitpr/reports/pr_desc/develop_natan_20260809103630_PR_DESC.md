# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: enhance PR flow with existing PR detection and merge
```

---

🎯 Summary
This change enhances the PR publishing workflow by detecting existing PRs before push, allowing users to update or open them directly, and adding an optional merge prompt after creation. It also introduces new translations and a configurable auto-merge option.

🛠️ Technical Changes
- Added `check_existing_pr`, `update_pull_request`, and `merge_pull_request` to GitHub API module.
- Refactored `PrPublishApp` to check for existing PRs, prompt user for actions, push + update PR description, and offer merge.
- Dynamic buttons in `CommitConfirmScreen` and initial status in `CommitProgressScreen`.
- Moved commit/push/publish logic to a background thread with stdout suppression for thread safety.
- New `GITPR_AUTO_MERGE` configuration option (env var).
- Added translation strings in ES, FR, PT-BR, PT-PT for new prompts and statuses.
- Removed prepended commit message section from PR body; now uses user-provided description only.

⚠️ Impact/Warnings
- PR body format changes: no longer includes auto-generated commit message block.
- New interactive prompts may alter existing automation; ensure UI tests are updated.
- `GITPR_AUTO_MERGE=false` by default; set to `true` to enable automatic merge (requires write access).
- Background threading with stdout redirection may affect logging or debug output in some setups.