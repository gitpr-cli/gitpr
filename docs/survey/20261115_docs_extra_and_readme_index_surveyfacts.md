# Survey Facts — Etapa 3: `docs/extra/`, `_EN_ONLY` e Índices dos `README*.md`

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Origem:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (L102–L125)

## Contexto da Tarefa

Mover o how-to avulso `docs/github-issue-prompt-com-gh.md` para `docs/extra/github-issue-prompt-com-gh.md`, zerar `_EN_ONLY` em `tests/unit/test_docs_translation_parity.py` para atingir 100% de cobertura em 5 idiomas na raiz de `docs/`, atualizar referências em `docs/ARCHITECTURE*.md` e completar os índices dos cinco `README*.md` com os guias canônicos ausentes (`gitpr-issue-option`, `guia-regex-gitpr`, `marketplace-publishing-guide`, `otimizacao-de-tokens`, `untracked-files`, `version-markers` e `mentor-mode`).

## Fatos Levantados no Repositório

1. `docs/extra/` já existe e contém `como_reverter_commit_git_localmente.md` e `testar_sem_usar_pypi.md`.
2. `tests/unit/test_docs_translation_parity.py` (L14–L16) define `_EN_ONLY = {"github-issue-prompt-com-gh": ...}`.
3. `docs/ARCHITECTURE.md` (L270–L275) e suas 4 traduções (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`, L247–L252) listam `github-issue-prompt-com-gh.md`, `como_reverter_commit_git_localmente.md` e `testar_sem_usar_pypi.md` sem o prefixo `extra/`.
4. `README.md` (L147) já lista `gitpr mentor [<finding_id>]` com link para `mentor-mode` na seção **Advanced Options and Commands**, mas não na seção `📚`. Os 4 READMEs traduzidos (`README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md`) não possuem `mentor-mode` em nenhuma das duas seções.
5. Os 6 guias (`gitpr-issue-option`, `guia-regex-gitpr`, `marketplace-publishing-guide`, `otimizacao-de-tokens`, `untracked-files`, `version-markers`) existem na raiz de `docs/` e não estão listados na seção `📚` de nenhum dos 5 `README*.md`.
6. O contrato de query params `?lang=` validado por `tests/test_doc_links.py` e `src/doc_links.py` exige:
   - `README.md`: sem `?lang=`
   - `README.pt_br.md`: `?lang=pt_br`
   - `README.pt_pt.md`: `?lang=pt_pt`
   - `README.es_es.md`: `?lang=es`
   - `README.fr_fr.md`: `?lang=fr`

## Decisões da Entrevista (`/grill-with-docs`)

| Pergunta | Decisão Confirmada |
|---|---|
| **Q1** (`mentor-mode` nos READMEs) | Adicionar `mentor-mode` tanto na seção **Opções e Comandos Avançados** dos 4 READMEs traduzidos (espelhando `README.md`) quanto na seção `📚` de todos os 5 `README*.md`. |
| **Q2** (Categorização na seção `📚`) | **Core Features:** `gitpr-issue-option`, `untracked-files`, `mentor-mode`. **DevOps & CI/CD:** `guia-regex-gitpr`. **Configuration & Infrastructure:** `marketplace-publishing-guide`, `otimizacao-de-tokens`, `version-markers`. |
| **Q3** (Links em `docs/ARCHITECTURE*.md`) | Atualizar `github-issue-prompt-com-gh.md` para `extra/github-issue-prompt-com-gh.md` e corrigir também `extra/` nos outros 2 links da mesma lista (`como_reverter_commit_git_localmente.md` e `testar_sem_usar_pypi.md`) nas 5 versões de `docs/ARCHITECTURE*.md`. |
| **Q4** (Glossário `CONTEXT.md`) | Registrar os termos canônicos **Canonical doc** e **Extra doc** em `CONTEXT.md`. (Sem ADR.) |
