# Understanding GitPR Interactive Chat

GitPR Interactive Chat is a **pair-programming AI assistant** that runs directly in your terminal. It sees your current uncommitted changes (`git diff`) and maintains a contextual conversation, helping you understand, refactor, test, and optimize your code.

## Starting the Chat

```bash
gitpr -ch
# or
gitpr --chat
```

To override the interface language for a single session:

```bash
gitpr --lang en_us -ch
gitpr --lang pt_br -ch
```

## Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| **F1** | Help | Opens a modal showing all shortcuts and slash commands |
| **F2** | Refresh Diff | Updates the AI context with the latest uncommitted code changes |
| **F5** | Auto-Patch | Extracts code blocks from the last AI response and saves them to a file |
| **F6** | Export | Saves the entire conversation to a structured Markdown file |
| **Esc** | Exit | Closes the chat application |

## Slash Commands

Type `/` in the chat input to see a dropdown of available commands. Start typing to filter.

| Command | Description |
|---------|-------------|
| `/explain` | Explains the current diff line by line |
| `/tests` | Generates unit tests for the changed functions |
| `/optimize` | Analyzes cyclomatic complexity and suggests performance improvements |
| `/clear` | Clears the conversation and starts a new chat session for the current diff |

You can type a partial command (e.g., `/ex`) and press **Enter** — it auto-completes to the full command.

## Memory and Sessions

The chat automatically persists your conversation and diff history on disk:

- **Location:** `~/.gitpr/cache/chat/<UUID>/`
- **Session key:** A unique 15-character UUID (format `XXXX-XXXXX-XXXX`) generated per branch and repository
- **Persistence:** Returning to the same branch reopens the existing session with full conversation history
- **Diff tracking:** Every code change is recorded. The AI knows when you've modified files and updates its context

## Auto-Patch (F5)

When the AI suggests code changes (in Markdown code blocks), press **F5** to extract and save them:

1. The last AI response is scanned for triple-backtick code blocks (` ```python ... ``` `)
2. All code blocks are concatenated and saved to a file named `GITPR_PATCH_SUGGESTION_<random-key>.txt`
3. Each key is unique (format `aB3-xK9`), so previous patches are never overwritten

Review the generated file and apply the changes manually to your project.

### Message-Level Actions (Ctrl+Shift+A / Ctrl+Shift+E)

You can apply Auto-Patch and Export to **any** AI message in the conversation, not just the last one.

Navigate between AI messages using **F7** and **F8**. The focused message is highlighted with a brighter left border, and an action bar appears above the input field.

- **Ctrl+Shift+S** — Extracts code blocks from the **focused message only** and saves to `GITPR_PATCH_SUGGESTION_<key>.txt`
- **Ctrl+Shift+E** — Exports the **focused message only** to `MESSAGE_<session-id>_<key>.md`

The default focus is always the most recent AI response.

## Export (F6)

Press **F6** to save your entire conversation to a structured Markdown file:

- **Filename:** `GITPR_CHAT_EXPORT_<session-uuid>.md`
- **Format:** Each message is labeled with its role (User / AI Assistant / System) and separated by horizontal rules
- **Use cases:** Documentation, sharing with teammates, or feeding context to other AI tools

## Refresh Diff (F2)

While coding in another editor, press **F2** to update the chat's context:

- If new changes are detected since the last diff snapshot, the AI is notified and can now see your latest edits
- If nothing changed, a confirmation message is shown

## Exiting the Chat

Press **Esc** or **Ctrl+C** to close the chat. Your session is automatically saved.

## Tips

- Use `/clear` to start fresh if the conversation gets too long or you want to change topics
- Combine `--lang` with `--provider` to customize both language and AI model: `gitpr --lang en_us --provider deepseek -ch`
- The `GITPR_CHAT_EXPORT_*.md` files can be committed to your repository as development notes
