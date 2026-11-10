# Documentação Técnica: SCM Multi-Forge (ScmProvider)

O GitPR publica Pull Requests e issues por meio de uma única abstração, o `ScmProvider`, que suporta quatro forges de hospedagem Git: GitHub, GitLab, Bitbucket Cloud e Azure DevOps. Todos os fluxos de publicação — o publicador interativo de PR (modo padrão), a publicação direta (`--no-edit`) e a TUI de issues (`-is`) — resolvem o provider **do repositório em que estão sendo executados** e chamam a API do forge por meio dele.

O forge pertence ao repositório, não à máquina: o GitPR o detecta a partir do remote `origin` (ou lê um override explícito versionado com o projeto) e mantém **um token criptografado por forge** em `~/.gitpr/.env`. Uma máquina pode, portanto, trabalhar com um repositório GitLab e um repositório GitHub ao mesmo tempo, cada um com a sua credencial.

Sem configuração de SCM, o GitPR mantém o comportamento legado exclusivo do GitHub — zero migração e saída byte-idêntica.

---

## 1. Forges Suportados

| Forge | Chave do provider | Base da API padrão | Autenticação |
| --- | --- | --- | --- |
| GitHub | `github` | `https://api.github.com` | Personal Access Token (PAT) |
| GitLab | `gitlab` | `https://gitlab.com/api/v4` | Personal Access Token (PAT) |
| Bitbucket Cloud | `bitbucket` | `https://api.bitbucket.org/2.0` | Usuário + App Password (HTTP Basic) |
| Azure DevOps | `azure_devops` | `https://dev.azure.com` | Personal Access Token (PAT) |

### 1.1 Qual Forge um Repositório Usa

O forge é resolvido por repositório, nesta ordem:

1. **Override do projeto** — `scm.provider` em `.gitpr/conf/gitpr.config.yml`, versionado com o repositório. Sempre vence, e é assim que você corrige um host self-managed cujo domínio não nomeia o forge.
2. **Detecção do remote origin** — correspondência de substring, sem diferenciar maiúsculas/minúsculas, na URL do `origin`.
3. **`github`** — o padrão histórico.

| A URL do remote contém | Provider |
| --- | --- |
| `gitlab` | `gitlab` |
| `bitbucket` | `bitbucket` |
| `dev.azure.com` ou `visualstudio.com` | `azure_devops` |
| qualquer outra coisa (padrão) | `github` |

```yaml
# .gitpr/conf/gitpr.config.yml — versione para compartilhar o forge com o time
scm:
  provider: gitlab
```

Um valor desconhecido no arquivo de projeto é ignorado com um aviso (um arquivo malformado nunca pode derrubar todo comando), e a detecção decide no lugar dele.

```bash
git remote get-url origin
# git@github.com:gitpr-cli/gitpr.git               -> github (padrão)
# https://gitlab.com/acme/platform/web-app.git     -> gitlab
# https://bitbucket.org/acme/web-app               -> bitbucket
# https://dev.azure.com/acme/project/_git/web-app  -> azure_devops
```

O repositório é endereçado por meio do `RepoRef`, extraído da URL do remote. O **workspace** é o owner do GitHub, o namespace do GitLab (incluindo subgrupos), o workspace do Bitbucket ou — no Azure DevOps — um rótulo `{org}/{project}` somente para exibição, pois as chamadas de API usam o `organization` e o `project` da configuração.

---

## 2. Configuração Inicial — `gitpr --init`

O wizard interativo detecta o forge, valida o token de acesso e persiste a configuração:

```bash
gitpr --init
```

| Etapa | O que acontece |
| --- | --- |
| 1. Detecção do forge | Detecta o forge a partir do remote `origin` e pede confirmação (você pode escolher outro forge; um host que não nomeia forge é perguntado, nunca presumido) |
| 2. Extras do provider | O Azure DevOps pede `organization` e `project`; o Bitbucket pede o `username`, que faz parte da credencial |
| 3. Base da API | Base da API customizada para todos os forges, exceto GitHub; o valor já gravado para aquele forge é oferecido como padrão |
| 4. Token | Pede o PAT — ou a App Password no Bitbucket |
| 5. Validação | `test_connection()` — até 3 tentativas; HTTP 401 (token expirado) reapresenta o prompt em amarelo; outras falhas abortam em vermelho |
| 6. Persistência | Somente em caso de sucesso: grava o token criptografado com Fernet no slot do seu forge (`GITLAB_TOKEN_ENCRYPTED`, …), a base da API e os extras, e registra `scm.provider` no arquivo de projeto **somente quando o forge escolhido difere do detectado** |

Nada é gravado quando a validação falha. Execute `gitpr --init` novamente em cada repositório para trocar de forge ou renovar um token expirado; os tokens dos outros forges ficam intocados. Valores de versões anteriores (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`) são migrados automaticamente no primeiro comando após a atualização.

---

## 3. Configuração Manual (.env)

Alternativa ao wizard: edite o `~/.gitpr/.env` diretamente. Consulte o [guia de integração do GitHub PAT](github-pat-integration.md) para entender como o GitPR protege os tokens em repouso.

| Variável | Forge | Descrição |
| --- | --- | --- |
| `GITPR_SCM_TOKEN` | todos | Token cru, somente para ambientes de CI/CD — único e global, consultado antes de qualquer token gravado |
| `GITHUB_TOKEN_ENCRYPTED` | `github` | Token criptografado com Fernet do forge GitHub |
| `GITLAB_TOKEN_ENCRYPTED` | `gitlab` | Token criptografado com Fernet do forge GitLab |
| `BITBUCKET_TOKEN_ENCRYPTED` | `bitbucket` | Token criptografado com Fernet do forge Bitbucket |
| `AZURE_DEVOPS_TOKEN_ENCRYPTED` | `azure_devops` | Token criptografado com Fernet do forge Azure DevOps |
| `GITHUB_BASE_URL` / `GITLAB_BASE_URL` / `BITBUCKET_BASE_URL` / `AZURE_DEVOPS_BASE_URL` | próprio forge | Base da API customizada (self-managed/enterprise); vazio = SaaS público |
| `GITPR_SCM_ORGANIZATION` | `azure_devops` | Nome da organização — obrigatório (erro fail-fast indica a variável ausente) |
| `GITPR_SCM_PROJECT` | `azure_devops` | Nome do projeto — obrigatório |
| `GITPR_SCM_USERNAME` | `bitbucket` | Usuário do Bitbucket — obrigatório (App Password usa HTTP Basic) |

Cada forge lê apenas o seu slot: um token de GitLab nunca responde por um repositório GitHub. O GitHub sem configuração de SCM mantém o armazenamento `GITHUB_TOKEN_ENCRYPTED` — zero migração.

### 3.1 Nota de Migração: Provisionamento Automatizado e Slots por Forge

> [!WARNING]
> **Nota de Migração para Scripts de Provisionamento e Infraestrutura:**  
> As chaves globais legadas `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` foram descontinuadas. A migração automática em tempo de execução remove essas linhas do `~/.gitpr/.env` na primeira execução.  
> 
> Scripts de provisionamento automatizado de máquinas (Ansible, Docker, devcontainers, dotfiles ou inicialização de VMs) agora devem preencher diretamente os slots dedicados por forge:
> - GitHub: `GITHUB_TOKEN_ENCRYPTED` (e opcionalmente `GITHUB_BASE_URL`)
> - GitLab: `GITLAB_TOKEN_ENCRYPTED` (e opcionalmente `GITLAB_BASE_URL`)
> - Bitbucket: `BITBUCKET_TOKEN_ENCRYPTED` (e `GITPR_SCM_USERNAME`)
> - Azure DevOps: `AZURE_DEVOPS_TOKEN_ENCRYPTED` (e `GITPR_SCM_ORGANIZATION` + `GITPR_SCM_PROJECT`)
> 
> Para servidores self-hosted em domínios customizados, configure o override no arquivo do projeto em `.gitpr/conf/gitpr.config.yml` (`scm.provider: <forge>`) em vez de tentar fixar um provedor global no `.env`. Ambientes CI efêmeros devem continuar utilizando `GITPR_SCM_TOKEN` (token cru não criptografado). Detalhes arquiteturais no [ADR-0020](adr/0020-per-repo-scm-provisioning-migration.md) e [ADR-016](plans/ADR-016-per-provider-scm-settings.md).

---

## 4. Usando o GitPR com o Forge Configurado

### 4.1 Publicação de Pull Requests

```bash
gitpr                # Publicador interativo (TUI) — revise e confirme o PR
gitpr --no-edit      # Publica diretamente, com auto-commit (pula a TUI)
gitpr --no-publish   # Gera somente o arquivo de descrição do PR (.md), sem TUI
```

O publicador resolve o provider a partir do remote `origin`, converte o repositório em um `RepoRef` e cria o pull request por meio de `provider.create_pull_request()`. O número, a URL e o estado do PR retornados pelo forge são exibidos na TUI e salvos no arquivo de saída.

### 4.2 Issues

```bash
gitpr -is            # Fluxo de issue: rascunho com IA -> TUI -> F3 cria a issue no forge
```

F3 chama `provider.create_issue()` no forge configurado. O Azure DevOps não possui recurso de API para issues (os Work Items dependem do process template do projeto); por isso, o GitPR orienta a salvar o rascunho localmente com F2. O Bitbucket exige que o **Issue Tracker** do repositório esteja habilitado; caso contrário, a API responde 404.

### 4.3 Expiração do Token e Reautenticação (HTTP 401)

Quando o token é rejeitado (HTTP 401), o GitPR remove o token expirado do slot **daquele** forge e pede um novo — até 3 tentativas. Prefira os fluxos interativos (`gitpr`, `gitpr -is`) para reautenticar: o `--no-edit` publica diretamente e não pode reapresentar o prompt.

Uma execução não interativa (hooks do git, servidor MCP, CI) nunca pede e nunca apaga a credencial gravada: ela para com uma mensagem indicando `gitpr --init` naquele repositório.

---

## 5. Notas e Limitações por Forge

### 5.1 GitHub

- Instalações existentes mantêm o comportamento exato (byte-paridade): payload, cabeçalho `Authorization: token` e o armazenamento legado `GITHUB_TOKEN_ENCRYPTED` permanecem inalterados.
- As sugestões de revisores são nativas (`requested_reviewers`); desative com `--no-suggest-reviewers`.

### 5.2 GitLab

- Merge requests: o identificador da API é o `iid` do MR — nunca o id global com escopo do projeto.
- Rascunhos: o GitLab não possui flag de draft ao criar um MR; por isso, o GitPR adiciona o prefixo `"Draft: "` ao título.
- Caminhos de repositório (grupos e subgrupos) são sempre URL-quoted.
- O parâmetro de estratégia de merge é ignorado — o GitLab faz o merge com a ação nativa dele.

### 5.3 Bitbucket Cloud

- As credenciais são HTTP Basic: usuário + App Password. O username é obrigatório (`GITPR_SCM_USERNAME`) e faz parte da credencial.
- Issues exigem o Issue Tracker habilitado no repositório.
- Estratégias de merge: `merge` -> `merge_commit`, `squash` e `fast_forward`.

### 5.4 Azure DevOps

- `organization` e `project` são obrigatórios — o erro fail-fast indica as variáveis de ambiente ausentes.
- Toda chamada REST leva `api-version=7.1`.
- Os refs de branch usam o prefixo `refs/heads/`.
- Sem diff unificado de PR via REST: `get_pull_request_diff()` retorna um resumo textual por arquivo (`path (+adds −dels)`) da última iteração.
- Issues não são suportadas (`ScmNotSupportedError`) — salve o rascunho localmente com F2.
- Remotes legados `*.visualstudio.com` são aceitos pelo detector.

---

## 6. Para Desenvolvedores e Plugins

A abstração vive em `src/infrastructure/scm/`: o contrato `ScmProvider` em `base.py`, um provider concreto por forge e o registro em `factory.py`. O código interno resolve providers somente por meio de `resolve_scm_provider()` e nunca importa as classes concretas diretamente. Os métodos dos providers levantam `ScmProviderError(provider, http_status, message)` — `http_status` é `0` em falhas de rede — ou `ScmNotSupportedError` quando o forge não possui operação equivalente. Eles nunca retornam as tuplas legadas `(ok, data, status)`.

O `src/github_api.py` é um **shim obsoleto**: ainda expõe as quatro funções legadas com retornos em tupla para integrações de terceiros, mas toda chamada levanta um `DeprecationWarning`. Código novo e plugins devem usar `resolve_scm_provider()`.

### 6.1 Contrato para Provedores de Terceiros (quebra desde a v1.2.0)

O `ScmProvider.request_pull_request_reviewers()` retornava `None`. Desde a **v1.2.0** ele retorna `list[str]`: os logins que o forge **realmente anexou**, relidos do corpo da resposta. Lista vazia significa "aceito, mas ignorado" — é assim que o GitPR detecta um revisor que o forge descartou em silêncio.

| | Até a v1.1.x | Desde a v1.2.0 |
| --- | --- | --- |
| Tipo de retorno | `None` | `list[str]` (logins anexados) |
| `[]` | — | Pedido aceito, ninguém anexado |
| Padrão na classe base | `ScmNotSupportedError` | `ScmNotSupportedError` (inalterado) |

**Quem é afetado:** apenas subclasses que **sobrescrevem** o método. Quem só o chama não é afetado. Uma subclasse que não o sobrescreve continua levantando `ScmNotSupportedError`, como antes.

**Como migrar:** devolva o que o forge anexou. Se o forge não devolve corpo, devolva a lista que você recebeu para anexar — é otimista e desliga o aviso de "não anexado" para esse forge.

```python
class MyForgeProvider(ScmProvider):
    def request_pull_request_reviewers(self, repo, pr_id, reviewers) -> list[str]:
        body = self._post_reviewers(repo, pr_id, reviewers)
        return [r["login"] for r in body.get("requested_reviewers", [])]
        # O forge não devolve corpo? Use `return list(reviewers)`.
```

Uma sobrescrita legada que ainda retorna `None` continua funcionando: o chamador a interpreta como "não dá para verificar" e pula o aviso de "não anexado". É tolerada, não recomendada. Registro da decisão: [ADR-0009](adr/0009-reviewer-attach-returns-read-back.md).

Registro de decisão de arquitetura e vocabulário canônico: [ADR-001 Abstração SCM](plans/ADR-001-scm-abstraction.md) e [Glossário SCM Multi-Forge](plans/glossary-scm-multiforge.md).

> **Nota:** Consulte também a [documentação de integração do GitHub PAT](github-pat-integration.md) para criar tokens e entender a criptografia do GitPR (Fernet).
