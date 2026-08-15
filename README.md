
# **GitPR CLI 🚀**

<p align="center">
  <img src="https://raw.githubusercontent.com/natanfiuza/gitpr/main/docs/logo.png" alt="GitPR Logo" width="150">
</p>

GitPR CLI is a command-line automation tool that uses **Google Gemini** and **DeepSeek** artificial intelligence to analyze your code changes (git diff) or entire files. The tool automatically generates commit messages in the *Conventional Commits* standard, detailed Pull Request descriptions, and deep Code Reviews aimed at reducing technical debt.

🌐 **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/) · 📂 **Repository:** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)

----

## ⚡ **Quick Start**

### **1. Installation via PyPI**

Install GitPR CLI using `pip`:

```bash
pip install gitpr-cli
```

### **2. Initializing in a Repository**

To set up GitPR in a folder of a new repository, run:

```bash
gitpr --install
```

> **Guided Setup:** Guided configuration that downloads skill templates, installs Git Hooks, configures MCP for your editors, and verifies the API key for your AI provider.  
> 📖 **Full Documentation:** [https://gitpr.natanfiuza.dev.br/docs/install-wizard?lang=en_us](https://gitpr.natanfiuza.dev.br/docs/install-wizard?lang=en_us)

## **🛠️ Technologies and Libraries Used**

This project was developed in Python and uses the following main libraries:

* [**Click**](https://click.palletsprojects.com/): To create a robust and user-friendly command-line interface (CLI).
* [**Google GenAI**](https://pypi.org/project/google-genai/): Official SDK for direct integration with the Gemini API.
* [**OpenAI**](https://pypi.org/project/openai/): Library used due to its full compatibility with the powerful **DeepSeek** API.
* [**Python-dotenv**](https://pypi.org/project/python-dotenv/): For secure environment variable management.
* [**Pytest**](https://docs.pytest.org/): For running unit tests in a simple, colorful, and readable way in the console.
* [**Cryptography**](https://cryptography.io/): To ensure your `GEMINI_API_KEY` is stored encrypted and securely on disk.
* [**PyYAML**](https://pyyaml.org/): Used to read and process the custom static analysis rules from the `.gitpr.linter.yml` file.
* [**Textual**](https://textual.textualize.io/): Powerful library for creating Terminal Graphical Interfaces (TUI), used in the interactive issue generation and editing panel.
* [**Requests**](https://pypi.org/project/requests/): Elegant and robust library for HTTP requests, used to communicate with the GitHub REST API.
* [**MCP**](https://pypi.org/project/mcp/): Official Python SDK for the Model Context Protocol, enabling GitPR to integrate directly with AI-powered editors and IDEs.

----

## 📦 How to Compile the Executable Locally

If you want to generate your own binary from the source code, we use **PyInstaller**. Make sure you are in the project root directory with the virtual environment configured.

1. Install development dependencies (if you haven't already):
   ```bash
   pipenv install --dev
   ```

2. Run the build command pointing to our entry point (`run.py`):
   ```bash
   pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py
   ```
> **Technical note:** The `--onefile` flag ensures all Python, libraries, and dependencies are compressed into a single binary, while `--paths src` helps the compiler find our `core.py` and `config.py` files. 🛠️

After running this command, PyInstaller will create some folders (`build` and `dist`).
Your final ready-to-use file will be inside the **`dist/`** folder named `gitpr` (or `gitpr.exe` on Windows).


----

## 🧪 Running Tests

To ensure the Git capture logic and AI integration are working correctly, we use unit tests.

1. Install test dependencies (if you haven't already):
   ```bash
   pipenv install --dev pytest
   ```

2. Run the tests with the command:
   ```bash
   pipenv run pytest -v
   ```
Pytest will automatically detect files inside the `tests/` folder and display a detailed execution report.

----
## **⚙️ Installation and Configuration**

### **Using the Executable (Recommended)**

1. Download the gitpr executable file from the "Releases" tab on GitHub.
2. Move the executable to a folder that is in your PATH (e.g.: /usr/local/bin on Linux/Mac or your user folder on Windows).
3. On the first run, the wizard will guide you:
   ```bash
   $ gitpr
   ```
```bash
🚀 Intelligent PR Automation with AI

🔧 First run detected! Let's configure GitPR CLI.

🔑 Enter your GEMINI_API_KEY:

📄 Default output filename pattern [{branch}_{datetime}_PR_DESC.md]:
```
*Note: Your configuration will be securely saved in the `~/.gitpr/.env` file.*

> **🔒 Security Note:** GitPR CLI uses symmetric encryption (Fernet). Your API key is stored as a hash in the `.env` file, and the master key for decryption is automatically generated in `~/.gitpr/secret.key`. **Never share your secret.key file.**

### From Source Code

1. Clone the repository: `git clone https://github.com/natanfiuza/gitpr.git`

2. Enter the folder: `cd gitpr`

3. Set up the environment:
```bash
pipenv install google-genai openai python-dotenv click cryptography
```
4. Run: pipenv run python src/main.py

## **💻 How to Use**

GitPR has a powerful default behavior and several advanced options to assist you in your day-to-day as a developer.

### **Default Behavior (Pull Request)**
Simply run the bare command in your terminal:
```bash
gitpr
```
The tool will sync with the remote (`git fetch`), compare your changes with the remote main branch (e.g.: `origin/main`), and generate a Markdown file (e.g.: `feature-login_20260421110134_PR_DESC.md`) at the root of your project with the complete suggestion for your Pull Request.

### **Advanced Options and Commands**
You can pass the following *flags* for specific actions:

* `-c` or `--commit`: Runs a local `git diff` and displays **only the suggested commit message**.
* `-r` or `--review`: Performs a detailed **Code Review** of local changes.
* `-f` or `--fullreview`: Performs a **Full Code Review** analyzing all changes since the remote branch.
* `-i <file>` or `--input <file>`: **Full File Audit.** Must be used together with `-r` or `-f`; it ignores git history and does a Code Review of the entire file. Excellent for acting as a consultant on legacy code refactoring.
* `--provider <gemini|deepseek|ollama>`: Forces the use of a specific AI only for this execution, ignoring your default saved in `.env`.
* `--lang <code>`: Forces the interface language for this execution (e.g.: `en_us`, `pt_br`). Overrides `GITPR_LANG` in `.env` without persisting the change.
* `-ch` or `--chat`: Opens the **Interactive Pair Programming Chat** — a TUI terminal where the AI sees your current diff and maintains a contextual conversation. Features memory per branch, slash commands (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patching (F5), diff refresh (F2), and session export (F6).
* `-l` or `--linter`: Runs **only the local static linter** (no AI calls). Ideal for use in CI/CD pipelines to block non-compliant code.
* `--status`: Lists uncommitted file changes categorized as **new**, **modified**, and **deleted** — fast, no AI, no network. 📖 [Full docs](https://github.com/natanfiuza/gitpr/blob/main/docs/git-status.md)
* `--no-unstaged-check`: Skips the unstaged files verification before AI processing for a single invocation. Equivalent to `GITPR_SKIP_UNSTAGED_CHECK=true` for one run. 📖 [Full docs](https://github.com/natanfiuza/gitpr/blob/main/docs/git-status.md)
* `--linter-setup`: **Interactive external linter wizard.** Guides you through installing and configuring external linters (ESLint, PHPCS, Stylelint) as a Checkstyle XML bridge. 📖 [Full docs](https://github.com/natanfiuza/gitpr/blob/main/docs/linter-regras-customizadas.md)
* `--mcp`: Starts GitPR as an **MCP server** (Model Context Protocol) on stdio transport. Enables integration with VS Code, Cursor, Claude Desktop, and other MCP-compatible editors — exposing all GitPR AI capabilities as 10 annotated tools, 15 resources, and 7 pre-built prompts directly inside your IDE. Also available as the standalone `gitpr-mcp` command.
* `--plugins`: Lists all **globally installed plugins** — custom linter packs from `~/.gitpr/plugins/linter/` and MCP prompt templates from `~/.gitpr/plugins/prompts/`. These plugins apply across all your projects without duplication. 📖 [Full docs](https://github.com/natanfiuza/gitpr/blob/main/docs/plugins-system.md)
* `--install`: **Interactive Setup Wizard.** Runs a guided 4-step setup: downloads skill templates, installs Git hooks, configures MCP for detected editors, and checks/requests your AI provider API key. Each step asks for confirmation before proceeding.
* `-ih` or `--installhooks`: Automatically installs **local Git Hooks** (`pre-commit` and `prepare-commit-msg`) in your repository.
* `-s` or `--skill`: Creates the AI context template files (`.gitpr.commit.md`, `.gitpr.pr.md`, `.gitpr.review.md`, `.gitpr.filereview.md`, `.gitpr.issue.md`, `.gitpr.blame.md`) and the Linter (`.gitpr.linter.yml`) at the project root.
* `-is` or `--issue`: Automatically generates a draft of a **standardized Issue** and opens an interactive interface (TUI) for editing or direct submission via REST API. This feature has **3 context engines** depending on the command combination:
  * **New Code Issue (`gitpr -is`):** Reads the current `git diff`. **Why use:** Ideal for quickly documenting the task you just finished programming, before committing.
  * **Epic/Release Issue (`gitpr -is -ht`):** Reads the full history of the current branch (Git Log + PR Cache). **Why use:** Ideal for generating consolidated documentation of an entire release or a large *feature* that took several days/commits to complete.
  * **Archaeological/Technical Debt Issue (`gitpr -is -b file:lines`):** Reads the timeline of a specific business rule. **Why use:** Ideal for documenting technical debt, explaining how a legacy code block evolved and why it needs to be refactored.
	* **PR Publisher (default):** Running `gitpr` generates the PR description with AI, saves the `.md` file to `.gitpr/reports/pr_desc/`, and opens an interactive terminal interface (TUI) to review, edit, and publish the Pull Request directly to GitHub via REST API. Before generation, it checks for unstaged files and offers a modal to manage them. Use `--no-publish` to save only the PR file locally without opening the publisher, or `--no-edit` to auto-commit pending changes (with lint validation), auto-push, and publish immediately — handling existing PR updates, optional auto-merge, and clear error feedback when merge conflicts occur. Use `--base <branch>` to change the target branch. 📖 [Full docs](https://github.com/natanfiuza/gitpr/blob/main/docs/pull-request-publication.md)
* `-h` or `--help`: Shows the general help with all options. Use together with another flag for **contextual help** (e.g.: `gitpr -h --issue`, `gitpr -h --linter`) with a direct link to the detailed documentation of each feature.
* `-u` or `--update`: Checks and installs the latest version of GitPR (Auto-Updater).

> **⚙️ Technical Note (--hook):** GitPR has a hidden flag `--hook <file>` that is triggered exclusively by the Git Hooks system in the background. It allows the AI to inject the suggested message directly into Git's temporary file, without cluttering your terminal.
>
> **⚙️ Technical Note (--pre-save):** GitPR has a hidden debug flag `--pre-save` that can be combined with any AI command (e.g.: `gitpr -c --pre-save`). Before each AI call, it saves the full payload that will be sent to the model (system instruction + prompt + character counters) to a `_{action}-{datetime}.json` file in the current folder, and then proceeds normally. Useful for inspecting very large prompts. Note: when the response comes from the local cache, no call is made and no file is generated.

### 📦 Huge Diffs (Map-Reduce)

When your diff is too large for a single AI call (over ~90k estimated tokens), GitPR automatically splits it into batches by file, asks the AI for a technical summary of each part (Map), and unifies everything into the final commit message, review, or PR description (Reduce). No flags needed — it activates on demand and shows the progress in the console.

📚 Full documentation: [docs/map-reduce-diff.md](https://github.com/natanfiuza/gitpr/blob/main/docs/map-reduce-diff.md)

## 🛡️ Local Linter (Static Analysis)

GitPR CLI allows you to define strict rules that will be validated instantly during `--review` or `--fullreview`, without depending on AI. This is ideal for preventing common errors (like `console.log` or test IPs) from reaching the repository.

### How to configure `.gitpr.linter.yml`:
When running `gitpr --skill`, a template will be generated. You can configure rules using Regular Expressions (Regex):

```yaml
rules:
  - name: "check-localhost"
    extensions: ["js", "php"] # Extensions to be validated
    regex: 'http(s)?://(localhost|127\.0\.0\.1)' # What to look for
    message: "🚨 Localhost usage detected in file {file_name}"
    ignore_comments: true # Ignores if the line is commented
    ignore_paths: # Folders or files ignored (accepts *)
      - "vendor/*"
      - "node_modules/*"
```

The Linter analyzes only the **added lines** in your `git diff`, ensuring a focused and extremely fast execution. If there are violations, they will appear highlighted at the top of your review file.

## 🧠 Multi-Model Architecture (AI-Agnostic)

GitPR is not tied to a single Artificial Intelligence. During initial setup, the user can choose their default engine. We currently support:
* **Google Gemini** (Default: `gemini-2.5-flash`)
* **DeepSeek** (Default: `deepseek-chat`)
* **Ollama** (Local) — run models locally without internet, fully compatible with the OpenAI API format

You can dynamically switch models by configuring the `GEMINI_API_MODEL` or `DEEPSEEK_API_MODEL` variables in your `~/.gitpr/.env` file, or switch in real-time using the `--provider` flag.

## 🎯 Customizable "Skills" System (Prompt Engineering)

Instead of hiding AI instructions in the source code, GitPR uses local Markdown files that act as *System Instructions*. When running `gitpr -s`, the following files are generated at the root of your project to customize the AI's "persona" according to your company's business rules:

* `.gitpr.commit.md`: Rules for generating short commit messages.
* `.gitpr.pr.md`: Required topic structure for the Pull Request description.
* `.gitpr.review.md`: Defines the architectural focus (e.g.: SOLID, Clean Code) for diff analysis.
* `.gitpr.filereview.md`: Defines strict cohesion and coupling rules for full file auditing (used with `--input`).
* `.gitpr.issue.md`: Defines the structure and level of detail required for generating standardized Issues (used with `--issue`).
* `.gitpr.blame.md`: Defines the focus of archaeological analysis for legacy code tracing (used with `--blame`).

## 🌐 Internationalization (i18n)

GitPR automatically detects your system language and displays messages in your native language. The i18n system is inspired by **Laravel's `__()` helper**:

* **Auto-detection:** On first run, GitPR detects your OS language and saves it to `~/.gitpr/.env` (`GITPR_LANG`).
* **Translation files:** Language packs are downloaded automatically from the official repository to `~/.gitpr/langs/`.
* **English fallback:** If a translation is missing, the English text is displayed directly.
* **Developer API:** Use `from src.i18n import __` and wrap all user-facing strings with `__("Your text here")`.
* **Placeholders:** Supports named parameters — `__("Downloading {file}...", file="template.md")`.

To force a specific language, set `GITPR_LANG=pt_br` or `GITPR_LANG=en` in `~/.gitpr/.env`.

> 📖 **Full developer guide:** [docs/i18n_explanation.md](https://github.com/natanfiuza/gitpr/blob/main/docs/i18n_explanation.md) — architecture, usage patterns, circular import precautions, and how to add new languages.

## 🔄 Hook Scripts Versioning & Auto-Sync

GitPR includes an automatic versioning system for Git hook scripts (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Every time you run `gitpr`, the system silently checks whether your installed hooks match the latest version and automatically updates them if needed — all while respecting your language preference.

**How it works:**
1. Reads `SCRIPTS_VERSION` and `SCRIPTS_LANG` from `~/.gitpr/.env`
2. Compares with the latest version (`__scripts_version__`) shipped with your GitPR release
3. If versions or language differ → automatically downloads and updates hooks
4. If everything matches → skips entirely (single `.env` read, zero network I/O)

**Example:**
```bash
# First run — no hooks installed yet
$ gitpr --installhooks
📥 Downloading pre-commit...
📥 Downloading prepare-commit-msg...
✅ Scripts synced successfully!

# Subsequent runs — silent checks
$ gitpr  # (no output = hooks are up to date)
```

The system supports **5 languages**: English (default), Portuguese (Brazil), Portuguese (Portugal), French, and Spanish. Scripts are thin shims — the real logic lives in the CLI, so even slightly stale hooks continue working correctly.

📚 [Full Documentation](https://gitpr.natanfiuza.dev.br/docs/hooks-versioning)

## 🔌 MCP Integration (Model Context Protocol)

GitPR can run as an **MCP server**, exposing its AI-powered capabilities as tools that your editor's AI assistant can invoke directly — no terminal needed. This enables a fully integrated workflow where you can generate commit messages, review code, run linters, trace code origins, and create issues without leaving your IDE.

### Supported Editors

| Editor | Config File |
| ------ | ----------- |
| **VS Code** | `.vscode/mcp.json` |
| **Cursor** | `.cursor/mcp.json` |
| **Claude Code** | `.mcp.json` |
| **Claude Desktop** | `claude_desktop_config.json` |
| **Zed** | `settings.json` |

### Quick Setup

Use the built-in installer to configure your editor automatically:

```bash
gitpr-mcp --install vscode    # Creates .vscode/mcp.json
gitpr-mcp --install cursor      # Creates .cursor/mcp.json
gitpr-mcp --install claude-code # Creates .mcp.json
gitpr-mcp --install claude      # Updates Claude Desktop config
gitpr-mcp --install zed         # Updates Zed settings
gitpr-mcp --install auto      # Auto-detect and install for all found
```

The installer creates the config directory if needed, merges with any existing
config (never overwrites other servers), and is safe to run multiple times.

> Manual setup is also supported — see [docs/mcp-integration.md](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md)
> for the JSON config format for each editor.

Once configured, use natural language in your editor's AI chat:

   * *"Review my current changes"* → calls `review_code`
   * *"Generate a commit message"* → calls `generate_commit_message`
   * *"Create a PR description"* → calls `generate_pr_description`
   * *"Run the linter on my diff"* → calls `run_linter`

### Available MCP Tools

| Tool | Description |
| ---- | ----------- |
| `get_git_context` | Current branch, repository name, and remote URL |
| `analyze_diff` | Git diff of uncommitted changes |
| `get_full_diff` | Full diff against origin/main |
| `generate_commit_message` | AI-generated Conventional Commits message |
| `review_code` | AI code review of local changes |
| `full_review` | AI code review of all changes since origin/main |
| `generate_pr_description` | Complete PR description (title + body) |
| `run_linter` | Static linter against `.gitpr.linter.yml` |
| `analyze_blame` | Git blame + AI classification |
| `generate_issue` | Structured issue from diff, history, or blame |
| `list_unstaged_files` | Uncommitted file changes categorized (new/modified/deleted) |
| `analyze_unstaged_diff` | Unstaged diff only (working tree vs index) |

### Direct CLI Invocation

All GitPR MCP tools can be invoked directly from the terminal without starting the stdio server:

```bash
# List all available tools with their parameter signatures
gitpr-mcp --tool

# Invoke a specific tool
gitpr-mcp --tool get_git_context
gitpr-mcp --tool review_code
gitpr-mcp --tool generate_commit_message --tool-args '{"diff_text":"..."}'
gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"src/main.py","start_line":"270","end_line":"284"}'
```

This is useful for scripting, CI/CD pipelines, and one-off queries where you don't need a persistent MCP server. JSON output goes to stdout; all diagnostic messages go to stderr — safe for piping.

📖 **Full documentation:** [docs/mcp-integration.md](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md) — available in 5 languages (EN, PT-BR, PT-PT, ES, FR).

> 💬 **MCP Prompts** — GitPR also exposes 7 pre-defined message templates (prompts) for common flows like "Review PR", "Generate Commit Message", and "Create Issue from Diff". See the [MCP Prompts guide](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-prompts.md) for the full list.

## 🎯 Smart Excludes (Token Optimization)

GitPR automatically removes non-code files from your `git diff` before sending them to the AI — reducing token consumption and API costs with **zero configuration** required.

**Two layers of exclusions:**
- **Lockfiles & generated files:** `package-lock.json`, `*.min.js`, `*.map`, `*.pyc`, `*.svg`, and 30+ more patterns defined in [`gitpr.smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.smart-excludes.json)
- **Documentation prose:** `*.md`, `*.txt`, `*.rst`, `*.adoc`, `*.tex`, and 20+ more extensions defined in [`gitpr.docs-smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.docs-smart-excludes.json)

**Documentation tracking:** Even though documentation content is excluded from the diff, GitPR still tells the AI _which_ documentation files changed by injecting their paths as metadata into the system instructions. The AI has full context about doc updates without consuming tokens on their prose.

**Benefits:**
- ✅ Up to **98% token reduction** on documentation-heavy branches
- ✅ **Faster AI responses** — less text to process per API call
- ✅ **Higher-quality analysis** — AI focuses on code changes, not markup
- ✅ **Zero configuration** — works automatically on every run, managed remotely

**Project-local configuration:** Each project can define extra exclusions at `.gitpr/conf/gitpr.smart-excludes.json`. The file is auto-seeded on first run and merged with the global list at runtime:

```json
{
  "_comment": "Project-specific Smart Excludes.",
  "excludes": [
    "dist/",
    "*.pyc",
    "build/",
    "node_modules/"
  ]
}
```

Add framework-specific build artifacts, generated folders, or any pattern that only applies to this project. The file is safe to commit — your team gets the same exclusions.

> 📖 **Full documentation:** [docs/smart-excludes.md](https://github.com/natanfiuza/gitpr/blob/main/docs/smart-excludes.md) — available in 5 languages (EN, PT-BR, PT-PT, FR, ES).

## 📁 Output Directory Structure

By default, GitPR saves all generated files in the `.gitpr/reports/` directory, organized by artifact type:

| Artifact | Default Location |
|---|---|
| PR Description | `.gitpr/reports/pr_desc/` |
| Code Review | `.gitpr/reports/review/` |
| Full Review | `.gitpr/reports/full_review/` |
| File Review | `.gitpr/reports/file_review/` |
| Blame Report | `.gitpr/reports/blame/` |
| Issue Draft | `.gitpr/reports/issue/` |

Directories are created automatically on first use. **Backward compatible:** if your `.env` already contains custom paths with directory separators (e.g., `OUTPUT_FILE_NAME=/home/user/prs/my_pr.md`), those are honored as-is — GitPR only redirects bare filenames to `.gitpr/reports/`.

## 📚 Technical Documentation and Advanced Guides

To keep this README concise, we detail the most advanced **DevOps** and **Continuous Integration** focused implementations in separate documents.

If you want to implement GitPR as an automated quality barrier in your team, check out the guides below.

> 🌐 Each guide is available in **5 languages** — add `.pt_br`, `.pt_pt`, `.fr_fr`, or `.es_es` before the `.md` extension for translated versions (e.g., `docs/understanding_chat_functionality.pt_br.md`). English is the default with no suffix.

### Chat & Interactive Features

* [**🧠 Interactive Chat (Pair Programming)**](https://github.com/natanfiuza/gitpr/blob/main/docs/understanding_chat_functionality.md) — How to use the AI chat with memory, slash commands, auto-patch, and session export.

### DevOps & CI/CD

* [**Local Git Hooks (Shift-Left)**](https://github.com/natanfiuza/gitpr/blob/main/docs/git-hooks-locais.md) — How to use `gitpr --installhooks` to create guardrails on the developer's machine and use AI to automatically write commit messages.
* [**Hook Scripts Versioning & Auto-Sync**](https://github.com/natanfiuza/gitpr/blob/main/docs/hooks-versioning.md) — How the automatic versioning and i18n-aware synchronization system keeps your Git hooks up to date.
* [**Customizable Static Linter**](https://github.com/natanfiuza/gitpr/blob/main/docs/linter-regras-customizadas.md) — How to create validation rules in `.gitpr.linter.yml` for CI/CD and pre-commit hooks.
* [**CI/CD Integration (GitHub Actions)**](https://github.com/natanfiuza/gitpr/blob/main/docs/github-ci-linter.md) — How to run GitPR in the pipeline to block "Merge" of PRs with violations.

### Core Features

* [**Pull Request (Default Mode)**](https://github.com/natanfiuza/gitpr/blob/main/docs/pr-descricao-padrao.md) — Complete flow for generating PR descriptions without flags.
* [**Pull Request Publisher TUI**](https://github.com/natanfiuza/gitpr/blob/main/docs/pull-request-publication.md) — How to review and publish Pull Requests directly to GitHub from the terminal.
* [**AI Code Review**](https://github.com/natanfiuza/gitpr/blob/main/docs/code-review-ia.md) — Guide to review modes (`--review`, `--fullreview`) and file auditing (`--input`).
* [**AI Commit Messages**](https://github.com/natanfiuza/gitpr/blob/main/docs/commit-message-ia.md) — How to generate messages in the Conventional Commits standard and integrate with Git Hooks.
* [**Issue Generation and TUI Interface**](https://github.com/natanfiuza/gitpr/blob/main/docs/issue-tui-help.md) — How to use the terminal graphical interface (TUI) and the 3 context engines to manage structured Issues.
* [**Code Archaeologist (Git Blame)**](https://github.com/natanfiuza/gitpr/blob/main/docs/blame-arqueologo.md) — How to trace the origin of business rules with `git blame` and AI.
* [**Skills and Templates System**](https://github.com/natanfiuza/gitpr/blob/main/docs/skill-template.md) — How to customize AI behavior with `.gitpr.*.md` files.

### Configuration & Infrastructure

* [**Install Wizard**](https://github.com/natanfiuza/gitpr/blob/main/docs/install-wizard.md) — Step-by-step guided setup for configuring GitPR in a new project.
* [**AI Providers**](https://github.com/natanfiuza/gitpr/blob/main/docs/providers-ia.md) — Configuration and selection between Google Gemini, DeepSeek, and Ollama.
* [**Auto-Updater**](https://github.com/natanfiuza/gitpr/blob/main/docs/auto-update.md) — How GitPR's automatic update (hot-swap) works.
* [**GitHub Token (PAT) Integration and Security**](https://github.com/natanfiuza/gitpr/blob/main/docs/github-pat-integration.md) — Understand how GitPR creates issues directly in the repository with authentication.
* [**Internationalization (i18n)**](https://github.com/natanfiuza/gitpr/blob/main/docs/i18n_explanation.md) — Architecture, usage patterns, and how to add new languages.
* [**MCP Integration**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md) — Connect GitPR to VS Code, Cursor, and Claude Desktop via Model Context Protocol.
* [**MCP Prompts**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-prompts.md) — Pre-built message templates (7 prompts, 35 language variants) for common GitPR workflows in your editor's AI chat.
* [**MCP Tool Annotations**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-annotations.md) — IDE integration hints (`readOnlyHint`, `destructiveHint`) for smarter UI behavior and safer tool execution.
* [**Metrics & Telemetry**](https://github.com/natanfiuza/gitpr/blob/main/docs/metricas-telemetria.md) — Local offline analytics for team usage metrics, exportable CSV reports, and interactive TUI dashboard.

## ⚡ Local Cache System (Quota Savings)

GitPR has an intelligent **MD5**-based cache engine. Whenever you run a command (`--review`, `--commit`, etc.), the tool generates an exact hash of your current code (diff) and instructions.
If you run the same command again without changing the code, GitPR intercepts the request and returns the result instantly (in milliseconds) from the `~/.gitpr/cache/prompts/` folder, saving you time and your Gemini API quotas!

## 🔄 Auto-Updater (Over-The-Air Update)

Never worry about manually downloading new versions again. GitPR has a Connection Guardian and a built-in updater:
* It checks network availability before starting so it doesn't block your offline workflow.
* On each execution, it silently checks if there is a new official release on the GitHub API.
* You can force the check and installation by running `gitpr --update` or `gitpr -u`.
* The tool uses the *Hot-Swap* technique, downloading the new `.exe` and transparently replacing the old version.

## Publishing to PyPI

```bash
pipenv run python -m build
pipenv run twine upload dist/*
```
## **🤝 How to Contribute**

Contributions are very welcome! To contribute:

1. Fork the project.
2. Create a branch for your *feature* (git checkout -b feature/NewFeature).
3. Commit your changes (git commit -m 'feat: add new feature'). Tip: Use GitPR itself to generate this message! 😄
4. Push to the branch (git push origin feature/NewFeature).
5. Open a Pull Request.

## **✨ Acknowledgments and Authorship**

Project conceived and developed by:

**Natan Fiuza** - [contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br)

## **📄 License**

This project is licensed under the **GNU Lesser General Public License v2.1 (LGPL-2.1)**. See the LICENSE file for more details.
