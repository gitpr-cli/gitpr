---
name: mcp-server-isolation
description: Servidor MCP usa monkey-patching de stdout para isolar JSON-RPC do output da aplicação
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-23_mcp_server_integration.md
  date: 2026-07-23
  branch: develop_natan
---

O servidor MCP (`src/mcp_server.py`) roda sobre transporte stdio, onde QUALQUER
`sys.stdout.write()` corrompe o protocolo JSON-RPC. Em vez de adicionar parâmetros
`quiet` a todas as funções existentes, o servidor usa duas técnicas de isolamento:

1. **`_patch_output()`**: redireciona todo output da aplicação para stderr,
   preservando `sys.__stdout__.buffer` para a camada de transporte MCP.
   Isso isola o servidor sem tocar em NENHUM módulo existente.

2. **`_safe_call()`**: wrapper que captura `SystemExit` (nossa versão patchada de
   `sys.exit`) e exceções gerais, retornando `None` em falha. O servidor nunca
   crasha na invocação de uma tool.

3. **`_init_config()`**: carrega `.env` diretamente em vez de chamar
   `setup_environment()` que usa `click.prompt()` (bloqueante em modo MCP).

Entry points: `gitpr-mcp` (primário) e `gitpr --mcp` (alias oculto).

**Why:** A abordagem de monkey-patching evita propagar `quiet=True` por dezenas
de assinaturas de função. O protocolo stdio do MCP é binário e qualquer byte
não-JSON na stdout quebra a comunicação com o editor.

**How to apply:**
1. Novas tools MCP devem ser wrappers finos que delegam para funções existentes
2. NUNCA usar `print()` ou `click.echo()` em código chamado pelo MCP — o patch
   redireciona para stderr, mas o design correto é retornar dados, não imprimir
3. `_safe_call()` deve envolver toda chamada que pode lançar exceção
4. O monkey-patching toca `sys.stdout`, `sys.stderr`, `sys.exit` e `builtins.print`
5. Testar com `gitpr-mcp` diretamente, não apenas `gitpr --mcp`

Relacionado: [[mcp-tool-annotations]]
