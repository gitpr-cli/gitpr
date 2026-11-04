# Survey — Encerramento da feature de fechamento automático de issue

- **Data:** 2026-11-03
- **Branch:** `feat/issue-autoclose`
- **Fonte da especificação:** `docs/specs/issue-autoclose/00-SPEC.md`
  (§7 testes, §8 critérios de aceite, §12 teste manual)
- **Escopo desta sessão:** verificação do que já foi entregue e fechamento da
  feature — teste manual §12, relatório consolidado e release `1.5.0`

## 1. Contexto da tarefa

A feature foi implementada de ponta a ponta nas tarefas T0–T9. O pedido desta
sessão foi verificar se tudo já estava feito e, em caso positivo, "encerrar a
issue-autoclose". O único critério de aceite da SPEC ainda não satisfeito é o
**teste manual final (§12)**, que depende de um repositório real no GitHub e de
execução humana — e, depois dele, a publicação da versão.

## 2. Decisões confirmadas (2 rodadas de grill)

### Rodada 1 — escopo do encerramento

| # | Tema | Decisão |
|---|---|---|
| Q1 | Escopo | Teste manual §12 + relatório final + release/tag. Preparar a descrição do PR **não** entra |
| Q2 | Execução do teste manual | Claude escreve o roteiro; o usuário executa em repositório de teste e devolve as evidências |
| Q3 | Descrição do PR | O usuário gera com o próprio `gitpr`; nada é preparado aqui |

### Rodada 2 — versão e ponto do bump

| # | Tema | Decisão |
|---|---|---|
| Q4 | Versão | `1.5.0` (minor — 11 commits `feat` desde a 1.4.4) |
| Q5 | Bump e tag | Commit `chore: bump version to 1.5.0` **na branch**, só depois de o teste manual passar; o usuário mergeia em `main` e empurra a tag `v1.5.0` no merge |

## 3. Relatório de fatos levantados

### 3.1 Entregas T0–T9

Dez relatórios em `docs/claude-code/reports/feat/issue-autoclose/`, de
`2026-11-01_t0_issue_autoclose_investigation.md` a
`2026-11-03_t9_issue_autoclose_docs.md`. Todos os commits da feature estão na
branch: os sete mais recentes (`4309268`…`eca21e8`) à frente de
`origin/feat/issue-autoclose`; a fatia T1/T2 (`7287251`) já está em
`origin/main` via PR #258.

### 3.2 Diff contra `origin/main`

58 arquivos, +3946/−20. Nenhum arquivo alheio à feature. Os artefatos sob
`.gitpr/reports/` seguem a norma do projeto (196 arquivos já versionados no
`main`), o ledger `.gitpr/metrics/` é ignorado e a árvore de trabalho está
limpa.

### 3.3 Testes

- Suíte ampla na receita das tarefas anteriores: **3163 passed**, 8 falhas
  pré-existentes de `tests/test_plugins.py` (só em execução ampla, por conta do
  `load_dotenv(override=True)` injetando `GITPR_LINTER_SECURITY='true'`; o
  arquivo passa 17/17 isolado), 2 skipped.
- `tests/test_i18n.py`: 22/22.
- `tests/issue_autoclose` + `tests/test_metrics.py`: 284 passed, 56 subtests.

### 3.4 Restrições arquiteturais

- Nenhum `requests`/chamada HTTP nova fora de `src/infrastructure/scm/`.
- Nenhuma chave i18n ausente (`tests/test_i18n.py` verde).
- Divergências da SPEC/ADRs registradas nos relatórios: configuração em env
  vars em vez de chave aninhada; registro em `src/issue_autoclose/` em vez de
  `src/infrastructure/state/`.

### 3.5 Mecânica de release

- `.github/workflows/release.yml` dispara em **push de tag `v*`**, roda
  `python -m pytest tests/ -q`, exige `v{__version__}` igual à tag, constrói e
  publica no PyPI via OIDC Trusted Publishing, e cria a GitHub Release.
- Versão SSOT em `src/updater.py:12` (`__version__ = "1.4.4"`); o
  `pyproject.toml` lê por `attr`. `tests/unit/test_version_consistency.py`
  também pina `CLAUDE.md` e `GEMINI.md`.
- `python run.py release --version 1.5.0 --since-tag v1.4.4` gera a seção do
  `CHANGELOG.md` a partir dos 26 commits desde a 1.4.4, mas **não** altera
  `src/updater.py` — o bump é manual.
- Padrão histórico: `80cb849 chore: bump version to 1.4.4` altera
  `src/updater.py`, `CHANGELOG.md`, `CLAUDE.md` e `GEMINI.md`; a tag fica no
  merge de `main`.

### 3.6 Estado do teste manual §12

Os cinco passos ainda não foram executados. O ambiente exigido é um repositório
de teste no GitHub com token em `~/.gitpr/.env` e uma branch com diff
publicável — pré-requisitos que o roteiro declara no topo. A execução será feita
com `python run.py`; o `gitpr` do PATH é a release antiga do PyPI.

## 4. Desfechos

- **Roteiro §12:** `docs/claude-code/reports/feat/issue-autoclose/2026-11-03_manual_test_issue_autoclose.md`.
- **Relatório final:** só depois das evidências do usuário.
- **Bump `1.5.0`:** só depois do teste manual passar.
- **Merge, PR e tag:** ações do usuário.
