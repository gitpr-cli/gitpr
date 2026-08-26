---
name: textual-modal-callback-dead-pump
description: Push de modal dentro de timer de tela que será removida liga o callback do dismiss à fila morta — o resultado nunca chega (Textual 8.x)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e57845bb-2246-4f61-b6e4-220efa86d6ad
  modified: 2026-08-19T13:55:25.934Z
---

No Textual 8.x, `App.push_screen(callback=...)` registra o callback com `active_message_pump.get()` como requester. Se o push acontece dentro de um timer/callback de uma tela que é removida (`pop_screen`) logo antes, o `dismiss()` posta o resultado na fila dessa tela morta e o callback **nunca executa** — o modal fecha e nada acontece (bug real do botão "Commit with --no-verify" em pr_publish_app, 2026-08-19).

**Why:** `dismiss` → `ResultCallback.__call__` → `requester.call_next(callback, result)`; requester = pump ativo no momento do push (não o app).

**How to apply:**
- Nunca faça `pop_screen()` + `push_screen(callback=...)` dentro de timer de tela que está sendo removida.
- Para escapar do contexto da tela: `self.call_next(...)` no app (posta na fila do app — funciona). **Não use** `call_after_refresh` (vira `InvokeLater` encaminhado para a tela **atual**) nem `call_from_thread` na thread principal (levanta RuntimeError).
- Padrão de teste: `App.query_one` não enxerga telas modais no 8.2.8 — use `app.screen.query_one`; `pilot.click(selector)` usa `screen.query_one` e funciona.
- Ver [[version-marker-pattern]] e [[staging-selecao-widget-erro-real]] para outros bugs de TUI/Textual.
