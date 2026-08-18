## Completion Report — MCP Tool Server Hang Fix (run_linter / all tools)

### What was done
- **Root cause fixed:** all 12 MCP tool handlers were sync functions run inline on the asyncio event loop (mcp SDK 1.28.1). Any blocking call inside a handler (git subprocess, OTA download, AI SDK call) froze the entire stdio server — the stdin reader and stdout writer stalled and Claude Code never received a response ("hang").
- Added the `_offload` decorator (`anyio.to_thread.run_sync`) and applied it to all 12 tools in `src/mcp_server.py`. `functools.wraps` preserves names/signatures; decorator order keeps FastMCP registration intact.
- `_TOOL_FUNCS` now unwraps to the original sync functions (`fn.__wrapped__`), keeping the `--tool` CLI mode synchronous.
- Warm-import thread at server startup pre-imports `src.core` so the OTA smart-excludes download never delays the first tool call (a racing import blocks on the import lock inside a worker thread, never on the loop).
- Subprocess hardening: `stdin=subprocess.DEVNULL` added to all `subprocess.run` sites in `src/core.py` and `src/metrics.py` (children no longer inherit the JSON-RPC pipe); `_run_external_linter` also gets `timeout=120`.
- OTA downloads bounded: new `_download_smart_excludes()` helper runs the request on a daemon thread with a 10s hard timeout (urllib's timeout does not bound Windows DNS resolution); all 3 smart-excludes download blocks now fall back to the offline copy on stall.
- Tests: `_call_tool` helper + 26 call sites converted in `tests/test_mcp_server.py`; new `TestOffloadDecorator` (7 deterministic tests); new `tests/test_mcp_server_e2e.py` spawning the real server as a subprocess and speaking JSON-RPC over stdio (initialize, `run_linter`, `get_git_context` — each response asserted within 60s) plus `--tool` CLI-mode tests.
- Docs: one-sentence note on handler offloading added to ARCHITECTURE.md item 13 in all 5 language variants.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/mcp_server.py | fix | `_offload` decorator applied to all 12 tools; warm-import daemon thread in `_init_config()`; `_TOOL_FUNCS` unwraps `__wrapped__` for sync `--tool` mode |
| src/core.py | fix | `_download_smart_excludes()` (daemon thread + 10s hard timeout) replacing 3 raw `urlopen` blocks; `stdin=subprocess.DEVNULL` on all subprocess.run sites |
| src/linter_engine.py | fix | `_run_external_linter`: `stdin=subprocess.DEVNULL` + `timeout=120` |
| src/metrics.py | fix | `stdin=subprocess.DEVNULL` on the `git config user.name` subprocess |
| tests/test_mcp_server.py | test | `_call_tool` async helper; 26 call sites converted; new `TestOffloadDecorator` (7 tests: worker thread, value, exceptions, signature preservation, registration, sync `_TOOL_FUNCS`, loop non-blocking) |
| tests/test_mcp_server_e2e.py | test | New: stdio JSON-RPC against a real server subprocess (network-independent via `GITPR_SKIP_SMART_EXCLUDES=1`) + `--tool` CLI tests |
| docs/ARCHITECTURE.md (+ es_es, fr_fr, pt_br, pt_pt) | docs | Item 13: note that all handlers are offloaded to anyio worker threads |

### Impact
- **Functionality:** MCP tools (`run_linter` and all others) no longer hang Claude Code; the event loop stays responsive while handlers do blocking work. CLI `--tool` mode and all other flows are unchanged.
- **Performance:** One thread hop per tool call (negligible); warm import hides first-call latency; OTA download bounded to ~10s worst case with the offline copy as fallback.
- **Compatibility:** No API breaks — tool names, JSON-RPC schemas and `--tool` exit codes preserved. Git credential prompts still open the console (`stdin=DEVNULL` only stops children from inheriting the JSON-RPC pipe).

### Test results
- `pytest tests/ -q`: **257 passed, 2 failed** — the 2 failures (`tests/test_external_linters.py::TestGenerateLinterReportContent`) are pre-existing on this machine (assertions expect English; OS locale auto-detects pt-BR) and were confirmed to fail without this change via `git stash`.
- `tests/test_mcp_server_e2e.py`: 6/6 passed (server subprocess + CLI mode).
- CLI verification: `gitpr-mcp --tool run_linter` → exit 0, valid JSON on stdout.

### Next steps (if applicable)
- **Rollout:** `taskkill /IM gitpr-mcp.exe /F` to kill hung servers; Claude Code relaunches via `.mcp.json` (editable install — no reinstall needed). First run self-heals: the smart-excludes download stamps `SMART_EXCLUDES_VERSION=v0.0.17` in `~/.gitpr/.env`.
- The version bump in `src/updater.py` (0.0.36→0.0.37 / v0.0.16→v0.0.17) is a separate pending change (docs re-download trigger) — committed separately.
- The ARCHITECTURE.md item-13 note rides along with the pending multilang docs commit (files already carried that task's changes; kept out of this commit for atomicity).
- Follow-ups from the plan (out of scope): bound AI SDK timeouts in `src/ai_providers.py` (~600s default); replace the `shell=True` f-string in `_run_external_linter` with a shlex/argv list; apply the same DNS-bounding pattern to the urllib sites in i18n/ai_providers.
- Pre-existing issue: `tests/test_external_linters.py` should force `GITPR_LANG=en` (or assert language-agnostic content) so it passes on pt-BR machines.
