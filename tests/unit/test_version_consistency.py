"""Automated tests ensuring version consistency across the codebase.

Validates that src.updater.__version__ is the canonical Single Source of Truth
(SSOT) for package versioning, and that pyproject.toml, CLAUDE.md, and GEMINI.md
remain strictly synchronized with it.
"""

import os
import re
import unittest
from packaging.version import InvalidVersion, Version

from src.updater import __lang_version__, __scripts_version__, __version__


class TestVersionConsistency(unittest.TestCase):
    """Guards against documentation and package configuration version drift."""

    def setUp(self):
        self.root_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    def test_package_version_is_valid_pep440(self):
        """Ensures __version__ is a valid PEP 440 version string."""
        self.assertIsInstance(__version__, str)
        self.assertFalse(
            __version__.startswith("v"),
            "Package __version__ must not have a leading 'v' (PEP 440 canonical).",
        )
        try:
            parsed = Version(__version__)
            self.assertIsNotNone(parsed)
        except InvalidVersion as exc:
            self.fail(f"__version__ '{__version__}' is not a valid PEP 440 version: {exc}")

    def test_pyproject_toml_points_to_ssot(self):
        """Verifies pyproject.toml binds dynamically to src.updater.__version__."""
        pyproject_path = os.path.join(self.root_dir, "pyproject.toml")
        self.assertTrue(os.path.isfile(pyproject_path), "pyproject.toml must exist at repo root.")

        with open(pyproject_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        self.assertIn(
            'version = {attr = "src.updater.__version__"}',
            content,
            "pyproject.toml must configure dynamic version from src.updater.__version__.",
        )

    def test_claude_md_version_matches_ssot(self):
        """Ensures CLAUDE.md current version matches src.updater.__version__."""
        claude_md_path = os.path.join(self.root_dir, "CLAUDE.md")
        self.assertTrue(os.path.isfile(claude_md_path), "CLAUDE.md must exist at repo root.")

        with open(claude_md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        match = re.search(r"-\s+\*\*Current version:\*\*\s+([0-9]+\.[0-9]+\.[0-9]+)", content)
        self.assertIsNotNone(
            match, "CLAUDE.md must contain '- **Current version:** <semver>' header entry."
        )
        doc_version = match.group(1)
        self.assertEqual(
            doc_version,
            __version__,
            f"CLAUDE.md version '{doc_version}' is out of sync with src.updater.__version__ '{__version__}'.",
        )

    def test_gemini_md_version_matches_ssot(self):
        """Ensures GEMINI.md current version matches src.updater.__version__."""
        gemini_md_path = os.path.join(self.root_dir, "GEMINI.md")
        self.assertTrue(os.path.isfile(gemini_md_path), "GEMINI.md must exist at repo root.")

        with open(gemini_md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        match = re.search(r"-\s+\*\*Current version:\*\*\s+([0-9]+\.[0-9]+\.[0-9]+)", content)
        self.assertIsNotNone(
            match, "GEMINI.md must contain '- **Current version:** <semver>' header entry."
        )
        doc_version = match.group(1)
        self.assertEqual(
            doc_version,
            __version__,
            f"GEMINI.md version '{doc_version}' is out of sync with src.updater.__version__ '{__version__}'.",
        )

    def test_asset_versions_distinct_from_package_version(self):
        """Validates that asset versions are distinct and properly formatted."""
        self.assertIsInstance(__lang_version__, str)
        self.assertTrue(
            __lang_version__.startswith("v"),
            "Language asset version must use 'v' prefix convention (e.g. v0.0.37).",
        )
        self.assertIsInstance(__scripts_version__, str)
        self.assertTrue(
            __scripts_version__.startswith("v"),
            "Hook scripts asset version must use 'v' prefix convention (e.g. v0.0.4).",
        )


if __name__ == "__main__":
    unittest.main()
