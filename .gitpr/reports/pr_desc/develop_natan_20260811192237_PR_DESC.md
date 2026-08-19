# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: handle merge outcome in PR publish UI
```

---

## 🎯 Summary
This change improves the merge workflow by introducing distinct handling for successful and failed merge operations. Previously, the user received a generic success/failure message without detailed guidance for conflicts. Now, the UI provides explicit feedback, including an error modal for merge conflicts (HTTP 405) with an option to open the PR in browser for manual resolution. This enhances user experience and reduces confusion during PR merges.

## 🛠️ Technical Changes
- Added `_on_merge_success` and `_on_merge_failure` methods to handle merge outcomes on the main thread.
- Updated `final_action` values to include `"merged"` and `"merge_failed"` for more granular state tracking.
- Implemented special handling for HTTP 405 status (merge conflict) by displaying a dedicated error modal with a direct link to the PR.
- Updated the color logic in `cli()` to include `"merged"` as a success status and extended the browser prompt condition to include `"merged"` and `"merge_failed"`.
- Changed the error message format to use a title and detail, improving clarity.

## ⚠️ Impact/Warnings
- No database or environment variable changes.
- The UI now relies on threading callbacks; ensure that `self.call_from_thread` correctly dispatches to the main thread to avoid race conditions.
- The new error modal uses `CommitConfirmScreen`; verify that the screen handles the callback appropriately for browser opening.

close #108