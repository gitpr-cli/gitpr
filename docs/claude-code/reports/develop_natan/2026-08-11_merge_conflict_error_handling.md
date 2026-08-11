## Completion Report — Merge Conflict Error Handling in PR Publisher

### What was done
- Fixed `_do_merge` to show an error modal when merge fails instead of silently proceeding to browser prompt
- Added special handling for HTTP 405 (merge conflicts) with a clear, actionable message
- Added `final_action` tracking for merge outcomes (`"merged"` / `"merge_failed"`) so post-TUI display uses correct colors
- Thread-safety: `final_message` and `final_action` updates now happen on the main thread via `call_from_thread`

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/ui/pr_publish_app.py | fix | Refactored `_do_merge` into 3 methods: `_do_merge` (spawns thread), `_on_merge_success` (main-thread callback), `_on_merge_failure` (main-thread callback with error modal). Special 405 conflict message. |
| src/main.py | fix | Added `"merged"` to green actions list; extended browser-prompt condition to include `"merged"` and `"merge_failed"` |

### Impact
- **Functionality:** Merge failures now show a visible error modal in the TUI with the GitHub error message. For 405 (merge conflicts), the message explicitly says conflicts must be resolved manually on GitHub. The user can open the PR in browser directly from the error modal.
- **Performance:** No impact — same number of API calls, same thread model.
- **Compatibility:** No breaking changes. `final_action` values `"merged"` and `"merge_failed"` are new but only affect internal display logic.

### Next steps
- Add Portuguese (pt_br) translations for the new i18n keys in `langs/pt_br.json`
