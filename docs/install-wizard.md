# GitPR Interactive Setup Wizard (`--install`)

The `gitpr --install` command runs an interactive guided wizard that prepares your project environment with all the essential GitPR configurations in a single flow. It consolidates several manual setup steps into one seamless experience.

## ✨ What It Does

The wizard guides you through **4 steps**, asking for confirmation before each one:

| Step | What it configures | Equivalent command |
|------|-------------------|--------------------|
| 1. Skill Templates | Downloads `.gitpr.*.md` and `.gitpr.linter.yml` template files | `gitpr --skill` |
| 2. Git Hooks | Installs `pre-commit` and `prepare-commit-msg` hooks locally | `gitpr --installhooks` |
| 3. MCP Configuration | Auto-detects and configures editors (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 4. API Key Check | Verifies or prompts for your AI provider API key | First-run wizard |

At the end, a link to this documentation is displayed for reference.

## 🚀 How to Use

```bash
gitpr --install
```

The wizard will:
1. Display a welcome header
2. For each step: explain what it does → ask for confirmation (`[Y/n]`) → execute or skip
3. Show results and the documentation URL when finished

Each step can be **skipped** by answering `n` (no) when prompted. Skipped steps can be run later individually using their equivalent commands.

## 📋 Prerequisites

- **Internet connection:** Required for downloading templates, hooks, and checking for updates.
- **Git repository:** The command must be run inside a git project (required for hooks and diff analysis).
- **Python environment:** GitPR must be installed and accessible in your PATH.

## 📖 Step-by-Step Details

### Step 1 — Skill Templates

Downloads AI context template files into your project's `.gitpr/skill/` folder:

- `.gitpr.commit.md` — Rules for commit message generation
- `.gitpr.pr.md` — Required structure for PR descriptions
- `.gitpr.review.md` — Architectural focus for code reviews
- `.gitpr.filereview.md` — Cohesion and coupling rules for file audits
- `.gitpr.issue.md` — Structure for standardized issue generation
- `.gitpr.blame.md` — Focus for legacy code tracing
- `.gitpr.linter.yml` — Custom static analysis rules

These files are **never overwritten** if they already exist. Edit them freely to customize AI behavior for your team's conventions.

📚 See also: [Skills and Templates System](skill-template.md)

### Step 2 — Git Hooks

Installs two local Git hooks into `.git/hooks/`:

- **`pre-commit`** — Runs the static linter (`.gitpr.linter.yml`) before every commit, blocking code that violates your rules.
- **`prepare-commit-msg`** — Uses AI to generate a Conventional Commits message and injects it into your commit editor.

This enables the **Shift-Left** practice — catching issues on the developer's machine before they reach CI/CD or code review.

📚 See also: [Local Git Hooks](git-hooks-locais.md)

### Step 3 — MCP Configuration

Auto-detects which AI-powered editors you use and creates the necessary configuration files:

| Editor | Config file created |
|--------|---------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Once configured, you can use natural language in your editor's AI chat to invoke GitPR tools: "Review my changes", "Generate a commit message", "Create a PR description", etc.

Existing config files are **merged** — other MCP servers are never overwritten.

📚 See also: [MCP Integration](mcp-integration.md)

### Step 4 — API Key Configuration

Checks whether your AI provider API key is already configured:

- **If configured:** Displays a success message — you're ready to go.
- **If missing:** Offers to set it up interactively. The key is encrypted with Fernet (symmetric encryption) and stored securely in `~/.gitpr/.env`.

You can skip this step and configure it later by running `gitpr` (which triggers the first-run wizard) or by editing `~/.gitpr/.env` directly.

📚 See also: [AI Providers](providers-ia.md)

## 🔄 Running Individual Steps Later

If you skipped a step, you can always run its equivalent command later:

```bash
gitpr --skill              # Step 1: Download templates
gitpr --installhooks    # Step 2: Install Git hooks
gitpr-mcp --install auto   # Step 3: Configure MCP
gitpr                      # Step 4: API key (first-run wizard)
```

## ⚙️ CI/CD Environments

In CI/CD pipelines (detected by `CI` or `GITHUB_ACTIONS` environment variables), GitPR will **not** prompt interactively for API keys. Configure your key in advance using environment variables or GitHub Secrets.

---
**Pro tip:** Run `gitpr --install` on every new clone to get the full GitPR experience set up in seconds.
