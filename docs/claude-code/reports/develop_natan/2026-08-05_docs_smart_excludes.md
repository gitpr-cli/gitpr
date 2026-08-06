## Completion Report — Docs Smart Excludes (Exclude documentation from git diff)

### What was done
- Verified that `SMART_EXCLUDES` is already applied consistently in all `git diff` calls across the codebase (both `get_git_diff()` and `get_git_full_diff()` use it). No fixes needed.
- Created new remote-managed template `templates/gitpr.docs-smart-excludes.json` with 25 documentation file extensions (`.md`, `.txt`, `.rst`, `.adoc`, `.asciidoc`, `.org`, `.textile`, `.wiki`, `.pod`, `.tex`, `.rtf`, `.markdown`, `.rdoc`, `.mdx`, `.rest`, `.man`, `.1`–`.8`).
- Implemented `_load_docs_smart_excludes()` in `src/core.py` — follows the same 4-layer resolution chain as `_load_smart_excludes()` (local cache → download → stale local → fallback constant), sharing the `SMART_EXCLUDES_VERSION` marker.
- Implemented `_get_raw_docs_patterns()` — returns plain glob patterns (without `:(exclude)` prefix) for fnmatch filtering.
- Implemented `get_changed_docs_list(ancestor_hash=None)` — runs `git diff --name-only` and filters results by doc extensions, returning only changed documentation file paths (no content).
- Merged doc excludes into the global `SMART_EXCLUDES` at module level: `SMART_EXCLUDES = _load_smart_excludes() + _load_docs_smart_excludes()`.
- Modified `generate_pr_content()` to inject the changed documentation list as metadata into the AI system instruction (prepended before the skill context), so the AI knows which docs changed without consuming tokens on their full content.
- Added 9 new unit tests covering `_load_docs_smart_excludes`, `_get_raw_docs_patterns`, and `get_changed_docs_list` (all passing).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `templates/gitpr.docs-smart-excludes.json` | feat | New remote template listing 25 documentation file extensions to exclude from diffs |
| `src/core.py` | feat | Added `fnmatch` import, `_FALLBACK_DOCS_SMART_EXCLUDES`, `DOCS_SMART_EXCLUDES_URL`, `_load_docs_smart_excludes()`, `_get_raw_docs_patterns()`, `get_changed_docs_list()`; merged doc excludes into `SMART_EXCLUDES`; injected changed docs metadata into system_instruction in `generate_pr_content()` |
| `tests/test_smart_excludes.py` | test | Added 9 new tests (3 test classes): `TestLoadDocsSmartExcludes` (4), `TestGetRawDocsPatterns` (2), `TestGetChangedDocsList` (3) |

### Impact
- **Functionality:** Documentation files (`.md`, `.txt`, `.rst`, etc.) are now excluded from `git diff` content sent to AI, significantly reducing token consumption. The AI still receives a metadata list of which documentation files changed — maintaining traceability without the token cost.
- **Performance:** Fewer tokens consumed per AI call when documentation files are part of the diff. The metadata injection is a fast local git operation (`git diff --name-only` + fnmatch filter) wrapped in try/except.
- **Compatibility:** No API breaks. `SMART_EXCLUDES` keeps its name and format (list of `:(exclude)*.ext` pathspecs). New functions are internal. The new template is remote-managed — available after merge to `main`. Until then, the `_FALLBACK_DOCS_SMART_EXCLUDES` constant serves as the built-in default.

### Next steps (if applicable)
- After merging to `main`, bump `__lang_version__` in `src/updater.py` so installed clients download the new `gitpr.docs-smart-excludes.json` template.
- Update `templates/gitpr.smart-excludes.json` on `main` to add any missing patterns (currently 35 entries). The two JSON files are independent but share the same version marker.
- Consider adding the `gitpr.docs-smart-excludes.json` URL to the `--skill` download list in `generate_skill_template()` so users can get it locally.
