# Implementation Plan — Etapa 3: `docs/extra/`, `_EN_ONLY`, and `README*.md` Indexes

## Goal Description

Reach 100% 5-language parity coverage for all top-level documents in `docs/` by moving the standalone Portuguese how-to `docs/github-issue-prompt-com-gh.md` into `docs/extra/`, emptying `_EN_ONLY` in `tests/unit/test_docs_translation_parity.py`, fixing tutorial links in `docs/ARCHITECTURE*.md`, and completing the documentation indexes across all five `README*.md` files (`README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md`).

## Proposed Changes

### Documentation & Extra How-Tos

#### [MOVE] `docs/github-issue-prompt-com-gh.md` → `docs/extra/github-issue-prompt-com-gh.md`
Move the standalone Portuguese `gh` CLI issue formatting guide out of the top-level `docs/` root into `docs/extra/`.

#### [MODIFY] `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE.pt_br.md`, `docs/ARCHITECTURE.pt_pt.md`, `docs/ARCHITECTURE.es_es.md`, `docs/ARCHITECTURE.fr_fr.md`
Update the three tutorial links in the "Tutorials (Portuguese only)" section so they resolve to `extra/`:
- `[github-issue-prompt-com-gh.md](extra/github-issue-prompt-com-gh.md)`
- `[como_reverter_commit_git_localmente.md](extra/como_reverter_commit_git_localmente.md)`
- `[testar_sem_usar_pypi.md](extra/testar_sem_usar_pypi.md)`

---

### Tests

#### [MODIFY] `tests/unit/test_docs_translation_parity.py`
Remove `"github-issue-prompt-com-gh"` from `_EN_ONLY`, leaving `_EN_ONLY = {}`.

---

### README Documentation Indexes

#### [MODIFY] `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md`
1. **Advanced Options and Commands** (only in `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md`, as `README.md` already has it at line 147):
   Add the localized `gitpr mentor [<finding_id>]` bullet linking to `https://gitpr.natanfiuza.dev.br/docs/mentor-mode` with the appropriate `?lang=` query parameter.
2. **`📚` Technical Documentation and Advanced Guides** (all 5 `README*.md` files):
   Add localized entries with faithful descriptions and the exact `?lang=` query contract (none for `README.md`, `?lang=pt_br`, `?lang=pt_pt`, `?lang=es`, `?lang=fr`):
   - **Core Features**: `gitpr-issue-option`, `untracked-files`, `mentor-mode`
   - **DevOps & CI/CD**: `guia-regex-gitpr`
   - **Configuration & Infrastructure**: `marketplace-publishing-guide`, `otimizacao-de-tokens`, `version-markers`

## Verification Plan

### Automated Tests
```bash
python -m pytest tests/test_doc_links.py tests/unit/test_docs_translation_parity.py -v
```
