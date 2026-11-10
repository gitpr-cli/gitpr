"""Tests verifying documentation parity and migration notes for scm-multiforge."""

from pathlib import Path
import pytest

SCM_MULTIFORGE_DOC_FILES = [
    "docs/scm-multiforge.md",
    "docs/scm-multiforge.pt_br.md",
    "docs/scm-multiforge.pt_pt.md",
    "docs/scm-multiforge.es_es.md",
    "docs/scm-multiforge.fr_fr.md",
]


def test_scm_multiforge_files_exist_and_have_migration_note_section():
    """All 5 language variants must contain section 3.1 with automated provisioning migration note."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for rel_path in SCM_MULTIFORGE_DOC_FILES:
        doc_path = repo_root / rel_path
        assert doc_path.is_file(), f"Missing doc file: {rel_path}"

        content = doc_path.read_text(encoding="utf-8")

        # Section 3.1 header must exist
        assert "### 3.1 " in content, f"{rel_path} is missing section 3.1 header"

        # Must mention all 3 retired legacy keys
        assert "GITPR_SCM_PROVIDER" in content, f"{rel_path} section 3.1 must mention GITPR_SCM_PROVIDER"
        assert "GITPR_SCM_TOKEN_ENCRYPTED" in content, f"{rel_path} section 3.1 must mention GITPR_SCM_TOKEN_ENCRYPTED"
        assert "GITPR_SCM_BASE_URL" in content, f"{rel_path} section 3.1 must mention GITPR_SCM_BASE_URL"

        # Must mention dedicated per-forge token slots
        assert "GITHUB_TOKEN_ENCRYPTED" in content, f"{rel_path} section 3.1 must mention GITHUB_TOKEN_ENCRYPTED"
        assert "GITLAB_TOKEN_ENCRYPTED" in content, f"{rel_path} section 3.1 must mention GITLAB_TOKEN_ENCRYPTED"
        assert "BITBUCKET_TOKEN_ENCRYPTED" in content, f"{rel_path} section 3.1 must mention BITBUCKET_TOKEN_ENCRYPTED"
        assert "AZURE_DEVOPS_TOKEN_ENCRYPTED" in content, f"{rel_path} section 3.1 must mention AZURE_DEVOPS_TOKEN_ENCRYPTED"

        # Must cross-reference ADR-0020
        assert "0020-per-repo-scm-provisioning-migration.md" in content, (
            f"{rel_path} section 3.1 must link to ADR-0020"
        )


def test_adr_0020_exists_and_references_docs_and_adr_016():
    """ADR-0020 must exist and cross-reference scm-multiforge.md and ADR-016."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    adr_path = repo_root / "docs/adr/0020-per-repo-scm-provisioning-migration.md"
    assert adr_path.is_file(), "Missing docs/adr/0020-per-repo-scm-provisioning-migration.md"

    content = adr_path.read_text(encoding="utf-8")
    assert "GITPR_SCM_PROVIDER" in content
    assert "GITPR_SCM_TOKEN_ENCRYPTED" in content
    assert "GITPR_SCM_BASE_URL" in content
    assert "GITHUB_TOKEN_ENCRYPTED" in content
    assert "GITLAB_TOKEN_ENCRYPTED" in content
    assert "BITBUCKET_TOKEN_ENCRYPTED" in content
    assert "AZURE_DEVOPS_TOKEN_ENCRYPTED" in content
    assert "ADR-016" in content
    assert "scm-multiforge.md" in content


def test_context_md_defines_scm_provisioning_terms():
    """CONTEXT.md must define domain terms for per-forge SCM provisioning."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    context_path = repo_root / "CONTEXT.md"
    assert context_path.is_file()

    content = context_path.read_text(encoding="utf-8")
    assert "**Forge token slot**:" in content
    assert "**Legacy SCM provisioning keys**:" in content
    assert "**Per-forge SCM provisioning**:" in content
