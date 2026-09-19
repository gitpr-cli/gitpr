"""`gitpr demo --no-tui` — the tour as plain, ordered text.

This is the path CI, limited terminals and GIF recordings use, so its output is
also the one place the whole tour can be asserted as a single artefact: every
step present, in order, with its content.
"""

import ast
import json
from pathlib import Path

import pytest

from src.demo.demo_runner import STEPS, new_state, run_demo_text_mode, step_title

REPO = Path(__file__).resolve().parents[2]
PT_BR_FILE = REPO / "langs" / "pt_br.json"
TEXT_MODE_DIR = REPO / "src" / "demo"


def _chrome_keys():
    """Every `__()` key the text mode can print, read from the source.

    Read from the AST instead of listed here: the point of the test below is to
    fail when a key is added and left in English, and a hand-kept list would
    simply not know about it. Implicitly concatenated literals fold into one key
    here, which is what `__()` sees at runtime — the regex in
    tests/sync_i18n.py does not, which is why that tool does not build the
    files.
    """
    keys = set()

    for path in TEXT_MODE_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            if node.func.id != "__" or not node.args:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                keys.add(first.value)

    return keys


def _shipped_pt_br():
    return json.loads(PT_BR_FILE.read_text(encoding="utf-8"))


@pytest.fixture
def output(capsys):
    """Run the tour once and hand back everything it printed."""

    def _run(scenario_name="laravel-bug-fix"):
        state = new_state(scenario_name)
        run_demo_text_mode(state)
        return capsys.readouterr().out

    return _run


class TestSectionOrder:
    """All six sections, in the order the tour defines."""

    def test_every_section_heading_is_present_in_order(self, output):
        text = output()
        total = len(STEPS)

        headings = [
            "{number}/{total}  {title}".format(
                number=number, total=total, title=step_title(step)
            )
            for number, step in enumerate(STEPS, start=1)
        ]

        positions = [text.index(heading) for heading in headings]
        assert positions == sorted(positions)

    def test_the_welcome_section_comes_first(self, output):
        text = output()

        assert text.index(step_title(STEPS[0])) < text.index(step_title(STEPS[1]))

    def test_the_last_section_comes_last(self, output):
        text = output()

        assert text.index(step_title(STEPS[-1])) > text.index(step_title(STEPS[-2]))


class TestSectionContent:
    """Each section shows the artifact it is supposed to."""

    def test_the_diff_is_shown(self, output):
        text = output()
        from src.demo.scenarios import load_scenario

        assert load_scenario("laravel-bug-fix").diff in text

    def test_the_commit_message_is_shown(self, output):
        text = output()
        from src.demo.scenarios import load_scenario

        assert load_scenario("laravel-bug-fix").commit_message in text

    def test_the_review_is_shown_with_its_linter_alerts(self, output):
        text = output()
        from src.demo.scenarios import load_scenario

        scenario = load_scenario("laravel-bug-fix")

        assert scenario.review in text
        assert scenario.linter["warnings"][0] in text

    def test_the_pull_request_description_is_shown(self, output):
        text = output()
        from src.demo.scenarios import load_scenario

        assert load_scenario("laravel-bug-fix").pr_description in text

    def test_the_next_steps_section_names_the_setup_command(self, output):
        assert "gitpr --init" in output()

    def test_the_scenario_title_is_announced(self, output):
        from src.demo.scenarios import load_scenario

        assert load_scenario("laravel-bug-fix").title in output()


class TestNonInteractive:
    """Piped output must run straight through."""

    def test_no_prompt_is_printed_when_stdin_is_not_a_terminal(self, output):
        """A prompt would block a pipe forever waiting for an answer."""
        assert "Press Enter" not in output()

    def test_the_whole_tour_prints_without_input(self, output):
        assert len(output().strip().splitlines()) > 60


class TestOtherScenarios:
    """The text mode is not tied to the default scenario."""

    def test_the_security_scenario_prints_its_own_content(self, output):
        from src.demo.scenarios import load_scenario

        scenario = load_scenario("security-issue")
        text = output("security-issue")

        assert scenario.diff in text
        assert scenario.pr_description in text
        assert load_scenario("laravel-bug-fix").commit_message not in text

    def test_a_scenario_in_another_language_prints_that_language(self, capsys, monkeypatch):
        import src.i18n

        monkeypatch.setattr(src.i18n, "CURRENT_LANG", "pt_br")
        monkeypatch.setattr(src.i18n, "TRANSLATIONS", {})

        state = new_state("laravel-bug-fix")
        run_demo_text_mode(state)

        from src.demo.scenarios import load_scenario

        assert load_scenario("laravel-bug-fix", "pt_br").pr_description in capsys.readouterr().out


class TestStateAfterTheTour:
    """The text mode drives the same state machine as the TUI."""

    def test_the_tour_ends_on_the_last_step(self, capsys):
        state = new_state()

        run_demo_text_mode(state)
        capsys.readouterr()

        assert state.is_last

    def test_every_step_but_the_last_is_recorded_as_seen(self, capsys):
        state = new_state()

        run_demo_text_mode(state)
        capsys.readouterr()

        assert state.completed_steps == list(STEPS[:-1])


class TestTheChromeFollowsTheLanguage:
    """`--lang` must move the tour's own wording, not only the scenario prose.

    tests/test_i18n.py enforces parity across the six files and non-identity
    only for keys carrying a placeholder; a chrome key left in English passes
    there and still renders a half-translated tour. These walk the rendered
    output and the shipped file instead.
    """

    @pytest.fixture
    def pt_br(self, monkeypatch, capsys):
        """The tour as a pt_br user sees it, with the committed file loaded.

        The file, not a download: this is what the next release publishes, and
        a key missing from it is exactly what these tests are looking for.
        """
        import src.i18n

        monkeypatch.setattr(src.i18n, "CURRENT_LANG", "pt_br")
        monkeypatch.setattr(src.i18n, "TRANSLATIONS", _shipped_pt_br())

        run_demo_text_mode(new_state("laravel-bug-fix"))

        return capsys.readouterr().out

    def test_every_step_heading_is_rendered_in_the_chosen_language(self, pt_br):
        total = len(STEPS)

        for number, step in enumerate(STEPS, start=1):
            heading = "{number}/{total}  {title}".format(
                number=number, total=total, title=step_title(step)
            )
            assert heading in pt_br

    def test_no_english_chrome_survives_in_the_rendered_tour(self, pt_br):
        survivors = sorted(key for key in _chrome_keys() if key in pt_br)

        assert survivors == []

    def test_the_shipped_file_carries_every_chrome_key_translated(self):
        translations = _shipped_pt_br()

        missing = sorted(key for key in _chrome_keys() if not translations.get(key))
        assert missing == []

        untranslated = sorted(
            key for key in _chrome_keys() if translations.get(key) == key
        )
        assert untranslated == []
