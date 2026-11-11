# Survey and Facts — Documentação da Mudança de Semântica de GITPR_SKIP_UPDATE_CHECK

**Data:** 2026-11-11  
**Branch:** develop_natan  
**Task:** document_gitpr_skip_update_check_migration_note  

---

## 1. Contexto e Problema

O GitPR é distribuído exclusivamente via PyPI e possui um portão de atualização obrigatório (*mandatory update gate*).
Ao rodar a partir do código fonte (checkout local editável via `pip install -e .`), a versão reportada é lida da working tree local (`src/updater.py::__version__`). Se uma versão mais recente já tiver sido publicada no PyPI, o portão bloqueia a execução.

Para permitir desenvolvimento local e automações de teste offline, o GitPR possui uma chave de escape via variável de ambiente: `GITPR_SKIP_UPDATE_CHECK`.

### Histórico da Mudança Semântica (v1.4.3)
- **Antes da v1.4.3**: O código verificava a presença/truthiness simples de string da variável de ambiente no Python/shell (ex.: `bool(os.environ.get("GITPR_SKIP_UPDATE_CHECK"))`). Qualquer valor não vazio — inclusive strings como `"false"`, `"0"`, `"off"`, `"no"` — era avaliado como verdadeiro e silenciava a verificação de versão.
- **A partir da v1.4.3**: Foi implementado um parser booleano estrito em `src/updater.py`:
  ```python
  SKIP_UPDATE_CHECK_ENV = "GITPR_SKIP_UPDATE_CHECK"
  _SKIP_TRUTHY_VALUES = ("1", "true", "yes", "on", "y")

  def is_update_check_disabled():
      value = os.environ.get(SKIP_UPDATE_CHECK_ENV, "")
      return value.strip().lower() in _SKIP_TRUTHY_VALUES
  ```
- **A Armadilha (The Breaking Change)**:
  Automações, pipelines de CI ou scripts de desenvolvedores que configuravam `GITPR_SKIP_UPDATE_CHECK=false` (ou `=0`) esperando desligar o aviso / silenciar a checagem com base no comportamento antigo agora têm o valor avaliado como falso. Consequentemente, a verificação de atualização **permanece ativa** e pode bloquear comandos não isentos com código de saída diferente de zero.
- **Estado Encontrado na Codebase**:
  - No commit `1995213` (09/11/2026), notas de migração preliminares foram adicionadas a `docs/auto-update.*.md` e `docs/tutorial/install-from-source.*.md` nos 5 idiomas suportados.
  - O termo canônico **Update check switch** foi registrado em `CONTEXT.md`.
  - No entanto, a formalização arquitetural via **ADR** e o teste unitário de **paridade documental** (padrão consolidado no projeto via ADR-0020 e `test_scm_multiforge_docs_parity.py`) ainda não existiam.

---

## 2. Decisões do Grill (Rodada 1)

1. **Escopo de Formalização (Q1)**:
   - **Decisão**: Opção A (Recomendado). Formalizar a quebra de semântica com ADR dedicada (`docs/adr/0021-strict-boolean-update-check-migration.md`), implementar o teste unitário de paridade multilíngue `tests/unit/test_auto_update_docs_parity.py` e vincular a ADR nas notas de migração dos 10 arquivos de documentação técnica.
2. **Criação da ADR-0021 (Q2)**:
   - **Decisão**: Opção A (Recomendado). Registrar formalmente a decisão arquitetural na ADR-0021, abordando contexto, o parser estrito, alternativas rejeitadas (presença simples de env var) e as orientações mandatória para automações legadas.
3. **Teste Automatizado de Paridade (Q3)**:
   - **Decisão**: Opção A (Recomendado). Criar `tests/unit/test_auto_update_docs_parity.py` cobrindo a existência dos 10 arquivos (`docs/auto-update.{md,pt_br.md,pt_pt.md,es_es.md,fr_fr.md}` e `docs/tutorial/install-from-source.{md,...}`), conferência do callout `[!WARNING]`, menção à variável `GITPR_SKIP_UPDATE_CHECK`, menção aos valores falsos (`false`, `0`), verdadeiros (`1`, `true`) e cross-reference para a ADR-0021.
4. **Refinamento do Texto da Nota (Q4)**:
   - **Decisão**: Opção A (Recomendado). Manter estrutura concisa, padronizar títulos e termos em `CONTEXT.md` (*Update check switch*) e adicionar link direto para a ADR-0021.

---

## 3. Matriz de Arquivos Afetados

| Arquivo | Mudança | Idioma / Escopo |
|---|---|---|
| `docs/adr/0021-strict-boolean-update-check-migration.md` | Nova ADR formalizando o parser estrito e migração | Arquitetura / Governança |
| `tests/unit/test_auto_update_docs_parity.py` | Novo teste unitário de paridade documental | Testes / Qualidade |
| `docs/auto-update.md` | Vinculação da ADR-0021 na nota de migração | Inglês (Canônico) |
| `docs/auto-update.pt_br.md` | Vinculação da ADR-0021 na nota de migração | Português (Brasil) |
| `docs/auto-update.pt_pt.md` | Vinculação da ADR-0021 na nota de migração | Português (Portugal) |
| `docs/auto-update.es_es.md` | Vinculação da ADR-0021 na nota de migração | Espanhol |
| `docs/auto-update.fr_fr.md` | Vinculação da ADR-0021 na nota de migração | Francês |
| `docs/tutorial/install-from-source.md` | Vinculação da ADR-0021 na nota de migração | Inglês (Canônico) |
| `docs/tutorial/install-from-source.pt_br.md` | Vinculação da ADR-0021 na nota de migração | Português (Brasil) |
| `docs/tutorial/install-from-source.pt_pt.md` | Vinculação da ADR-0021 na nota de migração | Português (Portugal) |
| `docs/tutorial/install-from-source.es_es.md` | Vinculação da ADR-0021 na nota de migração | Espanhol |
| `docs/tutorial/install-from-source.fr_fr.md` | Vinculação da ADR-0021 na nota de migração | Francês |
| `CONTEXT.md` | Validação/refinamento do termo `Update check switch` | Modelo de Domínio |
