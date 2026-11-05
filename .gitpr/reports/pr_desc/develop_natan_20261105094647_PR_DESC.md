# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: map doc links to localized documentation site URLs
```

---

## 🎯 Summary

Centralizes all in-app documentation links on the canonical documentation website and aligns them with the site's `?lang=` query contract. Previously, TUI help modals opened raw GitHub `blob/main` URLs and built locale suffixes ad-hoc, which broke for Spanish and French because the site uses two-letter codes (`es`, `fr`) while the internal locales are `es_es` / `fr_fr`. The refactor also makes `doc_url()` react to runtime language changes and hardens the smart-excludes loaders against corrupted `.env` files or unreadable paths so a bad local file can never crash a diff/lint run.

## 🛠️ Technical Changes

- Add `DOC_LANG_PARAMS` mapping internal locale codes to the documentation site's query contract (`es_es`→`es`, `fr_fr`→`fr`, `pt_br`/`pt_pt` unchanged) and `KNOWN_LOCALE_SUFFIXES` for suffix stripping.
- Refactor `doc_url()` to read `src.i18n.CURRENT_LANG` at call time (module import instead of frozen symbol) so `set_lang()` propagates to generated links, and to strip `.md` plus accidental locale suffixes from filenames.
- Replace hardcoded GitHub `blob/main` URLs in `HelpScreen` and `ChatHelpScreen` with `doc_url(...)` calls pointing to the canonical docs site.
- Harden `src/core.py`: wrap `load_dotenv()` in try/except, guard `Path.exists()`/`open()` for global and local exclude files, and restructure `data` initialization so failures fall through to the offline fallback.
- Add `tests/test_doc_links.py` covering the language query contract, dynamic language switching via `set_lang`, TUI modal URL wiring, README `?lang=es`/`?lang=fr` invariants, and 5-language parity of every doc referenced by `CATEGORIES`.
- Add ES/FR version-marker docs and supporting reports/plans for the docs-links work.

## ⚠️ Impact/Warnings

- No database, dependency, or environment-variable schema changes.
- `load_dotenv()` failures are now silently swallowed; misconfigured `~/.gitpr/.env` files will no longer surface an error, so configuration issues may be harder to diagnose.
- Links now depend on the docs site honoring the `?lang=` contract; the GitHub repository fallback URLs are removed.
- New test invariant requires all 5 language variants of every `CATEGORIES` doc (including `version-markers.md`) to exist and be non-empty in `docs/`, so adding a category without translations will fail CI.

close #273

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)