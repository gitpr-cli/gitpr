"""Tests verifying documentation parity across all 5 languages for marketplace-publishing-guide."""

from pathlib import Path
import pytest

MARKETPLACE_GUIDE_DOC_FILES = [
    "docs/marketplace-publishing-guide.md",
    "docs/marketplace-publishing-guide.pt_br.md",
    "docs/marketplace-publishing-guide.pt_pt.md",
    "docs/marketplace-publishing-guide.es_es.md",
    "docs/marketplace-publishing-guide.fr_fr.md",
]

EDITOR_EXTENSION_LOCALIZED_PAIRS = [
    ("docs/editor-extension.md", "marketplace-publishing-guide.md"),
    ("docs/editor-extension.pt_br.md", "marketplace-publishing-guide.pt_br.md"),
    ("docs/editor-extension.pt_pt.md", "marketplace-publishing-guide.pt_pt.md"),
    ("docs/editor-extension.es_es.md", "marketplace-publishing-guide.es_es.md"),
    ("docs/editor-extension.fr_fr.md", "marketplace-publishing-guide.fr_fr.md"),
]


def test_marketplace_publishing_guide_all_files_exist_and_non_empty():
    """All 5 language variants must exist in docs/ and not be empty."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for rel_path in MARKETPLACE_GUIDE_DOC_FILES:
        doc_path = repo_root / rel_path
        assert doc_path.is_file(), f"Missing doc file: {rel_path}"
        content = doc_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 500, f"{rel_path} is unexpectedly small or empty"


def test_marketplace_publishing_guide_section_parity():
    """All 5 language variants must contain all required sections and steps."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for rel_path in MARKETPLACE_GUIDE_DOC_FILES:
        doc_path = repo_root / rel_path
        content = doc_path.read_text(encoding="utf-8")

        # Top-level title and numbered major sections
        assert content.startswith("# "), f"{rel_path} must start with top-level H1 header"
        assert "## 1. " in content, f"{rel_path} missing Section 1 (VS Marketplace)"
        assert "## 2. " in content, f"{rel_path} missing Section 2 (Open VSX)"
        assert "## 3. " in content, f"{rel_path} missing Section 3 (Local Verification)"
        assert "## 4. " in content, f"{rel_path} missing Section 4 (Automated Release Trigger)"
        assert "## 5. " in content, f"{rel_path} missing Section 5 (Maintenance & Future Releases)"

        # Step subsections
        assert " 1.1" in content, f"{rel_path} missing Step 1.1"
        assert " 1.2" in content, f"{rel_path} missing Step 1.2"
        assert " 1.3" in content, f"{rel_path} missing Step 1.3"
        assert " 1.4" in content, f"{rel_path} missing Step 1.4"
        assert " 2.1" in content, f"{rel_path} missing Step 2.1"
        assert " 2.2" in content, f"{rel_path} missing Step 2.2"
        assert " 2.3" in content, f"{rel_path} missing Step 2.3"
        assert " 2.4" in content, f"{rel_path} missing Step 2.4"


def test_marketplace_publishing_guide_token_preservation():
    """Critical technical tokens, commands, and secrets must be preserved verbatim in all languages."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    required_tokens = [
        "VSCE_PAT",
        "OVSX_PAT",
        "ext-v",
        "natanfiuza",
        "gitpr-marketplace-publish",
        "Acquire",
        "Manage",
        "npx @vscode/vsce verify-pat",
        "npx ovsx verify-pat",
        "npm run compile",
        "npm test",
        "npm run package",
        "package.json",
        ".vsix",
    ]

    for rel_path in MARKETPLACE_GUIDE_DOC_FILES:
        doc_path = repo_root / rel_path
        content = doc_path.read_text(encoding="utf-8")
        for token in required_tokens:
            assert token in content, f"{rel_path} missing required technical token: {token}"


def test_editor_extension_cross_links_to_localized_guides():
    """docs/editor-extension.*.md must link to the matching localized guide."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for ext_doc, expected_guide in EDITOR_EXTENSION_LOCALIZED_PAIRS:
        doc_path = repo_root / ext_doc
        assert doc_path.is_file(), f"Missing editor-extension doc file: {ext_doc}"
        content = doc_path.read_text(encoding="utf-8")
        assert f"({expected_guide})" in content, (
            f"{ext_doc} must link directly to ({expected_guide})"
        )
