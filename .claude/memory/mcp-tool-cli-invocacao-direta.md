---
name: mcp-tool-cli-invocacao-direta
description: Invocação direta de MCP tools via CLI com gitpr-mcp --tool sem servidor stdio
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-11_mcp_tool_cli_flag.md
  date: 2026-08-11
  branch: develop_natan
---

As 12 tools MCP do GitPR podem ser invocadas diretamente da linha de comando sem
iniciar o servidor stdio JSON-RPC. O comando `gitpr-mcp --tool <name> [--tool-args '<json>']`
executa uma tool específica e retorna o resultado como JSON no stdout real,
enquanto todas as mensagens de diagnóstico vão para stderr.

A arquitetura usa dois padrões principais em `src/mcp_server.py`:

1. **Registry pattern:** `_TOOL_FUNCS` é um dicionário hand-maintained que mapeia
   nome da tool → `(callable, arg_parser_fn)`. `_get_tool_registry()` faz merge
   desse catálogo com as funções reais importadas, retornando o registro completo.

2. **Real stdout isolation:** `_write_real_stdout()` escreve diretamente no
   `sys.__stdout__` original (salvo antes do monkey-patching do MCP), garantindo
   que o JSON de saída não seja capturado pelo redirect do servidor stdio.

O comando `gitpr-mcp --tool` (sem nome) lista todas as tools disponíveis com
suas assinaturas de parâmetros. O `.env` é carregado automaticamente para que
API keys funcionem no modo CLI.

**Why:** O servidor MCP stdio foi projetado para comunicação processo-a-processo
com clientes MCP (IDEs, agentes). Mas para debug, scripts e uso manual, iniciar
o servidor completo era excessivo. O modo `--tool` permite invocar uma tool
isolada e receber JSON puro, sem o overhead do protocolo JSON-RPC.

**How to apply:**
1. Novas tools adicionadas ao MCP devem ser registradas em `_TOOL_FUNCS`
2. `_write_real_stdout()` deve ser usado para qualquer output JSON; stderr para logs
3. O parser de argumentos de cada tool (`arg_parser_fn`) faz parse e validação
4. `_prettify_result()` formata o output para exibição amigável no terminal

Ver também: [[mcp-server-isolation]]
