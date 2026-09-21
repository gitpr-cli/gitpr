"""Split-wide guards.

Two things every test under ``tests/split`` needs and should not have to ask
for. The network is off, because reading and regrouping a working tree is a
local operation end to end: the AI leg is always stubbed here, so a test that
reaches a provider is a test that escaped its own stubs, and it should fail in
the test that did it rather than quietly pass against a live key.

The interface language is pinned, so assertions can name the text they expect
instead of depending on the developer's ``~/.gitpr/langs``.

What is deliberately *not* here is a git guard. Every test in this directory
that touches a repository touches one the fixture created under ``tempfile``,
and the commands it runs there — including ``commit`` — are the subject of the
test, not a side effect on anyone's checkout.
"""

import ipaddress
import socket

import pytest


def _blocked():
    raise AssertionError("splitting a working tree must not touch the network")


def _is_loopback(address):
    """Whether a connection target stays on this machine."""
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
    monkeypatch.setattr(
        socket.socket, "connect", _guard_method(socket.socket.connect)
    )
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
    """Pin the interface language so assertions can name the expected text.

    English is the one language that needs no translation file — ``__()`` falls
    back to the key itself — so the suite does not depend on whatever the
    developer's ``~/.gitpr/langs`` happens to hold. A test that wants another
    language patches ``src.i18n`` itself, which wins over this.
    """
    import src.i18n

    monkeypatch.setattr(src.i18n, "CURRENT_LANG", "en_us")
    monkeypatch.setattr(src.i18n, "TRANSLATIONS", {})
