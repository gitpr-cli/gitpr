"""The badge reaches the two paths that publish a body, and no others.

`pr_data` is built once in `src/main.py` and read by both publishers: the TUI
seeds its editable text area from it, and `--no-edit` composes it straight into
`PullRequestRequest.description`. Both are exercised here against the real
code — the app is constructed for real, and `_publish_pr_directly` runs for
real against a provider that captures the request instead of sending it.

The third path, `--no-publish`, writes a local `.md` from the AI payload before
the badge is ever built, and returns. That is an ordering property of `main.py`
rather than something callable from here, so it is verified end to end (a real
run has to produce a file with no `shields.io` in it) and not asserted below.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from textual.widgets import TextArea

from src.branding.badge_builder import append_badge, build_pr_badge
from src.branding.badge_data import BadgeCounts
from src.ui.pr_publish_app import PrPublishApp

BADGE = build_pr_badge(BadgeCounts(errors=0, warnings=2))
BODY = "## Summary\n\nAdds the ownership check."
BADGED_BODY = append_badge(BODY, BADGE)

PR_DATA = {"commit_message": "feat: add thing", "pr_description": BADGED_BODY}


@pytest.fixture(autouse=True)
def _no_publish_log(tmp_path):
    """Keep the TUI's publish log out of the repository during tests."""
    with patch(
        "src.ui.pr_publish_app._init_publish_log",
        return_value=str(tmp_path / "pub.log"),
    ):
        with patch("src.ui.pr_publish_app._log_event"):
            yield


def _app(tmp_path, description):
    return PrPublishApp(
        pr_data={"commit_message": "feat: add thing", "pr_description": description},
        repo_info="natanfiuza/gitpr",
        github_token="ghp_fake",
        base_branch="main",
        output_filename=str(tmp_path / "pr.md"),
    )


def _publish(pr_data, tmp_path):
    """Run the real `--no-edit` publisher against a provider that captures."""
    from src.main import _publish_pr_directly

    captured = {}

    def create_pull_request(repo_ref, request):
        captured["request"] = request
        return SimpleNamespace(url="https://example.com/pr/1")

    provider = SimpleNamespace(name="github", create_pull_request=create_pull_request)

    with patch("src.core.get_current_branch", return_value="feat/x"):
        with patch("click.confirm", return_value=False):
            with patch("src.metrics.log_command_metric"):
                _publish_pr_directly(
                    pr_data,
                    provider,
                    SimpleNamespace(raw="natanfiuza/gitpr"),
                    "main",
                    str(tmp_path / "pr.md"),
                )

    return captured["request"]


class TestTheTuiPublisher:
    """The badge is on screen before anything is sent, and can be deleted."""

    def test_the_seeded_body_carries_the_badge(self, tmp_path):
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _app(tmp_path, BADGED_BODY)

        assert BADGE in app.pr_body

    def test_the_badge_is_inside_the_editable_text_area(self, tmp_path):
        """Q7: seeded, not injected at POST time — the user has the last word."""

        async def run():
            with patch(
                "src.ui.pr_publish_app.get_current_branch", return_value="feat/x"
            ):
                app = _app(tmp_path, BADGED_BODY)

            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                area = app.query_one("#pr_body", TextArea)

                assert BADGE in area.text

        asyncio.run(run())

    def test_a_body_without_a_badge_stays_without_one(self, tmp_path):
        """Nothing is added to a body the badge never described."""
        with patch("src.ui.pr_publish_app.get_current_branch", return_value="feat/x"):
            app = _app(tmp_path, BODY)

        assert "shields.io" not in app.pr_body


class TestTheDirectPublisher:
    """`--no-edit` sends one composed body, and the badge is in it."""

    def test_the_published_body_carries_the_badge(self, tmp_path):
        request = _publish(PR_DATA, tmp_path)

        assert BADGE in request.description

    def test_the_description_is_still_the_description(self, tmp_path):
        """The badge is a footer, not a replacement."""
        request = _publish(PR_DATA, tmp_path)

        assert BODY in request.description

    def test_the_commit_message_block_is_untouched(self, tmp_path):
        request = _publish(PR_DATA, tmp_path)

        assert "**Recommended Commit Message:**" in request.description
        assert "feat: add thing" in request.description

    def test_a_body_without_a_badge_publishes_without_one(self, tmp_path):
        request = _publish(
            {"commit_message": "feat: add thing", "pr_description": BODY}, tmp_path
        )

        assert "shields.io" not in request.description


class TestTheNotice:
    """A body sent unseen says what went into it, and how to stop it."""

    def test_the_badge_is_announced(self, tmp_path, capsys):
        _publish(PR_DATA, tmp_path)

        assert "GITPR_BADGE=false" in capsys.readouterr().out

    def test_the_announcement_names_what_was_added(self, tmp_path, capsys):
        _publish(PR_DATA, tmp_path)

        assert "badge" in capsys.readouterr().out

    def test_a_body_without_a_badge_is_not_announced(self, tmp_path, capsys):
        """Nothing was added, so there is nothing to disclose."""
        _publish(
            {"commit_message": "feat: add thing", "pr_description": BODY}, tmp_path
        )

        assert "GITPR_BADGE" not in capsys.readouterr().out
