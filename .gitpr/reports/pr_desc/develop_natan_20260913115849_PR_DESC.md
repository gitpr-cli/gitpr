# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add config TUI, skill registry and usage log
```

---

## 🎯 Summary

Introduce an interactive `gitpr config` TUI that lets users browse, validate and edit every key in `~/.gitpr/.env` without hand-editing files, along with a declarative schema, a skill-file registry, forced re-download support and per-command usage logging. The change also fixes long-standing hook language handling (user choice vs. on-disk state) and syncs the five language packs with ~200 new translation keys for the new configuration and release surfaces.

## 🛠️ Technical Changes

- **New config TUI**: Added a Textual master-detail app (`src/ui/config_app.py`) with sidebar navigation, search, F2 save, Ctrl+R restore-default, per-field downloads with force re-fetch, inline validation and a Skills pane that edits `.gitpr/skill/*.md` atomically (preserving CRLF/LF).
- **Declarative schema**: Added `src/config_schema.py` describing every editable `.env` key — categories, widget kinds (bool/int/str/enum/template/path/secret/version/words), `show_if` gating per AI provider and SCM forge, validators, version markers and download actions.
- **Skill registry + `.env` helpers in `src/config.py`**: `SKILL_FILES_BY_TYPE`, `skill_file_for`, `skill_file_path`, `skill_file_status`, `read_skill_file`, `write_skill_file` (shared with `get_skill_context()`), plus `read_env_file_values`, `save_config_values`, `remove_config_value` and `validate_ai_key()` probing Gemini/DeepSeek SDKs with short timeouts and distinguishing auth failures from network errors.
- **Forced re-downloads**: Threaded a `force=` flag through `_load_smart_excludes`, `get_translations`, `load_linter_presets` and `_load_thinking_words`/`reload_thinking_words`.
- **Lightweight links module**: Moved `doc_url()` to `src/doc_links.py` so the UI avoids importing `core`/AI SDKs.
- **Hook language fix**: Added `HOOK_SCRIPT_SUFFIXES` mapping interface codes (`es_es`, `fr_fr`) to published file suffixes (`.es`, `.fr`), separated `SCRIPTS_LANG` (user choice) from `SCRIPTS_INSTALLED_LANG` (on-disk state) so auto-sync detects language changes, added `effective_hook_lang()` and stopped ignoring `--lang`.
- **Usage log**: Added `src/usage_log.py` writing one synchronous, never-printing line per command to a daily `~/.gitpr/logs` file, invoked from the root CLI callback and the MCP server entry point, gated by `GITPR_SHOW_LOGS` (disabled in tests).
- **CLI wiring**: Registered the `config` subcommand in `src/main.py` without calling `setup_environment()` to avoid fighting the TUI for the terminal; bumped `__lang_version__` to `v0.0.24`.
- **i18n sync**: Renamed the `Detected language: {lang}` key to `Hooks language: {lang}` and added ~200 new keys across `es.json`, `es_es.json`, `fr.json`, `fr_fr.json`, `pt_br.json` and `pt_pt.json`, covering config TUI and release workflow surfaces; release-related keys were moved into alphabetical order and deduplicated.
- **Telemetry artifacts**: Committed metric exports under `.gitpr/metrics/export/` for 2026-09-12 and 2026-09-13 (CSV/JSON, shared schema).
- **Tests**: Added coverage for the TUI, CLI wiring, schema/`DEFAULT_CONFIG` sync, `.env` round-trips, validators, hook language resolution, skill registry agreement, forced downloads and the usage log.

## ⚠️ Impact/Warnings

- No database changes.
- Dependency changes: the config TUI relies on Textual (already part of the stack) and the AI key validation probes the Gemini/DeepSeek SDKs.
- Environment variable: new `GITPR_SHOW_LOGS` gates usage logging (default enabled; disabled in `tests/conftest.py`).
- i18n drift risk: other locales must be updated with the same key set to stay in sync with the renamed hook-language key and new config surfaces.
- Behavior change: `--lang` is no longer ignored when resolving hook scripts.

close #162