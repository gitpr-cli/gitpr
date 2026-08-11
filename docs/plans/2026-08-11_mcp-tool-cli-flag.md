# Plan: `--tool` CLI flag for gitpr-mcp

## Context

Users cannot invoke individual MCP tools from the terminal — `gitpr-mcp get_git_context` hangs because `gitpr-mcp` ignores unknown args and starts the stdio MCP server, waiting for JSON-RPC messages that never arrive. The only way to test a tool is through an MCP client (VS Code, Claude Code, etc.), which makes debugging and scripting cumbersome.

This adds `--tool <name>` and `--tool-args <json>` flags so users can invoke any of the 12 MCP tools directly from the CLI and get JSON on stdout.

## Changes

### 1. `src/mcp_server.py` — Core implementation

#### 1a. Add tool registry (~40 lines, after `_resolve_provider`)

A dict mapping tool name → `(callable, param_specs)` where `param_specs` is a dict of `param_name: {"type": str, "required": bool, "default": any}`.

```python
def _build_tool_registry():
    """Return {name: (callable, param_specs)} for all 12 MCP tools."""
    return {
        "get_git_context":         (get_git_context, {}),
        "analyze_diff":            (analyze_diff, {}),
        "list_unstaged_files":     (list_unstaged_files, {}),
        "analyze_unstaged_diff":   (analyze_unstaged_diff, {}),
        "get_full_diff":           (get_full_diff, {}),
        "run_linter":              (run_linter, {}),
        "generate_commit_message": (generate_commit_message, {
            "provider":  {"type": str, "required": False, "default": ""},
            "diff_text": {"type": str, "required": False, "default": ""},
        }),
        "review_code":             (review_code, {
            "provider":  {"type": str, "required": False, "default": ""},
            "diff_text": {"type": str, "required": False, "default": ""},
        }),
        "full_review":             (full_review, {
            "provider": {"type": str, "required": False, "default": ""},
        }),
        "generate_pr_description": (generate_pr_description, {
            "provider": {"type": str, "required": False, "default": ""},
        }),
        "analyze_blame":           (analyze_blame, {
            "file_path":  {"type": str, "required": True},
            "start_line": {"type": str, "required": True},
            "end_line":   {"type": str, "required": True},
        }),
        "generate_issue":          (generate_issue, {
            "context_type": {"type": str, "required": False, "default": "diff"},
        }),
    }
```

#### 1b. Add `_run_tool(tool_name, tool_args_json)` function (~60 lines)

Pattern: follows `_run_list()` — writes to real stdout, bypasses `_MCPStdout`.

Logic:
1. Build registry via `_build_tool_registry()`
2. If `tool_name` is empty or not in registry → print available tools list (name + params) and `sys.exit(0)`
3. Parse `tool_args_json` if provided (JSON → dict); validate types against param_specs
4. Check all required params are present; error if missing
5. Call `_init_config()` (silent `.env` load — needed for AI tools)
6. Call the tool function with `**resolved_kwargs`
7. Write result to real stdout (same `sys.__stdout__` + `_original_stdout` fallback as `_run_list`)
8. Handle errors: catch exceptions, print JSON error `{"status": "error", "message": "..."}`

#### 1c. Update `main()` argparse (~10 lines)

Add two arguments before `parse_known_args()`:
```python
parser.add_argument("--tool", type=str, default=None, metavar="NAME",
                    help="Run a specific tool directly (bypasses MCP transport). "
                         "Use --tool-args for parameters. Omit NAME to list available tools.")
parser.add_argument("--tool-args", type=str, default="{}", metavar="JSON",
                    help="JSON object with tool parameters (used with --tool).")
```

Add dispatch before server mode:
```python
if args.tool is not None:
    _run_tool(args.tool, args.tool_args)
    return
```

### 2. Documentation updates (15 files)

Each doc gets a small section about the `--tool` flag. The content is the same across languages, just translated.

#### 2a. `docs/mcp-integration.md` (EN) + 4 translations

Add a **"Direct CLI Invocation"** section after "Quick Install" (before "Available Tools"):

```markdown
## Direct CLI Invocation

You can invoke any MCP tool directly from the terminal without starting the server:

```bash
# No-param tools
gitpr-mcp --tool get_git_context
gitpr-mcp --tool analyze_diff
gitpr-mcp --tool run_linter

# Tools with parameters (JSON)
gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"src/main.py","start_line":"10","end_line":"20"}'
gitpr-mcp --tool generate_commit_message --tool-args '{"provider":"gemini"}'
gitpr-mcp --tool generate_issue --tool-args '{"context_type":"history"}'

# List all available tools
gitpr-mcp --tool
```

This is useful for debugging, scripting, and testing tools without an MCP client.
```

Translations:
- **pt_br/pt_pt:** "Invocação Direta via CLI"
- **es_es:** "Invocación Directa por CLI"
- **fr_fr:** "Invocation Directe par CLI"

#### 2b. `docs/mcp-annotations.md` (EN) + 4 translations

Add a note in the "Implementation" section about `--tool` respecting the same annotations (read-only tools don't need API keys, etc.). Minimal change — just mention that `--tool` is another way to invoke annotated tools.

#### 2c. `docs/mcp-prompts.md` (EN) + 4 translations

Add a short "CLI equivalents" subsection showing that prompts can also be fulfilled via `--tool`:
```bash
gitpr-mcp --tool full_review       # equivalent to "Review PR" prompt
gitpr-mcp --tool generate_commit_message  # equivalent to "Generate Commit Message" prompt
```

### 3. Test updates

#### 3a. `tests/test_mcp_server.py`

Add tests:
- `test_run_tool_list`: `--tool` with no name prints available tools
- `test_run_tool_invalid`: `--tool invalid_name` exits with error
- `test_run_tool_get_git_context`: calls tool, returns valid JSON with branch/repo
- `test_run_tool_missing_required_args`: `--tool analyze_blame` without args shows error
- `test_run_tool_with_args`: `--tool analyze_blame --tool-args '{"file_path":"...","start_line":"1","end_line":"5"}'`

## Files to modify

| File | Change |
|------|--------|
| `src/mcp_server.py` | Add `_build_tool_registry()`, `_run_tool()`, argparse flags, dispatch |
| `tests/test_mcp_server.py` | Add `--tool` tests |
| `docs/mcp-integration.md` | Add "Direct CLI Invocation" section |
| `docs/mcp-integration.pt_br.md` | Same, translated |
| `docs/mcp-integration.pt_pt.md` | Same, translated |
| `docs/mcp-integration.es_es.md` | Same, translated |
| `docs/mcp-integration.fr_fr.md` | Same, translated |
| `docs/mcp-annotations.md` | Mention `--tool` in Implementation section |
| `docs/mcp-annotations.pt_br.md` | Same, translated |
| `docs/mcp-annotations.pt_pt.md` | Same, translated |
| `docs/mcp-annotations.es_es.md` | Same, translated |
| `docs/mcp-annotations.fr_fr.md` | Same, translated |
| `docs/mcp-prompts.md` | Add "CLI equivalents" subsection |
| `docs/mcp-prompts.pt_br.md` | Same, translated |
| `docs/mcp-prompts.pt_pt.md` | Same, translated |
| `docs/mcp-prompts.es_es.md` | Same, translated |
| `docs/mcp-prompts.fr_fr.md` | Same, translated |

## Verification

1. `gitpr-mcp --tool` → lists all 12 tools with param signatures
2. `gitpr-mcp --tool get_git_context` → prints `{"branch": "develop_natan", "repository": "natanfiuza/gitpr"}`
3. `gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"src/mcp_server.py","start_line":"270","end_line":"284"}'` → prints blame analysis JSON
4. `gitpr-mcp --tool invalid` → prints error + available tools list
5. `gitpr-mcp --tool analyze_blame` (missing required args) → prints error about missing file_path
6. `python -m pytest tests/test_mcp_server.py -v` → all tests pass
7. `gitpr-mcp --list` still works (no regression)
8. `gitpr-mcp --install` still works (no regression)
9. `gitpr-mcp` (server mode) still works (no regression)
