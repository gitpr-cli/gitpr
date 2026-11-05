# Plan — ES/FR Documentation Site Links, CLI `doc_url()` Contract & 5-Language Docs Parity

**Date:** 2026-11-05
**Branch:** `develop_natan`
**Task:** `es_fr_site_docs_links`

---

## 1. Objective

Complete the alignment of GitPR's documentation links and localized markdown sources for Spanish (`es_es` -> `?lang=es`) and French (`fr_fr` -> `?lang=fr`), ensuring that:
1. Every documentation link emitted by the CLI (`gitpr -h ...`), Config TUI (`gitpr config`), and Help modals (`HelpScreen`, `ChatHelpScreen`, `PRPublishHelpScreen`, `LinterApp`, `MetricsApp`) uses the canonical site URL format (`https://gitpr.natanfiuza.dev.br/docs/<slug>` with `?lang=pt_br|pt_pt|es|fr` and no query parameter for English).
2. `doc_url()` resolves the active language dynamically at call time so `--lang` overrides work everywhere.
3. All 49 canonical documentation pages in `docs/` have complete 5-language coverage (`.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) by translating `docs/version-markers.md`.

---

## 2. Planned Changes

### Step 1: Domain Model (`CONTEXT.md`)
- Add **Documentation link** to `CONTEXT.md` defining the public documentation URL contract (`https://gitpr.natanfiuza.dev.br/docs/<slug>`, no `.md` extension, no query parameter for English, and `?lang=pt_br`, `?lang=pt_pt`, `?lang=es`, or `?lang=fr` for localized languages).

### Step 2: Canonical Documentation URL Builder (`src/doc_links.py`)
- Define `DOC_LANG_PARAMS`:
  ```python
  DOC_LANG_PARAMS = {
      "pt_br": "pt_br",
      "pt_pt": "pt_pt",
      "es_es": "es",
      "es": "es",
      "fr_fr": "fr",
      "fr": "fr",
  }
  ```
- Update `doc_url(filename: str) -> str`:
  - Read `src.i18n.CURRENT_LANG` dynamically at call time (avoiding the frozen module-level string binding).
  - Strip `.md` (and any accidental locale suffix like `.pt_br.md` if passed) to extract the clean slug.
  - Omit `?lang=` when the active language starts with `"en"`.
  - Append `?lang={DOC_LANG_PARAMS.get(lang, lang)}` for non-English locales.

### Step 3: Migrate Remaining TUI Help Modals (`src/ui/help_screen.py` & `src/ui/chat_app.py`)
- **`src/ui/help_screen.py`**:
  - Import `doc_url` from `src.doc_links` (removing unused `CURRENT_LANG` import).
  - Replace the hardcoded `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/issue-tui-help{lang_suffix}.md` URL with `doc_url("issue-tui-help.md")`.
- **`src/ui/chat_app.py`**:
  - In `ChatHelpScreen.on_button_pressed`, replace the hardcoded `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/understanding_chat_functionality{lang_suffix}.md` URL with `doc_url("understanding_chat_functionality.md")`.

### Step 4: Complete 5-Language Coverage for `docs/version-markers.md`
- Update `docs/version-markers.md` so examples reflect the current `1.5.0` package version and `src/updater.py` markers.
- Create localized translations with identical heading/table structure:
  - `docs/version-markers.pt_br.md` (Portuguese — Brazil)
  - `docs/version-markers.pt_pt.md` (Portuguese — Portugal)
  - `docs/version-markers.es_es.md` (Spanish — Spain)
  - `docs/version-markers.fr_fr.md` (French — France)

### Step 5: Automated Tests (`tests/test_doc_links.py`)
- Add unit tests verifying:
  - `doc_url()` output for `en_us`, `pt_br`, `pt_pt`, `es_es` (`?lang=es`), and `fr_fr` (`?lang=fr`).
  - Dynamic language switching via `i18n.set_lang()`.
  - `HelpScreen` and `ChatHelpScreen` use `doc_url()` and no longer reference `github.com/.../blob/main/docs/`.
  - `README.es_es.md` and `README.fr_fr.md` contain zero `?lang=es_es` / `?lang=fr_fr` links and use `?lang=es` / `?lang=fr`.
  - All 5 language variants of `docs/version-markers*.md` exist and are non-empty.

---

## 3. Verification Plan
- Run `pytest tests/test_doc_links.py tests/test_cli_help.py tests/test_config_schema.py -v`.
- Run the full test suite (`pytest`) to ensure zero regressions.
