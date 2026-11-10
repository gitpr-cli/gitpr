# Implementation Plan — Nota de Migração de SCM por Repositório e Provisionamento Automatizado

## Goal Description
Documentar e formalizar a nota de migração do SCM por repositório para scripts de provisionamento automatizado de ambientes e CI/CD. As chaves legadas `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` são removidas automaticamente do `~/.gitpr/.env` pela migração de runtime em favor de slots específicos por forge (`<FORGE>_TOKEN_ENCRYPTED` e `<FORGE>_BASE_URL`). É necessário orientar scripts de provisionamento sobre a nova estrutura, formalizar o ADR-0020, atualizar a documentação nos 5 idiomas suportados, enriquecer o glossário do `CONTEXT.md` e validar tudo através de testes unitários de paridade. Aproveitaremos também para sincronizar a versão em `CLAUDE.md` e `GEMINI.md` para 1.7.0.

## User Review Required
> [!NOTE]
> As decisões de arquitetura e escopo foram alinhadas na sessão de grilling com o usuário:
> - ADR canônico `0020-per-repo-scm-provisioning-migration.md` em `docs/adr/`.
> - Seção 3.1 dedicada nos 5 idiomas em `docs/scm-multiforge.*.md`.
> - Formalização dos termos no glossário em `CONTEXT.md`.
> - Criação de teste de paridade de documentação `test_scm_multiforge_docs_parity.py`.
> - Alinhamento da versão 1.7.0 em `CLAUDE.md` e `GEMINI.md`.

## Proposed Changes

### Documentation & Architecture Decision Records

#### [NEW] `docs/adr/0020-per-repo-scm-provisioning-migration.md`
- Formalizar a decisão arquitetural da transição do modelo global de máquina para o modelo de resolução por repositório e slots dedicados por forge.
- Detalhar a quebra de scripts de provisionamento e o comportamento da remoção automática das chaves legadas.
- Documentar diretrizes para provisionadores de ambiente (Ansible, Docker, devcontainers, CI).

#### [MODIFY] `docs/scm-multiforge.md` (EN)
- Adicionar a subseção `3.1 Migration Note: Automated Provisioning & Per-Forge Slots` com callout `> [!WARNING]`, orientando como migrar scripts de provisionamento e referenciando o ADR-0020.

#### [MODIFY] `docs/scm-multiforge.pt_br.md` (PT-BR)
- Adicionar a subseção `3.1 Nota de Migração: Provisionamento Automatizado e Slots por Forge` com callout `> [!WARNING]` equivalente em português do Brasil.

#### [MODIFY] `docs/scm-multiforge.pt_pt.md` (PT-PT)
- Adicionar a subseção `3.1 Nota de Migração: Provisionamento Automatizado e Slots por Forge` com callout `> [!WARNING]` equivalente em português europeu.

#### [MODIFY] `docs/scm-multiforge.es_es.md` (ES-ES)
- Adicionar a subseção `3.1 Nota de Migración: Aprovisionamiento Automatizado y Slots por Forge` com callout `> [!WARNING]` equivalente em espanhol.

#### [MODIFY] `docs/scm-multiforge.fr_fr.md` (FR-FR)
- Adicionar a subseção `3.1 Note de Migration : Provisionnement Automatisé et Slots par Forge` com callout `> [!WARNING]` equivalente em francês.

---

### Domain Modeling & Project Configuration

#### [MODIFY] `CONTEXT.md`
- Adicionar na seção de glossário os termos:
  - `Forge token slot`
  - `Legacy SCM provisioning keys`
  - `Per-forge SCM provisioning`

#### [MODIFY] `CLAUDE.md`
- Atualizar `- **Current version:** 1.6.0` para `1.7.0`.

#### [MODIFY] `GEMINI.md`
- Atualizar `- **Current version:** 1.6.0` para `1.7.0`.

---

### Automated Tests

#### [NEW] `tests/unit/test_scm_multiforge_docs_parity.py`
- Testar a existência dos 5 arquivos `docs/scm-multiforge.*.md`.
- Testar a presença da Seção 3.1 em todos os 5 arquivos.
- Testar que as chaves legadas (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`) e os slots por forge (`GITHUB_TOKEN_ENCRYPTED`, etc.) são citados.
- Testar a referência cruzada ao ADR-0020 e ao `CONTEXT.md`.

---

## Verification Plan

### Automated Tests
Executar os testes de paridade de documentação e consistência de versão:
```bash
python -m pytest tests/unit/test_scm_multiforge_docs_parity.py -v
python -m pytest tests/unit/test_version_consistency.py -v
python -m pytest tests/scm/ -v
```

### Manual Verification
- Inspecionar a renderização das seções 3 e 3.1 nos 5 arquivos de documentação do SCM Multi-Forge.
- Verificar que o ADR-0020 possui links funcionais para a documentação e para o ADR-016.
