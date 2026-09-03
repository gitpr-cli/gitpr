# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: silence MCP tool output and bound DNS lookups
```

---

🎯 Summary
The CLI `--tool` mode now guarantees a clean, bare JSON response by silencing all auxiliary output (spinner frames, cache hints, skill notices) on stdout/stderr. Additionally, DNS resolution for AI clients is bounded by a wall-clock timeout, preventing indefinite hangs when constructing Gemini or DeepSeek clients.

🛠️ Technical Changes
- `src/mcp_server.py`: `_MCPStdout` accepts a `silent` flag; `_patch_output(silent=True)` disables stderr forwarding and click helpers; `_run_tool` uses it.
- `src/net.py`: Added `bounded_resolve(host, timeout)` that runs `socket.getaddrinfo` in a daemon thread and raises `socket.gaierror` on timeout.
- `src/ai_providers.py`: Call `bounded_resolve` before creating Gemini client and DeepSeek client to fail fast.
- `src/config.py`: Decreased default `GITPR_AI_TIMEOUT` from 600 to 180 seconds.
- `tests/test_mcp_server.py`: Added test for silent mode output suppression.

⚠️ Impact/Warnings
- The default AI timeout is now 180s; workloads that require longer LLM responses should set `GITPR_AI_TIMEOUT` explicitly.
- DNS lookups for the AI providers are hard-limited to 120s (DEFAULT_HARD_TIMEOUT); environments with slow DNS may now see `socket.gaierror` instead of a hang.
- `--tool` mode output is strictly JSON-only; any downstream parser relying on informational stderr lines will need to adapt.

close #146