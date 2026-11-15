## Completion Report — Etapa 3: `docs/extra/`, `_EN_ONLY` e Índices dos `README*.md`

### What was done
- Moved `docs/github-issue-prompt-com-gh.md` to `docs/extra/github-issue-prompt-com-gh.md`.
- Updated `tests/unit/test_docs_translation_parity.py` to set `_EN_ONLY = {}`, removing `"github-issue-prompt-com-gh"`.
- Updated the Portuguese-only tutorials links in `docs/ARCHITECTURE.md` and its four translations (`docs/ARCHITECTURE.pt_br.md`, `docs/ARCHITECTURE.pt_pt.md`, `docs/ARCHITECTURE.es_es.md`, `docs/ARCHITECTURE.fr_fr.md`) to point to `extra/github-issue-prompt-com-gh.md`, `extra/como_reverter_commit_git_localmente.md`, and `extra/testar_sem_usar_pypi.md`.
- Added the `gitpr mentor [<finding_id>]` entry (with `mentor-mode` doc link) to the Advanced Options and Commands section in `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, and `README.fr_fr.md` (mirroring `README.md`).
- Added localized links with the exact site `?lang=` contract for `gitpr-issue-option`, `guia-regex-gitpr`, `marketplace-publishing-guide`, `otimizacao-de-tokens`, `untracked-files`, `version-markers`, and `mentor-mode` in the `📚` section of all five `README*.md` files.
- Updated `CONTEXT.md` with the canonical glossary terms **Canonical doc** and **Extra doc**.

### Changed files
| File | Change type | Description |
|---|---|---|
| `docs/extra/github-issue-prompt-com-gh.md` | move | Moved from `docs/github-issue-prompt-com-gh.md` |
| `docs/github-issue-prompt-com-gh.md` | delete | Removed from top-level `docs/` |
| `tests/unit/test_docs_translation_parity.py` | test | Emptied `_EN_ONLY = {}` |
| `docs/ARCHITECTURE.md` (and `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) | docs | Updated tutorial links to `extra/` |
| `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md` | docs | Completed `📚` index and `gitpr mentor` command entry |
| `CONTEXT.md` | docs | Added **Canonical doc** and **Extra doc** definitions |

### Impact
- **Functionality:** 100% of top-level `.md` files in `docs/` now have 5-language coverage without `_EN_ONLY` exceptions, and all 5 `README*.md` files index the missing canonical guides with valid `?lang=` parameters.
- **Performance:** None.
- **Compatibility:** No breaking changes; internal links in `docs/ARCHITECTURE*.md` now resolve cleanly to `docs/extra/`.

### Verification
- `python -m pytest tests/test_doc_links.py tests/unit/test_docs_translation_parity.py -v` → **14 passed in 13.44s**.
