# Survey — Fechamento automático de issue no PR (`close #N`)

- **Data:** 2026-11-01
- **Branch:** `feat/issue-autoclose` (criada a partir de `develop_natan`)
- **Fonte da especificação:** `docs/specs/issue-autoclose/` (glossário, ADR-001..007, entrevista, `00-SPEC.md`)
- **Escopo desta sessão:** T0 — investigação, sem código de produção

## 1. Contexto da tarefa

O `PROMPT-CLAUDE-CODE.md` manda executar a SPEC uma tarefa por vez, começando pela T0
(investigação) e aguardando confirmação. A T0 pede dez verificações no código real e uma
lista de divergências em relação à SPEC. As decisões que a T0 levantou foram levadas ao
usuário em quatro rodadas de grill e estão registradas abaixo; nenhuma foi assumida em
silêncio.

Resumo do pedido original: ao criar uma issue com `gitpr -is` (provider GitHub), registrar
o número em `.gitpr/conf/github.yml`; no `gitpr` seguinte, se a issue registrada ainda
estiver aberta, perguntar se deve adicionar `close #N` à descrição do PR, antes do badge.

## 2. Decisões confirmadas (4 rodadas de grill)

### Rodada 1 — protocolo de execução

| # | Tema | Decisão |
|---|---|---|
| Q1 | Commits | Seguir o `CLAUDE.md`: **nenhum** `git add/commit/push`. Cada tarefa termina com testes verdes e a mensagem Conventional Commits sugerida |
| Q2 | Branch | Criar `feat/issue-autoclose` a partir de `develop_natan` |
| Q3 | Escopo | Somente T0; parar e aguardar confirmação |
| Q4 | Artefatos | Survey + plan + completion report, em português, sob a branch |

### Rodada 2 — divergências entre SPEC/ADRs e código

| # | Tema | Decisão |
|---|---|---|
| Q5 | Inserção de `close #N` | Em `pr_desc_body` após a seção "Explain my PR" (`main.py:1807-1813`): o `.md`, a TUI e o `--no-edit` recebem; o badge é anexado depois |
| Q6 | Momento da pergunta | Lazy: antes da TUI de stage, mas só resolve provider/branch-alvo quando há registro e a feature está ativa; sem registro, custo zero |
| Q7 | Erros do provider | Sem classes novas — `ScmProviderError` + `http_status` (404 limpa; 401/403/0/5xx avisam e mantêm). Desvio da T2 registrado |
| Q8 | `.gitignore` | Acrescentar só `.gitpr/conf/github.yml` (não `.gitpr/conf/`) |

### Rodada 3 — estrutura

| # | Tema | Decisão |
|---|---|---|
| Q9 | Gravação (T3) | Dentro de `IssueApp.action_create_issue`, via `register_created_issue(...)`; MCP/chat não criam issue |
| Q10 | Layout | Pacote de feature `src/issue_autoclose/` (precedente: `src/fix/fix_history.py`) |
| Q11 | PrContext | Não existe e não será criado: variável local no fluxo `cli()` |
| Q12 | Divergências nos docs | Emendar os ADRs afetados com nota datada "Revisão T0 (2026-11-01)" |

### Rodada 4 — configuração, métricas, glossário, versão

| # | Tema | Decisão |
|---|---|---|
| Q13 | Config (T7) | `GITPR_ISSUE_AUTOCLOSE` (bool, default `true`) e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` (int, default `5`), categoria `issue` |
| Q14 | Métricas (T8) | `log_command_metric(command="issue_autoclose", provider="git", asked=, accepted=, skipped_reason=)` — vai para o `payload`, sem schema novo |
| Q15 | Glossário | Acrescentar "Issue registry" e "Closing line" ao `CONTEXT.md` quando cada termo for implementado |
| Q16 | Versão | Sem bump nesta feature; só no release |

## 3. Relatório de fatos levantados (os dez itens da T0)

### 3.1 Onde `gitpr -is` cria a issue e onde o número fica disponível

- Rota do `-is` no CLI: `src/main.py:1273-1448`; `IssueApp` construída em `src/main.py:1420`.
- Chamada real do provider: `src/ui/issue_app.py:137-140` →
  `IssueResult(id, url, number, provider)` (`src/infrastructure/scm/base.py:117-124`).
- O número **se perde**: só `result.url` é usado (`src/ui/issue_app.py:142-151`);
  `src/main.py:1444-1446` lê apenas `app.final_action` e `app.final_message`.
- Outros caminhos que criam issue no GitHub: **nenhum**.
  - MCP `generate_issue` só gera texto (`src/mcp_server.py:905-957`), sem provider.
  - Chat (`-ch` / `src/ui/chat_app.py`) não tem `ScmProvider` nem `create_issue`.
  - Azure DevOps levanta `ScmNotSupportedError` (`src/infrastructure/scm/azure_devops_provider.py:445`).
- `provider.create_issue(...)` tem um único chamador de produção: `src/ui/issue_app.py:137`.

### 3.2 Interface atual de `ScmProvider` e `GitHubProvider`

- `ScmProvider` (`src/infrastructure/scm/base.py:153`): **não** possui `get_issue`,
  `get_default_branch` nem `closing_line`. Possui `create_issue` (`:255`, abstrato) e
  `get_pull_request` (`:303`, concreto, padrão `ScmNotSupportedError`).
- `GitHubProvider.create_issue` (`src/infrastructure/scm/github_provider.py:447-463`):
  `POST /repos/{workspace}/{name}/issues`, espera 201, timeout 15; devolve
  `IssueResult(id=j["number"], url=j["html_url"], number=j["number"], provider="github")`.
- HTTP: `requests` direto, sem `Session`, via `_request` (`:122-146`); headers em
  `_headers` (`:97-101`); erros viram `ScmProviderError(provider, http_status, message)`,
  com `http_status == 0` para falha de transporte (`base.py:127-140`).
- Detecção de GitHub: `provider_is_github()` (`src/infrastructure/scm/factory.py:95-97`).

### 3.3 Ponto único de montagem final do corpo do PR e o badge

- Corpo: `pr_desc_body` em `src/main.py:1805`; seção Explain anexada em `:1807-1813`;
  `.md` escrito em `:1823-1825`; `pr_data` montado em `:1847-1850`;
  `--no-publish` retorna em `:1853`.
- Badge: `attach_pr_badge(pr_data, diff_text)` em `src/main.py:1875` →
  `src/branding/badge_builder.py:121-139`; `append_badge` (`:105-118`) coloca
  `\n\n---\n\n{badge}` ao fim.
- **Não existe selo "Reviewed by GitPR".** O badge é o shields.io de contagens do linter
  (marcador `img.shields.io/badge/GitPR`, `badge_builder.py:30`).
- `--no-edit` publica por `_publish_pr_directly` (`src/main.py:5837`); a TUI publica em
  `src/ui/pr_publish_app.py:1645` (o corpo é relido do `TextArea`).
- O MCP também chama `attach_pr_badge` (`src/mcp_server.py:1446`) — fora do escopo.

### 3.4 Início do fluxo `gitpr` padrão e onde cabe a pergunta

Ordem real do fluxo padrão:

1. `setup_environment()` em `src/main.py:1561`.
2. `action_type = "pr"` em `:1627`; TUI de stage em `:1628` via `check_unstaged_files`
   → `StageFilesApp` (`src/main.py:5565-5568`, `src/ui/pr_publish_app.py:277`).
3. `get_git_full_diff()` em `:1633`.
4. Geração por IA em `:1657-1663`.
5. Explain + `.md` em `:1805-1825`.
6. Provider resolvido em `:1840` (`_resolve_scm_context`).
7. `--no-publish` retorna em `:1853`.
8. Branch-alvo em `:1862` (`_resolve_pr_target`).
9. Badge em `:1875`.
10. `--no-edit` publica direto em `:1878-1890`; senão, TUI de publicação em `:1936`.

Conclusão: a pergunta, para cumprir o ADR-005, entra antes de `src/main.py:1628`; como
provider e branch-alvo só são resolvidos em `:1840`/`:1862`, a resolução precisa ser
antecipada **apenas** no caminho com registro (decisão Q6).

### 3.5 Como a branch de destino é configurada e lida

- Resolvedor único: `resolve_pull_request_base` (`src/project_config.py:380-421`), com
  precedência `--base` > arquivo do projeto > `PR_DEFAULT_BASE` > `origin/HEAD` > `main`.
- Verificação (`verify_remote_base`, `:339-377`) é local: `git rev-parse refs/remotes/origin/<branch>`.
- Wrapper do CLI: `_resolve_pr_target` (`src/main.py:439-485`); pode abrir o picker
  `src/ui/pr_base_app.py` quando a base configurada é a branch atual (interativo).
- Arquivo do projeto: `.gitpr/conf/gitpr.config.yml` (`src/project_config.py:31`), versionado.

### 3.6 A TUI "config"

- Comando `gitpr config` → `src/main.py:2243` → `launch_config_app()`
  (`src/ui/config_app.py:2041`); app em `:632`.
- Declaração: `ConfigField` e `FIELDS` em `src/config_schema.py:94/294`; `KIND_BOOL` em
  `:23`; stores `env`/`project` em `:58-64`; categorias (incluindo `issue`) em `:152+`.
- Persistência: `save_config_values` (`src/config.py:1265-1277`, `dotenv.set_key`);
  projeto em `write_project_field_values` (`src/project_config.py:199-253`).
- Precedentes: `GITPR_BADGE` (`config_schema.py:324-333`, bool, default `true`) e
  `GITPR_EXPLAIN_BY_DEFAULT` (`:559-568`, bool, default `false`).

### 3.7 Sistema de i18n e o teste de auditoria

- `__()` em `src/i18n.py:116-129`; **a string em inglês é a chave**; inglês não precisa de arquivo.
- Arquivos versionados em `langs/`: **seis** — `es.json`, `es_es.json`, `fr.json`,
  `fr_fr.json`, `pt_br.json`, `pt_pt.json` (os pares `es`/`es_es` e `fr`/`fr_fr` são duplicados).
- Auditoria em `tests/test_i18n.py`: paridade de chaves (`:147-158`), chaves ausentes
  (`:282-292`), órfãs (`:294-303`) e identidade/tradução obrigatória (`:237-262`).
- Ferramenta de sincronização: `python tests/sync_i18n.py`.

### 3.8 Detecção de TTY e modo não interativo

- Helper único: `_may_ask_the_user()` (`src/main.py:63-75`) — exige `stdin` e `stdout`
  TTY e respeita `--quiet`/`--hook`/`--mcp`.
- Sinal de ledger: `configure_terminal(interactive=...)` (`src/ledger.py:430`).
- `click.confirm` **não** checa TTY por conta própria; os gates são explícitos.
- Vocabulário do projeto: "Interactive run" em `CONTEXT.md`.

### 3.9 YAML e estado local

- PyYAML já é dependência (`pyproject.toml:20`); leitura/escrita em
  `src/project_config.py:150-253` (leitura tolerante, escrita **não atômica**).
- Padrão atômico a reutilizar: `write_skill_file` (`src/config.py:266-299`,
  `NamedTemporaryFile` + `os.replace`) e `local_baseline_repository.py:191-211`.
- `.gitpr/conf/` **existe**; `gitpr.config.yml` é **versionado**; o `.gitignore` só ignora
  `.gitpr/metrics/`. `github.yml` não existe.
- `src/infrastructure/state/` não existe; o pacote novo será `src/issue_autoclose/`.

### 3.10 Padrão de testes e de métricas

- SCM: `tests/scm/test_github_provider.py` — helper `_response` (`:35-42`),
  `@patch("src.infrastructure.scm.github_provider.requests.post")`, casos 201/404/401/
  403/5xx/`ConnectionError`/`Timeout`.
- `tests/conftest.py` fixa o ambiente antes de importar o projeto (idioma `en_us`,
  skip de update e de seed, linter security off).
- Métricas: `log_command_metric` (`src/metrics.py:123-171`); kwargs desconhecidos vão para
  a coluna `payload` — precedente em `tests/test_metrics.py:307-312`; fixture `home` em
  `:57-79`. Schema do ledger em `src/ledger.py:67-98`; nenhuma migração necessária.

## 4. Divergências SPEC × código e resolução

| # | Divergência | Resolução |
|---|---|---|
| D1 | O glossário fala em badge "Reviewed by GitPR"; o real é o shields.io do linter | Q5: a linha entra após a seção Explain; o badge continua sendo anexado depois |
| D2 | ADR-005 exige a pergunta antes da TUI de stage, mas provider/base são resolvidos depois | Q6: resolução lazy, só com registro |
| D3 | O `.md` é escrito antes do badge; `--no-publish` sai antes do badge | Q5: inserir no corpo antes da escrita do `.md` |
| D4 | T3 fala em "todos os caminhos de criação"; só `IssueApp` cria issue | Q9: gravar no `IssueApp`; MCP/chat registrados como não-caminhos |
| D5 | T2 pede exceções tipadas; a convenção é `ScmProviderError` | Q7: usar `http_status` |
| D6 | ADR-001 manda ignorar `.gitpr/conf/`, que contém arquivo versionado | Q8: ignorar só `github.yml` |
| D7 | T7 usa chaves pontuadas; o schema real é `GITPR_*` plano | Q13: `GITPR_ISSUE_AUTOCLOSE` e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` |
| D8 | "5 idiomas" são, na prática, 6 arquivos | Implementar e traduzir nos 6 |
| D9 | `PrContext` não existe no código | Q11: variável local no fluxo |
| D10 | A SPEC sugere `src/infrastructure/state/` | Q10: pacote `src/issue_autoclose/` |
| D11 | O MCP também monta corpo com badge | Inserção fica no fluxo `cli()`; MCP fora do escopo |
| D12 | `--close-issue` sem TTY ainda verifica a issue (ADR-005) | Mantido: verifica, não pergunta |

## 5. Suíte de base

Executada na branch `feat/issue-autoclose`, sem alterações de código:

```
python -m pytest tests/ -q --deselect "tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched"
→ 3125 passed, 2 skipped, 1 deselected, 138 subtests passed in 442.33s
```

O único teste desselecionado é pré-existente e alheio a esta feature: ele invoca
`gitpr -c` sem `--hook`, e o CLI abre a TUI `CommitApp` (`src/main.py:1591-1596`); neste
ambiente Windows sem TTY o driver Textual bloqueia em `wait_for_handles`. O pipeline de
CI roda em Linux. Com o teste incluído, a suíte fica presa nele.

## 6. Perguntas pendentes

Nenhuma decisão de projeto em aberto. Ficam para a execução:

- T1–T9 aguardam confirmação do usuário, uma tarefa por vez.
- O teste manual da seção 12 da SPEC exige um repositório real no GitHub com rede e será
  de responsabilidade do usuário ao final da T9.
