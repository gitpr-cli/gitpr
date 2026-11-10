# Implementation Plan — Segregação entre Auto-Seed de Runtime e Provisionamento de Projeto (`gitpr seed`)

## 1. Goal Description
Formalizar e consolidar a fronteira arquitetural entre o **Auto-Seed de Runtime** (que cria exclusivamente `.gitpr/conf/gitpr.config.yml` no primeiro comando executado em um repositório) e o **Provisionamento Explícito de Projeto** (executado via `gitpr seed`, `gitpr --install` ou `gitpr --skill`, que semeia o conjunto completo: `gitpr.config.yml`, `gitpr.smart-excludes.json` e `.gitpr/skill/.gitpr.linter.yml`). 

Esta decisão fecha o ciclo da pendência histórica identificada em `relatorio_estado_v0.0.22.md:898`, documentando formalmente no [ADR-0019](file:///docs/adr/0019-project-configuration-seed-segregation.md) as razões para manter o auto-seed de primeiro uso restrito à base do PR, evitando poluição inadvertida da árvore de trabalho do Git.

---

## 2. Decisões do Grill

- **Q1:** Confirmar que o débito já foi liquidado pela introdução de `gitpr seed` e do wizard de 5 passos, formalizando a arquitetura em ADR e documentação.
- **Q2:** Manter o auto-seed de primeiro uso restrito exclusivamente a `gitpr.config.yml`. Arquivos de `smart-excludes` e `linter` pertencem ao provisionamento deliberado via `gitpr seed` ou `gitpr --install`.
- **Q3:** Criar o ADR 0019 formalizando a segregação e atualizar os conceitos no glossário ubíquo (`CONTEXT.md`).

---

## 3. Componentes Afetados

- `docs/adr/0019-project-configuration-seed-segregation.md`
- `CONTEXT.md`
- `docs/plans/develop_natan/20261110_seed_conf_segregation_plansfacts.md`
- `docs/survey/20261110_seed_conf_segregation_surveyfacts.md`

---

## 4. Plano de Verificação

- `python -m pytest tests/test_seed_command.py tests/test_project_config.py -v`
