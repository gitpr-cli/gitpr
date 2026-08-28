## Completion Report — MCP Server Section in CLAUDE.md

### What was done
- Ran `gitpr-mcp --list` to enumerate the full MCP registry (12 tools, 16 resources, 7 prompts)
- Added a new "### MCP Server (IDE/agent integration)" subsection to CLAUDE.md under "Project-specific notes"
- Documented the entry points (`gitpr-mcp` / `--mcp`, `gitpr-mcp --list`, `gitpr-mcp --tool <name>`), runtime details (stdout monkey-patch isolation, `anyio` offload thread), the tools table, resources, and prompts

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| CLAUDE.md | docs | Added MCP Server subsection with tools/resources/prompts registry |

### Impact
- **Functionality:** None — documentation only
- **Performance:** None
- **Compatibility:** None

### Next steps (if applicable)
- Keep the tools table in sync when new MCP tools are added (regenerate with `gitpr-mcp --list`)
- Consider mirroring the section in GEMINI.md if that file should stay equivalent
