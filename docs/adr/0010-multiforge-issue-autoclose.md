# 0010 — Fechamento automático de issue multi-forge (GitLab, Bitbucket, Azure)

- **Status:** Aceito
- **Data:** 2026-11-06
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** Expansão da feature de autoclose (`get_issue`, `get_default_branch`, `closing_line`) de GitHub-only para multi-forge.

## Contexto e Decisão

O fechamento automático de issues foi originalmente concebido como GitHub-only (ADR-003 da SPEC). Os métodos `get_issue()`, `get_default_branch()` e `closing_line()` na classe base `ScmProvider` levantavam `ScmNotSupportedError` por padrão, e guardas hardcoded `provider_is_github()` impediam a execução em outros forges. Além disso, o registro local residia no arquivo com nome acoplado `.gitpr/conf/github.yml`.

Decidimos estender a arquitetura para ser multi-forge:

1. **GitLab e Bitbucket Provider:**
   - **GitLab:** Implementa `get_issue` (`GET /projects/:id/issues/:issue_iid`), normalizando o estado `"opened"` para `is_open=True, state="open"`. Implementa `get_default_branch` (`GET /projects/:id`) e `closing_line` devolvendo `Closes #{number}`.
   - **Bitbucket Cloud:** Implementa `get_issue` (`GET /2.0/repositories/{workspace}/{repo_slug}/issues/{number}`), normalizando os estados abertos `{"new", "open", "on hold"}` para `is_open=True, state="open"`. Trata repositórios sem issue tracker habilitado (HTTP 404) como issue ausente, limpando silenciosamente o registro. Implementa `get_default_branch` (`mainbranch.name`) e `closing_line` devolvendo `close #{number}`.

2. **Azure DevOps Provider:**
   - Implementa `get_default_branch` nativo via API de repositórios Git do Azure Repos (`GET _repo_url(repo)?api-version=7.1`).
   - Mantém `get_issue` e `closing_line` levantando `ScmNotSupportedError`, uma vez que o Azure DevOps utiliza Azure Boards (*Work Items*) e não possui recurso REST de issues associado ao repositório Git. O fluxo de PR degrada elegantemente para inativo no Azure sem quebrar.

3. **Generalização do Registro Local e Migração:**
   - O arquivo de registro passa a ser `.gitpr/conf/issue.yml`.
   - Adicionado o campo `provider: str = "github"` à dataclass `RegisteredIssue` e ao schema YAML (`schema_version: 1`).
   - Leitura com fallback retrocompatível: se `issue.yml` não existir mas `github.yml` existir, o arquivo legado é carregado.
   - Na primeira gravação via `record()`, os dados são gravados em `issue.yml` e o legado `github.yml` é removido.
   - `clear()` remove ambos os arquivos caso existam.
   - `.gitignore` passa a registrar `.gitpr/conf/issue.yml`.

4. **Polimorfismo no Fluxo:**
   - Remoção de guardas acopladas `provider_is_github()` em `register_created_issue`, `resolve_close_issue` e `issue_app.py`.
   - Captura graciosa de `ScmNotSupportedError` ao consultar issue ou closing line, marcando o resultado como `skipped_reason="not-supported"`.
   - Telemetria de criação de issue em `issue_app.py` padronizada como `command=f"issue:{provider.name}_create"`.

## Opções Consideradas

- **Manter o nome do arquivo como `.gitpr/conf/github.yml`:** Rejeitado. Criaria confusão em projetos hospedados em GitLab/Bitbucket e violaria a integridade conceitual do modelo de domínio.
- **Arquivo de registro separado por forge (`.gitpr/conf/<forge>.yml`):** Rejeitado. Como o gitpr trabalha com o contexto do repositório ativo e a última issue criada pelo usuário, um único arquivo canônico `.gitpr/conf/issue.yml` simplifica o ciclo de vida.
- **Implementar Work Items no Azure DevOps para simular issues:** Rejeitado. Work Items dependem de processos variáveis de Boards (Scrum, Agile, CMMI) e não possuem uma rota padronizada de issues Git.

## Consequências

- Usuários do GitLab e Bitbucket ganham fechamento automático de issues nativo nos Pull Requests / Merge Requests.
- Repositórios com `.gitpr/conf/github.yml` migram automaticamente sem perda de dados na próxima execução.
- O contrato de `IssueInfo` passa a fornecer `is_open: bool`, isolando as variações léxicas de estado de cada plataforma.
