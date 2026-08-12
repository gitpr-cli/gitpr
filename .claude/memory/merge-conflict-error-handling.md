---
name: merge-conflict-error-handling
description: Falha de merge no PR publisher exibe modal de erro em vez de prosseguir silenciosamente
metadata:
  type: feedback
  source: docs/claude-code/reports/develop_natan/2026-08-11_merge_conflict_error_handling.md
  date: 2026-08-11
  branch: develop_natan
---

No PR Publisher (Textual TUI), quando o merge de uma PR falha — especialmente com
HTTP 405 indicando conflitos — o sistema agora exibe um modal de erro visível com
a mensagem da API do GitHub, em vez de prosseguir silenciosamente para o prompt
de abrir no navegador. O modal oferece a opção de abrir a PR no browser para
resolução manual dos conflitos.

A correção envolveu refatorar `_do_merge` em `src/ui/pr_publish_app.py` em três
métodos com preocupações separadas:

1. **`_do_merge`** — dispara o merge em thread separada (para não bloquear a UI)
2. **`_on_merge_success`** — callback na thread principal, atualiza estado de sucesso
3. **`_on_merge_failure`** — callback na thread principal, exibe modal de erro

O rastreamento de `final_action` (`"merged"` / `"merge_failed"`) permite que o
display pós-TUI em `src/main.py` use as cores corretas (verde para merged,
vermelho para falha).

**Why:** Antes da correção, o fluxo era: merge falha → código ignorava o erro →
perguntava "abrir no navegador?" como se tudo tivesse dado certo. O usuário só
descobria o problema ao abrir a PR manualmente. O HTTP 405 é específico para
conflitos que o GitHub não consegue resolver automaticamente — a mensagem agora
deixa isso explícito.

**How to apply:**
1. Toda operação assíncrona na TUI que atualiza estado visual deve usar
   `call_from_thread` para garantir execução na thread principal do Textual
2. Callbacks de sucesso e falha devem ser métodos separados — nunca misturar
   lógica de erro no callback de sucesso
3. Sempre rastrear o resultado final (`final_action`) para feedback visual correto
4. HTTP 405 em merge PR = conflitos que exigem resolução manual no GitHub
