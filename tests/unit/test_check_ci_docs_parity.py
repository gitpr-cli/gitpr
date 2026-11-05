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
