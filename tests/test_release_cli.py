"""CLI tests for the ``gitpr release`` command surface (engine mocked).

Covers the R4/R5/R6 wiring added on top of the engine: first-use skill
auto-download (markdown only), the per-run artifact under
.gitpr/reports/release/, the exit-1 ordering when the changelog upsert
fails, and the stdout-only ``--format json`` contract.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from src.changelog_builder import ReleaseNotesResult
from src.i18n import CURRENT_LANG, set_lang
from src.main import cli
from src.release_engine import ReleaseNotesError


def _result(version="1.2.4", summary="Executive summary text."):
    """A real ReleaseNotesResult so result_to_json works in json mode."""
    return ReleaseNotesResult(
        version=version,
        previous_tag="v1.2.3",
        generated_at="2026-09-08T10:00:00",
        summary=summary,
        sections={},
        breaking_changes=[],
        contributors=["Ada"],
        markdown=f"## [{version}] - 2026-09-08\n\n### Summary\n{summary}\n",
    )


def _release_settings(changelog_path="CHANGELOG.md"):
    return {
        "changelog_path": changelog_path,
        "ai_summary": True,
        "auto_bump": True,
        "publish_draft_by_default": False,
    }


class ReleaseCliTestCase(unittest.TestCase):
    """Pins the interface language to English for deterministic assertions."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)


class TestReleaseMarkdownFlow(ReleaseCliTestCase):
    """R4 + R5: auto-download, changelog upsert and artifact persistence."""

    def test_auto_downloads_skill_and_saves_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = os.path.join(tmp, "main_20260908120000_RELEASE.md")
            with patch("src.config.get_release_settings",
                       return_value=_release_settings()), \
                 patch("src.main.ensure_release_skill_template") as ensure, \
                 patch("src.release_engine.generate_release_notes",
                       return_value=_result()) as engine, \
                 patch("src.release_engine.get_repo_root", return_value=tmp), \
                 patch("src.release_engine.upsert_changelog",
                       return_value="created") as upsert, \
                 patch("src.main.get_current_branch", return_value="main"), \
                 patch("src.main.resolve_output_path", return_value=artifact_path):
                runner = CliRunner()
                result = runner.invoke(cli, ["release"])

            self.assertEqual(result.exit_code, 0, result.output)
            ensure.assert_called_once()  # markdown mode triggers the download
            engine.assert_called_once()
            self.assertTrue(engine.call_args.kwargs["ask_version"])
            upsert.assert_called_once()
            self.assertEqual(upsert.call_args.args[0],
                             os.path.join(tmp, "CHANGELOG.md"))
            self.assertEqual(upsert.call_args.args[1], "1.2.4")
            # Artifact mirrors the generated markdown byte for byte.
            with open(artifact_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), _result().markdown)
            self.assertIn("Release notes artifact saved to", result.output)

    def test_upsert_failure_exits_1_before_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = os.path.join(tmp, "should_not_exist_RELEASE.md")
            with patch("src.config.get_release_settings",
                       return_value=_release_settings()), \
                 patch("src.main.ensure_release_skill_template"), \
                 patch("src.release_engine.generate_release_notes",
                       return_value=_result()), \
                 patch("src.release_engine.get_repo_root", return_value=tmp), \
                 patch("src.release_engine.upsert_changelog",
                       side_effect=ReleaseNotesError(
                           "Section for version 1.2.4 already has a section."
                       )), \
                 patch("src.main.get_current_branch", return_value="main"), \
                 patch("src.main.resolve_output_path", return_value=artifact_path):
                runner = CliRunner()
                result = runner.invoke(cli, ["release"])

            self.assertEqual(result.exit_code, 1)
            self.assertIn("already has a section", result.output)
            self.assertFalse(os.path.exists(artifact_path))


class TestReleaseJsonMode(ReleaseCliTestCase):
    """--format json is stdout-only: no download, no prompt, no file writes."""

    def test_json_mode_is_pure_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("src.config.get_release_settings",
                       return_value=_release_settings()), \
                 patch("src.main.ensure_release_skill_template") as ensure, \
                 patch("src.release_engine.generate_release_notes",
                       return_value=_result()) as engine, \
                 patch("src.release_engine.get_repo_root", return_value=tmp), \
                 patch("src.release_engine.upsert_changelog") as upsert, \
                 patch("src.main.resolve_output_path") as resolve:
                runner = CliRunner()
                result = runner.invoke(cli, ["release", "--format", "json"])

            self.assertEqual(result.exit_code, 0, result.output)
            payload = json.loads(result.output)
            self.assertEqual(payload["version"], "1.2.4")
            # The R4 hook and R6 prompt stay off in stdout-only mode.
            ensure.assert_not_called()
            self.assertFalse(engine.call_args.kwargs["ask_version"])
            self.assertTrue(engine.call_args.kwargs["quiet"])
            upsert.assert_not_called()
            resolve.assert_not_called()


class TestReleaseHelp(ReleaseCliTestCase):
    """``gitpr release -h`` routes to the release-notes documentation family."""

    def test_release_help_points_to_release_notes_docs(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["release", "-h"])

        self.assertEqual(result.exit_code, 0, result.output)
        # The epilog freezes at import under the machine locale, so only the
        # locale-independent docs URL fragment is asserted.
        self.assertIn("release-notes", result.output)


if __name__ == "__main__":
    unittest.main()
