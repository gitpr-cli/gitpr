# Plano de Execução — Formalização e Blindagem da Nota de Migração de GITPR_SKIP_UPDATE_CHECK

**Data:** 2026-11-11  
**Branch:** develop_natan  
**Task:** document_gitpr_skip_update_check_migration_note  

---

## 1. Objetivo

Fechar em definitivo o item herdado de documentação da quebra de semântica do `GITPR_SKIP_UPDATE_CHECK`, elevando a documentação ao padrão arquitetural de alta maturidade do repositório (ADR formal + teste de regressão e paridade documental nos 5 idiomas suportados + link cruzado).

---

## 2. Componentes e Mudanças Planejadas

### Componente 1: Registro Arquitetural (ADR)
- **Arquivo**: `docs/adr/0021-strict-boolean-update-check-migration.md`
- **Conteúdo**:
  - Contexto da quebra de expectativa entre v1.4.2 e v1.4.3.
  - O problema da avaliação baseada em presença (`bool(os.environ.get(...))`).
  - Decisão: Parser booleano estrito contra `_SKIP_TRUTHY_VALUES` (`1`, `true`, `yes`, `on`, `y`).
  - Impacto e Remediação: Automações legadas com `GITPR_SKIP_UPDATE_CHECK=false` ou `=0` agora deixam a checagem ativa. Devem atualizar para `1` ou `true`.
  - Consequências positivas e negativas/riscos.

### Componente 2: Referência Cruzada na Documentação dos 5 Idiomas
- **Arquivos**:
  - `docs/auto-update.{md,pt_br.md,pt_pt.md,es_es.md,fr_fr.md}` (5 arquivos)
  - `docs/tutorial/install-from-source.{md,pt_br.md,pt_pt.md,es_es.md,fr_fr.md}` (5 arquivos)
- **Mudança**:
  - Adicionar link cruzado explícito para `docs/adr/0021-strict-boolean-update-check-migration.md` dentro dos blocos `> [!WARNING]`.

### Componente 3: Teste Automatizado de Paridade Documental
- **Arquivo**: `tests/unit/test_auto_update_docs_parity.py`
- **Verificações**:
  - Existência dos 10 arquivos de documentação técnica.
  - Presença dos callouts `> [!WARNING]` com menção explícita a `GITPR_SKIP_UPDATE_CHECK`.
  - Presença dos valores canônicos falsos (`false`, `0`) e verdadeiros (`1`, `true`).
  - Presença da referência cruzada para a ADR-0021.
  - Verificação da integridade da ADR-0021 e do termo `Update check switch` em `CONTEXT.md`.

---

## 3. Plano de Verificação

### Testes Automatizados
- Executar `pytest tests/unit/test_auto_update_docs_parity.py -v`.
- Executar suíte completa de testes de updater e docs parity:
  - `pytest tests/test_updater.py -v`
  - `pytest tests/unit/ -v`

### Verificação Manual
- Revisão visual dos arquivos nos 5 idiomas para consistência ortográfica e semântica.
