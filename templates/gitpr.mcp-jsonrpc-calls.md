# GitPR MCP — JSON-RPC 2.0 Call Reference

> Auto-generated from `src/mcp_server.py` v0.0.30 — 2026-08-11
>
> Use this file as a **test reference** to manually invoke GitPR MCP tools
> via the JSON-RPC 2.0 stdio transport. Each section shows the exact JSON
> payload you can paste into an MCP client, `echo | gitpr-mcp`, or a test harness.

---

## Protocol Overview

| Aspect | Detail |
|--------|--------|
| Protocol | JSON-RPC 2.0 |
| Transport | stdio (stdin/stdout) |
| Encoding | UTF-8 |
| Line delimiter | `\n` (newline) |
| Server command | `gitpr-mcp` |

Every message is a single line of JSON terminated by `\n`. The MCP protocol
layers on top of JSON-RPC 2.0 with these methods:

| MCP Method | Purpose |
|------------|---------|
| `initialize` | Client↔Server handshake |
| `notifications/initialized` | Client signals ready after handshake |
| `tools/list` | Discover available tools |
| `tools/call` | Invoke a tool |
| `resources/list` | Discover available resources |
| `resources/read` | Read a resource |
| `prompts/list` | Discover available prompts |
| `prompts/get` | Get a prompt template |

---

## 1. Initialize Handshake

### Request (client → server)

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-harness","version":"1.0.0"}}}
```

### Expected Response (server → client)

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{},"resources":{},"prompts":{}},"serverInfo":{"name":"gitpr","version":"0.0.30"}}}
```

### Initialized Notification (client → server)

```json
{"jsonrpc":"2.0","method":"notifications/initialized"}
```

*No response expected — this is a notification.*

---

## 2. Tools

### 2.1 Discover Tools — `tools/list`

#### Request

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

#### Expected Response (12 tools)

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "get_git_context",
        "description": "Get the current git branch, repository name, and remote origin URL.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
      },
      {
        "name": "analyze_diff",
        "description": "Get the current uncommitted git diff (git diff HEAD — includes both staged and unstaged changes). Lists all changed files and their line-level modifications.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
      },
      {
        "name": "list_unstaged_files",
        "description": "List uncommitted file changes categorized as new (untracked), modified (unstaged modifications) or deleted. Returns structured JSON.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
      },
      {
        "name": "analyze_unstaged_diff",
        "description": "Get only the unstaged git diff (git diff without HEAD — compares the index against the working tree). Excludes staged changes. Untracked files are not shown; use list_unstaged_files for them.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
      },
      {
        "name": "get_full_diff",
        "description": "Get the full diff of the current branch against the remote base branch (origin/main or origin/master). Runs git fetch first.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
      },
      {
        "name": "generate_commit_message",
        "description": "Generate a Conventional Commits commit message from the current git diff using AI. Returns a message like 'feat: add user authentication'.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "provider": {"type": "string", "description": "AI provider override: gemini, deepseek, or ollama. Empty uses default from ~/.gitpr/.env."},
            "diff_text": {"type": "string", "description": "Optional diff text. If empty, auto-detects from git."}
          },
          "required": []
        }
      },
      {
        "name": "review_code",
        "description": "Perform an AI code review on uncommitted local changes (git diff HEAD). Returns structured feedback with issues and improvement suggestions.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "provider": {"type": "string", "description": "AI provider override: gemini, deepseek, or ollama."},
            "diff_text": {"type": "string", "description": "Optional diff text. If empty, auto-detects from git."}
          },
          "required": []
        }
      },
      {
        "name": "full_review",
        "description": "Perform a full AI code review comparing the entire current branch against origin/main. Runs git fetch automatically.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "provider": {"type": "string", "description": "AI provider override: gemini, deepseek, or ollama."}
          },
          "required": []
        }
      },
      {
        "name": "generate_pr_description",
        "description": "Generate a complete Pull Request description (title + body) from the full diff against origin/main. Uses AI to create a structured, professional PR document.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "provider": {"type": "string", "description": "AI provider override: gemini, deepseek, or ollama."}
          },
          "required": []
        }
      },
      {
        "name": "run_linter",
        "description": "Run the static local linter (regex-based rules from .gitpr.linter.yml) on the current git diff. Returns error and warning counts with detailed messages.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
      },
      {
        "name": "analyze_blame",
        "description": "Run AI-powered git blame analysis on a file region to trace the origin of business rules. Classifies each commit as ORIGIN (first introduction) or REFACTORING (later change).",
        "inputSchema": {
          "type": "object",
          "properties": {
            "file_path": {"type": "string", "description": "Path to the source file (relative to the repository root)."},
            "start_line": {"type": "string", "description": "Starting line number (as a string, e.g. '42')."},
            "end_line": {"type": "string", "description": "Ending line number (as a string, e.g. '58')."}
          },
          "required": ["file_path", "start_line", "end_line"]
        }
      },
      {
        "name": "generate_issue",
        "description": "Generate a structured Issue (What / Why / Where / How) from code context using AI. Supports three modes: diff (current changes), history (branch history), or blame (file region).",
        "inputSchema": {
          "type": "object",
          "properties": {
            "context_type": {"type": "string", "description": "Context source: 'diff' (default), 'history', or 'blame'."}
          },
          "required": []
        }
      }
    ]
  }
}
```

---

### 2.2 Tool Calls — `tools/call`

#### 2.2.1 `get_git_context` — No params

```json
{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"get_git_context","arguments":{}}}
```

**Expected response shape:**
```json
{"branch": "develop_natan", "repository": "natanfiuza/gitpr"}
```

---

#### 2.2.2 `analyze_diff` — No params

```json
{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"analyze_diff","arguments":{}}}
```

**Expected response shape (changes found):**
```json
{"status": "changes_found", "diff": "diff --git a/..."}
```

**Expected response shape (no changes):**
```json
{"status": "no_changes", "message": "No uncommitted changes detected."}
```

---

#### 2.2.3 `list_unstaged_files` — No params

```json
{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"list_unstaged_files","arguments":{}}}
```

**Expected response shape:**
```json
{
  "status": "changes_found",
  "new": ["untracked.py"],
  "modified": ["edited.py"],
  "deleted": ["removed.py"],
  "files": [
    {"path": "untracked.py", "type": "new"},
    {"path": "edited.py", "type": "modified"},
    {"path": "removed.py", "type": "deleted"}
  ],
  "total": 3,
  "message": ""
}
```

---

#### 2.2.4 `analyze_unstaged_diff` — No params

```json
{"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"analyze_unstaged_diff","arguments":{}}}
```

**Expected response shape:**
```json
{"status": "changes_found", "diff": "diff --git a/..."}
```

---

#### 2.2.5 `get_full_diff` — No params

```json
{"jsonrpc":"2.0","id":14,"method":"tools/call","params":{"name":"get_full_diff","arguments":{}}}
```

**Expected response shape:**
```json
{"status": "changes_found", "diff": "diff --git a/..."}
```

---

#### 2.2.6 `generate_commit_message` — Optional provider + diff_text

```json
{"jsonrpc":"2.0","id":15,"method":"tools/call","params":{"name":"generate_commit_message","arguments":{}}}
```

```json
{"jsonrpc":"2.0","id":16,"method":"tools/call","params":{"name":"generate_commit_message","arguments":{"provider":"gemini"}}}
```

```json
{"jsonrpc":"2.0","id":17,"method":"tools/call","params":{"name":"generate_commit_message","arguments":{"diff_text":"diff --git a/x.py b/x.py\n+print('hello')"}}}
```

```json
{"jsonrpc":"2.0","id":18,"method":"tools/call","params":{"name":"generate_commit_message","arguments":{"provider":"deepseek","diff_text":"diff --git a/x.py b/x.py\n+print('hello')"}}}
```

**Expected response shape (success):**
```json
{"status": "success", "commit_message": "feat: add hello world"}
```

**Expected response shape (no changes):**
```json
{"status": "no_changes", "message": "No diff to analyze. Make some changes first."}
```

**Expected response shape (AI failure):**
```json
{"status": "error", "message": "AI failed to generate a commit message."}
```

---

#### 2.2.7 `review_code` — Optional provider + diff_text

```json
{"jsonrpc":"2.0","id":20,"method":"tools/call","params":{"name":"review_code","arguments":{}}}
```

```json
{"jsonrpc":"2.0","id":21,"method":"tools/call","params":{"name":"review_code","arguments":{"provider":"gemini"}}}
```

```json
{"jsonrpc":"2.0","id":22,"method":"tools/call","params":{"name":"review_code","arguments":{"diff_text":"diff --git a/x.py b/x.py\n+print('debug')"}}}
```

**Expected response shape:**
```json
{"status": "success", "review": "## Code Review\n\n..."}
```

---

#### 2.2.8 `full_review` — Optional provider

```json
{"jsonrpc":"2.0","id":30,"method":"tools/call","params":{"name":"full_review","arguments":{}}}
```

```json
{"jsonrpc":"2.0","id":31,"method":"tools/call","params":{"name":"full_review","arguments":{"provider":"deepseek"}}}
```

**Expected response shape:**
```json
{"status": "success", "review": "## Full Code Review\n\n..."}
```

---

#### 2.2.9 `generate_pr_description` — Optional provider

```json
{"jsonrpc":"2.0","id":40,"method":"tools/call","params":{"name":"generate_pr_description","arguments":{}}}
```

```json
{"jsonrpc":"2.0","id":41,"method":"tools/call","params":{"name":"generate_pr_description","arguments":{"provider":"gemini"}}}
```

**Expected response shape:**
```json
{"status": "success", "commit_message": "feat: add new feature", "pr_description": "## Summary\n\nThis PR adds..."}
```

---

#### 2.2.10 `run_linter` — No params

```json
{"jsonrpc":"2.0","id":50,"method":"tools/call","params":{"name":"run_linter","arguments":{}}}
```

**Expected response shape (pass):**
```json
{"status": "success", "error_count": 0, "warning_count": 0, "errors": [], "warnings": [], "passed": true}
```

**Expected response shape (fail):**
```json
{"status": "success", "error_count": 2, "warning_count": 1, "errors": ["console.log() found on line 5", "TODO comment on line 12"], "warnings": ["Consider adding a docstring"], "passed": false}
```

---

#### 2.2.11 `analyze_blame` — Required: file_path, start_line, end_line

```json
{"jsonrpc":"2.0","id":60,"method":"tools/call","params":{"name":"analyze_blame","arguments":{"file_path":"src/main.py","start_line":"10","end_line":"20"}}}
```

**Expected response shape (success):**
```json
{
  "status": "success",
  "entries": [
    {"hash": "abc1234", "author": "...", "date": "...", "message": "Initial commit", "classification": "ORIGIN"},
    {"hash": "def5678", "author": "...", "date": "...", "message": "Refactor loop", "classification": "REFACTORING"}
  ]
}
```

**Expected response shape (file not found):**
```json
{"status": "error", "message": "File not found: nonexistent.py"}
```

**Expected response shape (no data):**
```json
{"status": "no_data", "message": "No traceable commits found for this region."}
```

---

#### 2.2.12 `generate_issue` — Optional context_type

```json
{"jsonrpc":"2.0","id":70,"method":"tools/call","params":{"name":"generate_issue","arguments":{}}}
```

```json
{"jsonrpc":"2.0","id":71,"method":"tools/call","params":{"name":"generate_issue","arguments":{"context_type":"diff"}}}
```

```json
{"jsonrpc":"2.0","id":72,"method":"tools/call","params":{"name":"generate_issue","arguments":{"context_type":"history"}}}
```

```json
{"jsonrpc":"2.0","id":73,"method":"tools/call","params":{"name":"generate_issue","arguments":{"context_type":"blame"}}}
```

**Expected response shape:**
```json
{"status": "success", "title": "Add user authentication", "body": "## What\n\n...\n## Why\n\n...\n## Where\n\n...\n## How\n\n..."}
```

---

## 3. Resources

### 3.1 List Resources — `resources/list`

```json
{"jsonrpc":"2.0","id":100,"method":"resources/list","params":{}}
```

**16 resources:**
| URI | MIME Type |
|-----|-----------|
| `skill://list` | application/json |
| `skill://pr` | text/markdown |
| `skill://commit` | text/markdown |
| `skill://review` | text/markdown |
| `skill://filereview` | text/markdown |
| `skill://issue` | text/markdown |
| `skill://blame` | text/markdown |
| `linter://config` | text/yaml |
| `prompt://list` | application/json |
| `prompt://review` | text/markdown |
| `prompt://commit` | text/markdown |
| `prompt://pr` | text/markdown |
| `prompt://linter` | text/markdown |
| `prompt://issue` | text/markdown |
| `prompt://blame` | text/markdown |
| `prompt://explore` | text/markdown |

---

### 3.2 Read Resources — `resources/read`

```json
{"jsonrpc":"2.0","id":110,"method":"resources/read","params":{"uri":"skill://list"}}
```

```json
{"jsonrpc":"2.0","id":111,"method":"resources/read","params":{"uri":"skill://pr"}}
```

```json
{"jsonrpc":"2.0","id":112,"method":"resources/read","params":{"uri":"linter://config"}}
```

```json
{"jsonrpc":"2.0","id":113,"method":"resources/read","params":{"uri":"prompt://list"}}
```

```json
{"jsonrpc":"2.0","id":114,"method":"resources/read","params":{"uri":"prompt://review"}}
```

```json
{"jsonrpc":"2.0","id":115,"method":"resources/read","params":{"uri":"prompt://explore"}}
```

---

## 4. Prompts

### 4.1 List Prompts — `prompts/list`

```json
{"jsonrpc":"2.0","id":200,"method":"prompts/list","params":{}}
```

**7 prompts:**
| Name | Description |
|------|-------------|
| Review PR | Full code review of current branch against origin/main |
| Generate Commit Message | Conventional Commits message from uncommitted changes |
| Create PR Description | Complete PR description from full branch diff |
| Run Code Linter | Static linter on uncommitted changes |
| Create Issue from Diff | Structured issue (What/Why/Where/How) from diff |
| Trace Code Origin | git blame + AI for a file region |
| Explore Project Context | Branch info + available skill templates |

---

### 4.2 Get Prompt — `prompts/get`

```json
{"jsonrpc":"2.0","id":210,"method":"prompts/get","params":{"name":"Review PR"}}
```

```json
{"jsonrpc":"2.0","id":211,"method":"prompts/get","params":{"name":"Generate Commit Message"}}
```

```json
{"jsonrpc":"2.0","id":212,"method":"prompts/get","params":{"name":"Explore Project Context"}}
```

---

## 5. CLI Direct Invocation (no JSON-RPC server)

For quick testing without starting the stdio server, use `gitpr-mcp --tool`:

```bash
# List all available tools
gitpr-mcp --tool

# Invoke a tool directly
gitpr-mcp --tool get_git_context

# Pass arguments as JSON
gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"src/main.py","start_line":"10","end_line":"20"}'

# Pass optional params to AI tools
gitpr-mcp --tool generate_commit_message --tool-args '{"provider":"gemini","diff_text":"+print(\"hello\")"}'

# Print the full tools catalog (same as tools/list but via CLI)
gitpr-mcp --list
```

All CLI output goes to **real stdout** (not stderr). Stderr contains diagnostics only.

---

## 6. Test Flow (Minimal Integration Sequence)

A complete happy-path test that an MCP client would execute:

```
# Step 1: Initialize
→ {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
← {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{},"resources":{},"prompts":{}},"serverInfo":{"name":"gitpr","version":"0.0.30"}}}

# Step 2: Notify initialized
→ {"jsonrpc":"2.0","method":"notifications/initialized"}

# Step 3: Discover tools
→ {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
← {"jsonrpc":"2.0","id":2,"result":{"tools":[...]}}

# Step 4: Call a no-param tool
→ {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_git_context","arguments":{}}}
← {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\"branch\":\"main\",\"repository\":\"org/repo\"}"}]}}

# Step 5: Call a tool with params
→ {"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"analyze_blame","arguments":{"file_path":"src/main.py","start_line":"1","end_line":"10"}}}
← {"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"{\"status\":\"success\",\"entries\":[...]}"}]}}
```

**Important:** Tool results are wrapped in `{"content": [{"type": "text", "text": "<tool-json-output>"}]}`
by the FastMCP framework. The `text` field contains the JSON string returned by each tool function.

---

## 7. Error Responses

### Tool not found (invalid params)
```json
{"jsonrpc":"2.0","id":999,"error":{"code":-32602,"message":"Invalid params: ..."}}
```

### Method not found
```json
{"jsonrpc":"2.0","id":999,"error":{"code":-32601,"message":"Method not found"}}
```

### Parse error (invalid JSON)
```json
{"jsonrpc":"2.0","id":null,"error":{"code":-32700,"message":"Parse error"}}
```

### Internal tool error (wrapped by _safe_call)
The tool returns a JSON error string inside a successful `tools/call` response:
```json
{"jsonrpc":"2.0","id":99,"result":{"content":[{"type":"text","text":"{\"status\":\"error\",\"message\":\"AI failed to generate a review.\"}"}]}}
```
