# ADR-003 — Feature `gitpr release` em módulos flat (sem camadas DDD)

- **Status:** Aceito
- **Data:** 2026-09-07
- **Contexto:** spec [20260904_skill_gitpr_release_notes_spec.md](20260904_skill_gitpr_release_notes_spec.md) §2/§3, grill rodada 2 (Q10)
- **Glossário:** [glossary-release-notes.md](glossary-release-notes.md)

## Contexto

A spec §2 propõe uma árvore em **camadas** para a feature:
`src/domain/release/`, `src/application/use_cases/`, `src/infrastructure/git/`.
O projeto, porém, **não é DDD**: o código vive em módulos flat em `src/`
(engines de fluxo como `issue_engine.py`, `blame_engine.py`, `linter_engine.py`),
com dois subpacotes de exceção — `ui/` (isolamento obrigatório de componentes
Textual) e `infrastructure/scm/` (contrato multi-forge consumido por vários
call sites). A spec §0 (fatos) confirmou que `-ht`/`get_branch_history_text()`
não fornece commits estruturados, logo a extração tag→HEAD é código novo.

## Decisão

Implementar a feature em **módulos flat na raiz de `src/`**, no estilo dos
engines existentes:

- `src/commit_classifier.py` — parsing puro de Conventional Commits
  (prefixo/scope/`BREAKING CHANGE:`/`!`, `pr_number` via `(#123)`), sem I/O.
- `src/version_bump.py` — decisão pura MAJOR/MINOR/PATCH, sem I/O.
- `src/changelog_builder.py` — contratos (`ChangeCategory`, `ClassifiedCommit`,
  `ReleaseNotesResult`) e montagem do Markdown, sem I/O.
- `src/release_engine.py` — orquestração: resolução do range/tags via git,
  classificação, chamada de IA (`call_ai_model`), escrita/prepend do
  `CHANGELOG.md`, `create_release` na forge (mesma forma de `issue_engine.py`
  orquestrar git + IA + TUI).

Testes flat em `tests/`: `test_commit_classifier.py`, `test_version_bump.py`,
`test_changelog_builder.py`, `test_release_engine.py` (espelhando
`tests/test_core.py` e a organização atual — sem `tests/domain/...`).

### Alternativas consideradas

| Alternativa | Veredito |
|---|---|
| Camadas DDD da spec §2 (`domain/`, `application/use_cases/`, `infrastructure/git/`) | Rejeitada — introduziria uma terceira convenção arquitetural (após flat e os 2 subpacotes) só para uma feature; a spec foi escrita contra a estrutura real. |
| Pacote fatia `src/release/` | Rejeitada — criaria um terceiro tipo de subpacote; `ui/` e `infrastructure/scm/` existem por motivos estruturais (Textual, contrato multi-forge), não por fatia de feature. |
| Tudo num `release_engine.py` gigante | Rejeitada — classificação/bump/builder são lógica pura; juntá-las à orquestração prejudicaria os testes unitários sem I/O exigidos pela spec §8. |

## Desvios aprovados (vs. a spec §2)

1. Árvore de arquivos substituída pelos módulos flat acima (a spec §3 de
   contratos é mantida — os dataclasses/enum continuam concentrados em
   `changelog_builder.py` como previsto, com imports puros entre módulos).
2. Testes sem a hierarquia `tests/domain/release/` e
   `tests/application/use_cases/` da spec §2; ficam flat como os demais.

## Consequências

**Positivas:**
- Módulos puros sem I/O = testes unitários rápidos e determinísticos (spec §8.1–8.3).
- Consistência com a convenção de engines; nenhuma convenção nova a manter.
- Se o projeto adotar camadas no futuro, os módulos puros movem-se de forma
  mecânica (não importam nada do projeto).

**Negativas / custos:**
- A raiz de `src/` ganha +4 módulos (aceitável; cada um com responsabilidade única).
- Quem ler a spec §2 antes do ADR vai estranhar a árvore — por isso este registro.
