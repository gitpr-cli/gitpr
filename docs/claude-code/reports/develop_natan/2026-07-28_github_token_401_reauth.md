## Completion Report — GitHub Token Auto-Revalidation on 401

### What was done
- Added `validate_github_token()` function in `config.py` to verify PAT validity via a lightweight GitHub API call (`GET /user`)
- Refactored `validate_or_request_github_token()` in `tui_issue.py` to validate the token before returning it, with automatic re-prompt on expiration
- Modified `IssueApp.action_create_issue()` in `ui/issue_app.py` to detect 401 errors and signal a "reauth" action instead of failing silently
- Updated `main.py` to handle the `reauth` action by looping back to token validation and relaunching the TUI

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| [src/config.py](src/config.py#L220) | feat | Added `validate_github_token()` — lightweight GitHub API call to verify PAT validity |
| [src/tui_issue.py](src/tui_issue.py) | refactor | Extracted `_remove_expired_token()`, `_show_auth_instructions()`, `_prompt_and_save_token()`; added token validation loop (max 3 attempts) |
| [src/ui/issue_app.py](src/ui/issue_app.py#L111) | feat | Added 401-specific handling with `needs_new_token` flag and `final_action = "reauth"` |
| [src/main.py](src/main.py#L534) | feat | Added `while True` loop to re-prompt and relaunch TUI on `reauth` action |

### Impact
- **Functionality:** When running `gitpr -is`, the token is now validated against the GitHub API **before** the TUI opens. If expired, the user is prompted for a new token immediately, with up to 3 attempts. If the token expires during the TUI session (rare), the 401 is caught and the user can re-authenticate without losing their issue draft.
- **Performance:** One extra HTTP call (`GET /api.github.com/user`) per `gitpr -is` invocation. Negligible (~200ms).
- **Compatibility:** No breaking changes. All existing APIs and CLI flags unchanged. 79/80 tests pass (1 pre-existing locale-dependent failure unrelated to this change).

### Next steps (if applicable)
- Consider adding the same token validation to any future GitHub API features (e.g., direct PR creation)
- The `_remove_expired_token()` utility could be exposed as a public function if other modules need it
