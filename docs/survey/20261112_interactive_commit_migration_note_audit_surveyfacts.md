# Survey and Facts — Auditoria e Encerramento da Nota de Migração do `-c` Interativo

**Data:** 2026-11-12  
**Branch:** develop_natan  
**Task:** interactive_commit_migration_note_audit  

---

## 1. Contexto e Origem do Item

No relatório de transição de estado [`docs/reports/relatorio_estado_v0.0.23.md`](../../docs/reports/relatorio_estado_v0.0.23.md), constava o seguinte item em aberto:
> `* **Nota de migração do -c interativo:** o commit-message-ia descreve o fluxo novo; vale dizer explicitamente que sem TTY ele cai no console e que --hook continua sendo o caminho de CI. **Item herdado, ainda aberto (a guarda de TTY reduziu o impacto).**`

### 1.1 Fatos Levantados na Base de Código
1. **Implementação Prévia:** No commit `1995213` (09/11/2026), a nota de migração já foi completamente redigida e inserida em:
   - `docs/commit-message-ia.md` (Inglês)
   - `docs/commit-message-ia.pt_br.md` (Português Brasil)
   - `docs/commit-message-ia.pt_pt.md` (Português Portugal)
   - `docs/commit-message-ia.es_es.md` (Espanhol)
   - `docs/commit-message-ia.fr_fr.md` (Francês)
   - `CONTEXT.md` (Refinamento do termo `Commit flow`)
2. **Registro de Conclusão no Relatório v0.0.24:** No relatório [`docs/reports/relatorio_estado_v0.0.24.md`](../../docs/reports/relatorio_estado_v0.0.24.md), o item já foi registrado como:
   > `* **Nota de migração do -c interativo:** ✅ **concluído** — docs/commit-message-ia.* nos 5 idiomas explica o fluxo sem TTY e o --hook.`
3. **Conteúdo do Callout Existente:**
   - Explicita que antes da v1.4.4, `gitpr -c` era puramente não-interativo e de console.
   - Esclarece que na ausência de TTY (`may_ask == False`), o GitPR recorre à exibição da sugestão no console sem abrir telas TUI e sem executar o commit.
   - Orienta que em automações, CI e git hooks deve-se usar sempre `--hook <arquivo>` ou `--no-edit`.

---

## 2. Decisões do Grill (Rodada 1)

| Questão | Decisão Escolhida | Justificativa |
|---|---|---|
| **Q1 — Status e Intenção** | **Opção 1 (Recomendada):** Auditoria e encerramento | A implementação existente atende integralmente aos requisitos técnicos e de i18n sem necessidade de retrabalho. |
| **Q2 — Superfície Adicional** | **Opção 1 (Recomendada):** Nenhuma alteração | Manter a documentação existente nos 5 idiomas e no `CONTEXT.md` sem modificações adicionais em código ou documentação externa. |

---

## 3. Matriz de Auditoria dos Arquivos

| Arquivo Auditado | Presença do Aviso de Migração | Orientação sem TTY / CI | Status |
|---|---|---|---|
| `docs/commit-message-ia.md` | Sim (`> [!WARNING]` §1) | Sim (Console fallback & `--hook`) | ✅ Conforme |
| `docs/commit-message-ia.pt_br.md` | Sim (`> [!WARNING]` §1) | Sim (Console fallback & `--hook`) | ✅ Conforme |
| `docs/commit-message-ia.pt_pt.md` | Sim (`> [!WARNING]` §1) | Sim (Console fallback & `--hook`) | ✅ Conforme |
| `docs/commit-message-ia.es_es.md` | Sim (`> [!WARNING]` §1) | Sim (Console fallback & `--hook`) | ✅ Conforme |
| `docs/commit-message-ia.fr_fr.md` | Sim (`> [!WARNING]` §1) | Sim (Console fallback & `--hook`) | ✅ Conforme |
| `CONTEXT.md` | N/A | Sim (Glossário `Commit flow` restringe commit a Interactive run) | ✅ Conforme |
