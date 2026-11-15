## Completion Report — Stage 7: Include `claude-code` in `--install` error message and sync i18n

### What was done
- Updated the unknown-editor error message in `_install_for_editor` (`src/mcp_server.py`) to include `claude-code` in the same order as `--install` `choices`: `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude-code, claude, zed, auto"`.
- Synchronized the new key and translated values across all 6 CLI language dictionaries in `langs/` (`pt_br.json`, `pt_pt.json`, `es.json`, `es_es.json`, `fr.json`, `fr_fr.json`).
- Added unit test `TestInstallConfigDescriptions.test_install_for_unknown_editor_lists_all_valid_options` in `tests/test_mcp_server.py`.
- Marked Stage 7 (`P7`) as completed in `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/mcp_server.py` | fix | Included `claude-code` in `_install_for_editor` unknown-editor message |
| `langs/pt_br.json` | fix | Updated unknown-editor key and PT-BR translation |
| `langs/pt_pt.json` | fix | Updated unknown-editor key and PT-PT translation |
| `langs/es.json` | fix | Updated unknown-editor key and ES translation |
| `langs/es_es.json` | fix | Updated unknown-editor key and ES-ES translation |
| `langs/fr.json` | fix | Updated unknown-editor key and FR translation |
| `langs/fr_fr.json` | fix | Updated unknown-editor key and FR-FR translation |
| `tests/test_mcp_server.py` | test | Added `test_install_for_unknown_editor_lists_all_valid_options` (and `from pathlib import Path`) |
| `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` | docs | Marked P7 / Etapa 7 as completed |

### Impact
- **Functionality:** `_install_for_editor` now reports all valid `--install` options (`vscode`, `cursor`, `claude-code`, `claude`, `zed`, `auto`) when given an unknown editor.
- **Performance:** None.
- **Compatibility:** Preserves full i18n parity across all 6 `langs/*.json` files (`tests/test_i18n.py` passes with 0 missing/orphan keys).

### Next steps (if applicable)
- Proceed to Stage 8 (`extensions/vscode/` `pt-pt` localization) when ready.
