# Survey Facts — Segregação entre Auto-Seed de Runtime e Provisionamento Explícito de Configuração

**Data:** 2026-11-10  
**Branch:** `develop_natan`  
**Task:** `seed_conf_segregation`  
**Origem:** Resolução definitiva do item de dívida histórica de `docs/reports/relatorio_estado_v0.0.22.md:898` (*"Seed de `.gitpr/conf/` local: o seed do smart-excludes e do linter continua pendente como subcomando próprio ou etapa do wizard — o `gitpr.config.yml` agora cobre só a base do PR"*).

---

## 1. Contexto e Fatos Levantados na Base de Código

1. **Estado do Subcomando e Flags:**
   - O subcomando `gitpr seed` e a flag top-level `--seed` / `-sd` (com opções `--force` e `--all`) foram implementados em `src/main.py` e `src/core.py:1650` (`seed_project_configuration`).
   - A função provisiona de forma idempotente:
     - `.gitpr/conf/gitpr.config.yml` (via `ensure_project_config()`)
     - `.gitpr/conf/gitpr.smart-excludes.json` (via `_seed_local_smart_excludes()`)
     - `.gitpr/skill/.gitpr.linter.yml` (via `download_skill_file()`)
     - Se `--all`, todos os templates de IA para `.gitpr/skill/`.

2. **Wizard Interativo de Instalação (`gitpr --install`):**
   - Reestruturado em 5 etapas no arquivo `src/core.py:2143`:
     - **Etapa 1:** Project Local Configuration (`.gitpr/conf/`)
     - **Etapa 2:** Skill Templates & Linter (`.gitpr/skill/`)
     - **Etapa 3:** Git Hooks
     - **Etapa 4:** MCP Server Configuration
     - **Etapa 5:** API Key Configuration

3. **Auto-Seed em Tempo de Execução Comum (`src/main.py:1427`):**
   - Ao executar comandos cotidianos dentro de repositórios Git (`gitpr`, `gitpr -c`, `gitpr -r`, etc.), o callback raiz aciona apenas `ensure_project_config()`, semeando exclusivamente `gitpr.config.yml`.
   - Essa segregação foi identificada como intencional para manter o primeiro uso não-invasivo e evitar poluição inesperada do `git status` com arquivos adicionais.

4. **Status dos Testes:**
   - 8 testes unitários cobrem o seed em `tests/test_seed_command.py` com 100% de taxa de sucesso.

---

## 2. Decisões do Grill (Rodada 1)

| Decisão | Tópico | Opção Escolhida | Justificativa |
|---|---|---|---|
| **D1 (Q1)** | Objetivo e Escopo da Tarefa | **(A) Validar e formalizar a segregação de responsabilidades** | O código do `gitpr seed` e wizard já estavam prontos; o objetivo foi formalizar a arquitetura e documentar que o débito está quitado. |
| **D2 (Q2)** | Comportamento do Auto-Seed de Runtime | **(A) Manter auto-seed restrito a `gitpr.config.yml`** | Previne que desenvolvedores executando comandos simples de leitura tenham arquivos secundários (`smart-excludes`, `linter`) criados silenciosamente em sua árvore de trabalho. |
| **D3 (Q3)** | Registro Arquitetural (ADR) | **(A) Criar ADR formal (ADR 0019)** | Consolida e encerra de forma definitiva a rationale técnica nos registros históricos do projeto, evitando dúvidas em futuros relatórios de estado. |

---

## 3. Entregas Realizadas

1. **ADR 0019 (`docs/adr/0019-project-configuration-seed-segregation.md`)**:
   - Formalização do contrato entre auto-seed de primeiro uso e provisionamento explícito de projeto.
2. **Glossário de Domínio (`CONTEXT.md`)**:
   - Refinamento e desambiguação dos termos `Runtime project configuration seed` e `Project configuration seed`.
3. **Artefatos de Planejamento**:
   - Registro em `docs/plans/develop_natan/20261110_seed_conf_segregation_plansfacts.md`.
