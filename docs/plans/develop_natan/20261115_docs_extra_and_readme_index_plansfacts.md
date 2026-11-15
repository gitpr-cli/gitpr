# Plano de Execução — Etapa 3: `docs/extra/`, `_EN_ONLY` e Índices dos `README*.md`

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Referência:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (L102–L125)

## Objetivo

Alcançar cobertura 100% em 5 idiomas na raiz de `docs/` movendo `docs/github-issue-prompt-com-gh.md` para `docs/extra/`, zerando `_EN_ONLY`, corrigindo referências em `docs/ARCHITECTURE*.md` e completando os índices dos cinco `README*.md`.

## Passos de Execução

1. **Mover documento avulso e atualizar referências (`docs/`):**
   - Mover `docs/github-issue-prompt-com-gh.md` para `docs/extra/github-issue-prompt-com-gh.md`.
   - Em `docs/ARCHITECTURE.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md` e `.fr_fr.md`, atualizar os 3 links da subseção de tutoriais para `extra/github-issue-prompt-com-gh.md`, `extra/como_reverter_commit_git_localmente.md` e `extra/testar_sem_usar_pypi.md`.
2. **Zerar `_EN_ONLY` nos testes:**
   - Em `tests/unit/test_docs_translation_parity.py` (L14–L16), alterar `_EN_ONLY` para `{}`.
3. **Completar os 5 `README*.md`:**
   - Em `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md` e `README.fr_fr.md`, adicionar o bullet `gitpr mentor [<finding_id>]` na seção de opções/comandos avançados (espelhando `README.md` L147) com o `?lang=` correto.
   - Na seção `📚` dos 5 `README*.md`, adicionar links traduzidos (com `?lang=` correto) para:
     - **Core Features:** `gitpr-issue-option`, `untracked-files`, `mentor-mode`
     - **DevOps & CI/CD:** `guia-regex-gitpr`
     - **Configuration & Infrastructure:** `marketplace-publishing-guide`, `otimizacao-de-tokens`, `version-markers`
4. **Verificação:**
   - Executar `python -m pytest tests/test_doc_links.py tests/unit/test_docs_translation_parity.py -v`.
   - Gerar relatório de conclusão em `docs/gemini/reports/develop_natan/2026-11-15_docs_extra_and_readme_index.md`.
