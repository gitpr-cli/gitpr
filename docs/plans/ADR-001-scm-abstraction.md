# ADR-001 — Abstração SCM Multi-Forge (`ScmProvider`)

- **Status:** Aceito
- **Data:** 2026-09-05
- **Contexto:** spec [2026-09-02_multi_skill_gitpr_multiforge_spec.md](2026-09-02_multi_skill_gitpr_multiforge_spec.md), entrevista (grilling) e plano aprovado
- **Glossário:** [glossary-scm-multiforge.md](glossary-scm-multiforge.md)

## Contexto

O GitPR falava **apenas GitHub**: `src/github_api.py` centralizava 4 operações
de PR com o padrão de tuplas `(ok, data, status)` que **engole exceções**, e os
consumidores reais (publisher direto em `main.py` e a TUI `pr_publish_app.py`)
tinham tratamento de erro acoplado a `status == 401`. Issues postavam inline em
`issue_app.py`. A spec pedia generalizar para GitHub/GitLab/Bitbucket/Azure
DevOps por trás de uma interface única.

A exploração do código revelou que a spec foi escrita contra suposições
defasadas: não havia Strategy Pattern em `ai_providers.py` (o ABC `ScmProvider`
seria o primeiro do projeto), não havia YAML de configuração (`~/.gitpr/.env`
é dotenv plano), e a flag `--init` não existia. Essas divergências foram
entrevistadas com o usuário (Rodadas 1–3 do grilling) e as respostas viraram
decisões vinculantes.

## Decisão

Criar `src/infrastructure/scm/` com:

1. **`base.py`** — ABC `ScmProvider` (11 métodos abstratos), dataclasses
   (`PullRequestRequest`, `PullRequestResult`, `RepoRef`, `IssueRequest`,
   `IssueResult`) e erros (`ScmProviderError`, `ScmNotSupportedError`).
2. **Um provider concreto por forge** — `github_provider.py` (extraído do
   `github_api.py`, com raise), `gitlab_provider.py`, `bitbucket_provider.py`,
   `azure_devops_provider.py`.
3. **`factory.py`** — `_REGISTRY` completo + `resolve_scm_provider(config)` +
   `detect_provider_from_remote(remote_url)`.
4. **Erros por exceção** — providers **levantam** `ScmProviderError(provider,
   http_status, message)` em 4xx/5xx e falha de rede (`http_status=0`); a
   tradução para o comportamento de UI atual (tuplas locais, reauth 401) mora
   nos call sites (`main.py`, `pr_publish_app.py`, `issue_app.py`).
5. **Config dotenv plana** — `GITPR_SCM_PROVIDER` (default `github`),
   `GITPR_SCM_TOKEN` (CI/raw) + `GITPR_SCM_TOKEN_ENCRYPTED` (Fernet, escrita
   pelo wizard), `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`,
   `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME`. Config ausente → `github` →
   comportamento atual byte a byte (fallback no `GITHUB_TOKEN_ENCRYPTED`
   legado).
6. **Flag `--init`** — `core.run_scm_init_wizard()`: detecta a forge do remote
   origin, confirma, coleta extras e token, valida via `test_connection()`
   (3 tentativas, 401 re-prompta) e **persiste só no sucesso**.
7. **`src/github_api.py` vira shim deprecado** — mesmas 4 assinaturas, mesmas
   tuplas, `DeprecationWarning`; delega ao `GitHubProvider`. Código interno
   deixou de importá-lo.

### Alternativas consideradas

| Alternativa | Veredito |
|---|---|
| Flags por forge (`gitpr --gitlab …`) | Rejeitada — duplicaria o dispatch, a TUI e a lógica de erro para cada forge. |
| Camadas HTTP independentes por forge, sem ABC | Rejeitada — repetição de auth/erro/parsing; a TUI precisaria de ifs por forge. |
| Manter `github_api.py` crescendo com ramificações por forge | Rejeitada — o padrão de tuplas engole o motivo do erro e impede reauth por status. |
| Config em YAML (`config.schema.yml`) como na spec §2/§6 | Rejeitada — o projeto não tem YAML de config; só dotenv plano + Fernet. |
| Converter call sites para exceções em toda parte | Rejeitada parcialmente — providers levantam; a UI legada mantém o comportamento local atual no boundary. |

## Desvios aprovados (vs. a spec §3–§6)

1. **ABC estendido com 3 métodos além da §3** — `check_existing_pull_request`,
   `update_pull_request` e `create_issue` entram no contrato (11 métodos
   abstratos): a TUI de PRs e o fluxo de issues exigem essas operações; sem
   elas os consumidores manteriam chamadas fora da abstração.
2. **Raise em vez de tuplas** — a convenção `(ok, data, status)` morre dentro
   dos providers. Todo erro vira `ScmProviderError`; a conversão para o
   comportamento de UI atual acontece no call site.
3. **Header `Authorization: token` (não `Bearer`)** no GitHub — a §4.1 da spec
   pedia Bearer; o código legado usa `token` e os testes migrados o fixam.
   Mantido por byte-parity (mudar o header é mudança de comportamento
   observável da API).
4. **Dotenv plano no lugar do YAML** — a §2/§6 assumia `config.schema.yml`;
   o projeto usa `~/.gitpr/.env` com `_ENCRYPTED` Fernet. As chaves SCM
   seguem o mesmo padrão das chaves existentes.
5. **`workspace` do Azure é display-only** — `RepoRef.workspace = "{org}/{project}"`
   serve só para rótulos; as chamadas usam `organization`/`project` dos extras
   (fail-fast no `__init__` com mensagem i18n nomeando as env vars).
6. **Diff do Azure é resumo estruturado** — a REST do Azure não expõe diff
   unificado de PR; `get_pull_request_diff` devolve um resumo textual por
   arquivo (`path (+adds −dels)`) montado da última iteration com mudanças.
   Limitação documentada no provider e no glossário.
7. **Issues do Bitbucket exigem Issue Tracker habilitado** — sem o tracker o
   endpoint `…/issues` responde 404 e o `ScmProviderError` propaga como
   qualquer erro de API (documentado).
8. **`create_issue` no Azure = `ScmNotSupportedError`** — Work Items dependem
   do process template do projeto (não há endpoint universal); a TUI de
   issues avisa para salvar localmente (F2).
9. **Shim `github_api.py` mantido** — terceiros/pipelines podem importar as 4
   funções legadas; `DeprecationWarning` orienta a migração. O GitPR interno
   não o importa mais.
10. **`labels`/`reviewers` reservados, não consumidos** — os campos existem no
    `PullRequestRequest` para contratos futuros, mas nenhum provider envia
    labels/reviewers hoje (payload do GitHub preserva as 4 chaves exatas do
    código legado).

## Consequências

**Positivas:**
- Um único caminho de código para PRs e issues em 4 forges; reauth 401 e
  tratamento de rede centralizados por provider.
- GitHub sem config SCM continua idêntico (default + fallback de token) —
  zero migração para usuários existentes.
- `gitpr --init` substitui a edição manual do `.env` para configurar forges.

**Negativas / custos:**
- Comportamentos específicos de forge (App Password do Bitbucket, org/project
  do Azure, MR do GitLab) precisam de extras de config que o usuário deve
  conhecer — mitigado pelo wizard e pelos erros fail-fast nomeando as env vars.
- O diff de PR do Azure é um resumo, não um diff aplicável (limitação da API).
- Mais testes de superfície (contrato por provider) para manter quando um
  forge mudar a API.

**Observado fora do escopo:** Bitbucket Server/DC, GitHub Enterprise Server e
OAuth2 interativo ficam para trabalho futuro; `validate_github_token`
(config.py) permanece sem callers internos e `issue_engine.get_github_repo_info`
permanece (fluxo `-ch` não migra).
