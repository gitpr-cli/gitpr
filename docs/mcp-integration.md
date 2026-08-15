# MCP Integration — GitPR

GitPR supports the **Model Context Protocol (MCP)**, enabling direct integration
with MCP-compatible editors and AI tools like **VS Code**, **Cursor**, and
**Claude Desktop**.

When connected, GitPR exposes its AI-powered capabilities as tools that your
editor's AI assistant can invoke — without leaving the editor or opening a terminal.

## Quick Install

The easiest way to configure MCP is with the built-in installer:

```bash
# Install for a specific editor
gitpr-mcp --install vscode      # Creates .vscode/mcp.json
gitpr-mcp --install cursor      # Creates .cursor/mcp.json
gitpr-mcp --install claude-code # Creates .mcp.json
gitpr-mcp --install claude      # Updates Claude Desktop config
gitpr-mcp --install zed         # Updates Zed settings

# Auto-detect editors and install for all found
gitpr-mcp --install auto
gitpr-mcp --install              # Same as --install auto
```

The installer:

* Creates the editor config directory if it doesn't exist
* Merges with existing config — never overwrites other servers
* Shows which editors were configured
* Is idempotent — safe to run multiple times

## Alternative Entry Point (`gitpr --mcp`)

The main `gitpr` CLI also exposes a **hidden `--mcp` alias** that starts the
MCP server directly:

```bash
gitpr --mcp    # Starts the MCP server (same as gitpr-mcp)
```

This alias always starts the server — it does not support the `--list`,
`--install`, or `--tool` modes (use `gitpr-mcp` for those). The startup
banner is suppressed automatically so stdout stays clean for the JSON-RPC
transport.

## Direct CLI Invocation

You can invoke any MCP tool directly from the terminal without starting the server.
This is useful for debugging, scripting, and testing tools without an MCP client.

```bash
# No-param tools
gitpr-mcp --tool get_git_context
gitpr-mcp --tool analyze_diff
gitpr-mcp --tool run_linter

# Tools with parameters (JSON)
gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"src/main.py","start_line":"10","end_line":"20"}'
gitpr-mcp --tool generate_commit_message --tool-args '{"provider":"gemini"}'
gitpr-mcp --tool generate_issue --tool-args '{"context_type":"history"}'

# List all available tools and their parameters
gitpr-mcp --tool
```

JSON output goes to stdout; all diagnostic messages (spinners, banners, logs) go to
stderr. The `.env` configuration is loaded automatically, so API keys work without
interactive prompts.

> **Note:** On Windows Command Prompt, use double quotes for `--tool-args` and
> escape inner quotes: `"{\"file_path\":\"src/main.py\",\"start_line\":\"10\"}"`.
> PowerShell and Unix shells accept single quotes as shown above.

## Available Tools

| Tool | Description |
|------|-------------|
| `get_git_context` | Current branch, repository name, and remote URL |
| `analyze_diff` | Raw git diff of uncommitted changes (`git diff HEAD`) |
| `list_unstaged_files` | Uncommitted files categorized as new, modified, or deleted (structured JSON) |
| `analyze_unstaged_diff` | Unstaged changes only (`git diff` — index vs working tree) |
| `get_full_diff` | Full diff against origin/main (`git fetch` + diff) |
| `generate_commit_message` | AI-generated Conventional Commits message |
| `review_code` | AI code review of local (uncommitted) changes |
| `full_review` | AI code review of all changes since origin/main |
| `generate_pr_description` | Complete PR description (title + body) |
| `run_linter` | Static linter against `.gitpr.linter.yml` rules |
| `analyze_blame` | Git blame + AI classification (ORIGIN vs REFACTORING) |
| `generate_issue` | Structured issue from diff, history, or blame context |

## Available Resources

| URI | Content |
|-----|---------|
| `skill://list` | List of all available skill template URIs |
| `skill://pr` | Custom PR description AI instructions |
| `skill://commit` | Custom commit message AI instructions |
| `skill://review` | Custom code review AI instructions |
| `skill://filereview` | Custom file review AI instructions |
| `skill://issue` | Custom issue generation AI instructions |
| `skill://blame` | Custom blame analysis AI instructions |
| `linter://config` | YAML linter rules (`.gitpr.linter.yml`) |

### Prompt Resources

Prompt templates are also exposed as resources — and as selectable prompts in
your editor's AI chat:

| URI | Content |
|-----|---------|
| `prompt://list` | List of all available prompt template URIs |
| `prompt://review` | Full code review of the current branch |
| `prompt://commit` | Conventional Commits message generation |
| `prompt://pr` | Pull Request description generation |
| `prompt://linter` | Static linter run on changes |
| `prompt://issue` | Structured issue generation from changes |
| `prompt://blame` | Code origin tracing with git blame + AI |
| `prompt://explore` | Project context exploration and available skills |

Custom prompts installed in `~/.gitpr/plugins/` are registered automatically
as `prompt://plugin/<name>`.

The server also exposes these built-in **prompts** (starter messages selectable
in the editor's AI chat): *Review PR*, *Generate Commit Message*, *Create PR
Description*, *Run Code Linter*, *Create Issue from Diff*, *Trace Code Origin*,
and *Explore Project Context*.

## Editor Configuration

### VS Code

Create `.vscode/mcp.json` in your project root:

```json
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

Or install globally via VS Code settings.

### Cursor

Create `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "gitpr": {
      "type": "stdio",
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Claude Code

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "gitpr": {
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gitpr": {
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Zed

Add to `settings.json`:

```json
{
  "context_servers": {
    "gitpr": {
      "command": {
        "path": "gitpr-mcp",
        "args": []
      }
    }
  }
}
```

## Usage Examples

After connecting GitPR via MCP, you can use natural language in your editor's
AI chat:

- **"Review my current changes"** → calls `review_code`
- **"Generate a commit message for these changes"** → calls `generate_commit_message`
- **"Create a PR description from my branch"** → calls `generate_pr_description`
- **"Run the linter on my diff"** → calls `run_linter`
- **"Trace the origin of lines 10-20 in src/main.py"** → calls `analyze_blame`
- **"Generate an issue from my changes"** → calls `generate_issue`
- **"What branch am I on?"** → calls `get_git_context`

## Prerequisites

1. **GitPR installed:** `pip install gitpr-cli` or the standalone binary
2. **API keys configured:** Run `gitpr` once interactively to set up API keys,
   or create `~/.gitpr/.env` manually with your encrypted keys
3. **An MCP-compatible editor:** VS Code, Cursor, Zed, Claude Desktop, etc.

## How It Works

The `gitpr-mcp` command starts an MCP server over **stdio transport** (standard
input/output). The editor launches it as a child process and communicates via
JSON-RPC 2.0 messages.

To keep the JSON-RPC channel clean, GitPR's terminal output (banners, spinners,
colored messages) is automatically redirected to stderr when running in MCP mode.
This requires no configuration — it happens transparently.

## Troubleshooting

### The editor doesn't discover GitPR tools
- Verify `gitpr-mcp` is on your PATH: `which gitpr-mcp` (Linux/macOS) or `where gitpr-mcp` (Windows)
- Run `pip install -e .` from the GitPR source directory if developing locally
- Check editor logs for MCP connection errors

### Tools return errors
- Ensure API keys are configured in `~/.gitpr/.env`
- Check stderr output from the MCP server (visible in editor logs)
- Run `gitpr --help` normally to verify the CLI works

### "Interactive prompt is unavailable" error
- You need to pre-configure API keys in `~/.gitpr/.env` — MCP mode cannot prompt interactively
- Run `gitpr` once in a terminal to complete the initial setup
