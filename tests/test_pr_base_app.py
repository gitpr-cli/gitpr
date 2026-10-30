"""The picker shown when the PR target is the branch checked out.

Two layers are covered here: the modal itself (driven headless) and the CLI
helper that opens it, writes the choice into the project file and resolves the
target again. Both talk to git only through functions this module patches, so
nothing here touches the real checkout or the user's .gitpr/conf.
"""

import asyncio
import contextlib
import sys
from unittest.mock import MagicMock, patch

import pytest
from textual.widgets import Select, Static

from src.main import _resolve_pr_target
from src.project_config import (
    BASE_BRANCH_FIELD,
    CurrentBranchError,
    ResolvedBase,
)
from src.ui.pr_base_app import (
    BRANCH_SELECT_ID,
    BaseBranchPromptApp,
    prompt_for_base_branch,
)


def run(coro):
    return asyncio.run(coro)


class TestBaseBranchPromptApp:
    def test_the_current_branch_is_not_an_option(self):
        async def scenario():
            app = BaseBranchPromptApp("develop", ["develop", "main", "release"])
            async with app.run_test() as pilot:
                await pilot.pause()
                select = app.query_one(f"#{BRANCH_SELECT_ID}", Select)
                assert [value for _, value in select._options] == ["main", "release"]
                assert select.value == "main"

        run(scenario())

    def test_the_screen_names_the_branch_it_is_refusing(self):
        async def scenario():
            app = BaseBranchPromptApp("develop", ["develop", "main"])
            async with app.run_test() as pilot:
                await pilot.pause()
                text = " ".join(
                    str(node.render()) for node in app.query(Static)
                )
                assert "develop" in text
                assert "cannot target itself" in text

        run(scenario())

    def test_confirming_returns_the_chosen_branch(self):
        async def scenario():
            app = BaseBranchPromptApp("develop", ["develop", "main", "release"])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one(f"#{BRANCH_SELECT_ID}", Select).value = "release"
                await pilot.pause()
                await pilot.click("#btn_prompt_confirm")
                await pilot.pause()
            return app.return_value

        assert run(scenario()) == "release"

    def test_cancelling_returns_empty(self):
        async def scenario():
            app = BaseBranchPromptApp("develop", ["develop", "main"])
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
            return app.return_value

        assert run(scenario()) == ""

    def test_no_alternative_means_no_modal(self):
        # Nothing to choose from: the caller must report the real error instead
        # of opening an empty picker.
        with patch.object(BaseBranchPromptApp, "run") as run_app:
            assert prompt_for_base_branch("main", ["main"]) == ""
        run_app.assert_not_called()


class TestResolvePrTarget:
    @pytest.fixture(autouse=True)
    def _tty(self):
        stdin = MagicMock()
        stdin.isatty.return_value = True
        with patch.object(sys, "stdin", stdin):
            yield

    def _patched(self, resolve, prompt=None, write=None):
        """Patches git and the picker; returns (context, prompt, write)."""
        stack = contextlib.ExitStack()
        stack.enter_context(
            patch("src.project_config.resolve_pull_request_base", side_effect=resolve)
        )
        stack.enter_context(
            patch("src.project_config.current_branch", return_value="develop")
        )
        stack.enter_context(
            patch(
                "src.project_config.list_branches",
                return_value=["develop", "main", "release"],
            )
        )
        stack.enter_context(
            patch(
                "src.project_config.project_config_path",
                return_value="/repo/.gitpr/conf/gitpr.config.yml",
            )
        )
        prompt_mock = MagicMock(return_value="") if prompt is None else prompt
        stack.enter_context(
            patch("src.ui.pr_base_app.prompt_for_base_branch", prompt_mock)
        )
        write_mock = MagicMock() if write is None else write
        stack.enter_context(
            patch("src.project_config.write_project_field_values", write_mock)
        )
        return stack, prompt_mock, write_mock

    def test_a_valid_target_never_opens_the_picker(self):
        stack, prompt, _ = self._patched(
            resolve=lambda base: ResolvedBase(branch="main", source="project")
        )
        with stack:
            resolved = _resolve_pr_target(None, quiet=False)

        assert resolved.branch == "main"
        prompt.assert_not_called()

    def test_the_picker_saves_the_choice_and_resolves_again(self):
        def resolve(base):
            resolve.calls += 1
            if resolve.calls == 1:
                raise CurrentBranchError("targets itself")
            return ResolvedBase(branch="release", source="project")

        resolve.calls = 0
        stack, prompt, write = self._patched(
            resolve=resolve, prompt=MagicMock(return_value="release")
        )
        with stack:
            resolved = _resolve_pr_target(None, quiet=False)

        prompt.assert_called_once_with("develop", ["develop", "main", "release"])
        write.assert_called_once_with(
            {BASE_BRANCH_FIELD: "release"},
            path="/repo/.gitpr/conf/gitpr.config.yml",
        )
        assert resolved.branch == "release"

    def test_cancelling_the_picker_keeps_the_refusal(self):
        stack, prompt, _ = self._patched(
            resolve=MagicMock(side_effect=CurrentBranchError("targets itself")),
            prompt=MagicMock(return_value=""),
        )
        with stack:
            with pytest.raises(CurrentBranchError):
                _resolve_pr_target(None, quiet=False)

        prompt.assert_called_once()

    def test_an_explicit_base_is_never_rewritten(self):
        # --base is a deliberate choice for this run, not stale configuration.
        stack, prompt, _ = self._patched(
            resolve=MagicMock(side_effect=CurrentBranchError("targets itself"))
        )
        with stack:
            with pytest.raises(CurrentBranchError):
                _resolve_pr_target("develop", quiet=False)

        prompt.assert_not_called()

    def test_a_quiet_run_does_not_open_the_picker(self):
        stack, prompt, _ = self._patched(
            resolve=MagicMock(side_effect=CurrentBranchError("targets itself"))
        )
        with stack:
            with pytest.raises(CurrentBranchError):
                _resolve_pr_target(None, quiet=True)

        prompt.assert_not_called()

    def test_a_non_interactive_run_does_not_open_the_picker(self):
        stack, prompt, _ = self._patched(
            resolve=MagicMock(side_effect=CurrentBranchError("targets itself"))
        )
        with patch.object(sys, "stdin", MagicMock(isatty=lambda: False)):
            with stack:
                with pytest.raises(CurrentBranchError):
                    _resolve_pr_target(None, quiet=False)

        prompt.assert_not_called()

    def test_an_unwritable_file_keeps_the_original_refusal(self):
        stack, _, _ = self._patched(
            resolve=MagicMock(side_effect=CurrentBranchError("targets itself")),
            prompt=MagicMock(return_value="release"),
            write=MagicMock(side_effect=OSError("read only")),
        )
        with stack:
            with pytest.raises(CurrentBranchError):
                _resolve_pr_target(None, quiet=False)
