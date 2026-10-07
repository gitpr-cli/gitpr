"""Pure domain builder and parser for GitPR Mentor Mode explanations.

Contains no I/O, no network, and no AI calls. Responsible for parsing
AI responses into structured MentorExplanation objects, enforcing epistemic
honesty, stripping fabricated URLs, and building formatted markdown.
"""
import json
import re
from dataclasses import dataclass
from typing import Sequence

from src.i18n import __

_URL_RE = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)

_PLACEHOLDER_MARKERS = ("[FILL", "[TODO", "[PREENCHER", "[REQUIRED")


@dataclass(frozen=True)
class MentorExplanation:
    """One pedagogical explanation linked to an original finding."""

    finding_id: str
    what_is_happening: str
    why_it_matters: str
    analogy: str | None
    learn_more_pointer: str | None
    has_sufficient_evidence: bool
    markdown: str


def build_mentor_markdown(
    finding_label: str,
    technical_message: str,
    what_is_happening: str,
    why_it_matters: str,
    analogy: str | None = None,
    learn_more_pointer: str | None = None,
) -> str:
    """Formats one explanation block in Markdown, keeping the original technical message intact."""
    lines = [
        f"### 💡 {finding_label}",
    ]
    if technical_message.strip():
        lines.append(f"> {technical_message.strip()}")
        lines.append("")

    lines.extend([
        "**" + __("What is happening:") + "** " + what_is_happening.strip(),
        "",
        "**" + __("Why it matters:") + "** " + why_it_matters.strip(),
        "",
    ])

    if analogy and analogy.strip() and analogy.strip().lower() != "null":
        lines.extend([
            "**" + __("Analogy:") + "** " + analogy.strip(),
            "",
        ])

    if learn_more_pointer and learn_more_pointer.strip():
        lines.extend([
            "**" + __("To learn more:") + "** " + learn_more_pointer.strip(),
            "",
        ])

    return "\n".join(lines).strip()


def build_mentor_section(
    explanations: Sequence[MentorExplanation],
    skipped_ids: Sequence[str] = (),
) -> str:
    """Constructs the full '## 🎓 Mentor' section to append to the review."""
    if not explanations:
        return ""

    lines = [
        "## 🎓 " + __("Mentor (Junior Guidance)"),
        "",
        __("The explanations below provide pedagogical context and practical learning points for the findings raised above:"),
        "",
    ]

    for item in explanations:
        lines.append(item.markdown)
        lines.append("")
        lines.append("---")
        lines.append("")

    # Remove the trailing divider
    if lines[-1] == "":
        lines.pop()
    if lines and lines[-1] == "---":
        lines.pop()
    if lines and lines[-1] == "":
        lines.pop()

    if skipped_ids:
        lines.extend([
            "",
            "ℹ️ " + __(
                "{count} additional finding(s) not expanded here. Run 'gitpr mentor --finding <id>' to inspect them individually.",
                count=len(skipped_ids),
            )
            + f" ({', '.join(skipped_ids)})",
        ])

    return "\n".join(lines).strip()


def parse_mentor_payload(
    payload: dict | str,
    expected_ids: Sequence[str],
    include_analogy: bool = True,
    insufficient_ids: frozenset[str] = frozenset(),
    technical_messages: dict[str, str] | None = None,
    finding_labels: dict[str, str] | None = None,
) -> list[MentorExplanation]:
    """Parses raw AI payload into a list of verified MentorExplanation instances."""
    if technical_messages is None:
        technical_messages = {}
    if finding_labels is None:
        finding_labels = {}

    data = None
    if isinstance(payload, dict):
        data = payload
    elif isinstance(payload, str) and payload.strip():
        try:
            data = json.loads(payload)
        except Exception:
            return []
    else:
        return []

    if not isinstance(data, dict):
        return []

    raw_list = data.get("explanations")
    if not isinstance(raw_list, list):
        return []

    parsed_by_id: dict[str, MentorExplanation] = {}
    valid_expected_ids = set(expected_ids)

    default_insufficient_msg = __(
        "Could not safely infer why this matters from the diff alone; ask whoever reviewed it."
    )

    for item in raw_list:
        if not isinstance(item, dict):
            continue

        raw_id = str(item.get("finding_id") or "").strip().upper()
        if not raw_id or raw_id not in valid_expected_ids:
            continue

        if raw_id in parsed_by_id:
            # Duplicate item; preserve the first seen
            continue

        what = str(item.get("what_is_happening") or "").strip()
        why = str(item.get("why_it_matters") or "").strip()

        # Discard if both are completely empty
        if not what and not why:
            continue

        # Epistemic honesty & evidence validation
        has_evidence = item.get("has_sufficient_evidence")
        if has_evidence is None:
            has_evidence = True
        else:
            has_evidence = bool(has_evidence)

        if raw_id in insufficient_ids:
            has_evidence = False

        if any(marker in why.upper() or marker in what.upper() for marker in _PLACEHOLDER_MARKERS):
            has_evidence = False

        if not why:
            has_evidence = False

        if not has_evidence:
            why = default_insufficient_msg

        # Analogy handling
        analogy = None
        if include_analogy:
            raw_analogy = item.get("analogy")
            if raw_analogy and str(raw_analogy).strip().lower() != "null":
                analogy = str(raw_analogy).strip()

        # Learn more pointer handling (never allow URLs)
        raw_pointer = item.get("learn_more_pointer")
        pointer = None
        if raw_pointer and str(raw_pointer).strip():
            pointer_str = str(raw_pointer).strip()
            if not _URL_RE.search(pointer_str):
                pointer = pointer_str

        label = finding_labels.get(raw_id, raw_id)
        tech_msg = technical_messages.get(raw_id, "")

        md = build_mentor_markdown(
            finding_label=label,
            technical_message=tech_msg,
            what_is_happening=what,
            why_it_matters=why,
            analogy=analogy,
            learn_more_pointer=pointer,
        )

        parsed_by_id[raw_id] = MentorExplanation(
            finding_id=raw_id,
            what_is_happening=what,
            why_it_matters=why,
            analogy=analogy,
            learn_more_pointer=pointer,
            has_sufficient_evidence=has_evidence,
            markdown=md,
        )

    # Return ordered strictly by expected_ids
    return [parsed_by_id[fid] for fid in expected_ids if fid in parsed_by_id]

