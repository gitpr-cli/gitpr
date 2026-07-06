# CLAUDE.md - GitPR CLI

## About the project

**GitPR** is a Python CLI for automating Pull Requests, commits, code review, and issue creation using AI (Google Gemini and DeepSeek). Distributed via PyPI (`pip install gitpr-cli`) and as a standalone executable (PyInstaller).

- **Author:** Natan Fiuza (contato@natanfiuza.dev.br)
- **Current version:** 0.0.22
- **Python:** >= 3.10
- **Main branch:** `main`
- **Development branch:** `develop_natan`
- **License:** LGPL-2.1

## Architecture

```
src/
├── main.py           # CLI (Click) — command and flag routing
├── core.py           # Orchestration — git ops, AI prompts, cache, skills
├── config.py         # Configuration, .env, API keys, models
├── security.py       # Fernet encryption (API keys at rest)
├── cache.py          # Local AI response cache (MD5)
├── ai_providers.py   # Unified AI call layer (Gemini + DeepSeek)
├── spinner.py        # Animated braille spinner with thinking words
├── i18n.py           # Internationalization engine (Laravel-inspired __() function)
├── linter_engine.py  # Static analysis with regex (YAML rules)
├── blame_engine.py   # Code archaeology with git blame + AI
├── issue_engine.py   # AI-powered issue draft creation
├── tui_issue.py      # GitHub token validation and TUI entry point
├── ui/               # Sub-package: TUI components (Textual)
│   ├── __init__.py       # Package marker (required for setuptools discovery)
│   ├── help_screen.py    # Help modal (F1) — shortcuts and instructions
│   └── issue_app.py      # Main TUI app — issue editing and submission
└── updater.py        # Version check (PyPI + GitHub) and hot-swap

scripts/
├── pre-commit-template.sh          # Pre-commit hook for local linting
└── prepare-commit-msg-template.sh  # Prepare-commit-msg hook for AI message generation

templates/            # Remote templates served from GitHub (--skill)
├── gitpr.blame.md              # EN: blame analysis rules
├── gitpr.blame.pt_br.md        # PT-BR: blame analysis rules
├── gitpr.commit.md             # EN: commit message rules
├── gitpr.commit.pt_br.md       # PT-BR: commit message rules
├── gitpr.filereview.md         # EN: full file review rules
├── gitpr.filereview.pt_br.md   # PT-BR: full file review rules
├── gitpr.issue.md              # EN: issue generation rules
├── gitpr.issue.pt_br.md        # PT-BR: issue generation rules
├── gitpr.linter.yml            # EN: linter rules
├── gitpr.linter.pt_br.yml      # PT-BR: linter rules
├── gitpr.pr.md                 # EN: PR description rules
├── gitpr.pr.pt_br.md           # PT-BR: PR description rules
├── gitpr.review.md             # EN: code review rules
├── gitpr.review.pt_br.md       # PT-BR: code review rules
└── gitpr.thinking-words.md     # Spinner thinking words list

langs/                # Language translation files
└── pt_br.json        # Portuguese (Brazil) translations

tests/
└── test_core.py      # Unit tests (unittest + mock)

docs/
├── ARCHITECTURE.md
├── auto-update.md              # Auto-Updater documentation
├── blame-arqueologo.md         # Code Archaeologist documentation
├── code-review-ia.md           # AI Code Review documentation
├── commit-message-ia.md        # AI Commit Message documentation
├── git-hooks-locais.md         # Local Git Hooks documentation
├── github-pat-integration.md   # GitHub Token (PAT + Fernet) security
├── issue-tui-help.md           # TUI Issue interface guide
├── linter-regras-customizadas.md  # Custom Linter rules documentation
├── pr-descricao-padrao.md      # Default PR description mode
├── providers-ia.md             # AI Providers documentation
├── skill-template.md           # Skills and Templates system
├── untracked-files.md          # Untracked files explanation
├── claude-code/reports/        # Claude Code task reports
├── plans/                      # Development plans
└── assets/                     # logo.png, logo.psd, progit.pdf
```

**Design patterns:** Facade/Mediator (`core.py`), Strategy (`ai_providers.py`), modular separation by responsibility. The `src/ui/` sub-package isolates visual components (Textual) from business logic.

### Main command flow

| Flag                     | Action                  | Pipeline                                                                 |
|--------------------------|------------------------|---------------------------------------------------------------------------|
| *(default)*              | PR description         | `git fetch` → diff against `origin/main` → AI → `.md`                    |
| `-c` / `--commit`        | Commit message         | `git diff HEAD` → AI → console (Conventional Commits)                     |
| `-r` / `--review`        | Local code review      | `git diff HEAD` → AI + Linter → `.txt`                                    |
| `-f` / `--fullreview`    | Full code review       | `git fetch` → diff against remote base → AI + Linter → `.txt`             |
| `-i` / `--input`         | File audit             | Entire file → AI (uses `.gitpr.filereview.md`)                            |
| `-l` / `--linter`        | Static linter          | `git diff` → YAML regex → console (no AI)                                 |
| `-is` / `--issue`        | Issue via TUI          | `git diff` → AI (draft) → Textual TUI → save .md or POST to GitHub       |
| `-is -ht` / `--history`  | Epic/Release issue     | `git log` + PR cache → AI → TUI                                           |
| `-is -b <file:lines>`    | Technical debt issue   | `git blame` timeline → AI → TUI                                           |
| `-b` / `--blame`         | Code archaeology       | `git blame` → AI classifies commits → timeline + summary                  |
| `-s` / `--skill`         | Download templates      | Download `.gitpr.*.md` from GitHub (never overwrites)                     |
| `-ih` / `--installhooks` | Install hooks           | Download + install hooks in `.git/hooks/`                                  |
| `-u` / `--update`        | Update                  | Check PyPI/GitHub Releases → hot-swap binary                              |
| `-h` / `--help`          | Contextual help         | Alone: all options. With flag: feature-specific help + docs link          |
| `--provider`             | Force AI provider       | `gemini` or `deepseek` (overrides default config)                          |

## Stack

| Component        | Technology                             |
|------------------|----------------------------------------|
| CLI framework    | Click >= 8.0.0                         |
| TUI (issues)     | Textual (ModalScreen, App, bindings)   |
| AI (Gemini)      | `google-genai` SDK                     |
| AI (DeepSeek)    | `openai` SDK (API compatible)          |
| GitHub API       | `requests` (REST, PAT via header)      |
| i18n             | Custom `__()` engine (Laravel-inspired) |
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

# Install dependencies (pip)
pip install -e .

# Run (dev mode)
pipenv run python run.py

# Run tests
pipenv run pytest -v
# or
python -m pytest tests/ -v
python -m unittest discover tests -v

# Build with PyInstaller
pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py

# Publish to PyPI
pipenv run python -m build
pipenv run twine upload dist/*
```

## Code preferences

### Python style
- **Language:** All variable names, function names, comments, and docstrings MUST be written in **English**
- **Encoding:** UTF-8 with `errors='replace'` for all file reads — NEVER use `errors='strict'` or bare `errors='ignore'`
- **Docstrings:** Free format (not strict Google/NumPy), in English
- **Typing:** Type hints are welcome but not mandatory — use where it improves clarity
- **Organization:** Each module has a single, clear responsibility. TUI components isolated in `src/ui/`
- **Naming:** snake_case for functions/variables, UPPER_CASE for constants, PascalCase for Textual classes
- **CLI:** Use Click with decorators; short flags (`-c`, `-r`, `-f`, `-is`) with long equivalents
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
  - `feat: add code archaeology module with git blame`
  - `refactor: extract TUI components to src/ui/ sub-package`
  - `fix: handle encoding in non-UTF8 environments`

### Commit rules
- NEVER amend already-pushed commits
- NEVER skip hooks (`--no-verify`, `--no-gpg-sign`)
- Commits must be atomic — one logical change per commit
- Messages in English
- Co-authorship in collaborative projects: `Co-Authored-By: Claude <noreply@anthropic.com>`

## Task rules (Task Workflow)

### When starting a task
1. **Read the context:** Check `CLAUDE.md`, relevant files, current diff
2. **Plan before coding:** For non-trivial features, use plan mode or present approach before implementing
3. **Check git state:** Correct branch, nothing accidentally staged
4. **Check dependencies:** `pipenv install --dev` if new packages are added to Pipfile

### During the task
5. **Follow existing style:** New code should look like it was always there
6. **Don't break the CLI:** Test main flows after changes (`gitpr`, `gitpr -c`, `gitpr -r`)
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
It must be placed in `docs/claude-code/reports/{branch}/{current_date}_{taskname}.md`, where `{current_date}` is today's date (`YYYY-MM-DD` format), `{branch}` is the current branch, and `{taskname}` is a short task description (only lowercase letters, numbers, and underscores, no spaces or special characters). Create the `docs/claude-code/reports/` folder if it doesn't exist.

## Project-specific notes

### Encoding
- All `subprocess.run()` capturing git output must use `encoding='utf-8'` with `errors='replace'`
- Output files (PR, review, blame, issue) must be written with `encoding='utf-8'`
- The project handles repositories that may contain non-UTF8 characters (legacy)

### Internationalization (i18n)
- `src/i18n.py` provides a `__()` function inspired by Laravel's translation engine
- `CURRENT_LANG` is auto-detected from the OS locale or forced via `GITPR_LANG` in `.env`
- English is the default/fallback language (no translation file needed)
- Other languages load JSON from `~/.gitpr/langs/{lang_code}.json` or download from GitHub
- Translation files are version-controlled via `__lang_version__` in `updater.py`
- The `get_doc_url()` function in `core.py` builds language-aware documentation URLs

### Skills System (Prompt Engineering)
- Local `.gitpr.<type>.md` files at the user's project root act as AI *System Instructions*
- Types: `commit`, `pr`, `review`, `filereview`, `blame`, `issue`, `linter.yml`
- Remote templates at `https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/`
- `--skill` downloads templates, but **never overwrites** existing local files
- Language-aware: EN downloads `gitpr.issue.md`, PT-BR downloads `gitpr.issue.pt_br.md`
- `get_skill_context()` in `core.py` manages fallbacks (tries `.gitpr.<type>.md`, then legacy `.gitpr.md`)

### User configuration
- Global directory: `~/.gitpr/`
- Config file: `~/.gitpr/.env` (dotenv format)
- Fernet key: `~/.gitpr/secret.key` (auto-generated on first run)
- Response cache: `~/.gitpr/cache/prompts/<action_folder>/<md5>.json`
- Update cache: `~/.gitpr/update_cache.json` (daily)
- Language files: `~/.gitpr/langs/{lang_code}.json`
- Environment variables: `DEFAULT_AI_PROVIDER`, `GEMINI_API_KEY_ENCRYPTED`, `DEEPSEEK_API_KEY_ENCRYPTED`, `GEMINI_API_MODEL`, `DEEPSEEK_API_MODEL`, `SECONDARY_GEMINI_API_MODEL`, `SECONDARY_DEEPSEEK_API_MODEL`, `OUTPUT_FILE_NAME`, `OUTPUT_FILE_NAME_REVIEW`, `OUTPUT_FILE_NAME_FULLREVIEW`, `OUTPUT_FILE_NAME_FILEREVIEW`, `OUTPUT_FILE_NAME_BLAME`, `OUTPUT_FILE_NAME_ISSUE`, `GITHUB_TOKEN_ENCRYPTED`, `SPINNER_THINKING_WORDS`, `GITPR_LANG`, `LANG_VERSION`

### AI Providers (Multi-Model Architecture)
- **Gemini:** `gemini-2.5-flash` (primary/advanced) / `gemini-2.5-flash-lite` (secondary/simple)
- **DeepSeek:** `deepseek-chat` (primary and secondary — same model)
- Both configured for JSON output (`response_mime_type` in Gemini, `response_format` in DeepSeek)
- Temperature 0.0 and top_p 0.1 for deterministic output
- Fallback: if configured provider fails, automatically try the other one
- `--provider` flag forces a specific engine for the execution

### Spinner (Animated loading indicator)
- `src/spinner.py` — runs in a background thread during AI calls
- Braille characters (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`) in magenta
- Thinking words loaded from `.env` (`SPINNER_THINKING_WORDS`) or downloaded from GitHub template
- Words "discovered" letter by letter with random characters, then dot cycle (`. .. ...`)
- Random word colors from a 10-color palette
- Retrocompatible cache: commit data JSON now includes `repo` field for multi-project filtering

### Static local linter
- Rules defined in `.gitpr.linter.yml` (YAML)
- Supports `error` (blocking) and `warning` (informational)
- Filters: file extension (`extensions`), `require_paths`, `ignore_paths`
- `ignore_comments: true` ignores comment lines (language-specific comment regex)
- In diff mode, only checks added lines (`+`) — focused and fast

### Blame engine (Code Archaeology)
- Maximum tracing depth: 4 parent commits
- Cheap model (secondary) for commit classification (`ORIGIN` vs `REFACTORING`)
- Advanced model (primary) for final executive summary
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
- `gitpr -h --issue`: feature-specific help + link to GitHub documentation
- `get_doc_url()` builds language-aware URLs: `.../docs/file.md` (EN) or `.../docs/file.pt_br.md` (PT-BR)
- All documentation files have EN originals and `.pt_br.md` copies

### Cache with repository name
- All cache JSON files include `"repo": "owner/repo"` field
- `get_cached_pr_descriptions()` filters by both `repo_name` AND `branch_name`
- Prevents mixing caches from different projects with same branch names

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
