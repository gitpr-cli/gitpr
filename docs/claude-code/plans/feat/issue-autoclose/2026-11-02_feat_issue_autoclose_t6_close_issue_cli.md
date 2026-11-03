# Plano — T6: integração do issue-autoclose no fluxo `gitpr`

## Contexto

As T1–T5 entregaram a base da feature: o registro local (`IssueRegistry`), a
gravação após `gitpr -is`, a decisão `resolve_close_issue` (verificação no
forge + pergunta), a linha por forge (`closing_line`) e a inserção idempotente
no ponto único de montagem do corpo (`insert_close_line`, já chamado em
`src/main.py` com `close_issue_decision`, hoje sempre `None`).

Falta o que o SPEC define para a T6 e o que os ADRs 003/005/006/007 exigem:

- perguntar antes da TUI de stage, com provider/branch-alvo resolvidos de forma
  **lazy** (só quando há registro para o repositório atual);
- preencher `close_issue_decision` para o corpo do PR;
- imprimir o aviso de verificação (`outcome.warning`) uma única vez;
- limpar o registro quando o PR é criado com a linha aplicada (ou já presente)
  e **manter** em recusa, cancelamento, falha de publicação e `--no-publish`;
- flags `--close-issue` / `--no-close-issue`, mutuamente exclusivas com erro
  claro.

## Abordagem

### 1. Flags e erro de exclusividade

Em `src/main.py`, depois de `--explain` (decorators ~648-655):

```python
@click.option("--close-issue", is_flag=True, help=__("..."))
@click.option("--no-close-issue", is_flag=True, help=__("..."))
```

Parâmetros `close_issue` e `no_close_issue` no `cli()`.

Validação **logo após `log_usage()`** (topo do callback), nunca depois:

```python
if close_issue and no_close_issue and not help_flag:
    click.secho(
        __("❌ --close-issue and --no-close-issue cannot be used together."),
        fg="red",
        err=True,
    )
    raise click.exceptions.Exit(1)
```

- Antes de `ensure_ledger`, do seed do projeto e do update gate: um erro de uso
  não pode disparar pergunta de migração nem escrever arquivo.
- `not help_flag` mantém `gitpr -h --close-issue --no-close-issue` mostrando a
  ajuda (a validação nunca rouba a saída de help).
- Subcomandos também recebem o erro (a combinação é inválida em qualquer uso).
- Três chaves i18n novas, traduzidas nos 6 arquivos `langs/*.json` —
  `tests/test_i18n.py` reprova chave ausente e valor idêntico ao inglês.
  Inserção ordenada, preservando CRLF e o formato `indent=2`:
  - `"Adds the closing line (close #N) to the Pull Request description without asking; the issue is still checked."`
  - `"Skips the automatic issue closure for this run (no record is read and no forge call is made)."`
  - `"❌ --close-issue and --no-close-issue cannot be used together."`

### 2. Decisão antes da TUI de stage — `_prepare_close_issue`

Novo helper em `src/main.py` (perto de `_resolve_scm_context`), com imports
locais dos módulos da feature (padrão do `main.py` para features; permite o
patch nos módulos de origem nos testes):

```python
def _prepare_close_issue(flags, base, may_ask):
    """Lê o registro cedo e decide a closing line antes da TUI de stage.

    Devolve (decision, registry, scm_context): registry é o que a limpeza
    usará depois do PR; scm_context é o (provider, repo_ref) resolvido aqui
    para o resto do fluxo reutilizar, ou None quando nada o exigiu.
    """
```

Comportamento, na ordem:

1. `flags.disabled` → `(None, None, None)` (nenhuma leitura, nenhuma rede).
2. `IssueRegistry()` + `load()` (uma leitura barata, sempre; sem registro e sem
   erro → `(None, None, None)` — é a não-regressão: nenhum provider, nenhuma
   chamada ao forge).
3. Se há registro (ou erro de leitura): `_resolve_scm_context()` **uma vez**,
   guardado em `scm_context` (inclusive `(None, None)` em falha, para o fluxo
   não repetir a mensagem de erro).
4. Provider `None` → `(None, None, scm_context)`.
5. `target_branch` só quando a pergunta pode acontecer (`may_ask and not
   flags.accept`): `resolve_pull_request_base(base, verify=False).branch`, em
   try/except (leitura barata, sem picker e sem validação; usada **apenas** no
   aviso de branch do ADR-005).
6. `resolve_close_issue(provider, registry, repo_ref, flags=flags,
   is_tty=may_ask, target_branch=target_branch,
   ask=lambda q, default=True: click.confirm(q, default=default))`.
   `enabled`/`timeout` ficam nos defaults da T4 (chaves são da T7).
7. `outcome.warning` → `click.secho(..., fg="yellow", err=True)` uma vez.
8. `(outcome.decision, registry, scm_context)`.

O `resolve_close_issue` relê o registro (duas leituras locais). Aceito:
evita mudar o contrato da T4 por um ganho irrelevante.

Chamada no ramo do PR (`src/main.py` ~1627), substituindo o seam
`close_issue_decision = None` e **antes** de `check_unstaged_files`:

```python
from src.issue_autoclose.resolve_close_issue import CloseIssueFlags

close_issue_decision, close_issue_registry, scm_context = _prepare_close_issue(
    CloseIssueFlags(accept=close_issue, disabled=no_close_issue), base, may_ask
)
```

No ponto existente de resolução do SCM (~1850):

```python
provider, repo_ref = scm_context or _resolve_scm_context()
```

`(None, None)` é uma tupla não vazia (truthy): a falha resolvida cedo é
reutilizada e a mensagem não aparece duas vezes.

### 3. Limpeza do registro (ADR-007)

Helper em `src/main.py`, ao lado de `_publish_pr_directly`:

```python
def _clear_close_issue_record(registry, decision):
    """Esquece a issue registrada quando o PR publicado carrega a linha."""
    if registry is None or decision is None:
        return
    try:
        registry.clear()
    except Exception:
        pass
```

- `decision is None` cobre recusa, no-tty, issue fechada/PR/inexistente e
  registro de outro repositório: nada a limpar.
- Falha ao remover nunca quebra o fluxo.

`_publish_pr_directly` passa a devolver `bool`: `False` nos dois ramos de
falha (401 e erro genérico) e `True` após o sucesso (métrica já registrada).
O único chamador de produção (`src/main.py:1899`) e o teste de
`tests/badge/test_badge_paths.py` ignoram o retorno — compatível.

Ramo `--no-edit`:

```python
if _publish_pr_directly(...):
    _clear_close_issue_record(close_issue_registry, close_issue_decision)
return
```

TUI: `PrPublishApp` ganha `self.body_published = False` no `__init__`, e só
vira `True` quando o corpo **foi enviado**:

- `_publish_pr_from_progress`, no `if ok:` (criação real);
- `_push_and_exit`, dentro do `try` do `update_pull_request` bem-sucedido
  (a atualização do PR existente publica a linha).

O ramo "No, Just Open Existing" também usa `final_action = "created"`, mas não
publica o corpo — por isso o sinal dedicado, e não `final_action`.

Depois do `app.run()` e do bloco de reauth (antes da mensagem final):

```python
if app.body_published:
    _clear_close_issue_record(close_issue_registry, close_issue_decision)
```

Mantêm o registro: recusa, cancelamento (Esc), falha de criação/atualização,
`--no-publish` (não publica), reauth sem publicação e `--close-issue` sem
sucesso de publicação.

## Arquivos

| Arquivo | Mudança |
|---|---|
| `src/main.py` | flags + validação, `_prepare_close_issue`, cache do SCM, `_clear_close_issue_record`, `_publish_pr_directly` → bool, chamadas de limpeza |
| `src/ui/pr_publish_app.py` | `body_published` (init + criação + atualização) |
| `langs/{es,es_es,fr,fr_fr,pt_br,pt_pt}.json` | 3 chaves novas traduzidas |
| `tests/issue_autoclose/test_close_issue_wiring.py` | novo: helper, flags, não-regressão, `_publish_pr_directly`, limpeza |
| `tests/test_pr_publish_app.py` | `body_published` na criação, na atualização e no "just open existing" |
| `docs/claude-code/plans/feat/issue-autoclose/2026-11-02_feat_issue_autoclose_t6_close_issue_cli.md` | cópia do plano aprovado (regra do CLAUDE.md) |
| `docs/claude-code/reports/feat/issue-autoclose/2026-11-02_t6_issue_autoclose_cli.md` | relatório de conclusão obrigatório |

## Testes

`tests/issue_autoclose/test_close_issue_wiring.py` (unittest, fakes simples —
`Mock` cria `.name` truthy e quebra `provider_is_github`):

- `PrepareCloseIssueTest`, com patch em
  `src.issue_autoclose.issue_registry.IssueRegistry`,
  `src.issue_autoclose.resolve_close_issue.resolve_close_issue`,
  `src.main._resolve_scm_context` e
  `src.project_config.resolve_pull_request_base`:
  - `--no-close-issue` → nada lido, nada resolvido;
  - sem registro → sem `_resolve_scm_context`, sem `resolve_close_issue`;
  - com registro → SCM resolvido uma vez, flags/`is_tty`/`target_branch`
    repassados, decisão devolvida junto do registry e do `scm_context`;
  - `--close-issue` e `may_ask=False` → branch-alvo não é lida;
  - pergunta possível → `resolve_pull_request_base(base, verify=False)` e
    branch repassada;
  - aviso impresso exatamente uma vez (amarelo, stderr);
  - falha do SCM → decisão não tentada e `(None, None)` reutilizado;
  - erro de leitura do registro → aviso do T4 propagado.
- `CloseIssueFlagsCliTest` (`CliRunner`):
  - as duas flags juntas → exit 1 + mensagem;
  - `gitpr -h` lista `--close-issue` e `--no-close-issue`;
  - `-h` com as duas flags → exit 0 (help vence);
  - **não-regressão (SPEC #8):** fluxo padrão sem registro, com
    `check_unstaged_files` interrompendo o fluxo → exit 0, `_resolve_scm_context`
    e `resolve_close_issue` nunca chamados.
- `PublishDirectlyResultTest`: sucesso → `True`; erro 500 e 401 → `False`
  (padrão de `tests/badge/test_badge_paths.py`, patchando o use case, o
  `click.confirm`, a métrica e `get_current_branch`).
- `ClearRecordTest`: registry/decisão `None` → não limpa; ambos presentes →
  `clear()` uma vez; `clear()` que lança → engolido.

`tests/test_pr_publish_app.py`:

- `body_published` começa `False` na construção;
- `True` em `test_publish_without_view_never_attaches` (criação);
- `True` em `test_update_path_attaches_reviewers_after_update` (atualização);
- novo caso: `_on_existing_pr_before_push_result("no", url, n)` com
  `_prompt_open_browser` mockado → `final_action == "created"` mas
  `body_published is False`.

## Verificação

- `python -m pytest tests/issue_autoclose tests/scm -q`
- `python -m pytest tests/test_pr_publish_app.py -q`
- `python -m pytest tests/test_i18n.py -q`
- `python -m pytest tests/badge tests/test_diff_failure_cli.py -q`
- Suíte ampla como nas T4/T5 (sem `tests/test_config_app.py` e
  `tests/test_commit_app.py`, com a deseleção do teste de baseline que trava
  sem TTY).
- Relatório em `docs/claude-code/reports/feat/issue-autoclose/`
  `2026-11-02_t6_issue_autoclose_cli.md`, com o commit sugerido
  (`feat: wire issue autoclose into the PR flow`) e parada para confirmação.
- Nenhum `git add/commit/push`.

## Fora de escopo

- T7 (`GITPR_ISSUE_AUTOCLOSE` / `..._TIMEOUT` no schema e na TUI config).
- T8 (métrica `issue_autoclose`; nenhuma métrica nova aqui).
- T9 (documentação de usuário e entradas no help contextual `HELP_MAP`).
- MCP, chat e forges não-GitHub.

## Decisões de desenho

1. **Sinal `body_published`, não `final_action`** — `"created"` também é usado
   ao apenas abrir um PR existente, quando o corpo não é publicado; limpar ali
   violaria o ADR-007.
2. **Branch-alvo antecipada = leitura barata** — a resolução validada (com
   picker e gravação do arquivo do projeto) continua em `_resolve_pr_target`
   no ponto de publicação. Reutilizar a leitura barata depois pularia a
   validação e o picker do ADR-015. O "reutilizada" do ADR-005 é honrado pelo
   provider/`repo_ref` (`scm_context`); a branch antecipada existe só para o
   aviso da pergunta.
3. **Duas leituras do registro** — a T4 não muda; o arquivo é local e pequeno.
4. **Pergunta também em `--no-publish`** — o ADR-004 determina que o `.md`
   local e o `--no-publish` recebem a linha; o registro não é limpo porque não
   há publicação.
5. **401 na verificação inicial** — aviso do ADR-003 e registro mantido; o
   token só é pedido depois (fluxo atual), e o corpo sai sem a linha nessa
   execução. É o comportamento especificado para verificação falha.
