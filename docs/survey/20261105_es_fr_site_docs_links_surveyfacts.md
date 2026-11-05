# Survey — ES/FR Documentation Site Links, CLI `doc_url()` Contract & 5-Language Docs Parity

**Date:** 2026-11-05
**Branch:** `develop_natan`
**Task:** `es_fr_site_docs_links`

---

## 1. Context & Problem Statement

In status report `docs/reports/relatorio_estado_v0.0.19.md` (and subsequent reports up to `v0.0.22.md`), the backlog item was recorded as:

> **🆕 Acompanhar o fallback ES/FR no site:** os links dos READMEs já levam `?lang=es_es` e `?lang=fr_fr`, mas o site ainda serve inglês para esses dois idiomas. Publicar as traduções torna os links corretos sem tocar nos READMEs.

A codebase audit revealed the following factual state across the repository:

1. **Root `README.es_es.md` and `README.fr_fr.md`:**
   - In v0.0.19 (`2026-10-27_readme_docs_site_links`), the 5 root READMEs were migrated from `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/*.md` to `https://gitpr.natanfiuza.dev.br/docs/*`. Initially, `README.es_es.md` and `README.fr_fr.md` used `?lang=es_es` and `?lang=fr_fr`.
   - In v0.0.20 (PR #226, commit `68df9ae`), `README.es_es.md` (75 links) and `README.fr_fr.md` (74 links) were updated to `?lang=es` and `?lang=fr` ("o formato que o site realmente serve").

2. **CLI & TUI `doc_url()` Discrepancy (`src/doc_links.py`):**
   - `src/doc_links.py` is the canonical builder for all CLI help links (`src/core.py::get_doc_url`), `gitpr config` category documentation links (`src/config_schema.py`), and TUI help modals (`src/ui/pr_publish_help.py`, `src/ui/linter_app.py`, `src/ui/metrics_app.py`).
   - However, `src/doc_links.py` had two bugs:
     1. **Language query parameter mismatch:** It emitted `?lang={CURRENT_LANG}` verbatim (`?lang=es_es` and `?lang=fr_fr`), diverging from the documentation site's contract (`?lang=es` and `?lang=fr`) and from `HOOK_SCRIPT_SUFFIXES` in `src/core.py` (`{"pt_br": "pt_br", "pt_pt": "pt_pt", "es_es": "es", "fr_fr": "fr"}`).
     2. **Frozen module-level import:** `from src.i18n import CURRENT_LANG` imported `CURRENT_LANG` by value at import time. When `i18n.set_lang()` ran later (e.g., via `gitpr --lang es_es -h -c`), `src.doc_links.CURRENT_LANG` remained frozen at the startup locale.

3. **Remaining Raw GitHub URLs in TUI Help Screens:**
   - `src/ui/help_screen.py` (`HelpScreen.compose`, lines 27–28) still constructed `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/issue-tui-help{lang_suffix}.md`.
   - `src/ui/chat_app.py` (`ChatHelpScreen.on_button_pressed`, lines 92–94) still constructed `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/understanding_chat_functionality{lang_suffix}.md`.

4. **5-Language Documentation Coverage in `docs/` (`docs/version-markers.md`):**
   - Out of 49 canonical GitPR documentation topics in `docs/` (45 top-level + 4 under `docs/tutorial/`), 48 already had all 5 language variants (`.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`).
   - `docs/version-markers.md` — which is linked directly from `src/config_schema.py` (`Category("advanced", ..., doc="version-markers.md")`) — existed only in English (`docs/version-markers.md`) and still referenced stale version numbers (`v0.0.39` / `v0.0.4`).
   - Note: `docs/github-issue-prompt-com-gh.md` was inspected and confirmed to be an internal developer cheat-sheet for `gh issue edit`, not a public GitPR documentation page.

---

## 2. Decisions Confirmed in Grilling Session

| # | Decision Topic | Chosen Option |
|---|---|---|
| **Q1** | Site Language Query Parameter Contract | Align `src/doc_links.py::doc_url()` with the documentation site (`?lang=pt_br`, `?lang=pt_pt`, `?lang=es`, `?lang=fr`; no query string for `en*`), matching `README.es_es.md`, `README.fr_fr.md`, and `HOOK_SCRIPT_SUFFIXES`. |
| **Q2** | Repository Scope & Missing Translations | Keep everything inside this repository: update `src/doc_links.py`, update `docs/version-markers.md` to current `1.5.0` examples, and create its 4 localized translations (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) to reach 100% 5-language coverage across all 49 canonical docs. Leave `docs/github-issue-prompt-com-gh.md` untouched. |
| **Q3** | Dynamic `CURRENT_LANG` & TUI Help Modals | Read `src.i18n.CURRENT_LANG` dynamically at call time inside `doc_url()`, and migrate `src/ui/help_screen.py` and `src/ui/chat_app.py` from legacy `github.com/.../blob/main/docs/...` URLs to `doc_url()`. |
| **Q4** | Domain Glossary (`CONTEXT.md`) | Record **Documentation link** in `CONTEXT.md` as the canonical domain term for public documentation URLs. |

---

## 3. Inventory of Affected Files

| File | Role | Planned Action |
|---|---|---|
| `CONTEXT.md` | Domain glossary | Add **Documentation link** term definition |
| `src/doc_links.py` | Canonical documentation URL builder | Read `src.i18n.CURRENT_LANG` dynamically; map `es_es -> es` and `fr_fr -> fr` via `DOC_LANG_PARAMS`; strip `.md` and any locale suffix cleanly |
| `src/ui/help_screen.py` | Issue TUI F1 Help modal | Replace raw GitHub URL with `doc_url("issue-tui-help.md")` |
| `src/ui/chat_app.py` | Chat TUI F1 Help modal (`ChatHelpScreen`) | Replace raw GitHub URL with `doc_url("understanding_chat_functionality.md")` |
| `docs/version-markers.md` | English documentation for version markers | Update stale version examples (`v0.0.39` -> `1.5.0`) |
| `docs/version-markers.pt_br.md` | Brazilian Portuguese translation | Create with full structural parity |
| `docs/version-markers.pt_pt.md` | European Portuguese translation | Create with full structural parity |
| `docs/version-markers.es_es.md` | Spanish translation | Create with full structural parity |
| `docs/version-markers.fr_fr.md` | French translation | Create with full structural parity |
| `tests/test_doc_links.py` | Unit test suite | Verify `doc_url()` across all locales, dynamic `set_lang()`, TUI help modal URLs, README link invariants, and 5-language parity of `docs/version-markers*.md` |
