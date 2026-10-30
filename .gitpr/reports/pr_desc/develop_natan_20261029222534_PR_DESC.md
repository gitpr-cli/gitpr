# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: auto-close commit progress screen after successful commit
```

---

## 🎯 Summary

Previously, after a successful commit the CLI returned silently and the TUI kept the user on the progress screen until they manually clicked **Close**. This change streamlines that flow: on a successful commit the progress screen marks the run as finished and automatically exits after a short delay, while the CLI now explicitly reports the new `committed` result with a success message and the captured commit output.

This removes a redundant manual step and gives consistent, visible feedback in both the interactive and headless CLI paths.

## 🛠️ Technical Changes

- Added handling for the new `app.result == "committed"` state in `src/main.py`, printing a success message and the trimmed commit output before returning.
- Updated `CommitApp` (`src/ui/commit_app.py`) to call `log.mark_finished(False)` and schedule `_schedule_auto_exit` on successful commit.
- Added `_schedule_auto_exit()` which registers a 0.6s timer to `self.exit`, closing the progress screen without user interaction.
- Bumped `__version__` to `1.4.4` and `__lang_version__` to `v0.0.36` in `src/updater.py`.
- Updated tests: unit test now asserts `_schedule_auto_exit` is invoked, a new test verifies the timer is registered with `(0.6, app.exit)`, and the headless flow test waits for `app.result == "committed"` instead of clicking `#btn_close`.

## ⚠️ Impact/Warnings

- **UX behavior change:** the commit progress screen now closes automatically; the `#btn_close` interaction is no longer part of the success path.
- **Version bump:** `1.4.3` → `1.4.4` and language dictionary `v0.0.35` → `v0.0.36`; the updater may trigger an update prompt and requires the corresponding language pack to exist.
- No database, API, or environment variable changes.

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)