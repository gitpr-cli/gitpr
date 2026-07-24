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
gitpr-mcp --install claude-code # Creates .claude/mcp.json
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

## Available Tools

| Tool | Description |
|------|-------------|
| `get_git_context` | Current branch, repository name, and remote URL |
| `analyze_diff` | Raw git diff of uncommitted changes (`git diff HEAD`) |
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

Create `.claude/mcp.json` in your project root:

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
