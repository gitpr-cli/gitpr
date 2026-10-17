"""Integrity guard for the skill templates served by ``gitpr --skill``.

A template is a prompt: whatever is pasted into it becomes an instruction the
model obeys. A stray JSON fragment once shipped inside the pt_br PR template's
required-structure rule and the model faithfully echoed it into every generated
PR body. These tests scan the shipped templates for embedded skill-file
references so a paste like that cannot reach users again.
"""

import re
from pathlib import Path

import pytest

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

# A skill filename inside a key/value pair, e.g. `.gitpr.commit.md": "gitpr.commit.md"`.
# Intentional JSON examples elsewhere ({"status": "ORIGIN", ...}) never match.
_EMBEDDED_SKILL_REFERENCE = re.compile(r'\.gitpr\.[a-z_]+\.(md|yml)"\s*:')

_TEMPLATE_FILES = sorted(
    path for path in TEMPLATES_DIR.glob("*") if path.suffix in {".md", ".yml"}
)


@pytest.mark.parametrize("template", _TEMPLATE_FILES, ids=lambda path: path.name)
def test_template_has_no_embedded_skill_reference_artifact(template):
    content = template.read_text(encoding="utf-8", errors="replace")
    offenders = [
        f"{template.name}:{number}: {line.strip()}"
        for number, line in enumerate(content.splitlines(), start=1)
        if _EMBEDDED_SKILL_REFERENCE.search(line)
    ]
    assert not offenders, "Embedded skill reference artifact(s):\n" + "\n".join(
        offenders
    )
