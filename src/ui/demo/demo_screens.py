"""Widget composers for the stops of the tour.

Functions, not Screen classes: every app in this project is single-screen with
``ModalScreen`` overlays, so the demo keeps that shape rather than introducing
the first ``Screen`` subclass in the codebase.

The three generated artifacts are Markdown — the same text the CLI writes to
disk — so they are rendered with Textual's Markdown widget. The diff is fenced
as ```` ```diff ```` for the same reason, and because its ``---``/``+++`` lines
would otherwise be read as setext headings.
"""

from textual.widgets import Markdown, Static

from src.demo.demo_runner import DemoStep, step_intro, step_title


def step_heading(state):
    """The "step 2 of 6 — The example change" line."""
    return Static(
        "{number}/{total}  {title}".format(
            number=state.step_number,
            total=state.total_steps,
            title=step_title(state.current_step),
        ),
        classes="step_heading",
        markup=False,
    )


def step_content(state):
    """The widgets that show what this step is about.

    Framing steps (welcome, next steps) have no artifact; their prose from
    ``step_intro`` is the whole screen.
    """
    step = state.current_step
    content = state.artifact_for(step)

    if content is None:
        return []

    if step is DemoStep.SHOW_DIFF:
        return [_markdown("```diff\n" + content + "\n```", "step_diff")]

    if step is DemoStep.COMMIT_GENERATION:
        # Shown as plain text, the way `gitpr -c` prints it: a commit message is
        # not Markdown, and the Markdown widget would reflow its blank line.
        return [Static(content, id="step_commit", markup=False)]

    return [_markdown(content, "step_content")]


def _markdown(text, widget_id):
    return Markdown(text, id=widget_id)


def has_intro(state):
    """Whether the step has framing prose above its content."""
    return bool(step_intro(state))
