# Walkthrough — Segregação entre Auto-Seed de Runtime e Provisionamento de Projeto (`gitpr seed`)

## Contexto e Visão Geral
Durante a análise dos relatórios de estado e débitos históricos (`relatorio_estado_v0.0.22.md:898`), foi identificada a necessidade de alinhamento e formalização sobre o estado da semeadura de configurações locais em `.gitpr/conf/` (`gitpr.config.yml` e `gitpr.smart-excludes.json`) e `.gitpr/skill/` (`.gitpr.linter.yml`).

A implementação do subcomando `gitpr seed` e a reestruturação do wizard interativo `gitpr --install` em 5 etapas já havia sido concluída com sucesso no relatório v0.0.23. Esta sessão de `/plan` e `/grill-with-docs` alinhou as decisões arquiteturais, estabeleceu um ADR formal e refinou o modelo de domínio do GitPR.

---

## O que foi realizado

1. **Sessão de Grill & Alinhamento:**
   - Confirmou-se que o débito já estava liquidado no código pelas entregas anteriores do `gitpr seed` e wizard de 5 etapas.
   - Decidiu-se deliberadamente manter o auto-seed silencioso do primeiro comando em repositório restrito a `.gitpr/conf/gitpr.config.yml`, evitando sujar o `git status` com arquivos que o desenvolvedor não solicitou.
   - Consolidou-se que o provisionamento completo de `smart-excludes` e `linter` reside exclusivamente nas ações explícitas: `gitpr seed`, `gitpr --install` e `gitpr --skill`.

2. **Criação do ADR 0019:**
   - Registrado em [`docs/adr/0019-project-configuration-seed-segregation.md`](file:///docs/adr/0019-project-configuration-seed-segregation.md).
   - Documenta o contexto, as alternativas rejeitadas (auto-seed agressivo de todos os arquivos vs. provisionamento explícito) e a rationale de design.

3. **Refinamento do Glossário Ubíquo (`CONTEXT.md`):**
   - Eliminada a duplicidade do termo `Project configuration seed`.
   - Adicionada a distinção canônica entre `Runtime project configuration seed` (restrito ao PR target base) e `Project configuration seed` (provisionamento completo via `gitpr seed`/wizard).

4. **Artefatos de Governança do Grill:**
   - Registrados em [`docs/plans/develop_natan/20261110_seed_conf_segregation_plansfacts.md`](file:///docs/plans/develop_natan/20261110_seed_conf_segregation_plansfacts.md) e [`docs/survey/20261110_seed_conf_segregation_surveyfacts.md`](file:///docs/survey/20261110_seed_conf_segregation_surveyfacts.md).

---

## Verificação e Testes

Todos os testes de seed e resolução de configuração de projeto foram executados e aprovados:
```bash
python -m pytest tests/test_seed_command.py tests/test_project_config.py -v
```
**Resultado:** 57 testes passaram em 18.57s com 100% de sucesso.
