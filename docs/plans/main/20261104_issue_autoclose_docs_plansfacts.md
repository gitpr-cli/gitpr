# Plano — Documentação técnica do fechamento automático de issue

- **Data:** 2026-11-04
- **Branch:** `main`
- **Origem:** skill `grill-with-docs` (grilling + domain-modeling)
- **Objetivo:** dar à feature `--close-issue` / `--no-close-issue` o mesmo
  tratamento documental das features análogas — documento técnico próprio nos
  5 idiomas, seção no README (e nas 4 traduções) e ligação correta na ajuda
  contextual

## 1. Contexto

A feature chegou à `main` no merge #260 (`chore: bump version to 1.5.0 and lang
to v0.0.38`) e estava documentada apenas como **§5.3 de
`docs/issue-tui-help.*`**, uma linha em `docs/config-tui.*`, um parágrafo em
`docs/metricas-telemetria.*`, um bullet nos 5 READMEs, o CHANGELOG e termos do
`CONTEXT.md`. Não existia `docs/issue-autoclose.*`.

Todas as features análogas (`risk-scoring`, `policy-packs`,
`baseline-suppressions`, `check-ci`, `mentor-mode`) têm documento próprio nos
5 idiomas + entrada no README + entrada no índice `📚 Technical Documentation`.
A fonte factual são os 12 relatórios de
`docs/claude-code/reports/feat/issue-autoclose/` (T0–T9, teste manual e
encerramento) e o código em `src/issue_autoclose/`, `src/main.py`,
`src/config.py`.

## 2. Decisões tomadas com o usuário

| Decisão | Escolha |
|---|---|
| Nome/slug | `issue-autoclose` (casa com `docs/specs/issue-autoclose/` e `src/issue_autoclose/`) |
| README | H2 próprio + entrada no índice `### Core Features` + retarget do bullet existente |
| `HELP_MAP` | `close_issue` e `no_close_issue` passam a apontar para `issue-autoclose.md` |
| Fora de escopo | `docs/ARCHITECTURE.*` (catálogo já obsoleto); bullet do `gitpr mentor` ausente nas traduções |

## 3. Arquivos tocados (17)

| Arquivo | Ação |
|---|---|
| `docs/issue-autoclose.md` | criar (EN, 259 linhas) |
| `docs/issue-autoclose.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md` | criar (traduções integrais) |
| `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md` | 3 edições por arquivo |
| `docs/issue-tui-help.md` (+4 idiomas) | 1 frase de cross-link na §5.3 |
| `src/main.py` | 2 URLs no `HELP_MAP` (linhas 230 e 237) |
| `tests/test_cli_help.py` | 1 asserção (linha 99) |

## 4. Estrutura dos 5 documentos

Título, parágrafo de abertura (o número da issue morre com a TUI; a feature o
leva até o PR), `---`, então as seções numeradas — mesma numeração e mesmos
títulos traduzidos nos 5 arquivos.

| # | Seção | Conteúdo |
|---|---|---|
| 1 | Overview | As três superfícies: criação registra, run de PR decide/insere, ajuda contextual explica. |
| 1.1 | Command Reference | As 5 invocações; flags mutuamente exclusivas (erro de uso, exceto com `-h`). |
| 2 | The Flow, End to End | 6 passos: registrar (F3) → gate barato → decidir → montar corpo → publicar → limpar. |
| 2.1 | What Each Step Costs | Tabela de I/O por passo; "sem registro = fluxo antigo, byte a byte". |
| 3 | The Registry File | `.gitpr/conf/github.yml`: local, não versionado, uma issue por vez. |
| 3.1 | The Format | YAML literal com `schema_version: 1` e os 6 campos de `last_issue`. |
| 3.2 | Writes, Corruption and `.gitignore` | Tempfile + `os.replace`; corrompido vira erro reportado e é sobrescrito; exatamente 1 linha no `.gitignore` (ADR-015). |
| 4 | The Decision: Gates in Order | Tabela dos 13 gates na ordem do código, com `skipped_reason`, custo e se limpa o registro. |
| 4.1 | The Question and the Target-Branch Warning | Texto da pergunta, `default=True`, aviso de branch default, Ctrl+C não engolido. |
| 4.2 | What the Outcome Carries | `decision`, `warning`, `skipped_reason`, `asked`, `accepted`. |
| 5 | Insertion and Idempotency | Ponto único de montagem do corpo; parágrafo próprio; regex de keywords com `owner/repo#N`; badge vem depois. |
| 6 | The SCM Contract and the Other Forges | `get_issue`/`get_default_branch`/`closing_line` são concretos mas levantam `ScmNotSupportedError` por padrão; só GitHub implementa. |
| 7 | Configuration | `GITPR_ISSUE_AUTOCLOSE` e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT`; precedência `--no-close-issue` > config > `--close-issue`. |
| 8 | Metrics | Linha `command="issue_autoclose"` com `asked`/`accepted`/`skipped_reason`. |
| 9 | Limits, Stated Plainly | 8 limites (uma issue por vez, só pela TUI, só GitHub, estado por clone, keywords em inglês etc.). |
| 10 | Related Reading | Caminhos em backticks para os docs vizinhos e ADRs. |

## 5. READMEs (5 arquivos, 3 edições cada)

1. **H2 novo** — entre a última linha da seção do badge e o H2 multi-modelo:
   `## 🔗 Automatic Issue Closure (--close-issue)` e traduções; 2 parágrafos,
   tabela de 4 linhas (2 flags + 2 variáveis), parágrafo de limites e
   `📖 **Full documentation:**` com `?lang=` nas traduções.
2. **Entrada no índice** — em `### Core Features`, imediatamente depois da
   entrada de Issues.
3. **Retarget do bullet** — no bullet `` `--close-issue` / `--no-close-issue` ``,
   trocar só a URL final de `issue-tui-help` para `issue-autoclose`,
   mantendo o `?lang=`.

Os 5 READMEs são integralmente **CRLF** — as edições foram aplicadas por
script que lê e escreve com `newline=''`, para não converter as terminações.

## 6. `HELP_MAP` + teste

- `src/main.py:230` e `:237`: `get_doc_url("issue-tui-help.md")` →
  `get_doc_url("issue-autoclose.md")` (título e descrição intactos).
- `tests/test_cli_help.py:99`: asserção passa a `docs/issue-autoclose`.

## 7. Ordem de execução

1. `docs/issue-autoclose.md` (EN completo).
2. As 4 traduções a partir do EN.
3. Cross-link na §5.3 dos 5 `issue-tui-help.*`.
4. READMEs um por vez, com as 3 edições juntas: EN → pt_br → pt_pt → es_es → fr_fr.
5. `src/main.py` + `tests/test_cli_help.py` no mesmo passo.
6. Verificação.
7. Artefatos (plansfacts, surveyfacts, relatório de conclusão).

## 8. Verificação

```bash
python -m pytest tests/test_cli_help.py -q
python -m pytest tests/issue_autoclose tests/test_config_issue_autoclose.py -q
python -m pytest -q --deselect "tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched"
```

- Paridade dos 5 docs: mesma sequência de headings, mesma contagem de linhas e
  de tabelas.
- Cada README: um único `^## 🔗`, `issue-autoclose` presente no H2, no índice e
  no bullet.
- Cross-link exatamente 1 (uma linha) em cada `issue-tui-help.*`.
- `doc_url('issue-autoclose.md')` resolve para o slug correto.

## 9. Restrições

- **Nunca** `git add`, `git commit` ou `git push` — tudo fica na árvore de trabalho.
- Leituras/escritas de arquivo em UTF-8 com `errors='replace'`; arquivos novos com LF.
- Não editar: `docs/ARCHITECTURE.*`, `build/lib/src/main.py`, `src/ui/help_screen.py`, `docs/config-tui.*`, `docs/metricas-telemetria.*`, `CONTEXT.md`.
