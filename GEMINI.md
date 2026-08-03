# GEMINI.md - GitPR CLI

## About the project

**GitPR** is a Python CLI for automating Pull Requests, commits, code review, interactive pair-programming chat, issue creation, and telemetry using AI (Google Gemini, DeepSeek, and Ollama). It also operates as a Model Context Protocol (MCP) server for IDE integration. Distributed via PyPI (`pip install gitpr-cli`) and as a standalone executable (PyInstaller).

- **Author:** Natan Fiuza (contato@natanfiuza.dev.br)
- **Current version:** 0.0.30
- **Python:** >= 3.10
- **Main branch:** `main`
- **Development branch:** `develop_natan`
- **License:** LGPL-2.1

## Architecture

```
src/
├── main.py           # CLI (Click) — command, flag routing, and MCP launcher
├── core.py           # Orchestration — git ops, AI prompts, cache, skills, install wizard
├── config.py         # Configuration, .env, API keys, models, skill path resolution
├── security.py       # Fernet encryption (API keys at rest)
├── cache.py          # Local AI response cache (MD5)
├── ai_providers.py   # Unified AI call layer (Gemini + DeepSeek + Ollama)
├── chat_memory.py    # Interactive chat session memory & history manager
├── mcp_server.py     # Model Context Protocol (MCP) Stdio server implementation
├── metrics.py        # Local telemetry & usage metrics tracking engine
├── spinner.py        # Animated braille spinner with thinking words
├── i18n.py           # Internationalization engine (Laravel-inspired __() function)
├── linter_engine.py  # Static analysis with regex (YAML rules)
├── blame_engine.py   # Code archaeology with git blame + AI
├── issue_engine.py   # AI-powered issue draft creation
├── tui_issue.py      # GitHub token validation and TUI entry point
├── ui/               # Sub-package: TUI components (Textual)
│   ├── __init__.py       # Package marker (required for setuptools discovery)
│   ├── chat_app.py       # Interactive Pair Programming Chat TUI (F5 auto-patch, F2 refresh)
│   ├── help_screen.py    # Help modal (F1) — shortcuts and instructions
│   ├── issue_app.py      # Main issue TUI app — draft editing and submission
│   └── metrics_app.py    # Interactive metrics analytics dashboard TUI
└── updater.py        # Version check (PyPI + GitHub) and hot-swap

scripts/
├── pre-commit-template.sh          # Pre-commit hook for local linting
└── prepare-commit-msg-template.sh  # Prepare-commit-msg hook for AI message generation

templates/            # Remote and local templates served from GitHub (--skill)
├── chat_commands.*.json          # Chat command definitions (EN, PT-BR, PT-PT, ES-ES, FR-FR)
├── gitpr.blame.*.md              # Blame analysis rules by language
├── gitpr.commit.*.md             # Commit message rules by language
├── gitpr.filereview.*.md         # Full file review rules by language
├── gitpr.issue.*.md              # Issue generation rules by language
├── gitpr.linter.*.yml            # Linter rules by language
├── gitpr.pr.*.md                 # PR description rules by language
├── gitpr.prompt.*.md             # MCP prompt templates by language
├── gitpr.review.*.md             # Code review rules by language
├── gitpr.smart-excludes.json   # Smart diff pathspec exclusions (language-independent)
└── gitpr.thinking-words.*.md     # Spinner thinking words list by language

langs/                # Internationalization translation files
├── es_es.json        # Spanish (Spain)
├── fr_fr.json        # French (France)
├── pt_br.json        # Portuguese (Brazil)
└── pt_pt.json        # Portuguese (Portugal)

tests/
├── test_chat_backend.py      # Interactive chat memory and backend tests
├── test_core.py              # Core orchestration unit tests
├── test_install_wizard.py    # Setup wizard tests
├── test_mcp_prompts.py       # MCP prompt templates tests
├── test_mcp_server.py        # MCP server protocol tests
├── test_metrics.py           # Telemetry and metrics dashboard tests
├── test_pre_save.py          # AI prompt pre-save debug mode tests
├── test_skill_command.py     # Skill download and resolution tests
├── test_smart_excludes.py    # Pathspec exclusion filter tests
└── test_thinking_words.py    # Spinner thinking words tests

docs/
├── ARCHITECTURE.md
├── auto-update.md              # Auto-Updater documentation
├── blame-arqueologo.md         # Code Archaeologist documentation
├── chat-interativo.md          # Interactive Pair-Programming Chat documentation
├── code-review-ia.md           # AI Code Review documentation
├── commit-message-ia.md        # AI Commit Message documentation
├── git-hooks-locais.md         # Local Git Hooks documentation
├── github-pat-integration.md   # GitHub Token (PAT + Fernet) security
├── install-wizard.md           # Setup Wizard documentation
├── issue-tui-help.md           # TUI Issue interface guide
├── linter-regras-customizadas.md  # Custom Linter rules documentation
├── map-reduce-diff.md          # Map-Reduce chunking for huge diffs
├── mcp-annotations.md          # MCP Annotations guide
├── mcp-integration.md          # MCP Integration guide for IDEs
├── mcp-prompts.md              # MCP Prompts specification
├── metricas-telemetria.md      # Telemetry and Analytics documentation
├── pr-descricao-padrao.md      # Default PR description mode
├── providers-ia.md             # AI Providers documentation (Gemini, DeepSeek, Ollama)
├── skill-template.md           # Skills and Templates system
├── untracked-files.md          # Untracked files explanation
├── gemini/reports/             # Gemini task reports
├── plans/                      # Development plans
└── assets/                     # logo.png, logo.psd, progit.pdf
```

**Design patterns:** Facade/Mediator (`core.py`), Strategy (`ai_providers.py`), modular separation by responsibility. The `src/ui/` sub-package isolates visual components (Textual) from business logic.

### Main command flow

| Flag / Entry point        | Action                  | Pipeline                                                                 |
|---------------------------|-------------------------|---------------------------------------------------------------------------|
| *(default)*               | PR description          | `git fetch` → diff against `origin/main` → AI → `.md`                    |
| `-c` / `--commit`         | Commit message          | `git diff HEAD` → AI → console (Conventional Commits)                     |
| `-r` / `--review`         | Local code review       | `git diff HEAD` → AI + Linter → `.txt`                                    |
| `-f` / `--fullreview`     | Full code review        | `git fetch` → diff against remote base → AI + Linter → `.txt`             |
| `-i` / `--input`          | File audit              | Entire file → AI (uses `.gitpr.filereview.md`)                            |
| `-l` / `--linter`         | Static linter           | `git diff` → YAML regex → console (no AI)                                 |
| `-is` / `--issue`         | Issue via TUI           | `git diff` → AI (draft) → Textual TUI → save .md or POST to GitHub       |
| `-is -ht` / `--history`   | Epic/Release issue      | `git log` + PR cache → AI → TUI                                           |
| `-is -b <file:lines>`     | Technical debt issue    | `git blame` timeline → AI → TUI                                           |
| `-b` / `--blame`          | Code archaeology        | `git blame` → AI classifies commits → timeline + summary                  |
| `-ch` / `--chat`          | Interactive Chat        | `git diff` → Textual TUI (`ChatApp`) → Pair programming with auto-patch    |
| `--install`               | Setup Wizard            | Interactive CLI wizard for templates, hooks, MCP, and API keys           |
| `-s` / `--skill`          | Download templates      | Download `.gitpr.*.md` into `.gitpr/skill/` (never overwrites)           |
| `-ih` / `--installhooks`  | Install hooks            | Download + install hooks in `.git/hooks/`                                  |
| `-u` / `--update`         | Update                  | Check PyPI/GitHub Releases → hot-swap binary                              |
| `--metrics` / `--dashboard` | Telemetry & Analytics | View summary, `--export` CSV/JSON, `--purge` data, or `--dashboard` TUI  |
| `--lang <lang>`           | Override language       | Forces interface language (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`)   |
| `--provider`              | Force AI provider       | `gemini`, `deepseek`, or `ollama`                                         |
| `--mcp` / `gitpr-mcp`     | MCP Server              | Starts stdio Model Context Protocol server for IDE/agent integration      |
| `-h` / `--help`           | Contextual help         | Alone: all options. With flag: feature-specific help + docs link          |

## Stack

| Component        | Technology                             |
|------------------|----------------------------------------|
| CLI framework    | Click >= 8.0.0                         |
| TUI (issues, chat, metrics) | Textual (ModalScreen, App, bindings)|
| AI (Gemini)      | `google-genai` SDK                     |
| AI (DeepSeek)    | `openai` SDK (API compatible)          |
| AI (Ollama)      | `requests` (Local REST API)            |
| MCP Protocol     | `mcp >= 1.0.0` (Stdio Server)          |
| GitHub API       | `requests` (REST, PAT via header)      |
| i18n             | Custom `__()` engine (EN, PT-BR, PT-PT, ES-ES, FR-FR) |
| Config/Build     | `pyproject.toml` + setuptools >= 61    |
| Encryption       | `cryptography.fernet` (symmetric)      |
| Linter           | `pyyaml` (rules) + regex               |
| Testing          | `pytest` + `unittest.mock`             |
| Packaging        | PyInstaller (`run.py` as entry point)  |
| Virtual env      | Pipenv (Pipfile)                       |

## Commands

```bash
# Install dependencies (pipenv)
pipenv install --dev

# Install dependencies in editable mode (pip)
pip install -e .

# Run CLI (dev mode)
pipenv run python run.py

# Run MCP Server
pipenv run python -m src.mcp_server
# or after pip install -e .
gitpr-mcp

# Run unit tests (full suite: 100 tests)
pipenv run pytest -v
# or
python -m pytest tests/ -v

# Build standalone executable with PyInstaller
pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py

# Publish package to PyPI
pipenv run python -m build
pipenv run twine upload dist/*
```

## Code preferences

### Python style
- **Language:** All variable names, function names, comments, and docstrings MUST be written in **English**
- **Encoding:** UTF-8 with `errors='replace'` for all file reads — NEVER use `errors='strict'` or bare `errors='ignore'`
- **Docstrings:** Free format (not strict Google/NumPy), in English
- **Typing:** Type hints are welcome but not mandatory — use where it improves clarity
- **Organization:** Each module has a single, clear responsibility. Visual components isolated in `src/ui/`
- **Naming:** snake_case for functions/variables, UPPER_CASE for constants, PascalCase for Textual classes
- **CLI:** Use Click with decorators; short flags (`-c`, `-r`, `-f`, `-is`, `-ch`) with long equivalents
- **Imports:** stdlib first, then external dependencies, then internal modules (`from src.*`)
- **Sub-packages:** Create `__init__.py` only when needed for setuptools discovery

### AI responses
- All AI calls must return structured JSON
- Temperature 0.0 for deterministic output
- Automatic retry (3 attempts, 2s interval)
- Mandatory MD5 cache to avoid redundant calls

### Messages and UI
- All user-facing text uses the `__()` i18n function (English keys, translations in `langs/`)
- ASCII banner at startup (suppressed in `--quiet` or `--hook` mode)
- Use `click.style()` or `click.secho()` for terminal colors
- Standard colors: green/cyan = success/info, yellow = warning, red = error
- TUI (Textual): use `$surface`, `$accent`, `$background` from theme; footer with visible bindings
- Animated braille spinner (`src/spinner.py`) during AI calls with thinking words and random colors

## Commits

### Message style
- **Language:** English
- **Format:** Conventional Commits — `type: short description`
- **Types used:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`
- **Descriptions:** short, imperative, no period at the end
- **Examples:**
  - `feat: add interactive pair programming chat TUI`
  - `feat: implement MCP server protocol support`
  - `refactor: extract metrics dashboard to src/ui/ sub-package`
  - `fix: handle encoding in non-UTF8 environments`

### Commit rules
- NEVER amend already-pushed commits
- NEVER skip hooks (`--no-verify`, `--no-gpg-sign`)
- Commits must be atomic — one logical change per commit
- Messages in English
- Co-authorship in collaborative projects: `Co-Authored-By: Gemini <noreply@google.com>`

## Task rules (Task Workflow)

> [!IMPORTANT]
> **PRIORITY RULE — Mandatory Task Completion Report:**
> Upon completing ANY implementation, refactoring, fix, or development task, you **MUST** generate a completion report file saved to:
> `docs/gemini/reports/{branch}/{date}_{task_name}.md`
> - `{branch}`: the current git branch name (e.g. `develop_natan`, `main`).
> - `{date}`: today's date in `YYYY-MM-DD` format.
> - `{task_name}`: a short descriptive name using only lowercase letters, numbers, and underscores (e.g. `create_gemini_md`, `update_mcp_server`).
> 
> Create parent directories (`docs/gemini/reports/{branch}/`) if they do not exist.

### When starting a task
1. **Read the context:** Check `GEMINI.md`, relevant files, current diff
2. **Plan before coding:** For non-trivial features, use plan mode or present approach before implementing
3. **Check git state:** Correct branch, nothing accidentally staged
4. **Check dependencies:** `pipenv install --dev` if new packages are added to Pipfile

### During the task
5. **Follow existing style:** New code should look like it was always there
6. **Don't break the CLI:** Test main flows after changes (`gitpr`, `gitpr -c`, `gitpr -r`, `pytest`)
7. **Keep cache in mind:** Prompt changes must consider MD5 cache impact
8. **Encoding always with `errors='replace'`:** Absolute rule for any `open()` or `subprocess`
9. **New dependencies:** Add to `pyproject.toml` (dependencies) and `Pipfile`

### When finishing a task — MANDATORY REPORT
10. **Generate completion report** with the following format:

```markdown
## Completion Report — [Task Title]

### What was done
- [Objective list of changes made]
- [Modified files with relative paths]

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/... | feat/fix/refactor | What changed |

### Impact
- **Functionality:** [What changed in behavior]
- **Performance:** [Relevant impact]
- **Compatibility:** [API breaks, necessary migrations]

### Next steps (if applicable)
- [Pending tasks or improvement suggestions]
```

This report is **mandatory** at the end of every implementation task — not just for the user, but as historical development documentation.
It must be placed in `docs/gemini/reports/{branch}/{date}_{task_name}.md`, where `{date}` is today's date (`YYYY-MM-DD` format), `{branch}` is the current branch, and `{task_name}` is a short task description (only lowercase letters, numbers, and underscores, no spaces or special characters). Create the `docs/gemini/reports/` folder if it doesn't exist.

## Project-specific notes

### Encoding
- All `subprocess.run()` capturing git output must use `encoding='utf-8'` with `errors='replace'`
- Output files (PR, review, blame, issue) must be written with `encoding='utf-8'`
- The project handles repositories that may contain non-UTF8 characters (legacy)

### Internationalization (i18n)
- `src/i18n.py` provides a `__()` function inspired by Laravel's translation engine
- Supported locales: `en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`
- `CURRENT_LANG` is auto-detected from the OS locale, set via `--lang` or forced via `GITPR_LANG` in `.env`
- English is the default/fallback language (no translation file needed)
- Other languages load JSON from `~/.gitpr/langs/{lang_code}.json` or download from GitHub
- Translation files are version-controlled via `__lang_version__` in `updater.py`
- The `get_doc_url()` function in `core.py` builds language-aware documentation URLs

### Skills System (Prompt Engineering)
- Local `.gitpr.<type>.md` files inside `.gitpr/skill/` act as AI *System Instructions*
- Canonical skill location: `.gitpr/skill/` (files in root are automatically migrated)
- Skill types: `commit`, `pr`, `review`, `filereview`, `blame`, `issue`, `linter.yml`
- Remote templates at `https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/`
- `--skill` downloads templates, but **never overwrites** existing local files
- Language-aware: downloads localized template according to active locale (e.g. `gitpr.issue.pt_br.md`)

### User configuration
- Global directory: `~/.gitpr/`
- Config file: `~/.gitpr/.env` (dotenv format)
- Fernet key: `~/.gitpr/secret.key` (auto-generated on first run)
- Response cache: `~/.gitpr/cache/prompts/<action_folder>/<md5>.json`
- Update cache: `~/.gitpr/update_cache.json` (daily)
- Language files: `~/.gitpr/langs/{lang_code}.json`
- Smart excludes config: `~/.gitpr/conf/gitpr.smart-excludes.json`
- Telemetry metrics: `~/.gitpr/metrics/*.json`
- Environment variables: `DEFAULT_AI_PROVIDER`, `GEMINI_API_KEY_ENCRYPTED`, `DEEPSEEK_API_KEY_ENCRYPTED`, `GEMINI_API_MODEL_PRIMARY`, `GEMINI_API_MODEL_SECONDARY`, `DEEPSEEK_API_MODEL_PRIMARY`, `DEEPSEEK_API_MODEL_SECONDARY`, `OLLAMA_API_MODEL_PRIMARY`, `OLLAMA_API_MODEL_SECONDARY`, `OUTPUT_FILE_NAME`, `OUTPUT_FILE_NAME_REVIEW`, `OUTPUT_FILE_NAME_FULLREVIEW`, `OUTPUT_FILE_NAME_FILEREVIEW`, `OUTPUT_FILE_NAME_BLAME`, `OUTPUT_FILE_NAME_ISSUE`, `GITHUB_TOKEN_ENCRYPTED`, `SPINNER_THINKING_WORDS`, `GITPR_LANG`, `LANG_VERSION`, `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`

### AI Providers (Multi-Model Architecture)
- **Gemini:** `gemini-pro-latest` (primary/advanced) / `gemini-flash-lite-latest` (secondary/simple)
- **DeepSeek:** `deepseek-v4-pro` (primary) / `deepseek-v4-flash` (secondary)
- **Ollama:** `llama3` (local execution without API key)
- Structured JSON output enforced (`response_mime_type` in Gemini, `response_format` in DeepSeek)
- Temperature 0.0 and top_p 0.1 for deterministic output
- Fallback: if configured provider fails, automatically try alternative provider
- `--provider` flag forces engine (`gemini`, `deepseek`, `ollama`) for execution

### Model Context Protocol (MCP) Server Integration
- Entry point: `gitpr-mcp` or `gitpr --mcp`
- Implementation: `src/mcp_server.py` using `mcp >= 1.0.0` stdio server
- Exposes tools, prompt templates, and resources for IDE integration (VS Code, Cursor, Antigravity, Claude Desktop)
- Standardized config: `.mcp.json`

### Interactive Pair Programming Chat (`-ch` / `--chat`)
- Interactive TUI: `src/ui/chat_app.py` → class `ChatApp(App)`
- Context manager: `src/chat_memory.py` → class `ChatMemoryManager`
- Features: full diff context, message history, F5 auto-patching code changes into workspace, F2 diff refresh

### Telemetry & Analytics Engine (`--metrics`, `--dashboard`)
- Engine: `src/metrics.py` logs local token counts, execution status, and timing data
- TUI Dashboard: `src/ui/metrics_app.py` → class `MetricsApp(App)`
- Commands: `--metrics` (summary), `--export` (CSV/JSON export), `--purge` (clean logs), `--dashboard` (interactive TUI)

### Interactive Setup Wizard (`--install`)
- Guided CLI wizard (`run_install_wizard()` in `core.py`)
- Downloads templates into `.gitpr/skill/`, installs local Git hooks, configures MCP editor files, and validates API keys

### Spinner (Animated loading indicator)
- `src/spinner.py` — runs in a background thread during AI calls
- Braille characters (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`) in magenta
- Thinking words loaded from `.env` or downloaded from GitHub template by language
- Words "discovered" letter by letter with random characters, then dot cycle (`. .. ...`)
- Random word colors from a 10-color palette

### Static local linter
- Rules defined in `.gitpr.linter.yml` (YAML) inside `.gitpr/skill/`
- Supports `error` (blocking) and `warning` (informational)
- Filters: file extension (`extensions`), `require_paths`, `ignore_paths`
- `ignore_comments: true` ignores comment lines (language-specific comment regex)
- In diff mode, only checks added lines (`+`) — focused and fast

### Blame engine (Code Archaeology)
- Maximum tracing depth: 4 parent commits
- Secondary model for commit classification (`ORIGIN` vs `REFACTORING`)
- Primary model for final executive summary
- Output: color-coded terminal (green=origin, yellow=refactoring) + Markdown report
- Can feed issue context via `--issue -b file:lines`

### Issues TUI (Textual)
- Main app: `src/ui/issue_app.py` → class `IssueApp(App)`
- Help modal: `src/ui/help_screen.py` → class `HelpScreen(ModalScreen)`
- Bindings: F1 (Help), F2 (Save local .md), F3 (Create via GitHub API), Esc (Exit)
- GitHub token (PAT) validated in `src/tui_issue.py` → `validate_or_request_github_token()`
- PAT scope: `repo` (generated via dynamic URL with pre-filled parameters)
- Issue draft follows the pattern: What / Why / Where / How
- 3 context engines: diff (default), history (`-ht`), blame (`-b`)

### Auto-Updater (Hot-Swap)
- Daily cached check against GitHub Releases (binary) or PyPI (pip)
- `--update` forces immediate check and installation
- Hot-swap: renames current `.exe` to `.old`, downloads new one, rollback on failure
- Connection verified via socket `8.8.8.8:53` before any network operation

### Contextual help (`-h --flag`)
- `gitpr -h` alone: standard Click help with all options
- `gitpr -h --<flag>`: feature-specific help + link to GitHub documentation
- `get_doc_url()` builds language-aware URLs: `.../docs/file.md` or localized variant
- Documentation files supported in EN, PT-BR, PT-PT, ES-ES, FR-FR

## Behavior Guidelines

**Tradeoff:** These guidelines favor caution over speed. Use judgment for trivial tasks.

### 1. Think Before Coding
- State your assumptions explicitly. If uncertain, ask.
- If there are multiple interpretations, present them — don't silently pick one.
- If something is unclear, stop. Name what is confusing. Ask.

### 2. Simplicity First
- Minimum code that solves the problem. Nothing speculative.
- No features beyond what was requested.
- No abstractions for single-use code.
- No unsolicited "flexibility" or "configurability".
- If you write 200 lines and it can be 50, rewrite.

### 3. Surgical Changes
- Touch only what is needed. Clean up only your own mess.
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match the existing style, even if you would do it differently.
- Remove imports/variables/functions that YOUR changes made unused.

### 4. Goal-Oriented Execution
- Define success criteria. Execute in a loop until verified.
- Turn tasks into verifiable goals:
  - "Add validation" → "Write tests for invalid inputs, then make them pass"
  - "Fix the bug" → "Write a test that reproduces it, then fix"
- For multi-step tasks, state a brief plan with per-step verifications.

---
**These guidelines are working if:** there are fewer unnecessary changes in diffs, fewer rewrites due to overcomplexity, and clarifying questions come before implementation, not after errors.
