## Completion Report — Unstaged Files Modal Not Staging on Confirm

### What was done
- Investigated the "Unstaged Files" modal (`StageFilesScreen` / `StageFilesApp`) where clicking "Stage Selected" did not include the files, with the user's working tree confirming the files remained unstaged after the flow.
- Reproduced the exact symptom headlessly: the modal dismissed with `result = "stage"` but `selected_files = []` — the `git add` never ran — when the file selection was made through individual row toggles.
- Root causes identified in the staging path:
  1. **Selection desync:** `btn_stage` built the file list from a manual `self._selected` dict that only the "Select All" / "Deselect All" buttons updated. Individual row toggles (mouse click / Enter on a `SelectionList` row) were ignored — after "Deselect All" + clicking rows, the UI showed files selected but the modal staged an empty list.
  2. **Silent failure / false success:** `stage_files()` failures were swallowed at every call site. The console always printed "✅ N file(s) added to stage." even when `git add` failed, so the real git error never surfaced — matching the "git add seems to not be executed" symptom.
  3. **Double staging:** the modal and `check_unstaged_files()` both ran `git add` on the same selection, with neither call site checking the result.
- Fixed by: reading the real selection from `SelectionList.selected` at stage time; making `stage_files()` return `(success, error_message)`; staging exactly once (in `check_unstaged_files`) with success/failure feedback including git's actual error output.
- Note: the "not included in the PR description" side effect for docs-only changes is also influenced by the docs-smart-excludes design (`*.md` files are excluded from AI diffs by design; changed docs paths are reported to the AI as metadata). Not changed in this task.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/core.py | fix | `stage_files()` now returns `(success, message)` — captures git's stderr/stdout on failure instead of `check=True` swallowing it |
| src/ui/pr_publish_app.py | fix | `StageFilesScreen.btn_stage` reads the selection from `SelectionList.selected` (respects individual row toggles); removed stale manual-dict tracking and the in-TUI `git add` (staging now happens once in main.py); removed a stray "No files selected" notify and dead dict updates in the draft `FileStageScreen` class |
| src/main.py | fix | `check_unstaged_files()` checks the `stage_files()` result on all 3 call sites (TUI result, pr/issue auto-stage, commit auto-stage) and prints "❌ Failed to stage files: {error}" with the real git error when it fails |
| langs/pt_br.json | feat | Added translation for the new "❌ Failed to stage files: {error}" key |
| tests/test_core.py | test | Added `TestStageFiles` (4 tests): empty list, success, failure returning git error, exception path |

### Impact
- **Functionality:** Clicking "Stage Selected" now stages exactly the files the user selected in the modal (including files chosen via individual row toggles). When `git add` fails, the user sees the actual git error instead of a false success message. No more duplicate `git add` per run.
- **Performance:** No impact — one `git add` per flow instead of two.
- **Compatibility:** `stage_files()` return type changed from `bool` to `(bool, str)` — all call sites are internal (src/main.py, src/ui/pr_publish_app.py) and were updated. No external API change.

### Verification
- 214/214 tests pass (`pytest tests/`), including 4 new `stage_files` unit tests.
- Headless (Textual Pilot) modal scenarios:
  - Plain confirm → all files staged (`A` in `git status --porcelain`).
  - Deselect All → click row → Stage → only the clicked file staged; the other stays untracked (previously: nothing staged).
  - Deselect All → Stage → `[]`, no files staged, "⏭️ No files selected" message.
- `check_unstaged_files()` branch tests with mocked stage failures: success prints "✅ N file(s) added to stage.", failure prints "❌ Failed to stage files: fatal: pathspec ...", empty selection prints the localized "⏭️ Nenhum arquivo selecionado" message.
- `python run.py -h` and the local linter (`python run.py -l`) run clean.

### Next steps
- Add pt_br translations for the other language files served remotely (pt_pt, es_es, fr_fr) when the lang version next changes.
- Consider wiring the draft `FileStageScreen` class or deleting it — it duplicates `StageFilesScreen` and is currently dead code.
- If the user still reproduces a no-staging case in a real terminal, the new error output will now show the underlying `git add` failure (e.g., pathspec issues with special characters in file names) instead of a silent success.
