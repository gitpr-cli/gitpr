# GEMINI.md - GitPR CLI

## About the project

**GitPR** is a Python CLI for automating Pull Requests, commits, code review, interactive pair-programming chat, issue creation, and telemetry using AI (Google Gemini, DeepSeek, and Ollama). It also operates as a Model Context Protocol (MCP) server for IDE integration. Distributed via PyPI (`pip install gitpr-cli`) and as a standalone executable (PyInstaller).

- **Author:** Natan Fiuza (contato@natanfiuza.dev.br)
- **Current version:** 0.0.37
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
| *(default)*               | PR publisher (TUI)      | `git fetch` → diff against `origin/main` → AI → `.md` → TUI → POST to GitHub |
| `--no-publish`            | PR description only     | Same as default, but saves the `.md` locally without opening the TUI      |
| `--no-edit`               | Direct PR publish       | Same as default, but auto-commits and POSTs directly (skips the TUI)     |
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
It must be placed in `docs/gemini/reports/{branch}/{current_date}_{taskname}.md`, where `{current_date}` is today's date (`YYYY-MM-DD` format), `{branch}` is the current branch, and `{taskname}` is a short task description (only lowercase letters, numbers, and underscores, no spaces or special characters). Create the `docs/gemini/reports/` folder if it doesn't exist.

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

## Project Memory & Lessons Learned

This section summarizes the design decisions, patterns, and historical fixes captured in `.claude/memory/`:

### ai-call-duration-tracking
- **Description:** Rastreamento de duração real (wall-clock) das chamadas de IA via perf_counter
- **How to apply:**
  1. Usar `time.perf_counter()` (não `time.time()`) — é monotônico, imune a ajustes de relógio
  2. Capturar ANTES do retry loop (retries reenviam payload idêntico, duração total inclui todos)
  3. Injetar `duration_ms` no `meta_raw` antes de `_telemetry_meta` ser extraído
  4. `_aggregate_meta` deve somar (`+=`) não sobrescrever
  5. Cache antigo sem `duration_ms` mostra 0 (backward-compatible)

### cache-filter-repo-branch
- **Description:** Cache JSON inclui campo repo; filtro por repo_name + branch_name evita colisões entre projetos
- **How to apply:**
  Ao adicionar novos tipos de cache que precisam de filtro por repositório:
  1. Garantir que `save_cached_response()` está sendo chamada com o contexto correto
  2. Usar `get_repo_name()` para obter o identificador do repositório
  3. Filtrar por ambos `repo_name` e `branch_name` nas consultas
  4. Caches legacy sem `"repo"` são descartados (comportamento seguro)

### claude-md-desatualizado-vs-architecture
- **Description:** CLAUDE.md e GEMINI.md derivam silenciosamente do código porque são auto-carregados e ninguém os relê; conferir versão e flags contra src/ antes de citar
- **How to apply:**
  - Antes de citar versão, flag ou lista de features a partir de CLAUDE.md/GEMINI.md, **confira no código**: `src/main.py` para flags, `src/updater.py` para versões.
  - Ao adicionar flag nova ao GitPR, atualize as tabelas de comando dos **dois** arquivos junto — é o passo que sempre foi esquecido.
  - Verificação rápida de links de doc do HELP_MAP: `grep -oE 'get_doc_url\("[^"]+"\)' src/main.py` e testar cada um contra `docs/`.
  - `docs/ARCHITECTURE.md` (EN canônico + 4 locales, reescrito em 2026-08-18 a partir do código com refs `file:line`) segue sendo a visão de arquitetura mais fiel.
  - Ver [[docs-multilingue-convencao]] e [[help-contextual-pattern]].

### coauthor-trailer-injecao-pos-cache
- **Description:** Trailer Co-Authored-By é anexado no consumo (nunca no prompt nem no cache MD5) e só entra na TUI no momento do commit
- **How to apply:**
  - Ao adicionar um novo fluxo que produza mensagem de commit, chame `append_coauthor_trailer()` no ponto de consumo — nunca antes do cache.
  - Se o fluxo tem tela de revisão, injete só imediatamente antes de `execute_git_commit()` e sobre uma variável local, mantendo o estado da tela limpo.
  - Cuidado com mensagem vazia: nenhum caminho deve criar um commit que seja só o trailer.
  - Consumidores externos do tool MCP `generate_commit_message` fazendo comparação exata precisam contar com o trailer na saída.

### dashboard-repo-scope
- **Description:** Dashboard de métricas com escopo por repositório, merge cache+eventos e export local
- **How to apply:**
  1. `MetricsApp` recebe `repo_filter` como parâmetro (de `main.py`)
  2. `export_metrics(repo_filter=...)` filtra eventos antes de exportar
  3. `_setup_columns()` no `on_mount`; `_populate_table()` só adiciona rows
  4. Cache files sem campo `"repo"` são excluídos quando repo filter ativo
  5. `processed_cache.json` permite retomar scan incremental no futuro

### docs-multilingue-convencao
- **Description:** Convenção de documentação multilíngue com inglês como base canônica e localizações por sufixo de idioma
- **How to apply:**
  1. Nova documentação: criar `<nome>.md` em inglês + `<nome>.pt_br.md` no mínimo
  2. Blocos de código e comandos NUNCA são traduzidos
  3. Usar `get_doc_url()` para gerar links de documentação — nunca hardcodar URLs
  4. Ao adicionar uma nova localização, seguir o padrão de nomenclatura existente
  5. Documentação referenciada no help contextual usa URLs resolvidas por idioma

### gemini-reports-convention
- **Description:** GEMINI.md exige relatório de conclusão em docs/gemini/reports/ para cada tarefa Gemini
- **How to apply:**
  1. `CLAUDE.md` e `GEMINI.md` devem ser mantidos em sincronia quando novos comandos ou mudanças de arquitetura são introduzidos
  2. Relatórios do Gemini seguem o mesmo padrão de nomenclatura dos relatórios do Claude: `{YYYY-MM-DD}_{taskname}.md`
  3. Ambos os diretórios de relatórios são fontes de entrada para `/reports-to-memory`
  4. Features documentadas em um rulebook devem ser espelhadas no outro

### github-api-shared-module
- **Description:** src/github_api.py como módulo compartilhado de chamadas à API REST do GitHub
- **How to apply:**
  Sempre que precisar de uma nova chamada à API do GitHub, adicionar a função em `github_api.py` seguindo o padrão `(ok, data, status)` — NUNCA fazer chamada HTTP inline em TUI ou CLI. Para autenticação, usar `get_github_token()` de `config.py` que já trata Fernet decrypt e fallback raw key. Para validação interativa, `validate_or_request_github_token()` em `tui_issue.py`.

### github-token-reauth-flow
- **Description:** Validação de PAT via GET /user antes da TUI com loop de re-autenticação em 401
- **How to apply:**
  1. `validate_github_token()` deve ser usada antes de qualquer operação GitHub
  2. O loop `while True` com `reauth` action em `main.py` preserva o estado da TUI
  3. Max 3 tentativas de token antes de desistir
  4. O PAT necessário tem scope `repo` (URL de geração com parâmetros preenchidos)
  5. Novas features que usam GitHub API devem integrar o mesmo fluxo de validação

### help-contextual-pattern
- **Description:** Padrão de help contextual com Click usando flag regular em vez de help_option
- **How to apply:**
  Ao adicionar novas flags ao GitPR:
  1. Adicionar entrada no `HELP_MAP` com título, descrição e URL da doc
  2. Se a flag pode ser usada com outras, ajustar `HELP_PRIORITY`
  3. A flag `-h` DEVE ser `is_flag=True, is_eager=False` (regular, não eager)
  4. Flags com `exists=True` (como `--input`) precisam de guard `not help_flag` na validação, já que o Click não bloqueia mais automaticamente
- **Gotchas / Technical Debt:**
  O dispatcher fazia `locals().get(param_name)` usando o nome da flag como está no `HELP_MAP`, então nenhuma flag com hífen (`--linter-setup`, `--no-publish`, `--no-edit`, `--no-unstaged-check`) era encontrada — o Click converte o nome do parâmetro para snake_case. A correção é `param_name.replace('-', '_')` antes do lookup. Flags de palavra única sempre funcionaram, o que escondeu o bug por meses.

### hook-templates-release-ordering
- **Description:** Templates de hook devem chegar ao GitHub main antes do bump de __scripts_version__ no updater
- **How to apply:**
  Em qualquer release que altere arquivos em `scripts/`, mergear os templates em `main` primeiro e só então versionar/bumpar `__scripts_version__` no `updater.py`. O mesmo vale para todo recurso remoto controlado por marcador de versão — ver [[version-marker-pattern]].

### i18n-auditoria-ast-categorias
- **Description:** Auditoria autoritativa de i18n é via AST de todos os __() em src/; três categorias de falha (mangled, untranslated, missing)
- **How to apply:**
  - Ao investigar "mensagem saiu em inglês", classifique primeiro em qual das 3 categorias ela cai — não presuma que é falta de tradução.
  - **11 chaves são inglês por decisão de projeto** e não devem ser traduzidas: conteúdo de prompt de IA (`=== AI PR HISTORY ===`, `=== REGISTERED COMMITS ===`, instrução do resumo de blame, prompt do arquiteto), marcadores universais `[OK]`/`[FAIL]`, e termos técnicos universais (`Tokens`, `Auto-Patch`). O `ORIGIN`/`REFACTORING` do blame_engine também é valor de protocolo, não texto de UI. Existe allowlist em `tests/test_i18n.py`.
  - `es`/`es_es` e `fr`/`fr_fr` são dicionários duplicados da mesma família — valores podem ser cross-preenchidos entre o par, mas os dois arquivos precisam existir e ficar em paridade.
  - Chaves novas são **anexadas ao fim** de cada JSON (os arquivos não são ordenados alfabeticamente).
  - Ver [[i18n-sync-regex-chaves-mangled]] e [[langs-ota-stale-race]].

### i18n-sync-regex-chaves-mangled
- **Description:** Regex antiga do sync_i18n capturava kwargs do call-site dentro da chave, gerando chaves que nunca casam em runtime
- **How to apply:**
  - O `PATTERN` corrigido para na própria aspa do literal e passa o capturado por `ast.literal_eval` — os escapes viram a string exata de runtime.
  - Chamadas `__()` com literais adjacentes (concatenação implícita em várias linhas) não são extraíveis: refatore para um único literal, como foi feito no `src/mcp_server.py`. Descrições multi-linha de prompts MCP são limitação conhecida do PATTERN — chaves truncadas delas nascem mortas.
  - O sync tem `_live_key()` (índice que desescapa) para migrar entradas legacy em vez de descartá-las, e um **guard que recusa escrever quando o scan extrai 0 chaves**. Nunca remova esse guard.
  - `tests/test_i18n.py` guarda o padrão de chave mangled, a paridade entre os 6 arquivos e a contagem — rode-o depois de qualquer mexida em `langs/`.
  - Ver [[i18n-auditoria-ast-categorias]], [[langs-ota-stale-race]] e [[testes-i18n-pin-translations]].

### langs-ota-stale-race
- **Description:** Correções em langs/*.json exigem bump de __lang_version__; rodar código dev com marcador novo antes do main atualizado grava arquivo velho sob a versão nova
- **How to apply:**
  - Sempre que mudar `langs/*.json`, bumpar `__lang_version__` em `src/updater.py` **após** o merge no main (senão clientes fixam conteúdo antigo sob o marcador novo).
  - Para diagnosticar em máquinas: comparar `~/.gitpr/langs/{lang}.json` com `git show origin/main:langs/{lang}.json` e o `LANG_VERSION` no `~/.gitpr/.env`.
  - O bump sozinho cura máquinas existentes: na próxima execução o download substitui o arquivo local.
  - Ver [[version-marker-pattern]] e [[textual-modal-callback-dead-pump]].

### linter-externo-checkstyle-bridge
- **Description:** Bridge de linters externos usa stdout do subprocess ignorando o exit code e cruza o XML Checkstyle só com as linhas adicionadas do diff
- **How to apply:**
  - Relatório Markdown vai para `.gitpr/reports/linter/` (`OUTPUT_FILE_NAME_LINTER`) e **só é escrito quando há warnings ou errors** — execução limpa não cria arquivo.
  - Com erros bloqueantes fora de hook/quiet abre a TUI (`src/ui/linter_app.py`); em hook/quiet imprime e faz `sys.exit(1)`, preservando o bloqueio de commit.
  - Pendências conhecidas: `external_linters` não funciona no modo full-file (`--input`); `_run_external_linter` ainda monta comando com f-string + `shell=True` (candidato a shlex/argv).
  - Ver [[plugin-system-architecture]], [[version-marker-pattern]] e [[output-reports-centralized-paths]].

### mcp-run-linter-hangs
- **Description:** Hang das tools MCP do GitPR resolvido com _offload (anyio worker threads); se voltar a travar, matar gitpr-mcp.exe e reiniciar o editor
- **How to apply:**
  Se uma tool MCP travar de novo: `taskkill /IM gitpr-mcp.exe /F` e reiniciar o Claude Code (o `.mcp.json` relança; install editável — sem reinstalar). Para validar mudanças no MCP: `python -m pytest tests/test_mcp_server.py tests/test_mcp_server_e2e.py -q` (o e2e sobe o servidor real via JSON-RPC) e `gitpr-mcp --tool run_linter`. Follow-ups pendentes: timeouts do SDK de IA em ai_providers.py e shell=True em `_run_external_linter`. Ver [[mcp-server-isolation]].

### mcp-server-isolation
- **Description:** Servidor MCP usa monkey-patching de stdout para isolar JSON-RPC do output da aplicação
- **How to apply:**
  1. Novas tools MCP devem ser wrappers finos que delegam para funções existentes
  2. NUNCA usar `print()` ou `click.echo()` em código chamado pelo MCP — o patch redireciona para stderr, mas o design correto é retornar dados, não imprimir
  3. `_safe_call()` deve envolver toda chamada que pode lançar exceção
  4. O monkey-patching toca `sys.stdout`, `sys.stderr`, `sys.exit` e `builtins.print`
  5. Testar com `gitpr-mcp` diretamente, não apenas `gitpr --mcp`

### mcp-tool-cli-invocacao-direta
- **Description:** Invocação direta de MCP tools via CLI com gitpr-mcp --tool sem servidor stdio
- **How to apply:**
  1. Novas tools adicionadas ao MCP devem ser registradas em `_TOOL_FUNCS`
  2. `_write_real_stdout()` deve ser usado para qualquer output JSON; stderr para logs
  3. O parser de argumentos de cada tool (`arg_parser_fn`) faz parse e validação
  4. `_prettify_result()` formata o output para exibição amigável no terminal

### merge-conflict-error-handling
- **Description:** Falha de merge no PR publisher exibe modal de erro em vez de prosseguir silenciosamente
- **How to apply:**
  1. Toda operação assíncrona na TUI que atualiza estado visual deve usar `call_from_thread` para garantir execução na thread principal do Textual
  2. Callbacks de sucesso e falha devem ser métodos separados — nunca misturar lógica de erro no callback de sucesso
  3. Sempre rastrear o resultado final (`final_action`) para feedback visual correto
  4. HTTP 405 em merge PR = conflitos que exigem resolução manual no GitHub

### metrics-cache-enrichment
- **Description:** Enriquecimento de métricas com tokens reais via scan do cache de prompts
- **How to apply:**
  1. Todo `call_ai_model()` deve retornar `meta_raw` com `_telemetry_meta`
  2. `save_cached_response()` deve receber e persistir `meta_raw`
  3. `_telemetry_meta` contém: `prompt_tokens`, `completion_tokens`, `model`, `duration_ms`
  4. O matching é por minuto-granularity com token tie-breaker (suficiente para ~99% dos casos)
  5. Dashboard deve trancar contra JSON não-dict (lista, escalar) para evitar crash

### metrics-telemetry-architecture
- **Description:** Arquitetura de telemetria offline com fire-and-forget threads e dashboard TUI
- **How to apply:**
  1. Novos comandos devem chamar `log_command_metric()` com status, provider, duration
  2. Usar lazy import: `from src.metrics import log_command_metric` dentro da função
  3. Eventos são agregados por uuid+data; re-execuções no mesmo dia sobrescrevem
  4. Dashboard acessível via `gitpr --metrics --dashboard`
  5. Export via `gitpr --metrics --export` (salva em `./.gitpr/metrics/export/`)

### nothing-to-commit-detection
- **Description:** Detecção multilingue de "nothing to commit" no git commit — trata como sucesso, não erro
- **How to apply:**
  A função `execute_git_commit()` em `core.py` já tem essa detecção. Se um novo ponto de entrada precisar verificar saída de commit, usar `execute_git_commit()` em vez de chamar `subprocess.run(['git', 'commit', ...])` diretamente. Se precisar adicionar novos padrões, manter a busca case-insensitive e adicionar ao array de padrões.

### output-reports-centralized-paths
- **Description:** Centralização de paths de output em .gitpr/reports/ com resolve_output_path() e fallback por env var
- **How to apply:**
  Ao adicionar um novo tipo de artefato (ex: novo comando que gera arquivo), criar a env var no `DEFAULT_CONFIG`, adicionar a entrada no `_OUTPUT_FOLDER_MAP`, e usar `resolve_output_path()` no call site. Não duplicar a lógica de path — sempre delegar ao helper.

### plugin-system-architecture
- **Description:** Arquitetura do sistema de plugins globais — linter aditivo + prompts MCP dinâmicos com factory closures
- **How to apply:**
  Para adicionar um novo tipo de plugin, seguir o padrão:
  1. Criar subpasta em `~/.gitpr/plugins/<tipo>/` via `setup_environment()`.
  2. Adicionar função de discovery `get_<tipo>_plugins()` em `config.py`.
  3. No ponto de consumo, iterar sobre os plugins e fazer merge aditivo (nunca substitutivo).
  4. Tratar erros silenciosamente — plugin malformado nunca deve quebrar o fluxo principal.

### pre-save-debug-flag
- **Description:** Flag oculta --pre-save que dumps payload completo da IA em JSON antes do envio
- **How to apply:**
  1. `gitpr --pre-save` ativa o dump para todas as operações daquela execução
  2. Para forçar dump quando há cache hit, limpar `~/.gitpr/cache/prompts/`
  3. O dump acontece UMA vez antes do retry loop (retries reenviam payload idêntico)
  4. Falha ao escrever o dump é silenciosa — ferramenta de debug nunca quebra o pipeline
  5. Adicionar `action=` kwarg em novas chamadas a `call_ai_model()` para rastreabilidade

### skill-folder-auto-migration
- **Description:** resolve_skill_path() migra arquivos legacy da raiz para .gitpr/skill/ transparentemente
- **How to apply:**
  1. NUNCA referenciar arquivos de skill diretamente na raiz — sempre usar `resolve_skill_path()`
  2. O download de novos templates (`--skill`) deve criar `.gitpr/skill/` e baixar direto lá
  3. Arquivos que já existem (na pasta ou migrados da raiz) NUNCA são sobrescritos
  4. Mensagens de ajuda devem referenciar `.gitpr/skill/`, não a raiz

### smart-excludes-local-projeto
- **Description:** Arquivo local .gitpr/conf/gitpr.smart-excludes.json mergeado com lista global no runtime
- **How to apply:**
  1. Exclusões específicas do projeto vão em `.gitpr/conf/gitpr.smart-excludes.json`
  2. Exclusões genéricas (cross-project) continuam no template remoto global
  3. `_seed_local_smart_excludes()` deve ser chamado no download de templates (`--skill`)
  4. O merge é union+dedup — não há remoção de exclusões globais via arquivo local
  5. Para debug, `GITPR_SKIP_SMART_EXCLUDES=1` desabilita tudo sem modificar arquivos

### smart-excludes-remote-control
- **Description:** Lista de exclusão do git diff controlada remotamente via template JSON no GitHub
- **How to apply:**
  1. Para adicionar novo padrão de exclusão, editar `templates/gitpr.smart-excludes.json`
  2. Bumpar `__lang_version__` em `src/updater.py` para propagar a todos os clientes
  3. O loader é 100% silencioso em falha — diff nunca quebra por causa dessa lista
  4. Edições manuais do usuário em `~/.gitpr/conf/` sobrevivem até o próximo bump de versão

### smart-excludes-sys-inst-mapreduce
- **Description:** Lista de docs excluídos pelo Smart Excludes vai no sys_inst, não no corpo do prompt, para sobreviver ao Map-Reduce
- **How to apply:**
  - Qualquer metadado que a IA precise ver por inteiro (lista de arquivos, política, persona) vai no `sys_inst`; só o conteúdo fatiável vai no corpo.
  - Ao adicionar um fluxo novo que consome diff, copie o par: seção no `sys_inst` + mensagens "📄 N documentation file(s) excluded from diff (Smart Excludes)." e link "Learn more".
  - Carregamento de skill segue a mesma lógica de escopo: no blame a skill é lida **uma vez** em `run_blame_analysis()` e passada por parâmetro a `analyze_commit_with_ai()`, em vez de uma leitura (e uma mensagem) por commit. Modos `return_data=True` (usados por `-is -b` e pelo MCP) carregam em silêncio.
  - Ver [[smart-excludes-remote-control]], [[smart-excludes-local-projeto]] e [[skill-folder-auto-migration]].

### spinner-adaptive-speed
- **Description:** Velocidade adaptativa do spinner baseada no comprimento da frase
- **How to apply:**
  1. Ao adicionar novas frases ao template `gitpr.thinking-words.md`, verificar se os thresholds de comprimento ainda fazem sentido
  2. O cálculo é feito uma vez por palavra (na transição), não por frame
  3. Manter os thresholds como constantes no método para fácil ajuste
  4. A lógica de "descoberta" de caracteres aleatórios é independente da velocidade

### spinner-config-pattern
- **Description:** Cadeia de resolução env → download GitHub → fallback para recursos configuráveis
- **How to apply:**
  Ao adicionar novo recurso configurável remotamente:
  1. Criar o template no GitHub (`templates/gitpr.<nome>.*.md`)
  2. Adicionar constante `_FALLBACK_<NOME>` no módulo
  3. Criar função `_load_<nome>()` com a cadeia de 3 níveis
  4. Usar version marker (`__lang_version__`) como gatilho de re-download
  5. NUNCA emitir output no caminho de falha (degradação silenciosa)

### staging-selecao-widget-erro-real
- **Description:** Modal de staging dessincronizava seleção de arquivos e engolia erros de git add com falso sucesso
- **How to apply:**
  - Em qualquer tela Textual, ler o estado do widget no momento da ação (`SelectionList.selected`), nunca manter dicionários paralelos de seleção.
  - Wrappers de comandos git devem retornar `(success, error_message)` com o stderr/stdout capturado; os call sites devem exibir o erro real.
  - Executar operações com efeito colateral (git add) uma única vez por fluxo.

### testes-i18n-pin-translations
- **Description:** Testes que afirmam texto de usuário quebram em máquinas pt-BR; fixar src.i18n.TRANSLATIONS = {} via mock.patch
- **How to apply:**
  - A correção adotada foi `mock.patch` fixando `src.i18n.TRANSLATIONS` em `{}` (dicionário vazio = fallback inglês), **não** setar `GITPR_LANG=en` por env: o env var é lido antes do teste rodar e não afeta um módulo já importado.
  - Alternativa igualmente aceita: escrever assertions agnósticas de idioma (checar estrutura/números em vez de frases).
  - Ao escrever teste novo que toca saída de usuário, decida explicitamente entre pinar as traduções ou não assertar texto — nunca deixe implícito.
  - Sintoma de reconhecimento: teste passa no CI e falha localmente (ou vice-versa) sem nenhuma mudança de código.
  - Ver [[i18n-auditoria-ast-categorias]].

### textual-modal-callback-dead-pump
- **Description:** Push de modal dentro de timer de tela que será removida liga o callback do dismiss à fila morta — o resultado nunca chega (Textual 8.x)
- **How to apply:**
  - Nunca faça `pop_screen()` + `push_screen(callback=...)` dentro de timer de tela que está sendo removida.
  - Para escapar do contexto da tela: `self.call_next(...)` no app (posta na fila do app — funciona). **Não use** `call_after_refresh` (vira `InvokeLater` encaminhado para a tela **atual**) nem `call_from_thread` na thread principal (levanta RuntimeError).
  - Padrão de teste: `App.query_one` não enxerga telas modais no 8.2.8 — use `app.screen.query_one`; `pilot.click(selector)` usa `screen.query_one` e funciona.
  - Ver [[version-marker-pattern]] e [[staging-selecao-widget-erro-real]] para outros bugs de TUI/Textual.

### tui-stdout-conflict-fix
- **Description:** Textual substitui sys.stdout e quebra click.secho() no Windows; wrapper _with_real_stdout() resolve
- **How to apply:**
  Usar o wrapper `_with_real_stdout()` ao chamar funções de backend dentro de handlers de TUI. O wrapper salva `sys.stdout` atual, restaura o `sys.__stdout__` real durante a chamada, e re-restaura o `_PrintCapture` do Textual depois. Sempre que uma nova tela Textual precisar chamar `generate_pr_content()`, `get_git_diff()`, ou qualquer função que use `click`, envolver com esse wrapper.

### ui-subpackage-packaging
- **Description:** src/ui/ requer __init__.py vazio e find-packages no pyproject.toml para ser incluído no .whl
- **How to apply:**
  Ao criar qualquer novo sub-package em `src/`:
  1. Criar `__init__.py` (pode ser vazio ou com exports)
  2. Verificar se `pyproject.toml` já cobre com `"src.*"` no `find.include`
  3. Adicionar dependências do sub-package (ex: `textual`, `requests`) no `pyproject.toml`
  4. Testar com `pip install -e .` antes de publicar

### unstaged-check-before-ai-commands
- **Description:** Verificação de arquivos unstaged antes de comandos de IA com escape hatch --no-unstaged-check
- **How to apply:**
  1. Todo novo comando que usa `git diff` deve chamar `check_unstaged_files()` antes
  2. Usar `get_uncommitted_summary()` para visão completa do estado do repositório
  3. MCP tools que expõem estado do git devem seguir o padrão de 3 categorias
  4. O escape hatch `--no-unstaged-check` deve ser respeitado em todos os comandos

### version-marker-pattern
- **Description:** Marcadores de versão no .env controlam re-download de recursos remotos em bloco
- **How to apply:**
  1. Ao adicionar novo recurso remoto, criar seu próprio marker (ex: `MY_FEATURE_VERSION`)
  2. Comparar com `__lang_version__` no loader
  3. Bumpar `__lang_version__` quando o recurso mudar no GitHub
  4. User customizations no `.env` são sobrescritas no bump (comportamento esperado)

### windows-utf8-encoding-fix
- **Description:** Consoles Windows com cp1252 crasham em emojis; fix com sys.stdout.reconfigure
- **How to apply:**
  1. `sys.stdout.reconfigure()` deve ser uma das PRIMEIRAS coisas no `main()`
  2. SEMPRE usar `errors='replace'`, nunca `errors='strict'` ou `errors='ignore'`
  3. Verificar se outros streams (`sys.stderr`) também precisam de reconfigure
  4. Ao adicionar novos emojis à interface, testar em terminal Windows com cp1252
  5. O `[tool.pyright]` no `pyproject.toml` é obrigatório para Pylance resolver imports relativos ao source root

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
