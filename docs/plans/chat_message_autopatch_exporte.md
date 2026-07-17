# Plan: Message-level Auto-Patch + Export with focus navigation

## Context

Currently F5 (Auto-Patch) and F6 (Export) work on the **last** AI message only. The user wants per-message actions with keyboard navigation, so they can scroll through the conversation and apply Auto-Patch or Export to any AI message, not just the last one. The user chose a **hybrid Tab + Scroll** focus model.

## Design overview

1. **Focus system** — `ChatApp` tracks `_focused_msg_index` (which AI message is active). Default: the last AI message. New AI responses auto-focus. Tab/Shift+Tab cycles through AI messages. Scrolling also updates focus to the topmost visible AI message.

2. **Visual feedback** — Focused message gets a CSS class `.focused-assistant` (brighter left border, subtle background change). A compact action bar appears between the chat container and the input showing: `📌 Msg #N | Ctrl+Shift+A: Auto-Patch | Ctrl+Shift+E: Export`.

3. **Keyboard shortcuts** — `Ctrl+Shift+A` (Auto-Patch focused) and `Ctrl+Shift+E` (Export focused). Using Shift modifier avoids conflict with Input's built-in Ctrl+A (select-all) and Ctrl+E (go to end).

4. **Auto-Patch (Ctrl+Shift+A)** — Reuses the existing `split("``` ")` extraction logic from `action_apply_code` but targets `self._focused_msg_content` instead of the last AI message. Saves to `GITPR_PATCH_SUGGESTION_<key>.txt`.

5. **Export (Ctrl+Shift+E)** — Saves only the focused message to `MESSAGE_<chat_id>_<random>.md` (format: `MESSAGE_oGy3-qsQf4-7Si5_aB3-xK9.md`).

6. **i18n** — All new text via `__()`.

7. **Documentation** — Update `understanding_chat_functionality.md` (all 5 languages) and the F1 help modal.

## Files to modify

### 1. `src/ui/chat_app.py` — Primary implementation

**A) `ChatMessage` — add index tracking**
```python
class ChatMessage(Static):
    def __init__(self, role, content, msg_index=-1, **kwargs):
        super().__init__(content, markup=False, **kwargs)
        self.role = role
        self.msg_index = msg_index  # position in the AI message list
```

**B) `ChatApp` CSS — add focused-assistant class**
```css
.assistant.focused {
    border-left: thick $accent;
    background: $panel-lighten-1;
}
#focus_bar {
    dock: bottom;
    height: 1;
    padding: 0 2;
    background: $surface-darken-1;
    color: $text-muted;
}
```

**C) `ChatApp.__init__` — new state**
```python
self._focused_msg_index = -1    # which AI message is focused (-1 = none)
self._focused_msg_content = ""  # content of focused message (for actions)
self._focus_bar = None          # Static widget showing focus info
self._ai_message_count = 0      # how many AI messages exist
```

**D) `ChatApp.compose` — add focus bar**
Yield a `Static(id="focus_bar")` between the chat container and CommandSuggestions.

**E) `ChatApp.load_history` / `ChatApp.add_message` — count AI messages**
Increment `_ai_message_count` for each assistant message. Set `msg_index` on each ChatMessage.

**F) `ChatApp.add_message` — auto-focus last AI**
When adding an assistant message, set `_focused_msg_index = _ai_message_count - 1` and call `_update_focus_visual()`.

**G) `ChatApp BINDINGS` — add new shortcuts**
```python
Binding("ctrl+shift+a", "auto_patch_focused", __("Auto-Patch Msg")),
Binding("ctrl+shift+e", "export_focused_msg", __("Export Msg")),
Binding("ctrl+up", "focus_prev_msg", __("Previous Msg")),
Binding("ctrl+down", "focus_next_msg", __("Next Msg")),
```

**H) New methods**

`_update_focus_visual()` — removes `.focused` from all AI messages, adds it to the one at `_focused_msg_index`. Updates the focus bar text. Stores its content in `_focused_msg_content`.

`_get_ai_messages()` — returns list of `ChatMessage` widgets with `role == "assistant"` from the container, sorted by mount order.

`action_focus_prev_msg()` / `action_focus_next_msg()` — decrement/increment `_focused_msg_index`, clamp to valid range, call `_update_focus_visual()`, scroll to make the message visible.

`action_auto_patch_focused()` — runs code extraction regex + split on `_focused_msg_content`, saves to `GITPR_PATCH_SUGGESTION_<key>.txt`, shows system message.

`action_export_focused_msg()` — saves `_focused_msg_content` to `MESSAGE_<session_uuid>_<random>.md`, shows system message.

**I) Scroll sync** — watch the container's scroll
Add a `_watch_scroll` or timer-based check that updates focus when the user scrolls (mouse wheel, PageUp/Down). Debounce to avoid excessive updates.

### 2. `langs/*.json` — New translation keys

| Key                                                                   | EN               | pt_br                                                             | pt_pt            | fr_fr                | es_es             |
| --------------------------------------------------------------------- | ---------------- | ----------------------------------------------------------------- | ---------------- | -------------------- | ----------------- |
| `Auto-Patch Msg`                                                      | Auto-Patch Msg   | Auto-Patch Msg                                                    | Auto-Patch Msg   | Auto-Patch Msg       | Auto-Patch Msg    |
| `Export Msg`                                                          | Export Msg       | Exportar Msg                                                      | Exportar Msg     | Exporter Msg         | Exportar Msg      |
| `Previous Msg`                                                        | Previous Msg     | Msg Anterior                                                      | Msg Anterior     | Msg Précédent        | Msg Anterior      |
| `Next Msg`                                                            | Next Msg         | Próx Msg                                                          | Próx Msg         | Msg Suivant          | Sig Msg           |
| `Msg #{n} focused`                                                    | Msg #{n} focused | Msg #{n} em foco                                                  | Msg #{n} em foco | Msg #{n} sélectionné | Msg #{n} enfocado |
| `🧪 Auto-Patch: Code extracted from message #{n} and saved to {file}!` | (EN)             | 🧪 Auto-Patch: Código extraído da mensagem #{n} e salvo em {file}! | ...              | ...                  | ...               |
| `📤 Message #{n} exported to {file}!`                                  | (EN)             | 📤 Mensagem #{n} exportada para {file}!                            | ...              | ...                  | ...               |
| `❌ No code blocks found in message #{n}.`                             | (EN)             | ❌ Nenhum bloco de código encontrado na mensagem #{n}.             | ...              | ...                  | ...               |

### 3. `docs/understanding_chat_functionality.md` (all 5 languages) — Add message-level actions section

New section after "Auto-Patch (F5)":
```
### Message-Level Actions (Ctrl+Shift+A / Ctrl+Shift+E)

Navigate between AI messages with **Ctrl+↑** and **Ctrl+↓**. The focused message shows a highlighted left border.

- **Ctrl+Shift+A** — Extracts code blocks from the focused message only
- **Ctrl+Shift+E** — Exports the focused message to a file
```

### 4. F1 Help modal — Update keyboard shortcuts list

Add to the help section:
```
• [bold]Ctrl+↑/↓[/bold] — Navigate between AI messages
• [bold]Ctrl+Shift+A[/bold] — Auto-Patch focused message
• [bold]Ctrl+Shift+E[/bold] — Export focused message
```

## Verification

1. Start chat, ask AI for code → press Ctrl+Shift+A → code extracted from last message
2. Press Ctrl+Up → focus moves to previous AI message → border highlights
3. Press Ctrl+Shift+E → single message exported to `MESSAGE_<id>_<key>.md`
4. Scroll with mouse → focus updates to topmost visible AI message
5. Press Tab multiple times → cycles through AI messages
6. `gitpr --lang pt_br -ch` → all new text appears in Portuguese
