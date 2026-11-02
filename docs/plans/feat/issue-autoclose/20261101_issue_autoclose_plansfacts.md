# Plano de execução — Fechamento automático de issue (`close #N`)

- **Data:** 2026-11-01
- **Branch:** `feat/issue-autoclose` (a partir de `develop_natan`)
- **Fonte:** `docs/specs/issue-autoclose/` + decisões de grill registradas em
  `docs/survey/20261101_issue_autoclose_surveyfacts.md`
- **Modo:** uma tarefa por vez, com parada para confirmação; **nenhum commit automático**
  (regra do `CLAUDE.md`); ao fim de cada tarefa, testes verdes + mensagem Conventional
  Commits sugerida.

## Decisões que governam a implementação

| # | Tema | Decisão |
|---|---|---|
| Q5 | Inserção de `close #N` | Em `pr_desc_body` após a seção Explain (`src/main.py:1807-1813`), antes da escrita do `.md`; o badge é anexado depois em `attach_pr_badge` |
| Q6 | Momento da pergunta | Lazy: antes da TUI de stage, resolvendo provider/branch-alvo só quando há registro, feature ativa e provider GitHub |
| Q7 | Erros | `ScmProviderError` + `http_status` (404 limpa; 401/403/0/5xx avisam e mantêm) |
| Q8 | `.gitignore` | Acrescentar só `.gitpr/conf/github.yml` |
| Q9 | Gravação | `IssueApp.action_create_issue` → `register_created_issue(...)`; só GitHub |
| Q10 | Layout | Pacote `src/issue_autoclose/` |
| Q11 | Contexto | Variável local `close_issue` no `cli()` — sem `PrContext` |
| Q12 | Docs | Emendas datadas nos ADRs 001, 004 e 005 da SPEC |
| Q13 | Config | `GITPR_ISSUE_AUTOCLOSE` (bool, `true`), `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` (int, `5`), categoria `issue` |
| Q14 | Métricas | `log_command_metric(command="issue_autoclose", provider="git", asked=, accepted=, skipped_reason=)` no payload |
| Q15 | Glossário | "Issue registry" e "Closing line" no `CONTEXT.md` na tarefa que os cria |
| Q16 | Versão | Sem bump; só no release |

## T0 — Investigação (esta sessão)

Entregáveis, sem código de produção:

1. Branch `feat/issue-autoclose` criada.
2. `docs/survey/20261101_issue_autoclose_surveyfacts.md` com os dez itens e as divergências.
3. Este documento.
4. `docs/claude-code/reports/feat/issue-autoclose/2026-11-01_t0_issue_autoclose_investigation.md`.
5. Emendas datadas em `ADR-001`, `ADR-004` e `ADR-005`.
6. Suíte de base executada e registrada.
7. Relatório entregue no chat; parada para confirmação.

## T1 — Registro (`IssueRegistry`)

- `src/issue_autoclose/issue_registry.py`: `RegisteredIssue`, `load()`, `record(issue)`,
  `clear()`, `matches_repo(owner_repo)`.
- YAML `.gitpr/conf/github.yml`, `schema_version: 1`, campos do ADR-001.
- Escrita atômica pelo padrão `NamedTemporaryFile` + `os.replace`
  (`src/config.py:266-299`); arquivo corrompido: avisar, ignorar, sobrescrever na próxima gravação.
- `.gitignore`: `git check-ignore` e acréscimo idempotente de `.gitpr/conf/github.yml`,
  com aviso de uma linha. Sem rede.
- Termo "Issue registry" no `CONTEXT.md`.
- Testes: gravar/ler/limpar, escrita atômica, corrompido, `.gitignore` uma única vez.

## T2 — Extensão do `ScmProvider`

- `IssueInfo(number, title, url, state, is_pull_request)` em `src/infrastructure/scm/base.py`.
- `get_issue(repo, number, timeout=None)`, `get_default_branch(repo)`, `closing_line(number)`
  no ABC; demais providers levantam `NotImplementedError`.
- `GitHubProvider.get_issue`: `GET /repos/{o}/{r}/issues/{n}`, checando `pull_request`;
  `get_default_branch`: `GET /repos/{o}/{r}` → `default_branch`; `closing_line` → `close #N`.
- Timeout padrão 5 s, configurável; erros como `ScmProviderError` (`http_status`).
- Testes HTTP mockados: aberta, fechada, PR, 404, 403, timeout, 5xx.

## T3 — Gravação ao criar issue

- `src/issue_autoclose/register_created_issue.py`: função única chamada por
  `IssueApp.action_create_issue` após sucesso.
- Só provider GitHub; usa `IssueResult.number/url` + título, branch atual e `created_at`
  (`datetime.now().astimezone().isoformat()`), `repo` = `repo_ref.display`.
- Falha ao gravar: aviso de uma linha e segue.
- Testes: grava no caminho único; falha não quebra a criação.

## T4 — Caso de uso `resolve_close_issue`

- `src/issue_autoclose/resolve_close_issue.py`: função pura recebendo provider, registry,
  flags, `is_tty`, `target_branch`, `ask` injetável e logger.
- Árvore do passo 2.2 da SPEC; devolve `CloseIssueDecision | None` e o aviso de branch
  de destino quando aplicável.
- Testes: cada ramo (sem registro, outro repo, aberta com TTY sim/não, sem TTY,
  `--close-issue`, `--no-close-issue`, falha de rede, branch diferente da padrão).

## T5 — Inserção no corpo do PR

- Helper em `src/issue_autoclose/` aplicado em `pr_desc_body` após a seção Explain
  (`src/main.py:1807-1813`), antes da escrita do `.md`.
- Texto `close #N` em linha própria, separado por linha em branco; sem duplicar.
- Idempotência: regex insensível a maiúsculas, limite de palavra, `close(s|d)?`,
  `fix(es|ed)?`, `resolve(s|d)?` + `#N` (opcional `owner/repo#N`); `#12` não casa com `#123`.
- Testes: antes do badge, sem badge, com seção Explain, variações de keyword e número.

## T6 — Integração no fluxo `gitpr`

- Antes de `src/main.py:1628`: se a feature está ativa e `--no-close-issue` ausente,
  lê o registro; sem registro ou de outro repo, sai sem custo. Com registro: resolve
  provider e branch-alvo (reutilizando a resolução depois) e chama `resolve_close_issue`.
- Guarda a decisão em variável local; aplica em T5.
- Flags `--close-issue` / `--no-close-issue` mutuamente exclusivas, com erro claro.
- Limpa o registro após PR criado quando a linha foi aplicada ou já estava presente;
  mantém em "não", falha ou cancelamento.
- Testes: ciclo de vida, flags conflitantes, não-regressão sem registro (nenhuma chamada de rede extra).

## T7 — Configuração e TUI "config"

- `GITPR_ISSUE_AUTOCLOSE` e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` em `src/config_schema.py`
  (categoria `issue`), getter em `src/config.py` no modelo de `badge_enabled()`.
- Opção de ligar/desligar na TUI `config` (widget `Switch` já existente para `KIND_BOOL`).
- Testes do schema e da conversão de valores.

## T8 — i18n e metrics

- Chaves nos 6 arquivos de `langs/` (pergunta, aviso de branch, falha de verificação,
  aviso de `.gitignore`, erro de flags conflitantes) via `tests/sync_i18n.py` + tradução real.
- Auditoria `tests/test_i18n.py` verde.
- Evento `issue_autoclose` no payload; sem dados sensíveis.
- Testes: auditoria de idiomas, evento registrado.

## T9 — Documentação

- README/ajuda da CLI: comportamento, flags e arquivo de registro.
- Nota no changelog **sem bump de versão** (Q16).
- Termos "Issue registry"/"Closing line" confirmados no `CONTEXT.md`.

## Verificação global (fim da T9)

- Suíte completa verde: `python -m pytest tests/ -q`.
- Nenhum `requests`/HTTP novo fora do provider.
- Nenhuma chave de i18n faltando.
- Teste manual da seção 12 da SPEC (repositório real no GitHub, executado pelo usuário).
