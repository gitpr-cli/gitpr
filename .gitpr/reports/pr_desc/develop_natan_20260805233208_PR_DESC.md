# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: exclude doc files from diff, report as metadata
```

---

## 🎯 Summary

This PR introduces documentation file exclusions to reduce token usage while still informing the AI which docs were changed. Instead of sending full prose/markup content, only a list of changed documentation files is appended as metadata, ensuring the AI has context without consuming excessive tokens.

## 🛠️ Technical Changes

- Added `_load_docs_smart_excludes()` to load documentation exclusion patterns with the same remote/local resolution chain as existing smart excludes.
- Added `_get_raw_docs_patterns()` to obtain plain glob patterns for documentation files.
- Added `get_changed_docs_list()` to retrieve changed documentation file paths via `git diff --name-only` filtered by the patterns.
- Merged documentation exclusions into the main `SMART_EXCLUDES` list so they are applied during diff generation.
- In `generate_pr_content()`, injected the list of changed documentation files as a metadata prefix in the system instruction when available.
- Added a new template `gitpr.docs-smart-excludes.json` containing default documentation file extensions to ignore.
- Added comprehensive tests covering all resolution paths and the new functions.

## ⚠️ Impact/Warnings

- The `SMART_EXCLUDES` variable now includes both code and documentation patterns, which may increase the number of files excluded from the diff. Ensure the updated remote template is accessible to avoid fallback to built‑in defaults.
- The feature relies on the same version tracking (`SMART_EXCLUDES_VERSION`) as existing smart excludes; no new environment variables are introduced.

close #84