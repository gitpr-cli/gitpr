# Completion Report — MCP docs sync (EN + 4 translations)

## What was done
- Compared `docs/mcp-integration.md` against `src/mcp_server.py` (MCP server implementation) and found:
  - 2 tools missing from the "Available Tools" table: `list_unstaged_files`, `analyze_unstaged_diff`
  - The `prompt://*` resources and built-in MCP prompts (`@mcp.prompt`) missing from the docs
- Compared the 4 translations (pt_br, pt_pt, es_es, fr_fr) against the English doc and found:
  - Missing `gitpr-mcp --install claude-code` line in the Quick Install block
  - Missing "Claude Code" editor-configuration section
- Added the 2 missing tools to the "Available Tools" table in all 5 docs
- Added a new "Prompt Resources" subsection (`prompt://*` URIs, plugin prompts, built-in MCP prompts) in all 5 docs
- Added the `claude-code` line and the "Claude Code" section to the 4 translations

## Changed files
| File | Change type | Description |
|------|-------------|-------------|
| docs/mcp-integration.md | docs | Added 2 missing tools + prompt resources section |
| docs/mcp-integration.pt_br.md | docs | Synced with EN + pt-BR translations of new content |
| docs/mcp-integration.pt_pt.md | docs | Synced with EN + pt-PT translations of new content |
| docs/mcp-integration.es_es.md | docs | Synced with EN + es-ES translations of new content |
| docs/mcp-integration.fr_fr.md | docs | Synced with EN + fr-FR translations of new content |

## Impact
- **Functionality:** None — documentation only, no code changes
- **Performance:** None
- **Compatibility:** None — all 5 docs now describe the same tool/resource/editor surface

## Next steps (if applicable)
- `src/mcp_server.py` argparse help for `--install` omits `claude-code` in its text ("vscode, cursor, claude, zed, or auto-detect") — consider updating the help string to include `claude-code`
- Consider documenting the hidden `gitpr --mcp` alias (src/main.py) in mcp-integration.md
