## Completion Report — Binary Diff Safeguard and Smart Excludes Expansion

### What was done
- Expanded `templates/gitpr.smart-excludes.json` from 35 to 155 patterns, adding all 8 families of real-world binary assets (images/design, Office/PDF documents, archives/packages/disk images, fonts, audio/video, compiled binaries/libraries/bytecode, databases/datasets/ML weights/raw binary, and binary certificates/keystores).
- Synchronized `_FALLBACK_SMART_EXCLUDES` in `src/core.py` in 1:1 parity with `templates/gitpr.smart-excludes.json` and added an automated parity test in `tests/test_smart_excludes.py`.
- Bumped `__lang_version__` from `"v0.0.38"` to `"v0.0.39"` in `src/updater.py` so global cached Smart Excludes update automatically on the next run.
- Implemented the **Binary hunk guard** (`collapse_binary_hunks`) in `src/diff_parser.py`, which inspects unified diff sections with hunks and collapses any section whose hunk content lines contain a contiguous run of `>= 8` `U+FFFD` characters or `>= 32` total `U+FFFD` characters with `>= 10%` hunk density into a standard `Binary files a/<path> and b/<path> differ` marker, while preserving legitimate non-UTF-8 legacy source files (e.g., Latin-1 / Windows-1252) byte-for-byte.
- Wired `collapse_binary_hunks` across all analysis diff capture paths (`get_git_diff`, `get_git_staged_diff`, `get_unstaged_diff`, `get_git_full_diff`, `get_check_diff`, `current_diff`, `filter_excluded_sections` for remote PR diffs, and direct `git diff` calls in `src/main.py` for `tests --file` and `risk --base`), while keeping `get_split_diff` untouched for `gitpr split`.
- Updated `CONTEXT.md` (updated **Smart Excludes** definition and added **Binary hunk guard**) and localized documentation (`docs/smart-excludes*.md` in EN, PT-BR, PT-PT, ES-ES, FR-FR).
- Added unit and real-repository integration tests in `tests/test_smart_excludes.py` and `tests/test_full_diff_encoding.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `CONTEXT.md` | docs | Updated `Smart Excludes` definition and added `Binary hunk guard` to domain glossary |
| `templates/gitpr.smart-excludes.json` | feat | Added 8 categories of binary file extensions to Core Exclusions |
| `src/updater.py` | chore | Bumped `__lang_version__` to `"v0.0.39"` |
| `src/diff_parser.py` | feat | Implemented `collapse_binary_hunks` and binary `U+FFFD` detection thresholds |
| `src/review/diff_normalizer.py` | feat | Applied `collapse_binary_hunks` in `filter_excluded_sections` for remote PR diffs |
| `src/core.py` | feat | Synced `_FALLBACK_SMART_EXCLUDES` 1:1 with template and applied `collapse_binary_hunks` in diff getters |
| `src/main.py` | feat | Applied `collapse_binary_hunks` to direct `git diff` calls in `tests --file` and `risk --base` |
| `src/application/use_cases/create_baseline.py` | feat | Applied `collapse_binary_hunks` to `current_diff(base=...)` |
| `src/application/use_cases/run_check.py` | feat | Applied `collapse_binary_hunks` to `get_check_diff` |
| `docs/smart-excludes.md` (+ `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) | docs | Documented binary asset categories and the Binary Hunk Guard |
| `tests/test_smart_excludes.py` | test | Added 1:1 template parity test and 8-category binary extension coverage test |
| `tests/test_full_diff_encoding.py` | test | Added real-git integration and unit tests for `collapse_binary_hunks` and binary pathspecs |

### Impact
- **Functionality:** Binary files with known extensions are excluded directly at the `git diff` pathspec level, and custom/unknown-extension binary files that Git diffs as text have their `U+FFFD` hunks collapsed into a standard `Binary files ... differ` marker without affecting legacy Latin-1 source code.
- **Performance:** Eliminates token waste and avoids sending massive `U+FFFD` streams to AI providers on repositories containing large binary assets or custom binary blobs; fast-paths in $O(1)$ when no `U+FFFD` is present.
- **Compatibility:** Fully backwards-compatible; `get_split_diff()` (`gitpr split --binary`) and legitimate Latin-1 source diffs remain untouched.

### Next steps (if applicable)
- None.
