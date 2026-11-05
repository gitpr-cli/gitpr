## Completion Report — ES/FR Documentation Site Links, CLI `doc_url()` Contract & 5-Language Docs Parity

### What was done
- Recorded the canonical **Documentation link** domain concept in `CONTEXT.md`.
- Aligned `src/doc_links.py::doc_url()` with the documentation website's language query parameter contract (`?lang=pt_br`, `?lang=pt_pt`, `?lang=es`, `?lang=fr`, and no query string for English), matching `README.es_es.md`, `README.fr_fr.md`, and `HOOK_SCRIPT_SUFFIXES`.
- Fixed `src/doc_links.py::doc_url()` to read `src.i18n.CURRENT_LANG` dynamically at call time so runtime language overrides (`--lang`) take effect immediately.
- Migrated the last two TUI help modals (`HelpScreen` in `src/ui/help_screen.py` and `ChatHelpScreen` in `src/ui/chat_app.py`) from legacy `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/...` URLs to `doc_url()`.
- Updated stale version references in `docs/version-markers.md` (`1.5.0`, `v0.0.39`, `v0.0.4`) and created the 4 missing localized translations (`docs/version-markers.pt_br.md`, `docs/version-markers.pt_pt.md`, `docs/version-markers.es_es.md`, `docs/version-markers.fr_fr.md`), achieving 100% 5-language parity across all 49 canonical documentation pages in `docs/`.
- Added unit test suite `tests/test_doc_links.py` and verified all 72 tests across `test_doc_links.py`, `test_cli_help.py`, and `test_config_schema.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `CONTEXT.md` | docs | Added **Documentation link** domain glossary entry |
| `src/doc_links.py` | fix | Mapped `es_es -> es` and `fr_fr -> fr` via `DOC_LANG_PARAMS` and resolved `i18n.CURRENT_LANG` dynamically at call time |
| `src/ui/help_screen.py` | refactor | Replaced raw GitHub doc URL with `doc_url("issue-tui-help.md")` |
| `src/ui/chat_app.py` | refactor | Replaced raw GitHub doc URL in `ChatHelpScreen` with `doc_url("understanding_chat_functionality.md")` |
| `docs/version-markers.md` | docs | Updated version examples to `1.5.0`, `v0.0.39`, and `v0.0.4` |
| `docs/version-markers.pt_br.md` | docs | Added Brazilian Portuguese translation of `version-markers.md` |
| `docs/version-markers.pt_pt.md` | docs | Added European Portuguese translation of `version-markers.md` |
| `docs/version-markers.es_es.md` | docs | Added Spanish translation of `version-markers.md` |
| `docs/version-markers.fr_fr.md` | docs | Added French translation of `version-markers.md` |
| `tests/test_doc_links.py` | test | Added unit tests for `doc_url()`, TUI help modal URLs, README ES/FR link invariants, and 5-language docs parity |
| `docs/survey/20261105_es_fr_site_docs_links_surveyfacts.md` | docs | Saved session survey facts |
| `docs/plans/develop_natan/20261105_es_fr_site_docs_links_plansfacts.md` | docs | Saved session plan |
| `docs/gemini/plans/develop_natan/2026-11-05_develop_natan_es_fr_site_docs_links.md` | docs | Saved Gemini implementation plan |
| `docs/gemini/walkthrough/develop_natan/2026-11-05_es_fr_site_docs_links.md` | docs | Saved Gemini walkthrough |

### Impact
- **Functionality:** CLI contextual help (`gitpr -h ...`), Config TUI (`gitpr config`), and TUI help modals (`HelpScreen`, `ChatHelpScreen`, `PRPublishHelpScreen`, `LinterApp`, `MetricsApp`) now emit `?lang=es` and `?lang=fr` for Spanish and French and honor `--lang` overrides dynamically. All 49 canonical documentation pages in `docs/` now have full 5-language coverage.
- **Performance:** Zero performance impact (`doc_url()` remains an in-memory string builder).
- **Compatibility:** Fully backward-compatible; existing English, Brazilian Portuguese, and European Portuguese URLs are unchanged.

### Next steps (if applicable)
- When deploying the external documentation site (`gitpr.natanfiuza.dev.br`), sync the `docs/*.es_es.md` and `docs/*.fr_fr.md` files (including the new `docs/version-markers.*` translations) so the site serves localized Spanish and French content under `?lang=es` and `?lang=fr`.
