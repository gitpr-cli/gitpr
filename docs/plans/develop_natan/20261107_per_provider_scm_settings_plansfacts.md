# Plano de execução — Forge por repositório e token por provider

- **Branch:** develop_natan
- **Data:** 2026-11-07
- **Origem:** `/grill-with-docs` — entrevista de design em três rodadas, fronteira esgotada e plano aprovado.

## Problema

`~/.gitpr/.env` guarda um único `GITPR_SCM_PROVIDER` e um único
`GITPR_SCM_TOKEN_ENCRYPTED` para a máquina inteira. O provider global tem
precedência sobre a detecção do remote, então configurar um repositório GitLab
passa a tratar todo repositório GitHub da mesma máquina como GitLab — e a
procurar um token que só existe para o outro forge.

Um segundo vazamento da mesma classe: `resolve_scm_provider()` repassa
`base_url` para **todos** os providers, então um `GITPR_SCM_BASE_URL` de GitLab
self-hosted aponta o GitHub para a API errada.

## Resultado esperado

O forge passa a ser uma propriedade **do repositório**; cada forge ganha seu
próprio slot de token cifrado e seu próprio `base_url`. Uma máquina serve
GitHub, GitLab, Bitbucket e Azure ao mesmo tempo.

## Decisões

| # | Decisão |
|---|---|
| 1 | Precedência: override no `.gitpr/conf/gitpr.config.yml` → detecção do `origin` → `github`. Override explícito sempre vence. |
| 2 | `detect_provider_from_remote(url, default=None)` distingue "desconhecido"; chamadas de um argumento mantêm desconhecido → `github`. |
| 3 | Token cifrado por provider: `GITHUB_TOKEN_ENCRYPTED` (nome preservado), `GITLAB_TOKEN_ENCRYPTED`, `BITBUCKET_TOKEN_ENCRYPTED`, `AZURE_DEVOPS_TOKEN_ENCRYPTED`. `GITPR_SCM_TOKEN` continua único e global (CI), consultado primeiro. |
| 4 | `base_url` por provider: `GITHUB_BASE_URL`, `GITLAB_BASE_URL`, `BITBUCKET_BASE_URL`, `AZURE_DEVOPS_BASE_URL`. |
| 5 | `GITPR_SCM_ORGANIZATION` / `GITPR_SCM_PROJECT` / `GITPR_SCM_USERNAME` continuam globais — cada um é lido por exatamente um provider. |
| 6 | Migração one-shot, idempotente, na primeira chamada do resolvedor; nunca sobrescreve um `<PROVIDER>_TOKEN_ENCRYPTED` existente; falha de escrita degrada para valores do processo. |
| 7 | `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` saem do schema, do seed, da TUI e das leituras. |
| 8 | Token ausente: execução interativa pede/valida/salva na hora; hooks, MCP e CI falham apontando `gitpr --init`. |
| 9 | `gitpr --init` vira wizard do repositório; só grava o override no projeto quando o forge resolvido difere da detecção. |
| 10 | Todas as cinco superfícies SCM passam pelo resolvedor novo. |
| 11 | Docs: ADR-016 novo, nota de superação parcial no ADR-001, vocabulário novo no glossário SCM. `CONTEXT.md` intocado. |

## Arquitetura

Novo módulo `src/scm_settings.py`:

```
scm_settings → {config, project_config, infrastructure.scm.factory}
```

- `origin_remote_url()` — subprocess próprio (não importar `core`, que puxa `google.genai`).
- `resolve_provider_choice(project_value, remote_url)` — função pura da precedência.
- `migrate_legacy_scm_config()` — one-shot, sob `threading.Lock`.
- `provider_token()` / `provider_base_url()` / `provider_extras()`.
- `resolve_scm_settings()` / `get_scm_settings()` — a segunda devolve o dict plano que `resolve_scm_provider()` já consome, para que os consumidores mudem só o import.

`factory.py` continua sem ler variáveis de ambiente; `config.py` continua sendo
só a camada dotenv.

## Etapas

1. `src/scm_settings.py` (novo).
2. `detect_provider_from_remote(..., default=...)` no factory.
3. Seção `scm:` em `src/project_config.py` (leitura, escrita, campos do TUI).
4. Bloco SCM de `src/config_schema.py` (4 tokens, 4 base URLs, provider no projeto, effective provider computado).
5. `src/tui_issue.py` (`_token_env_var` por provider, `allow_prompt`).
6. `run_scm_init_wizard` em `src/core.py`.
7. Os cinco consumidores (`main.py` ×2, `release_engine.py`, `metrics.py`, `mcp_server.py`).
8. `src/ui/config_app.py` (effective provider, probe por token).
9. Remoção de `get_scm_token` / `get_scm_settings` / `get_scm_provider` de `src/config.py`.
10. Testes novos e reescritos.
11. ADR-016, nota no ADR-001, glossário, CLAUDE.md.

## Verificação

- `python -m pytest tests -q`
- `python -m unittest discover tests -q`
- `python scripts/validate_i18n.py`
- Prova manual com `python run.py` (não o `gitpr` do PATH — é a release antiga do PyPI) num repositório GitLab e num GitHub da mesma máquina.

## Riscos

- Token não-GitHub global deixa de ser compartilhado: cada repositório daquele forge pede o token uma vez (interativo) ou falha com aviso (CI/hooks/MCP).
- Forge self-hosted cujo domínio não contém `gitlab`/`bitbucket` perde o sinal antigo quando a chave legada é apagada → warning na migração e override no `--init`.
- HOME somente leitura: migração e salvamento degradam com aviso.

## Fora de escopo

Token por repositório do *mesmo* forge (exigiria keyring), duas organizações
Azure na mesma máquina, GitHub Enterprise Server e Bitbucket Server/DC além do
`*_BASE_URL` manual, o shim `src/github_api.py`.
