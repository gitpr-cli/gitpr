# Spec — MCP CLI silent mode, bounded AI timeout, DNS-bounded clients

> Feature spec for the fix shipped in commit `681a7fa` ("fix: silence CLI tool output and bound DNS resolution"), 2026-09-01. Written retroactively so future agents and tasks have a single reference for the design and the acceptance evidence.

## Objective

Eliminate the perceived "MCP tool hang" when agents invoke `gitpr-mcp` tools (reported for `review_code` and `get_git_context`). The root cause was **not a code deadlock** but a combination of: DeepSeek API latency (15–25s for a trivial diff, minute-scale spikes), an unbounded wait chain (`GITPR_AI_TIMEOUT=600` × 3 retries ≈ 30min apparent hang), a spinner with no progress feedback, and client-side serialization of MCP calls per server (a slow AI call makes unrelated tools appear hung because they queue behind it).

The fix makes tool invocations **fail fast with a visible error** instead of hanging silently, and makes the `--tool` CLI output **machine-consumable** (bare JSON, zero noise).

## Scope

**In scope**
- `gitpr-mcp --tool <name>` CLI mode: silent output (JSON-only stdout, no diagnostic messages, stderr stays empty).
- `GITPR_AI_TIMEOUT` default: 600 → 180 seconds (config default + user `~/.gitpr/.env`).
- DNS resolution bounded with a hard wall-clock limit for AI client creation (Gemini + DeepSeek).
- Regression coverage in `tests/test_mcp_server.py`.

**Out of scope**
- Progress notifications / elapsed-time feedback for MCP tool calls (larger, separate feature).
- Server-mode spinner behavior (unchanged — messages still go to stderr in server mode).
- Changing the retry count (still 3 attempts).

## Design

### 1. Silent CLI output (`src/mcp_server.py`)
- `_MCPStdout` gains a `silent` flag: when set, `write()`/`flush()` discard instead of forwarding. The `.buffer` property still exposes `sys.__stdout__.buffer` so the MCP transport (server mode) is unaffected.
- `_patch_output(silent=False)` — default keeps server-mode behavior; `_run_tool` (CLI mode) calls `_patch_output(silent=True)`.
- `_mcp_secho`/`_mcp_echo` become no-ops when `silent` is set.
- The spinner writes to `sys.stdout` directly (not via click), so click-patching alone was insufficient — the silent stdout sink is what actually silences it.

### 2. Bounded AI timeout (`src/config.py`)
- `DEFAULT_CONFIG["GITPR_AI_TIMEOUT"]` and `_DEFAULT_AI_TIMEOUT` changed 600 → 180.
- Still configurable via `~/.gitpr/.env`; invalid/non-positive values fall back to 180.
- Worst case with 3 retries: ~9 minutes, down from ~30.

### 3. DNS-bounded AI clients (`src/net.py`, `src/ai_providers.py`)
- `bounded_resolve(host, timeout)` — resolves via `socket.getaddrinfo()` on a daemon thread, raises `socket.gaierror` if the lookup exceeds the bound. Windows `getaddrinfo` is **not** covered by SDK/httpx timeouts, so a stalled resolver previously froze the call indefinitely.
- Applied in `_make_gemini_client` (`generativelanguage.googleapis.com`) and `_make_openai_client` for DeepSeek (`api.deepseek.com`) before client construction.

## Acceptance Criteria

1. `gitpr-mcp --tool review_code` (and `run_linter`, `get_git_context`) prints **only the JSON payload** on stdout; stderr is 0 bytes.
2. No skill-loaded notices, smart-excludes lines, cache hints, or spinner text appear in CLI mode.
3. Server mode (stdio MCP) is unchanged: diagnostic messages still go to stderr, JSON-RPC stream stays clean.
4. `get_ai_timeout()` returns 180.0 with no `.env` override; a stalled DNS lookup fails in ≤10s per attempt with a visible error instead of hanging.
5. Full test suite passes (incl. `tests/test_mcp_server.py` silent-output test).

## Test Cases

| Case | Input | Expected |
|------|-------|----------|
| Silent CLI output | `gitpr-mcp --tool run_linter` on a dirty tree | stdout = JSON only; stderr = 0 bytes |
| Silent CLI with AI call | `gitpr-mcp --tool review_code --tool-args '{"diff_text":"…"}'` | stdout = JSON only; stderr = 0 bytes (proves spinner/notices suppressed at source) |
| Silent-mode unit test | `test_patch_silent_discards_output` | stdout writes + `click.secho` produce no stderr calls while `silent=True` |
| Timeout default | `get_ai_timeout()` with clean config | `180.0` |
| DNS bound | `bounded_resolve` against an unroutable host / stalled resolver | raises `socket.gaierror` within the bound |
| Server-mode regression | e2e stdio tests (`tests/test_mcp_server_e2e.py`) | 6/6 green, JSON-RPC intact |

## Evidence (verified 2026-09-01)

- e2e stdio suite green (6/6); CLI direct invocations green; network-enabled probe green.
- Cache-as-proof diagnostic: an MD5 cache JSON written at the moment of the reported "hang" proves the AI call completed — the hang was client-side perception, not a deadlock.
- `get_git_context` "hang" was collateral: Claude Code serializes MCP calls per server, so it queued behind the slow `review_code`.
- Two zombie `gitpr-mcp.exe` processes (stale morning-session servers) were killed; the editor session restart respawns them via `.mcp.json`.
