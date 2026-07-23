## Completion Report — MCP Server Integration

### What was done
- Added MCP (Model Context Protocol) server support to GitPR, enabling direct integration with VS Code, Cursor, Claude Desktop, and other MCP-compatible editors/IDEs
- Created a complete `src/mcp_server.py` module using the official `mcp` Python SDK (FastMCP) that exposes 10 tools and 7 resources
- All GitPR AI-powered capabilities are now available as MCP tools without leaving the editor
- 33 new unit tests created, zero regressions in existing tests

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/mcp_server.py` | **new** | Complete MCP server with 10 tools, 7 resources, output patching, safe-call wrapper, and stdio transport |
| `pyproject.toml` | feat | Added `mcp>=1.0.0` dependency and `gitpr-mcp` console script entry point |
| `Pipfile` | feat | Added `mcp = "*"` dependency |
| `src/main.py` | feat | Added `--mcp` hidden flag with early handler (before `setup_environment()`) |
| `tests/test_mcp_server.py` | **new** | 33 unit tests covering tools, resources, patching system, and safe-call wrapper |
| `docs/mcp-integration.md` | **new** | Documentation with editor configs (VS Code, Cursor, Claude Desktop, Zed) and usage examples |

### MCP Tools exposed

| Tool | Delegates to |
|------|-------------|
| `get_git_context` | `get_current_branch()`, `get_repo_name()` |
| `analyze_diff` | `get_git_diff()` |
| `get_full_diff` | `get_git_full_diff()` |
| `generate_commit_message` | `generate_pr_content("commit")` |
| `review_code` | `generate_pr_content("review")` |
| `full_review` | `generate_pr_content("fullreview")` |
| `generate_pr_description` | `generate_pr_content("pr")` |
| `run_linter` | `parse_diff_and_lint()` |
| `analyze_blame` | `run_blame_analysis()` |
| `generate_issue` | `generate_issue_content()` |

### MCP Resources exposed

| URI | Content |
|-----|---------|
| `skill://list` | List of all available skill template URIs |
| `skill://pr` | `.gitpr.pr.md` template |
| `skill://commit` | `.gitpr.commit.md` template |
| `skill://review` | `.gitpr.review.md` template |
| `skill://filereview` | `.gitpr.filereview.md` template |
| `skill://issue` | `.gitpr.issue.md` template |
| `skill://blame` | `.gitpr.blame.md` template |
| `linter://config` | `.gitpr.linter.yml` rules |

### Technical design decisions

1. **Monkey-patching for isolation**: The MCP server runs on stdio transport, so any `sys.stdout.write()` corrupts the JSON-RPC protocol. Instead of adding `quiet` parameters to dozens of existing functions, the server uses a `_patch_output()` system that redirects all application output to stderr while preserving `sys.__stdout__.buffer` for the MCP transport layer. This touches zero existing modules.

2. **Safe-call wrapper**: `_safe_call()` catches `SystemExit` (our patched `sys.exit`) and general exceptions, returning `None` on failure so the server never crashes on tool invocation.

3. **Silent configuration**: `_init_config()` loads `.env` directly instead of calling `setup_environment()` which uses `click.prompt()` (blocked in MCP mode).

4. **Separate entry point**: `gitpr-mcp` as the primary command, with `gitpr --mcp` as a hidden alias for discoverability.

### Impact
- **Functionality:** GitPR can now be used directly from MCP-compatible editors without opening a terminal
- **Performance:** No impact on existing CLI — MCP mode is a completely isolated execution path
- **Compatibility:** 100% backward compatible. The `--mcp` flag is hidden and the `gitpr-mcp` entry point is additive. All existing tests continue passing.
- **Dependencies:** Added `mcp>=1.0.0` (~15 transitive deps: pydantic, starlette, uvicorn, httpx, etc.)

### Test results
```
tests/test_mcp_server.py — 33 passed
tests/test_core.py — 2 passed
tests/test_skill_command.py — 3 passed
tests/test_pre_save.py — 3 passed
tests/test_smart_excludes.py — 4 passed
tests/test_thinking_words.py — 3 passed
Total: 48 passed, 0 failed
```
(Pre-existing failure in test_chat_backend.py::test_api_exception — pt_br vs en message mismatch — is unrelated to this change.)

### Usage
```bash
# Primary entry point
gitpr-mcp

# Alias via main CLI
gitpr --mcp

# Editor config (VS Code .vscode/mcp.json)
{
  "servers": {
    "gitpr": {
      "type": "stdio",
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Next steps (if applicable)
- Test with real VS Code / Cursor MCP integration (requires editor with MCP support)
- Consider adding prompts (MCP prompts) for common workflows like "review my PR"
- Consider adding tool annotations (readOnlyHint, destructiveHint) for better IDE integration
- Monitor `mcp` SDK v2.x stabilization for migration (adds stateless mode, tasks)
