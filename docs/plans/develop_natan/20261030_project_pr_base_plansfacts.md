# Plano de execução — branch base do PR configurável por projeto

Data: 2026-10-30 · Branch: `develop_natan`

## Objetivo

Adicionar `.gitpr/conf/gitpr.config.yml` (versionado, no topo do repo) com
`pull_request.base_branch`, semeado automaticamente e editável no `gitpr config`,
usado como alvo do PR por projeto. Precedência: `--base` > arquivo > `PR_DEFAULT_BASE`
> auto-detect > `main`.

## Desenho

1. **Novo `src/project_config.py`** — módulo leve (stdlib + `yaml` + i18n):
   - `project_config_path()`: `git rev-parse --show-toplevel` + `.gitpr/conf/gitpr.config.yml`, fallback `cwd`.
   - `read_project_config()`: `safe_load`; ausente → vazio; inválido → `ProjectConfig.error` sem levantar.
   - `load_project_field_values()`: valor para o TUI.
   - `write_project_field_values()`: preserva outras chaves, recusa YAML não parseável, cabeçalho fixo.
   - `ensure_project_config()`: seed best-effort, nunca sobrescreve, no-op fora de repo,
     valor = `PR_DEFAULT_BASE` strip → `main`; detecta `git check-ignore`.
   - `resolve_pull_request_base(cli_base, verify=True)`: única cadeia de precedência;
     importa `core.get_base_branch(quiet=True)` tardiamente.
   - `verify_remote_base()`: `refs/remotes/origin/<branch>`, erro distinto para repo sem `origin`.
2. **`src/core.py`** — `get_base_branch(quiet=False)` para não imprimir aviso no TUI/MCP.
3. **`src/main.py`** — seed no `cli()` antes do retorno de subcomandos (exceto ajuda; escape
   `GITPR_SKIP_PROJECT_CONFIG_SEED`); anúncio só no caminho raiz interativo; resolução do alvo
   após `--no-publish` com `BaseBranchError` → `Exit(1)`.
4. **`src/mcp_server.py`** — `publish_pull_request` usa o mesmo resolver; falha → JSON `error`.
5. **`src/core.py` (`run_install_wizard`)** — reporta/seed do arquivo antes dos 4 passos.
6. **`src/config_schema.py`** — `STORE_ENV`/`STORE_PROJECT`, categoria `project`, três campos
   (`PROJECT_CONFIG_FILE` leitura, `PROJECT_BASE_BRANCH` edição, `PROJECT_EFFECTIVE_BASE` leitura),
   renomeia `PR_DEFAULT_BASE` para "Global Default Base Branch".
7. **`src/ui/config_app.py`** — estado do projeto, linhas por `store`, plano separado
   (`project`/`project_removals`), gravação do YAML isolada, aviso (não bloqueio) se a branch
   não existir, recarga após salvar.
8. **Testes** — `GITPR_SKIP_PROJECT_CONFIG_SEED` no conftest; patch de caminho no `ConfigAppTestCase`;
   novo `tests/test_project_config.py`; ajustes em MCP, schema, TUI e install.
9. **i18n** — `python tests/sync_i18n.py` + traduções nos seis `langs/*.json`.
10. **Docs/ADR/relatório** — `config-tui.md`, `pull-request-publication.md`, `pr-descricao-padrao.md`,
    `install-wizard.md` (+ traduções), `ADR-015`, glossário, `CLAUDE.md`, survey e relatório.

## Riscos

- Contaminação do pytest pelo seed (mitigada no conftest e no `setUp` do ConfigApp).
- Repos com default `master`: seed literal `main` falha na verificação até ser editado (decisão Q9).
- Stdout de subcomandos/hooks/MCP deve permanecer limpo (sem anúncio).
- YAML inválido do usuário nunca é sobrescrito.
