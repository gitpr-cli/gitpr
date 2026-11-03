# Plano — T8: i18n do issue-autoclose e métrica `issue_autoclose`

## Contexto

As T1–T7 entregaram a feature completa: registro local, gravação após
`gitpr -is`, decisão em `resolve_close_issue`, inserção idempotente da closing
line, integração no fluxo do PR, flags, limpeza do registro (ADR-007) e a
configuração (`GITPR_ISSUE_AUTOCLOSE` / `GITPR_ISSUE_AUTOCLOSE_TIMEOUT`).

O SPEC da T8 pede duas coisas: (1) as chaves i18n da pergunta, do aviso de
branch-alvo, do aviso de falha de verificação, do aviso de `.gitignore` e do
erro de flags conflitantes, com o teste de auditoria verde; (2) **opcional**,
um evento de métrica `issue_autoclose` com `asked`, `accepted` e
`skipped_reason`, sem dado sensível, seguindo o padrão local de
`src/metrics.py`.

Levantamento (feito no plano, sem código novo):

- **A i18n já está inteira.** As cinco strings do SPEC já são literais `__()`
  e estão traduzidas nos 6 arquivos `langs/*.json` (1694 chaves por arquivo,
  paridade exata, sem tradução-identidade). Onde cada uma mora:
  pergunta `resolve_close_issue.py:148`, aviso de branch-alvo `:186`, aviso de
  verificação `:219`, aviso de registro ilegível `:209`, mensagem de
  `.gitignore` `src/ui/issue_app.py:166`, aviso de falha de registro `:171`,
  erro de flags `src/main.py:771`, ajudas das flags `main.py:656-669`.
  A T8 **não adiciona chave nenhuma**; a auditoria
  (`tests/test_i18n.py`) roda como verificação, não como tarefa.
- **A métrica ainda não existe.** Q14 da sessão de grill
  (`docs/plans/feat/issue-autoclose/20261101_issue_autoclose_plansfacts.md`)
  fixou: `log_command_metric(command="issue_autoclose", provider="git",
  asked=, accepted=, skipped_reason=)`, sem coluna nova no ledger.
- O ledger (`src/ledger.py`) não tem caminho de migração local: `_ensure_schema`
  só aplica `_SCHEMA` quando `user_version == 0`. Colunas não mapeadas em
  `_KWARG_COLUMNS` viajam em `payload` (JSON) — o `record_event` já faz isso e
  `tests/test_metrics.py:290-312` já prova o comportamento. **Nenhuma mudança
  de schema.**

## Abordagem

### 1. O evento — uma linha em `_prepare_close_issue` (`src/main.py`)

Adicionar o import local junto dos que já existem (~l. 5865) e a chamada
**depois de `resolve_close_issue` retornar e depois de imprimir o aviso**,
antes do `return`:

```python
    from src.metrics import log_command_metric
```

```python
    if outcome.warning:
        click.secho(outcome.warning, fg="yellow", err=True)
    # Q14: one row per decision the use case reached. The helper's own
    # short-circuits never engaged the feature and stay out of the ledger.
    log_command_metric(
        command="issue_autoclose",
        provider="git",
        asked=outcome.asked,
        accepted=outcome.accepted,
        skipped_reason=outcome.skipped_reason,
    )
    return outcome.decision, registry, scm_context
```

Decisões embutidas (registrar no relatório):

- **Uma linha só quando o caso de uso decidiu (Opção A).** Por este helper só
  saem `not-github`, `registry-error`, `other-repo`, `issue-missing`,
  `issue-is-pr`, `issue-not-open`, `no-tty`, `declined`, `verify-failed` e o
  aceite (`skipped_reason=""`). Os quatro curto-circuitos do helper
  (`flag-disabled`, config `disabled`, `no-record`, SCM não resolvido) **não
  logam**: a feature nem foi exercitada. `no-record` é o caminho dominante de
  quem nunca rodou `gitpr -is` — logá-lo dobraria as linhas do fluxo de PR no
  ledger e faria as taxas de conclusão parecerem quase zero. `scm-error` não
  existe: `_resolve_scm_context` já imprime o erro, e o fluxo não publica.
- **Sem `status`.** O default é `"success"` (`metrics.py:125`), que é o Q14
  literal. `skipped_reason` já carrega o desfecho (inclusive `verify-failed`
  e `registry-error`); derivar `status="error"` criaria um segundo vocabulário
  para manter em sincronia e inflaria a taxa de erro para falhas transitórias
  de rede numa métrica "fire-and-forget". Os testes de chamada exata pinam a
  omissão.
- **Sem `warning` no payload.** Ele interpola texto de exceção e número de
  issue — exatamente o vazamento de privacidade que a métrica não pode ter. Só
  vão três campos booleanos/literais de vocabulário fixo.
- **`provider="git"`**, nunca `provider.name`: a coluna `provider` significa
  provedor de IA em todo o resto do ledger.
- **No helper, não no caso de uso:** `resolve_close_issue` é puro por contrato
  (T4) e pode ter outros chamadores.
- **Sem `try/except`:** `log_command_metric` é documentado como nunca levantar
  (`metrics.py:100-101`); um wrapper só esconderia quebra de contrato.

Estender o docstring de `_prepare_close_issue` com uma frase:

```python
    The outcome is also reported once to the local ledger as an
    ``issue_autoclose`` row (``asked``, ``accepted``, ``skipped_reason``).
```

### 2. i18n — verificação apenas

Nenhuma edição em `src/` para i18n e nenhuma em `langs/`. O único item de i18n
é rodar `tests/test_i18n.py` (auditoria AST: chave ausente, tradução
identidade, órfã, paridade). **Um diff em `langs/` é sinal de erro**, não de
progresso. Nada novo da T8 é string de usuário (uma chamada de métrica, um
docstring, testes).

### 3. Testes — `tests/issue_autoclose/test_close_issue_wiring.py`

**(a) `_run`** ganha um `Mock()` para `log_metric` e um `patch` de
`src.metrics.log_command_metric` (o alvo é o módulo de origem porque o import
do helper é local), exposto como `self.log_metric`. Continua devolvendo a
6-tupla.

**(b) `self.log_metric.assert_not_called()`** ao fim dos cinco testes de
curto-circuito já existentes: `test_disabled_flag_touches_nothing`,
`test_config_disabled_skips_before_the_registry_is_constructed`,
`test_config_disabled_wins_over_close_issue`,
`test_no_record_returns_before_the_forge`,
`test_scm_failure_is_reused_and_no_decision_is_made`. Nenhum outro teste
afirma chamada exata, então o log novo não os quebra.

**(c) Quatro testes novos** (depois de
`test_registry_error_still_reaches_the_warning`), todos com
`assert_called_once_with(...)` — que pina de uma vez "exatamente uma linha" e
o conjunto exato de campos (sem `status`, sem `warning`):

- pergunta respondida "sim" → `asked=True, accepted=True, skipped_reason=""`;
- `--close-issue` (sem pergunta) → `asked=False, accepted=True, skipped_reason=""`;
- pergunta recusada → `asked=True, accepted=False, skipped_reason="declined"`
  e `result[0] is None`;
- falha de verificação → `asked=False, accepted=False,
  skipped_reason="verify-failed"` (prova que só loga uma vez mesmo com aviso).

**Não** adicionar caso em `tests/test_metrics.py`: os testes genéricos de
payload já pinam o único comportamento não óbvio de que a T8 depende, e o
arquivo sozinho leva ~50 s.

## Arquivos

| Arquivo | Mudança |
|---|---|
| `src/main.py` | `_prepare_close_issue`: import local + `log_command_metric(...)` + frase no docstring |
| `tests/issue_autoclose/test_close_issue_wiring.py` | patch do métrico em `_run`, `assert_not_called` nos gates, 4 testes novos |
| `docs/claude-code/plans/feat/issue-autoclose/2026-11-03_feat_issue_autoclose_t8_i18n_metric.md` | cópia do plano aprovado |
| `docs/claude-code/reports/feat/issue-autoclose/2026-11-03_t8_issue_autoclose_i18n_metric.md` | relatório de conclusão obrigatório |

Nada em `langs/`, nada em `src/metrics.py`, nada em `src/ledger.py`, nada em
`src/ui/`.

## Verificação

1. `python -m pytest tests/issue_autoclose/test_close_issue_wiring.py -q`
   → **26 passed** (22 atuais + 4 novos).
2. `python -m pytest tests/issue_autoclose tests/test_i18n.py -q`
   → **142 passed, 56 subtests passed** (auditoria i18n = item 1).
3. `python -m pytest tests/test_metrics.py -q` → **164 passed** (inalterado;
   prova que o ledger aceita os campos no `payload`).
4. Suíte ampla como nas T1–T7 (sem `test_config_app.py`/`test_commit_app.py`,
   com a deseleção do teste de baseline que trava sem TTY), documentando as
   **8 falhas pré-existentes** de `tests/test_plugins.py` se reaparecerem
   (em isolamento: 17 passed).
5. Conferir que `git status` não mostra `langs/` nem `~/.gitpr/metrics/`.
6. Relatório com o commit sugerido e parada para confirmação. Nenhum
   `git add/commit/push`.

## Fora de escopo

- **T9:** README/ajuda da CLI, changelog, `docs/metricas-telemetria*.md`
  (exemplos de comando + documentar `asked`/`accepted`/`skipped_reason` como
  campos **só de payload**, ausentes de `CSV_COLUMNS`) e a atualização de
  `docs/config-tui.md` ("83 fields" → 85, "thirteen categories", linha da
  categoria Issue) nas 4 traduções.
- Rotas de funil adicionais (`no-record`, `flag-disabled`, `disabled`) no ramo
  do helper — podem vir depois, reusando o vocabulário do caso de uso se
  quiserem contar registros.
- `status` derivado, `scm-error`, `warning` no payload.

## Decisão pendente registrada

A divergência herdeira da T7 (o fluxo nunca emite `skipped_reason="disabled"`)
fica **resolvida**: a T8 é Opção A e não loga o ramo desligado; o valor segue
coberto pelo teste do caso de uso. Se o funil vier a existir, nasce no helper
com o mesmo literal.

## Commit sugerido

`feat: add issue autoclose metric`
