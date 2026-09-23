"""Unit tests for the release flow orchestration (engine, git mocked)."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.changelog_builder import ChangeCategory
from src.i18n import CURRENT_LANG, set_lang
from src.release_engine import (
    ReleaseNotesError,
    _LOG_FORMAT,
    _LOG_SEP_FIELD,
    _ask_about_suggested_version,
    _resolve_contributor_logins,
    _stdin_is_interactive,
    generate_release_notes,
    publish_release,
    result_to_json,
    upsert_changelog,
)

_REPO_ROOT = "C:/fake/repo"
_ORIGIN = "https://github.com/o/r.git"

# The engine's own log format, so a format change can never desync the mocks.
_LOG_ARGS = ("log", "--no-merges", f"--pretty=format:{_LOG_FORMAT}")


def _log_record(sha, subject, date="2026-09-01T10:00:00+00:00", author="Ada",
                email="ada@x.com"):
    """One ``git log`` record in the engine's field-separated shape."""
    return f"\x1e{sha}\x1f{author}\x1f{email}\x1f{date}\x1f{subject}\x1f"


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

    def setUp(self):
        """Keeps the contributor lookup offline for every engine test.

        In production it reads ``~/.gitpr/cache/contributors.json`` and, for the
        addresses it has never seen, calls the forge API. A unit test must do
        neither, so the map starts empty here; the resolution itself is covered
        by TestContributorLogins.
        """
        patcher = patch("src.release_engine._resolve_contributor_logins", return_value={})
        self.addCleanup(patcher.stop)
        self.resolve_logins = patcher.start()

    def _base_script(self, extra=None):
        script = {
            ("rev-parse", "--show-toplevel"): (0, _REPO_ROOT + "\n"),
            ("remote", "get-url", "origin"): (0, _ORIGIN + "\n"),
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


class TestChangelogRange(EngineTestCase):
    """The previous changelog section bounds the range and filters the commits.

    This is the fix for the repetition: a release used to list every commit of
    every previous release because the range came from ``git describe``, which
    only sees tags reachable from HEAD (v0.0.8 here, not v1.2.0).
    """

    OLDEST = "2" * 40  # shipped in 1.1.0
    NEWEST = "1" * 40  # shipped in 1.2.0 — the tip of the last release
    FRESH = "a" * 40  # the only commit of the release being generated

    def _changelog(self, tmp, body):
        """Writes a changelog and returns its absolute path."""
        path = os.path.abspath(os.path.join(tmp, "CHANGELOG.md"))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        return path

    def _section(self):
        """A hand-written previous section: two bullets, no tag behind them."""
        return (
            "# Changelog\n\n## [1.2.0] - 2026-09-07\n\n"
            "### ✨ Features\n"
            "- shipped second ([1111111](https://github.com/o/r/commit/" + self.NEWEST + "))\n"
            "- shipped first ([2222222](https://github.com/o/r/commit/" + self.OLDEST + "))\n"
        )

    def _no_walk_key(self):
        return (
            "log",
            "--no-walk",
            f"--pretty=format:%H{_LOG_SEP_FIELD}%at",
            "1111111",
            "2222222",
        )

    def test_anchor_is_the_newest_hash_of_the_previous_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            changelog = self._changelog(tmp, self._section())
            script = self._base_script(
                {
                    # Deliberately out of file order: the date decides, not the line.
                    self._no_walk_key(): (
                        0,
                        f"{self.NEWEST}\x1f1600000000\n{self.OLDEST}\x1f1700000000",
                    ),
                    ("merge-base", "--is-ancestor", self.OLDEST, "HEAD"): (0, ""),
                    _LOG_ARGS + (self.OLDEST + "..HEAD",): (
                        0,
                        _log_record(self.FRESH, "feat: brand new thing"),
                    ),
                }
            )
            with patch("src.release_engine.subprocess.run",
                       side_effect=_fake_run(script)), \
                 patch("src.release_engine.click.secho"):
                result = generate_release_notes(
                    repo_path=".", target_version="1.3.0", ai_summary=False,
                    changelog_path=changelog,
                )
        self.assertEqual(result.previous_tag, self.OLDEST)
        self.assertEqual(result.previous_version, "1.2.0")
        self.assertIn("brand new thing", result.markdown)
        # Nothing that already shipped may show up again.
        self.assertNotIn("shipped second", result.markdown)
        self.assertNotIn("shipped first", result.markdown)

    def test_anchor_falls_back_to_the_section_version_tag(self):
        # Unknown hashes (rewritten history, another clone): the tag of the
        # section carries the anchor instead.
        with tempfile.TemporaryDirectory() as tmp:
            changelog = self._changelog(tmp, self._section())
            script = self._base_script(
                {
                    self._no_walk_key(): (128, ""),
                    ("rev-parse", "--verify", "--quiet", "1.2.0^{commit}"): (128, ""),
                    ("rev-parse", "--verify", "--quiet", "v1.2.0^{commit}"): (0, ""),
                    ("merge-base", "--is-ancestor", "v1.2.0", "HEAD"): (0, ""),
                    _LOG_ARGS + ("v1.2.0..HEAD",): (
                        0,
                        _log_record(self.FRESH, "feat: brand new thing"),
                    ),
                }
            )
            with patch("src.release_engine.subprocess.run",
                       side_effect=_fake_run(script)), \
                 patch("src.release_engine.click.secho"):
                result = generate_release_notes(
                    repo_path=".", target_version="1.3.0", ai_summary=False,
                    changelog_path=changelog,
                )
        self.assertEqual(result.previous_tag, "v1.2.0")

    def test_unanchorable_section_degrades_to_describe_with_a_warning(self):
        # A hand-written section with no hashes at all (the 0.0.x era).
        with tempfile.TemporaryDirectory() as tmp:
            changelog = self._changelog(
                tmp,
                "# Changelog\n\n## [1.2.0] - 2026-09-07\n\n### ✨ Features\n- shipped it\n",
            )
            script = self._base_script(
                {
                    ("rev-parse", "--verify", "--quiet", "1.2.0^{commit}"): (128, ""),
                    ("rev-parse", "--verify", "--quiet", "v1.2.0^{commit}"): (128, ""),
                    ("describe", "--tags", "--abbrev=0"): (0, "v0.0.8\n"),
                    _LOG_ARGS + ("v0.0.8..HEAD",): (
                        0,
                        _log_record(self.FRESH, "feat: brand new thing"),
                    ),
                }
            )
            with patch("src.release_engine.subprocess.run",
                       side_effect=_fake_run(script)), \
                 patch("src.release_engine.click.secho"):
                result = generate_release_notes(
                    repo_path=".", target_version="1.3.0", ai_summary=False,
                    changelog_path=changelog,
                )
        self.assertEqual(result.previous_tag, "v0.0.8")
        self.assertEqual(result.previous_version, "1.2.0")
        self.assertTrue(
            any("Could not locate the previous release" in w for w in result.warnings)
        )

    def test_first_release_without_a_changelog_warns_about_nothing(self):
        # No previous release to duplicate: the describe fallback stays silent.
        script = self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v0.0.8\n"),
                _LOG_ARGS + ("v0.0.8..HEAD",): (
                    0,
                    _log_record(self.FRESH, "feat: brand new thing"),
                ),
            }
        )
        with patch("src.release_engine.subprocess.run", side_effect=_fake_run(script)), \
             patch("src.release_engine.click.secho"):
            result = generate_release_notes(
                repo_path=".", target_version="1.0.0", ai_summary=False
            )
        self.assertEqual(result.previous_version, None)
        self.assertFalse(
            [w for w in result.warnings if "Could not locate" in w]
        )

    def test_commits_already_released_are_dropped(self):
        # --since wins over the changelog, but the filter still protects the
        # section from a range that reaches back into a released version.
        with tempfile.TemporaryDirectory() as tmp:
            changelog = self._changelog(tmp, self._section())
            script = self._base_script(
                {
                    ("rev-parse", "--verify", "--quiet", "v0.0.8^{commit}"): (0, ""),
                    _LOG_ARGS + ("v0.0.8..HEAD",): (
                        0,
                        _log_record(self.OLDEST, "feat: shipped second")
                        + _log_record(self.FRESH, "feat: brand new thing"),
                    ),
                }
            )
            with patch("src.release_engine.subprocess.run",
                       side_effect=_fake_run(script)), \
                 patch("src.release_engine.click.secho"):
                result = generate_release_notes(
                    repo_path=".", since_tag="v0.0.8", target_version="1.3.0",
                    ai_summary=False, changelog_path=changelog,
                )
        self.assertNotIn("shipped second", result.markdown)
        self.assertIn("brand new thing", result.markdown)
        self.assertTrue(
            any("1 commit(s) already released" in w for w in result.warnings)
        )

    def test_a_range_with_nothing_new_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            changelog = self._changelog(tmp, self._section())
            script = self._base_script(
                {
                    ("rev-parse", "--verify", "--quiet", "v0.0.8^{commit}"): (0, ""),
                    _LOG_ARGS + ("v0.0.8..HEAD",): (
                        0,
                        _log_record(self.OLDEST, "feat: shipped second"),
                    ),
                }
            )
            with patch("src.release_engine.subprocess.run",
                       side_effect=_fake_run(script)), \
                 patch("src.release_engine.click.secho"):
                with self.assertRaises(ReleaseNotesError) as ctx:
                    generate_release_notes(
                        repo_path=".", since_tag="v0.0.8", target_version="1.3.0",
                        ai_summary=False, changelog_path=changelog,
                    )
        self.assertIn("Nothing new to release", str(ctx.exception))

    def test_bump_baseline_comes_from_the_previous_section(self):
        # The real-repo bug: with the range anchored on v0.0.8 the suggestion
        # used to be v0.0.9 while the changelog was already at 1.2.0.
        with tempfile.TemporaryDirectory() as tmp:
            changelog = self._changelog(
                tmp,
                "# Changelog\n\n## [1.2.0] - 2026-09-07\n\n### ✨ Features\n- shipped it\n",
            )
            script = self._base_script(
                {
                    ("rev-parse", "--verify", "--quiet", "1.2.0^{commit}"): (128, ""),
                    ("rev-parse", "--verify", "--quiet", "v1.2.0^{commit}"): (128, ""),
                    ("describe", "--tags", "--abbrev=0"): (0, "v0.0.8\n"),
                    _LOG_ARGS + ("v0.0.8..HEAD",): (
                        0,
                        _log_record(self.FRESH, "feat: brand new thing"),
                    ),
                }
            )
            with patch("src.release_engine.subprocess.run",
                       side_effect=_fake_run(script)), \
                 patch("src.release_engine.click.secho"):
                result = generate_release_notes(
                    repo_path=".", ai_summary=False, changelog_path=changelog
                )
        self.assertEqual(result.version, "1.3.0")


class TestLinksInTheSection(EngineTestCase):
    """The section ships clickable hashes, pull requests and contributor names."""

    SQUASH_SUBJECT = "feat(linter): add bridges (#190)"

    def _script(self, subject=None):
        return self._base_script(
            {
                ("describe", "--tags", "--abbrev=0"): (0, "v1.2.3\n"),
                _LOG_ARGS + ("v1.2.3..HEAD",): (
                    0,
                    _log_record("a" * 40, subject or self.SQUASH_SUBJECT),
                ),
            }
        )

    def test_hash_scope_pull_request_and_date_are_rendered(self):
        # The subject keeps the "(#190)" tail the classifier also reads the PR
        # number from — the linked group after it is what makes it clickable.
        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script())), \
             patch("src.release_engine.click.secho"):
            result = generate_release_notes(
                repo_path=".", target_version="1.3.0", ai_summary=False
            )
        self.assertIn(
            "- add bridges (#190) ([aaaaaaa](https://github.com/o/r/commit/"
            + "a" * 40 + ")) — linter · [#190](https://github.com/o/r/pull/190)"
            " · 2026-09-01",
            result.markdown,
        )

    def test_contributors_link_to_their_profile(self):
        self.resolve_logins.return_value = {"ada@x.com": "ada"}
        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script("fix: repair"))), \
             patch("src.release_engine.click.secho"):
            result = generate_release_notes(
                repo_path=".", target_version="1.3.0", ai_summary=False
            )
        self.assertIn("**Contributors:** [@ada](https://github.com/ada)", result.markdown)

    def test_without_an_origin_remote_the_section_has_no_links(self):
        script = self._script()
        script[("remote", "get-url", "origin")] = (2, "")
        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(script)), \
             patch("src.release_engine.click.secho"):
            result = generate_release_notes(
                repo_path=".", target_version="1.3.0", ai_summary=False
            )
        self.assertIn(
            "- add bridges (#190) (aaaaaaa) — linter · #190 · 2026-09-01",
            result.markdown,
        )
        self.assertNotIn("https://github.com", result.markdown)


class TestContributorLogins(unittest.TestCase):
    """The best-effort e-mail -> login resolution and its on-disk cache."""

    def _commits(self, *emails):
        return [
            SimpleNamespace(
                author_email=email,
                author_name="Ada",
                hash=f"{index:040d}",
            )
            for index, email in enumerate(emails)
        ]

    def test_resolves_and_caches_the_logins(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = os.path.join(tmp, "contributors.json")
            provider = SimpleNamespace(email_to_handle=lambda email: "ada")
            with patch("src.release_engine._contributors_cache_path",
                       return_value=Path(cache)), \
                 patch("src.config.get_scm_settings", return_value={}), \
                 patch("src.infrastructure.scm.factory.resolve_scm_provider",
                       return_value=provider):
                logins = _resolve_contributor_logins(
                    self._commits("ada@x.com"), _ORIGIN
                )
                self.assertEqual(logins, {"ada@x.com": "ada"})
                with open(cache, "r", encoding="utf-8") as handle:
                    self.assertEqual(json.load(handle), {"ada@x.com": "ada"})
                # Second run: served from the cache, the forge is not asked again.
                provider.email_to_handle = lambda email: (_ for _ in ()).throw(
                    AssertionError("the cache should have answered")
                )
                self.assertEqual(
                    _resolve_contributor_logins(self._commits("ada@x.com"), _ORIGIN),
                    {"ada@x.com": "ada"},
                )

    def test_the_commit_lookup_wins_over_the_email_search(self):
        # The reliable path: GitHub sees the commit even when the address is
        # private and invisible to the `in:email` user search.
        seen = {}

        def commit_login(repo, sha):
            seen["repo"], seen["sha"] = repo, sha
            return "ada"

        provider = SimpleNamespace(
            get_commit_author_login=commit_login,
            parse_repo_ref=lambda remote: f"ref:{remote}",
            email_to_handle=lambda email: (_ for _ in ()).throw(
                AssertionError("the commit lookup should have answered")
            ),
        )
        with tempfile.TemporaryDirectory() as tmp, \
             patch("src.release_engine._contributors_cache_path",
                   return_value=Path(os.path.join(tmp, "contributors.json"))), \
             patch("src.config.get_scm_settings", return_value={}), \
             patch("src.infrastructure.scm.factory.resolve_scm_provider",
                   return_value=provider):
            logins = _resolve_contributor_logins(
                self._commits("ada@x.com"), _ORIGIN
            )
        self.assertEqual(logins, {"ada@x.com": "ada"})
        # Newest first: the first commit of the range is the one asked for.
        self.assertEqual(seen, {"repo": f"ref:{_ORIGIN}", "sha": "0" * 40})

    def test_the_email_search_covers_a_commit_the_forge_does_not_know(self):
        provider = SimpleNamespace(
            get_commit_author_login=lambda repo, sha: None,
            parse_repo_ref=lambda remote: remote,
            email_to_handle=lambda email: "ada",
        )
        with tempfile.TemporaryDirectory() as tmp, \
             patch("src.release_engine._contributors_cache_path",
                   return_value=Path(os.path.join(tmp, "contributors.json"))), \
             patch("src.config.get_scm_settings", return_value={}), \
             patch("src.infrastructure.scm.factory.resolve_scm_provider",
                   return_value=provider):
            logins = _resolve_contributor_logins(
                self._commits("ada@x.com"), _ORIGIN
            )
        self.assertEqual(logins, {"ada@x.com": "ada"})

    def test_cache_lookup_ignores_the_email_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = os.path.join(tmp, "contributors.json")
            with open(cache, "w", encoding="utf-8") as handle:
                json.dump({"ada@x.com": "ada"}, handle)
            with patch("src.release_engine._contributors_cache_path",
                       return_value=Path(cache)):
                logins = _resolve_contributor_logins(
                    self._commits("ADA@X.com"), _ORIGIN
                )
        self.assertEqual(logins, {"ada@x.com": "ada"})

    def test_a_failed_lookup_is_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = os.path.join(tmp, "contributors.json")
            provider = SimpleNamespace(email_to_handle=lambda email: None)
            with patch("src.release_engine._contributors_cache_path",
                       return_value=Path(cache)), \
                 patch("src.config.get_scm_settings", return_value={}), \
                 patch("src.infrastructure.scm.factory.resolve_scm_provider",
                       return_value=provider):
                self.assertEqual(
                    _resolve_contributor_logins(self._commits("ada@x.com"), _ORIGIN),
                    {},
                )
                self.assertFalse(os.path.exists(cache))

    def test_an_unusable_provider_never_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("src.release_engine._contributors_cache_path",
                       return_value=Path(os.path.join(tmp, "contributors.json"))), \
                 patch("src.infrastructure.scm.factory.resolve_scm_provider",
                       side_effect=RuntimeError("no token")):
                self.assertEqual(
                    _resolve_contributor_logins(self._commits("ada@x.com"), _ORIGIN),
                    {},
                )

    def test_a_remote_the_provider_cannot_parse_never_raises(self):
        # parse_repo_ref fails, the email search still answers.
        provider = SimpleNamespace(
            get_commit_author_login=lambda repo, sha: None,
            parse_repo_ref=lambda remote: (_ for _ in ()).throw(ValueError("nope")),
            email_to_handle=lambda email: "ada",
        )
        with tempfile.TemporaryDirectory() as tmp, \
             patch("src.release_engine._contributors_cache_path",
                   return_value=Path(os.path.join(tmp, "contributors.json"))), \
             patch("src.config.get_scm_settings", return_value={}), \
             patch("src.infrastructure.scm.factory.resolve_scm_provider",
                   return_value=provider):
            logins = _resolve_contributor_logins(
                self._commits("ada@x.com"), _ORIGIN
            )
        self.assertEqual(logins, {"ada@x.com": "ada"})

    def test_no_emails_means_no_lookup(self):
        with patch("src.config.get_scm_settings",
                   side_effect=AssertionError("no email, no provider call")):
            self.assertEqual(
                _resolve_contributor_logins(self._commits("", None), _ORIGIN), {}
            )


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

    def test_force_drops_the_whole_old_block_including_its_subsections(self):
        # The section ends at the next level-2 header: a "### Summary" of the
        # block being replaced must not survive above the new body, or the
        # regenerated version lists its own commits twice.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "CHANGELOG.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    "# Changelog\n\n"
                    "## [1.3.0] - 2026-09-07\n\n"
                    "### Summary\nOld summary.\n\n"
                    "### ✨ Features\n- stale bullet (aaaaaaa)\n\n"
                    "**Contributors:** Ada\n\n"
                    "## [1.2.0] - 2026-08-01\n\n### Summary\nOlder.\n"
                )
            upsert_changelog(path, "1.3.0", self._section("1.3.0"), force=True)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(content.startswith("# Changelog\n\n## [1.3.0]"))
            self.assertNotIn("Old summary.", content)
            self.assertNotIn("stale bullet", content)
            self.assertNotIn("**Contributors:** Ada", content)
            # The neighbouring block is untouched.
            self.assertIn("## [1.2.0] - 2026-08-01\n\n### Summary\nOlder.", content)
            self.assertEqual(content.count("## [1.3.0]"), 1)


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
            previous_version="1.1.0",
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

    def test_quiet_flag_reaches_the_ai_call(self):
        # Without it the spinner animates on stdout and breaks --format json.
        log_out = "\x1e" + "d" * 40 + "\x1fAda\x1fada@x.com\x1fd\x1ffeat: shiny thing\x1f"
        captured = {}

        def fake_ai(*args, **kwargs):
            captured.update(kwargs)
            return {"summary": "Shiny."}

        with patch("src.release_engine.subprocess.run",
                   side_effect=_fake_run(self._script(log_out))), \
             patch("src.release_engine.click.secho"), \
             patch("src.release_engine.get_ai_provider", return_value="gemini"), \
             patch("src.release_engine.get_api_key", return_value="key"), \
             patch("src.release_engine.get_api_model", return_value="gemini-x"), \
             patch("src.release_engine.get_cached_response", return_value=None), \
             patch("src.release_engine.save_cached_response"), \
             patch("src.release_engine.get_skill_context", return_value="Persona"), \
             patch("src.release_engine.call_ai_model", side_effect=fake_ai):
            generate_release_notes(repo_path=".", ai_summary=True, quiet=True)
        self.assertTrue(captured["quiet"])


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
