# Plano de Execução — Etapa 7: Incluir `claude-code` na mensagem de erro de `--install` e sincronizar i18n

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `etapa7_install_error_claude_code`

## Escopo e Arquivos-Alvo

1. `src/mcp_server.py` (linha ~2901):
   - Atualizar a string em `__(...)` dentro de `_install_for_editor` para:
     `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude-code, claude, zed, auto"`
2. `langs/pt_br.json`, `langs/pt_pt.json`, `langs/es.json`, `langs/es_es.json`, `langs/fr.json`, `langs/fr_fr.json` (linha ~1179):
   - Substituir a chave antiga `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude, zed, auto"` pela nova chave `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude-code, claude, zed, auto"` e incluir `claude-code` na mesma posição em cada tradução:
     - `pt_br` / `pt_pt`: `"Editor desconhecido: '{editor}'. Opções válidas: vscode, cursor, claude-code, claude, zed, auto"`
     - `es` / `es_es`: `"Editor desconocido: '{editor}'. Opciones válidas: vscode, cursor, claude-code, claude, zed, auto"`
     - `fr` / `fr_fr`: `"Éditeur inconnu : '{editor}'. Options valides : vscode, cursor, claude-code, claude, zed, auto"`
3. `tests/test_mcp_server.py`:
   - Adicionar teste unitário para `_install_for_editor` com editor inválido verificando `ok is False` e a presença de `vscode`, `cursor`, `claude-code`, `claude`, `zed`, `auto` na mensagem retornada.

## Verificação

- `python -m pytest tests/test_i18n.py tests/test_mcp_server.py -v`
