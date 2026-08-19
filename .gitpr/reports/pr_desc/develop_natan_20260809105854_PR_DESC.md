# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add existing PR handling and merge flow
```

---

## 🎯 Summary

Enhances the PR publish flow to intelligently handle branches that already have an open Pull Request. Before pushing, the system checks for an existing PR; if found, it offers to push commits and update the PR description instead of creating a duplicate. After PR creation or update, users are prompted to merge the PR directly (or auto-merge via the new `GITPR_AUTO_MERGE` environment variable). Internationalization keys are added for all new dialogs in Spanish, French, and Brazilian/European Portuguese. The commit progress screen now runs in a background thread to avoid UI blocking.

## 🛠️ Technical Changes

- Added `check_existing_pr`, `update_pull_request`, and `merge_pull_request` functions to `github_api.py` for GitHub REST API operations.
- Made `CommitConfirmScreen` accept custom button labels (`btn_yes`, `btn_no`) for reusable prompts.
- Updated `CommitProgressScreen` to support an initial status message and non-blocking background work via threading.
- Refactored `_start_commit_and_publish` to execute commit, push, and PR creation in a background thread, with proper thread-safe UI updates.
- Added flow to detect existing PR before push and ask user whether to push and update the existing PR or keep the commit local.
- Added auto-set-upstream for `git push` when `upstream` branch is missing.
- Added merge prompt after PR creation/push, with an optional auto-merge via `GITPR_AUTO_MERGE` config.
- Removed the commit message section from the PR body; only the user-provided description is used.
- Increased error screen max-height to 80% with overflow-y auto for better readability of long error messages.
- Added 15+ new i18n keys for all new UI messages and dialogs.
- Added `GITPR_AUTO_MERGE` to `DEFAULT_CONFIG` (defaults to `"false"`).

## ⚠️ Impact/Warnings

- **New environment variable**: `GITPR_AUTO_MERGE` (default `false`). Set to `true`/`1`/`yes`/`y` to automatically merge the PR after creation without user prompt.
- **GitHub token permissions**: The token must have `repo` scope for merge and update API calls.
- **Translation coverage**: Only Spanish, French, Brazilian Portuguese, and European Portuguese were updated. Other languages will show English fallbacks for new keys.
- **UI flow**: The publish process now runs entirely in a background thread; threads share `stdout` suppression to avoid artifacts, but this may affect debugging.
- No database or deployment changes required.