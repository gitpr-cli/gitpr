"""Tests verifying documentation parity and migration notes for gitpr check."""

from pathlib import Path
import pytest

CHECK_CI_DOC_FILES = [
    "docs/check-ci.md",
    "docs/check-ci.pt_br.md",
    "docs/check-ci.pt_pt.md",
    "docs/check-ci.es_es.md",
    "docs/check-ci.fr_fr.md",
]


def test_check_ci_files_exist_and_have_all_sections():
    """All 5 language variants must contain all 7 sections with migration guide."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for rel_path in CHECK_CI_DOC_FILES:
        doc_path = repo_root / rel_path
        assert doc_path.is_file(), f"Missing doc file: {rel_path}"

        content = doc_path.read_text(encoding="utf-8")

        for sec_num in range(1, 8):
            expected_header_prefix = f"## {sec_num}."
            assert expected_header_prefix in content, (
                f"{rel_path} is missing section {sec_num} ({expected_header_prefix})"
            )

        # Section 7 must mention the contract change
        assert "action.yml" in content, f"{rel_path} section 7 must mention action.yml"
        assert "--linter" in content, f"{rel_path} section 7 must mention --linter"
        assert "--fullreview" in content, f"{rel_path} section 7 must mention --fullreview"
        assert "gitpr check" in content, f"{rel_path} section 7 must mention gitpr check"
        assert "SARIF" in content, f"{rel_path} section 7 must mention SARIF"


def test_context_md_defines_legacy_ci_action_contract():
    """CONTEXT.md must define the domain concept for Legacy CI action contract."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    context_path = repo_root / "CONTEXT.md"
    assert context_path.is_file()

    content = context_path.read_text(encoding="utf-8")
    assert "**Legacy CI action contract**:" in content
    assert "action.yml" in content
    assert "CI Check" in content


def test_action_yml_and_adr_0011_reference_migration_guide():
    """ADR-0011 and action.yml must reference the unified check migration."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    adr_path = repo_root / "docs/adr/0011-action-unified-check-migration.md"
    assert adr_path.is_file(), "Missing docs/adr/0011-action-unified-check-migration.md"

    adr_content = adr_path.read_text(encoding="utf-8")
    assert "action.yml" in adr_content
    assert "gitpr check" in adr_content
    assert "--linter" in adr_content
    assert "--fullreview" in adr_content
    assert "SARIF" in adr_content
    assert "docs/check-ci.md" in adr_content

    action_path = repo_root / "action.yml"
    assert action_path.is_file(), "Missing action.yml"
    action_content = action_path.read_text(encoding="utf-8")
    assert "gitpr check" in action_content
    assert "docs/check-ci" in action_content
