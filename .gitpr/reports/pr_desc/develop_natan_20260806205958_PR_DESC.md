# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
refactor: centralize report output paths under .gitpr/reports
```

---

## 🎯 Summary

This change centralizes the storage of generated reports (PR descriptions, reviews, blame analyses, issues) into organized subfolders under `.gitpr/reports/`, instead of scattering them in the project root. It also adds Portuguese translations for the smart documentation exclusion feature and includes a temporary script for i18n coverage checks.

## 🛠️ Technical Changes

- Added `.gitpr/reports/` to `.gitignore` to prevent generated reports from being committed.
- Introduced `resolve_output_path()` in `src/core.py` with a mapping from environment variables to dedicated subfolders (e.g., `pr_desc`, `review`, `blame`, `issue`).
- Updated `src/main.py`, `src/blame_engine.py`, and `src/ui/issue_app.py` to use the new centralized function, removing duplicated path formatting logic.
- Expanded `langs/pt_br.json` with translation keys for smart excludes, telemetry summary, and help options.
- Added `scripts/_temp_check_i18n.py` to verify translation coverage of `__()` calls in `main.py`.
- Extended `tests/sync_i18n.py` to include `es.json` and `fr.json` when synchronizing language files.

## ⚠️ Impact/Warnings

- **Default output location changed:** All generated files now go under `.gitpr/reports/<action>/` by default, which may affect existing scripts or workflows expecting files in the project root.
- **Custom paths preserved:** If an environment variable (e.g., `OUTPUT_FILE_NAME`) contains a directory separator (`/` or `\`), the original value is used without modification, ensuring backward compatibility.
- **New translation keys:** No breaking changes for other languages, but they will need similar updates for full coverage.

close #88