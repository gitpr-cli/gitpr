"""Unit tests for the release flow orchestration (engine, git mocked)."""

import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.changelog_builder import ChangeCategory
from src.i18n import CURRENT_LANG, set_lang
from src.release_engine import (
    ReleaseNotesError,
    _ask_about_suggested_version,
    _stdin_is_interactive,
    generate_release_notes,
    publish_release,
    result_to_json,
    upsert_changelog,
)

_REPO_ROOT = "C:/fake/repo"


def _fake_run(script):
    """Builds a subprocess.run mock whose stdout depends on the git args.

    ``script`` maps a tuple of git args (after ``-C <root>``) to a
    (returncode, stdout) pair.
    """

    def fake_run(cmd, capture_output=None, text=None, encoding=None,
                 errors=None, check=None):
        key = tuple(cmd[3:])
        if key not in script:
            raise AssertionError(f"Unexpected git command: {cmd}")
        rc, stdout = script[key]
        return SimpleNamespace(returncode=rc, stdout=stdout, stderr="")

    return fake_run


def _raw_commit(subject, hash_="bbbbbbb1", body=""):
    """One raw-commit dict shaped like the engine's git log parsing output."""
    return {
        "hash": hash_ * 5,
        "short_hash": hash_[:7],
        "author_name": "Ada Lovelace",
        "author_email": "ada@example.com",
        "date": "2026-09-01T10:00:00+00:00",
        "subject": subject,
        "body": body,
    }


class EngineTestCase(unittest.TestCase):
    """Pins the interface language to English for deterministic assertions."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)

    def _base_script(self, extra=None):
        script = {
            ("rev-parse", "--show-toplevel"): (0, _REPO_ROOT + "\n"),
        }
        if extra:
            script.update(extra)
        return script


class TestGenerateReleaseNotes(EngineTestCase):
    def test_first_release_with_explicit_version(self):
        # No tags at all -> whole-history log; --version supplied by the user.
        script = self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (128, ""),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "HEAD",
                ): (0, "\x1e" + "a" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1ffeat: hello\x1f"),
            }
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value=None), \
             patch("src.release_engine.click.secho"):
            result = generate_release_notes(
                repo_path=".", target_version="1.0.0", ai_summary=True
            )
        self.assertEqual(result.version, "1.0.0")
        self.assertIsNone(result.previous_tag)  # first release
        self.assertEqual(result.sections[ChangeCategory.FEATURE][0].subject, "hello")
        self.assertIn("## [1.0.0] -", result.markdown)
        self.assertTrue(any("no API key" in w for w in result.warnings))

    def test_first_release_without_version_asks_for_it(self):
        script = self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (128, ""),
                ("tag", "--merged", "HEAD"): (0, ""),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "HEAD",
                ): (0, "\x1e" + "a" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1ffeat: hello\x1f"),
            }
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value=None):
            with self.assertRaises(ReleaseNotesError):
                generate_release_notes(repo_path=".", ai_summary=True)

    def test_default_since_and_auto_bump_to_patch(self):
        # describe finds v1.2.3; only fixes in the range -> suggested v1.2.4.
        log_out = "\x1e" + "c" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1ffix: repair widget\x1f"
        script = self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v1.2.3\n"),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "v1.2.3..HEAD",
                ): (0, log_out),
            }
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value="key"):
            result = generate_release_notes(repo_path=".", ai_summary=False)
        self.assertEqual(result.version, "v1.2.4")
        self.assertEqual(result.previous_tag, "v1.2.3")

    def test_invalid_explicit_since_reference(self):
        script = self._base_script(
            {("rev-parse", "--verify", "--quiet", "nope^{commit}"): (128, "")}
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)):
            with self.assertRaises(ReleaseNotesError) as ctx:
                generate_release_notes(repo_path=".", since_tag="nope")
        self.assertIn("not found", str(ctx.exception))

    def test_empty_range_raises(self):
        script = self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v1.0.0\n"),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "v1.0.0..HEAD",
                ): (0, ""),
            }
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)):
            with self.assertRaises(ReleaseNotesError):
                generate_release_notes(repo_path=".", ai_summary=False)

    def test_ai_summary_used_and_cached(self):
        log_out = "\x1e" + "d" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1ffeat: shiny thing\x1f"
        script = self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v1.2.3\n"),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "v1.2.3..HEAD",
                ): (0, log_out),
            }
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value="key"), \
             patch("src.release_engine.get_api_model", return_value="gemini-x"), \
             patch("src.release_engine.get_cached_response", return_value=None), \
             patch("src.release_engine.save_cached_response") as save_mock, \
             patch("src.release_engine.call_ai_model",
                   return_value={"summary": "The shiny thing now shines."}):
            result = generate_release_notes(repo_path=".", ai_summary=True)
        self.assertEqual(result.summary, "The shiny thing now shines.")
        self.assertIn("The shiny thing now shines.", result.markdown)
        save_mock.assert_called_once()

    def test_ai_failure_degrades_with_warning(self):
        log_out = "\x1e" + "d" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1ffeat: shiny thing\x1f"
        script = self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v1.2.3\n"),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "v1.2.3..HEAD",
                ): (0, log_out),
            }
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value="key"), \
             patch("src.release_engine.get_cached_response", return_value=None), \
             patch("src.release_engine.call_ai_model", return_value=None):
            result = generate_release_notes(repo_path=".", ai_summary=True)
        self.assertEqual(result.summary, "")
        self.assertNotIn("### Summary", result.markdown)
        self.assertTrue(any("AI summary failed" in w for w in result.warnings))

    def test_non_conventional_commits_warned_not_failed(self):
        log_out = (
            "\x1e" + "e" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1frandom prose\x1f"
            + "\x1e" + "f" * 40 + "\x1fBob\x1fbob@x.com\x1fd\x1ffix: ok\x1f"
        )
        script = self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v1.2.3\n"),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "v1.2.3..HEAD",
                ): (0, log_out),
            }
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value=None):
            result = generate_release_notes(repo_path=".", ai_summary=False)
        self.assertEqual(result.version, "v1.2.4")
        self.assertTrue(any("1 commit(s) without Conventional Commits" in w for w in result.warnings))
        self.assertIn("random prose", result.markdown)


class TestUpsertChangelog(EngineTestCase):
    def _section(self, version="1.2.0"):
        return f"## [{version}] - 2026-09-07\n\n### Summary\nHi\n"

    def test_creates_file_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "CHANGELOG.md")
            status = upsert_changelog(path, "1.2.0", self._section())
            self.assertEqual(status, "created")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content.strip(), self._section().strip())

    def test_keeps_h1_title_on_top(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "CHANGELOG.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Changelog\n\n## [1.1.0] - 2026-08-01\n\nOld stuff\n")
            upsert_changelog(path, "1.2.0", self._section())
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(content.startswith("# Changelog\n\n## [1.2.0]"))
            self.assertLess(content.index("[1.2.0]"), content.index("[1.1.0]"))

    def test_duplicate_version_aborts_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "CHANGELOG.md")
            upsert_changelog(path, "1.2.0", self._section())
            with self.assertRaises(ReleaseNotesError) as ctx:
                upsert_changelog(path, "1.2.0", self._section("1.2.0"))
            self.assertIn("already has a section", str(ctx.exception))
            with open(path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read().count("## [1.2.0]"), 1)

    def test_force_replaces_only_the_version_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "CHANGELOG.md")
            upsert_changelog(path, "1.2.0", self._section())
            upsert_changelog(path, "1.3.0", self._section("1.3.0"))
            status = upsert_changelog(path, "1.2.0", self._section() + "RENEWED\n", force=True)
            self.assertEqual(status, "replaced")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("RENEWED", content)
            self.assertIn("## [1.3.0]", content)
            self.assertEqual(content.count("## [1.2.0]"), 1)
            # Regenerating 1.2.0 moves it back to the top (newest first).
            self.assertLess(content.index("RENEWED"), content.index("[1.3.0]"))


class TestPublishRelease(EngineTestCase):
    def _result(self, version="1.2.0"):
        with patch("src.release_engine.subprocess.run"), \
             patch("src.release_engine.click.secho"):
            return generate_release_notes(repo_path=".", target_version=version,
                                          ai_summary=False)

    def test_provider_create_release_called(self):
        provider = SimpleNamespace(name="github", create_release=lambda *a, **k: "https://url")
        with patch("src.release_engine.generate_release_notes") as gen, \
             patch("src.release_engine.click.secho"):
            gen.return_value = SimpleNamespace(version="1.2.0", markdown="## [1.2.0] - x\nBody\n")
            repo = SimpleNamespace(display="me/repo")
            url = publish_release(gen.return_value, provider, repo, draft=False)
        self.assertEqual(url, "https://url")
        # Assert through a spy instead of the lambda:
        provider = unittest.mock.MagicMock(name="github")
        with patch("src.release_engine.click.secho"):
            publish_release(
                SimpleNamespace(version="1.2.0", markdown="## [1.2.0] - x\nBody text\n"),
                provider,
                SimpleNamespace(),
            )
        provider.create_release.assert_called_once()
        call = provider.create_release.call_args
        self.assertEqual(call.kwargs["tag"], "1.2.0")
        self.assertEqual(call.kwargs["body"], "Body text")
        self.assertFalse(call.kwargs["draft"])

    def test_gitlab_draft_warns_and_publishes_direct(self):
        provider = unittest.mock.MagicMock()
        provider.name = "gitlab"  # MagicMock(name=...) only drives repr, not .name
        with patch("src.release_engine.click.secho"):
            publish_release(
                SimpleNamespace(version="1.2.0", markdown="## [1.2.0] - x\nBody\n"),
                provider,
                SimpleNamespace(),
                draft=True,
            )
        self.assertFalse(provider.create_release.call_args.kwargs["draft"])

    def test_result_to_json_roundtrip(self):
        from src.changelog_builder import ReleaseNotesResult

        result = ReleaseNotesResult(
            version="1.2.0",
            previous_tag="v1.1.0",
            generated_at="2026-09-07T00:00:00",
            summary="",
            sections={},
            breaking_changes=[],
            contributors=["Ada"],
            markdown="",
        )
        data = result_to_json(result)
        self.assertEqual(json.loads(json.dumps(data))["version"], "1.2.0")


class TestSkillAsSystemInstruction(EngineTestCase):
    """R3: the user's .gitpr.release.md drives the executive summary persona."""

    def _script(self, log_out):
        return self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v1.2.3\n"),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "v1.2.3..HEAD",
                ): (0, log_out),
            }
        )

    def _generate_with_skill(self, skill_content, quiet=False):
        """Runs the AI path, capturing the system_instruction actually sent."""
        log_out = "\x1e" + "d" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1ffeat: shiny thing\x1f"
        captured = {}

        def fake_ai(*args, **kwargs):
            # call_ai_model(provider, api_key, api_model, prompt, system_instruction, ...)
            captured["system_instruction"] = args[4]
            return {"summary": "The shiny thing now shines."}

        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script(log_out))), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value="key"), \
             patch("src.release_engine.get_api_model", return_value="gemini-x"), \
             patch("src.release_engine.get_cached_response", return_value=None), \
             patch("src.release_engine.save_cached_response"), \
             patch("src.release_engine.get_skill_context",
                   return_value=skill_content) as skill_mock, \
             patch("src.release_engine.call_ai_model", side_effect=fake_ai):
            result = generate_release_notes(
                repo_path=".", ai_summary=True, quiet=quiet
            )
        return result, captured, skill_mock

    def test_skill_content_is_the_system_instruction(self):
        result, captured, skill_mock = self._generate_with_skill(
            "You are MY custom release persona."
        )
        self.assertEqual(
            captured["system_instruction"], "You are MY custom release persona."
        )
        self.assertEqual(result.summary, "The shiny thing now shines.")
        skill_mock.assert_called_once_with("release", quiet=False)

    def test_empty_skill_falls_back_to_builtin_persona(self):
        _, captured, _ = self._generate_with_skill("")
        self.assertIn("Release Manager", captured["system_instruction"])

    def test_quiet_flag_propagates_to_skill_loading(self):
        _, _, skill_mock = self._generate_with_skill("Persona", quiet=True)
        skill_mock.assert_called_once_with("release", quiet=True)


class TestAskVersionPrompt(EngineTestCase):
    """R6: the interactive confirmation around the automatic version bump."""

    def _script(self):
        log_out = "\x1e" + "c" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1ffix: repair widget\x1f"
        return self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v1.2.3\n"),
                (
                    "log",
                    "--no-merges",
                    "--pretty=format:%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b",
                    "v1.2.3..HEAD",
                ): (0, log_out),
            }
        )

    def test_accepts_suggestion_when_interactive(self):
        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script())), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value=None), \
             patch("src.release_engine._stdin_is_interactive", return_value=True), \
             patch("src.release_engine._ask_about_suggested_version",
                   return_value="v1.2.4") as ask:
            result = generate_release_notes(
                repo_path=".", ai_summary=False, ask_version=True
            )
        self.assertEqual(result.version, "v1.2.4")
        ask.assert_called_once_with("v1.2.4")

    def test_user_typed_version_overrides_suggestion(self):
        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script())), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value=None), \
             patch("src.release_engine._stdin_is_interactive", return_value=True), \
             patch("src.release_engine._ask_about_suggested_version",
                   return_value="v2.0.0") as ask:
            result = generate_release_notes(
                repo_path=".", ai_summary=False, ask_version=True
            )
        self.assertEqual(result.version, "v2.0.0")

    def test_no_prompt_when_stdin_is_not_a_tty(self):
        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script())), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value=None), \
             patch("src.release_engine._stdin_is_interactive", return_value=False), \
             patch("src.release_engine._ask_about_suggested_version") as ask:
            result = generate_release_notes(
                repo_path=".", ai_summary=False, ask_version=True
            )
        self.assertEqual(result.version, "v1.2.4")
        ask.assert_not_called()

    def test_default_ask_version_false_never_interacts(self):
        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script())), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value=None), \
             patch("src.release_engine._stdin_is_interactive") as tty, \
             patch("src.release_engine._ask_about_suggested_version") as ask:
            result = generate_release_notes(repo_path=".", ai_summary=False)
        self.assertEqual(result.version, "v1.2.4")
        tty.assert_not_called()
        ask.assert_not_called()

    def test_quiet_mode_suppresses_the_prompt(self):
        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script())), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value=None), \
             patch("src.release_engine._stdin_is_interactive", return_value=True), \
             patch("src.release_engine._ask_about_suggested_version") as ask:
            result = generate_release_notes(
                repo_path=".", ai_summary=False, ask_version=True, quiet=True
            )
        self.assertEqual(result.version, "v1.2.4")
        ask.assert_not_called()

    def test_ask_helper_accepts_by_default(self):
        with patch("src.release_engine.click.confirm", return_value=True) as confirm, \
             patch("src.release_engine.click.prompt") as prompt:
            self.assertEqual(_ask_about_suggested_version("v1.2.4"), "v1.2.4")
        confirm.assert_called_once()
        prompt.assert_not_called()

    def test_ask_helper_loops_until_valid_semver(self):
        with patch("src.release_engine.click.confirm", return_value=False), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.click.prompt",
                   side_effect=["not a version", "v2.0.0"]) as prompt:
            self.assertEqual(_ask_about_suggested_version("v1.2.4"), "v2.0.0")
        self.assertEqual(prompt.call_count, 2)

    def test_ask_helper_accepts_bare_semver(self):
        with patch("src.release_engine.click.confirm", return_value=False), \
             patch("src.release_engine.click.prompt", return_value="2.0.0") as prompt:
            self.assertEqual(_ask_about_suggested_version("v1.2.4"), "2.0.0")
        prompt.assert_called_once()

    def test_stdin_isatty_survey(self):
        with patch("sys.stdin") as fake_stdin:
            fake_stdin.isatty.return_value = True
            self.assertTrue(_stdin_is_interactive())
            fake_stdin.isatty.return_value = False
            self.assertFalse(_stdin_is_interactive())
            fake_stdin.isatty.side_effect = Exception("no tty")
            self.assertFalse(_stdin_is_interactive())


if __name__ == "__main__":
    unittest.main()
