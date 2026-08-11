## Completion Report — Add `--tool` CLI flag to gitpr-mcp

### What was done
- Added `--tool <name>` and `--tool-args <json>` CLI flags to `gitpr-mcp` for direct tool invocation without starting the MCP stdio server
- Extracted `_write_real_stdout()` helper to share real-stdout writing between `--list` and `--tool` modes
- Built `_TOOL_FUNCS` dict + `_get_tool_registry()` that merges the hand-maintained catalog with actual callables
- Added `_prettify_result()`, `_print_tool_help()`, and `_run_tool()` functions
- Updated `main()` with mutually exclusive group (`--list` | `--install` | `--tool`) and dispatch
- Added 75 unit tests (18 new) covering tool registry, tool invocation, error cases, and CLI integration
- Updated 15 documentation files (3 docs × 5 languages: EN, pt_BR, pt_PT, es_ES, fr_FR) with `--tool` usage sections
- Saved implementation plan to `docs/plans/2026-08-11_mcp-tool-cli-flag.md`

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/mcp_server.py` | feat | Added `_write_real_stdout()`, `_TOOL_FUNCS`, `_get_tool_registry()`, `_prettify_result()`, `_print_tool_help()`, `_run_tool()`, updated `main()` argparse and dispatch, updated module docstring |
| `tests/test_mcp_server.py` | test | Added 5 test classes: `TestWriteRealStdout`, `TestToolRegistry`, `TestPrettifyResult`, `TestRunTool` (9 tests), `TestMainCli` (3 tests) |
| `docs/mcp-integration.md` | docs | Added "Direct CLI Invocation" section |
| `docs/mcp-integration.pt_br.md` | docs | Added "Invocação Direta via CLI" section (translated) |
| `docs/mcp-integration.pt_pt.md` | docs | Same, European Portuguese |
| `docs/mcp-integration.es_es.md` | docs | Same, Spanish |
| `docs/mcp-integration.fr_fr.md` | docs | Same, French |
| `docs/mcp-annotations.md` | docs | Added "Direct CLI Invocation" section |
| `docs/mcp-annotations.pt_br.md` | docs | Added "Invocação Direta via CLI" (translated) |
| `docs/mcp-annotations.pt_pt.md` | docs | Same, European Portuguese |
| `docs/mcp-annotations.es_es.md` | docs | Same, Spanish |
| `docs/mcp-annotations.fr_fr.md` | docs | Same, French |
| `docs/mcp-prompts.md` | docs | Added "CLI Equivalents" section with prompt→tool mapping table |
| `docs/mcp-prompts.pt_br.md` | docs | Added "Equivalentes via CLI" (translated) |
| `docs/mcp-prompts.pt_pt.md` | docs | Same, European Portuguese |
| `docs/mcp-prompts.es_es.md` | docs | Same, Spanish |
| `docs/mcp-prompts.fr_fr.md` | docs | Same, French |
| `docs/plans/2026-08-11_mcp-tool-cli-flag.md` | docs | Implementation plan (saved from `.claude/plans/`) |

### Impact
- **Functionality:** Users can now invoke any of the 12 MCP tools directly from the CLI via `gitpr-mcp --tool <name> [--tool-args '<json>']`. Bare `gitpr-mcp --tool` lists all available tools with their parameter signatures. `.env` is loaded automatically so API keys work. JSON output goes to real stdout; all diagnostic messages go to stderr.
- **Performance:** No impact on server mode. `--tool` mode runs the tool and exits — no persistent process.
- **Compatibility:** Fully backward-compatible. `--list`, `--install`, and server mode unchanged. The `_run_list()` function was refactored to use the new `_write_real_stdout()` helper but behavior is identical.

### Verification
- `gitpr-mcp --tool` → prints help listing with all 12 tools
- `gitpr-mcp --tool get_git_context` → `{"branch": "develop_natan", "repository": "natanfiuza/gitpr"}`
- `gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"src/mcp_server.py","start_line":"270","end_line":"284"}'` → returns blame analysis JSON
- `gitpr-mcp --tool invalid` → JSON error + help listing, exit 1
- `gitpr-mcp --tool analyze_blame` (missing args) → error about missing file_path
- `gitpr-mcp --list` → unchanged, prints full catalog
- `python -m pytest tests/test_mcp_server.py tests/test_core.py -v` → **94/94 passed**

### Next steps
- Consider adding shell completion for `--tool` names (the 12 tool names could be auto-completed)
- Update `README.md` and `README.pt_br.md` with `--tool` usage examples (if desired)
