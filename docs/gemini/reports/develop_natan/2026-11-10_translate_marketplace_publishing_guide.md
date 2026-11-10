## Completion Report — Tradução do Marketplace Publishing Guide

### What was done
- Translated `docs/marketplace-publishing-guide.md` into 4 additional supported languages:
  - `docs/marketplace-publishing-guide.pt_br.md` (Português do Brasil)
  - `docs/marketplace-publishing-guide.pt_pt.md` (Português de Portugal)
  - `docs/marketplace-publishing-guide.es_es.md` (Español)
  - `docs/marketplace-publishing-guide.fr_fr.md` (Français)
- Preserved 100% structural parity, code snippets, bash commands, technical identifiers, secrets (`VSCE_PAT`, `OVSX_PAT`), tags (`ext-v*`), and cloud portal scope labels (`Acquire`, `Manage`).
- Updated relative links in `docs/editor-extension.*.md` for PT-BR, PT-PT, ES, and FR to point directly to their localized marketplace publishing guides.
- Created automated test suite `tests/unit/test_marketplace_publishing_guide_docs_parity.py` with 4 tests verifying existence, section parity, token preservation, and cross-reference links.
- Promoted documentation coverage from 50 to 51 topics with 100% 5-language coverage (leaving only 1 partial topic: `github-issue-prompt-com-gh.md`).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/marketplace-publishing-guide.pt_br.md` | docs | Brazilian Portuguese translation of marketplace publishing guide |
| `docs/marketplace-publishing-guide.pt_pt.md` | docs | European Portuguese translation of marketplace publishing guide |
| `docs/marketplace-publishing-guide.es_es.md` | docs | Spanish translation of marketplace publishing guide |
| `docs/marketplace-publishing-guide.fr_fr.md` | docs | French translation of marketplace publishing guide |
| `docs/editor-extension.pt_br.md` | docs | Updated cross-link to `marketplace-publishing-guide.pt_br.md` |
| `docs/editor-extension.pt_pt.md` | docs | Updated cross-link to `marketplace-publishing-guide.pt_pt.md` |
| `docs/editor-extension.es_es.md` | docs | Updated cross-link to `marketplace-publishing-guide.es_es.md` |
| `docs/editor-extension.fr_fr.md` | docs | Updated cross-link to `marketplace-publishing-guide.fr_fr.md` |
| `tests/unit/test_marketplace_publishing_guide_docs_parity.py` | test | Unit tests verifying documentation parity and cross-links across all 5 languages |
| `docs/plans/develop_natan/20261110_translate_marketplace_publishing_guide_plansfacts.md` | docs | Execution plan facts artifact from grill session |
| `docs/survey/20261110_translate_marketplace_publishing_guide_surveyfacts.md` | docs | Survey facts artifact from grill session |
| `docs/gemini/plans/develop_natan/2026-11-10_develop_natan_translate_marketplace_publishing_guide.md` | docs | Implementation plan artifact |

### Impact
- **Functionality:** Users consulting documentation in Portuguese (BR/PT), Spanish, and French can now access the full step-by-step publisher setup and marketplace release guide in their native language.
- **Performance:** Zero runtime overhead; all operations are documentation and automated unit tests.
- **Compatibility:** Fully compatible; adheres to existing GitPR documentation naming conventions (`.<locale>.md`) and relative link structures.

### Next steps (if applicable)
- In the next release status report, promote `marketplace-publishing-guide` to 100% 5-language coverage in the documentation inventory.
