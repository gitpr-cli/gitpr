# Survey — Forge por repositório e token por provider

- **Branch:** develop_natan
- **Data:** 2026-11-07
- **Método:** `/grill-with-docs` (grilling + domain-modeling), três rodadas de entrevista,
  duas explorações de código e uma rodada de design.

## 1. Contexto da tarefa

Relato do usuário: ao rodar o wizard num repositório GitLab, o GitPR gravou
`GITPR_SCM_PROVIDER=gitlab` no `~/.gitpr/.env`. De volta a um projeto GitHub, o
GitPR não reconhece o forge — o provider global tem precedência sobre a detecção
do remote. O token também é um só (`GITPR_SCM_TOKEN_ENCRYPTED`).

Pedido: detectar o forge do repositório em execução, pedir o PAT correspondente,
salvar um token por provider (`GITHUB_TOKEN_ENCRYPTED`, `GITLAB_TOKEN_ENCRYPTED`, …)
e usar o provider correto.

## 2. Decisões por rodada

### Rodada 1 — raiz da árvore

| Pergunta | Decisão |
|---|---|
| Onde vive o override manual, já que a detecção por substring falha em self-hosted (`git.acme.com`)? | Detectar sempre; override no `.gitpr/conf/gitpr.config.yml` (arquivo de projeto, versionado). `GITPR_SCM_PROVIDER` deixa de ser escrito. |
| Esquema de nomes dos tokens | Só o cifrado, por provider; `GITPR_SCM_TOKEN` cru continua global para CI. |
| Destino dos valores globais existentes | Migração automática one-shot. |
| Escopo das variáveis extras | Só `base_url` por provider; org/project/username ficam globais (cada um lido por um único provider). |

### Rodada 2 — contrato de resolução

| Pergunta | Decisão |
|---|---|
| Override do projeto vs. remote reconhecível | Override explícito sempre vence. |
| Token ausente no forge detectado | Pedir na hora, só em execução interativa; hooks/MCP/CI falham apontando `--init`. |
| Papel do `--init` | Wizard por repositório; grava override só quando o forge difere da detecção. |
| Tela `gitpr config` | Atualizar: provider no store de projeto, quatro tokens, quatro base URLs. |

### Rodada 3 — migração e alcance

| Pergunta | Decisão |
|---|---|
| Chaves antigas depois da migração | Removidas do schema, do seed, da TUI e das leituras. |
| Gatilho da migração | No resolvedor, na primeira chamada, idempotente. |
| `GITPR_SCM_BASE_URL` legado | Migra junto para `<PROVIDER>_BASE_URL`. |
| Superfícies afetadas | Todas as cinco (PR/issues, `release --publish`, `metrics`, MCP). |
| Documentação | ADR-016 + nota no ADR-001 + glossário SCM. |
| Forma no YAML | Só gravar `scm.provider` quando houver override. |
| Conflito na migração | Nunca sobrescrever um `<PROVIDER>_TOKEN_ENCRYPTED` já existente. |

## 3. Fatos levantados no código

### Configuração e credenciais

- `src/config.py:891-942` — `get_github_token()`, `get_scm_token()`, `get_scm_settings()`, `get_scm_provider()` (esta nunca chamada). Todas leem um slot único.
- `src/config.py:1198-1225` — `save_config_values()` e `remove_config_value()`: o escritor genérico de `.env` que a migração pode reusar.
- `src/config.py:503-596` — `setup_environment()` semeia `DEFAULT_CONFIG`; **não** roda em toda execução (só em `src/main.py:2445, 2801, 3009`).
- `src/security.py` — `encrypt_data` / `decrypt_data`; esta última engole exceções e devolve `""`.
- `~/.gitpr/.env` é o único store; `GITHUB_TOKEN_ENCRYPTED` **não** é semeado, `GITPR_SCM_*` são.

### Factory e providers

- `src/infrastructure/scm/factory.py:24-33` — `_REGISTRY` e `_EXTRA_KEYS`.
- `factory.py:40-61` — `resolve_scm_provider()`; o token explícito vence, e só GitHub cai no `GITHUB_TOKEN_ENCRYPTED` (fallback lazy).
- `factory.py:61` — `base_url` é repassado a **todos** os providers: a raiz do segundo vazamento.
- `factory.py:64-77` — `detect_provider_from_remote()`, substring, desconhecido → `github`.
- `base.py:199-202` — `self.token`, `self.base_url`, `self.extra`; `base.py:419-421` — `with_token()` preserva `base_url` e extras.
- Bitbucket exige `username` no construtor; Azure exige `organization` + `project` (fail-fast com o nome da variável na mensagem).

### Consumidores

- `src/main.py:4443` — release publish.
- `src/main.py:11841-11923` — `_resolve_scm_context`; detecta somente quando `GITPR_SCM_PROVIDER` está vazio (linha 11891-11893) — o bug.
- `src/release_engine.py:383` — resolução de logins de contribuidores.
- `src/metrics.py:886` — métrica de ciclo.
- `src/mcp_server.py:1082` — contexto do MCP, também detecta só quando o provider está vazio.

### Wizards e TUI

- `src/core.py:2269-2443` — `run_scm_init_wizard()`; persiste `GITPR_SCM_PROVIDER` + `GITPR_SCM_TOKEN_ENCRYPTED` (2414-2415) só após validação.
- `src/core.py:2129-2260` — `run_install_wizard()` **não** toca em token de forge (só chave de IA).
- `src/tui_issue.py:45-54` — `_token_env_var()` escolhe entre `GITHUB_TOKEN_ENCRYPTED` e `GITPR_SCM_TOKEN_ENCRYPTED`.
- `src/tui_issue.py:171-281` — `validate_or_request_scm_token()`; pergunta, valida, salva e remove token expirado.
- `src/ui/config_app.py:2020-2056` — `_probe_scm_token()` valida contra o estado planejado de `GITPR_SCM_PROVIDER`.
- `src/config_schema.py:1151-1251` — bloco SCM; `store=STORE_PROJECT` já existe e é plenamente suportado pela TUI (`config_app.py:920, 1163, 1184, 1917`), com `PROJECT_BASE_BRANCH` como exemplar (`config_schema.py:600-638`).
- `src/project_config.py` — `_run_git`, `project_config_path`, `read_project_config` (nunca levanta), `write_project_field_values` (preserva as demais chaves, recusa sobrescrever YAML não-mapping).

### Testes que fixam o comportamento atual

- `tests/scm/test_factory.py` — tabela de detecção; desconhecido → `github`.
- `tests/scm/test_init_wizard.py` — exatamente dois `set_key` no caminho GitHub; `assert_not_called()` em toda falha.
- `tests/test_config_app.py::TestForgeSections`, `tests/test_config_schema.py`, `tests/test_project_config.py` — visibilidade e store de projeto.
- `tests/test_metrics.py` e `tests/test_release_engine.py` — patcham `src.config.get_scm_settings`.
- Nenhum teste cobre `validate_or_request_scm_token`.

### Documentação existente

- `docs/plans/ADR-001-scm-abstraction.md` — documenta exatamente o modelo global substituído.
- `docs/plans/glossary-scm-multiforge.md` — vocabulário SCM e a tabela de chaves.
- `CONTEXT.md` — não tem vocabulário de forge; o glossário SCM é a casa.
- `CLAUDE.md` — lista de variáveis de ambiente e seção Multi-Forge SCM.

## 4. Conclusão

O comportamento relatado tem duas causas independentes — precedência do provider
global e slot único de token — mais um terceiro vazamento da mesma família no
`base_url`. A correção é uma mudança de escopo de configuração: o forge passa a
ser do repositório, os segredos passam a ser do forge.

Plano executável: `docs/plans/develop_natan/20261107_per_provider_scm_settings_plansfacts.md`.
