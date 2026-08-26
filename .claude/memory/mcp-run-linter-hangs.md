---
name: mcp-run-linter-hangs
description: "Hang das tools MCP do GitPR resolvido com _offload (anyio worker threads); se voltar a travar, matar gitpr-mcp.exe e reiniciar o editor"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7fe310ed-23c7-4b70-9a46-183f916281a3
  modified: 2026-08-18T17:46:59.557Z
---

As tools MCP do GitPR (`run_linter` etc.) travavam no Claude Code porque o SDK mcp executava handlers sync inline no event loop asyncio — qualquer chamada bloqueante (subprocess git, download OTA, SDK de IA) congelava o servidor stdio inteiro. **Corrigido em 2026-08-18** (commit `fix: offload MCP tool handlers from the event loop to fix server hangs`): decorator `_offload` (anyio worker threads) nas 12 tools, warm import de `src.core`, `stdin=DEVNULL` nos subprocessos e download OTA limitado a 10s.

**Why:** O sintoma registrado (tool trava / nunca retorna) era o loop de eventos parado; as correções garantem que o loop nunca bloqueia.

**How to apply:** Se uma tool MCP travar de novo: `taskkill /IM gitpr-mcp.exe /F` e reiniciar o Claude Code (o `.mcp.json` relança; install editável — sem reinstalar). Para validar mudanças no MCP: `python -m pytest tests/test_mcp_server.py tests/test_mcp_server_e2e.py -q` (o e2e sobe o servidor real via JSON-RPC) e `gitpr-mcp --tool run_linter`. Follow-ups pendentes: timeouts do SDK de IA em ai_providers.py e shell=True em `_run_external_linter`. Ver [[mcp-server-isolation]].
