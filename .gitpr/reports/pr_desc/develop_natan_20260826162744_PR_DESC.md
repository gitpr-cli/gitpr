# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add 91 i18n keys and refine issue/blame skill loading
```

---

## 🎯 Summary

This change completes the i18n coverage by adding the 91 missing translation keys to all supported languages (pt_br, pt_pt, es, es_es, fr, fr_fr), with AI prompt keys intentionally kept in English. It also introduces developer tooling to audit and maintain i18n keys automatically, and refactors the blame and issue engines to load their skill files more efficiently, avoiding redundant confirmation messages and injecting Smart Excludes metadata into issue context.

## 🛠️ Technical Changes

- Added 91 missing i18n keys to all language files via `scripts_dev/add_i18n_keys.py`.
- Introduced `scripts_dev/i18n_audit.py` to detect missing keys by analyzing `__()` calls in the source code.
- Added `scripts_dev/i18n_missing.json` as a snapshot of currently missing keys.
- Refactored `blame_engine.py` to load the `.gitpr.blame.md` skill once per run and pass it as a parameter, eliminating duplicate "skill loaded" messages in console mode.
- Updated `core.py` `get_skill_context` to support the `blame` action and fixed variable scoping for `nome_arquivo`.
- Modified `issue_engine.py` to use `get_skill_context("issue")` for loading the issue skill and to inject a list of changed documentation files (Smart Excludes) into the system instruction for diff contexts.
- Updated `main.py` HELP_MAP URLs to point to the correct documentation files.
- Added unit tests for blame skill loading and issue engine changes (including Smart Excludes metadata and fallback personas).
- Added example metrics export files (CSV/JSON) for demonstration purposes.

## ⚠️ Impact/Warnings

- **AI prompt keys remain English by design** – they are used directly in prompts sent to AI models and must not be translated.
- **New script `add_i18n_keys.py`** is idempotent and safe to re-run; it skips keys already present.
- **Issue engine now queries changed docs list** – if the function fails, it is caught and ignored, so impact is minimal.
- **Help documentation URLs updated** – ensure the referenced files (`understanding_chat_functionality.md`, `metricas-telemetria.md`) exist in the repository; otherwise, the help links may break.
- **Blame engine refactor** – `get_skill_context` must handle the `blame` action; if not, the default persona is used as fallback.

close #141