# Plano de Execução — Governança e Nota de Migração do `action.yml`

- **Data:** 2026-11-09
- **Branch:** `develop_natan`
- **Task:** `action_yml_migration_note`
- **Referência:** `docs/survey/20261109_action_yml_migration_note_surveyfacts.md`

---

## 1. Objetivos

Formalizar e consolidar a governança da quebra de contrato da composite action (`action.yml`), que substituiu a execução discreta de `--linter` + `--fullreview` pelo comando unificado `gitpr check`, gerador de SARIF 2.1.0 e relatórios padronizados.

## 2. Ações Planejadas

### Componente 1: Architectural Decision Record (`docs/adr/0011-action-unified-check-migration.md`)
- Criar o ADR 0011 no padrão canônico do repositório (análogo ao ADR-0009).
- Documentar:
  - Contexto da mudança (`action.yml` legada gerando `*_PR_FULLREVIEW.txt` vs moderna rodando `gitpr check`).
  - Decisões adotadas (adoção de SARIF 2.1.0, opcionalidade de chave de IA, supressões via baseline).
  - Opções consideradas e descartadas (manter steps separadas com flags legadas, manter geração de arquivo `.txt`).
  - Consequências e estratégia de migração orientada à Seção 7 de `docs/check-ci.md`.

### Componente 2: Metadados e Comentários no `action.yml`
- Adicionar comentário de cabeçalho no [action.yml](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/action.yml) alertando mantenedores sobre a quebra contratual desde a versão modernizada e fornecendo link direto para o guia de migração.

### Componente 3: Registro de Breaking Changes no `CHANGELOG.md`
- Atualizar o [CHANGELOG.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CHANGELOG.md) para explicitar a quebra de contrato do `action.yml` sob a seção pertinente, fornecendo contexto para equipes que atualizam workflows legados.

### Componente 4: Verificação e Testes
- Executar a suíte de testes de documentação (`pytest tests/unit/test_check_ci_docs_parity.py`).
- Executar testes de consistência geral (`pytest tests/unit/test_version_consistency.py`).
