"""The tour's three promises: no connection, no repository, no configuration.

Each class below states one of them and then tries to break it. The first test
in ``TestNoNetwork`` matters most: it proves the ban is real, so the tests that
follow are not passing simply because nothing ever tried to reach out.
"""

import socket
import urllib.request
from pathlib import Path

import pytest

from src.demo.demo_runner import new_state, run_demo, run_demo_text_mode


def _profile_snapshot():
    """Every path under the user's ~/.gitpr, relative to it."""
    root = Path.home() / ".gitpr"

    if not root.exists():
        return set()

    return {str(path.relative_to(root)) for path in root.rglob("*")}


class TestNoNetwork:
    """The tour works with the network completely unavailable."""

    def test_the_ban_itself_fails_a_real_attempt(self):
        """Without this, everything below could pass while proving nothing."""
        with pytest.raises(AssertionError):
            socket.create_connection(("example.com", 80))

    def test_urlopen_is_banned_too(self):
        with pytest.raises(AssertionError):
            urllib.request.urlopen("https://example.com")

    def test_the_internet_check_the_product_itself_uses_is_banned(self):
        """`check_internet_connection()` opens exactly this socket."""
        sock = socket.socket()

        try:
            with pytest.raises(AssertionError):
                sock.connect(("8.8.8.8", 53))
        finally:
            sock.close()

    def test_only_loopback_gets_through(self):
        """The ban's one exception, kept narrow.

        The Windows proactor event loop builds its self-pipe over 127.0.0.1,
        so loopback has to stay reachable — but a refused connection is not a
        banned one, and any address off this machine still fails.
        """
        sock = socket.socket()
        sock.settimeout(2)

        try:
            with pytest.raises(OSError) as refused:
                sock.connect(("127.0.0.1", 9))
        finally:
            sock.close()

        assert not isinstance(refused.value, AssertionError)

    def test_the_tour_completes_in_text_mode(self, capsys):
        run_demo(tui=False)

        assert "gitpr --init" in capsys.readouterr().out

    def test_the_tour_completes_for_every_scenario(self, capsys):
        from src.demo.scenarios import SCENARIO_NAMES

        for name in SCENARIO_NAMES:
            state = new_state(name)
            run_demo_text_mode(state)

        assert capsys.readouterr().out.count("gitpr --init") == len(SCENARIO_NAMES)


class TestNoRepository:
    """Nothing here needs a checkout, and nothing may create one."""

    def test_the_working_directory_is_not_a_repository(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        assert not (tmp_path / ".git").exists()

    def test_the_tour_completes_outside_a_repository(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)

        run_demo(tui=False)

        assert "gitpr --init" in capsys.readouterr().out

    def test_it_leaves_the_working_directory_untouched(self, tmp_path, monkeypatch, capsys):
        """No checkout, no output file, not even a cache directory."""
        monkeypatch.chdir(tmp_path)

        run_demo(tui=False)
        capsys.readouterr()

        assert list(tmp_path.iterdir()) == []


class TestNoConfiguration:
    """No API key, no provider, no .env — the tour still runs."""

    def test_the_tour_completes_without_a_config_file(self, tmp_path, monkeypatch, capsys):
        missing = tmp_path / "no-such-env-file"
        monkeypatch.setattr("src.config.ENV_FILE", missing)

        run_demo(tui=False)
        capsys.readouterr()

        assert not missing.exists()

    def test_no_api_key_is_read_from_the_environment(self, monkeypatch, capsys):
        """conftest clears these; assert it here so the guarantee is visible."""
        for name in ("GEMINI_API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY_ENCRYPTED"):
            assert not __import__("os").environ.get(name)

        run_demo(tui=False)
        capsys.readouterr()

    def test_a_configured_provider_does_not_change_the_output(
        self, monkeypatch, capsys, tmp_path
    ):
        """Whatever the developer has configured must not reach the tour."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEFAULT_AI_PROVIDER", "deepseek")

        run_demo(tui=False)
        configured = capsys.readouterr().out

        monkeypatch.delenv("DEFAULT_AI_PROVIDER")
        run_demo(tui=False)
        default = capsys.readouterr().out

        assert configured == default


class TestNothingIsWritten:
    """The demo may not touch the user's ~/.gitpr — cache, metrics or logs."""

    def test_the_prompt_cache_and_metrics_are_untouched(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        before = _profile_snapshot()

        run_demo(tui=False)
        capsys.readouterr()

        assert _profile_snapshot() == before

    def test_the_snapshot_actually_sees_the_profile(self):
        """A snapshot that always came back empty would make the test above free.

        Importing ``src.i18n`` creates ``~/.gitpr/.env`` on first run, so an
        empty snapshot here means the helper is looking in the wrong place —
        not that the machine is clean.
        """
        assert _profile_snapshot(), "snapshot found nothing; the guard above proves nothing"
