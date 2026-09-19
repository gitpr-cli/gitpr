"""``gitpr badge`` — the adoption snippet, printed and never installed.

Somebody who wants the badge in their own README should not have to hand-build a
shields.io URL. That is the whole command: it prints, and it stays away from the
file. The README belongs to the user, and a CLI that edits it is a CLI they
uninstall — the last class here holds it to that.

``--readme`` is the pipe-friendly form, so it prints the snippet and nothing
else, nothing that would need stripping before it lands in a file.
"""

import os

import pytest
from click.testing import CliRunner

from src.branding.badge_builder import (
    VALID_STYLES,
    build_readme_badge,
)
from src.main import cli

FLAT_SNIPPET = build_readme_badge("flat")
HEADER = "GitPR badge for your README"


@pytest.fixture(autouse=True)
def no_usage_log(monkeypatch):
    """`cli` records every invocation — in the developer's profile, not here."""
    monkeypatch.setattr("src.main.log_usage", lambda: None)


def _run(*args):
    return CliRunner().invoke(cli, ["badge", *args])


def _lines(stdout):
    return [line for line in stdout.splitlines() if line.strip()]


class TestTheReadmeSnippet:
    """`--readme` is the form that goes into a pipe.

    Asserted against ``stdout``, not the runner's combined ``output``: redirecting
    the snippet into a file has to leave a warning out of the file, and the
    combined stream would hide a warning printed on the wrong one.
    """

    def test_it_prints_the_snippet(self):
        assert _run("--readme").stdout.strip() == FLAT_SNIPPET

    def test_it_prints_nothing_else(self):
        assert len(_lines(_run("--readme").stdout)) == 1

    def test_no_explanation_is_mixed_into_the_output(self):
        assert HEADER not in _run("--readme").stdout

    def test_the_snippet_is_ready_to_paste(self):
        stdout = _run("--readme").stdout

        assert stdout.startswith("[![GitPR](https://img.shields.io/badge/")
        assert stdout.strip().endswith("](https://gitpr.natanfiuza.dev.br/)")


class TestTheStyle:
    @pytest.mark.parametrize("style", VALID_STYLES)
    def test_the_requested_style_lands_in_the_url(self, style):
        stdout = _run("--readme", "--style", style).stdout

        assert stdout.strip() == build_readme_badge(style)
        assert f"?style={style}" in stdout

    def test_the_default_style_is_flat(self):
        assert "?style=flat" in _run("--readme").stdout

    def test_an_unknown_style_warns_and_falls_back(self):
        result = _run("--readme", "--style", "holographic")

        assert result.exit_code == 0
        assert "holographic" in result.stderr
        assert "flat" in result.stderr
        assert result.stdout.strip() == FLAT_SNIPPET


class TestTheBareCommand:
    """Without `--readme`, the command explains itself before printing."""

    def test_it_says_what_the_snippet_is_for(self):
        assert HEADER in _run().stdout

    def test_it_still_prints_the_snippet(self):
        assert FLAT_SNIPPET in _run().stdout

    def test_it_mentions_the_badge_on_published_pull_requests(self):
        assert "pull request" in _run().stdout.lower()


class TestItNeverTouchesTheReadme:
    def test_nothing_is_written_to_the_project(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        _run()
        _run("--readme")
        _run("--readme", "--style", "for-the-badge")

        assert os.listdir(tmp_path) == []


class TestHelp:
    def test_it_lists_both_options(self):
        result = _run("--help")

        assert result.exit_code == 0
        assert "--readme" in result.output
        assert "--style" in result.output

    def test_it_links_the_documentation(self):
        """The epilog is built at import time, so assert on the page, not the language."""
        assert "/docs/badge" in _run("--help").stdout
