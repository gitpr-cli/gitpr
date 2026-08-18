# Plan: Fix GitPR MCP tool hang (run_linter / all tools) in Claude Code

## Context

- User reports the gitpr MCP tool `run_linter` hangs (never returns) when Claude Code executes it; probably affects all MCP tools.
- Memory `mcp-run-linter-hangs` (2026-08-18) recorded the symptom without a root cause. This task: diagnose (done) + fix + verify.

## Confirmed diagnosis (verified against code)

**Root cause — sync handlers run inline on the MCP event loop.** All 12 tools are sync functions registered via `@mcp.tool()` in [src/mcp_server.py](src/mcp_server.py) (~lines 282-780). The `mcp` SDK 1.28.1 runs sync handlers directly on the asyncio loop (`mcp/.../func_metadata.py:93-96` — no thread off-load, verified). Any blocking call inside a handler (git subprocess, OTA download, AI SDK call with ~600s default timeout) freezes the whole stdio server: stdin reader + stdout writer stall → Claude Code never gets a response → hang. Matches "happens with all tools".

**Concrete trigger for `run_linter`:** handler lazily does `from src.core import ...` ([src/mcp_server.py:673](src/mcp_server.py#L673)). First `import src.core` runs module-level `SMART_EXCLUDES = _load_smart_excludes() + _load_docs_smart_excludes()` ([src/core.py:287](src/core.py#L287)) → two `urllib.request.urlopen(timeout=3)` downloads ([src/core.py:184](src/core.py#L184), [:265](src/core.py#L265)) fire because `~/.gitpr/.env` has `SMART_EXCLUDES_VERSION='v0.0.16'` while `src/updater.py` now declares `__lang_version__="v0.0.17"` (uncommitted version bump). urllib's timeout does NOT bound Windows DNS resolution → effectively unbounded stall, inline on the loop. On failure `.env` stays stale → repeats every new server process.

**Dormant hazards (same class):** `subprocess.run` calls leave `stdin=None` → children inherit the JSON-RPC pipe (never EOF) → a stdin-reading child (git credential prompt, interactive external linter) blocks forever. Sites: [src/core.py:446](src/core.py#L446), [:474](src/core.py#L474), [:525](src/core.py#L525), [:504](src/core.py#L504), [:550](src/core.py#L550), [:565](src/core.py#L565), [:762](src/core.py#L762), [:1120](src/core.py#L1120), [:1143](src/core.py#L1143) (git fetch — highest risk), [:1168](src/core.py#L1168); [src/metrics.py:18](src/metrics.py#L18); `_run_external_linter` ([src/linter_engine.py:72-89](src/linter_engine.py#L72-L89), shell=True, no timeout — dormant: `.gitpr/skill/.gitpr.linter.yml` has only 2 regex rules).

**Environment:** `.mcp.json` launches `gitpr-mcp.exe` from the pipenv venv — an EDITABLE install, so code fixes take effect on server restart. `--tool` CLI mode calls the same sync functions via `_TOOL_FUNCS` ([src/mcp_server.py:1635-1648](src/mcp_server.py#L1635-L1648)) — must stay sync. 246 tests collected currently.

## Changes

### 1. `_offload` decorator + apply to all 12 tools — `src/mcp_server.py`

- Imports (lines 33-38): add `threading`, `from functools import wraps`, `import anyio`.
- New decorator after `_safe_call` (~line 243):

```python
def _offload(fn):
    """Wrap a sync MCP tool handler so it runs on an anyio worker thread."""
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))
    return wrapper
```

(anyio 4.x `run_sync` takes no `**kwargs` — closure marshals them. `@mcp.tool(...)` must sit ABOVE `@_offload`; `wraps` preserves `__name__`/`__wrapped__` so FastMCP signature introspection and tool names are unchanged.)
- Insert `@_offload` between each `@mcp.tool(...)` block and its `def` (12 sites: get_git_context:282, analyze_diff:308, list_unstaged_files:338, analyze_unstaged_diff:375, get_full_diff:405, generate_commit_message:441, review_code:501, full_review:558, generate_pr_description:608, run_linter:663, analyze_blame:709, generate_issue:770). Bodies untouched.
- `_TOOL_FUNCS`: change values to `fn.__wrapped__` (keeps `--tool` CLI mode synchronous; add comment explaining).

### 2. Warm imports at startup — `src/mcp_server.py` `_init_config()` (~209-223)

Daemon thread pre-imports `src.core` so the OTA download never delays the first tool call; a racing tool import blocks on the import lock inside its worker thread, never the loop.

### 3. Subprocess hardening

- Add `stdin=subprocess.DEVNULL` to the subprocess.run sites listed above in `src/core.py` and `src/metrics.py:18`. (Git credential prompts open the console, not stdin — CLI flows unaffected; in MCP/CI a would-be hang becomes a fast `CalledProcessError`, already handled.)
- `src/linter_engine.py` `_run_external_linter` (72-89): add `stdin=subprocess.DEVNULL` **and** `timeout=120` (swallowed by existing `except Exception: return ""`; fixes the infinite-hang class in both CLI and MCP).

### 4. Bound the OTA download — `src/core.py`

- Add `import threading`; add `_download_smart_excludes(url, hard_timeout=10.0)` helper: daemon thread + `join(10)`; returns None on stall → existing offline fallback chain handles it.
- Replace the three raw `urlopen` download blocks: [src/core.py:184](src/core.py#L184), [:265](src/core.py#L265), [:314](src/core.py#L314). (Line 1070 already has timeout=5 — untouched.)

## Tests

- `tests/test_mcp_server.py`: add `_call_tool(fn, *a, **kw)` helper (`asyncio.run(fn(...))`) and convert the sync call sites (run_linter at 143/158/168 and the other 23) to it.
- New `TestOffloadDecorator` in the same file (7 deterministic tests): runs on worker thread (thread id differs), returns value, propagates exceptions, preserves name/signature/`__wrapped__`, all 12 registered FastMCP tools are async, `_TOOL_FUNCS` stays sync, concurrent slow+fast calls don't block the loop.
- New `tests/test_mcp_server_e2e.py`: (a) spawn server subprocess (sys.path bootstrap + `GITPR_SKIP_SMART_EXCLUDES=1` to be network-independent), send JSON-RPC `initialize` + `tools/call run_linter` + `tools/call get_git_context` over stdin, assert both responses arrive ≤60s (reader-thread pattern — no `select` on Windows pipes); (b) `--tool run_linter` subprocess returns 0 + valid JSON on stdout.
- Full suite: `pipenv run pytest tests/ -v` (246 existing + new).

## Rollout / verification

1. `taskkill /IM gitpr-mcp.exe /F` to kill hung servers; Claude Code session restart relaunches via `.mcp.json` (editable install — no reinstall needed).
2. First run self-heals: smart-excludes download stamps `SMART_EXCLUDES_VERSION` to v0.0.17 in `~/.gitpr/.env`; if DNS still stalls, Change 4 bounds it to ~10s and the offline copy is used.
3. Functional checks in Claude Code: `run_linter`, `get_git_context`, `analyze_diff`, one AI tool.
4. CLI check: `gitpr-mcp --tool run_linter`.
5. Commit (atomic Conventional Commits + Co-Authored-By trailer, e.g. `fix: offload MCP tool handlers from the event loop to fix server hangs`).
6. Completion report → `docs/claude-code/reports/develop_natan/2026-08-18_mcp_run_linter_hang_fix.md`; plan copy → `docs/plans/2026-08-18_mcp_run_linter_hang_fix.md` (user convention).
7. Update memory `mcp-run-linter-hangs` with root cause + fix.
8. One-sentence ARCHITECTURE.md item 13 note (handler offloading) in all 5 language variants.

## Follow-ups (out of scope, noted in report)

- Bound AI SDK timeouts in `src/ai_providers.py` (explicit http timeout; SDK default ~600s).
- `_run_external_linter` shell injection (shlex/argv instead of f-string + shell=True).
- Same DNS-bounding pattern for i18n/ai_providers urllib sites.
