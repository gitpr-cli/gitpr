"""A badge that needed the network would fail where it matters most.

The URL is written into a pull request body and rendered later by the reader's
browser. GitPR only ever writes the address; asking shields.io to confirm it
renders would put a third party between the user and the publish button.

The first two tests prove the ban in ``conftest`` is real, so the rest are not
passing because nothing ever tried to reach out.
"""

import socket
import urllib.request

import pytest

from src.branding.badge_builder import (
    build_pr_badge,
    build_readme_badge,
    append_badge,
)
from src.branding.badge_data import BadgeCounts


class TestTheBanItself:
    def test_fetching_the_badge_url_is_banned(self):
        with pytest.raises(AssertionError):
            urllib.request.urlopen(
                "https://img.shields.io/badge/GitPR-no_issues-brightgreen"
            )

    def test_a_socket_to_shields_io_is_banned(self):
        sock = socket.socket()

        try:
            with pytest.raises(AssertionError):
                sock.connect(("img.shields.io", 443))
        finally:
            sock.close()


class TestNothingIsFetched:
    """Every badge the product can produce, built with the network banned."""

    def test_every_pr_badge_builds(self):
        for counts in (
            BadgeCounts(errors=0, warnings=0),
            BadgeCounts(errors=0, warnings=3),
            BadgeCounts(errors=2, warnings=0),
            BadgeCounts(errors=7, warnings=11),
        ):
            assert "img.shields.io" in build_pr_badge(counts)

    def test_every_readme_style_builds(self):
        for style in ("flat", "flat-square", "for-the-badge", "unknown"):
            assert "img.shields.io" in build_readme_badge(style)

    def test_the_whole_publish_composition_builds(self):
        """Data, badge and body together — the path a publish actually walks."""
        body = append_badge("## Summary\n\nSomething.", build_pr_badge(BadgeCounts(0, 1)))

        assert "img.shields.io" in body

    def test_the_url_is_all_that_is_produced(self):
        """The badge is text. Nothing is downloaded, cached or verified."""
        badge = build_pr_badge(BadgeCounts(errors=0, warnings=0))

        assert badge.startswith("[![GitPR](https://img.shields.io/badge/")
        assert badge.endswith("](https://gitpr.natanfiuza.dev.br/)")
