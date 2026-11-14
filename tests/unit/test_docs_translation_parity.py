"""Tests that every top-level doc has its four translations and that they stay structurally aligned.

A translation is allowed to read differently — it is a different language — but it must not lose
or gain structure: the same headings, the same table rows, the same bullets, the same code blocks.
Comparing counts of those anchors catches the drift that line wrapping and translated prose hide.
"""

import re
from pathlib import Path

_LANGS = (".pt_br", ".pt_pt", ".es_es", ".fr_fr")

# Documents kept in English only, on purpose.
_EN_ONLY = {
    "github-issue-prompt-com-gh": "how-to in English only (docs/plans/2026-08-18_architecture_multilang.md)",
}

# Known drift, recorded as debt: repair the translation, then delete the line. The entry is a
# snapshot of the divergence so the reason survives without re-running the comparison.
_PARITY_EXCEPTIONS = {
    "ARCHITECTURE": "headings 27 vs 26, bullets 77 vs 69, fences 4 vs 2",
    "check-ci": "fences 12 vs 10",
    "git-hooks-locais": "headings 10 vs 10 (pt_br) / 9, fences 10 vs 8 (pt_br) / 4",
    "git-status": "fences 14 vs 14 (pt_br) / 8",
    "linter-regras-customizadas": "headings 16 vs 14 (pt_br) / 10, table rows 9 vs 0 in three languages",
    "mentor-mode": "headings 6 vs 4, table rows 11 vs 4, bullets 3 vs 0 (pt_pt/es_es/fr_fr)",
    "pull-request-publication": "headings 54 vs 47, table rows 99 vs 91, bullets 16 vs 13, fences 58 vs 46",
    "skill-template": "table rows 20 vs 18",
}

_HEADING_RE = re.compile(r"^(#{1,6})\s")
_BULLET_RE = re.compile(r"^\s*[-*]\s")


def _docs_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "docs"


def _base_docs() -> list:
    """Top-level English docs — those without a language suffix."""
    return sorted(
        path
        for path in _docs_dir().glob("*.md")
        if not any(path.stem.endswith(suffix) for suffix in _LANGS)
    )


def _scan(text: str) -> tuple:
    """Count the structural anchors of a doc, ignoring what sits inside fenced code blocks."""
    headings = []
    table_rows = 0
    bullets = 0
    fences = 0
    in_fence = False

    for line in text.splitlines():
        if line.startswith("```"):
            fences += 1
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            headings.append(len(heading.group(1)))
        if line.startswith("|"):
            table_rows += 1
        if _BULLET_RE.match(line):
            bullets += 1

    return tuple(headings), table_rows, bullets, fences


def _signature(path: Path) -> tuple:
    return _scan(path.read_text(encoding="utf-8", errors="replace"))


def test_every_doc_has_all_four_languages():
    """Each top-level doc has four non-empty translations, unless it is English-only on purpose."""
    for base_doc in _base_docs():
        name = base_doc.stem

        if name in _EN_ONLY:
            siblings = [base_doc.with_name(f"{name}{suffix}.md") for suffix in _LANGS]
            assert not any(path.exists() for path in siblings), (
                f"{name} is listed in _EN_ONLY but has translations; remove the entry"
            )
            continue

        for suffix in _LANGS:
            translated = base_doc.with_name(f"{name}{suffix}.md")
            assert translated.is_file(), f"Missing translation: docs/{translated.name}"
            assert translated.read_text(encoding="utf-8", errors="replace").strip(), (
                f"Empty translation: docs/{translated.name}"
            )


def test_translations_match_english_structure():
    """Every translation repeats the English structure — same headings, rows, bullets and fences."""
    for base_doc in _base_docs():
        name = base_doc.stem
        if name in _EN_ONLY or name in _PARITY_EXCEPTIONS:
            continue

        english = _signature(base_doc)
        for suffix in _LANGS:
            translated = _signature(base_doc.with_name(f"{name}{suffix}.md"))
            assert translated == english, (
                f"docs/{name}{suffix}.md drifted from docs/{name}.md\n"
                f"  English:   headings={len(english[0])} rows={english[1]} "
                f"bullets={english[2]} fences={english[3]}\n"
                f"  translation: headings={len(translated[0])} rows={translated[1]} "
                f"bullets={translated[2]} fences={translated[3]}"
            )


def test_parity_exceptions_are_still_real():
    """An exception that no longer diverges must be deleted, so the baseline cannot go stale."""
    for name, reason in _PARITY_EXCEPTIONS.items():
        base_doc = _docs_dir() / f"{name}.md"
        assert base_doc.is_file(), f"_PARITY_EXCEPTIONS names a missing doc: {name}"

        english = _signature(base_doc)
        diverges = any(
            _signature(base_doc.with_name(f"{name}{suffix}.md")) != english
            for suffix in _LANGS
        )
        assert diverges, (
            f"{name} now matches its translations but is still in _PARITY_EXCEPTIONS "
            f"({reason}); remove the entry"
        )
