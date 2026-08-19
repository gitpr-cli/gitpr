## Completion Report — Linter Error Modal Fixes (PR Publish TUI)

### What was done
- Fixed the three bugs in the linter error modal (`LinterErrorScreen`) of the PR publish TUI, per the plan `docs/plans/20260819_prompt_correcao_gitpr_linter.md`.
- **Button overlap:** the "Commit with --no-verify" and "Abort" buttons were stacked in a `Vertical` container whose greedy `1fr` height pushed the second button into the dialog border (clipped top border, invisible label). They now sit side by side in a `Horizontal` container with `height: auto`, and the dialog hugs its content instead of filling the whole screen.
- **Dead button handler:** clicking "Commit with --no-verify" dismissed the modal but never executed anything. Root cause: the modal was pushed from inside the progress screen's timer callback; Textual binds the dismiss callback to the *active message pump* at push time (the progress screen), which had just been popped — so the result was posted to a dead message queue and `_on_linter_result` never ran. The push is now deferred to the app's own pump via `call_next()`, and the flow resumes with the linter skipped (`skip_linter=True`), generating the AI commit message and executing the commit with `no_verify=True` (visible progress, errors handled via the existing `ErrorScreen`).
- **Untranslated "Abort" button:** the key already existed and was translated in all six repo language files, but clients kept a stale local copy because the language OTA marker was not bumped after the translation fix — the local file had `"Abort": "Abort"`. Bumped `__lang_version__` v0.0.19 → v0.0.20, which forces a re-download of the corrected files from GitHub on next run (verified: the dev machine's stale `~/.gitpr/langs/pt_br.json` self-healed to `"Abortar"` immediately on first run after the bump).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/ui/pr_publish_app.py | fix | Buttons side by side in `Horizontal` with `height: auto`; push of `LinterErrorScreen` deferred to the app pump via `call_next` (new `_show_linter_error_modal()`); `_start_progress_and_commit()`/`_run_linter_and_commit()` accept `skip_linter` so the no-verify choice skips the linter and the commit executes with `--no-verify` |
| src/updater.py | fix | Bumped `__lang_version__` v0.0.19 → v0.0.20 to force OTA refresh of corrected translation files |
| tests/test_pr_publish_linter_modal.py | test | New: 4 regression tests (layout side-by-side/no overlap, abort result, no-verify result, full TUI flow with mocked linter/AI/git asserting commit runs with `no_verify=True` and the linter is not re-run) |
| tests/test_i18n.py | test | New `test_linter_modal_keys_present_and_translated` guarding "Abort" and "Commit with --no-verify" across the six language files |

### Impact
- **Functionality:** The linter error modal now shows both buttons fully rendered, side by side, correctly translated. "Abort" returns to the TUI; "Commit with --no-verify" continues the flow (AI message → confirmation → commit with `--no-verify` → push → PR), with failures surfaced via the existing error modal. No more silent dismissal or modal loop.
- **Performance:** Negligible — one deferred message pump per linter-error path.
- **Compatibility:** No API breaks. `__lang_version__` bump causes a one-time re-download of `~/.gitpr/langs/{lang}.json` on every client with `LANG_VERSION != v0.0.20`; offline fallback to the existing local file is preserved.
- **Validation:** 264/264 tests pass (`pipenv run pytest tests/`); CLI boot smoke-tested (`run.py --help`). Full TUI flow exercised headlessly via Textual `run_test` pilot (F3 → confirm → linter error → no-verify → commit with flag).

### Next steps (if applicable)
- Merge `develop_natan` → `main` so the `__lang_version__` bump and TUI fixes reach users (the corrected `langs/*.json` are already on `main` via e2f0fa0; the marker bump is what ships the refresh).
- Manual sanity pass of the real `gitpr` TUI flow on a terminal with a lint-breaking diff (the headless tests mock git/AI; one real end-to-end run is recommended).
