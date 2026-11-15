# Survey Facts — Etapa 7: Incluir `claude-code` na mensagem de erro de `--install` e sincronizar i18n

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `etapa7_install_error_claude_code`
- **Referência:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (L192–L211)

## Contexto da Tarefa

Alinhar a mensagem de erro de editor desconhecido em `_install_for_editor` (`src/mcp_server.py`) às opções aceitas pelo argumento `--install` (`choices`) e manter paridade total nos 6 arquivos JSON de tradução em `langs/`, com cobertura de teste unitário em `tests/test_mcp_server.py`.

## Fatos Levantados no Repositório

1. **`src/mcp_server.py`**:
   - `_CONFIG_TEMPLATES` (linhas 2755–2820) define templates para: `vscode`, `cursor`, `claude-code`, `claude`, `zed`.
   - `_install_for_editor(editor: str, project_root: Path) -> tuple[bool, str]` (linha 2880) chama `_resolve_editor_config(editor)` e, quando `config is None` (linhas 2897–2904), retorna:
     `(False, __("Unknown editor: '{editor}'. Valid options: vscode, cursor, claude, zed, auto", editor=editor))`.
   - `--install` (linhas 3054–3062) define `choices=["vscode", "cursor", "claude-code", "claude", "zed", "auto"]` e `help=__("Install MCP configuration for an editor (vscode, cursor, claude-code, claude, zed, or auto-detect).")`.
2. **`langs/*.json`**:
   - A chave `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude, zed, auto"` está presente na linha 1179 de todos os 6 arquivos:
     - `langs/pt_br.json`
     - `langs/pt_pt.json`
     - `langs/es.json`
     - `langs/es_es.json`
     - `langs/fr.json`
     - `langs/fr_fr.json`
3. **`scripts/sync_all_langs.py`**:
   - Existe no repositório e **não** contém a string `"Unknown editor"` nem `"vscode, cursor"`.
4. **`CONTEXT.md` e ADRs**:
   - `CONTEXT.md` existe; a tarefa não introduz novo conceito de domínio nem decisão arquitetural irreversível, não demandando alteração em `CONTEXT.md` ou novo ADR.

## Decisões das Rodadas (`/grill-with-docs`)

- **Q1 (Texto exato e ordem das opções):** Adotar `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude-code, claude, zed, auto"`, espelhando exatamente a ordem de `choices` em `--install`.
- **Q2 (Cobertura do teste unitário):** Adicionar teste em `tests/test_mcp_server.py` chamando `_install_for_editor` com um editor inválido e validando que retorna `ok is False` e que todas as opções válidas (`vscode`, `cursor`, `claude-code`, `claude`, `zed`, `auto`) aparecem na mensagem.
