# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: make linter modal buttons side-by-side and resume no-verify flow
```

---

## 🎯 Summary

Fixes two bugs in the PR publish linter error modal: the `Commit with --no-verify` and `Abort` buttons were stacked vertically and overlapped, and clicking `Commit with --no-verify` dismissed the modal without resuming the commit flow, sometimes causing the linter to run again and loop back into the modal. The buttons now sit side by side in a horizontal row and the no-verify choice resumes the progress flow with the linter skipped, allowing the commit to execute with `no_verify=True`. The modal presentation is also deferred through the app message pump to avoid a Textual callback-binding issue when the progress screen is popped.

## 🛠️ Technical Changes

- Change `linter_buttons` container from `Vertical` to `Horizontal` and add `height: auto` to the CSS so both buttons are fully visible and share the same row.
- Add `skip_linter` parameter to `_start_progress_and_commit` and `_run_linter_and_commit`; use it in the `skip_lint` decision and dynamic initial status.
- Replace inline pop/push in the linter error path with `self.call_next(self._show_linter_error_modal, errors)` and a new `_show_linter_error_modal` method to ensure the dismiss callback is bound to the app message pump.
- In `_on_linter_result`, on no-verify choice set `_commit_no_verify = True` and call `_start_progress_and_commit(skip_linter=True)` to prevent the linter from running again.
- Bump language dictionary version from `v0.0.19` to `v0.0.20`.
- Add regression tests for modal button layout, abort/no-verify results, and end-to-end no-verify commit flow; add i18n assertion for required modal keys.

## ⚠️ Impact/Warnings

- Language dictionary version bumped to `v0.0.20`; translation files must contain the `Abort` and `Commit with --no-verify` keys and be up to date.
- No database, environment variable, or dependency changes. Existing `GITPR_SKIP_LINT` behavior is preserved.