# Implementation Plan - Fix 7 Failures in test_badge_paths.py

**Date:** 2026-10-27  
**Branch:** `develop_natan`  
**Task:** `fix_badge_paths_tests`  

---

## 1. Problem Overview

In `tests/badge/test_badge_paths.py`, seven test cases fail with `KeyError: 'request'`:
- `TestTheDirectPublisher::test_the_published_body_carries_the_badge`
- `TestTheDirectPublisher::test_the_description_is_still_the_description`
- `TestTheDirectPublisher::test_the_commit_message_block_is_untouched`
- `TestTheDirectPublisher::test_a_body_without_a_badge_publishes_without_one`
- `TestTheNotice::test_the_badge_is_announced`
- `TestTheNotice::test_the_announcement_names_what_was_added`
- `TestTheNotice::test_a_body_without_a_badge_is_not_announced`

### Root Cause Analysis
1. `_publish()` in `tests/badge/test_badge_paths.py` constructs a fake provider with `SimpleNamespace(name="github", create_pull_request=create_pull_request)` lacking a `.token` attribute.
2. In `_publish_pr_directly` (`src/main.py`), publication is delegated to `publish_pull_request_use_case(..., check_remote_state=False)`.
3. In `publish_pull_request_use_case` (`src/application/use_cases/publish_pull_request.py`), an upfront check `if not getattr(provider, "token", ""):` runs unconditionally before checking `if check_remote_state:`, despite the docstring specifying that token verification is part of the `check_remote_state=True` flow (used by MCP).
4. Because `.token` is missing or empty, `publish_pull_request_use_case` returns `status="auth_required"` with `http_status=401`.
5. `_publish_pr_directly` receives the 401 outcome, logs a token expired/invalid message to stdout, and exits early without calling `provider.create_pull_request`.
6. `captured["request"]` is never populated, raising `KeyError: 'request'`.

---

## 2. Proposed Changes

### 2.1 Use Case Alignment (`src/application/use_cases/publish_pull_request.py`)
- Move the `if not getattr(provider, "token", ""):` validation inside the `if check_remote_state:` block.
- For callers passing `check_remote_state=False` (such as CLI `--no-edit`, where authentication was already validated by the CLI orchestration layer), the use case does not preemptively fail when a custom or lightweight provider object does not declare a `.token` attribute, deferring any authorization error handling to the forge invocation itself (`create_pull_request`).

### 2.2 Test Provider Contract Enhancement (`tests/badge/test_badge_paths.py`)
- In `_publish()`, add `token="ghp_fake"` to `SimpleNamespace(...)`.
- This ensures the mock provider explicitly satisfies the full SCM provider contract for tests exercising direct publishing.

### 2.3 Textual Async Test Clean Teardown (`tests/badge/test_badge_paths.py`)
- In `TestTheTuiPublisher::test_the_badge_is_inside_the_editable_text_area`, add `await pilot.exit(None)` after assertions to ensure clean, non-blocking termination of the Textual event loop across all environments.

---

## 3. Verification Steps

1. Run the targeted tests in `tests/badge/test_badge_paths.py` to verify that all 10 tests pass (including the 7 previously failing tests):
   ```bash
   python -m pytest tests/badge/test_badge_paths.py -v
   ```
2. Run related publisher and use case tests:
   ```bash
   python -m pytest tests/test_pr_publish_app.py tests/test_mcp_server.py -k "publish_pull_request" -v
   ```
3. Generate the mandatory task completion report at `docs/gemini/reports/develop_natan/2026-10-27_fix_badge_paths_tests.md`.
