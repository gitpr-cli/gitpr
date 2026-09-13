"""Validation tests for the configuration screen.

Two layers, tested separately because they fail differently:

  * config_schema.validate_field_value() — offline rules derived from the kind
    the field declares. These mirror the silent fallbacks in the read path.
  * config.validate_ai_key() — one network round trip that must distinguish a
    rejected credential from an unreachable provider, because only the former
    may block a save.

No test here touches the network: the provider SDKs are mocked.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.config import (
    VALIDATION_AUTH,
    VALIDATION_NETWORK,
    VALIDATION_OK,
    _is_auth_failure,
    validate_ai_key,
)
from src.config_schema import (
    KIND_BOOL,
    KIND_ENUM,
    KIND_INT,
    KIND_PATH,
    KIND_SECRET,
    KIND_STR,
    KIND_TEMPLATE,
    ConfigField,
    validate_field_value,
)


def make_field(kind, **overrides):
    """Builds a throwaway ConfigField — only the validation inputs matter."""
    defaults = dict(
        key="TEST_KEY",
        label="Test",
        description="Test",
        category="general",
        kind=kind,
        default="",
    )
    defaults.update(overrides)
    return ConfigField(**defaults)


class FakeProviderError(Exception):
    """Stands in for a provider SDK error carrying an HTTP status."""

    def __init__(self, message, code=None, status_code=None):
        super().__init__(message)
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class TestValidateFieldValueOffline(unittest.TestCase):
    def test_bool_accepts_every_literal_the_readers_agree_on(self):
        field = make_field(KIND_BOOL)
        for literal in ("true", "false", "1", "0", "yes", "no", "off", "y", "n"):
            with self.subTest(literal=literal):
                self.assertEqual(validate_field_value(field, literal), "")

    def test_bool_is_case_insensitive(self):
        field = make_field(KIND_BOOL)
        self.assertEqual(validate_field_value(field, "TRUE"), "")
        self.assertEqual(validate_field_value(field, "False"), "")

    def test_bool_rejects_an_ambiguous_literal(self):
        """"maybe" is read as false by main.py's _env_flag and as true by
        config.py's _env_bool_default_true — the exact class of silent
        divergence this screen exists to surface."""
        self.assertNotEqual(validate_field_value(make_field(KIND_BOOL), "maybe"), "")

    def test_bool_rejects_on_even_though_it_looks_like_off(self):
        """"on" is the trap in plain sight: _env_flag() does not list it as
        true, while _env_bool_default_true() does not list it as false. The
        reader decides, so a GITPR_AUTO_STAGE=on would mean "false" in main.py
        and "true" in config.py."""
        self.assertNotEqual(validate_field_value(make_field(KIND_BOOL), "on"), "")
        # ...while "off" is unambiguous: false to both readers.
        self.assertEqual(validate_field_value(make_field(KIND_BOOL), "off"), "")

    def test_int_accepts_a_positive_number(self):
        self.assertEqual(validate_field_value(make_field(KIND_INT), "180"), "")

    def test_int_rejects_text(self):
        """_positive_float() swallows this and silently returns the default."""
        self.assertNotEqual(validate_field_value(make_field(KIND_INT), "abc"), "")

    def test_int_rejects_zero_and_negatives(self):
        field = make_field(KIND_INT)
        self.assertNotEqual(validate_field_value(field, "0"), "")
        self.assertNotEqual(validate_field_value(field, "-5"), "")

    def test_int_rejects_a_float_literal(self):
        self.assertNotEqual(validate_field_value(make_field(KIND_INT), "1.5"), "")

    def test_enum_accepts_a_declared_choice(self):
        field = make_field(KIND_ENUM, choices=("gemini", "deepseek"))
        self.assertEqual(validate_field_value(field, "gemini"), "")

    def test_enum_rejects_an_undeclared_choice(self):
        field = make_field(KIND_ENUM, choices=("gemini", "deepseek"))
        self.assertNotEqual(validate_field_value(field, "gpt"), "")

    def test_enum_accepts_the_empty_choice_when_declared(self):
        """An empty choice means "auto-detect" and must stay selectable."""
        field = make_field(KIND_ENUM, choices=("", "github", "gitlab"))
        self.assertEqual(validate_field_value(field, ""), "")

    def test_template_accepts_the_declared_defaults(self):
        for pattern in (
            "{branch}_{datetime}_PR_DESC.md",
            "{branch}_{datetime}_ISSUE.md",
            "{datetime}.md",
        ):
            with self.subTest(pattern=pattern):
                self.assertEqual(
                    validate_field_value(make_field(KIND_TEMPLATE), pattern), ""
                )

    def test_template_rejects_an_unknown_placeholder(self):
        """resolve_output_path() calls .format(branch=, datetime=) — anything
        else is a KeyError on the next command run."""
        error = validate_field_value(make_field(KIND_TEMPLATE), "{foo}.md")
        self.assertNotEqual(error, "")
        self.assertIn("foo", error)

    def test_template_requires_datetime(self):
        """Without {datetime} every run resolves to the same filename and
        silently overwrites the previous report."""
        self.assertNotEqual(
            validate_field_value(make_field(KIND_TEMPLATE), "{branch}_PR.md"), ""
        )

    def test_template_rejects_a_malformed_pattern(self):
        self.assertNotEqual(
            validate_field_value(make_field(KIND_TEMPLATE), "{branch"), ""
        )

    def test_template_error_names_only_the_offending_placeholders(self):
        error = validate_field_value(
            make_field(KIND_TEMPLATE), "{foo}_{bar}_{datetime}.md"
        )
        self.assertIn("bar", error)
        self.assertIn("foo", error)

    def test_template_accepts_a_path_with_directories(self):
        self.assertEqual(
            validate_field_value(
                make_field(KIND_TEMPLATE), "reports/{branch}_{datetime}.md"
            ),
            "",
        )

    def test_free_text_kinds_accept_anything(self):
        for kind in (KIND_STR, KIND_PATH, KIND_SECRET):
            with self.subTest(kind=kind):
                self.assertEqual(validate_field_value(make_field(kind), "any value"), "")

    def test_empty_value_is_allowed_for_free_text_kinds(self):
        """Emptying a field is how the screen clears an override."""
        for kind in (KIND_STR, KIND_PATH, KIND_SECRET):
            with self.subTest(kind=kind):
                self.assertEqual(validate_field_value(make_field(kind), ""), "")

    def test_surrounding_whitespace_is_ignored(self):
        self.assertEqual(validate_field_value(make_field(KIND_BOOL), "  true  "), "")
        self.assertEqual(validate_field_value(make_field(KIND_INT), " 180 "), "")

    def test_secret_kinds_are_not_validated_offline(self):
        """A secret is validated by a network probe, never by shape: the screen
        must not pretend to know what a valid token looks like."""
        field = make_field(KIND_SECRET, validator="ai_key")
        self.assertEqual(validate_field_value(field, "x"), "")


class TestIsAuthFailure(unittest.TestCase):
    def test_401_and_403_are_auth_failures(self):
        self.assertTrue(_is_auth_failure(FakeProviderError("nope", code=401)))
        self.assertTrue(_is_auth_failure(FakeProviderError("nope", status_code=403)))

    def test_unauthorized_message_without_a_status_is_auth(self):
        self.assertTrue(_is_auth_failure(FakeProviderError("Unauthorized")))

    def test_gemini_bad_key_is_recognised_despite_http_400(self):
        """Gemini answers 400 "API key not valid" for a malformed key."""
        self.assertTrue(
            _is_auth_failure(
                FakeProviderError("API key not valid. Please pass a valid API key.", code=400)
            )
        )

    def test_nested_response_status_is_read(self):
        exc = FakeProviderError("boom")
        exc.response = MagicMock(status_code=401)
        self.assertTrue(_is_auth_failure(exc))

    def test_a_connection_error_is_not_auth(self):
        self.assertFalse(_is_auth_failure(ConnectionError("network is unreachable")))

    def test_an_unrecognised_error_defaults_to_not_auth(self):
        """The asymmetry is deliberate: a false positive would block a valid
        key, so anything unclear is treated as a network problem."""
        self.assertFalse(_is_auth_failure(FakeProviderError("something odd", code=500)))
        self.assertFalse(_is_auth_failure(ValueError("unexpected")))


class TestValidateAiKey(unittest.TestCase):
    def test_ollama_needs_no_credential_and_no_network(self):
        with patch("src.ai_providers._make_gemini_client") as gemini:
            self.assertEqual(
                validate_ai_key("ollama", "ollama-local"), (True, VALIDATION_OK, "")
            )
        gemini.assert_not_called()

    def test_empty_key_is_rejected_without_a_network_call(self):
        with patch("src.ai_providers._make_gemini_client") as gemini:
            is_valid, kind, message = validate_ai_key("gemini", "")
        self.assertFalse(is_valid)
        self.assertEqual(kind, VALIDATION_AUTH)
        self.assertTrue(message)
        gemini.assert_not_called()

    def test_provider_name_is_case_insensitive(self):
        with patch("src.ai_providers._make_gemini_client") as factory:
            factory.return_value.models.list.return_value = []
            self.assertEqual(
                validate_ai_key("Gemini", "k")[0:2], (True, VALIDATION_OK)
            )
        factory.assert_called_once()

    def test_an_accepted_gemini_key_is_valid(self):
        with patch("src.ai_providers._make_gemini_client") as factory:
            factory.return_value.models.list.return_value = [MagicMock()]
            self.assertEqual(
                validate_ai_key("gemini", "good-key"), (True, VALIDATION_OK, "")
            )

    def test_a_rejected_gemini_key_reports_auth(self):
        with patch("src.ai_providers._make_gemini_client") as factory:
            factory.return_value.models.list.side_effect = FakeProviderError(
                "API key not valid", code=400
            )
            is_valid, kind, _ = validate_ai_key("gemini", "bad-key")
        self.assertFalse(is_valid)
        self.assertEqual(kind, VALIDATION_AUTH)

    def test_an_unreachable_gemini_reports_network(self):
        """Decision 14: a network failure must NOT block the save, otherwise a
        correct key typed behind a proxy could never be stored."""
        with patch("src.ai_providers._make_gemini_client") as factory:
            factory.return_value.models.list.side_effect = ConnectionError("no route")
            is_valid, kind, _ = validate_ai_key("gemini", "good-key")
        self.assertFalse(is_valid)
        self.assertEqual(kind, VALIDATION_NETWORK)

    def test_a_gemini_timeout_reports_network(self):
        with patch("src.ai_providers._make_gemini_client") as factory:
            factory.return_value.models.list.side_effect = TimeoutError("timed out")
            self.assertEqual(validate_ai_key("gemini", "k")[1], VALIDATION_NETWORK)

    def test_deepseek_uses_the_openai_client(self):
        with patch("src.ai_providers._make_openai_client") as factory:
            factory.return_value.models.list.return_value = []
            self.assertEqual(
                validate_ai_key("deepseek", "good-key"), (True, VALIDATION_OK, "")
            )
        self.assertEqual(factory.call_args[0][1], "deepseek")

    def test_a_rejected_deepseek_key_reports_auth(self):
        with patch("src.ai_providers._make_openai_client") as factory:
            factory.return_value.models.list.side_effect = FakeProviderError(
                "Unauthorized", status_code=401
            )
            is_valid, kind, _ = validate_ai_key("deepseek", "bad-key")
        self.assertFalse(is_valid)
        self.assertEqual(kind, VALIDATION_AUTH)

    def test_an_unreachable_deepseek_reports_network(self):
        with patch("src.ai_providers._make_openai_client") as factory:
            factory.return_value.models.list.side_effect = ConnectionError("no route")
            self.assertEqual(validate_ai_key("deepseek", "k")[1], VALIDATION_NETWORK)

    def test_an_unknown_provider_is_left_alone(self):
        """Nothing meaningful can be probed, so the screen must not block."""
        self.assertEqual(validate_ai_key("mystery", "k"), (True, VALIDATION_OK, ""))

    def test_the_probe_uses_the_short_validation_timeout(self):
        """GITPR_AI_TIMEOUT defaults to 180s — reusing it would freeze the
        screen for three minutes on an unreachable provider."""
        from src.config import _AI_KEY_VALIDATION_TIMEOUT

        with patch("src.ai_providers._make_gemini_client") as factory:
            factory.return_value.models.list.return_value = []
            validate_ai_key("gemini", "k")
        self.assertEqual(factory.call_args[0][1], _AI_KEY_VALIDATION_TIMEOUT)
        self.assertLess(_AI_KEY_VALIDATION_TIMEOUT, 30)

    def test_the_probe_never_generates_content(self):
        """call_ai_model() swallows every exception, retries three times and
        sleeps 2s between attempts — it can never tell 401 from a dead network."""
        with patch("src.ai_providers._make_gemini_client") as factory, patch(
            "src.ai_providers.call_ai_model"
        ) as generate:
            factory.return_value.models.list.return_value = []
            validate_ai_key("gemini", "k")
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
