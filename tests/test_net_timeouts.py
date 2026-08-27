"""Unit tests for the network hardening: DNS-bounding and AI SDK timeouts.

Covers src/net.py (bounded_urlopen), the timeout getters in src/config.py, and
the fact that every AI SDK client is constructed with an explicit timeout.
"""
import threading
import unittest
from unittest.mock import patch, MagicMock


class TestBoundedUrlopen(unittest.TestCase):
    """Tests for the DNS-bounded fetch helper."""

    def test_returns_bytes_on_success(self):
        from src.net import bounded_urlopen

        response = MagicMock()
        response.read.return_value = b'{"ok": true}'
        response.__enter__ = lambda s: response
        response.__exit__ = lambda s, *a: False

        with patch("src.net.urllib.request.urlopen", return_value=response):
            self.assertEqual(bounded_urlopen("https://x/y"), b'{"ok": true}')

    def test_returns_none_on_request_error(self):
        from src.net import bounded_urlopen

        with patch("src.net.urllib.request.urlopen", side_effect=OSError("offline")):
            self.assertIsNone(bounded_urlopen("https://x/y"))

    def test_returns_none_when_resolver_stalls(self):
        """The whole point: a hung getaddrinfo() must not block the caller.

        urlopen is replaced by a call that blocks far past hard_timeout; the
        helper must give up and hand back None so the caller uses its fallback.
        """
        from src.net import bounded_urlopen

        release = threading.Event()

        def _stall(*args, **kwargs):
            release.wait(30)  # Simulates a stalled DNS resolution
            raise OSError("never reached in this test")

        try:
            with patch("src.net.urllib.request.urlopen", side_effect=_stall):
                self.assertIsNone(
                    bounded_urlopen("https://x/y", hard_timeout=0.2)
                )
        finally:
            release.set()  # Let the daemon thread unwind

    def test_does_not_block_longer_than_hard_timeout(self):
        from src.net import bounded_urlopen
        import time

        release = threading.Event()

        def _stall(*args, **kwargs):
            release.wait(30)
            raise OSError("never reached")

        try:
            with patch("src.net.urllib.request.urlopen", side_effect=_stall):
                started = time.perf_counter()
                bounded_urlopen("https://x/y", hard_timeout=0.2)
                elapsed = time.perf_counter() - started
        finally:
            release.set()

        self.assertLess(elapsed, 5, "bounded_urlopen exceeded its hard bound")

    def test_headers_are_forwarded(self):
        from src.net import bounded_urlopen

        response = MagicMock()
        response.read.return_value = b"x"
        response.__enter__ = lambda s: response
        response.__exit__ = lambda s, *a: False

        with patch("src.net.urllib.request.urlopen", return_value=response):
            with patch("src.net.urllib.request.Request") as mock_request:
                bounded_urlopen("https://x/y", headers={"User-Agent": "GitPR"})

        self.assertEqual(
            mock_request.call_args.kwargs["headers"], {"User-Agent": "GitPR"}
        )


class TestTimeoutConfig(unittest.TestCase):
    """Tests for the configurable timeout getters."""

    def test_ai_timeout_defaults_to_600(self):
        from src.config import get_ai_timeout

        with patch("src.config.load_dotenv"), patch(
            "src.config.os.getenv", return_value=None
        ):
            self.assertEqual(get_ai_timeout(), 600.0)

    def test_ai_timeout_reads_env(self):
        from src.config import get_ai_timeout

        with patch("src.config.load_dotenv"), patch(
            "src.config.os.getenv", return_value="42"
        ):
            self.assertEqual(get_ai_timeout(), 42.0)

    def test_invalid_ai_timeout_falls_back_to_default(self):
        from src.config import get_ai_timeout

        for junk in ("abc", "", "0", "-5"):
            with patch("src.config.load_dotenv"), patch(
                "src.config.os.getenv", return_value=junk
            ):
                self.assertEqual(
                    get_ai_timeout(), 600.0, f"{junk!r} should fall back"
                )

    def test_linter_timeout_defaults_to_120(self):
        from src.config import get_linter_timeout

        with patch("src.config.load_dotenv"), patch(
            "src.config.os.getenv", return_value=None
        ):
            self.assertEqual(get_linter_timeout(), 120.0)


class TestAiClientTimeouts(unittest.TestCase):
    """Every AI SDK client must be built with an explicit request timeout."""

    def test_gemini_client_gets_timeout_in_milliseconds(self):
        """google-genai expresses http_options.timeout in MILLISECONDS."""
        from src.ai_providers import _make_gemini_client

        with patch("src.ai_providers.genai.Client") as mock_client:
            _make_gemini_client("key", 600.0)

        self.assertEqual(
            mock_client.call_args.kwargs["http_options"], {"timeout": 600000}
        )

    def test_openai_client_gets_timeout_in_seconds(self):
        from src.ai_providers import _make_openai_client

        with patch("src.ai_providers.OpenAI") as mock_client:
            _make_openai_client("key", "deepseek", 600.0)

        self.assertEqual(mock_client.call_args.kwargs["timeout"], 600.0)
        self.assertEqual(
            mock_client.call_args.kwargs["base_url"], "https://api.deepseek.com"
        )

    def test_ollama_client_points_at_localhost(self):
        from src.ai_providers import _make_openai_client

        with patch("src.ai_providers.OpenAI") as mock_client:
            _make_openai_client("key", "ollama", 30.0)

        self.assertEqual(
            mock_client.call_args.kwargs["base_url"], "http://localhost:11434/v1"
        )
        self.assertEqual(mock_client.call_args.kwargs["timeout"], 30.0)


if __name__ == "__main__":
    unittest.main()
