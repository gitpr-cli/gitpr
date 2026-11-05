# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add seed command to bootstrap project-local configuration
```

---

## 🎯 Summary

Introduces a dedicated, discoverable way to bootstrap repository-local configuration. Previously, project configuration (PR base branch, Smart Excludes, local linter rules) was created implicitly as a side effect of the root callback and skill downloads. This change promotes it to a first-class operation via a new `gitpr seed` subcommand and `--seed` flag, and reworks the install wizard into a 5-step flow that starts with an explicit project-local configuration step. The goal is to give teams a repeatable, idempotent, and safe command to seed the files needed for consistent PR automation and linting—without ever destroying user edits unless explicitly forced.

## 🛠️ Technical Changes

- Add `seed_project_configuration()` in `src/core.py` that seeds `.gitpr/conf/gitpr.config.yml`, `.gitpr/conf/gitpr.smart-excludes.json`, and `.gitpr/skill/.gitpr.linter.yml`, returning a structured summary (`config`, `smart_excludes`, `linter`, `skills_downloaded`).
- Add `gitpr seed` subcommand with `--force/-f` (overwrite existing templates) and `--all/-a` (also download all AI prompt skill templates) plus a global `-sd/--seed` flag; both emit command metrics.
- Extend `_seed_local_smart_excludes()` to accept `force` and return a result dict (`created`, `path`, `already_existed`, `error`) instead of silently swallowing failures.
- Extend `ensure_project_config()` and `download_skill_file()` with a `force` parameter to support intentional overwrites while preserving default no-clobber behavior.
- Auto-seed smart-excludes as part of `generate_skill_template()` for backward compatibility.
- Rework `run_install_wizard()` into 5 steps: **1)** Project Local Configuration (new, confirmable), **2)** Skill Templates (with optional external linter bridge setup via `run_linter_setup_wizard`), **3)** Git Hooks, **4)** MCP Configuration, **5)** API Key. Skipping is now explicit.
- Make `.env` loading resilient: wrap `load_dotenv` calls in `src/i18n.py` and `src/spinner.py` in `try/except` so a missing or unwritable `.env` never breaks startup.
- Update `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt` dictionaries: add new strings, renumber wizard steps 4→5, relocate out-of-order keys to alphabetical position, and remove obsolete `Could not create the project configuration` message.
- Bump language dictionary asset version to `v0.0.40`.
- Add `tests/test_seed_command.py` covering file creation, idempotency, force overwrite, `--all`, and CLI/flag behaviors; patch `run_linter_setup_wizard` in existing wizard tests.

## ⚠️ Impact/Warnings

- **CLI surface (additive):** new `gitpr seed` command and `--seed` flag; existing flags unaffected.
- **Behavior change:** the install wizard now begins with an explicit project-local configuration prompt (Step 1 of 5) and prompts for optional external linter bridge setup. Step numbering changed, which may affect docs/screenshots referencing the old 4-step flow.
- **Filesystem:** `seed` writes into `.gitpr/conf/` and `.gitpr/skill/`. Default behavior never overwrites existing files; `--force` will replace them with default templates.
- **Environment:** `.env` loading is now best-effort and non-fatal; errors are silently ignored (previously would raise).
- **i18n asset:** language dictionary version bumped (`v0.0.39` → `v0.0.40`); translations must ship alongside this change to keep keys in sync.
- **No database changes or new third-party runtime dependencies.**

close #277

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_4_warnings-yellow)](https://gitpr.natanfiuza.dev.br/)