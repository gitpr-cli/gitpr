# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: skip token validation when check_remote_state is disabled
```

---

## 🎯 Summary

Adjusts the pull request publishing flow so that all remote-state checks (including the provider token validation) are gated behind the `check_remote_state` flag. Previously, the token check ran unconditionally, which broke flows that intentionally skip remote verification (e.g., badges and local/dry-run scenarios). This change makes the flag the single source of truth for whether any remote validation is performed.

Additionally, result extraction now uses defensive `getattr` access for `url` and `number`, preventing `AttributeError` when a provider returns a lighter-weight result object.

## 🛠️ Technical Changes

- Moved the provider token validation inside the `if check_remote_state:` block in `publish_pull_request_use_case`.
- Reordered the guard so the entire remote-state verification block is conditional on `check_remote_state`.
- Extracted `pr_url` and `pr_number` via `getattr(result, "url", "")` and `getattr(result, "number", 0)` with safe defaults, and reused `pr_url` in the label generation.
- Updated `tests/badge/test_badge_paths.py` mocks to include `token` on the provider and `number` on the returned result, matching the stricter/extended contract.
- Added `pilot.exit(None)` to the TUI publisher test to ensure clean termination.

## ⚠️ Impact/Warnings

- No database, environment variable, or dependency changes.
- Behavior change: when `check_remote_state` is disabled, token validation is now skipped entirely. Any caller relying on token errors being raised in this mode will no longer receive them.
- Provider result objects missing `url`/`number` now degrade gracefully to `""`/`0` instead of raising, which may surface empty PR links downstream if a provider does not populate these fields.

close #225

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_1_warning-yellow)](https://gitpr.natanfiuza.dev.br/)