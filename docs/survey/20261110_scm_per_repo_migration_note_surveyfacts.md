# Survey — Nota de Migração de SCM por Repositório e Provisionamento Automatizado

- **Data:** 2026-11-10
- **Branch:** develop_natan
- **Task:** scm_per_repo_migration_note
- **Método:** `/grill-with-docs` (grilling + domain-modeling)

---

## 1. Contexto e Problema

No relatório de status `docs/reports/relatorio_estado_v0.0.24.md` (e versões anteriores), constava o seguinte item herdado ainda em aberto:
> *"Nota de migração do SCM por repositório: as chaves `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` foram retiradas do `.env` pela migração automática. Quem automatizou a escrita dessas chaves precisa saber que agora há um slot por forge. Item herdado, ainda aberto."*

### Diagnóstico Técnico no Código
1. **Migração em `src/scm_settings.py`:**
   - A função `migrate_legacy_scm_config()` (chamada sob lock antes de qualquer resolução de SCM) detecta se as chaves antigas (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`) existem.
   - Ela transfere os valores para as chaves dedicadas por forge:
     - `GITHUB_TOKEN_ENCRYPTED` / `GITHUB_BASE_URL`
     - `GITLAB_TOKEN_ENCRYPTED` / `GITLAB_BASE_URL`
     - `BITBUCKET_TOKEN_ENCRYPTED` / `BITBUCKET_BASE_URL`
     - `AZURE_DEVOPS_TOKEN_ENCRYPTED` / `AZURE_DEVOPS_BASE_URL`
   - Em seguida, remove permanentemente as chaves legadas do arquivo `~/.gitpr/.env`.
   - Se scripts de provisionamento de máquinas, imagens Docker ou templates CI/CD continuarem gravando as chaves globais antigas no `.env`, a migração as remove ou os novos fluxos por forge não encontrarão o slot esperado caso o provider não esteja definido na mesma execução.
2. **Documentação Existente:**
   - A documentação técnica em `docs/scm-multiforge.*.md` aborda a resolução por repositório e a tabela manual de variáveis de ambiente na Seção 3, mas não possuía uma seção/callout formal de nota de migração alertando os autores de scripts de automação/provisionamento sobre a obsolescência das chaves globais e o redirecionamento para slots por forge.
   - O ADR-016 está localizado em `docs/plans/ADR-016-per-provider-scm-settings.md`, porém a pasta canônica de ADRs numerados do projeto é `docs/adr/`.
   - `CONTEXT.md` não possuía a formalização dos termos de domínio específicos para o provisionamento automatizado por forge e migração de slots legados.

---

## 2. Decisões Consolidadas (Grilling com o Usuário)

| Tópico | Decisão |
|---|---|
| **ADR Canônico** | Criar `docs/adr/0020-per-repo-scm-provisioning-migration.md` formalizando a governança da descontinuação das chaves globais de SCM, a automação de provisionamento e o modelo de slots dedicados por forge. |
| **Documentação Multi-Forge (5 idiomas)** | Criar a subseção `3.1 Migration Note: Automated Provisioning & Per-Forge Slots` em `docs/scm-multiforge.md` e suas 4 traduções (`pt_br`, `pt_pt`, `es_es`, `fr_fr`), com alerta explícito (`> [!WARNING]`) para mantenedores de scripts de provisionamento. |
| **Glossário e Modelo de Domínio (`CONTEXT.md`)** | Registrar os termos canônicos `Forge token slot`, `Legacy SCM provisioning keys` e `Per-forge SCM provisioning` com suas restrições e termos a evitar. |
| **Teste de Paridade** | Criar `tests/unit/test_scm_multiforge_docs_parity.py` validando que todos os 5 arquivos possuem a Seção 3.1 com a menção explícita às chaves legadas, aos novos slots por forge e ao ADR-0020. |
| **Alinhamento de Versão** | Atualizar `CLAUDE.md` e `GEMINI.md` para **1.7.0** para resolver as falhas pré-existentes de `tests/unit/test_version_consistency.py`. |

---

## 3. Matriz de Arquivos Afetados

| Arquivo | Ação | Descrição |
|---|---|---|
| `docs/adr/0020-per-repo-scm-provisioning-migration.md` | [NEW] | ADR formalizando a nota de migração de provisionamento e slots por forge |
| `docs/scm-multiforge.md` | [MODIFY] | Adicionar seção 3.1 com a nota de migração para scripts de automação (EN) |
| `docs/scm-multiforge.pt_br.md` | [MODIFY] | Adicionar seção 3.1 com a nota de migração para scripts de automação (PT-BR) |
| `docs/scm-multiforge.pt_pt.md` | [MODIFY] | Adicionar seção 3.1 com a nota de migração para scripts de automação (PT-PT) |
| `docs/scm-multiforge.es_es.md` | [MODIFY] | Adicionar seção 3.1 com a nota de migração para scripts de automação (ES-ES) |
| `docs/scm-multiforge.fr_fr.md` | [MODIFY] | Adicionar seção 3.1 com a nota de migração para scripts de automação (FR-FR) |
| `CONTEXT.md` | [MODIFY] | Adicionar termos ubíquos de provisionamento de forge e slots legados |
| `tests/unit/test_scm_multiforge_docs_parity.py` | [NEW] | Teste unitário de paridade de documentação e link com ADR |
| `CLAUDE.md` | [MODIFY] | Alinhar versão com SSOT (1.7.0) |
| `GEMINI.md` | [MODIFY] | Alinhar versão com SSOT (1.7.0) |
