# **🚀 GitPR - Intelligent Code Review and Pull Request Automation**

The **GitPR** is a Command Line Interface (CLI) tool developed in Python that acts as a software engineering assistant directly in the terminal. It combines the speed of local static validations with the analytical power of Artificial Intelligences (**Google Gemini**, **DeepSeek** and **Ollama** — local) to automate and raise the quality of Commits, Code Reviews, Issues and Pull Requests.

Beyond the CLI, GitPR also operates as an **MCP (Model Context Protocol) server** — exposing all of its AI capabilities to editors such as VS Code, Cursor, Claude Desktop, Zed and Claude Code — and offers TUI (Textual) interfaces for PR publishing, Issue creation, pair-programming chat and a metrics dashboard.

## **🎯 What is it for?**

The main goal of GitPR is to eliminate repetitive work and guarantee a high quality standard (*Quality Gate*) in the software development lifecycle. It solves three main problems:

1. **Polluted Git History:** Enforces *Conventional Commits* and generates semantic messages automatically — including via git hooks installed in the repository.  
2. **Empty or Poor Pull Requests:** Writes detailed descriptions based on the diff, separating technical changes from business impact, and publishes the PR directly on GitHub via TUI.  
3. **Technical Debt and Bugs:** Performs semantic Code Reviews and rule validations (Regex) before the code even leaves the developer's machine (*Shift-Left* approach), plus code archaeology with `git blame` to trace the origin of business rules.

---

## **✨ Key Features**

* **📝 Auto-Commit (`-c` / `--commit`):** Reads the staged changes (git diff) and generates a concise commit message in imperative format (Conventional Commits). In hook mode (`--hook`), injects the message directly into Git's temporary file; ignores merges, squashes and amends. Commits carry a `Co-Authored-By` trailer, appended only at execution time — the TUI edit screens never display it.  
* **📖 Pull Request Generation → PR Publisher (Default):** Analyzes the diff between the current branch and the main one, generating a .md with summary, impact and technical details. Then opens a TUI (Textual) to review, edit and publish the PR directly on the configured forge — GitHub by default, with GitLab, Bitbucket Cloud and Azure DevOps supported through the `ScmProvider` abstraction. Comes with linter-validated auto-commit, automatic push, existing PR update and optional merge. Modifiers: `--no-publish` (saves locally only), `--no-edit` (publishes directly, no TUI) and `--base <branch>` (target branch).  
* **🕵️ Intelligent Code Review (`-r` / `--review`):** Inspects the changed code looking for bad architecture practices, SOLID violations and security vulnerabilities.  
* **🔬 Full File Audit (`-i` / `--input`):** Points GitPR at a specific file (e.g. legacy code) so the AI performs a top-to-bottom architectural analysis, suggesting refactorings for the entire file.  
* **⚡ Local Static Linter (`-l` / `--linter`):** An ultra-fast Regular Expression (Regex) engine that runs locally to detect obvious errors (e.g. console.log, hardcoded keys) without spending AI tokens. Also supports **external linters** (ESLint, PHPCS, Stylelint) as a Checkstyle bridge — configured via an interactive wizard (`--linter-setup`).  
* **🪝 Git Hooks Integration (`-ih` / `--installhooks`):** Injects GitPR into Git's natural cycle, running the Linter on pre-commit or suggesting messages on prepare-commit-msg. Installs **5 hooks** (pre-commit, prepare-commit-msg, pre-push, post-checkout, post-merge) with **versioned and localized auto-sync** (EN, PT-BR, PT-PT, ES, FR).  
* **🗿 Code Archaeology (`-b` / `--blame`):** Traces the origin of a business rule with `git blame` + AI (maximum depth of 4 parent commits), classifying each commit as **ORIGIN** or **REFACTORING** and generating a timeline with an executive summary.  
* **📋 Standardized Issues (`-is` / `--issue`):** Generates an Issue draft in the **What / Why / Where / How** format and opens a TUI for editing or publishing via the configured forge's API (GitHub, GitLab, Bitbucket; Azure DevOps offers no universal issue endpoint — save locally). Has **3 context engines**: diff (default), branch history (`-ht`) and blame (`-b file:lines`).  
* **💬 Pair-Programming Chat (`-ch` / `--chat`):** Interactive TUI where the AI sees the current diff and keeps a contextual conversation, with memory per branch, slash commands (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patch and session export.  
* **🔌 MCP Server (`--mcp` / `gitpr-mcp`):** Exposes all AI capabilities as **12 tools**, **resources** and **7 prompts** for MCP-compatible editors (VS Code, Cursor, Claude Desktop, Zed, Claude Code). Automatic installation via `gitpr-mcp --install <editor|auto>`. Direct invocation without a persistent server: `gitpr-mcp --tool <name> --tool-args '{...}'` — JSON on stdout, diagnostics on stderr (safe for pipes, scripts and CI).  
* **📊 Metrics and Local Telemetry (`--metrics` / `--dashboard`):** Offline event collection (command, status, provider, tokens, duration) with CSV/JSON export and a TUI dashboard scoped by repository, enriched with real tokens read from the prompt cache.  
* **🧙 Setup Wizard (`--install`):** Guided setup in 4 steps — skill templates, git hooks, MCP configuration in detected editors and AI provider API key verification.  
* **🪄 SCM Forge Wizard (`--init`):** Detects the repository's forge from the origin remote (GitHub, GitLab, Bitbucket Cloud, Azure DevOps), collects provider extras and the access token, validates it against the forge API and persists the encrypted configuration (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, extras) — only on success.
* **🔎 File Status (`--status`):** Lists uncommitted files categorized (new / modified / deleted) — fast, no AI and no network.  
* **🧩 Plugin System (`--plugins`):** Global packs of linter rules (`~/.gitpr/plugins/linter/*.yml`) and MCP prompts (`~/.gitpr/plugins/prompts/*.md`) applied additively across all projects.  
* **🔄 Multi-Model (AI-Agnostic):** Choose between **Google Gemini**, **DeepSeek** or **Ollama** (local, no network) as the reasoning engine, switching dynamically via .env or the `--provider` flag, with automatic fallback between providers.  
* **🌐 Internationalization (`--lang`):** Interface in 5 languages with automatic OS detection, English fallback and temporary per-flag override.  
* **🗜️ Token Optimization (Map-Reduce + Smart Excludes):** Diffs above ~90k tokens are split into per-file chunks and summarized (Map) before the final consolidation (Reduce). Lockfiles, minified files and documentation are excluded from the diff automatically (remote lists + per-project local configuration).  
* **🔄 Auto-Update (`-u` / `--update`):** Checks the GitHub Releases (binary) or PyPI (pip) and replaces its own executable (*hot-swap*) with rollback on failure.  

---

## **🛠️ Development and Architecture Details**

GitPR was architected focusing on **Performance**, **Security** and **Extensibility**.

### **1. Facade/Mediator (core.py)**

The `core.py` module orchestrates everything: git operations, prompt assembly, cache, skills, hooks, smart excludes and file output. The CLI (`main.py`) only routes flags; the specialized modules (AI, linter, blame, issues, MCP, metrics, TUI) are coordinated by the core. The visual components stay isolated in the `src/ui/` sub-package.

### **2. Skills System (Decoupled Prompt Engineering)**

Instead of hardcoding the AI *prompts* in the Python code, GitPR uses a system of local .md files (Skills) that act as *System Instructions*.

* .gitpr.commit.md  
* .gitpr.pr.md  
* .gitpr.review.md  
* .gitpr.filereview.md  
* .gitpr.issue.md  
* .gitpr.blame.md  

This allows each team to adapt the "personality" and business rules of the AI without changing a single line of the tool's source code. The files live in `.gitpr/skill/` (with automatic migration of legacy paths from the project root).

### **3. Strategy Pattern for AI Providers**

The `ai_providers.py` module isolates communication with the external APIs. The engine (Core) only asks for JSON, and this module decides how to format the request using Google's SDK (Gemini) or OpenAI's SDK (DeepSeek and Ollama — 100% OpenAI API compatible). Characteristics:

* **Automatic Retry** (3 attempts, 2s interval) for network instability.  
* **Automatic fallback** to the other provider when the configured one fails.  
* **Mandatory structured JSON** and temperature 0.0 for deterministic output.  
* **Model tiering by complexity:** simple tasks (commit) use the secondary/cheap model; advanced tasks (review, PR, issue) use the primary model.

### **4. Key Security (Cryptography)**

API keys (API_KEYS) are never saved in plain text. The `security.py` module uses the cryptography library (Fernet) to generate a local master key and store the credentials encrypted in the `~/.gitpr/.env` file. The **GitHub PAT** follows the same pattern and is validated against `api.github.com/user` before any use, with a re-authentication loop (max 3 attempts) when it expires.

### **5. MD5 Cache System**

To save AI token consumption (money) and time (latency), GitPR creates an MD5 hash of the *prompt* generated from the *diff*. If the developer asks for a Code Review of the same code twice, the system recovers the response from the `~/.gitpr/cache/prompts/` directory instantly. Each entry stores **repo + branch** — the double filter avoids collisions between projects with the same branch name, and the cached PR history feeds the history-issue context (`-ht`).

### **6. Triple "Quality Gate" (Performance)**

The tool was designed to balance resource consumption:

* **Layer 1 (Local Linter):** Fast (<100ms), offline, syntax-focused (via linter_engine.py and .gitpr.linter.yml).  
* **Layer 2 (External Linters):** Checkstyle bridge — runs ESLint/PHPCS/Stylelint and filters errors only for the lines changed in the diff.  
* **Layer 3 (Cloud AI):** Deep (2s-8s), online, focused on semantics and intent.

### **7. Map-Reduce for Giant Diffs**

When the diff exceeds ~90k estimated tokens, GitPR splits it into per-file chunks (preserving the `diff --git` headers), asks the AI for a technical summary of each part (Map) and unifies everything into the final commit, review, PR or issue message (Reduce). Automatic activation, no flags — with console progress and its own metric.

### **8. Smart Excludes (Token Optimization)**

Non-code files are removed from the diff before it goes to the AI, with two remotely controlled layers: lockfiles/generated (`.lock`, `*.min.js`, `*.map`, `*.svg`…) and documentation prose (`*.md`, `*.txt`, `*.rst`…). Changed documentation is still communicated to the AI as **metadata** (paths only, no content). Each project can add local exclusions in `.gitpr/conf/gitpr.smart-excludes.json`, merged with the global list at runtime. Overrides via env: `GITPR_SKIP_SMART_EXCLUDES`.

### **9. Unstaged Files Check**

Before any AI command, GitPR lists the uncommitted files (new/modified/deleted) and offers a staging selection TUI — or auto-stages when `GITPR_AUTO_STAGE=true`. The behavior is adapted per command (PR/issue require staging, review only informs) and can be disabled with `--no-unstaged-check`.

### **10. Centralized Output (.gitpr/reports/)**

All generated artifacts (PR, review, full review, file review, blame, issue, linter) are saved to `.gitpr/reports/<type>/` via `resolve_output_path()`. Custom paths in `.env` (with directory separator) are respected — only "bare" filenames are redirected (backward compatible). The linter report is only generated when violations are found.

### **11. Offline Telemetry (Fire-and-Forget)**

The `metrics.py` module records events on daemon threads — telemetry can never break the CLI. Each event stores command, status, provider, tokens, duration (via `time.perf_counter()`), repo and branch. The dashboard enriches the events with **real tokens** read from the prompt cache and merges incrementally with the cache.

### **12. Global Plugin System**

`~/.gitpr/plugins/` holds packs of linter rules (`linter/*.yml`) and MCP prompt templates (`prompts/*.md`). The rules are merged **additively** with the project's `.gitpr.linter.yml`; the prompts become dynamic MCP resources and prompts via factory closures (avoiding late-binding in loops). Malformed plugins raise a warning, never break execution.

### **13. MCP Server (stdout Isolation)**

The `mcp_server.py` runs over stdio and exposes 12 annotated tools (`get_git_context`, `analyze_diff`, `analyze_unstaged_diff`, `get_full_diff`, `list_unstaged_files`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`), resources (skills, linter, prompts) and 7 pre-built prompts. The architecture isolates JSON-RPC via **stdout monkey-patching** (every print is redirected to stderr, exposing only the real buffer to the MCP transport) — applied before any internal import. The `--tool` mode invokes any tool directly from the command line without a persistent server. Since the MCP SDK runs sync handlers inline on the event loop, all 12 handlers are wrapped in an `_offload` decorator (anyio worker threads) so blocking work (git subprocess, downloads, AI calls) never freezes the stdio server.

### **14. TUI Ecosystem (Textual)**

The visual interfaces live in `src/ui/` and follow common patterns: state returned via `final_action`/`final_message` (allowing re-authentication loops in main), AI calls on background threads, help modals (F1) with localized URLs, and the `_with_real_stdout()` wrapper that works around the Textual×click conflict on Windows. Applications: `PrPublishApp` (PR publishing with staging, commit, linter and error screens), `IssueApp`, `ChatApp`, `MetricsApp` and `LinterApp`.

### **15. Internationalization Engine (__())**

`src/i18n.py` implements an engine inspired by Laravel's `__()` helper: English keys in the code, translations in JSON (`~/.gitpr/langs/{lang}.json`) downloaded OTA when the language changes, fallback to the English text itself and named-placeholder support. Languages: EN, PT-BR, PT-PT, ES, FR.

### **16. Version Markers (OTA Resources)**

Remote resources (translations, thinking words, smart excludes, linter presets, hook scripts) are re-downloaded in bulk when the version markers (`__lang_version__`, `__scripts_version__` in `updater.py`) change. The installed hooks are compared against `SCRIPTS_VERSION` + `SCRIPTS_LANG` in `.env` and **silently auto-synced** on every run (respecting the user's language).

The five markers (`LANG_VERSION`, `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`, `SCRIPTS_VERSION`), what each one caches and the correct order for publishing a change are documented in **[version-markers.md](version-markers.md)**.

### **17. Auto-Update System**

Built with PyInstaller packaging, the `updater.py` module checks the repository's *Releases* on GitHub. If a new version exists, the executable downloads the new binary, replaces itself (*hot-swap*) and relaunches the command seamlessly — with automatic rollback on failure. Daily cached check (`~/.gitpr/update_cache.json`) and connection guard (socket `8.8.8.8:53`) before any network operation.

### **18. Adaptive Spinner**

During AI calls, the `spinner.py` runs on a background thread with braille characters, "thinking words" discovered letter by letter (remotely controlled list, cached by version) and speed adaptive to the sentence length.

### **19. Multi-Forge SCM (ScmProvider)**

PR and issue publication is no longer GitHub-only (in development after v0.0.37). `src/infrastructure/scm/` abstracts the Git hosting forges behind one contract:

* **`base.py`** — `ScmProvider` ABC (11 abstract methods: create/check/update/merge PR, diff, list open PRs, comment, issues, connection test, repo parsing), the `RepoRef`/`PullRequestRequest`/`PullRequestResult`/`IssueRequest`/`IssueResult` dataclasses and the `ScmProviderError` / `ScmNotSupportedError` hierarchy.
* **Providers** — one module per forge (`github_provider.py`, `gitlab_provider.py`, `bitbucket_provider.py`, `azure_devops_provider.py`), each implementing the same REST verbs with forge-specific auth and payloads. Providers **raise** `ScmProviderError` (`http_status` 0 = network) — the old silent `(ok, data, status)` tuples survive only at the UI boundary (`src/github_api.py` is now a deprecated shim).
* **`factory.py`** — `resolve_scm_provider()` selects the provider from the `GITPR_SCM_PROVIDER` env key (default `github`, falling back to the legacy `GITHUB_TOKEN_ENCRYPTED` token — zero migration); `detect_provider_from_remote()` guesses the forge from the origin remote URL.
* **`--init` wizard** — `core.run_scm_init_wizard()` detects the forge, collects provider extras (Azure organization/project, Bitbucket username) and the access token, validates it via `test_connection()` (3 attempts, 401 re-prompt) and persists **only on success**: `GITPR_SCM_PROVIDER` + `GITPR_SCM_TOKEN_ENCRYPTED` (Fernet) + extras.
* **Design notes** — see the [Multi-Forge glossary and ADR](plans/glossary-scm-multiforge.md) in `docs/plans/` for forge-specific quirks (Azure `api-version`, GitLab `iid` vs `id`, Bitbucket App Password, Azure textual diff summary) and the approved deviations.

---

## **💻 Technology Stack**

| Component | Technology |
| --- | --- |
| CLI framework | click >= 8.0.0 |
| TUI (issues, PRs, chat, dashboard) | Textual (ModalScreen, App, bindings) |
| AI (Gemini) | `google-genai` SDK |
| AI (DeepSeek / Ollama) | `openai` SDK (API compatible) |
| MCP Server | `mcp` (official Python SDK) |
| GitHub API | `requests` (REST, PAT via header) |
| i18n | Custom `__()` engine inspired by Laravel |
| Config/Build | `pyproject.toml` + setuptools >= 61 |
| Encryption | `cryptography.fernet` (symmetric) |
| Linter | `pyyaml` (rules) + regex |
| Tests | pytest + unittest.mock |
| Packaging | PyInstaller (standalone executable) |

---

## **🗂️ Project Structure**

```text
src/
├── main.py           # CLI (Click) — command and flag routing
├── core.py           # Orchestration — git ops, AI prompts, cache, skills, hooks
├── config.py         # Configuration, .env, API keys, models, plugins
├── security.py       # Fernet encryption (API keys at rest)
├── cache.py          # Local AI response cache (MD5, repo+branch)
├── ai_providers.py   # Unified AI call layer (Gemini + DeepSeek + Ollama)
├── spinner.py        # Animated braille spinner with thinking words
├── i18n.py           # Internationalization engine (__())
├── linter_engine.py  # Static analysis with regex (YAML rules) + external linters
├── linter_wizard.py  # External linters setup wizard (Checkstyle bridge)
├── blame_engine.py   # Code archaeology with git blame + AI
├── issue_engine.py   # AI-powered issue generation (3 context engines)
├── chat_memory.py    # Chat session persistence (repo+branch, diff history)
├── tui_issue.py      # SCM token validation (validate_or_request_scm_token) + TUI entry point
├── metrics.py        # Offline telemetry (fire-and-forget, cache enrichment)
├── infrastructure/   # Domain infrastructure
│   └── scm/          # Multi-forge SCM: base.py (ScmProvider ABC, dataclasses, errors),
│                     # github/gitlab/bitbucket/azure_devops providers + factory.py
├── github_api.py     # DEPRECATED shim → src/infrastructure/scm/github_provider.py
├── mcp_server.py     # MCP server (stdio) + tools/resources/prompts + --tool mode
├── updater.py        # Version check (PyPI + GitHub), hot-swap and version markers
└── ui/               # Sub-package: TUI components (Textual)
    ├── __init__.py       # Package marker (setuptools discovery)
    ├── issue_app.py      # Issue editing and publishing TUI
    ├── pr_publish_app.py # PR publisher TUI + staging selection + commit screens
    ├── chat_app.py       # Pair-programming chat TUI
    ├── metrics_app.py    # Metrics dashboard TUI
    ├── linter_app.py     # Linter violations display
    ├── help_screen.py    # Help modal (F1) — shortcuts and instructions
    └── pr_publish_help.py # PR publisher help modal

scripts/            # Localized git hook templates (5 languages)
templates/          # Remote templates served from GitHub (--skill)
langs/              # Translation files (pt_br, pt_pt, es, fr)
tests/              # Unit tests (unittest + mock)
docs/               # Technical documentation (EN canonical + language suffixes)
```

---

## **📚 Detailed Documentation**

Each feature has a dedicated guide in `docs/` (English canonical + `.pt_br` / `.pt_pt` / `.es_es` / `.fr_fr`):

* [pull-request-publication.md](pull-request-publication.md) — PR Publisher (TUI, auto-commit, merge)  
* [pr-descricao-padrao.md](pr-descricao-padrao.md) — Default PR description mode  
* [understanding_chat_functionality.md](understanding_chat_functionality.md) — Pair-programming chat  
* [mcp-integration.md](mcp-integration.md) — MCP integration with editors  
* [mcp-annotations.md](mcp-annotations.md) — MCP tool annotations  
* [mcp-prompts.md](mcp-prompts.md) — MCP predefined prompts  
* [metricas-telemetria.md](metricas-telemetria.md) — Metrics and local telemetry  
* [plugins-system.md](plugins-system.md) — Global plugin system  
* [map-reduce-diff.md](map-reduce-diff.md) — Map-reduce for giant diffs  
* [smart-excludes.md](smart-excludes.md) — Token optimization  
* [hooks-versioning.md](hooks-versioning.md) — Hook versioning and auto-sync  
* [git-hooks-locais.md](git-hooks-locais.md) — Local git hooks guide  
* [linter-regras-customizadas.md](linter-regras-customizadas.md) — Linter rules and external linters  
* [guia-regex-gitpr.md](guia-regex-gitpr.md) — Regex guide for linter rules  
* [github-ci-linter.md](github-ci-linter.md) — CI integration for the linter  
* [blame-arqueologo.md](blame-arqueologo.md) — Code archaeology (git blame)  
* [issue-tui-help.md](issue-tui-help.md) — Standardized issues and TUI  
* [gitpr-issue-option.md](gitpr-issue-option.md) — Issue generation options  
* [commit-message-ia.md](commit-message-ia.md) — AI commit messages  
* [code-review-ia.md](code-review-ia.md) — AI code review  
* [install-wizard.md](install-wizard.md) — Setup wizard  
* [i18n_explanation.md](i18n_explanation.md) — i18n engine  
* [github-pat-integration.md](github-pat-integration.md) — GitHub PAT security  
* [git-status.md](git-status.md) — Uncommitted file status listing  
* [untracked-files.md](untracked-files.md) — Untracked files explanation  
* [auto-update.md](auto-update.md) — Auto-updater (hot-swap)  
* [providers-ia.md](providers-ia.md) — AI providers (Gemini, DeepSeek, Ollama)  
* [skill-template.md](skill-template.md) — Skills and templates system  

Tutorials (Portuguese only):

* [github-issue-prompt-com-gh.md](github-issue-prompt-com-gh.md) — Formatting and updating issues via gh CLI  
* [como_reverter_commit_git_localmente.md](como_reverter_commit_git_localmente.md) — Reverting commits locally  
* [testar_sem_usar_pypi.md](testar_sem_usar_pypi.md) — Testing without spending a PyPI version  
* [otimizacao-de-tokens.md](otimizacao-de-tokens.md) — Token optimization in context files (.gitpr.*.md)  

---
