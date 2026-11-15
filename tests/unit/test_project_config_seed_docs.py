"""Tests verifying documentation parity and ADR-0019 contract for project config seeding."""

from pathlib import Path
import re

CONFIG_TUI_DOC_FILES = [
    ("docs/config-tui.md", "docs/pull-request-publication.md"),
    ("docs/config-tui.pt_br.md", "docs/pull-request-publication.pt_br.md"),
    ("docs/config-tui.pt_pt.md", "docs/pull-request-publication.pt_pt.md"),
    ("docs/config-tui.es_es.md", "docs/pull-request-publication.es_es.md"),
    ("docs/config-tui.fr_fr.md", "docs/pull-request-publication.fr_fr.md"),
]

PR_PUBLICATION_DOC_FILES = [rel_pr for _, rel_pr in CONFIG_TUI_DOC_FILES]


def _github_heading_slug(heading_text: str) -> str:
    """Compute GitHub-style Markdown anchor slug for a heading string."""
    slug = heading_text.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = slug.replace(" ", "-")
    return slug


def test_pull_request_publication_files_exist_and_have_seed_opt_out_docs():
    """All 5 language variants must document section 9.4, [!IMPORTANT] callout, and GITPR_SKIP_PROJECT_CONFIG_SEED."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for rel_path in PR_PUBLICATION_DOC_FILES:
        doc_path = repo_root / rel_path
        assert doc_path.is_file(), f"Missing doc file: {rel_path}"

        content = doc_path.read_text(encoding="utf-8", errors="replace")

        assert "> [!IMPORTANT]" in content, (
            f"{rel_path} section 9.1 must include a [!IMPORTANT] callout"
        )
        assert "### 9.4 " in content, f"{rel_path} is missing section 9.4 header"
        assert "GITPR_SKIP_PROJECT_CONFIG_SEED" in content, (
            f"{rel_path} must mention GITPR_SKIP_PROJECT_CONFIG_SEED"
        )


def test_config_tui_files_exist_and_reference_seed_opt_out():
    """All 5 language variants of config-tui must document GITPR_SKIP_PROJECT_CONFIG_SEED and link to #94-..."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    for rel_tui, rel_pr in CONFIG_TUI_DOC_FILES:
        tui_path = repo_root / rel_tui
        pr_path = repo_root / rel_pr
        assert tui_path.is_file(), f"Missing doc file: {rel_tui}"
        assert pr_path.is_file(), f"Missing doc file: {rel_pr}"

        tui_content = tui_path.read_text(encoding="utf-8", errors="replace")
        pr_content = pr_path.read_text(encoding="utf-8", errors="replace")

        assert "GITPR_SKIP_PROJECT_CONFIG_SEED" in tui_content, (
            f"{rel_tui} must mention GITPR_SKIP_PROJECT_CONFIG_SEED"
        )

        match = re.search(r"^### (9\.4 .+)$", pr_content, flags=re.MULTILINE)
        assert match, f"{rel_pr} is missing ### 9.4 heading"
        expected_anchor = _github_heading_slug(match.group(1))
        expected_link = f"{pr_path.name}#{expected_anchor}"

        assert expected_link in tui_content, (
            f"{rel_tui} must link to {expected_link}"
        )


def test_adr_0019_exists_and_references_docs():
    """ADR-0019 must exist and cross-reference pull-request-publication.md and config-tui.md."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    adr_path = repo_root / "docs/adr/0019-project-configuration-seed-segregation.md"
    assert adr_path.is_file(), "Missing docs/adr/0019-project-configuration-seed-segregation.md"

    content = adr_path.read_text(encoding="utf-8", errors="replace")
    assert "GITPR_SKIP_PROJECT_CONFIG_SEED" in content
    assert "pull-request-publication.md" in content
    assert "config-tui.md" in content


def test_context_md_defines_project_config_seed_terms():
    """CONTEXT.md must define domain terms for runtime project configuration seed and opt-out."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    context_path = repo_root / "CONTEXT.md"
    assert context_path.is_file()

    content = context_path.read_text(encoding="utf-8", errors="replace")
    assert "**Runtime project configuration seed**:" in content
    assert "**Project configuration seed opt-out**:" in content
    assert "GITPR_SKIP_PROJECT_CONFIG_SEED" in content
