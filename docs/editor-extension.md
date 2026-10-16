# GitPR Editor Extension (VS Code & Cursor)

The **GitPR Editor Extension** brings AI-powered Conventional Commits, Code Reviews, Pull Request generation and publishing, and Unified CI Check diagnostics directly into **VS Code** and **Cursor** as a lightweight **MCP thin client**.

---

## Architecture: True Thin Client over MCP

Instead of duplicating prompt templates, diff parsers, or credential management in TypeScript, the extension communicates over `stdio` with your local `gitpr-mcp` server (`@modelcontextprotocol/sdk`):

- **One Session per Workspace Folder**: The extension spawns `gitpr-mcp` lazily on the first command (with `cwd` set to the workspace folder root) and keeps the session persistent, reconnecting automatically if the process exits.
- **Contract Handshake**: On connect, the extension calls `listTools` and verifies that all required tools (`get_git_context`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_check`, `publish_pull_request`) are present. If your `gitpr-cli` is outdated, it shows an upgrade prompt (`pip install --upgrade gitpr-cli`).
- **Zero Parallel Configuration**: API keys, SCM tokens, and preferences remain in `~/.gitpr/.env` encrypted with Fernet. The extension never asks for or stores secrets.
- **Defense-in-Depth Secret Masking**: Both the Python MCP server (`mask_sensitive_text`) and the TypeScript extension (`maskSensitiveText`) redact tokens (`ghp_*`, `glpat-*`, `sk-*`, `AIza*`, `Bearer *`, private keys) before displaying notifications or writing to the `GitPR` OutputChannel.

---

## Installation

### 1. Prerequisite: `gitpr-cli`

Ensure `gitpr-cli` is installed and configured on your machine:

```bash
pip install --upgrade gitpr-cli
gitpr --install
```

### 2. Install the Extension (VS Code & Cursor)

Both VS Code and Cursor share the same VSIX package (`natanfiuza.gitpr`):

- **VS Code Marketplace**: Search for `GitPR` (`natanfiuza.gitpr`).
- **Cursor / Open VSX**: Search for `GitPR` or install from `.vsix`.
- **From Source (Local VSIX)**:
  ```bash
  cd extensions/vscode
  npm install
  npm run compile
  npm run package
  code --install-extension gitpr-0.1.0.vsix
  ```

---

## Commands & Workflows

All commands are available from the **Command Palette** (`Ctrl+Shift+P` / `Cmd+Shift+P`), and the 4 core actions (**Commit**, **Review**, **PR**, **Check**) are pinned to the **Status Bar**.

| Command | MCP Tool Called | Behavior |
|---|---|---|
| `GitPR: Commit (Generate Message)` | `generate_commit_message` | Generates a Conventional Commits draft and populates the VS Code **Source Control** input box (with clipboard notification fallback). Never commits automatically. |
| `GitPR: Review (Local Changes)` | `review_code(mentor=false)` | Reviews uncommitted changes (`git diff HEAD`) and opens a side-by-side Markdown preview. |
| `GitPR: Full Review (Against Base Branch)` | `full_review(mentor=false)` | Runs `git fetch` and reviews the entire branch against `origin/main`, opening a Markdown preview. |
| `GitPR: Review (Junior Mentor Mode)` | `review_code(mentor=true)` | Appends didactic Junior Mentor explanations to the code review preview. |
| `GitPR: Generate PR Draft` | `generate_pr_description(explain=false)` | Opens an editable Markdown PR draft (`line 1` = PR title, remainder = PR body). |
| `GitPR: Generate PR Draft (with Reviewer Guide)` | `generate_pr_description(explain=true)` | Generates the editable PR draft including the **Explain my PR** Reviewer Guide section. |
| `GitPR: Publish PR from Active Draft` | `publish_pull_request` | Reads the active edited Markdown draft, asks for modal confirmation (`Publish` or `Publish as Draft`), and creates the PR on your configured forge (GitHub, GitLab, Bitbucket, Azure DevOps). |
| `GitPR: Check (Unified Linter & Security Diagnostics)` | `run_check` | Runs the unified check pipeline and populates the **Problems** panel with clickable file, line, and severity diagnostics. |

### Two-Step Pull Request Publishing

Publishing is never blind:
1. Run **`GitPR: Generate PR Draft`** (or **`Generate PR Draft (with Reviewer Guide)`**).
2. Review and edit the generated Markdown document. The first non-empty line is used as the Pull Request title, and the rest of the document is the body.
3. Click the **`Publish PR`** icon in the editor title bar (or run **`GitPR: Publish PR from Active Draft`**).
4. Confirm in the modal dialog. The server returns structured outcomes:
   - `needs_push` → offers a **Push & Publish** button via `vscode.git`.
   - `already_exists` → offers to open the existing PR in your browser.
   - `auth_required` → offers to open a terminal running `gitpr` to authenticate.
   - `success` → offers to open the newly created PR in your browser.

---

## Extension Settings

Configure via VS Code `settings.json`:

```json
{
  "gitpr.mcpCommand": "gitpr-mcp",
  "gitpr.mcpArgs": [],
  "gitpr.provider": "",
  "gitpr.check.useAI": false
}
```

| Setting | Type | Default | Description |
|---|---|---|---|
| `gitpr.mcpCommand` | `string` | `"gitpr-mcp"` | Executable used to launch the GitPR MCP server. |
| `gitpr.mcpArgs` | `string[]` | `[]` | Additional CLI arguments passed to the MCP server executable. |
| `gitpr.provider` | `string` | `""` | Optional AI provider override (`gemini`, `deepseek`, `ollama`). Empty inherits `~/.gitpr/.env`. |
| `gitpr.check.useAI` | `boolean` | `false` | Enables AI review inside `GitPR: Check`. Disabled by default so interactive editor checks stay fast and token-free. |

---

## Internationalization (i18n) & Telemetry

- **Extension UI Locales**: Packaged with `en`, `pt-br`, `es`, and `fr` bundles (`package.nls.*.json` and `l10n/bundle.l10n.*.json`). Note: VS Code does not provide a separate `pt-pt` display language pack, so Portuguese (Portugal) users receive the `pt-br` UI bundle while server-generated content respects `GITPR_LANG=pt_pt`.
- **Local Telemetry Only**: The extension emits zero telemetry and opens no network connections. The local MCP server records `mcp:check` and `mcp:publish_pr` events in your local SQLite ledger (`~/.gitpr/metrics/telemetry.db`).
