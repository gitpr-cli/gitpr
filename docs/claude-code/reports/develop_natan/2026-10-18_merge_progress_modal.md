## Completion Report — Animated progress modal during PR merge

### What was done
- `CommitProgressScreen` now accepts an optional `title` and `mark_finished(show_close=False)`, so the commit flows keep their current behavior while other flows reuse the same animation.
- `_do_merge` pushes the animated modal before the merge runs, both for the manual "Yes, Merge Now" path and for `GITPR_AUTO_MERGE`.
- On success the modal shows `✅ PR #N merged successfully!`, fills the bar, keeps Close hidden and auto-dismisses after 1.2 s before the existing Open-in-Browser prompt.
- On failure (`ScmProviderError` or any unexpected exception) the modal is dismissed and the existing `_on_merge_failure` screen is reused; unexpected errors are logged and reported with status 0 instead of silently killing the worker thread.
- Added the three new user-facing strings to all six language files (parity requirement of `tests/test_i18n.py`).
- Added 10 tests covering the generic modal, the manual and auto-merge success paths, conflict/generic failure paths and early dismissal.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/ui/pr_publish_app.py | feat | Reusable progress title/Close control; merge progress modal and success/failure sequencing |
| langs/pt_br.json | feat | 3 new translated strings |
| langs/pt_pt.json | feat | 3 new translated strings |
| langs/es_es.json | feat | 3 new translated strings |
| langs/es.json | feat | 3 new translated strings |
| langs/fr_fr.json | feat | 3 new translated strings |
| langs/fr.json | feat | 3 new translated strings |
| tests/test_pr_publish_app.py | test | 10 tests for modal reuse and merge flows |

### Impact
- **Functionality:** the PR TUI now displays the animated modal with status messages while merging, instead of leaving the editable PR screen idle. The commit flow is unchanged (title and Close defaults preserve behavior).
- **Performance:** no change; the HTTP merge call still runs on a daemon thread and the animation ticks on the Textual timer.
- **Compatibility:** no public API change; `CommitProgressScreen` gains optional parameters only. No AI prompt or cache changes.

### Verification
- `python -m pytest tests/test_pr_publish_app.py -v -k "CommitProgressScreen or MergeProgress"` → 10 passed.
- `python -m pytest tests/test_pr_publish_app.py tests/test_pr_publish_linter_modal.py` → all passed.
- Full suite: 2940 passed, 10 failed — all pre-existing and unrelated: 3 in `tests/test_i18n.py` (missing/orphan keys from earlier features) and 7 in `tests/badge/test_badge_paths.py` (`--no-edit` token path in `src/main.py`). No new failures.

### Next steps (if applicable)
- Pre-existing i18n debt: 8 `__()` keys missing in all six files (MCP/check/PR-publish messages) and 2 orphan keys in four files; `es.json`/`fr.json` also lack the two orphan keys, so `test_key_parity_and_count` fails. Track separately.
- Pre-existing badge test failures in `_publish_pr_directly` (token validation) are unrelated to this change.
