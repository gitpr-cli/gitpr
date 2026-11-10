# ADR-0020 — Nota de Migração de SCM por Repositório e Provisionamento Automatizado

- **Status:** Aceito
- **Data:** 2026-11-10
- **Contexto:** Governança e orientação para scripts de provisionamento de máquinas, imagens de contêiner e automações após a migração do SCM de escopo global para escopo por repositório.
- **Relacionados:** [ADR-016](../plans/ADR-016-per-provider-scm-settings.md) (Forge por repositório e credencial por provider), [ADR-001](../plans/ADR-001-scm-abstraction.md) (Abstração SCM inicial)
- **Documentação de referência:** [Multi-Forge SCM (`docs/scm-multiforge.md`)](../scm-multiforge.md)
- **Glossário:** [SCM Multi-Forge Glossary](../plans/glossary-scm-multiforge.md), [CONTEXT.md](../../CONTEXT.md)

---

## 1. Contexto

Historicamente (introduzido no ADR-001), as configurações do provedor de hospedagem de código (SCM) eram definidas em variáveis de ambiente com escopo **global de máquina** gravadas no arquivo `~/.gitpr/.env`:
- `GITPR_SCM_PROVIDER`: identificava o provedor ativo (`github`, `gitlab`, `bitbucket`, `azure_devops`).
- `GITPR_SCM_TOKEN_ENCRYPTED`: token cifrado com Fernet compartilhado para qualquer forge configurado.
- `GITPR_SCM_BASE_URL`: URL base customizada da API para instâncias self-hosted / enterprise.

Conforme estabelecido pelo [ADR-016](../plans/ADR-016-per-provider-scm-settings.md), esse modelo causava severos conflitos em ambientes multi-projeto:
1. Uma máquina não podia operar concomitantemente com repositórios de forges distintos (ex.: um repositório interno GitLab e um repositório público GitHub).
2. O valor de `base_url` vazava entre provedores diferentes.
3. A resolução do provedor pertence conceitualmente ao **repositório** (baseado no remote `origin` ou no arquivo de projeto versionado `.gitpr/conf/gitpr.config.yml`), e não à máquina.

Para viabilizar a transição transparente, `src/scm_settings.py` implementou a migração automática one-shot (`migrate_legacy_scm_config()`), executada no primeiro comando de qualquer fluxo do GitPR. Essa rotina:
1. Move os valores legados para os novos slots dedicados por forge (`GITHUB_TOKEN_ENCRYPTED`, `GITLAB_TOKEN_ENCRYPTED`, `BITBUCKET_TOKEN_ENCRYPTED`, `AZURE_DEVOPS_TOKEN_ENCRYPTED` e respectivos `<FORGE>_BASE_URL`).
2. Remove permanentemente as linhas `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` do arquivo `~/.gitpr/.env`.

### O Problema com Scripts de Provisionamento Automatizado
Equipes de engenharia e operações que utilizavam ferramentas de automação (como Ansible, Chef, Puppet, Dockerfiles, devcontainers, dotfiles ou scripts bash) para provisionar ambientes locais ou runners de desenvolvimento frequentemente escreviam as chaves legadas diretamente no `~/.gitpr/.env`.

Com a introdução da resolução por repositório:
- As chaves gravadas por esses scripts são removidas silenciosamente na primeira execução.
- Se o script automatizado tentar reescrever as chaves legadas em execuções subsequentes ou omitir o provider correspondente, a resolução não localizará os slots dedicados por forge necessários para autenticação contra o host de destino.

---

## 2. Decisão

Formaliza-se a governança e o contrato de migração para scripts de provisionamento automatizado:

1. **Slots Dedicados por Forge no `.env`**:
   Scripts de provisionamento e automação que configuram `~/.gitpr/.env` devem gravar diretamente as credenciais nos slots específicos de cada forge:
   - GitHub: `GITHUB_TOKEN_ENCRYPTED` (e opcionalmente `GITHUB_BASE_URL`)
   - GitLab: `GITLAB_TOKEN_ENCRYPTED` (e opcionalmente `GITLAB_BASE_URL`)
   - Bitbucket: `BITBUCKET_TOKEN_ENCRYPTED` (e `GITPR_SCM_USERNAME` obrigatório)
   - Azure DevOps: `AZURE_DEVOPS_TOKEN_ENCRYPTED` (e `GITPR_SCM_ORGANIZATION` + `GITPR_SCM_PROJECT` obrigatórios)

2. **Descontinuação das Chaves Globais**:
   As chaves `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` são consideradas permanentemente descontinuadas (obsoletas). Qualquer escrita dessas chaves será consumida pela rotina de migração em tempo de execução e eliminada do arquivo de configuração local.

3. **Override de Forge em Self-Hosted / Domínios Customizados**:
   Quando uma forge utiliza domínio customizado que não contenha a substring identificadora do provedor (ex.: `git.empresa.com.br` para GitLab), o provisionamento **não deve** tentar forçar a forge globalmente no `.env`. O override deve ser versionado no arquivo de configuração do projeto:
   ```yaml
   # .gitpr/conf/gitpr.config.yml
   scm:
     provider: gitlab
   ```

4. **Ambientes CI/CD**:
   Em pipelines de integração contínua efêmeros (CI/CD) onde o token não é criptografado localmente em repouso, o uso da variável global `GITPR_SCM_TOKEN` (token cru em texto limpo) continua plenamente suportado e tem precedência máxima sobre qualquer slot gravado.

---

## 3. Consequências

### Positivas
- Elimina a ambiguidade em automações de setup de máquinas e ambientes de desenvolvimento.
- Permite que templates de provisionamento configurem credenciais para múltiplos forges simultaneamente em uma única máquina ou imagem base.
- Garante total conformidade com a arquitetura definida no ADR-016.

### Negativas / Riscos
- Scripts legados de provisionamento que dependiam da gravação estática de `GITPR_SCM_PROVIDER` precisarão ser atualizados para gravar os slots específicos e, quando aplicável, o arquivo de configuração do repositório `.gitpr/conf/gitpr.config.yml`.
