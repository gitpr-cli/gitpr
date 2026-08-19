# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add GitHub token validation and reauth on 401
```

---

## 🎯 Summary

Enhances the GitHub token handling to validate the PAT before launching the issue creation TUI and to gracefully handle 401 errors during the session. Users are now prompted for a new token if the current one is invalid or expires, without losing their issue draft.

## 🛠️ Technical Changes

- Added `validate_github_token()` in `config.py` to perform a lightweight `GET /user` call and verify the token's validity.
- Refactored `validate_or_request_github_token()` in `tui_issue.py` into smaller helpers (`_remove_expired_token`, `_show_auth_instructions`, `_prompt_and_save_token`) and introduced a token validation loop with up to 3 attempts.
- Modified `IssueApp.action_create_issue()` in `ui/issue_app.py` to detect 401 responses and signal a `reauth` action through a `needs_new_token` flag.
- Updated `main.py` to wrap the TUI launch in a `while True` loop that re-prompts for a token and restarts the TUI when `final_action == "reauth"`.
- Fixed a bug in `metrics.py` where the `path` key was missing from the early return dictionary.
- Removed a redundant `metrics` condition in `main.py` (`if metrics and show_dashboard` → `if show_dashboard`).

## ⚠️ Impact/Warnings

- **New dependency:** `requests` is now used in `config.py` for the API call. Ensure it is installed.
- **Network call:** One additional HTTP request to `api.github.com/user` per `gitpr -is` invocation. Negligible performance impact (~200ms).
- **Behavior change:** Users will be unable to proceed without a valid token, and expired tokens are automatically removed from the `.env` file.
- **No breaking changes** for existing APIs or CLI flags.