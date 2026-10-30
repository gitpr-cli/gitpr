## Completion Report — Auto-Close Commit Progress Modal on Completion

### What was done
- Updated `CommitApp` in `src/ui/commit_app.py` so that when git commit execution completes successfully, the progress modal automatically dismisses and the application cleanly shuts down.
- Implemented `_schedule_auto_exit()` with a 0.6s timer (`self.set_timer(0.6, self.exit)`) after rendering the success indicator `✅ Commit successfully created!`, ensuring smooth visual feedback before returning to the terminal.
- Preserved manual close button on error so users can review the error details if a pre-commit hook or git command fails.
- In `src/main.py`, upon return from `CommitApp`, if `app.result == "committed"`, the full commit summary and SHA are printed cleanly directly to the terminal stdout.
- Updated `tests/test_commit_app.py` with unit tests for `_schedule_auto_exit()` and updated headless integration test verifying automatic exit upon commit.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/ui/commit_app.py` | fix | Added automatic exit timer (`_schedule_auto_exit`) upon commit success. |
| `src/main.py` | feat | Output commit summary and output to stdout after `CommitApp` closes. |
| `tests/test_commit_app.py` | test | Added test for `_schedule_auto_exit()` and updated full flow headless test. |

### Impact
- **Functionality:** `gitpr -c` now automatically closes the progress modal and exits back to the terminal prompt once the commit is created, without requiring the user to manually click a Close button.
- **Performance:** Instant and seamless return to shell prompt after commit completion.
- **Compatibility:** 100% backward compatible.

### Next steps (if applicable)
- None. All tests passing (14/14).
