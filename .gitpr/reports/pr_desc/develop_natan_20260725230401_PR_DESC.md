# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add MCP annotations, prompt templates, and adaptive spinner
```

---

## 🎯 Summary

Enhance IDE integration and maintainability by adding MCP tool annotations for safer UI behavior, refactoring prompt messages into multilingual template files, and optimizing the spinner animation for long phrases. This release also synchronizes thinking words across all supported languages and bumps the version to 0.0.29.

## 🛠️ Technical Changes

- Added `ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`) to all 10 MCP tools for better client-side decisions
- Externalized prompt bodies into 35 template files (7 prompts × 5 languages) with language fallback, loaded via `_read_prompt_file()`
- Exposed prompt content as MCP resources (`prompt://` scheme) for raw template access
- Implemented adaptive spinner speed based on word length (fast reveal for long phrases)
- Merged thinking words from `words_happy.md`, synchronized all 5 language files to 201 entries each (no numbering)
- Updated `src/mcp_server.py` with `PROMPT_FILES` mapping, `_read_prompt_file()`, and `prompt://` resources
- Updated `src/spinner.py` with `_adaptive_speed()` and `_next_word()` methods
- Added 35 prompt template files under `templates/`, new documentation files (`mcp-annotations.md`, `mcp-prompts.md` and their translations)
- Updated all 5 README variants with new links and `--mcp` flag description
- Added new report (`relatorio_estado_v0.0.4.md`) and plan (`criar-mcp-prompts-adicionar-wondrous-wren.md`)
- Updated test suite with `CURRENT_LANG` mock and new prompt-specific tests
- Bumped version to 0.0.29 in `pyproject.toml`, `updater.py`, and `CLAUDE.md`

## ⚠️ Impact/Warnings

- **No breaking changes** – all prompt functions keep identical signatures; tool annotations are additive metadata.
- Prompt messages are now loaded from template files, allowing updates/translations without code changes.
- IDEs consuming MCP will receive annotation hints for smarter UI (confirmation dialogs, caching).
- Spinner animation for long phrases now reveals faster (from ~18s to ~2.2s).
- Thinking words format changed to plain text (no numbers), but parser already supports it.
- Requires `mcp.types.ToolAnnotations` import (already available in `mcp` >= 1.0.0).
- No new environment variables or database changes – `GITPR_LANG` is respected for prompt language selection.

close #66