# Walkthrough — Stage 7: Include `claude-code` in `--install` error message and sync i18n

## Changes Made
- Updated `_install_for_editor` in `src/mcp_server.py` (line 2901) to include `claude-code` in the unknown-editor error string:
  `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude-code, claude, zed, auto"`
- Replaced the old key and updated translations in all 6 `langs/*.json` files (`pt_br.json`, `pt_pt.json`, `es.json`, `es_es.json`, `fr.json`, `fr_fr.json`).
- Added `test_install_for_unknown_editor_lists_all_valid_options` to `TestInstallConfigDescriptions` in `tests/test_mcp_server.py`.
- Marked `P7` / `Etapa 7` as completed in `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md`.

## Validation Results
- `python -m pytest tests/test_i18n.py tests/test_mcp_server.py -k "TestInstallConfigDescriptions or TestLangFileIntegrity or TestNoMissingKeys or TestAstExtraction or TestFormattingSmoke" -v`: **28 passed, 112 deselected** in 10.20s (22/22 in `tests/test_i18n.py` and 6/6 in `TestInstallConfigDescriptions`).
  - Note: An unfiltered run of `tests/test_mcp_server.py` stalled at `TestGitContextTool::test_fallback_on_error` and was cancelled, so the remaining `test_mcp_server.py` classes were deselected in this run.
