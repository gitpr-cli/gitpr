---
name: staging-selecao-widget-erro-real
description: Modal de staging dessincronizava seleção de arquivos e engolia erros de git add com falso sucesso
metadata:
  type: feedback
  source: docs/claude-code/reports/develop_natan/2026-08-13_unstaged_modal_stage_fix.md
  date: 2026-08-13
  branch: develop_natan
---

O bug "Stage Selected não stageia nada" no PR Publisher tinha três causas que
se acumulavam:

1. **Seleção dessincronizada:** o modal mantinha um dicionário paralelo
   (`self._selected`) atualizado apenas pelos botões "Select All"/"Deselect
   All" — toggles individuais de linha do `SelectionList` eram ignorados e o
   modal stageava uma lista vazia.
2. **Falhas engolidas:** `stage_files()` usava `check=True` e os call sites
   engoliam a exceção — o console imprimia "✅ N arquivos adicionados" mesmo
   quando o `git add` falhava (falso sucesso que escondia o erro real).
3. **Staging duplicado:** o modal e o `check_unstaged_files()` executavam
   `git add` duas vezes sobre a mesma seleção, sem conferir resultado.

**Why:** Em TUIs Textual, manter estado paralelo a widgets é fonte de
dessincronização silenciosa — o próprio widget (`SelectionList.selected`) é a
única fonte de verdade. E wrappers de comandos git que retornam bool engolido
transformam falha em sucesso falso, impedindo o diagnóstico do usuário.

**How to apply:**
- Em qualquer tela Textual, ler o estado do widget no momento da ação
  (`SelectionList.selected`), nunca manter dicionários paralelos de seleção.
- Wrappers de comandos git devem retornar `(success, error_message)` com o
  stderr/stdout capturado; os call sites devem exibir o erro real.
- Executar operações com efeito colateral (git add) uma única vez por fluxo.

Ver também: [[unstaged-check-before-ai-commands]], [[tui-stdout-conflict-fix]]
