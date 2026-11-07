# Documentação Técnica: SCM Multi-Forge (ScmProvider)

O GitPR publica Pull Requests e issues através de uma única abstração, o `ScmProvider`, que suporta quatro forges de alojamento Git: GitHub, GitLab, Bitbucket Cloud e Azure DevOps. Todos os fluxos de publicação — o publicador interativo de PR (modo predefinido), a publicação direta (`--no-edit`) e a TUI de issues (`-is`) — resolvem o provider **do repositório onde estão a ser executados** e chamam a API do forge através dele.

O forge pertence ao repositório, não à máquina: o GitPR deteta-o a partir do remote `origin` (ou lê um override explícito versionado com o projeto) e mantém **um token encriptado por forge** em `~/.gitpr/.env`. Uma máquina pode, portanto, trabalhar com um repositório GitLab e um repositório GitHub ao mesmo tempo, cada um com a sua credencial.

Sem configuração de SCM, o GitPR mantém o comportamento legado exclusivo do GitHub — zero migração e saída byte-idêntica.

---

## 1. Forges Suportados

| Forge | Chave do provider | Base da API predefinida | Autenticação |
| --- | --- | --- | --- |
| GitHub | `github` | `https://api.github.com` | Personal Access Token (PAT) |
| GitLab | `gitlab` | `https://gitlab.com/api/v4` | Personal Access Token (PAT) |
| Bitbucket Cloud | `bitbucket` | `https://api.bitbucket.org/2.0` | Nome de utilizador + App Password (HTTP Basic) |
| Azure DevOps | `azure_devops` | `https://dev.azure.com` | Personal Access Token (PAT) |

### 1.1 Qual o Forge que um Repositório Usa

O forge é resolvido por repositório, nesta ordem:

1. **Override do projeto** — `scm.provider` em `.gitpr/conf/gitpr.config.yml`, versionado com o repositório. Vence sempre, e é assim que se corrige um host self-managed cujo domínio não nomeia o forge.
2. **Deteção do remote origin** — correspondência de substring, sem diferenciar maiúsculas de minúsculas, no URL do `origin`.
3. **`github`** — a predefinição histórica.

| O URL do remote contém | Provider |
| --- | --- |
| `gitlab` | `gitlab` |
| `bitbucket` | `bitbucket` |
| `dev.azure.com` ou `visualstudio.com` | `azure_devops` |
| qualquer outra coisa (predefinido) | `github` |

```yaml
# .gitpr/conf/gitpr.config.yml — versione para partilhar o forge com a equipa
scm:
  provider: gitlab
```

Um valor desconhecido no ficheiro de projeto é ignorado com um aviso (um ficheiro malformado nunca pode derrubar todos os comandos), e a deteção decide no lugar dele.

```bash
git remote get-url origin
# git@github.com:gitpr-cli/gitpr.git               -> github (predefinido)
# https://gitlab.com/acme/platform/web-app.git     -> gitlab
# https://bitbucket.org/acme/web-app               -> bitbucket
# https://dev.azure.com/acme/project/_git/web-app  -> azure_devops
```

O repositório é endereçado através do `RepoRef`, extraído do URL do remote. O **workspace** é o proprietário (owner) do GitHub, o namespace do GitLab (incluindo subgrupos), o workspace do Bitbucket ou — no Azure DevOps — um rótulo `{org}/{project}` apenas para exibição, pois as chamadas de API usam o `organization` e o `project` da configuração.

---

## 2. Configuração Inicial — `gitpr --init`

O wizard interativo deteta o forge, valida o token de acesso e persiste a configuração:

```bash
gitpr --init
```

| Passo | O que acontece |
| --- | --- |
| 1. Deteção do forge | Deteta o forge a partir do remote `origin` e pede confirmação (pode escolher outro forge; um host que não nomeia forge é perguntado, nunca presumido) |
| 2. Extras do provider | O Azure DevOps pede `organization` e `project`; o Bitbucket pede o `username`, que faz parte da credencial |
| 3. Base da API | Base da API personalizada para todos os forges, exceto GitHub; o valor já guardado para esse forge é oferecido como predefinição |
| 4. Token | Pede o PAT — ou a App Password no Bitbucket |
| 5. Validação | `test_connection()` — até 3 tentativas; HTTP 401 (token expirado) volta a pedir com aviso amarelo; outras falhas abortam a vermelho |
| 6. Persistência | Apenas em caso de sucesso: guarda o token encriptado com Fernet no slot do seu forge (`GITLAB_TOKEN_ENCRYPTED`, …), a base da API e os extras, e regista `scm.provider` no ficheiro de projeto **apenas quando o forge escolhido difere do detetado** |

Nada é guardado quando a validação falha. Execute `gitpr --init` novamente em cada repositório para mudar de forge ou renovar um token expirado; os tokens dos outros forges ficam intactos. Valores de versões anteriores (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`) são migrados automaticamente no primeiro comando após a atualização.

---

## 3. Configuração Manual (.env)

Alternativa ao wizard: edite o `~/.gitpr/.env` diretamente. Consulte o [guia de integração do GitHub PAT](github-pat-integration.md) para perceber como o GitPR protege os tokens em repouso.

| Variável | Forge | Descrição |
| --- | --- | --- |
| `GITPR_SCM_TOKEN` | todos | Token cru, apenas para ambientes de CI/CD — único e global, consultado antes de qualquer token guardado |
| `GITHUB_TOKEN_ENCRYPTED` | `github` | Token encriptado com Fernet do forge GitHub |
| `GITLAB_TOKEN_ENCRYPTED` | `gitlab` | Token encriptado com Fernet do forge GitLab |
| `BITBUCKET_TOKEN_ENCRYPTED` | `bitbucket` | Token encriptado com Fernet do forge Bitbucket |
| `AZURE_DEVOPS_TOKEN_ENCRYPTED` | `azure_devops` | Token encriptado com Fernet do forge Azure DevOps |
| `GITHUB_BASE_URL` / `GITLAB_BASE_URL` / `BITBUCKET_BASE_URL` / `AZURE_DEVOPS_BASE_URL` | próprio forge | Base da API personalizada (self-managed/enterprise); vazio = SaaS público |
| `GITPR_SCM_ORGANIZATION` | `azure_devops` | Nome da organização — obrigatório (erro fail-fast indica a variável em falta) |
| `GITPR_SCM_PROJECT` | `azure_devops` | Nome do projeto — obrigatório |
| `GITPR_SCM_USERNAME` | `bitbucket` | Nome de utilizador do Bitbucket — obrigatório (App Password usa HTTP Basic) |

Cada forge lê apenas o seu slot: um token de GitLab nunca responde por um repositório GitHub. O GitHub sem configuração de SCM mantém o armazenamento `GITHUB_TOKEN_ENCRYPTED` — zero migração.

---

## 4. Usar o GitPR com o Forge Configurado

### 4.1 Publicação de Pull Requests

```bash
gitpr                # Publicador interativo (TUI) — reveja e confirme o PR
gitpr --no-edit      # Publica diretamente, com auto-commit (salta a TUI)
gitpr --no-publish   # Gera apenas o ficheiro de descrição do PR (.md), sem TUI
```

O publicador resolve o provider a partir do remote `origin`, converte o repositório num `RepoRef` e cria o pull request através de `provider.create_pull_request()`. O número, o URL e o estado do PR devolvidos pelo forge são apresentados na TUI e guardados no ficheiro de saída.

### 4.2 Issues

```bash
gitpr -is            # Fluxo de issue: rascunho com IA -> TUI -> F3 cria a issue no forge
```

F3 chama `provider.create_issue()` no forge configurado. O Azure DevOps não possui recurso de API para issues (os Work Items dependem do process template do projeto); por isso, o GitPR indica que deve guardar o rascunho localmente com F2. O Bitbucket exige que o **Issue Tracker** do repositório esteja ativado; caso contrário, a API responde 404.

### 4.3 Expiração do Token e Reautenticação (HTTP 401)

Quando o token é rejeitado (HTTP 401), o GitPR remove o token expirado do slot **daquele** forge e pede um novo — até 3 tentativas. Prefira os fluxos interativos (`gitpr`, `gitpr -is`) para reautenticar: o `--no-edit` publica diretamente e não pode voltar a pedir.

Uma execução não interativa (hooks do git, servidor MCP, CI) nunca pede e nunca apaga a credencial guardada: para com uma mensagem a indicar `gitpr --init` nesse repositório.

---

## 5. Notas e Limitações por Forge

### 5.1 GitHub

- Instalações existentes mantêm o comportamento exato (byte-paridade): payload, cabeçalho `Authorization: token` e o armazenamento legado `GITHUB_TOKEN_ENCRYPTED` permanecem inalterados.
- As sugestões de revisores são nativas (`requested_reviewers`); desative com `--no-suggest-reviewers`.

### 5.2 GitLab

- Merge requests: o identificador da API é o `iid` do MR — nunca o id global com âmbito de projeto.
- Rascunhos: o GitLab não possui flag de draft ao criar um MR; por isso, o GitPR adiciona o prefixo `"Draft: "` ao título.
- Caminhos de repositório (grupos e subgrupos) são sempre URL-quoted.
- O parâmetro de estratégia de merge é ignorado — o GitLab faz o merge com a ação nativa dele.

### 5.3 Bitbucket Cloud

- As credenciais são HTTP Basic: nome de utilizador + App Password. O username é obrigatório (`GITPR_SCM_USERNAME`) e faz parte da credencial.
- As issues exigem o Issue Tracker ativado no repositório.
- Estratégias de merge: `merge` -> `merge_commit`, `squash` e `fast_forward`.

### 5.4 Azure DevOps

- `organization` e `project` são obrigatórios — o erro fail-fast indica as variáveis de ambiente em falta.
- Todas as chamadas REST levam `api-version=7.1`.
- Os refs de branch usam o prefixo `refs/heads/`.
- Sem diff unificado de PR via REST: `get_pull_request_diff()` devolve um resumo textual por ficheiro (`path (+adds −dels)`) da última iteração.
- As issues não são suportadas (`ScmNotSupportedError`) — guarde o rascunho localmente com F2.
- Os remotes legados `*.visualstudio.com` são aceites pelo detector.

---

## 6. Para Programadores e Plugins

A abstração vive em `src/infrastructure/scm/`: o contrato `ScmProvider` em `base.py`, um provider concreto por forge e o registo em `factory.py`. O código interno resolve providers apenas através de `resolve_scm_provider()` e nunca importa as classes concretas diretamente. Os métodos dos providers levantam `ScmProviderError(provider, http_status, message)` — `http_status` é `0` em falhas de rede — ou `ScmNotSupportedError` quando o forge não possui operação equivalente. Nunca devolvem as tuplas legadas `(ok, data, status)`.

O `src/github_api.py` é um **shim obsoleto**: ainda expõe as quatro funções legadas com devoluções em tupla para integrações de terceiros, mas todas as chamadas levantam um `DeprecationWarning`. Código novo e plugins devem usar `resolve_scm_provider()`.

### 6.1 Contrato para Fornecedores de Terceiros (quebra desde a v1.2.0)

O `ScmProvider.request_pull_request_reviewers()` devolvia `None`. Desde a **v1.2.0** devolve `list[str]`: os logins que o forge **realmente associou**, relidos do corpo da resposta. Lista vazia significa "aceite, mas ignorado" — é assim que o GitPR deteta um revisor que o forge descartou em silêncio.

| | Até à v1.1.x | Desde a v1.2.0 |
| --- | --- | --- |
| Tipo de devolução | `None` | `list[str]` (logins associados) |
| `[]` | — | Pedido aceite, ninguém associado |
| Predefinição na classe base | `ScmNotSupportedError` | `ScmNotSupportedError` (inalterado) |

**Quem é afetado:** apenas as subclasses que **substituem** o método. Quem apenas o chama não é afetado. Uma subclasse que não o substitui continua a levantar `ScmNotSupportedError`, como antes.

**Como migrar:** devolva o que o forge associou. Se o forge não devolve corpo, devolva a lista que recebeu para associar — é otimista e desliga o aviso de "não associado" para esse forge.

```python
class MyForgeProvider(ScmProvider):
    def request_pull_request_reviewers(self, repo, pr_id, reviewers) -> list[str]:
        body = self._post_reviewers(repo, pr_id, reviewers)
        return [r["login"] for r in body.get("requested_reviewers", [])]
        # O forge não devolve corpo? Use `return list(reviewers)`.
```

Uma substituição legada que ainda devolve `None` continua a funcionar: o chamador interpreta-a como "não é possível verificar" e salta o aviso de "não associado". É tolerada, não recomendada. Registo da decisão: [ADR-0009](adr/0009-reviewer-attach-returns-read-back.md).

Registo de decisão de arquitetura e vocabulário canónico: [ADR-001 Abstração SCM](plans/ADR-001-scm-abstraction.md) e [Glossário SCM Multi-Forge](plans/glossary-scm-multiforge.md).

> **Nota:** Consulte também a [documentação de integração do GitHub PAT](github-pat-integration.md) para criar tokens e compreender a encriptação do GitPR (Fernet).
