"""`gitpr demo` on screen — the same tour the text mode prints, drawn by Textual.

Headless: `run_test` drives a simulated terminal, and every artifact comes from
the recorded scenario, so no step here needs the network, a repository or a key.

The app is torn down when the tour ends, so the tests assert on what the screen
showed at each point — captured while it still existed — rather than on live
widgets.
"""

import asyncio

from textual.widgets import Markdown

from src.demo.demo_runner import STEPS, new_state, step_title
from src.demo.scenarios import load_scenario
from src.ui.demo.demo_app import DemoApp
from src.ui.demo.demo_help_screen import DemoHelpScreen

SCENARIO = "laravel-bug-fix"


def _text(container):
    """Everything a container is showing, whether or not it fits on screen."""
    parts = []

    for child in container.children:
        if isinstance(child, Markdown):
            parts.append(child.source)
        else:
            parts.append(str(child.render()))

    return "\n".join(parts)


def _tour(keys=(), scenario_name=SCENARIO, size=(100, 30), probe=None):
    """Press `keys` on a fresh tour and report what happened.

    Returns ``(snapshots, state, running, probed)``: the body text after each
    key press (index 0 is before any), the state machine at the end, whether
    the app was still running, and whatever `probe` returned when it was.
    """
    state = new_state(scenario_name)
    app = DemoApp(state)
    snapshots = []
    outcome = {}

    async def run():
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            snapshots.append(_text(app.query_one("#body")))

            for key in keys:
                await pilot.press(key)
                await pilot.pause()
                snapshots.append(_text(app.query_one("#body")))

            outcome["running"] = app.is_running
            outcome["probed"] = probe(app) if probe else None

    asyncio.run(run())

    return snapshots, state, outcome["running"], outcome["probed"]


def _heading(number):
    return "{number}/{total}  {title}".format(
        number=number, total=len(STEPS), title=step_title(STEPS[number - 1])
    )


class TestTheTourOnScreen:
    """The six steps, in order, each showing its own artifact."""

    def test_it_opens_on_the_welcome_step(self):
        snapshots, state, _, _ = _tour()

        assert state.current_step == STEPS[0]
        assert _heading(1) in snapshots[0]

    def test_the_first_screen_names_the_example(self):
        snapshots, _, _, _ = _tour()

        assert load_scenario(SCENARIO).title in snapshots[0]

    def test_each_press_shows_the_next_step(self):
        snapshots, state, _, _ = _tour(["n"] * 5)

        for number in range(2, len(STEPS) + 1):
            assert _heading(number) in snapshots[number - 1]

        assert state.current_step == STEPS[-1]

    def test_the_diff_is_shown_on_its_own_step(self):
        snapshots, _, _, _ = _tour(["n"])

        assert load_scenario(SCENARIO).diff in snapshots[1]

    def test_the_commit_message_is_shown_on_its_own_step(self):
        snapshots, _, _, _ = _tour(["n", "n"])

        assert load_scenario(SCENARIO).commit_message in snapshots[2]

    def test_the_review_is_shown_with_the_linter_alerts(self):
        snapshots, _, _, _ = _tour(["n", "n", "n"])
        scenario = load_scenario(SCENARIO)

        assert scenario.review in snapshots[3]
        assert scenario.linter["warnings"][0] in snapshots[3]

    def test_the_pull_request_description_is_shown_on_its_own_step(self):
        snapshots, _, _, _ = _tour(["n", "n", "n", "n"])

        assert load_scenario(SCENARIO).pr_description in snapshots[4]

    def test_the_last_screen_names_the_setup_command(self):
        snapshots, _, _, _ = _tour(["n"] * 5)

        assert "gitpr --init" in snapshots[5]

    def test_the_scenario_title_reaches_the_header(self):
        state = new_state(SCENARIO)

        assert DemoApp(state).sub_title == state.scenario.title


class TestMovingBackwards:
    """Reading a step twice must show the same thing, not regenerate it."""

    def test_going_back_shows_the_previous_step_again(self):
        snapshots, state, _, _ = _tour(["n", "n", "p"])

        assert state.current_step == STEPS[1]
        assert _heading(2) in snapshots[3]

    def test_a_step_read_twice_reads_the_same(self):
        snapshots, _, _, _ = _tour(["n", "n", "p", "n"])

        assert snapshots[4] == snapshots[2]

    def test_going_back_at_the_start_stays_on_the_welcome_step(self):
        snapshots, state, running, _ = _tour(["p"])

        assert state.current_step == STEPS[0]
        assert snapshots[1] == snapshots[0]
        assert running

    def test_a_step_already_seen_is_not_recorded_twice(self):
        _, state, _, _ = _tour(["n", "n", "p", "n"])

        assert state.completed_steps == [STEPS[0], STEPS[1]]


class TestLeavingTheTour:
    """Both ways out, and the one that must not leave early."""

    def test_the_last_press_leaves_the_tour(self):
        _, state, running, _ = _tour(["n"] * 6)

        assert not running
        assert state.completed_steps == list(STEPS[:-1])

    def test_escape_leaves_the_tour(self):
        _, _, running, _ = _tour(["escape"])

        assert not running

    def test_the_arrow_keys_drive_the_same_actions(self):
        snapshots, state, _, _ = _tour(["right", "right", "left"])

        assert state.current_step == STEPS[1]
        assert _heading(2) in snapshots[3]


class TestTheHelpModal:
    """F1 explains the keys without taking over the tour."""

    def test_f1_opens_the_help(self):
        _, _, _, screen = _tour(["f1"], probe=lambda app: type(app.screen).__name__)

        assert screen == DemoHelpScreen.__name__

    def test_the_help_lists_the_keys(self):
        _, _, _, text = _tour(
            ["f1"], probe=lambda app: _text(app.screen.query_one("#demo_help_dialog"))
        )

        for key in ("N", "P", "F1", "Esc"):
            assert key in text

    def test_the_help_says_what_the_tour_does_not_need(self):
        _, _, _, text = _tour(
            ["f1"], probe=lambda app: _text(app.screen.query_one("#demo_help_dialog"))
        )

        assert "no API key" in text

    def test_escape_closes_the_help_instead_of_the_tour(self):
        _, _, running, screen = _tour(
            ["f1", "escape"], probe=lambda app: type(app.screen).__name__
        )

        assert running
        assert screen != DemoHelpScreen.__name__


class TestIsolation:
    """§9.1 with the TUI in play: the whole tour on screen, network banned."""

    def test_the_whole_tour_runs_with_the_network_unavailable(self):
        snapshots, _, running, _ = _tour(["n"] * 5)

        assert running
        assert len(snapshots) == 6

    def test_no_binding_reaches_the_footer_twice(self):
        """The alternates are bound but hidden, so the footer lists four keys."""
        shown = [binding.action for binding in DemoApp.BINDINGS if binding.show]

        assert len(shown) == len(set(shown))
