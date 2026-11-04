# Survey — Documentação técnica do fechamento automático de issue

- **Data:** 2026-11-04
- **Branch:** `main`
- **Pedido:** verificar se a nova feature recebeu arquivo de documentação
  técnica (os relatórios de implementação estão em
  `docs/claude-code/reports/feat/issue-autoclose`), salvar a documentação em
  `docs/` e implementá-la também no `README.md` e em todas as versões de
  idioma suportadas
- **Escopo desta sessão:** criar `docs/issue-autoclose.*` (5 idiomas), seção e
  entrada de índice nos 5 READMEs, cross-link na §5.3 de `issue-tui-help.*` e
  retarget da ajuda contextual

## 1. Contexto da tarefa

A feature de fechamento automático (`--close-issue` / `--no-close-issue`)
chegou à `main` no merge #260. A verificação inicial mostrou que **não havia
documento técnico próprio**: o assunto vivia apenas como §5.3 de
`docs/issue-tui-help.*` (5 idiomas), uma linha de `docs/config-tui.*`, um
parágrafo de `docs/metricas-telemetria.*`, um bullet nos 5 READMEs, o
CHANGELOG e termos do `CONTEXT.md`.

Features análogas (`risk-scoring`, `policy-packs`, `baseline-suppressions`,
`check-ci`, `mentor-mode`) seguem a convenção da casa: um `docs/<slug>.md` em
EN com quatro traduções (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`),
uma seção no README de cada idioma e uma entrada no índice
`📚 Technical Documentation`.

## 2. Decisões confirmadas (1 rodada de grill)

| # | Tema | Decisão |
|---|---|---|
| Q1 | Nome/slug | `issue-autoclose` — casa com `docs/specs/issue-autoclose/` e `src/issue_autoclose/` |
| Q2 | Tratamento no README | H2 próprio + entrada no índice `### Core Features` + retarget do bullet existente para o novo doc |
| Q3 | `HELP_MAP` | `close_issue` e `no_close_issue` passam a apontar para `issue-autoclose.md`, com o teste de ajuda contextual ajustado |
| Q4 | Extras | Nenhum — `docs/ARCHITECTURE.*` (catálogo já obsoleto) e o bullet ausente do `gitpr mentor` nas traduções ficam fora |

## 3. Relatório de fatos levantados

### 3.1 Fonte factual

Doze relatórios em `docs/claude-code/reports/feat/issue-autoclose/`, de
`2026-11-01_t0_issue_autoclose_investigation.md` a
`2026-11-03_t9_issue_autoclose_docs.md` (T0–T9, teste manual e encerramento).
O código confirma o que os relatórios descrevem:

- **Gates** em `src/issue_autoclose/resolve_close_issue.py:88-165`, nesta
  ordem: `flag-disabled` → `disabled` → `not-github` → `registry-error` →
  `no-record` → `other-repo` → `issue-missing` (404, limpa) →
  `verify-failed` (mantém) → `issue-is-pr` (checado **antes** do estado) →
  `issue-not-open` (limpa) → `no-tty` → decisão (`--close-issue` aceita ou
  pergunta; `declined` recusa).
- **Limpeza nunca é decisão de `resolve_close_issue`** (ADR-007): quem limpa é
  o fluxo de publicação em `src/main.py:1951` (publicação direta) e `:2023`
  (TUI), via `_clear_close_issue_record`.
- **`_prepare_close_issue`** (`src/main.py:5861-5941`) roda antes do check de
  unstaged, do diff e da IA; constrói o registro só depois de checar flag e
  config.
- **`insert_close_line`** roda em `src/main.py:1868-1870`, depois do reviewer
  guide e antes do `.md` e do `pr_data`.
- **Registro** em `src/issue_autoclose/issue_registry.py`: dataclass
  `RegisteredIssue(repo, number, title, url, created_at, branch)`,
  `SCHEMA_VERSION = 1`, `GITIGNORE_ENTRY = ".gitpr/conf/github.yml"`,
  comparação de repositório com `casefold`.
- **Configuração** em `src/config.py:508-519`; `--close-issue` **não**
  sobrepõe `GITPR_ISSUE_AUTOCLOSE=false`.
- **Métrica** `issue_autoclose` com `asked` / `accepted` / `skipped_reason`.

### 3.2 Convenções da casa verificadas

- Título de abertura `# Technical Documentation: <Feature> (<command>)` em EN,
  com equivalências nos 4 idiomas; parágrafo de introdução; `---`; seções
  `## N.` numeradas.
- Links do README: `https://gitpr.natanfiuza.dev.br/docs/<slug>` (EN) e
  `?lang=pt_br|pt_pt|es|fr` nas traduções.
- Os 5 READMEs são **integralmente CRLF** (613/611/609/609/610 linhas antes da
  edição); qualquer escrita precisa preservar as terminações.

### 3.3 Entregas desta sessão

| Grupo | Arquivos | Conteúdo |
|---|---|---|
| Documentos | `docs/issue-autoclose*.md` (5) | 259 linhas cada, 16 headings idênticos, 7 tabelas cada |
| Docs vizinhos | `docs/issue-tui-help*.md` (5) | 1 frase de cross-link na §5.3, antes do `> **Tip**` |
| READMEs | `README*.md` (5) | H2 `## 🔗 … (--close-issue)`, entrada no índice, retarget do bullet — CRLF preservado |
| Código | `src/main.py` | 2 URLs do `HELP_MAP` |
| Teste | `tests/test_cli_help.py` | 1 asserção |

Diff final: 12 arquivos versionados modificados (+108/−8) e 5 documentos
novos não rastreados.

### 3.4 Testes

- `tests/test_cli_help.py`: 9 passed.
- `tests/issue_autoclose` + `tests/test_config_issue_autoclose.py`: 130 passed,
  86 subtests.
- Suíte completa (com o teste de integração que trava sem TTY deselecionado):
  **3273 passed, 2 skipped, 1 deselected, 227 subtests**, 12 minutos — nenhuma
  falha, inclusive nas duas pré-existentes de `tests/test_plugins.py`.
- `doc_url('issue-autoclose.md')` resolve para
  `https://gitpr.natanfiuza.dev.br/docs/issue-autoclose` (+ `?lang=` do idioma
  corrente).
- Paridade dos 5 docs: mesmas 16 headings na mesma ordem, mesmas 7 tabelas,
  mesmas 259 linhas.
- Cross-link: exatamente 1 linha por `issue-tui-help.*`.
- READMEs: 1 único H2 `🔗` por arquivo; o slug aparece 4× por arquivo (duas na
  linha do H2 — texto e href —, uma no índice, uma no bullet).

### 3.5 Observações

- `docs/i18n` e `docs/understanding` são slugs citados nos READMEs que nunca
  tiveram arquivo local — condição **pré-existente**, não introduzida aqui.
- `doc_url()` recebe um único argumento (o nome do arquivo) e acrescenta o
  idioma corrente; não aceita um código de idioma explícito.
