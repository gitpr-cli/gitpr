# Plano de Execução — Nota de Migração de SCM por Repositório e Provisionamento Automatizado

- **Data:** 2026-11-10
- **Branch:** `develop_natan`
- **Task:** `scm_per_repo_migration_note`
- **Referência:** `docs/survey/20261110_scm_per_repo_migration_note_surveyfacts.md`

---

## 1. Objetivos

Formalizar e consolidar a governança e documentação técnica da migração do SCM por repositório, garantindo que scripts de provisionamento automatizado de máquinas, contêineres e CI/CD conheçam os slots dedicados por forge (`<FORGE>_TOKEN_ENCRYPTED`, `<FORGE>_BASE_URL`) e a remoção automática das chaves legadas globais (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`).

---

## 2. Ações Planejadas

### Componente 1: Architectural Decision Record (`docs/adr/0020-per-repo-scm-provisioning-migration.md`)
- Criar o ADR 0020 seguindo o padrão canônico do repositório em `docs/adr/`.
- Documentar:
  - Contexto do problema: transição da máquina para o repositório e a remoção das chaves globais pela migração automática.
  - Decisões adotadas: slots por forge no `.env`, separação entre credenciais estáticas de máquina e overrides de projeto (`.gitpr/conf/gitpr.config.yml`), preservação do `GITPR_SCM_TOKEN` cru para CI.
  - Impacto e orientações para scripts de provisionamento automatizado (Ansible, Chef, Dockerfiles, devcontainer setups, dotfiles).
  - Consequências e alternativas consideradas.

### Componente 2: Seção 3.1 em `docs/scm-multiforge.*.md` (5 idiomas)
- Adicionar a subseção `3.1 Migration Note: Automated Provisioning & Per-Forge Slots` (e equivalentes localizados) em:
  - `docs/scm-multiforge.md` (EN)
  - `docs/scm-multiforge.pt_br.md` (PT-BR)
  - `docs/scm-multiforge.pt_pt.md` (PT-PT)
  - `docs/scm-multiforge.es_es.md` (ES-ES)
  - `docs/scm-multiforge.fr_fr.md` (FR-FR)
- Incluir callout `> [!WARNING]` alertando explicitamente que:
  - `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` são limpas do `.env` pela migração automática one-shot.
  - Automações devem provisionar diretamente os slots correspondentes (`GITHUB_TOKEN_ENCRYPTED`, `GITLAB_TOKEN_ENCRYPTED`, `BITBUCKET_TOKEN_ENCRYPTED`, `AZURE_DEVOPS_TOKEN_ENCRYPTED`).
  - Para forges self-hosted em domínios customizados, o provisionamento deve gravar o override no arquivo do projeto (`.gitpr/conf/gitpr.config.yml` -> `scm.provider`).

### Componente 3: Modelo de Domínio e Glossário (`CONTEXT.md`)
- Adicionar ao glossário em `CONTEXT.md` os termos:
  - `Forge token slot`: O slot de variável de ambiente específico de cada forge para armazenamento de tokens cifrados.
  - `Legacy SCM provisioning keys`: O trio descontinuado `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL`.
  - `Per-forge SCM provisioning`: O padrão de provisionamento onde variáveis de ambiente de credenciais são configuradas por provedor.

### Componente 4: Teste de Paridade e Consistência (`tests/unit/test_scm_multiforge_docs_parity.py`)
- Criar teste automatizado garantindo:
  - Existência dos 5 arquivos `docs/scm-multiforge.*.md`.
  - Presença da Seção 3.1 em todos os 5 arquivos.
  - Menção às chaves legadas e aos slots por forge.
  - Referência cruzada ao ADR-0020.

### Componente 5: Alinhamento de Versão em `CLAUDE.md` e `GEMINI.md`
- Atualizar `- **Current version:** 1.6.0` para `1.7.0` em ambos os arquivos, garantindo que `tests/unit/test_version_consistency.py` fique 100% verde.
