# Survey Facts — Estabilização de `test_headless_full_flow`

**Data:** 2026-11-05  
**Branch:** `develop_natan`  
**Identificador da tarefa:** `stabilize_test_headless_full_flow`

---

## 1. Contexto e Diagnóstico

- **Sintoma histórico:** O teste de integração headless `tests/test_commit_app.py::TestCommitAppHeadlessFlow::test_headless_full_flow` apresentava falha intermitente documentada nos relatórios `relatorio_estado_v0.0.21.md` e `relatorio_estado_v0.0.22.md`.
- **Causa raiz:** O teste aguardava apenas a existência do seletor no DOM (`bool(app.screen.query("#btn_confirm"))`). Em ambientes de teste do Textual, o widget pode ser adicionado à árvore antes que a tela modal (`CommitMessageScreen`) complete a fase de montagem (`is_mounted`) e antes que as coordenadas espaciais sejam resolvidas pelo compositor. Quando `pilot.click("#btn_confirm")` era despachado imediatamente, o clique por coordenadas em tela falhava silenciosamente ou era ignorado, mantendo a tela aberta e estourando o timeout de 5 segundos em `_wait_until(..., lambda: app.result == "committed")`.
- **Comportamento em ambiente sandbox Windows:** O loop de eventos assíncrono do Python no Windows (`ProactorEventLoop`) utiliza `socket.socketpair()` em loopback local para acordar canais internos. Em sandbox estrito sem rede, o loopback aguarda autorização, podendo causar atraso caso executado sem privilégios unsandboxed.

---

## 2. Decisões do Grill (Rodada 1)

1. **Q1 — Acionamento do botão `#btn_confirm`:**
   - **Decisão:** Substituir `pilot.click("#btn_confirm")` por `app.screen.query_one("#btn_confirm", Button).press()`.
   - **Justificativa:** Disparo semântico direto do evento de botão, idêntico ao padrão adotado nos demais testes de modais em `tests/test_pr_publish_app.py`, imune a atrasos de cálculo de layout geométrico pelo compositor do Textual.

2. **Q2 — Condição de guarda na transição de telas:**
   - **Decisão:** Reforçar o predicado de `_wait_until` para verificar explicitamente o tipo da tela ativa, seu status de montagem e a presença do botão:
     `isinstance(app.screen, CommitMessageScreen) and app.screen.is_mounted and bool(app.screen.query("#btn_confirm"))`
   - **Justificativa:** Elimina race conditions em que o botão foi instanciado mas a tela anterior (`CommitProgressScreen`) ainda não completou a desmontagem ou a nova tela ainda não concluiu `on_mount`.

3. **Q3 — Margem de timeout em `_wait_until`:**
   - **Decisão:** Elevar o timeout padrão de 5.0 s para 10.0 s.
   - **Justificativa:** Provê resiliência extra para esteiras de CI e máquinas sob carga elevada, sem retardar execuções bem-sucedidas.

---

## 3. Conformidade com o Modelo de Domínio (`CONTEXT.md`)

- A terminologia preservada inclui **Commit flow** (a sequência interativa de seleção, geração, edição e execução do commit) e **Modal screen**.
- Nenhuma alteração foi necessária no vocabulário de domínio do `CONTEXT.md` (o problema e sua solução pertencem à infraestrutura de testes de UI do Textual).
