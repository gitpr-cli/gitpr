# Implementation Plan — ES/FR Documentation Site Links, CLI `doc_url()` Contract & 5-Language Docs Parity

**Date:** 2026-11-05
**Branch:** `develop_natan`
**Plan Name:** `es_fr_site_docs_links`

---

## 1. Goal Description

Ensure complete consistency between GitPR's documentation links and the public documentation site (`https://gitpr.natanfiuza.dev.br/docs/<slug>`), especially for Spanish (`?lang=es`) and French (`?lang=fr`):

1. **Align `src/doc_links.py::doc_url()` with the site's language parameter contract:** Map internal locale codes `es_es -> es` and `fr_fr -> fr` (while keeping `pt_br -> pt_br`, `pt_pt -> pt_pt`, and omitting `?lang=` for `en*`), and resolve `src.i18n.CURRENT_LANG` dynamically at call time so `--lang` overrides work across CLI help and TUIs.
2. **Migrate remaining TUI Help modals off raw GitHub URLs:** Update `src/ui/help_screen.py` (`HelpScreen`) and `src/ui/chat_app.py` (`ChatHelpScreen`) to use `doc_url()` instead of `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/...`.
3. **Complete 5-language coverage in `docs/`:** Update stale version references in `docs/version-markers.md` (referenced by `src/config_schema.py` category `"advanced"`) and create `docs/version-markers.pt_br.md`, `docs/version-markers.pt_pt.md`, `docs/version-markers.es_es.md`, and `docs/version-markers.fr_fr.md` so all 49 canonical documentation pages in `docs/` have 100% 5-language parity.
4. **Domain Glossary (`CONTEXT.md`):** Add the canonical term **Documentation link**.

---

## 2. Proposed Changes

### Domain Model
#### [MODIFY] [CONTEXT.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CONTEXT.md)
- Add **Documentation link** entry to the domain glossary.

---

### CLI & TUI Documentation Links
#### [MODIFY] [doc_links.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/doc_links.py)
- Define `DOC_LANG_PARAMS = {"pt_br": "pt_br", "pt_pt": "pt_pt", "es_es": "es", "es": "es", "fr_fr": "fr", "fr": "fr"}`.
- Read `src.i18n.CURRENT_LANG` dynamically inside `doc_url(filename)` so runtime `i18n.set_lang()` calls are reflected.
- Strip `.md` (and any locale suffix if present) and append `?lang=<site_code>` for non-English languages.

#### [MODIFY] [help_screen.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/ui/help_screen.py)
- Replace hardcoded `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/issue-tui-help{lang_suffix}.md` with `doc_url("issue-tui-help.md")`.

#### [MODIFY] [chat_app.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/ui/chat_app.py)
- In `ChatHelpScreen.on_button_pressed`, replace hardcoded `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/understanding_chat_functionality{lang_suffix}.md` with `doc_url("understanding_chat_functionality.md")`.

---

### Documentation Translations (`docs/version-markers*.md`)
#### [MODIFY] [version-markers.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/version-markers.md)
- Refresh version examples (`v0.0.39` -> `1.5.0`) to match current `src/updater.py` SSOT.

#### [NEW] [version-markers.pt_br.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/version-markers.pt_br.md)
- Brazilian Portuguese translation of `docs/version-markers.md`.

#### [NEW] [version-markers.pt_pt.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/version-markers.pt_pt.md)
- European Portuguese translation of `docs/version-markers.md`.

#### [NEW] [version-markers.es_es.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/version-markers.es_es.md)
- Spanish translation of `docs/version-markers.md`.

#### [NEW] [version-markers.fr_fr.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/version-markers.fr_fr.md)
- French translation of `docs/version-markers.md`.

---

### Tests
#### [NEW] [test_doc_links.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/test_doc_links.py)
- Unit tests for `doc_url()` across all 5 supported languages (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`), dynamic `i18n.set_lang()` updates, TUI help modal URLs (`HelpScreen`, `ChatHelpScreen`), README link invariants, and 5-language existence/parity for `docs/version-markers*.md`.

---

## 3. Verification Plan

1. Run `pytest tests/test_doc_links.py tests/test_cli_help.py tests/test_config_schema.py -v`.
2. Run full test suite (`pytest`) to confirm zero regressions.
