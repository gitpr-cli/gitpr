"""Integration-wide guards.

Same two guards as ``tests/split/conftest.py`` and for the same reasons. The
network is off because a policy pack is *local* by design — resolution reads a
lockfile, hashes files and composes text, and a run that reached a registry
would be a different feature wearing this one's name. Whatever the AI would
answer is stubbed in the module that asks for it, so a test that reaches a
provider is a test that escaped its own stubs, and it should fail where it did
rather than quietly pass against a live key.

The language is pinned so assertions can name the text they expect instead of
depending on whatever ``~/.gitpr/langs`` holds on the machine running the suite.

What is deliberately *not* here is a guard against writing. These tests drive
``gitpr policy use``, which writes a lockfile — into a repository the fixture
created under ``tempfile``, never into one of anybody's. The two directories the
code would otherwise write to outside the fixture — ``~/.gitpr/policies`` and the
prompt cache — are redirected by the test case itself, which is where a reader
looking for "what does this touch" will look.
"""

import ipaddress
import socket

import pytest


def _blocked():
    raise AssertionError("a policy pack is local; nothing here may reach the network")


def _is_loopback(address):
    host = address[0] if isinstance(address, (tuple, list)) and address else address

    try:
        return ipaddress.ip_address(str(host)).is_loopback
    except ValueError:
        return str(host) == "localhost"


def _guard_method(real):
    """Guard a ``socket.socket`` method — ``self`` comes before the address."""

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
    a real connection over 127.0.0.1 — banning it outright would ban the event
    loop itself.
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
def english_interface(monkeypatch):
    """Pin the interface language so assertions can name the expected text."""
    import src.i18n

    monkeypatch.setattr(src.i18n, "CURRENT_LANG", "en_us")
    monkeypatch.setattr(src.i18n, "TRANSLATIONS", {})
