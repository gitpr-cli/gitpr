"""The replay provider keeps the real pipeline's contract.

The tour claims to show what the tool actually produces. That holds only while
``FakeAIProvider`` is a drop-in for ``call_ai_model`` and ``demo_pipeline``
leaves the rest of the generation path intact, so the signature comparison and
the end-to-end run below are the load-bearing tests in this file.
"""

import contextlib
import importlib
import inspect
import io

import pytest

from src.ai_providers import call_ai_model
from src.demo.fake_ai_provider import FakeAIProvider, demo_pipeline
from src.demo.scenarios import load_scenario

PATCH_TARGETS = (
    ("src.core", "call_ai_model"),
    ("src.core", "get_cached_response"),
    ("src.core", "save_cached_response"),
    ("src.core", "get_api_key"),
    ("src.core", "get_api_model"),
    ("src.core", "get_skill_context"),
    ("src.core", "get_base_branch"),
    ("src.metrics", "log_command_metric"),
    ("src.metrics", "log_local_metric"),
)


def _artifact(kind, scenario):
    """Run one action through the real pipeline and return what it produced."""
    from src.core import generate_pr_content

    folders = {"commit": "commit", "review": "review", "pr": "pr_desc"}
    return generate_pr_content(folders[kind], kind, scenario.diff, "gemini")


@pytest.fixture
def scenario():
    return load_scenario("laravel-bug-fix", "en")


class TestContract:
    """FakeAIProvider must be substitutable for call_ai_model."""

    def test_signature_matches_the_real_provider(self, scenario):
        """The whole design rests on this: replace, do not reimplement."""
        fake = FakeAIProvider(scenario)

        assert inspect.signature(fake.call_ai_model) == inspect.signature(call_ai_model)

    def test_returns_every_key_the_pipeline_reads(self, scenario):
        result = FakeAIProvider(scenario).call_ai_model(
            "gemini", "key", "model", "prompt", "system"
        )

        assert result == {
            "commit_message": scenario.commit_message,
            "review": scenario.review,
            "pr_description": scenario.pr_description,
        }

    def test_each_call_gets_its_own_dict(self, scenario):
        """generate_pr_content pops its bookkeeping key out of what it gets."""
        fake = FakeAIProvider(scenario)

        first = fake.call_ai_model("gemini", "key", "model", "p", "s")
        first.pop("review")

        second = fake.call_ai_model("gemini", "key", "model", "p", "s")
        assert "review" in second

    def test_records_the_arguments_it_was_called_with(self, scenario):
        fake = FakeAIProvider(scenario)

        fake.call_ai_model("deepseek", "k", "m", "the prompt", "the system", action="review")

        assert len(fake.calls) == 1
        assert fake.calls[0]["provider"] == "deepseek"
        assert fake.calls[0]["prompt"] == "the prompt"
        assert fake.calls[0]["system_instruction"] == "the system"
        assert fake.calls[0]["action"] == "review"

    def test_ignores_the_prompt(self, scenario):
        """A different diff must not change the answer: the tour is deterministic."""
        fake = FakeAIProvider(scenario)

        one = fake.call_ai_model("gemini", "k", "m", "diff one", "s")
        two = fake.call_ai_model("gemini", "k", "m", "diff two", "s")

        assert one == two


class TestDemoPipeline:
    """Every outward effect of the generation path is removed."""

    @pytest.mark.parametrize("module, name", PATCH_TARGETS, ids=lambda value: value)
    def test_every_patch_target_still_exists(self, module, name):
        """A rename in core.py or metrics.py must break this loudly.

        patch.multiple would raise on entry, but naming the targets here says
        which module owns each one and why the split is not arbitrary.
        """
        assert hasattr(importlib.import_module(module), name)

    def test_the_real_pipeline_returns_the_scenario_text(self, scenario):
        """The tour's core claim, tested end to end through production code."""
        with demo_pipeline(scenario):
            commit = _artifact("commit", scenario)
            review = _artifact("review", scenario)
            pr = _artifact("pr", scenario)

        assert commit["commit_message"] == scenario.commit_message
        assert review["review"] == scenario.review
        assert pr["pr_description"] == scenario.pr_description

    def test_the_pipeline_still_drives_the_provider(self, scenario):
        """Proves the substitution is in the call path, not bypassed."""
        with demo_pipeline(scenario) as fake:
            _artifact("commit", scenario)
            _artifact("review", scenario)
            _artifact("pr", scenario)

        assert [call["action"] for call in fake.calls] == ["commit", "review", "pr_desc"]

    def test_the_pipeline_is_never_asked_for_a_real_key(self, scenario):
        """get_api_key is stubbed, so nothing can consult the config."""
        with demo_pipeline(scenario) as fake:
            _artifact("commit", scenario)

        assert fake.calls[0]["api_key"] == "demo"
        assert fake.calls[0]["api_model"] == "demo-model"

    def test_pipeline_chatter_is_suppressed(self, scenario, capsys):
        """The tour prints its own framing; the pipeline must stay silent.

        An inner redirect captures what the pipeline would have printed, so the
        test fails if the pipeline ever goes quiet on its own and the
        suppression stops being the reason nothing reaches stdout.
        """
        chatter = io.StringIO()

        with demo_pipeline(scenario):
            with contextlib.redirect_stdout(chatter):
                _artifact("commit", scenario)

        assert chatter.getvalue(), "pipeline printed nothing; test proves nothing"
        assert capsys.readouterr().out == ""

    def test_swaps_the_function_while_inside(self, scenario):
        import src.core

        original = src.core.call_ai_model

        with demo_pipeline(scenario):
            assert src.core.call_ai_model is not original

        assert src.core.call_ai_model is original

    def test_restores_everything_after_an_error(self, scenario):
        import src.core

        original = src.core.get_api_key

        with pytest.raises(RuntimeError):
            with demo_pipeline(scenario):
                raise RuntimeError("boom")

        assert src.core.get_api_key is original

    def test_the_cache_write_is_swapped_for_a_no_op(self, scenario):
        """A real save would poison the user's cache with demo content.

        Asserted on the name the pipeline actually resolves. core.py binds the
        function at import time, so patching src.cache.save_cached_response
        would never intercept the pipeline's call — the test would pass while
        proving nothing about the demo.
        """
        import src.core

        original = src.core.save_cached_response

        with demo_pipeline(scenario):
            patched = src.core.save_cached_response

            assert patched is not original
            assert patched("commit", "commit", "hash", {"review": "x"}) is None

        assert src.core.save_cached_response is original
