# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
fix: offload MCP handlers and bound blocking calls
```

---

## 🎯 Summary

The MCP server's synchronous tool handlers executed inline on the asyncio event loop, causing the entire stdio server to hang during blocking operations such as Git subprocess calls, lazy imports, or over-the-air smart-exclude downloads (especially DNS resolution stalls on Windows). This PR moves all tool handlers to worker threads via an `_offload` decorator, adds a hard timeout to the remote smart-excludes download, and adds `stdin=subprocess.DEVNULL` to subprocess invocations to prevent interactive hangs. It also bumps the version and adds end-to-end regression tests.

## 🛠️ Technical Changes

- Add `_offload` decorator using `anyio.to_thread.run_sync` and apply it to all MCP tool handlers; `_TOOL_FUNCS` unwraps to the original synchronous functions so the `--tool` CLI mode stays synchronous.
- Start a background warm-up import of `src.core` to avoid first-call latency and prevent the OTA download from stalling the event loop.
- Introduce `_download_smart_excludes` with a daemon thread and 10-second hard timeout, falling back to the offline copy when DNS resolution stalls (urllib timeout does not bound DNS on Windows).
- Add `stdin=subprocess.DEVNULL` to numerous Git subprocess calls and a 120-second timeout to the external linter subprocess to avoid blocking on input.
- Bump `__version__` to 0.0.37 and `__lang_version__` to v0.0.17.
- Add example metric export files (`gitpr_metrics_2026-08-18.csv` and `.json`) and remove `.gitpr/reports/` from `.gitignore`.
- Update unit tests for async tool calls and add new `test_mcp_server_e2e.py` with stdio JSON-RPC tests that spawn the real server and assert prompt responses.

## ⚠️ Impact/Warnings

- New dependency: `anyio` is used for the offload wrapper; ensure it is added to project dependencies if not already present.
- `stdin=subprocess.DEVNULL` changes subprocess behavior for any commands that previously read from stdin; this is intended to prevent hangs but may affect interactive use cases.
- The end-to-end tests set `GITPR_SKIP_SMART_EXCLUDES=1` to avoid network access; this environment variable must be respected by `src.core` to keep tests hermetic.
- The background warm-up import is best-effort; if it fails, handlers retry on demand, but first call could still see slight delay.

close #133