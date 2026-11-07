# Glossário — SCM Multi-Forge

> Vocabulário canônico da abstração `ScmProvider` (GitPR Multi-Forge).
> Mantido junto da [spec](2026-09-02_multi_skill_gitpr_multiforge_spec.md); a lista de desvios aprovados vive no [ADR-001](ADR-001-scm-abstraction.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **forge** | Plataforma de hospedagem Git com API própria: GitHub, GitLab, Bitbucket Cloud, Azure DevOps. |
| **provider** | Implementação concreta da interface `ScmProvider` para um forge. Identificador estável (`name`): `github`, `gitlab`, `bitbucket`, `azure_devops`. |
| **pull request** | Termo unificado para o objeto de revisão de código entre branches. Sinônimos por forge: *pull request* (GitHub/Bitbucket/Azure), *merge request (MR)* (GitLab). Nunca usar "merge request" no código. |
| **source_branch / target_branch** | Nomes canônicos das branches do PR. Aliases por forge na API: GitHub `head`/`base`, GitLab `source`/`target`, Bitbucket `source`/`destination`, Azure `sourceRefName`/`targetRefName` (prefixo `refs/heads/`). |
| **workspace** | Segmento de namespace do repositório no forge, extraído do remote por `parse_repo_ref`. GitHub = *owner*; GitLab = grupo/subgrupos (tudo antes do último segmento); Bitbucket = *workspace*; Azure DevOps = `"{org}/{project}"` **somente para display** (as chamadas de API usam `organization`/`project` da config `extra`). |
| **RepoRef** | Representação canônica de um repositório: `raw` (URL do remote), `workspace`, `name`, `provider`. Substitui a string solta `"owner/repo"` nos fluxos migrados; `display` é o rótulo legível (`workspace/name`). |
| **id vs number** | `PullRequestResult.id` = identificador usado em chamadas subsequentes (GitLab: `iid` do MR, **nunca** o `id` global do projeto; Azure: `pullRequestId`). `number` = número visível ao usuário (GitLab `iid`, GitHub `number`, Bitbucket `id`, Azure `pullRequestId`). |
| **draft** | PR em rascunho. GitHub/Azure/Bitbucket têm flag nativa; GitLab não tem no create da API v4 — vira prefixo `"Draft: "` no título. |
| **issue** | Item rastreável criado via `create_issue`: GitHub Issues, GitLab Issues, Bitbucket Issue Tracker. **Azure DevOps não tem** (Work Items dependem do process template) → `ScmNotSupportedError`. Bitbucket exige o Issue Tracker habilitado no repositório. |
| **token** | Credencial de API: PAT (GitHub/GitLab/Azure) ou App Password (Bitbucket, exige `username`). Sempre criptografada em repouso (Fernet), guardada no slot do **próprio** forge; `GITPR_SCM_TOKEN` cru só para CI. |
| **token slot** | A chave `<PROVIDER>_TOKEN_ENCRYPTED` do forge resolvido (`GITHUB_TOKEN_ENCRYPTED`, `GITLAB_TOKEN_ENCRYPTED`, `BITBUCKET_TOKEN_ENCRYPTED`, `AZURE_DEVOPS_TOKEN_ENCRYPTED`). Um forge nunca responde pelo token de outro. |
| **base_url** | URL da API do forge. Omitida = SaaS público (`default_base_url()`); customizada = self-managed (GitLab, Bitbucket Server — fora de escopo —, Azure) ou enterprise. Guardada por forge (`<PROVIDER>_BASE_URL`). |
| **extra** | Campos de config adicionais do provider, validados no `__init__` (fail-fast): `organization`/`project` (Azure), `username` (Bitbucket). |
| **ScmProviderError** | Exceção única dos providers: `http_status` = código HTTP (4xx/5xx) ou `0` (falha de rede, sem resposta HTTP); `message` = melhor esforço da mensagem do servidor (rede já localizada). |
| **ScmNotSupportedError** | Subclasse para operação sem equivalente no forge (ex.: `create_issue` no Azure). |
| **detect_provider_from_remote** | Heurística por substring na URL do remote (case-insensitive): `gitlab` → gitlab; `bitbucket` → bitbucket; `dev.azure.com`/`visualstudio.com` → azure_devops; **qualquer outro → `default`** — `github` quando chamada com um argumento, `None` ("não reconhecido") quando o resolvedor pede para distinguir. |
| **provider override** | Valor de `scm.provider` no `.gitpr/conf/gitpr.config.yml`. Versão com o repositório e **sempre** vence a detecção do remote — é a saída para um self-hosted cujo domínio não nomeia o forge. |
| **effective provider** | O forge que o repositório usa agora, depois da precedência override → detecção → `github`, junto da origem (`project`, `remote`, `default`). É o que a TUI mostra e o que qualquer comando usa. |
| **one-shot migration** | Movimento automático, na primeira chamada do resolvedor, de `GITPR_SCM_PROVIDER`/`GITPR_SCM_TOKEN_ENCRYPTED`/`GITPR_SCM_BASE_URL` para o slot do forge que o par nomeia. Idempotente, nunca sobrescreve um slot já preenchido e nunca quebra o comando quando o `.env` não pode ser escrito. |
| **api-version** | Query param obrigatório em toda chamada REST do Azure DevOps (`7.1`). |

## Chaves de configuração

**Por repositório — `.gitpr/conf/gitpr.config.yml` (versionado):**

| Chave | Significado |
|---|---|
| `scm.provider` | Override do forge. Ausente = detecção do remote `origin`. Gravado por `gitpr --init` só quando diverge da detecção. |

**Por máquina — `~/.gitpr/.env` (dotenv plano):**

| Chave | Significado |
|---|---|
| `GITPR_SCM_TOKEN` | Token cru (CI apenas). Único e global, consultado antes de qualquer slot. |
| `GITHUB_TOKEN_ENCRYPTED` / `GITLAB_TOKEN_ENCRYPTED` / `BITBUCKET_TOKEN_ENCRYPTED` / `AZURE_DEVOPS_TOKEN_ENCRYPTED` | Token criptografado (Fernet) de cada forge, escrito por `gitpr --init`/reauth. |
| `GITHUB_BASE_URL` / `GITLAB_BASE_URL` / `BITBUCKET_BASE_URL` / `AZURE_DEVOPS_BASE_URL` | API base customizada de cada forge (self-managed/enterprise). |
| `GITPR_SCM_ORGANIZATION` / `GITPR_SCM_PROJECT` | Obrigatórias para `azure_devops`. |
| `GITPR_SCM_USERNAME` | Obrigatório para `bitbucket` (App Password). |

`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` estão
**aposentadas**: a migração one-shot as move para o slot do forge que nomeiam e
remove as linhas.

## Notas de fidelidade de API

- **Diff de PR**: GitHub devolve diff unificado (`Accept: vnd.github.v3.diff`); Bitbucket devolve texto plano pronto; GitLab concatena `changes[].diff`; **Azure não tem diff unificado** — `get_pull_request_diff` monta um resumo textual por arquivo (`path (+adds −dels)`) a partir da última iteration com mudanças.
- **Caminho de projeto GitLab**: sempre `quote("group/subgroup/proj", safe="")` — nunca embutido cru numa URL.
- **Azure repositoryId**: aceita nome ou GUID; nomes podem ter espaços → sempre `quote(..., safe="")`.
