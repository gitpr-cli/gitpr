# Walkthrough — Etapa 3: `docs/extra/`, `_EN_ONLY` e Índices dos `README*.md`

## Changes Made
1. **Relocated standalone how-to:** Moved `docs/github-issue-prompt-com-gh.md` to `docs/extra/github-issue-prompt-com-gh.md` and updated tutorial links across all 5 `docs/ARCHITECTURE*.md` files (`extra/github-issue-prompt-com-gh.md`, `extra/como_reverter_commit_git_localmente.md`, `extra/testar_sem_usar_pypi.md`).
2. **Removed `_EN_ONLY` exception:** Updated `tests/unit/test_docs_translation_parity.py` so `_EN_ONLY = {}`.
3. **Completed `README*.md` indexes:** Added localized descriptions and `?lang=`-compliant links for `gitpr-issue-option`, `guia-regex-gitpr`, `marketplace-publishing-guide`, `otimizacao-de-tokens`, `untracked-files`, `version-markers`, and `mentor-mode` across `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, and `README.fr_fr.md` (including `gitpr mentor` in the command list of the 4 translated READMEs).
4. **Domain glossary:** Added **Canonical doc** and **Extra doc** to `CONTEXT.md`.

## Validation Results
Ran:
```bash
python -m pytest tests/test_doc_links.py tests/unit/test_docs_translation_parity.py -v
```
Result: **14 passed in 13.44s**.
