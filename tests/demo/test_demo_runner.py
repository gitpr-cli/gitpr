"""The tour's state machine and the artifacts it pre-generates.

The sequence is the part a user notices when it breaks — a step skipped, a
"back" that lands somewhere else, an artifact that changes because the tour
regenerated it. None of that needs a terminal to test.
"""

from dataclasses import replace

import pytest

from src.demo.demo_runner import (
    STEPS,
    DemoState,
    DemoStep,
    build_artifacts,
    new_state,
    step_intro,
    step_title,
)
from src.demo.scenarios import load_scenario


@pytest.fixture
def state():
    return new_state("laravel-bug-fix")


class TestStateMachine:
    """Advancing, going back, and what counts as seen."""

    def test_starts_at_the_welcome_step(self, state):
        assert state.current_step is DemoStep.WELCOME
        assert state.completed_steps == []

    def test_advancing_walks_every_step_in_order(self, state):
        seen = [state.current_step]

        while state.advance():
            seen.append(state.current_step)

        assert seen == list(STEPS)
        assert state.current_step is DemoStep.NEXT_STEPS

    def test_advance_reports_the_end_of_the_tour(self, state):
        while state.advance():
            pass

        assert state.advance() is False
        assert state.current_step is DemoStep.NEXT_STEPS

    def test_back_reports_the_start_of_the_tour(self, state):
        assert state.back() is False
        assert state.current_step is DemoStep.WELCOME

    def test_back_returns_to_the_previous_step(self, state):
        state.advance()
        state.advance()

        assert state.current_step is DemoStep.COMMIT_GENERATION
        assert state.back() is True
        assert state.current_step is DemoStep.SHOW_DIFF

    def test_completed_steps_record_the_way_out(self, state):
        for _ in range(3):
            state.advance()

        assert state.completed_steps == [
            DemoStep.WELCOME,
            DemoStep.SHOW_DIFF,
            DemoStep.COMMIT_GENERATION,
        ]

    def test_revisiting_a_step_does_not_record_it_twice(self, state):
        state.advance()
        state.advance()
        state.back()
        state.back()
        state.advance()

        assert state.completed_steps == [DemoStep.WELCOME, DemoStep.SHOW_DIFF]

    def test_going_back_does_not_unsee_a_step(self, state):
        state.advance()
        state.advance()
        state.back()

        assert DemoStep.WELCOME in state.completed_steps
        assert DemoStep.SHOW_DIFF in state.completed_steps

    def test_first_and_last_flags_track_the_position(self, state):
        assert state.is_first and not state.is_last

        while state.advance():
            pass

        assert state.is_last and not state.is_first

    def test_step_number_is_one_based(self, state):
        assert state.step_number == 1
        state.advance()
        assert state.step_number == 2
        assert state.total_steps == len(STEPS)

    def test_the_scenario_survives_navigation(self, state):
        """Nothing about the scenario may depend on how far the user got."""
        scenario = state.scenario
        artifacts = dict(state.artifacts)

        for _ in range(5):
            state.advance()
        for _ in range(5):
            state.back()
        for _ in range(5):
            state.advance()

        assert state.scenario is scenario
        assert state.artifacts == artifacts


class TestArtifacts:
    """What each step shows, and that it is generated exactly once."""

    def test_every_content_step_has_an_artifact(self, state):
        for step in (
            DemoStep.SHOW_DIFF,
            DemoStep.COMMIT_GENERATION,
            DemoStep.QUALITY_REVIEW,
            DemoStep.PR_GENERATION,
        ):
            assert state.artifact_for(step).strip(), step

    def test_framing_steps_have_no_artifact(self, state):
        assert state.artifact_for(DemoStep.WELCOME) is None
        assert state.artifact_for(DemoStep.NEXT_STEPS) is None

    def test_show_diff_shows_the_scenario_diff(self, state):
        assert state.artifact_for(DemoStep.SHOW_DIFF) == state.scenario.diff

    def test_commit_artifact_is_the_pipeline_commit_message(self, state):
        assert state.artifacts["commit"] == state.scenario.commit_message

    def test_pr_artifact_starts_with_the_pipeline_description(self, state):
        assert state.artifacts["pr"].startswith(state.scenario.pr_description)

    def test_review_artifact_carries_the_linter_alerts(self, state):
        """Composed the way the local review flow composes it."""
        review = state.artifacts["review"]

        assert state.scenario.review in review
        for alert in state.scenario.linter["warnings"]:
            assert alert in review

    def test_artifacts_are_generated_once(self, monkeypatch):
        """Stepping back and forth must not re-run the pipeline."""
        import src.core

        original = src.core.generate_pr_content
        requested = []

        def spy(action_folder, action_type, *args, **kwargs):
            requested.append(action_type)
            return original(action_folder, action_type, *args, **kwargs)

        monkeypatch.setattr(src.core, "generate_pr_content", spy)

        state = new_state("laravel-bug-fix")
        for _ in range(5):
            state.advance()
        for _ in range(4):
            state.back()
        for _ in range(3):
            state.advance()

        assert requested == ["commit", "review", "pr"]

    def test_build_artifacts_covers_all_three_actions(self):
        assert set(build_artifacts(load_scenario("security-issue"))) == {
            "commit",
            "review",
            "pr",
        }


class TestTheBadgeOnThePrStep:
    """The PR step shows the badge a publish would attach.

    The tour replays where a real run measures, so the counts come from the
    scenario's own linter block: no rule is read and no diff is linted.
    """

    def test_the_pr_artifact_carries_the_badge(self, state):
        assert "img.shields.io/badge/GitPR" in state.artifacts["pr"]

    def test_the_badge_closes_the_body(self, state):
        """It is a footer under the description, not a replacement."""
        assert state.artifacts["pr"].rstrip().endswith("(https://gitpr.natanfiuza.dev.br/)")

    def test_a_lone_warning_is_yellow(self, state):
        """laravel-bug-fix records one warning and no errors."""
        assert "GitPR-0_errors_%C2%B7_1_warning-yellow" in state.artifacts["pr"]

    def test_a_recorded_error_is_red(self):
        state = new_state("security-issue")

        assert "GitPR-1_error_%C2%B7_1_warning-red" in state.artifacts["pr"]

    def test_the_counts_come_from_the_scenario_not_from_the_working_tree(
        self, tmp_path, monkeypatch
    ):
        """Outside a repository there are no rules, so a real lint would find
        nothing to report — the badge is there all the same, saying what the
        scenario recorded."""
        monkeypatch.chdir(tmp_path)

        state = new_state("security-issue")

        assert "1_error_%C2%B7_1_warning-red" in state.artifacts["pr"]

    def test_the_step_explains_where_the_badge_comes_from(self, state):
        """A raw shields.io line under the body needs saying out loud."""
        state.current_step = DemoStep.PR_GENERATION

        assert "gitpr --skill" in step_intro(state)


class TestStepCopy:
    """Titles and framing prose, which the TUI and the text mode share."""

    def test_every_step_has_a_title(self):
        for step in STEPS:
            assert step_title(step).strip(), step

    def test_titles_are_distinct(self):
        """A repeated title makes the section list in the output useless."""
        titles = [step_title(step) for step in STEPS]

        assert len(set(titles)) == len(titles)

    def test_every_step_has_framing_prose(self, state):
        for _ in STEPS:
            assert step_intro(state).strip(), state.current_step
            if state.is_last:
                break
            state.advance()

    def test_the_welcome_mentions_the_scenario(self, state):
        intro = step_intro(state)

        assert state.scenario.title in intro
        assert state.scenario.description in intro

    def test_the_tour_says_the_answers_are_replayed(self, state):
        """Showing canned output as if it were live would be dishonest."""
        assert "replayed" in step_intro(state)

    def test_next_steps_point_at_the_setup_command(self, state):
        while state.advance():
            pass

        assert "gitpr --init" in step_intro(state)
        assert "gitpr demo" in step_intro(state)

    def test_next_steps_suggest_another_scenario(self, state):
        while state.advance():
            pass

        assert "--scenario security-issue" in step_intro(state)

    def test_next_steps_omit_the_suggestion_when_there_is_no_sibling(self):
        """A build with one scenario must not advertise one that is absent."""
        scenario = replace(load_scenario("laravel-bug-fix"), other_scenarios=())
        state = DemoState(scenario=scenario, artifacts={}, current_step=DemoStep.NEXT_STEPS)

        assert "--scenario" not in step_intro(state)
