# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
refactor: externalize MCP prompts to template files
```

---

## 🎯 Summary

Refactor the MCP prompt system to load prompt messages from external template files with multi-language support (English, Brazilian Portuguese, European Portuguese, Spanish, French). This change allows prompt content to be updated and translated independently of the Python code, and exposes the templates as MCP resources (`prompt://...`) for direct access by AI editors.

## 🛠️ Technical Changes

- Added 35 prompt template files under `templates/gitpr.prompt.<name>.<lang>.md` (7 prompts × 5 languages).
- Introduced `PROMPT_FILES` dictionary and `_read_prompt_file()` function in `src/mcp_server.py` to load prompt content with language fallback based on `GITPR_LANG`.
- Refactored all 7 MCP prompt functions (`review`, `commit`, `pr`, `linter`, `issue`, `blame`, `explore`) to return content from template files instead of hardcoded strings.
- Added `prompt://list` resource and individual `prompt://<name>` resources to expose raw prompt templates.
- Updated `docs/mcp-prompts.md` to document the new template-based design and resources.
- Updated `README.md` to reflect the prompt count and add a link to the new `docs/mcp-prompts.md`.
- Added a new plan document `docs/plans/criar-mcp-prompts-adicionar-wondrous-wren.md` detailing the implementation steps.
- Adapted `tests/test_mcp_prompts.py` to work with the externalized templates, patching `CURRENT_LANG` for deterministic English output and adding tests for `PROMPT_FILES` and `_read_prompt_file`.

## ⚠️ Impact/Warnings

- Prompt messages are now language-sensitive: the content returned depends on the `GITPR_LANG` environment variable (or system locale). Previously, translations were done via `__()` calls; now they are file-based.
- New MCP resources (`prompt://*`) are available to editors supporting MCP; ensure your client can handle them.
- Deployment note: The `templates/` directory must be present and accessible (bundled with the package or installed via `--skill`). No database or environment variable changes beyond the existing `GITPR_LANG` usage.

close #64