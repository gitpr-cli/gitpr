## Completion Report — Linter report only written when violations exist

### What was done
- The linter Markdown report (`.gitpr/reports/linter/`) was being written unconditionally on every `gitpr -l` run, even when the diff had no violations. Now the report file is only created when there is at least one warning or error.
- Wrapped the report generation/save block in `if has_warnings or has_errors:` in the `linter` command flow.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/main.py | fix | Guarded linter report save behind `has_warnings or has_errors` |

### Impact
- **Functionality:** Running `gitpr -l` on a clean diff (or one with no rule matches) no longer creates `.gitpr/reports/linter/*_LINTER.md`. The terminal output ("✅ Clean code!") is unchanged, as are the TUI (blocking errors), warning display, and fire-and-forget metrics.
- **Performance:** Negligible — avoids one file write per clean run.
- **Compatibility:** No API breaks. Report filename/content format unchanged when violations exist.

### Next steps (if applicable)
- None.
