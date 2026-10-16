# GitPR Editor Extension (VS Code & Cursor)

**GitPR** brings AI-powered Conventional Commits, Code Reviews, Pull Request generation/publishing, and Unified CI Check diagnostics directly into **VS Code** and **Cursor** as a lightweight **MCP thin client**.

## Features

- **Zero Duplicated Logic**: Communicates over stdio with the local `gitpr-mcp` server. All prompts, skills (`.gitpr/skill/`), Fernet-encrypted credentials (`~/.gitpr/.env`), and baselines remain managed by `gitpr-cli`.
- **Commands & Status Bar Shortcuts**:
  - `GitPR: Commit (Generate Message)` — Generates a Conventional Commits message and populates the Source Control input box (never commits automatically).
  - `GitPR: Review (Local Changes)` — Runs AI code review on `git diff HEAD` and opens a Markdown preview.
  - `GitPR: Full Review (Against Base Branch)` — Reviews the full branch diff against `origin/main`.
  - `GitPR: Review (Junior Mentor Mode)` — Appends didactic explanations for review findings.
  - `GitPR: Generate PR Draft` — Generates an editable Pull Request draft (`line 1` = title, rest = Markdown body).
  - `GitPR: Generate PR Draft (with Reviewer Guide)` — Includes the `Explain my PR` Reviewer Guide section.
  - `GitPR: Publish PR from Active Draft` — Confirms in a modal and publishes the edited draft to your SCM forge (GitHub, GitLab, Bitbucket, Azure DevOps).
  - `GitPR: Check (Unified Linter & Security Diagnostics)` — Runs `gitpr check` and populates the VS Code **Problems** panel with file, line, and severity diagnostics.

## Requirements

Install and configure `gitpr-cli` (`>= 0.0.37`):

```bash
pip install --upgrade gitpr-cli
gitpr --install
```

## Extension Settings

| Setting | Default | Description |
|---|---|---|
| `gitpr.mcpCommand` | `"gitpr-mcp"` | Executable used to launch the GitPR MCP server. |
| `gitpr.mcpArgs` | `[]` | Additional arguments passed to the MCP server executable. |
| `gitpr.provider` | `""` | Optional AI provider override (`gemini`, `deepseek`, `ollama`). Empty inherits `~/.gitpr/.env`. |
| `gitpr.check.useAI` | `false` | Enable AI code review inside `GitPR: Check` (disabled by default for fast, token-free editor checks). |

## Privacy & Security

- **100% Local Transport**: The extension opens no external network connections; it communicates exclusively with your local `gitpr-mcp` process over stdio.
- **No Plaintext Secrets**: API keys and SCM tokens are never stored in VS Code settings. Defense-in-depth masking redacts sensitive tokens from notifications and OutputChannel logs.
