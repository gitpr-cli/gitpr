"""Tests for the skill context loader (get_skill_context).

Covers the action -> file mapping (including the new ``release`` action),
the unknown-action fallback to the review file, and the ``quiet`` mode that
keeps terminal messages off stdout (mandatory for ``--format json``).
"""

import pytest

from src.config import SKILL_FILES_BY_TYPE, SKILL_TYPES, skill_file_for
from src.core import get_skill_context
from src.i18n import CURRENT_LANG, set_lang


class TestGetSkillContext:
    """get_skill_context resolves .gitpr.<type>.md under the project cwd."""

    @pytest.fixture(autouse=True)
    def _tmp_cwd(self, tmp_path, monkeypatch):
        """Redirect os.getcwd() so .gitpr/skill/ resolves under tmp_path."""
        monkeypatch.setattr("src.core.os.getcwd", lambda: str(tmp_path))
        monkeypatch.setattr("src.config.os.getcwd", lambda: str(tmp_path))

    @pytest.fixture(autouse=True)
    def _pin_english(self):
        """Pin the interface language so message assertions are deterministic."""
        previous = CURRENT_LANG
        set_lang("en_us")
        yield
        set_lang(previous)

    def _write_skill(self, tmp_path, filename, content):
        skill_dir = tmp_path / ".gitpr" / "skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / filename).write_text(content, encoding="utf-8")
        return skill_dir / filename

    def test_release_action_reads_release_file(self, tmp_path):
        self._write_skill(tmp_path, ".gitpr.release.md", "Release persona content")
        assert get_skill_context("release", quiet=True) == "Release persona content"

    def test_release_without_file_returns_empty(self, tmp_path):
        # No .gitpr.release.md and no legacy .gitpr.md in this cwd.
        assert get_skill_context("release", quiet=True) == ""

    def test_unknown_action_falls_back_to_review_file(self, tmp_path):
        self._write_skill(tmp_path, ".gitpr.review.md", "Review persona content")
        assert get_skill_context("weird_action", quiet=True) == "Review persona content"

    def test_legacy_root_file_fallback_applies_to_release(self, tmp_path):
        # Legacy combined .gitpr.md keeps working as the last-resort fallback.
        self._write_skill(tmp_path, ".gitpr.md", "Legacy persona content")
        assert get_skill_context("release", quiet=True) == "Legacy persona content"

    def test_quiet_loads_without_terminal_message(self, tmp_path, capsys):
        self._write_skill(tmp_path, ".gitpr.release.md", "Persona")
        get_skill_context("release", quiet=True)
        assert capsys.readouterr().out == ""

    def test_not_quiet_announces_the_loaded_skill(self, tmp_path, capsys):
        self._write_skill(tmp_path, ".gitpr.release.md", "Persona")
        get_skill_context("release")
        assert "found and loaded" in capsys.readouterr().out


class TestRegistryMatchesTheLoader:
    """The registry in config.py is the one source for both the loader and the
    configuration screen. If the two ever drift, the screen would offer to edit
    a file that no command reads — or hide one that every command does."""

    @pytest.fixture(autouse=True)
    def _tmp_cwd(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.core.os.getcwd", lambda: str(tmp_path))
        monkeypatch.setattr("src.config.os.getcwd", lambda: str(tmp_path))

    def _write_skill(self, tmp_path, filename, content):
        skill_dir = tmp_path / ".gitpr" / "skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / filename).write_text(content, encoding="utf-8")

    @pytest.mark.parametrize("skill_type", SKILL_TYPES)
    def test_every_type_loads_the_file_the_registry_declares(
        self, tmp_path, skill_type
    ):
        # Every supported file is seeded with its own content, so the returned
        # text proves WHICH file was read, not merely that one was.
        for other_type, filename in SKILL_FILES_BY_TYPE.items():
            self._write_skill(tmp_path, filename, f"content of {other_type}")
        assert get_skill_context(skill_type, quiet=True) == f"content of {skill_type}"

    def test_the_registry_covers_the_review_fallback(self):
        # Anything the registry does not know is answered with the review file,
        # so the fallback cannot point at a type that is not in the registry.
        assert skill_file_for("fullreview") == SKILL_FILES_BY_TYPE["review"]
        assert skill_file_for("not_a_command") == SKILL_FILES_BY_TYPE["review"]


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
