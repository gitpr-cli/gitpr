## Completion Report — Nota de Migração de SCM por Repositório e Provisionamento Automatizado

### What was done
- Formalizamos e consolidamos a governança arquitetural da nota de migração do SCM por repositório para scripts de provisionamento e infraestrutura automatizada.
- Redigimos o Architectural Decision Record canônico [`docs/adr/0020-per-repo-scm-provisioning-migration.md`](../../../adr/0020-per-repo-scm-provisioning-migration.md) documentando contexto, decisões, regras para scripts de automação (Ansible, Docker, devcontainers, CI) e descontinuação permanente de `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL`.
- Adicionamos a subseção `3.1 Migration Note: Automated Provisioning & Per-Forge Slots` com callout `> [!WARNING]` nas documentações técnicas de referência em todos os 5 idiomas suportados (`docs/scm-multiforge.*.md`).
- Adicionamos os termos de domínio canônicos `Forge token slot`, `Legacy SCM provisioning keys` e `Per-forge SCM provisioning` no [`CONTEXT.md`](../../../../CONTEXT.md).
- Sincronizamos a versão do projeto em [`CLAUDE.md`](../../../../CLAUDE.md) e [`GEMINI.md`](../../../../GEMINI.md) para `1.7.0`, alinhando com a SSOT em `src/updater.py`.
- Criamos a suíte de testes unitários [`tests/unit/test_scm_multiforge_docs_parity.py`](../../../../tests/unit/test_scm_multiforge_docs_parity.py) verificando paridade dos 5 idiomas, menção às chaves legadas e novos slots, além de referências cruzadas ao ADR-0020 e ao `CONTEXT.md`.
- Salvamos os artefatos de processo em `docs/survey/` e `docs/plans/` de acordo com a skill `/grill-with-docs`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/adr/0020-per-repo-scm-provisioning-migration.md` | feat | Novo ADR formalizando a nota de migração para scripts de provisionamento |
| `docs/scm-multiforge.md` | docs | Adição da subseção 3.1 com alerta de migração de provisionamento (EN) |
| `docs/scm-multiforge.pt_br.md` | docs | Adição da subseção 3.1 com alerta de migração de provisionamento (PT-BR) |
| `docs/scm-multiforge.pt_pt.md` | docs | Adição da subseção 3.1 com alerta de migração de provisionamento (PT-PT) |
| `docs/scm-multiforge.es_es.md` | docs | Adição da subseção 3.1 com alerta de migração de provisionamento (ES-ES) |
| `docs/scm-multiforge.fr_fr.md` | docs | Adição da subseção 3.1 com alerta de migração de provisionamento (FR-FR) |
| `CONTEXT.md` | docs | Inclusão de termos ubíquos de provisionamento de forge e slots legados |
| `CLAUDE.md` | docs | Atualização de versão para 1.7.0 (alinhamento SSOT) |
| `GEMINI.md` | docs | Atualização de versão para 1.7.0 (alinhamento SSOT) |
| `tests/unit/test_scm_multiforge_docs_parity.py` | test | Teste automatizado de paridade dos 5 idiomas e referências do ADR-0020 |
| `docs/survey/20261110_scm_per_repo_migration_note_surveyfacts.md` | docs | Fatos e decisões levantados na sessão de grilling |
| `docs/plans/develop_natan/20261110_scm_per_repo_migration_note_plansfacts.md` | docs | Fatos do plano de execução gerados na sessão |
| `docs/gemini/plans/develop_natan/2026-11-10_develop_natan_scm_per_repo_migration_note.md` | docs | Plano formal Gemini |
| `docs/gemini/walkthrough/develop_natan/2026-11-10_scm_per_repo_migration_note.md` | docs | Walkthrough formal Gemini |

### Impact
- **Functionality:** Scripts de provisionamento automatizado de imagens base e máquinas contam agora com diretrizes contratuais claras em todas as superfícies de documentação sobre a descontinuação das chaves globais e a adoção de slots por forge no `.env`.
- **Performance:** Zero overhead de runtime; puramente governança, documentação, metadados e testes.
- **Compatibility:** Totalmente compatível. Fecha o item herdado aberto do relatório de status e garante 100% de integridade e consistência da suíte de testes (`test_version_consistency.py` e `test_scm_multiforge_docs_parity.py`).

### Next steps (if applicable)
- Nenhum. O débito de documentação da nota de migração do SCM por repositório está formalizado, testado e completamente encerrado.
