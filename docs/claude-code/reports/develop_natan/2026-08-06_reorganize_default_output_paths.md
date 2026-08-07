## Completion Report — Reorganize Default Output Paths to .gitpr/reports/

### What was done
- Created a centralized `resolve_output_path()` helper function in `src/core.py` that resolves the output file path for all artifact types (PR, review, full review, file review, blame, issue).
- The function respects three scenarios per the plan: (1) env var contains a directory separator → use as-is, (2) env var contains only a filename → save in `.gitpr/reports/{folder}/`, (3) env var is empty → use default pattern in `.gitpr/reports/{folder}/`.
- Automatically creates the target directories via `os.makedirs(exist_ok=True)`.
- Updated all 4 call sites (main.py, blame_engine.py, issue_app.py) to use the new helper, eliminating duplicated `os.getenv` + `.format()` logic.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| [src/core.py](src/core.py) | feat | Added `_OUTPUT_FOLDER_MAP` dict and `resolve_output_path()` function |
| [src/main.py](src/main.py) | refactor | Import `resolve_output_path`; replace 2 duplicated output-path blocks (reviews + PR description) with calls to the helper |
| [src/blame_engine.py](src/blame_engine.py) | refactor | Import `resolve_output_path`; replace blame output path logic with helper call |
| [src/ui/issue_app.py](src/ui/issue_app.py) | refactor | Import `resolve_output_path`; replace issue save path logic with helper call; removed unused `os` import |

### Folder mapping implemented
| Env var | Subfolder in `.gitpr/reports/` |
|---------|-------------------------------|
| `OUTPUT_FILE_NAME` | `pr_desc` |
| `OUTPUT_FILE_NAME_REVIEW` | `review` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `full_review` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `file_review` |
| `OUTPUT_FILE_NAME_BLAME` | `blame` |
| `OUTPUT_FILE_NAME_ISSUE` | `issue` |

### Impact
- **Functionality:** Output files are now saved in `.gitpr/reports/{type}/` by default instead of the project root. Users with custom directory paths in their `.env` keep their existing behavior — full backwards compatibility.
- **Performance:** Negligible — one extra `os.makedirs(exist_ok=True)` per invocation, which is a no-op after the first run.
- **Compatibility:** No API breaks. All 6 env vars continue to work. Custom paths with directories are honored as-is. Only bare filenames get the new `.gitpr/reports/` prefix.

### Verification
- **Tests:** 130/131 tests pass. The single failure (`test_api_exception` i18n mismatch) is pre-existing and unrelated to this change.
- **Smoke test:** Import succeeds. `resolve_output_path()` correctly handles: custom directory paths, plain filenames (→ `.gitpr/reports/{folder}/`), empty env vars (→ default pattern in reports folder), and Windows backslash paths.
