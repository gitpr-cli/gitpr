# ADR-009 — Estrutura de Domínio e Acoplamento da Feature `gitpr mentor`

- **Status:** Aceito
- **Data:** 2026-10-06
- **Contexto:** spec [20260926_skill_gitpr_junior_mentor_spec.md](20260926_skill_gitpr_junior_mentor_spec.md), grill rodadas 1–3
- **Glossário:** [glossary-gitpr-mentor.md](glossary-gitpr-mentor.md)

## Contexto

A spec original de "Junior Mentor" propôs criar uma camada explicativa pedagógica sobre findings de code review. Duas questões fundamentais de design precisavam ser decididas:
1. **Onde residem os módulos**: o projeto possui módulos flat (`src/review_engine.py`), um pacote isolado (`src/fix/`, ADR-004) e subpacotes orientados a domínio sob `src/domain/` e `src/application/use_cases/` (usados nas features recentes `explain` e `tests generate`).
2. **Origem dos findings e identidade de IDs**: o motor de review do GitPR (`core.generate_pr_content`) gera apenas texto markdown/prosa, sem entidades estruturadas de finding.

## Decisão

1. **Estrutura de pastas**: Adotar `src/domain/mentor/` (para dataclasses e builder puro sem I/O) e `src/application/use_cases/generate_mentor_explanation.py` (para o orquestrador do caso de uso). Esta escolha segue estritamente a convenção das features mais recentes (`explain` e `tests generate`), mantendo a coesão arquitetural das novas expansões da CLI.
2. **Reuso da normalização de findings do `fix`**: O mentor consome os findings gerados por `collect_candidates` de `src/fix/apply_fix.py`, reutilizando os identificadores `FIX-NNN`. Isso garante uma única identidade de finding em todo o GitPR, evita duplicar o parsing de IA e permite sinergia imediata entre `gitpr mentor` e `gitpr fix`.
3. **Execução em lote com teto (cap)**: O caso de uso processa os findings em uma única chamada de IA em lote (com teto máximo de 10 findings priorizados por severidade), em vez de uma chamada por finding. Isso controla o consumo de tokens e a latência, armazenando o resultado sob cache de `mentor/`.

## Consequências

- **Positivas:**
  - Nenhuma segunda entidade de finding criada no produto.
  - Testes do builder de domínio 100% puros e desacoplados de I/O ou chamadas de IA.
  - Custo de IA previsível via lote e teto de segurança.
- **Negativas / Limitações:**
  - O mentor cria uma dependência de runtime com `src/fix/apply_fix.py` (especificamente `collect_candidates` e `FindingRef`). Caso o prompt do `fix` mude, os IDs do `mentor` acompanham essa evolução.

