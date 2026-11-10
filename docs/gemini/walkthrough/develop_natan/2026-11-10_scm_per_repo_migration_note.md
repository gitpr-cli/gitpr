# Walkthrough — Nota de Migração de SCM por Repositório e Provisionamento Automatizado

- **Data:** 2026-11-10
- **Branch:** `develop_natan`
- **Task:** `scm_per_repo_migration_note`

## Resumo das Alterações Realizadas

Formalizamos a nota de migração do SCM por repositório para scripts de provisionamento e automações de infraestrutura. Esclarecemos que as chaves globais legadas `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` são removidas automaticamente do arquivo `~/.gitpr/.env` na primeira execução pela migração de runtime, orientando as equipes a provisionarem diretamente os slots dedicados por forge e a utilizarem o arquivo versionado de projeto `.gitpr/conf/gitpr.config.yml` para overrides em domínios customizados.

### 1. Architectural Decision Record (ADR-0020)
- Criado [0020-per-repo-scm-provisioning-migration.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/adr/0020-per-repo-scm-provisioning-migration.md) formalizando a decisão arquitetural, histórico de migração, impacto em scripts de provisionamento (Ansible, Docker, devcontainers, CI) e orientações canônicas.

### 2. Documentação Técnica em 5 Idiomas
Adicionada a subseção dedicada `3.1 Migration Note: Automated Provisioning & Per-Forge Slots` (com alerta `> [!WARNING]`) em todas as variantes linguísticas de `scm-multiforge`:
- [docs/scm-multiforge.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.md) (EN)
- [docs/scm-multiforge.pt_br.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.pt_br.md) (PT-BR)
- [docs/scm-multiforge.pt_pt.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.pt_pt.md) (PT-PT)
- [docs/scm-multiforge.es_es.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.es_es.md) (ES-ES)
- [docs/scm-multiforge.fr_fr.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.fr_fr.md) (FR-FR)

### 3. Modelo de Domínio e Glossário
- Atualizado [CONTEXT.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CONTEXT.md) com os termos ubíquos:
  - `Forge token slot`
  - `Legacy SCM provisioning keys`
  - `Per-forge SCM provisioning`

### 4. Alinhamento de Versão SSOT
- Sincronizados [CLAUDE.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CLAUDE.md) e [GEMINI.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/GEMINI.md) para a versão `1.7.0` (SSOT em `src/updater.py`).

### 5. Teste Automatizado de Paridade
- Criado [tests/unit/test_scm_multiforge_docs_parity.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/unit/test_scm_multiforge_docs_parity.py) com 3 testes unitários garantindo:
  - Presença da Seção 3.1 nos 5 idiomas.
  - Citação de todas as chaves legadas e novos slots por forge.
  - Link com o ADR-0020 e registro dos termos no `CONTEXT.md`.

---

## Verificação e Resultados

Executamos as suítes de testes automatizados com 100% de sucesso:
1. `python -m pytest tests/unit/test_scm_multiforge_docs_parity.py -v`: 3 passed em 0.50s.
2. `python -m pytest tests/unit/test_version_consistency.py -v`: 5 passed em 0.15s (CLAUDE.md e GEMINI.md agora sincronizados).
3. `python -m pytest tests/scm/ -v`: 368 passed, 2 skipped, 21 subtests passed em 8.38s.
