"""Tests verifying documentation parity and migration notes for auto-update and install-from-source."""

from pathlib import Path
import pytest

AUTO_UPDATE_DOC_FILES = [
    "docs/auto-update.md",
    "docs/auto-update.pt_br.md",
    "docs/auto-update.pt_pt.md",
    "docs/auto-update.es_es.md",
    "docs/auto-update.fr_fr.md",
]

INSTALL_FROM_SOURCE_DOC_FILES = [
    "docs/tutorial/install-from-source.md",
    "docs/tutorial/install-from-source.pt_br.md",
    "docs/tutorial/install-from-source.pt_pt.md",
    "docs/tutorial/install-from-source.es_es.md",
    "docs/tutorial/install-from-source.fr_fr.md",
]


def test_auto_update_files_exist_and_have_migration_note():
    """All 5 language variants of auto-update must contain the migration note with ADR link."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for rel_path in AUTO_UPDATE_DOC_FILES:
        doc_path = repo_root / rel_path
        assert doc_path.is_file(), f"Missing doc file: {rel_path}"

        content = doc_path.read_text(encoding="utf-8")

        # Warning callout must be present
        assert "> [!WARNING]" in content, f"{rel_path} must have a [!WARNING] callout"

        # Must mention the environment variable
        assert "GITPR_SKIP_UPDATE_CHECK" in content, (
            f"{rel_path} must mention GITPR_SKIP_UPDATE_CHECK"
        )

        # Must mention truthy and falsey values
        assert "`1`" in content or "1" in content
        assert "`true`" in content or "true" in content
        assert "`false`" in content or "false" in content
        assert "`0`" in content or "0" in content

        # Must cross-reference ADR-0021
        assert "0021-strict-boolean-update-check-migration.md" in content, (
            f"{rel_path} must link to ADR-0021"
        )


def test_install_from_source_files_exist_and_have_migration_note():
    """All 5 language variants of install-from-source must contain Section 5 migration note with ADR link."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for rel_path in INSTALL_FROM_SOURCE_DOC_FILES:
        doc_path = repo_root / rel_path
        assert doc_path.is_file(), f"Missing doc file: {rel_path}"

        content = doc_path.read_text(encoding="utf-8")

        # Warning callout must be present
        assert "> [!WARNING]" in content, f"{rel_path} must have a [!WARNING] callout"

        # Must mention the environment variable
        assert "GITPR_SKIP_UPDATE_CHECK" in content, (
            f"{rel_path} must mention GITPR_SKIP_UPDATE_CHECK"
        )

        # Must cross-reference ADR-0021
        assert "0021-strict-boolean-update-check-migration.md" in content, (
            f"{rel_path} must link to ADR-0021"
        )


def test_adr_0021_exists_and_references_docs_and_updater():
    """ADR-0021 must exist and document the strict boolean evaluation and remediation."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    adr_path = repo_root / "docs/adr/0021-strict-boolean-update-check-migration.md"
    assert adr_path.is_file(), "Missing docs/adr/0021-strict-boolean-update-check-migration.md"

    content = adr_path.read_text(encoding="utf-8")
    assert "GITPR_SKIP_UPDATE_CHECK" in content
    assert "_SKIP_TRUTHY_VALUES" in content
    assert "auto-update.md" in content
    assert "install-from-source.md" in content
    assert "0014-canonical-package-version-ssot.md" in content


def test_context_md_defines_update_check_switch():
    """CONTEXT.md must define domain term for Update check switch."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    context_path = repo_root / "CONTEXT.md"
    assert context_path.is_file()

    content = context_path.read_text(encoding="utf-8")
    assert "**Update check switch**:" in content
    assert "GITPR_SKIP_UPDATE_CHECK" in content
