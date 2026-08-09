## Completion Report — Reorganização do Fluxo de Verificação de Unstaged Files

### What was done

Implemented the plan `docs/plans/20260808_correcoes_ustaged_files_interface.md` which moves the unstaged files check from the F3 publish flow to the beginning of `gitpr` execution, isolates it in a standalone TUI, and removes the duplicate check during publication.

1. **Moved `get_unstaged_files()` to `core.py`** as a reusable utility, along with `stage_files()` for batch `git add`.
2. **Created `StageFilesApp`** — a minimal standalone Textual app that shows only the `FileStageScreen` modal, runs before PR generation, and returns the result to the CLI.
3. **Added startup check in `main.py`** — after the banner but before PR generation, checks for unstaged files. If found and `GITPR_SKIP_UNSTAGED_CHECK` is false, opens `StageFilesApp`. Handles cancel (abort), stage (git add + proceed), and skip (proceed without staging).
4. **Removed duplicate check** from the F3 auto-commit flow in `PrPublishApp` — `_check_unstaged_files()`, `_on_file_stage_result()`, and `_stage_files()` removed. `_on_commit_confirm` now goes directly to `_start_progress_and_commit()`.
5. **New env var**: `GITPR_SKIP_UNSTAGED_CHECK` (skip the entire unstaged check at startup).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/core.py` | feat | Added `get_unstaged_files()` and `stage_files()` public functions |
| `src/config.py` | feat | Added `GITPR_SKIP_UNSTAGED_CHECK` to DEFAULT_CONFIG |
| `src/main.py` | feat | Added unstaged files check at startup (default PR flow) with TUI launch |
| `src/ui/pr_publish_app.py` | refactor | Removed `_get_unstaged_files()` module function (moved to core); added `StageFilesApp` class; removed `_check_unstaged_files`, `_on_file_stage_result`, `_stage_files` from `PrPublishApp`; `_on_commit_confirm` now calls `_start_progress_and_commit()` directly |
| `langs/pt_br.json` | feat | 10 new i18n keys |
| `langs/pt_pt.json` | feat | Same — PT-PT |
| `langs/es_es.json` | feat | Same — ES |
| `langs/fr_fr.json` | feat | Same — FR |
| `docs/pull-request-publication.md` | update | Added `GITPR_AUTO_STAGE` and `GITPR_SKIP_UNSTAGED_CHECK` to env vars table |
| `docs/pull-request-publication.pt_br.md` | update | Same |
| `docs/pull-request-publication.pt_pt.md` | update | Same |
| `docs/pull-request-publication.es_es.md` | update | Same |
| `docs/pull-request-publication.fr_fr.md` | update | Same |

### New flow

```
gitpr
  ├─ Banner
  ├─ Unstaged files check (NEW — before PR generation)
  │   ├─ GITPR_SKIP_UNSTAGED_CHECK=true → skip
  │   ├─ No unstaged files → proceed
  │   ├─ GITPR_AUTO_STAGE=true → auto git add → proceed
  │   └─ Has unstaged files → StageFilesApp TUI
  │       ├─ Stage Selected → git add → proceed
  │       ├─ Skip → proceed (no staging)
  │       └─ Cancel → abort
  ├─ PR generation (AI) → .md file
  └─ TUI (default) or --no-publish / --no-edit
      └─ F3 Publish PR → auto-commit (no duplicate unstaged check)
```

### Verification

- 130/131 tests pass (1 pre-existing i18n issue in test_chat_backend)
- `main.py` and `pr_publish_app.py` import cleanly
- New `get_unstaged_files()` and `stage_files()` in `core.py` are importable
