"""Badge-wide guards.

A badge is only text: a shields.io URL is written into a pull request body and
rendered later, in the reader's browser. GitPR never asks for that URL itself —
if it ever did, publishing a pull request would start depending on a third
party being up. The network is therefore banned for every test under
``tests/badge``, so an accidental request fails the test that provoked it.

Two smaller guarantees live here as well: the interface language is pinned, so
the CLI assertions can name the expected text, and the linter's local metric is
neutralised, so running this suite does not write into the developer's own
``~/.gitpr/metrics``.
"""

import ipaddress
import socket

import pytest


def _blocked():
    raise AssertionError("building a badge must not touch the network")


def _is_loopback(address):
    """Whether a connection target stays on this machine."""
    host = address[0] if isinstance(address, (tuple, list)) and address else address

    try:
        return ipaddress.ip_address(str(host)).is_loopback
    except ValueError:
        return str(host) == "localhost"


def _guard_method(real):
    """Guard a `socket.socket` method — `self` comes before the address."""

    def guarded(self, address, *args, **kwargs):
        if not _is_loopback(address):
            _blocked()
        return real(self, address, *args, **kwargs)

    return guarded


def _guard_function(real):
    """Guard a module-level connect helper, whose first argument is the address."""

    def guarded(address, *args, **kwargs):
        if not _is_loopback(address):
            _blocked()
        return real(address, *args, **kwargs)

    return guarded


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Any attempt to reach another machine fails the test.

    Loopback is the one exception, and only because the Windows proactor event
    loop builds its self-pipe with ``socket.socketpair()``, which falls back to
    a real connection over 127.0.0.1 — banning it would ban the event loop, and
    with it the Textual tests that publish a PR body.
    """
    monkeypatch.setattr(socket.socket, "connect", _guard_method(socket.socket.connect))
    monkeypatch.setattr(
        socket.socket, "connect_ex", _guard_method(socket.socket.connect_ex)
    )
    monkeypatch.setattr(
        socket, "create_connection", _guard_function(socket.create_connection)
    )

    for target in (
        "urllib.request.urlopen",
        "requests.Session.request",
        "requests.adapters.HTTPAdapter.send",
    ):
        monkeypatch.setattr(target, lambda *args, **kwargs: _blocked())


@pytest.fixture(autouse=True)
def no_linter_metrics(monkeypatch):
    """Keep the linter's telemetry thread out of the developer's profile.

    Logging a metric per run is correct in production — the badge runs the
    linter on a real command — but a test suite that appends to the user's own
    ``~/.gitpr/metrics`` is a side effect nobody asked for.
    """
    monkeypatch.setattr("src.linter_engine.log_local_metric", lambda *a, **k: None)


@pytest.fixture(autouse=True)
def english_interface(monkeypatch):
    """Pin the interface language so assertions can name the expected text.

    English is the one language that needs no translation file — `__()` falls
    back to the key itself — so the suite does not depend on whatever the
    developer's ``~/.gitpr/langs`` happens to hold. The badge text itself is
    English in every language; this is about the CLI around it.
    """
    import src.i18n

    monkeypatch.setattr(src.i18n, "CURRENT_LANG", "en_us")
    monkeypatch.setattr(src.i18n, "TRANSLATIONS", {})
