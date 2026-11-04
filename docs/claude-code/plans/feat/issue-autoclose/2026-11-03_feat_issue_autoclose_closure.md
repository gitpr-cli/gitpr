# Plano — Encerramento da feature issue-autoclose

## Contexto

T0–T9 estão entregues, com dez relatórios em
`docs/claude-code/reports/feat/issue-autoclose/`. O diff contra `origin/main`
tem 58 arquivos (+3946/−20), todos da feature; a fatia T1/T2 (`7287251`) já
chegou ao `main` pelo PR #258 e os sete commits restantes (`4309268`…`eca21e8`)
estão na branch. A árvore de trabalho está limpa.

O critério de aceite que falta é o **teste manual final (§12 da SPEC)**. Depois
dele, o encerramento se completa com um relatório consolidado e a release
`1.5.0`.

Decisões da sessão (grill de 2026-11-03):

| # | Tema | Decisão |
|---|---|---|
| Q1 | Escopo | Teste manual §12 + relatório final + release/tag; descrição do PR não é preparada aqui |
| Q2 | Teste manual | Roteiro escrito por Claude; execução e evidências do usuário |
| Q3 | Descrição do PR | Gerada pelo usuário com o próprio `gitpr` |
| Q4 | Versão | `1.5.0` (minor) |
| Q5 | Bump e tag | Bump na branch depois do teste manual; tag `v1.5.0` no merge de `main`, pelo usuário |

## Abordagem

### Passo 0 — Artefatos de planejamento

- `docs/survey/20261103_issue_autoclose_closure_surveyfacts.md`
- `docs/plans/feat/issue-autoclose/20261103_issue_autoclose_closure_plansfacts.md`
- Este documento.

### Passo 1 — Roteiro do teste manual

`docs/claude-code/reports/feat/issue-autoclose/2026-11-03_manual_test_issue_autoclose.md`.
Pré-requisitos (repositório de teste no GitHub, token em `~/.gitpr/.env`,
branch com diff publicável) e os cinco passos do §12 com comando, resultado
esperado e evidência:

1. `-is` + F3 → `.gitpr/conf/github.yml` com `schema_version: 1` e `last_issue`
   completo; linha única em `.gitignore`; `git check-ignore` confirma.
2. `gitpr` → pergunta **antes** da TUI de stage, resposta Sim, `close #N` no fim
   do corpo, imediatamente antes do badge e uma única vez.
3. Registro removido após o PR publicado (`IssueRegistry.clear()` desvincula o
   arquivo).
4. Issue fechada no GitHub → sem pergunta e registro removido.
5. `--no-close-issue` → sem pergunta e registro mantido; sem TTY
   (`cmd /c "python run.py --no-edit < nul"`) → sem pergunta e sem linha.

Execução sempre com `python run.py`: o `gitpr` do PATH é a release antiga do
PyPI.

### Passo 2 — Relatório final

`docs/claude-code/reports/feat/issue-autoclose/2026-11-03_final_issue_autoclose_closure.md`
com as evidências: tabela de verificação, resultado do §12, fora de escopo e
checklist de release.

### Passo 3 — Bump para 1.5.0

1. `python run.py release --version 1.5.0 --since-tag v1.4.4` — gera a seção a
   partir dos 26 commits desde a 1.4.4.
2. Remover `## [Unreleased]` (o bullet da feature já está na seção gerada).
3. `1.4.4` → `1.5.0` em `src/updater.py`, `CLAUDE.md` e `GEMINI.md`.
4. Testes: `test_version_consistency`, i18n e suíte ampla.
5. Deixar na árvore; commit sugerido `chore: bump version to 1.5.0`.

### Passo 4 — Merge e tag (usuário)

PR para `main` com a descrição gerada pelo `gitpr`; `git tag v1.5.0` +
`git push origin v1.5.0` no merge. O `release.yml` valida tag == `__version__`,
roda a suíte, publica no PyPI (OIDC) e cria a GitHub Release.

## Arquivos

| Arquivo | Mudança |
|---|---|
| `docs/survey/20261103_issue_autoclose_closure_surveyfacts.md` | novo — levantamento |
| `docs/plans/feat/issue-autoclose/20261103_issue_autoclose_closure_plansfacts.md` | novo — plano da sessão |
| `docs/claude-code/plans/feat/issue-autoclose/2026-11-03_feat_issue_autoclose_closure.md` | novo — este plano |
| `docs/claude-code/reports/feat/issue-autoclose/2026-11-03_manual_test_issue_autoclose.md` | novo — roteiro §12 |
| `docs/claude-code/reports/feat/issue-autoclose/2026-11-03_final_issue_autoclose_closure.md` | novo — relatório final |
| `src/updater.py`, `CLAUDE.md`, `GEMINI.md` | `1.4.4` → `1.5.0` |
| `CHANGELOG.md` | seção `[1.5.0]` gerada; `[Unreleased]` removido |

## Verificação

1. `python -m pytest tests/unit/test_version_consistency.py -q` → verde.
2. Suíte ampla na receita das tarefas anteriores, documentando as 8 falhas
   pré-existentes de `tests/test_plugins.py`.
3. `python -m pytest tests/test_i18n.py -q` → 22 passed.
4. Evidências do §12 registradas no relatório final.
5. `git diff --stat` do bump: só `src/updater.py`, `CLAUDE.md`, `GEMINI.md`,
   `CHANGELOG.md`.

## Fora de escopo

Preparar a descrição do PR; executar `git add/commit/push/tag`; follow-ups
(funil de métricas, outras forges, múltiplas issues, "não perguntar mais").
