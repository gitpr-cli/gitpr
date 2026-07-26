## Completion Report — MCP Prompts Refactoring + Tool Annotations + Thinking Words Sync + Spinner Adaptive Speed

### What was done

This session implemented four interconnected improvements to the GitPR CLI:

1. **MCP Prompts — Template-Based Refactoring:** Externalized all 7 MCP prompt
   bodies from hardcoded Python strings into 35 language-specific template files
   (7 prompts × 5 languages) in `templates/`. Added `prompt://` resources (8 new
   MCP resources) and a `_read_prompt_file()` function with language fallback.
   Prompt content can now be updated/translated independently of Python code.

2. **MCP Tool Annotations:** Added `ToolAnnotations` (`readOnlyHint`,
   `destructiveHint`, `idempotentHint`) to all 10 MCP tools via the
   `@mcp.tool(annotations=...)` parameter. Classified 3 tools as read-only
   (`get_git_context`, `analyze_diff`, `run_linter`) and 7 as non-read-only
   with network side effects. All tools marked `destructiveHint=False` since
   GitPR never writes files.

3. **Thinking Words Sync (5 languages):** Synchronized `templates/gitpr.thinking-words.md`
   across all 5 languages. Merged 84 original entries + 117 phrases from
   `docs/plans/words_happy.md` without dedup (total 201 entries per language).
   Removed numbering — one word/phrase per line. All 5 files now have exactly
   201 lines.

4. **Spinner Adaptive Speed:** Modified `src/spinner.py` to speed up character
   reveal animation for long phrases. Added `_adaptive_speed()` method that
   calculates `chars_per_letter` and `sleep_time` based on word length:
   ≤15 chars → original speed (4 frames/letter, 0.08s), 16-35 chars → moderate
   (2 frames, 0.06s), 36+ chars → fast (1 frame, 0.04s). Long phrases now
   reveal in ~2.2s instead of ~18s.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/mcp_server.py` | refactor | Added `PROMPT_FILES` dict, `_read_prompt_file()`, refactored 7 `@mcp.prompt()` functions, added 8 `prompt://` resources, imported `CURRENT_LANG` |
| `src/mcp_server.py` | feat | Added `ToolAnnotations` to all 10 `@mcp.tool()` decorators (import from `mcp.types`) |
| `src/spinner.py` | feat | Added `_adaptive_speed()` and `_next_word()` methods; dynamic `chars_per_letter` + `sleep_time` per word |
| `templates/gitpr.prompt.*.md` (35 files) | new | 7 prompts × 5 languages (EN, PT-BR, PT-PT, ES, FR) |
| `templates/gitpr.thinking-words.md` | sync | 83 → 201 entries (merged with words_happy.md, no numbers) |
| `templates/gitpr.thinking-words.{pt_br,pt_pt,es_es,fr_fr}.md` | sync | 53 → 201 entries each (previous sync + words_happy translations) |
| `tests/test_mcp_prompts.py` | refactor | Added `CURRENT_LANG` mock, 4 new tests (`PROMPT_FILES`, `_read_prompt_file()`) |
| `docs/mcp-prompts.md` | update | Documented template-based loading, `prompt://` resources table |
| `docs/mcp-prompts.{pt_br,pt_pt,es_es,fr_fr}.md` | update | 4 translated variants synced with EN content |
| `docs/mcp-annotations.md` | new | EN documentation for tool annotations |
| `docs/mcp-annotations.{pt_br,pt_pt,es_es,fr_fr}.md` | new | 4 translated variants |
| `docs/plans/words_happy.md` | reference | Source of 117 phrases merged into thinking words |
| `README.md` | update | Updated `--mcp` flag description, added MCP Prompts + Annotations doc links |

### Impact

- **Functionality:** MCP prompts now load from template files with language
  fallback — translations can be updated without touching Python code. IDEs
  receive tool annotations for smarter UI behavior (confirmation dialogs, caching).
  Thinking words spinner can now display both single words and full phrases in
  any of 5 languages. Long phrases animate at adaptive speed instead of taking
  ~18 seconds to reveal.

- **Performance:** Spinner animation for long phrases improved from ~18s to
  ~2.2s reveal time. No impact on other operations. MCP startup unchanged.

- **Compatibility:** No API breaks. All existing `@mcp.prompt()` decorators
  keep identical `name=` and `description=` parameters. Prompt body loading
  is transparent — same prompt names, same behavior. Tool annotations are
  purely additive metadata. Thinking words format changed from numbered to
  plain text — `_load_thinking_words()` parser already supports this format.
  Spinner method signatures unchanged.

### Next steps

- [ ] Translate the 4 README variants (pt_br, pt_pt, es_es, fr_fr) with the
  new MCP Prompts and MCP Annotations doc links
- [ ] Consider adding a `prompt://` URI to the MCP config installer
  (`--install`) so editors can auto-discover prompt templates
- [ ] Consider extending the spinner to show a different animation style for
  phrases vs single words (e.g., typewriter effect for phrases)
