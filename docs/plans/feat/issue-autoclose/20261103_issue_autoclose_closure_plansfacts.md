# Plano de execução — Encerramento da feature `issue-autoclose`

- **Data:** 2026-11-03
- **Branch:** `feat/issue-autoclose`
- **Fonte:** `docs/specs/issue-autoclose/00-SPEC.md` + decisões de grill
  registradas em `docs/survey/20261103_issue_autoclose_closure_surveyfacts.md`
- **Modo:** um passo por vez, com parada para evidências; **nenhum
  `git add/commit/push/tag`** (regra do `CLAUDE.md`).

## Decisões que governam a execução

| # | Tema | Decisão |
|---|---|---|
| Q1 | Escopo | Teste manual §12 + relatório final + release/tag; descrição do PR não é preparada aqui |
| Q2 | Teste manual | Roteiro escrito aqui, executado pelo usuário em repositório de teste, que devolve as evidências |
| Q3 | Descrição do PR | Gerada pelo usuário com o próprio `gitpr` |
| Q4 | Versão | `1.5.0` (minor) |
| Q5 | Bump e tag | Bump na branch após o teste manual; merge em `main` e tag `v1.5.0` no merge, pelo usuário |

## Passo 0 — Registrar a sessão

- `docs/survey/20261103_issue_autoclose_closure_surveyfacts.md`
- Este documento.
- `docs/claude-code/plans/feat/issue-autoclose/2026-11-03_feat_issue_autoclose_closure.md`.

## Passo 1 — Roteiro do teste manual (§12)

`docs/claude-code/reports/feat/issue-autoclose/2026-11-03_manual_test_issue_autoclose.md`
com pré-requisitos e os cinco passos do §12, cada um com o comando exato, o
resultado esperado e a evidência a devolver:

- Rodar `python run.py`, nunca o `gitpr` do PATH.
- Passo 1: `-is` + F3 grava `.gitpr/conf/github.yml` (`schema_version: 1`,
  `last_issue` com repo/number/title/url/created_at/branch) e acrescenta a
  linha única em `.gitignore`.
- Passo 2: a pergunta vem antes da TUI de stage; `close #N` no fim do corpo,
  imediatamente antes do badge.
- Passo 3: o registro deixa de existir após o PR publicado.
- Passo 4: issue fechada no GitHub não pergunta e limpa o registro.
- Passo 5: `--no-close-issue` mantém o registro sem perguntar; execução sem TTY
  não pergunta nem insere.

## Passo 2 — Relatório final

`docs/claude-code/reports/feat/issue-autoclose/2026-11-03_final_issue_autoclose_closure.md`
depois das evidências: verificação (testes, i18n, HTTP, diff), resultado passo a
passo do §12, fora de escopo e checklist de release.

## Passo 3 — Bump para 1.5.0 (somente após o teste manual passar)

1. `python run.py release --version 1.5.0 --since-tag v1.4.4`.
2. Remover o bloco `## [Unreleased]` da T9 — a seção gerada já carrega a
   feature; manter os dois duplicaria o bullet.
3. `1.4.4` → `1.5.0` em `src/updater.py`, `CLAUDE.md` e `GEMINI.md`.
4. `python -m pytest tests/unit/test_version_consistency.py -q`, i18n e suíte
   ampla.
5. Deixar na árvore de trabalho; commit sugerido `chore: bump version to 1.5.0`.

## Passo 4 — Merge e tag (usuário)

PR `feat/issue-autoclose` → `main` com a descrição gerada pelo `gitpr`;
`git tag v1.5.0` e `git push origin v1.5.0` no merge. O workflow publica no
PyPI e cria a GitHub Release.

## Fora de escopo

- Preparar título/descrição do PR.
- Executar `git add/commit/push/tag`.
- Follow-ups: funil de métricas do autoclose, outras forges, múltiplas issues,
  "não perguntar mais".
