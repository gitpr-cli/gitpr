"""Demo-wide guards.

Every test under ``tests/demo`` runs with the network disabled. Working with no
connection at all is the tour's central promise, so an accidental request should
fail loudly in whichever test provoked it, not only in the one written to assert
the promise by name.

The demo also has to survive a machine with no configuration, so the API-key
environment is cleared here too — a developer running the suite with a real
``GEMINI_API_KEY`` in their shell must not get a different result.
"""

import ipaddress
import socket

import pytest

_API_KEY_VARIABLES = (
    "GEMINI_API_KEY",
    "GEMINI_API_KEY_ENCRYPTED",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_API_KEY_ENCRYPTED",
    "DEFAULT_AI_PROVIDER",
)


def _blocked():
    raise AssertionError("the demo must not touch the network")


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
    a real connection over 127.0.0.1. Banning that outright would ban the event
    loop itself — and with it every Textual test in the suite. Traffic that
    actually leaves the machine, which is what the tour promises to avoid, is
    still blocked at the socket, the URL and the HTTP layer.
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
def no_api_keys(monkeypatch):
    """The demo runs with nothing configured."""
    for name in _API_KEY_VARIABLES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def english_interface(monkeypatch):
    """Pin the interface language so assertions can name the expected text.

    English is the one language that needs no translation file — `__()` falls
    back to the key itself — so the suite does not depend on whatever the
    developer's ``~/.gitpr/langs`` happens to hold. A test that wants another
    language patches ``src.i18n`` itself, which wins over this.
    """
    import src.i18n

    monkeypatch.setattr(src.i18n, "CURRENT_LANG", "en_us")
    monkeypatch.setattr(src.i18n, "TRANSLATIONS", {})
