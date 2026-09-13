# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: enforce mandatory PyPI update gate and drop binary support
```

---

## 🎯 Summary

GitPR drops the standalone PyInstaller binary distribution and adopts a PyPI-only update model. Instead of downloading and hot-swapping an executable at runtime, the tool now verifies at startup whether a newer version is published on PyPI and, if so, blocks execution until the user runs `pip install --upgrade gitpr-cli`. This guarantees that users always run a published, supported build and eliminates the complexity of maintaining a parallel binary release pipeline (GitHub Releases + hot-swap/rollback).

## 🛠️ Technical Changes

- Rewrite `src/updater.py` around a single PyPI source of truth: remove the GitHub Releases API lookup, the asset/download-URL resolution, the `_perform_hot_swap` routine and `print_update_notice`.
- Add `enforce_update_required()`: returns `True` and prints the upgrade instructions when the published PyPI version is newer than the local `__version__`; returns `False` when up to date, when the remote version is unknown (offline) or when the check is disabled.
- Keep `check_and_update()` for the `--update` flag, but it now only reports the version diff and the `pip install --upgrade gitpr-cli` command.
- Wire the mandatory gate at the beginning of `cli()` in `src/main.py`, skipping internal/utility invocations (`--quiet`, `--hook`, `--mcp`, `--update`, `-h/--help`) and exiting with code 1 when outdated.
- Remove every legacy `print_update_notice()` call site and the old `.old` executable cleanup logic from `src/main.py`.
- Introduce the `GITPR_SKIP_UPDATE_CHECK` environment switch so test harnesses and offline automation can mute the gate.
- Remove the `pyinstaller` dev dependency from `Pipfile` and delete `icon.ico` (no longer needed without a compiled binary).
- Update the `.gitignore` comment to reflect generic build artifacts instead of PyInstaller output.
- Refresh i18n dictionaries (`es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt`): drop obsolete update/binary strings, add the new PyPI-gate keys, and translate previously untranslated entries; update `scripts/sync_all_langs.py` and `scripts/fix_mangled_i18n_keys.py` accordingly.
- Add `tests/test_updater.py` covering version parsing, daily cache behaviour, PyPI fetch, gate decisions and CLI wiring; set `GITPR_SKIP_UPDATE_CHECK=true` in `tests/conftest.py`; adjust `tests/test_i18n.py` `CLEAN_KEYS` from 50 to 49.

## ⚠️ Impact/Warnings

- **BREAKING CHANGE**: the standalone binary distribution (GitHub Releases / `gitpr.exe`) and its hot-swap update flow are removed. Binary users must migrate to `pip install --upgrade gitpr-cli`.
- **Behavioural change**: an outdated installation now aborts with exit code 1 before doing any work. Runs with no network connectivity are *not* blocked, since the remote version cannot be determined.
- **New environment variable**: `GITPR_SKIP_UPDATE_CHECK` (any non-empty value disables the mandatory check). Required by the test suite and useful for offline automation.
- **Dependency removed**: `pyinstaller` (dev-only). The daily update cache no longer stores a `download_url` field.

close #164