# Changelog

## [v0.1.0] - 2026-09-07

### Summary
Esta versão traz grandes melhorias de usabilidade e integração: o fluxo de Pull Requests agora conta com sugestão de revisores, publicação e merge diretamente pela ferramenta. Também foram adicionados provedores de SCM multi-forge, suporte a plugins globais e locais, integração com linters externos (com assistente de configuração) e um sistema de métricas/telemetria com painel e exportação CSV. A internacionalização foi ampliada para vários idiomas, com correção de chaves de tradução e garantia de paridade. No desempenho, grandes diffs agora são processados com estratégia map-reduce. A segurança foi reforçada com prevenção de injeção de shell e limites de tempo em resoluções DNS. Também há suporte a servidor MCP para editores, integração com Ollama, nova interface de chat e diversas melhorias de documentação.

### ✨ Features
- add suggested reviewers to PR flow (c7148ed)
- add multi-forge SCM providers, migrate tests, expand translations (dd2ecef)
- add i18n translations and enhance issue/blame skill loading (9a9affb)
- add metrics export (f78970c)
- add coauthor trailer to commits (4bf8e48)
- add external linter support and setup wizard (97e584a)
- add metrics export (397ba94)
- add status translations for languages (b0ac04d) — i18n
- handle PR merge success and failure states (600a6a1)
- add mcp tool cli flag (1cc4545)
- add CLI version option (8a1adb3)
- add project-local smart excludes (86194ef)
- add unstaged files handling and telemetry exports (d3129e3)
- add global plugin system (6210d97)
- add map-reduce for large diff processing (f91af9e)
- add map-reduce for large diff issue generation (15b01ed)
- add pull request merge flow (d8283dd)
- add option to push to existing PR (744fc15)
- add existing PR handling on publish (47a9004)
- enhance progress screen with initial status (3ff5820)
- add git push before PR publishing (886c835)
- add PR publisher with TUI and auto-commit (02aa34e)
- add docs smart excludes (9a297d3)
- add i18n and automatic hook sync (6743691)
- add metrics for linter, blame, and git hooks (f509662)
- add i18n cache, sync script, and expanded translations (26c2628)
- track AI call duration and enhance metrics dashboard (1e1bfdc)
- add repo-scoped metrics dashboard and token reauth (08ba813)
- add metrics and telemetry system with CSV export and TUI dashboard (7876914)
- add MCP Tool Annotations and template-based prompts (5efd7cb)
- add adaptive speed to spinner and expand thinking words (5e3b3dc)
- add MCP prompts for common GitPR workflows (bb8287d)
- add interactive setup wizard (--install) (d69fa13)
- add MCP config installer and Claude Code support (b42ce80)
- add MCP server integration for editor support (9a25d81)
- add map-reduce, remote smart excludes, and --pre-save flag (67b300d)
- add interactive chat TUI, --lang flag, and Ollama support (d6fca4f)
- internacionaliza skills, spinner e documentação (bf46833)
- adds support for the Ollama provider (1655b95)
- adota inglês como idioma padrão e implementa i18n com  es, fr, pt_pt (f4c718c)
- implementa internacionalização com suporte a pt-BR e en-US (a1d6692)
- adiciona spinner animado com braille e palavras de pensamento (c9cdbf9)
- adiciona suporte a múltiplos repositórios no cache (9dc242c)
- adiciona ajuda contextual e documentação técnica (ad72ca2)
- adiciona motor triplo de contexto para criação de issues (ce86bcb)
- atualiza pyproject.toml (4844eb7)
- adiciona geração de issues padronizadas com TUI e integração GitHub (c76f9ae)
- adiciona geração de issues padronizadas com TUI e integração GitHub (cd458b8)
- adiciona módulo de arqueologia de código com git blame (ad4f3f4)
- adiciona suporte a PyPI e aviso de atualização (4118639)
- prepara projeto para distribuicao no PyPI (38e2e37)
- adiciona alerta de arquivos não monitorados no git diff e documentação (e56ff7a)
- adiciona suporte multi-modelo e auditoria de arquivos completos (dc1fba1)
- adiciona modo de revisão de arquivo completo via --input (4a4f53b)

### 🐛 Fixes
- silence CLI tool output and bound DNS resolution (681a7fa)
- prevent shell injection in linters and bound network timeouts (7324ff2)
- resume commit flow after linter --no-verify (3d2a63a)
- translate untranslated keys and normalize newlines (e2f0fa0) — i18n
- offload MCP tool handlers from the event loop to fix server hangs (9d4d58c)
- generate linter report only on violations (eebd507)
- make sync script extraction capture only the string literal (4dc5119) — i18n
- repair 51 mangled translation keys, prune dead keys, bump lang version to v0.0.16 (2ea73ce) — i18n
- improve git add error handling and file selection (4302b58)
- skip AI commit message on git-generated sources (merge, squash, amend) (827b77c)
- change thinking words delimiter to semicolon and sync translations (9db4a29)

### ⚡ Performance
- adiciona filtro smart para reduzir tokens da IA (f7ce5c0)

### 📚 Docs
- update technical documentation: Suggested Reviewers (a645def)
- update technical documentation (ddc8fff)
- update technical documentation (1b090f2)
- update technical documentation (43ab597)
- change GEMINI.md and CLAUDE.md files (7ae8a5c)
- updates readme (77b63bc)
- updates pr desc reports (dfd7684)
- update technical documentation (a755237)
- add plan and completion report for i18n mangled keys cleanup (46c4f6b)
- update README.md (6ba6ccb)
- atualiza memória do projeto (9b00eda)
- document merge-source skip in git-hooks-locais docs (7e28aeb)
- add Claude memory index and pattern docs (8637209)
- add v0.0.6 status report and bump version to 0.0.31 (cb5bc77)
- enhance MCP prompts docs with template info and resources (e6f0556)
- finaliza traduções multilingues e adiciona plano de chat (f8f54a2)
- reestrutura documentação e destaca ajuda contextual (aaf7330)

### ♻️ Refactoring
- hide coauthor trailer from TUI (d65c175)
- format codebase for consistency (c67ab6a)
- remove unused FileStageScreen and update translations (4570646)
- centralize output path resolution (cae5be5)
- extract MCP prompts to template files (2c3fb5b)
- remove fallback pipenv e adiciona errors='replace' (aa675a7)

### 🔧 Chores
- update repo URL and localize issue prompts (fa4bac1)
- bump versions to 0.0.32 and v0.0.10 (4c0d05e)
- derive version from updater and update pt_PT (25e3103)
- update lang version and refine spinner output (5dad289)
- delete exported chat log files (60ea186)
- atualiza versão para 0.0.23 (1e2e752)
- atualiza versão para 0.0.18 e corrige empacotamento (d77132a)

### 📦 Other Changes
- guard against mangled keys and enforce language parity (9ca8146) — i18n
- Create other lenguages to plugins-system doc (52229a9)
- Add tokenizer.json (1560d4f)
- Adiciona lista Thinking Words (9485cd4)
- AJustes finais (38e62d4)
- Update to 0.0.14 (60fb15f)
- Retira índice de comantários (306dc11)
- Update linter-regras-customizadas.md (1689e6e)
- Remove arquivos desnecessários (b55df27)

**Contributors:** Nataniel Fiuza

All notable changes to GitPR CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Multi-Forge SCM abstraction** (`src/infrastructure/scm/`): single `ScmProvider` interface over GitHub, GitLab, Bitbucket Cloud and Azure DevOps — pull requests, issues, diffs, comments, merges and connection checks behind one contract (`base.py`, `factory.py`, one provider module per forge).
- **`--init` flag**: Interactive SCM forge wizard (`core.run_scm_init_wizard()`) — detects the forge from the origin remote, validates the access token (`test_connection`, up to 3 attempts, 401 re-prompt) and persists configuration **only on success** (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` via Fernet, plus provider extras).
- **GitLab, Bitbucket Cloud and Azure DevOps providers**: PR create/check/update/merge, diff, comments, issue creation (Bitbucket requires the Issue Tracker enabled; Azure DevOps raises not-supported for issues — Work Items depend on the process template).
- **SCM configuration keys**: `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN` (CI/raw), `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME` in `DEFAULT_CONFIG`/`setup_environment`.

### Changed
- Providers now **raise** `ScmProviderError(provider, http_status, message)` instead of swallowing failures (`http_status` 0 = network); the legacy `(ok, data, status)` mapping lives at the UI call sites.
- Repository addressing goes through `parse_repo_ref()` → `RepoRef` (GitHub owner / GitLab namespace / Bitbucket workspace / Azure display-only `org/project`); the TUI publisher, the issues TUI and the direct publish flow resolve the provider from config.
- i18n dictionaries expanded to 675 keys per language (6 files).

### Deprecated
- `src/github_api.py` is now a deprecated shim delegating to `GitHubProvider` (same 4 signatures, same `(ok, data, status)` tuples, `DeprecationWarning`); no internal code imports it anymore.

### Documentation
- [docs/plans/glossary-scm-multiforge.md](docs/plans/glossary-scm-multiforge.md) — canonical Multi-Forge vocabulary.
- [docs/plans/ADR-001-scm-abstraction.md](docs/plans/ADR-001-scm-abstraction.md) — decision record with the 10 approved deviations from the spec.

---

## [0.0.33] — 2026-08-09

### Added
- **PR Publisher TUI** (`gitpr` default): Interactive terminal interface to review, edit, and publish Pull Requests directly to GitHub via REST API. Includes title, body, and base branch editing with F1 help, F2 save, F3 publish, and Esc exit bindings.
- **`--no-publish` flag**: Generate PR description and save locally without opening the interactive editor.
- **`--no-edit` flag**: Skip the TUI entirely — auto-commit pending changes (with lint validation), auto-push, and publish directly to GitHub. Ideal for CI/CD pipelines.
- **`--base <branch>` flag**: Override the target branch for the Pull Request.
- **Auto-commit flow**: When `--no-edit` or F3 is used with uncommitted changes, GitPR runs the static linter, generates an AI commit message (Conventional Commits), confirms with the user, and executes `git commit` before publishing.
- **TUI commit dialogs**: `CommitConfirmScreen`, `FileStageScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, and `ErrorScreen` modals for a rich commit experience inside the terminal.
- **Unstaged files management**: At startup, GitPR checks for unstaged files and offers a `StageFilesApp` TUI modal to select, skip, or cancel before PR generation.
- **Existing PR handling**: When a PR already exists for the current branch, the TUI offers to push changes to the existing PR (updating its body via PATCH) or create a new one.
- **Auto-upstream on push**: When `git push` fails due to missing upstream, GitPR automatically retries with `--set-upstream origin <branch>`.
- **"Nothing to commit" detection**: Commit failures due to no staged changes are now treated as success — the flow continues to PR publication instead of erroring.
- **Merge flow**: After PR creation or update, GitPR can optionally merge the PR. Controlled by `GITPR_AUTO_MERGE` env var.
- **Centralized output paths**: All generated files now default to `.gitpr/reports/` organized by artifact type (`pr_desc/`, `review/`, `full_review/`, `file_review/`, `blame/`, `issue/`). Custom directory paths in `.env` are honored as-is for full backward compatibility.
- **`GITPR_AUTO_COMMIT`** env var: Skip commit confirmation prompt during auto-commit.
- **`GITPR_SKIP_LINT`** env var: Skip linter validation during auto-commit.
- **`GITPR_AUTO_STAGE`** env var: Automatically stage all unstaged files without showing the selection modal.
- **`GITPR_SKIP_UNSTAGED_CHECK`** env var: Skip the unstaged files check entirely at startup.
- **`GITPR_SHOW_LOGS`** env var: Control commit/push progress log display in the TUI.
- **`GITPR_AUTO_MERGE`** env var: Auto-merge PRs after creation/update without prompting.
- **Multi-language technical documentation**: `docs/pull-request-publication.md` in 5 languages (EN, PT-BR, PT-PT, ES, FR).
- **GitHub API module** (`src/github_api.py`): Shared functions for `create_pull_request()`, `update_pull_request()`, and `merge_pull_request()`.

### Changed
- **Default behavior**: Running `gitpr` now opens the TUI publisher by default (was: save file and exit).
- **Output directory**: Files now save to `.gitpr/reports/{type}/` by default instead of the project root. Backward compatible.
- **README**: Updated with PR publisher features, output directory structure, and documentation links in all 5 languages.

### Fixed
- `OSError: [Errno 9] Bad file descriptor` when Textual TUI calls `click.secho()` by adding `_with_real_stdout()` wrapper.
- PR body sent to GitHub now contains only the TextArea content — no wrapper or commit message prefix.
- Error screen modal sizing: capped at `max-height: 80%` with `overflow-y: auto` for large error outputs.

---

## [0.0.32] — 2026-08-06

### Added
- **i18n coverage expanded to 491 keys** (+44 from v0.0.31): Full synchronization of `__()` calls in `core.py`, `main.py`, and `linter_engine.py` with translation dictionaries. New `tests/sync_i18n.py` script to detect orphaned translation keys in any source file.
- **Smart Excludes for documentation files**: Pathspec filter now detects and excludes documentation files (`.md`, `.rst`, `.txt`) from diffs, with visual notification (`📄 {count} documentation file(s) excluded`) and documentation link.
- **Git Hooks auto-sync with versioning**: `__scripts_version__` (v0.0.1) independent version marker for hook scripts. Running `--installhooks` automatically checks and updates hooks when the remote version changes, with language-aware template download.
- **Metrics for Linter, Blame, and Git Hooks**: `log_hook_event()` for hook events, `log_linter_metric()` for standalone linter runs, `log_blame_metric()` for code archaeology — all with duration, error counts, and repo-scope.
- **Cache i18n indexing**: AI response cache now includes the current language in the MD5 key, preventing collisions between responses generated in different languages.
- **Centralized versioning**: `__version__` and `__lang_version__` now derived exclusively from `src/updater.py` (single source of truth), eliminating duplication with `pyproject.toml`.
- **Architecture patterns memory index**: 14 documented patterns extracted from 36 task reports, covering cache, spinner, MCP, metrics, UI, versioning, and other subsystems.

### Changed
- **Language dictionaries**: `__lang_version__` updated to v0.0.10.
- **Test suite**: Expanded to 12 test files with 131 scenarios (100% pass rate).

---

## [0.0.31] — 2026-08-03

### Added
- **Dashboard TUI reformulated with repo-scope**: Isolated metrics by repository (`repo_filter`), asynchronous unlimited cache file scanning (`~/.gitpr/cache/prompts/`), visual overlay with `ProgressBar`, unified token totals per project, processed cache file tracking (`./.gitpr/metrics/{repo}/processed_cache.json`).
- **Wall-clock duration tracking**: `duration_ms` injected via `time.perf_counter()` in all LLM responses, persisted through cache, and displayed in the metrics dashboard.
- **Local export per project**: `gitpr --metrics --export` now generates CSV and JSON reports in the local project folder (`./.gitpr/metrics/export/`) filtered by the active repository.
- **GitHub Token auto-reauth on 401**: PAT validation via `GET /user`, pre-validation before TUI issues (`gitpr -is`), and graceful HTTP 401 recovery without losing drafts.
- **Quick Start in READMEs**: Installation instructions (`pip install gitpr-cli` and `gitpr --install`) added to all 5 language READMEs.
- **`GEMINI.md` guide**: Complete architectural guide, code conventions, command pipeline, and report patterns for Gemini-based development.

### Changed
- **Thinking Words delimiter**: Changed phrase separator from comma (`,`) to semicolon (`;`), allowing complex phrases with internal commas without breaking parsing.
- **Test suite**: 10 test files with 114 scenarios.

### Fixed
- **Dashboard F5 refresh**: Fixed duplicate column bug on refresh by using single-initialization (`_setup_columns()`).

---

## [0.0.30] — 2026-07-26

### Added
- **Metrics & Telemetry system** (`src/metrics.py`, `src/ui/metrics_app.py`): Local offline fire-and-forget event collection in `~/.gitpr/metrics/{owner}/{branch}/`. Each CLI command generates an async JSON event with timestamp, command, status, provider, tokens, duration, repo, and branch.
- **CSV/JSON export**: `gitpr --metrics --export` consolidates all unexported events with `click.progressbar()`, generating `gitpr_metrics_YYYY-MM-DD.csv` and `.json`.
- **Metrics purge**: `gitpr --metrics --purge` removes metrics files after user confirmation.
- **Dashboard TUI**: `gitpr --metrics --dashboard` opens an interactive Textual interface with DataTable (last 100 events), summary bar (totals, errors, tokens, top commands/providers), and F5/Esc bindings.
- **Git Hooks for telemetry**: `post-checkout`, `pre-push`, `post-merge` hooks for behavioral telemetry, installed via `--installhooks`.
- **`--install` flag**: Guided 4-step wizard that downloads skill templates, installs Git Hooks, configures MCP in editors, and validates API keys.
- **Expanded Thinking Words**: 263 entries per language (31 "Sussing" + 31 "Cerebrating" phrases added to the existing 201 entries).

### Changed
- **i18n expanded**: 447 translation keys per language (+83 from v0.0.29: 16 metrics CLI + 20 dashboard TUI + 47 incremental).
- **Language dictionaries**: `__lang_version__` updated to v0.0.8.
- **Code cleanup**: All comments and docstrings in `src/metrics.py`, `src/main.py`, and `src/ai_providers.py` translated to English.

### Fixed
- **Spinner flickering**: Replaced `ljust(70)` with ANSI `\033[K` (clear to end of line) to eliminate visual artifacts when switching from long to short phrases.

---

## [0.0.29] — 2026-07-25

### Added
- **MCP Prompts with templates**: 7 MCP prompts with content externalized into 35 template files (7 prompts × 5 languages) in `templates/gitpr.prompt.*.md`, with automatic language fallback.
- **MCP Tool Annotations**: All 10 MCP tools annotated with `readOnlyHint`, `destructiveHint`, and `idempotentHint` for better IDE integration (3 read-only, 7 with side effects).
- **MCP Prompt resources**: 8 new `prompt://` resources (7 templates + `prompt://list`) exposed via MCP server.
- **Expanded Thinking Words**: 201 entries per language (84 words + 117 phrases), with creative phrases merged from `words_happy.md`.
- **Adaptive spinner speed**: Long phrases (36+ characters) revealed faster (1 frame/letter, 0.04s) to display full text before switching words. Short words maintain original speed.

### Changed
- **MCP Resources**: Increased from 7 to 15 (skills + linter + prompts).
- **Documentation**: 110+ pages across 5 languages (+2 new topics: `mcp-prompts.md`, `mcp-annotations.md`).
- **Test suite**: 8 test files with 165+ scenarios.

---

## [0.0.28] — 2026-07-24

### Added
- **MCP Server integration** (`src/mcp_server.py`): GitPR now operates as an MCP (Model Context Protocol) server, exposing all AI capabilities as tools directly inside editors like VS Code, Cursor, and Claude Desktop — no terminal needed.
- **10 MCP Tools**: `get_git_context`, `analyze_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`.
- **7 MCP Resources**: Skill templates (`skill://pr`, `skill://commit`, etc.) + linter config (`linter://config`).
- **MCP Installer** (`gitpr-mcp --install`): Automatic configuration for 6 editors (VS Code, Cursor, Claude Code, Claude Desktop, Zed) with intelligent JSON merge — idempotent and safe.
- **`gitpr-mcp` entry point**: Dedicated console script registered in `pyproject.toml` for MCP transport.
- **`--mcp` flag**: Alias via main CLI (`gitpr --mcp`) to start the MCP server on stdio transport.
- **MCP output isolation**: Monkey-patching system that redirects all terminal output (banners, spinners, colors) to stderr, keeping stdout clean for the JSON-RPC 2.0 protocol.

### Changed
- **i18n expanded**: 364 translation keys per language (+42 MCP-related keys).
- **Test suite**: 8 test files with 160+ scenarios (new: `test_mcp_server.py` with 33 scenarios).

---

## [0.0.27] — 2026-07-19

### Added
- **Ollama provider support**: Local AI models via Ollama's OpenAI-compatible API, joining existing Gemini and DeepSeek providers.
- **Multi-language support**: 5 languages — en_us, pt_br, pt_pt, es_es, fr_fr — with automatic OS locale detection and English fallback.
- **Interactive Chat TUI** (`src/ui/chat_app.py`): Textual-based chat interface with branch-persistent memory (`src/chat_memory.py`), slash commands (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patching (F5), diff reload (F2), and session export (F6).
- **Smart Excludes**: Remote pathspec filter (`gitpr.smart-excludes.json`) downloaded from GitHub with versioning (`SMART_EXCLUDES_VERSION`), excluding irrelevant files (lock files, build artifacts, binary assets) from diffs.
- **Pre-save debug flag** (`--pre-save`): Hidden flag that saves the complete AI payload (system instruction + prompt) in JSON before each AI call.
- **Contextual help**: `-h --flag` displays feature-specific documentation with language-aware GitHub links.
- **`--lang` flag**: Force interface language for the current execution without persisting the change.
- **`--provider` flag**: Force AI provider (`gemini`, `deepseek`, `ollama`) for the current execution.
- **Map-reduce for large diffs**: Automatic chunking when diff exceeds ~90k tokens, with safe split at `diff --git` boundaries, rate limiting (`time.sleep(1)`), and progress display.
- **CI/CD integration**: GitHub Actions workflow (`pr-review.yml`) and `action.yml` for external pipeline use.
- **Git Hooks**: `pre-commit` (linter) and `prepare-commit-msg` (AI message generation), installable via `--installhooks`.
- **Multi-language templates**: Skill templates (commit, PR, review, file review, blame, issue, linter) available in 5 languages.
- **Website**: [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)

### Changed
- **Skills organization**: Templates migrated to `.gitpr/skill/` folder with `resolve_skill_path()` auto-migration from legacy root files.
- **Cache**: JSON cache now includes `repo` field for multi-project filtering.
- **Test suite**: 7 test files with 130+ scenarios.
- **Documentation**: 95+ pages across 5 languages (19 topics).

---

## [0.0.26] — 2026-07-18

### Added
- **Core CLI** (`src/main.py`, `src/core.py`): Click-based command routing for PR descriptions, commit messages, and code review using AI (Google Gemini + DeepSeek).
- **AI Providers** (`src/ai_providers.py`): Multi-model architecture with structured JSON output, temperature 0.0, and automatic fallback between providers.
- **Static Linter** (`src/linter_engine.py`): YAML-based regex rules for offline analysis of added lines in git diff.
- **Security** (`src/security.py`): Fernet encryption for API keys at rest.
- **Auto-Updater** (`src/updater.py`): Hot-swap binary updates from GitHub Releases with rollback capability.
- **Issue TUI** (`src/ui/issue_app.py`): Textual-based issue editor with 3 context engines (diff, history, blame), F1 help, F2 save, F3 publish to GitHub.
- **Blame Engine** (`src/blame_engine.py`): Code archaeology with git blame + AI, classifying commits as `ORIGIN` or `REFACTORING`.
- **i18n Engine** (`src/i18n.py`): Laravel-inspired `__()` function with named placeholders.
- **Spinner** (`src/spinner.py`): Animated braille spinner with thinking words during AI calls.
- **Cache** (`src/cache.py`): MD5-based local response cache to avoid redundant AI calls.
- **Skills system** (`--skill`): Downloadable AI system instruction templates from GitHub.

---

For versions prior to 0.0.26, see the [GitHub Releases page](https://github.com/gitpr-cli/gitpr.git/releases).
