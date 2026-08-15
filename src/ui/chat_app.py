import re
import random
import string
import webbrowser
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Header,
    Footer,
    Input,
    Markdown,
    Static,
    Button,
    ListView,
    ListItem,
)
from textual.containers import VerticalScroll, Vertical
from textual.binding import Binding
from textual import work
from src.core import get_git_diff
from src.i18n import __, CURRENT_LANG
from src.ai_providers import call_ai_chat, process_chat_command, load_chat_commands
from src.spinner import THINKING_WORDS


class ChatMessage(Static):
    """Custom component to render each message bubble."""

    def __init__(self, role, content, msg_index=-1, **kwargs):
        super().__init__(content, markup=False, **kwargs)
        self.role = role
        self.msg_index = msg_index

    def compose(self) -> ComposeResult:
        # Add the class corresponding to the role (user, assistant or system)
        yield Markdown(self.content, classes=f"message {self.role}")


class ChatHelpScreen(ModalScreen):
    """Help modal showing keyboard shortcuts and slash commands."""

    CSS = """
    ChatHelpScreen { align: center middle; }
    #help_dialog {
        width: 72; height: auto; max-height: 90%; padding: 1 2;
        background: $surface; border: thick $accent 50%;
    }
    #help_scroll {
        max-height: 28; overflow-y: scroll;
    }
    .help_title { text-align: center; text-style: bold; margin-bottom: 1; }
    .help_section { text-style: bold; color: $accent; margin-top: 1; margin-bottom: 1; }
    .help_text { margin-bottom: 1; }
    Button {
        width: 20%;
        margin-top: 1;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        commands = load_chat_commands()
        cmd_lines = []
        for cmd, desc in commands.items():
            cmd_lines.append(f"• [bold $accent]{cmd}[/bold $accent] — {desc}")
        cmd_text = "\n".join(cmd_lines)

        with Vertical(id="help_dialog"):
            yield Static("💡 Chat Help", classes="help_title")
            yield Static("⌨️ Keyboard Shortcuts", classes="help_section")
            with VerticalScroll(id="help_scroll"):
                yield Static(
                    "• [bold]F1[/bold] Help — Shows this help modal\n"
                    "• [bold]F2[/bold] Refresh Diff — Updates the chat context with the latest code changes\n"
                    "• [bold]F5[/bold] Auto-Patch — Extracts code blocks from the last AI response\n"
                    "• [bold]F6[/bold] Export — Saves the full conversation to a Markdown file\n"
                    "• [bold]F7/F8[/bold] — Navigate focus between AI messages\n"
                    "• [bold]Ctrlhift+S[/bold] — Auto-Patch the focused AI message\n"
                    "• [bold]Ctrlhift+E[/bold] — Export the focused AI message\n"
                    "• [bold]Esc[/bold] Exit — Closes the chat",
                    classes="help_text",
                )
                yield Static("⚡ Slash Commands", classes="help_section")
                yield Static(cmd_text, classes="help_text")
            yield Button(__("Got it"), variant="primary", id="close_help")
            yield Button(__("Online Help"), variant="default", id="online_help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_help":
            self.app.pop_screen()
        elif event.button.id == "online_help":
            lang_suffix = "" if CURRENT_LANG.startswith("en") else f".{CURRENT_LANG}"
            url = f"https://github.com/natanfiuza/gitpr/blob/main/docs/understanding_chat_functionality{lang_suffix}.md"
            webbrowser.open(url)


class CommandSuggestions(Vertical):
    """Slash-command suggestion panel that appears above the input while the user types."""

    DEFAULT_CSS = """
    CommandSuggestions {
        margin: 0 2 1 2;
        height: auto;
        max-height: 12;
        background: $surface-darken-1;
        border: solid $accent;
        display: none;
    }
    CommandSuggestions ListView {
        height: auto;
        max-height: 10;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.commands = {}
        self.filtered = []

    def compose(self) -> ComposeResult:
        yield ListView()

    def load_commands(self):
        """Load the translated command list."""
        self.commands = load_chat_commands()

    def filter_commands(self, query: str) -> None:
        """Update the list with commands matching the partial input."""
        list_view = self.query_one(ListView)
        list_view.clear()
        list_view.index = (
            None  # Reset highlight so stale index doesn't cause wrong auto-complete
        )

        if not query.startswith("/"):
            self.display = False
            return

        query_lower = query.lower()
        matches = [
            (cmd, desc)
            for cmd, desc in self.commands.items()
            if cmd.lower().startswith(query_lower)
        ]
        if not matches:
            self.display = False
            return

        for cmd, desc in matches:
            list_view.append(ListItem(Static(f"{cmd} — {desc}")))

        self.filtered = [cmd for cmd, _ in matches]
        self.display = True

    def get_selected_command(self) -> str | None:
        """Return the highlighted command, or the first match as auto-complete fallback."""
        list_view = self.query_one(ListView)
        if list_view.index is not None and 0 <= list_view.index < len(self.filtered):
            return self.filtered[list_view.index]
        if self.filtered:
            return self.filtered[0]
        return None


class ChatApp(App):
    """Terminal interface for the Interactive Pair Programming Chat."""

    TITLE = "GitPR - AI Pair Programming"
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    #chat_container {
        height: 1fr;
        padding: 1 2;
        overflow-y: scroll;
    }
    .message {
        margin-bottom: 1;
        padding: 1 2;
        border: solid $accent 50%;
    }
    .user {
        background: $surface;
        border-left: thick $accent;
    }
    .assistant {
        background: $panel;
        border-left: thick $success;
    }
    .assistant.focused {
        border-left: thick $warning;
        background: $accent 30%;
    }
    #focus_bar {
        dock: bottom;
        height: 1;
        padding: 0 2;
        background: $surface-darken-1;
        color: $text-muted;
    }
    .system {
        background: $warning-muted;
        color: $text;
        text-align: center;
        border: none;
        padding: 0 1;
    }
    #chat_input {
        dock: bottom;
        margin: 1 2;
    }
    """

    # Shortcuts already mapped for Phase 4!
    BINDINGS = [
        Binding("f1", "show_help", __("Help")),
        Binding("f2", "refresh_diff", __("Refresh Diff")),
        Binding("f5", "apply_code", __("Auto-Patch")),
        Binding("f6", "export_session", __("Export")),
        Binding("f7", "focus_prev_msg", __("Previous Msg")),
        Binding("f8", "focus_next_msg", __("Next Msg")),
        Binding("ctrl+s", "auto_patch_focused", __("Auto-Patch Msg"), priority=True),
        Binding("ctrl+e", "export_focused_msg", __("Export Msg"), priority=True),
        Binding("escape", "quit", __("Exit")),
    ]

    def __init__(
        self, memory_manager, provider, api_key, api_model, system_instruction, **kwargs
    ):
        super().__init__(**kwargs)
        self.memory = memory_manager
        self.provider = provider
        self.api_key = api_key
        self.api_model = api_model
        self.system_instruction = system_instruction

        self.sub_title = f"{self.memory.repo_name} | Branch: {self.memory.branch_name} | ID: {self.memory.session_uuid}"
        self._thinking_widget = None
        self._thinking_timer = None
        self._thinking_state = {}
        self._focused_msg_index = -1
        self._focused_msg_content = ""
        self._ai_msg_widgets = []
        self._focus_bar = None

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="chat_container"):
            pass  # Populated dynamically in on_mount
        yield Static("", id="focus_bar")
        yield CommandSuggestions(id="cmd_suggestions")
        yield Input(
            placeholder=__("Type your message or / for commands..."), id="chat_input"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load the history stored in the base-15 UUID when opening the screen."""
        self._focus_bar = self.query_one("#focus_bar", Static)
        self.load_history()
        self._cmd_suggestions = self.query_one("#cmd_suggestions", CommandSuggestions)
        self._cmd_suggestions.load_commands()

    def load_history(self):
        container = self.query_one("#chat_container")
        history = self.memory.get_history()

        if not history:
            welcome_msg = __(
                "🤖 Hello! I am your AI assistant. I'm looking at your current diff. How can I help you?"
            )
            container.mount(ChatMessage("system", welcome_msg))
        else:
            for msg in history:
                msg_index = (
                    len(self._ai_msg_widgets) if msg["role"] == "assistant" else -1
                )
                widget = ChatMessage(msg["role"], msg["content"], msg_index=msg_index)
                container.mount(widget)

                if msg["role"] == "assistant":
                    self._ai_msg_widgets.append(widget)

            if self._ai_msg_widgets:
                self._focused_msg_index = len(self._ai_msg_widgets) - 1
                self._update_focus_visual()

        container.scroll_end(animate=False)

    BRAILLE = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def _animate_thinking(self) -> None:
        """Called by the App-level timer to animate the thinking indicator."""
        if not self._thinking_widget or not self._thinking_state:
            return

        st = self._thinking_state
        braille = self.BRAILLE[st["braille_idx"]]
        st["braille_idx"] = (st["braille_idx"] + 1) % len(self.BRAILLE)

        if len(st["discovered"]) < len(st["word"]):
            st["char_step"] += 1
            if st["char_step"] >= 4:
                st["discovered"] = st["word"][: len(st["discovered"]) + 1]
                st["char_step"] = 0
            else:
                fake = random.choice(string.ascii_uppercase + "0123456789!@#$")
                st["discovered"] = st["word"][: len(st["discovered"])] + fake
            display = f"  {braille} {st['discovered']}"
        else:
            st["dots_cycle"] = (st["dots_cycle"] + 1) % 12
            if st["dots_cycle"] < 4:
                dots = "."
            elif st["dots_cycle"] < 8:
                dots = ".."
            else:
                dots = "..."
            display = f"  {braille} {st['word']}{dots}"

            if st["dots_cycle"] == 0 and st["braille_idx"] == 0:
                st["word"] = random.choice(THINKING_WORDS)
                st["discovered"] = ""
                st["char_step"] = 0

        self._thinking_widget.update(display)

    def add_message(self, role, content):
        """Add the message visually and scroll the screen to the end."""
        container = self.query_one("#chat_container")
        msg_index = -1
        if role == "assistant":
            msg_index = len(self._ai_msg_widgets)
        msg = ChatMessage(role, content, msg_index=msg_index)
        container.mount(msg)
        container.scroll_end(animate=True)
        if role == "assistant":
            self._ai_msg_widgets.append(msg)
            self._focused_msg_index = msg_index
            self._update_focus_visual()

    # ── Message focus system ──────────────────────────────────────────

    def _notify_action(self, message, severity="information"):
        """Show a floating notification that does NOT scroll the chat."""
        self.notify(message, severity=severity, timeout=5)

    def _update_focus_visual(self):
        for message in self._ai_msg_widgets:
            message.query_one(Markdown).remove_class("focused")

        if 0 <= self._focused_msg_index < len(self._ai_msg_widgets):
            focused = self._ai_msg_widgets[self._focused_msg_index]
            focused.query_one(Markdown).add_class("focused")
            self._focused_msg_content = focused.content

            if self._focus_bar:
                self._focus_bar.update(
                    __(
                        "Msg #{n} focused | Ctrl+S: Auto-Patch | Ctrlhift+E: Export",
                        n=self._focused_msg_index + 1,
                    )
                )
        else:
            self._focused_msg_content = ""

            if self._focus_bar:
                self._focus_bar.update("")

    # def _update_focus_visual(self):
    #     """Apply visual highlight to the active AI message and update the focus bar."""
    #     for m in self._ai_msg_widgets:
    #         m.styles.border_left = ("thick", "green")
    #     if 0 <= self._focused_msg_index < len(self._ai_msg_widgets):
    #         focused = self._ai_msg_widgets[self._focused_msg_index]
    #         focused.styles.border_left = ("thick", "yellow")
    #         self._focused_msg_content = focused.content
    #         if self._focus_bar:
    #             self._focus_bar.update(__("Msg #{n} focused | Ctrlhift+S: Auto-Patch | Ctrlhift+E: Export", n=self._focused_msg_index + 1))
    #     else:
    #         self._focused_msg_content = ""
    #         if self._focus_bar:
    #             self._focus_bar.update("")

    def action_focus_prev_msg(self):
        """F7: move focus to the previous AI message."""
        if not self._ai_msg_widgets:
            return
        self._focused_msg_index = max(0, self._focused_msg_index - 1)
        self._update_focus_visual()

    def action_focus_next_msg(self):
        """F8: move focus to the next AI message."""
        if not self._ai_msg_widgets:
            return
        self._focused_msg_index = min(
            len(self._ai_msg_widgets) - 1, self._focused_msg_index + 1
        )
        self._update_focus_visual()

    def action_auto_patch_focused(self):
        """Ctrlhift+S: extract code from the focused AI message only."""
        if not self._focused_msg_content:
            self._notify_action(
                __("❌ No AI message focused. Use F7/F8 to select one."),
                severity="warning",
            )
            return
        content = self._focused_msg_content
        code_blocks = re.findall(r"`{3}\s*(?:\w+)?\s*\n(.*?)`{3}", content, re.DOTALL)
        if not code_blocks:
            parts = content.split("```")
            for i in range(1, len(parts), 2):
                block = parts[i].strip()
                if block:
                    first_line_end = block.find("\n")
                    if first_line_end > 0 and first_line_end < 20:
                        first_line = block[:first_line_end].strip()
                        if first_line and " " not in first_line:
                            block = block[first_line_end + 1 :]
                    code_blocks.append(block.strip())
        if code_blocks:
            extracted_code = "\n\n".join(code_blocks)
            key = (
                "".join(random.choices(string.ascii_letters + string.digits, k=3))
                + "-"
                + "".join(random.choices(string.ascii_letters + string.digits, k=3))
            )
            export_file = f"GITPR_PATCH_SUGGESTION_{key}.txt"
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(extracted_code)
            self._notify_action(
                __(
                    "🧪 Auto-Patch: Code extracted from message #{n} and saved to {file}!",
                    n=self._focused_msg_index + 1,
                    file=export_file,
                )
            )
        else:
            self._notify_action(
                __(
                    "❌ No code blocks found in message #{n}.",
                    n=self._focused_msg_index + 1,
                ),
                severity="warning",
            )

    def action_export_focused_msg(self):
        """Ctrlhift+E: export the focused AI message to a Markdown file."""
        if not self._focused_msg_content:
            self._notify_action(
                __("❌ No AI message focused. Use F7/F8 to select one."),
                severity="warning",
            )
            return
        key = (
            "".join(random.choices(string.ascii_letters + string.digits, k=3))
            + "-"
            + "".join(random.choices(string.ascii_letters + string.digits, k=3))
        )
        export_file = f"MESSAGE_{self.memory.session_uuid}_{key}.md"
        with open(export_file, "w", encoding="utf-8") as f:
            f.write(self._focused_msg_content)
        self._notify_action(
            __(
                "📤 Message #{n} exported to {file}!",
                n=self._focused_msg_index + 1,
                file=export_file,
            )
        )

    # ── Input handlers ────────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter slash-command suggestions as the user types."""
        self._cmd_suggestions.filter_commands(event.value)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Fill the input with the clicked/highlighted slash command."""
        cmd = self._cmd_suggestions.get_selected_command()
        if cmd:
            input_widget = self.query_one("#chat_input", Input)
            input_widget.value = cmd + " "
            input_widget.focus()
            self._cmd_suggestions.display = False

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Capture the user's Enter key."""
        user_text = event.value.strip()
        if not user_text:
            return

        # Auto-complete slash command from the highlighted or first suggestion
        if user_text.startswith("/"):
            selected = self._cmd_suggestions.get_selected_command()
            if selected and selected.startswith(user_text) and selected != user_text:
                user_text = selected

        # Hide suggestions after submission
        self._cmd_suggestions.display = False

        # Clear the input
        input_widget = self.query_one("#chat_input", Input)
        input_widget.value = ""

        # Intercept dynamic commands (Phase 2)
        is_cmd, is_clear, processed_msg = process_chat_command(user_text)

        if is_clear:
            # Recreate the session to clear memory using the current diff
            current_diff = self.memory.get_latest_diff()
            diff_md5 = self.memory._generate_md5(current_diff)
            self.memory._create_new_session(current_diff, diff_md5)

            # Clear the screen visually
            container = self.query_one("#chat_container")
            await container.query("*").remove()
            self.sub_title = f"{self.memory.repo_name} | Branch: {self.memory.branch_name} | ID: {self.memory.session_uuid}"
            self.add_message(
                "system", __("🧹 Conversation cleared. A new session has started.")
            )
            return

        # Display the user's message on screen (if it's a command, the screen shows the raw command, but the AI reads the processed one)
        self.add_message("user", user_text)

        # Save the processed message to persistent memory
        self.memory.save_message("user", processed_msg if is_cmd else user_text)

        # Show the animated thinking indicator (braille spinner + word discovery)
        container = self.query_one("#chat_container")
        self._thinking_widget = Static("  ⠋", classes="message system")
        container.mount(self._thinking_widget)
        self._thinking_state = {
            "braille_idx": 0,
            "word": random.choice(THINKING_WORDS),
            "discovered": "",
            "char_step": 0,
            "dots_cycle": 0,
        }
        self._thinking_timer = self.set_interval(0.08, self._animate_thinking)
        container.scroll_end(animate=True)

        # Call the API asynchronously to avoid freezing the interface
        self.call_ai_background()

    @work(exclusive=True, thread=True)
    def call_ai_background(self) -> None:
        """Run the AI in the background (Thread) to keep the UI responsive."""
        history = self.memory.get_history()

        # Since we already saved the user's message in history,
        # we separate the last message from the rest to send to the Phase 2 function.
        history_to_send = history[:-1]
        new_message = history[-1]["content"]

        response = call_ai_chat(
            provider=self.provider,
            api_key=self.api_key,
            api_model=self.api_model,
            system_instruction=self.system_instruction,
            chat_history=history_to_send,
            new_message=new_message,
            quiet=True,  # Don't print terminal loading (sys.stdout) since we're in a TUI
        )

        # Update the interface from the main thread
        def update_ui(result):
            # Remove the animated thinking indicator
            if self._thinking_timer:
                self._thinking_timer.stop()
                self._thinking_timer = None
            if self._thinking_widget:
                self._thinking_widget.remove()
                self._thinking_widget = None
            self._thinking_state = {}

            if result:
                self.memory.save_message("assistant", result)
                self.add_message("assistant", result)
            else:
                self.add_message("system", __("❌ Failed to get response from AI."))

        self.call_from_thread(update_ui, response)

    def action_show_help(self):
        """F1 shortcut: Show the help modal with shortcuts and slash commands."""
        self.push_screen(ChatHelpScreen())

    def action_refresh_diff(self):
        """F2 shortcut: Update the chat context with the latest code diff."""
        new_diff = get_git_diff(quiet=True)
        updated = self.memory.update_diff_if_changed(new_diff)
        if updated:
            self.add_message(
                "system", __("🔄 Diff updated! The AI now sees your latest changes.")
            )
        else:
            self.add_message("system", __("✅ Diff is already up to date."))

    def action_apply_code(self):
        """F5 shortcut: Extract the last AI code block and save it to a suggestion file."""
        history = self.memory.get_history()

        # Filter only the AI messages
        ai_messages = [m for m in history if m["role"] == "assistant"]
        if not ai_messages:
            self._notify_action(
                __("❌ No AI responses available to extract code from."),
                severity="warning",
            )
            return

        last_msg = ai_messages[-1]["content"]

        # Match triple-backtick code blocks: ```python, ``` python, ```, etc.
        code_blocks = re.findall(r"`{3}\s*(?:\w+)?\s*\n(.*?)`{3}", last_msg, re.DOTALL)

        # Fallback: split by triple backticks and take odd-indexed parts
        if not code_blocks:
            parts = last_msg.split("```")
            for i in range(1, len(parts), 2):
                block = parts[i].strip()
                if block:
                    # Strip language identifier from first line if present
                    first_line_end = block.find("\n")
                    if first_line_end > 0 and first_line_end < 20:
                        first_line = block[:first_line_end].strip()
                        if first_line and not " " in first_line:
                            block = block[first_line_end + 1 :]
                    code_blocks.append(block.strip())

        if code_blocks:
            extracted_code = "\n\n".join(code_blocks)
            key = (
                "".join(random.choices(string.ascii_letters + string.digits, k=3))
                + "-"
                + "".join(random.choices(string.ascii_letters + string.digits, k=3))
            )
            export_file = f"GITPR_PATCH_SUGGESTION_{key}.txt"
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(extracted_code)
            self._notify_action(
                __(
                    "⚡ Auto-Patch: Code extracted and saved to {file}!",
                    file=export_file,
                )
            )
        else:
            self._notify_action(
                __("❌ No code blocks found in the last AI message."),
                severity="warning",
            )

    def action_export_session(self):
        """F6 shortcut: Export the entire conversation to a structured Markdown file at the project root."""
        history = self.memory.get_history()
        export_text = f"# GitPR Chat Session Export\n**Repo:** {self.memory.repo_name} | **Branch:** {self.memory.branch_name}\n\n"

        for msg in history:
            role_icon = (
                "🧑‍💻 User"
                if msg["role"] == "user"
                else "🤖 AI Assistant"
                if msg["role"] == "assistant"
                else "⚙️ System"
            )
            export_text += f"### {role_icon}\n{msg['content']}\n\n---\n\n"

        export_file = f"GITPR_CHAT_EXPORT_{self.memory.session_uuid}.md"
        with open(export_file, "w", encoding="utf-8") as f:
            f.write(export_text)

        self._notify_action(
            __("📤 Session exported successfully to {file}!", file=export_file)
        )
