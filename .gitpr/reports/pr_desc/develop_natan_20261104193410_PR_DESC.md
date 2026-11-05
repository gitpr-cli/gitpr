# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add Smart Excludes section with project exclusion editor
```

---

## 🎯 Summary

The existing "Diff Filters" section only exposed flat, global environment-based paths, giving users no way to maintain project-specific exclusion rules. This change introduces a dedicated **Smart Excludes** section that surfaces three clearly separated exclusion sources (project, global core, global docs) and lets users create and edit a project-scoped exclusion file directly from the TUI. The goal is to make exclusion management self-service, discoverable, and version-friendly without forcing manual JSON edits.

## 🛠️ Technical Changes

- Rename the `diff` config category to `smart_excludes` and update its label/description in `src/config_schema.py`.
- Move the `SMART_EXCLUDES_VERSION` field from the `advanced` `downloads` group into the new `smart_excludes` category.
- Add core helpers in `src/core.py` to resolve and read/write exclusion files:
  - `get_project_smart_excludes_path`, `get_global_smart_excludes_path`, `get_global_docs_smart_excludes_path`
  - `load_raw_project_excludes_text`, `save_project_excludes_text`
  - `load_global_core_excludes_text`, `load_global_docs_excludes_text` (with fallback lists)
- Build a new Smart Excludes pane in `src/ui/config_app.py` with a source `ListView`, a `TextArea` editor, a create-file button, status/note widgets, and dirty-state tracking.
- Integrate exclusions into the dirty indicator, discard-confirmation flow, save plan, and `_after_save` reporting (F2 saves the project file).
- Add translations for all new strings in `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, and `pt_pt`, and remove the obsolete `Diff Filters` keys.
- Add tests for the new UI section, schema category, and i18n identity terms.

## ⚠️ Impact/Warnings

- **Environment variables:** Honors `GITPR_SMART_EXCLUDES_LOCAL` and `GITPR_SMART_EXCLUDES_GLOBAL` path overrides; defaults to `.gitpr/conf/gitpr.smart-excludes.json` (project) and `~/.gitpr/conf/` (global).
- **File I/O / On-disk format:** Introduces a new JSON exclusion file (`_comment` + `excludes` array). Existing files are read defensively; malformed files silently fall back to empty/fallback lists.
- **Config category migration:** The `diff` category key is removed in favor of `smart_excludes`; any external references or saved user state keyed on `diff` must be updated.
- **Documentation/dependencies:** No new runtime dependencies. New docs (`docs/smart-excludes.*.md`) accompany the change.

close #263

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)