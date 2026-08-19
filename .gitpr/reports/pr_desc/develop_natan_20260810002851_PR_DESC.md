# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: add unstaged file checks, MCP tools, tests, and i18n support
```

---

## 🎯 Summary

This PR introduces a comprehensive unstaged file detection system to prevent accidental commits or PR publications with unintended changes. It adds new `core.py` functions to identify and categorize unstaged files, a `--no-unstaged-check` CLI flag, and MCP tools for external access. Broad localization updates support these features along with PR publishing options, plugin system, and more. Sample metrics export data is included for testing, and UI visibility has been improved.

## 🛠️ Technical Changes

- Added `get_unstaged_files`, `get_unstaged_categorized`, `get_unstaged_diff`, and `get_uncommitted_summary` in `core.py` to detect unstaged changes using `git status --porcelain`.
- Introduced `--no-unstaged-check` CLI flag in `main.py` to bypass unstaged verification during PR publication and status checks.
- Added MCP server tools `list_unstaged_files` and `analyze_unstaged_diff` for unstaged file inspection via the Model Context Protocol.
- Expanded unit tests (`test_core.py`, `test_mcp_server.py`) covering all new core and MCP functions, including edge cases and error handling.
- Refactored and extended localization files (`es.json`, `es_es.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`) with keys for unstaged checks, PR publishing (`--publish`, `--no-edit`), plugins, merge/auto-patch, and removed deprecated entries.
- Added sample metrics export files (CSV and JSON) in `.gitpr/metrics/export/` for demonstration and testing.
- Adjusted `max-height` from 6 to 16 in `pr_publish_app.css` for better content visibility.

## ⚠️ Impact/Warnings

- The unstaged file check is now **enabled by default**. Use `--no-unstaged-check` to skip it when needed.
- Localization files have been reorganized; existing translation customizations should be reviewed for compatibility.

close #100