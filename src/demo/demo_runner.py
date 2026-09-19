"""The tour's state machine and its two front ends.

The state machine holds no UI: the Textual app and the plain-text mode drive
the same ``DemoState``, which is what makes the sequence testable without a
terminal. The three artifacts are generated once, before the tour starts, so
stepping backwards never regenerates anything and what the user sees cannot
depend on how far they had already got.
"""

import sys
from dataclasses import dataclass, field
from enum import Enum

import click

from src.branding.badge_builder import append_badge, build_pr_badge
from src.branding.badge_data import BadgeCounts
from src.doc_links import doc_url
from src.demo.fake_ai_provider import demo_pipeline
from src.demo.scenarios import DemoScenario, load_scenario
from src.i18n import __
from src.review.render import compose_review_content

class DemoStep(str, Enum):
    """The tour's stops, in the order they are shown."""

    WELCOME = "welcome"
    SHOW_DIFF = "show_diff"
    COMMIT_GENERATION = "commit_generation"
    QUALITY_REVIEW = "quality_review"
    PR_GENERATION = "pr_generation"
    NEXT_STEPS = "next_steps"


STEPS = tuple(DemoStep)

_ARTIFACT_KEYS = {
    DemoStep.COMMIT_GENERATION: "commit",
    DemoStep.QUALITY_REVIEW: "review",
    DemoStep.PR_GENERATION: "pr",
}


def step_title(step):
    """Translated title of a step.

    Built per call, not at import: `__` reads the live translation table, so a
    module-level dict would freeze whatever language was detected at start-up
    and ignore `--lang`.
    """
    return {
        DemoStep.WELCOME: __("Welcome to GitPR"),
        DemoStep.SHOW_DIFF: __("The example change"),
        DemoStep.COMMIT_GENERATION: __("Commit message"),
        DemoStep.QUALITY_REVIEW: __("Code review"),
        DemoStep.PR_GENERATION: __("Pull request description"),
        DemoStep.NEXT_STEPS: __("Next steps"),
    }[step]


def step_intro(state):
    """The prose that frames a step, above the artifact it shows."""
    scenario = state.scenario

    if state.current_step is DemoStep.WELCOME:
        return "\n\n".join(
            [
                __(
                    "GitPR turns a diff into a commit message, a code review and "
                    "a pull request description, using an AI provider you "
                    "configure. This tour walks through all three."
                ),
                __(
                    "Everything here runs on a recorded example: no API key, no "
                    "Git repository and no connection are needed, and the "
                    "answers you are about to see were generated once by GitPR "
                    "and are replayed."
                ),
                __("Example: {title}", title=scenario.title),
                scenario.description,
            ]
        )

    if state.current_step is DemoStep.SHOW_DIFF:
        return __(
            "This is the change the tour works on. Everything that follows is "
            "produced from this diff alone."
        )

    if state.current_step is DemoStep.COMMIT_GENERATION:
        return __(
            "What `gitpr -c` writes for that diff: a Conventional Commits "
            "subject, plus the reasoning that does not fit in it."
        )

    if state.current_step is DemoStep.QUALITY_REVIEW:
        return __(
            "What `gitpr -r` reports. The local linter runs first, so its "
            "alerts are listed above the review itself."
        )

    if state.current_step is DemoStep.PR_GENERATION:
        return "\n\n".join(
            [
                __(
                    "What `gitpr` writes for the branch: a pull request description "
                    "with what changed, why, and what the reviewer should look at."
                ),
                __(
                    "The badge at the end is attached when the pull request is "
                    "published, with what the linter found. It only appears once "
                    "you have linter rules configured: run `gitpr --skill`."
                ),
            ]
        )

    if state.current_step is DemoStep.NEXT_STEPS:
        steps = [
            __("Configure a provider and a forge token: gitpr --init"),
            __("Documentation: {url}", url=doc_url("demo.md")),
            __("Guided tour again: gitpr demo"),
        ]
        if scenario.other_scenarios:
            steps.append(
                __(
                    "Another example: gitpr demo --scenario {name}",
                    name=scenario.other_scenarios[0],
                )
            )
        return "\n".join(f"  • {line}" for line in steps)

    return ""


def _step_body(state):
    """The artifact a step shows, or empty for the framing steps."""
    return state.artifact_for(state.current_step) or ""


@dataclass
class DemoState:
    """Where the tour is, what it has to show, and what has been seen."""

    scenario: DemoScenario
    artifacts: dict
    current_step: DemoStep = DemoStep.WELCOME
    completed_steps: list = field(default_factory=list)

    @property
    def step_number(self):
        """1-based position, for the "step 2 of 6" heading."""
        return STEPS.index(self.current_step) + 1

    @property
    def total_steps(self):
        return len(STEPS)

    @property
    def is_first(self):
        return self.current_step is STEPS[0]

    @property
    def is_last(self):
        return self.current_step is STEPS[-1]

    def artifact_for(self, step):
        """The text a step puts on screen, or None for the framing steps."""
        if step is DemoStep.SHOW_DIFF:
            return self.scenario.diff
        return self.artifacts.get(_ARTIFACT_KEYS.get(step))

    def advance(self):
        """Move one step forward. False at the end of the tour.

        Steps are recorded as seen on the way out rather than on the way back:
        going back to re-read something does not un-see it.
        """
        if self.is_last:
            return False

        if self.current_step not in self.completed_steps:
            self.completed_steps.append(self.current_step)

        self.current_step = STEPS[STEPS.index(self.current_step) + 1]
        return True

    def back(self):
        """Move one step back. False at the start of the tour."""
        if self.is_first:
            return False

        self.current_step = STEPS[STEPS.index(self.current_step) - 1]
        return True


def build_artifacts(scenario):
    """Generate the three artifacts the tour shows, once.

    The review is composed with the linter alerts exactly as the local review
    flow composes it, so the screen matches what `gitpr -r` writes to disk. The
    pull request carries the badge a publish would attach, counted from the
    same recorded alerts.
    """
    from src.core import generate_pr_content

    with demo_pipeline(scenario):
        commit = generate_pr_content("commit", "commit", scenario.diff, "gemini")
        review = generate_pr_content("review", "review", scenario.diff, "gemini")
        pr = generate_pr_content("pr_desc", "pr", scenario.diff, "gemini")

    return {
        "commit": _required(commit, "commit_message"),
        "review": compose_review_content(_required(review, "review"), scenario.linter),
        "pr": append_badge(
            _required(pr, "pr_description"), _recorded_badge(scenario.linter)
        ),
    }


def _recorded_badge(linter):
    """The badge this scenario's alerts would produce.

    The tour replays where a real run measures: the counts come from the
    scenario's own linter block, so no rule is read from disk and no diff is
    linted. A scenario whose block is empty shows the badge of a clean run —
    rules did run there, they just found nothing.
    """
    return build_pr_badge(
        BadgeCounts(
            errors=len(linter.get("errors", [])),
            warnings=len(linter.get("warnings", [])),
        )
    )


def _required(result, key):
    """Pull a generation result out of the pipeline, refusing to ship a blank.

    An empty tour is worse than a loud failure: it would look like the tool
    produced nothing, when the real cause is that the pipeline never reached
    the provider.
    """
    value = (result or {}).get(key, "")

    if not value.strip():
        raise RuntimeError(
            "gitpr demo: the generation pipeline returned no {key!r}".format(key=key)
        )

    return value


def new_state(scenario_name=None):
    """Load a scenario and pre-generate everything the tour will show.

    The language is not a parameter: the scenario follows the live interface
    language, the same one the surrounding chrome is written in. `--lang` is
    handled by the CLI through ``i18n.set_lang()``, as it is for every other
    command, so both halves of the tour always agree.
    """
    scenario = load_scenario(scenario_name)

    return DemoState(scenario=scenario, artifacts=build_artifacts(scenario))


def run_demo(scenario_name=None, tui=True):
    """Entry point for `gitpr demo`.

    Never instantiates a real provider and never opens a socket: the only
    generation path is the one `demo_pipeline` has stripped of outward effects.
    """
    state = new_state(scenario_name)

    if tui:
        from src.ui.demo.demo_app import DemoApp

        DemoApp(state).run()
    else:
        run_demo_text_mode(state)


def run_demo_text_mode(state):
    """Print the tour straight through, without Textual.

    Carries the same steps and the same artifacts as the TUI, for CI, for
    limited terminals, and for recording a GIF or an asciinema cast where a
    repeatable linear output beats an interactive screen.
    """
    while True:
        _render_step(state)

        if state.is_last:
            return

        _pause()
        state.advance()


def _render_step(state):
    rule = "─" * 64
    heading = "{number}/{total}  {title}".format(
        number=state.step_number,
        total=state.total_steps,
        title=step_title(state.current_step),
    )

    click.echo()
    click.secho(rule, dim=True)
    click.secho("  " + heading, fg="cyan", bold=True)
    click.secho(rule, dim=True)
    click.echo()

    intro = step_intro(state)
    if intro:
        click.echo(intro)
        click.echo()

    body = _step_body(state)
    if body:
        click.echo(body)
        click.echo()


def _pause():
    """Wait for Enter, but only when a human is watching.

    Piped output — CI, a recording — must run straight through: asking a pipe
    for input would block it forever.
    """
    if not sys.stdin.isatty():
        return

    try:
        input("  " + __("Press Enter to continue..."))
    except (EOFError, KeyboardInterrupt):
        click.echo()
