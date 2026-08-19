# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: add project-local smart excludes support and UI overflow fix
```

---

## 🎯 Summary

Introduce project-local smart excludes to allow per-project AI diff exclusions alongside global defaults. The global list continues to be managed in `~/.gitpr/conf/gitpr.smart-excludes.json`, while a new optional project file at `.gitpr/conf/gitpr.smart-excludes.json` can be created automatically (idempotent). Environment variables `GITPR_SMART_EXCLUDES_GLOBAL` and `GITPR_SMART_EXCLUDES_LOCAL` override file paths, and `GITPR_SKIP_SMART_EXCLUDES` disables all excludes. Additionally, fix overflow styling in staging screens to prevent content clipping.

## 🛠️ Technical Changes

- Add `_seed_local_smart_excludes()` to create a template project-local excludes file (best-effort, never overwrites user config).
- Refactor `_load_smart_excludes()` to support:
  - Global skip via `GITPR_SKIP_SMART_EXCLUDES`.
  - Override paths via `GITPR_SMART_EXCLUDES_GLOBAL` / `GITPR_SMART_EXCLUDES_LOCAL`.
  - Merge global and local exclude patterns (union) with deduplication.
  - Download and update logic adjusted to use `global_file` variable.
- Apply same skip logic to `_load_docs_smart_excludes()`.
- Add `.gitpr/conf/gitpr.smart-excludes.json` (template) to repository.
- Modify `StageFilesScreen` and `FileStageScreen` CSS: fix overflow and height to prevent content overflow, replacing `max-height: 16; height: auto` with `height: 6;`.

## ⚠️ Impact/Warnings

- New environment variables added; should be documented for users.
- Project-local excludes file is seeded automatically but not deleted – manual cleanup if needed.
- UI changes may affect interactive TUI layout; test on various terminal sizes.
- No database or dependency changes.