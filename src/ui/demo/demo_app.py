"""The tour's Textual front end.

Single-screen, like every other app in this project: one screen with the step
in a scrollable body, and the help modal on top of it. The state machine lives
in ``src.demo.demo_runner`` — this module only draws it.
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Static

from src.demo.demo_runner import step_intro
from src.ui.demo.demo_help_screen import DemoHelpScreen
from src.ui.demo.demo_screens import step_content, step_heading
from src.i18n import __


class DemoApp(App):
    """Guided tour of GitPR over a recorded example."""

    TITLE = __("GitPR - Guided Tour")
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    #body { padding: 1 2; }
    #body Markdown { padding: 0; }
    .step_heading { text-style: bold; color: $accent; margin-bottom: 1; }
    .step_intro { margin-bottom: 1; color: $text-muted; }
    """

    # One visible binding per action, with the alternates bound but hidden: the
    # footer shows one entry per binding, so binding them all visibly would
    # print "n Next  enter Next  right Next".
    BINDINGS = [
        Binding("n", "next_step", __("Next"), key_display="n / →"),
        Binding("enter", "next_step", "", show=False),
        Binding("right", "next_step", "", show=False),
        Binding("p", "previous_step", __("Previous"), key_display="p / ←"),
        Binding("left", "previous_step", "", show=False),
        Binding("f1", "show_help", __("Help")),
        Binding("escape", "quit", __("Exit")),
    ]

    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.sub_title = state.scenario.title

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield VerticalScroll(id="body")
        yield Footer()

    async def on_mount(self) -> None:
        await self._render_step()

    async def _render_step(self) -> None:
        """Replace the body with the widgets of the current step."""
        body = self.query_one("#body", VerticalScroll)

        widgets = [step_heading(self.state)]

        intro = step_intro(self.state)
        if intro:
            widgets.append(Static(intro, classes="step_intro", markup=False))

        widgets.extend(step_content(self.state))

        await body.remove_children()
        await body.mount_all(widgets)
        body.scroll_home(animate=False)

    async def action_next_step(self) -> None:
        """Advance, or leave the tour once there is nothing left to show."""
        if not self.state.advance():
            self.exit()
            return

        await self._render_step()

    async def action_previous_step(self) -> None:
        """Go back one step; a bell at the start says there is nowhere to go."""
        if not self.state.back():
            self.bell()
            return

        await self._render_step()

    def action_show_help(self) -> None:
        self.push_screen(DemoHelpScreen())
