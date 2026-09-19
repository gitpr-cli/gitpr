"""Replay provider and pipeline isolation for the guided tour.

``FakeAIProvider.call_ai_model`` mirrors ``src.ai_providers.call_ai_model``
argument for argument. The tour replaces that function instead of branching
inside it, so the rest of the generation pipeline — prompt assembly, skill
context, diff chunking, cache keys, response parsing — is the production code
path. Only the source of the answer changes.

``demo_pipeline()`` removes everything along that path that would reach the
disk, the wire or the user's ``~/.gitpr/``: the prompt cache, telemetry,
metrics, the git lookups for changed documentation, and the API key lookups
that would otherwise make the pipeline give up before it ever calls the
provider.
"""

import contextlib
import io
from unittest import mock


class FakeAIProvider:
    """Answers every AI call from the scenario, without touching the network."""

    def __init__(self, scenario):
        self.scenario = scenario
        self.calls = []

    def call_ai_model(
        self,
        provider,
        api_key,
        api_model,
        prompt,
        system_instruction,
        quiet=False,
        action="ai_call",
    ):
        """Same signature as ``src.ai_providers.call_ai_model``, recorded per call.

        The prompt is recorded and then ignored: the tour replays a fixed
        answer, so nothing in it can steer the result.
        """
        self.calls.append(
            {
                "provider": provider,
                "api_key": api_key,
                "api_model": api_model,
                "prompt": prompt,
                "system_instruction": system_instruction,
                "quiet": quiet,
                "action": action,
            }
        )

        # A superset of every key the pipeline reads. generate_pr_content maps
        # the action onto a cache folder and then reads the key it wants off
        # the returned dict, so serving all three keys covers commit, review
        # and pr without dispatching on `action` here. A fresh dict per call:
        # the pipeline pops its own bookkeeping key out of what it gets back.
        return {
            "commit_message": self.scenario.commit_message,
            "review": self.scenario.review,
            "pr_description": self.scenario.pr_description,
        }


def _no_cache_read(*args, **kwargs):
    """Never answer from cache.

    A hit would replay whatever review the user last generated in their own
    repository — the opposite of a reproducible first impression.
    """
    return None


def _discard(*args, **kwargs):
    """Accept and drop. Used for every write and every metric."""
    return None


@contextlib.contextmanager
def demo_pipeline(scenario):
    """Run the real generation pipeline with every outward effect removed.

    The patches split across two modules on purpose: ``src.core`` holds the
    names ``generate_pr_content`` looks up at module level, but the two metric
    helpers are imported inside the function body from ``src.metrics``, so the
    name that matters is the one over there.

    Yields the fake, so a caller can inspect what the pipeline asked for.
    """
    fake = FakeAIProvider(scenario)

    with mock.patch.multiple(
        "src.core",
        call_ai_model=fake.call_ai_model,
        get_cached_response=_no_cache_read,
        save_cached_response=_discard,
        get_api_key=lambda *args, **kwargs: "demo",
        get_api_model=lambda *args, **kwargs: "demo-model",
        get_skill_context=lambda *args, **kwargs: "",
        get_base_branch=lambda *args, **kwargs: "",
    ), mock.patch.multiple(
        "src.metrics",
        log_command_metric=_discard,
        log_local_metric=_discard,
    ):
        # generate_pr_content announces the provider, the model and the cache
        # in the middle of generating. The tour prints its own framing, so the
        # pipeline's chatter is swallowed here rather than filtered later.
        with contextlib.redirect_stdout(io.StringIO()):
            yield fake
