# SPEC — GitPR Multi-Forge (ScmProvider Abstraction)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: generalizar o acesso a forges Git (GitHub, GitLab, Bitbucket, Azure DevOps) por trás de uma interface única, seguindo o Strategy Pattern já usado em `ai_providers.py`.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler o `github_api.py` atual (localização real no repo — inspecionar `ARCHITECTURE.md` para confirmar o caminho) e extrair a lista completa de funções/métodos hoje expostos e consumidos por `core.py`, `action.yml`, MCP server e TUIs.
2. Ler `ai_providers.py` e confirmar o formato exato do Strategy Pattern já em uso (nome da classe base, método de registro/factory, convenção de nomes) para replicar o mesmo estilo — não inventar um padrão novo.
3. Listar todos os call sites de `github_api.py` no projeto (`grep -r "github_api"` ou equivalente) antes de remover/alterar qualquer import.
4. Confirmar se o projeto usa `dataclasses`, `pydantic` ou outro padrão de modelagem de dados já dominante no restante do código, e usar o mesmo (a spec abaixo assume `dataclasses` como default, mas deve ser ajustado se o padrão real for outro).

Não prosseguir com a implementação sem completar os passos 1–3. Se `github_api.py` tiver assinaturas diferentes das assumidas nesta spec, a skill deve adaptar os métodos concretos mantendo o contrato abstrato inalterado.

## 1. Escopo da feature

- **Objetivo:** permitir que o GitPR opere sobre GitHub, GitLab, Bitbucket Cloud e Azure DevOps sem duplicar lógica de negócio em `core.py`.
- **Fora de escopo nesta fase:** Bitbucket Server/Data Center (API distinta da Cloud), GitHub Enterprise Server (API distinta do SaaS), autenticação OAuth2 interativa (login via browser) — usar apenas PAT/App Password nesta primeira versão.
- **Compatibilidade:** o comportamento atual com GitHub não pode regredir. Todo teste existente que cobre `github_api.py` deve continuar passando após a refatoração.

## 2. Árvore de arquivos a criar/alterar

```
src/infrastructure/scm/
├── __init__.py
├── base.py                  # NOVO — interface ScmProvider + dataclasses
├── github_provider.py       # NOVO — extraído/refatorado de github_api.py
├── gitlab_provider.py       # NOVO
├── bitbucket_provider.py    # NOVO
├── azure_devops_provider.py # NOVO
└── factory.py                # NOVO — registry + resolve_scm_provider + detect_provider_from_remote

tests/scm/
├── test_contract.py          # NOVO — testes de contrato (todos providers)
├── test_github_provider.py   # NOVO/migrado dos testes atuais de github_api
├── test_gitlab_provider.py   # NOVO
├── test_bitbucket_provider.py # NOVO
└── test_azure_devops_provider.py # NOVO

.gitpr/config.schema.yml      # ATUALIZAR — adicionar bloco `scm:`
core.py                       # ALTERAR — trocar import direto de github_api por resolve_scm_provider
main.py ou cli entrypoint      # ALTERAR — flag/comando `--init` passa a perguntar o provider
github_api.py                 # DEPRECAR — manter como shim fino chamando GitHubProvider, remover em versão futura
```

## 3. Contrato da interface (obrigatório, não alterar assinatura)

```python
# src/infrastructure/scm/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PullRequestRequest:
    title: str
    description: str
    source_branch: str
    target_branch: str
    draft: bool = False
    labels: list[str] = field(default_factory=list)
    reviewers: list[str] = field(default_factory=list)


@dataclass
class PullRequestResult:
    id: str | int
    url: str
    number: int
    state: str
    source_branch: str
    target_branch: str
    provider: str


@dataclass
class RepoRef:
    raw: str
    workspace: str
    name: str
    provider: str


class ScmProvider(ABC):
    name: str

    def __init__(self, token: str, base_url: Optional[str] = None, **kwargs):
        self.token = token
        self.base_url = base_url or self.default_base_url()
        self.extra = kwargs

    @abstractmethod
    def default_base_url(self) -> str: ...

    @abstractmethod
    def parse_repo_ref(self, remote_url: str) -> RepoRef: ...

    @abstractmethod
    def create_pull_request(self, repo: RepoRef, req: PullRequestRequest) -> PullRequestResult: ...

    @abstractmethod
    def get_pull_request_diff(self, repo: RepoRef, pr_id: str | int) -> str: ...

    @abstractmethod
    def list_open_pull_requests(self, repo: RepoRef) -> list[PullRequestResult]: ...

    @abstractmethod
    def add_comment(self, repo: RepoRef, pr_id: str | int, body: str) -> None: ...

    @abstractmethod
    def merge_pull_request(self, repo: RepoRef, pr_id: str | int, strategy: str = "merge") -> None: ...

    @abstractmethod
    def test_connection(self) -> bool: ...
```

**Regra:** nenhum método pode ser adicionado ou removido desta interface sem atualizar as 4 implementações e os testes de contrato no mesmo commit/PR.

## 4. Especificação por provider (dados de API para a skill implementar)

### 4.1 GitHubProvider (`name = "github"`)
| Campo | Valor |
|---|---|
| `default_base_url()` | `https://api.github.com` |
| Header de auth | `Authorization: Bearer {token}` |
| Criar PR | `POST /repos/{workspace}/{name}/pulls` — body: `title`, `body`, `head`, `base`, `draft` |
| Obter diff | `GET /repos/{workspace}/{name}/pulls/{pr_id}` com `Accept: application/vnd.github.v3.diff` |
| Listar abertos | `GET /repos/{workspace}/{name}/pulls?state=open` |
| Comentar | `POST /repos/{workspace}/{name}/issues/{pr_id}/comments` — body: `{"body": ...}` |
| Merge | `PUT /repos/{workspace}/{name}/pulls/{pr_id}/merge` — body: `{"merge_method": strategy}` |
| Test connection | `GET /user` — 200 = ok |
| Parse repo ref | extrair `owner`/`repo` dos dois últimos segmentos da URL do remote |

### 4.2 GitLabProvider (`name = "gitlab"`)
| Campo | Valor |
|---|---|
| `default_base_url()` | `https://gitlab.com/api/v4` (self-managed: valor customizado via config `base_url`) |
| Header de auth | `Private-Token: {token}` |
| Identificador de projeto | `quote(f"{workspace}/{name}", safe="")` — URL-encoded, NUNCA usar sem encode |
| Criar MR | `POST /projects/{project_id}/merge_requests` — body: `title`, `description`, `source_branch`, `target_branch` |
| Obter diff | `GET /projects/{project_id}/merge_requests/{iid}/changes` — concatenar campo `diff` de cada item em `changes[]` |
| Listar abertos | `GET /projects/{project_id}/merge_requests?state=opened` |
| Comentar | `POST /projects/{project_id}/merge_requests/{iid}/notes` — body: `{"body": ...}` |
| Merge | `PUT /projects/{project_id}/merge_requests/{iid}/merge` |
| Test connection | `GET /user` — 200 = ok |
| Parse repo ref | suportar subgrupos (`grupo/subgrupo/projeto`); `workspace` = tudo antes da última `/`, `name` = último segmento |
| Nota de nomenclatura | resposta da API usa `iid` (não `id`) como número visível do MR — usar `iid` em `PullRequestResult.number` |

### 4.3 BitbucketProvider (`name = "bitbucket"`)
| Campo | Valor |
|---|---|
| `default_base_url()` | `https://api.bitbucket.org/2.0` |
| Auth | Basic (`username` + `token` como App Password) — `username` vem de `extra["username"]`, campo obrigatório na config |
| Criar PR | `POST /repositories/{workspace}/{name}/pullrequests` — body aninhado: `source.branch.name`, `destination.branch.name` |
| Obter diff | `GET /repositories/{workspace}/{name}/pullrequests/{pr_id}/diff` — retorna texto plano direto |
| Listar abertos | `GET /repositories/{workspace}/{name}/pullrequests?state=OPEN` — resultado em `values[]` |
| Comentar | `POST /repositories/{workspace}/{name}/pullrequests/{pr_id}/comments` — body: `{"content": {"raw": ...}}` |
| Merge | `POST /repositories/{workspace}/{name}/pullrequests/{pr_id}/merge` — body: `{"merge_strategy": strategy}` |
| Test connection | `GET /user` com Basic auth — 200 = ok |
| Restrição | Bitbucket **Server/Data Center** usa API diferente (`/rest/api/1.0/...`) — NÃO implementar nesta fase, documentar como limitação conhecida |

### 4.4 AzureDevOpsProvider (`name = "azure_devops"`)
| Campo | Valor |
|---|---|
| `default_base_url()` | `https://dev.azure.com` |
| Campos extras obrigatórios | `extra["organization"]`, `extra["project"]` — validar presença no `__init__`, levantar erro claro se ausentes |
| Auth | Basic com usuário vazio (`""`) e PAT como senha |
| Versão de API | Anexar `?api-version=7.1` em toda chamada |
| URL base do repo | `{base_url}/{organization}/{project}/_apis/git/repositories/{repositoryId}` |
| Criar PR | `POST .../pullrequests?api-version=7.1` — body: `sourceRefName: "refs/heads/{branch}"`, `targetRefName: "refs/heads/{branch}"`, `title`, `description` |
| Obter diff | Sem endpoint de diff unificado nativo — usar `.../pullrequests/{pr_id}/iterations?api-version=7.1` e tratar/normalizar na camada de domínio (documentar limitação) |
| Listar abertos | `GET .../pullrequests?searchCriteria.status=active&api-version=7.1` — resultado em `value[]` |
| Comentar | `POST .../pullrequests/{pr_id}/threads?api-version=7.1` — body: `{"comments": [{"content": ..., "commentType": 1}], "status": 1}` |
| Merge | `PATCH .../pullrequests/{pr_id}?api-version=7.1` — body: `{"status": "completed", "completionOptions": {"mergeStrategy": strategy}}` |
| Test connection | `GET {base_url}/{organization}/_apis/projects/{project}?api-version=7.1` — 200 = ok |
| `repositoryId` | pode ser nome ou GUID; `parse_repo_ref` deve extrair o nome do repo a partir de `.../_git/{repo}` na URL |

## 5. Factory / registry (arquivo `factory.py`)

Requisitos funcionais:

1. `_REGISTRY: dict[str, type[ScmProvider]]` mapeando `"github" | "gitlab" | "bitbucket" | "azure_devops"` para as classes.
2. `resolve_scm_provider(config: dict) -> ScmProvider` — lê `config["provider"]`, `config["token"]`, `config.get("base_url")`, e repassa qualquer chave extra (`organization`, `project`, `username`) via `**kwargs`. Levantar `ValueError` com mensagem listando providers válidos se a chave não existir no registry.
3. `detect_provider_from_remote(remote_url: str) -> str` — heurística por substring case-insensitive: `"gitlab"` → `gitlab`; `"bitbucket"` → `bitbucket`; `"dev.azure.com"` ou `"visualstudio.com"` → `azure_devops`; qualquer outro → `github` (default).
4. Erro de configuração ausente (`organization`/`project` faltando para Azure DevOps, `username` faltando para Bitbucket) deve ser levantado no momento da instanciação (`__init__`), não no primeiro uso — falha rápida.

## 6. Config e persistência

Adicionar bloco `scm:` ao schema de config existente:

```yaml
scm:
  provider: gitlab
  token: ${GITPR_SCM_TOKEN}
  base_url: https://gitlab.empresa.com/api/v4   # opcional, omitir = SaaS público
  organization: minha-org                        # obrigatório somente se provider = azure_devops
  project: SIG-JB                                 # obrigatório somente se provider = azure_devops
  username: meu.usuario                           # obrigatório somente se provider = bitbucket
```

Requisitos:
- Token deve ser criptografado usando o **mesmo mecanismo Fernet já usado para chaves de IA** (não introduzir um segundo esquema de criptografia).
- `gitpr --init` deve: (a) rodar `git remote get-url origin`, (b) chamar `detect_provider_from_remote`, (c) exibir o provider detectado e pedir confirmação, (d) coletar token (e campos extras se necessário), (e) chamar `test_connection()` antes de persistir, (f) salvar criptografado somente se a conexão for validada.

## 7. Pontos de integração a alterar em `core.py`

Buscar todos os pontos onde `core.py` hoje importa/chama funções de `github_api.py` (ex.: criação de PR, obtenção de diff para review, listagem de PRs abertos, comentários automáticos, merge). Substituir cada chamada direta por:

```python
scm = resolve_scm_provider(loaded_config["scm"])
repo_ref = scm.parse_repo_ref(git_remote_url)
```

seguido da chamada ao método correspondente da interface. Nenhuma lógica de negócio (formatação de título de PR, geração de descrição via IA, etc.) deve mudar — apenas o transporte/API muda de lugar.

## 8. Retrocompatibilidade — `github_api.py`

Não remover o arquivo nesta fase. Transformá-lo em um shim fino:

```python
# github_api.py (deprecated shim)
import warnings
from src.infrastructure.scm.github_provider import GitHubProvider

def create_pull_request(*args, **kwargs):
    warnings.warn(
        "github_api.create_pull_request está deprecado, use ScmProvider via factory.resolve_scm_provider",
        DeprecationWarning, stacklevel=2,
    )
    # mapear args antigos para a nova interface e delegar para GitHubProvider
    ...
```

Isso evita quebrar integrações externas (plugins, scripts do usuário) que ainda importem `github_api` diretamente.

## 9. Testes obrigatórios (critério de aceite)

1. **Teste de contrato** (`tests/scm/test_contract.py`): parametrizado pelos 4 providers, verifica que cada classe implementa todos os métodos abstratos da interface e instancia sem erro com kwargs mínimos válidos.
2. **Teste unitário por provider** com `requests` mockado (usar `responses` ou `pytest-mock`, conforme padrão já usado nos 264 testes existentes do projeto): cobrir `create_pull_request`, `get_pull_request_diff`, `list_open_pull_requests`, `add_comment`, `merge_pull_request`, `test_connection` — sucesso e erro HTTP (4xx/5xx deve propagar exceção, não engolir silenciosamente).
3. **Teste de regressão do GitHub**: todo teste que hoje cobre `github_api.py` deve ser migrado para `test_github_provider.py` e continuar passando sem alteração de comportamento observável.
4. **Teste do factory**: `resolve_scm_provider` com provider inválido levanta `ValueError`; `detect_provider_from_remote` cobre pelo menos um exemplo de URL real por forge (SaaS) e um exemplo self-managed para GitLab.
5. **Teste de config**: Azure DevOps sem `organization`/`project` levanta erro claro na instanciação; Bitbucket sem `username` idem.

Critério de "feature completa": suite de testes nova + migrada passa 100%, sem reduzir a cobertura total de testes do projeto (hoje 264 cenários, segundo o relatório de status).

## 10. Ordem de execução recomendada (para a skill seguir em etapas)

1. Criar `base.py` com a interface e dataclasses — sem lógica, só contrato.
2. Extrair `GitHubProvider` de `github_api.py`, criar shim de compatibilidade, migrar testes existentes. Validar que nada quebrou antes de seguir.
3. Implementar `GitLabProvider` + testes.
4. Implementar `factory.py` com registry contendo GitHub + GitLab, e `detect_provider_from_remote`.
5. Integrar `factory.py` em `core.py` (trocar imports), validar fluxo end-to-end manualmente contra um repo GitLab de teste.
6. Implementar `AzureDevOpsProvider` + testes, registrar no factory.
7. Implementar `BitbucketProvider` + testes, registrar no factory.
8. Atualizar `gitpr --init` para o fluxo de detecção/confirmação/validação de provider.
9. Atualizar `config.schema.yml` e documentação de configuração.
10. Rodar suite completa de testes e só então abrir PR final.

Não implementar os 4 providers em paralelo num único commit grande — cada etapa acima deve ser um commit/PR revisável isoladamente, permitindo rollback pontual se um provider tiver problema.

## 11. Fora de escopo explícito (não implementar sem novo pedido)

- OAuth2 interativo (fluxo de login via browser) para qualquer provider.
- Bitbucket Server/Data Center (on-prem).
- GitHub Enterprise Server (API própria, diferente do SaaS).
- Webhooks de entrada (receber eventos dos forges) — esta spec cobre apenas chamadas de saída (GitPR → forge).
- Qualquer UI/TUI nova — a spec assume que a TUI do PR Publisher já existente apenas passa a receber `PullRequestResult` normalizado, sem redesenho visual.
