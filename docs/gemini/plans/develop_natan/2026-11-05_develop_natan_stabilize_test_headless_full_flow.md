# Implementation Plan — Stabilize `test_headless_full_flow`

**Date:** 2026-11-05  
**Branch:** `develop_natan`  
**Plan Name:** `stabilize_test_headless_full_flow`

---

## Goal Description
Resolve the intermittent failure in `tests/test_commit_app.py::TestCommitAppHeadlessFlow::test_headless_full_flow` where `pilot.click("#btn_confirm")` was dispatched before the `CommitMessageScreen` layout settled in Textual, leading to dropped click events and a 5-second timeout on waiting for the commit result.

## Proposed Changes

### Tests
#### [MODIFY] `tests/test_commit_app.py`
- Import `Button` from `textual.widgets`.
- Increase `_wait_until` default timeout from `5.0` to `10.0` seconds.
- In `test_headless_full_flow`:
  - Strengthen the transition predicate to assert that the active screen is an instance of `CommitMessageScreen`, that it is mounted (`app.screen.is_mounted`), and that `#btn_confirm` exists in its query selector.
  - Trigger the confirmation action via `app.screen.query_one("#btn_confirm", Button).press()` followed by `await pilot.pause()`, aligning with the proven modal interaction pattern used across `test_pr_publish_app.py`.

## Verification Plan
- Run `pytest tests/test_commit_app.py -v` across multiple consecutive iterations to confirm 100% determinism.
- Ensure the full suite of `TestCommitAppUnit` and `TestCommitAppHeadlessFlow` pass cleanly.
