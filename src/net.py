"""Outbound network helpers with a hard wall-clock bound.

urllib's ``timeout`` argument bounds socket operations but NOT DNS
resolution: on Windows a stalled resolver can block ``getaddrinfo()``
for minutes, freezing the CLI before a single byte is sent.  The pattern
used across GitPR ("DNS-bounding") is therefore to run the request on a
daemon thread and abandon it after ``hard_timeout`` seconds, letting the
caller fall back to its offline copy.

This module is intentionally dependency-free: ``src.i18n`` imports it, so
it must never import back into the GitPR package.
"""

import threading
import urllib.request

# Wall-clock ceiling for a single fetch, DNS resolution included.
DEFAULT_HARD_TIMEOUT = 10.0


def bounded_urlopen(url, timeout=3, hard_timeout=DEFAULT_HARD_TIMEOUT, headers=None):
    """Fetch *url* and return its raw bytes, or None on any failure.

    *timeout* bounds the socket once connected; *hard_timeout* bounds the
    whole call including name resolution.  Returns None when the worker is
    still alive after *hard_timeout* (stalled DNS), when the request raised,
    so every caller treats "no data" as "use the offline fallback".
    """
    result = {}

    def _fetch():
        try:
            request = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                result["data"] = response.read()
        except Exception as exc:
            result["error"] = exc

    fetcher = threading.Thread(target=_fetch, daemon=True)
    fetcher.start()
    fetcher.join(hard_timeout)

    if fetcher.is_alive() or "error" in result:
        return None  # Stalled DNS or failed request — caller uses its fallback
    return result.get("data")
