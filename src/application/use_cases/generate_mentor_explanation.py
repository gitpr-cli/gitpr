"""Orchestration use case for GitPR Junior Mentor Mode.

Connects findings collected by `src.fix.apply_fix.collect_candidates` to the AI
mentor skill prompt, executes batch AI requests (with MD5 local caching), and
structures the response into a MentorRun.
"""
import json
from dataclasses import dataclass
from typing import Sequence

from src.ai_providers import call_ai_model
from src.cache import get_cached_response, save_cached_response
from src.config import (
    get_ai_provider,
    get_api_key,
    get_api_model,
    mentor_include_analogy,
)
from src.core import get_skill_context
from src.diff_parser import split_patch_sections
from src.domain.mentor.mentor_explanation_builder import (
    MentorExplanation,
    build_mentor_section,
    parse_mentor_payload,
)
from src.fix.patch_provenance import PatchCandidate
from src.i18n import __

MENTOR_ACTION = "mentor"
PROMPT_VERSION = "1"
MAX_FINDINGS_PER_RUN = 10
MAX_CONTEXT_CHARS_PER_FINDING = 4000

_SEVERITY_ORDER = {
    "blocker": 0,
    "critical": 1,
    "high": 2,
    "error": 3,
    "medium": 4,
    "warning": 5,
    "low": 6,
    "info": 7,
}


class MentorError(Exception):
    """Raised when the mentor pipeline cannot generate explanations."""


@dataclass(frozen=True)
class MentorRun:
    """The outcome of a mentor explanation generation run."""

    explanations: tuple[MentorExplanation, ...]
    skipped_ids: tuple[str, ...]
    markdown: str


def _sort_key(candidate: PatchCandidate):
    sev = str(candidate.finding.severity or "").lower()
    return _SEVERITY_ORDER.get(sev, 99)


def _system_instruction(skill_context: str | None = None, quiet: bool = False) -> str:
    if skill_context:
        return skill_context
    return get_skill_context("mentor", quiet=quiet) or __(
        "You are an empathetic, experienced Senior Software Engineer and Technical Mentor. "
        "Transform code review findings into pedagogical, actionable, and didactic feedback for junior engineers."
    )


def _extract_file_contexts(diff_text: str) -> dict[str, str]:
    """Map normalized file path to its diff text slice."""
    if not diff_text or not diff_text.strip():
        return {}
    sections = split_patch_sections(diff_text)
    mapping = {}
    for sec in sections:
        norm_path = sec.path.replace("\\", "/").lstrip("./")
        mapping[norm_path] = sec.text
    return mapping


def generate_mentor_explanations_for_review(
    candidates: Sequence[PatchCandidate],
    diff_text: str,
    ai_provider: str | None = None,
    skill_context: str | None = None,
    include_analogy: bool = True,
    quiet: bool = False,
) -> MentorRun:
    """Generates pedagogical explanations in batch for a list of review candidates."""
    if not candidates:
        return MentorRun(explanations=(), skipped_ids=(), markdown="")

    provider = ai_provider or get_ai_provider()
    api_key = get_api_key(provider)
    if not api_key:
        raise MentorError(
            __(
                "❌ No API key configured for {provider}. Generate one with --install.",
                provider=provider,
            )
        )

    api_model = get_api_model(provider, task_complexity="advanced")

    # Sort candidates by severity (stable sort retains order of FIX-NNN for identical severities)
    sorted_candidates = sorted(candidates, key=_sort_key)
    selected = sorted_candidates[:MAX_FINDINGS_PER_RUN]
    skipped_ids = tuple(c.finding.id for c in sorted_candidates[MAX_FINDINGS_PER_RUN:])

    # Map candidate IDs and gather code context
    file_diffs = _extract_file_contexts(diff_text)
    insufficient_ids = set()
    technical_messages = {}
    finding_labels = {}

    findings_prompt_items = []
    for cand in selected:
        f = cand.finding
        f_id = f.id
        technical_messages[f_id] = f.message
        label = f"{f_id} · {f.category} · {f.file_path}"
        if f.line_start:
            label += f":{f.line_start}"
        finding_labels[f_id] = label

        norm_file = f.file_path.replace("\\", "/").lstrip("./")
        f_diff = file_diffs.get(norm_file, "")
        if not f_diff:
            insufficient_ids.add(f_id)
        elif len(f_diff) > MAX_CONTEXT_CHARS_PER_FINDING:
            f_diff = f_diff[:MAX_CONTEXT_CHARS_PER_FINDING] + "\n... [truncated]"

        findings_prompt_items.append({
            "finding_id": f_id,
            "category": f.category,
            "severity": f.severity,
            "file_path": f.file_path,
            "line_start": f.line_start,
            "message": f.message,
            "code_diff_context": f_diff,
        })

    analogy_inst = (
        "Include an everyday or basic programming analogy if it clarifies the concept, or null if unnecessary."
        if include_analogy
        else "Always set analogy to null."
    )

    prompt = (
        "Below is a list of code review findings with their respective code diff contexts.\n"
        "Generate pedagogical and didactic explanations for junior developers learning software engineering.\n\n"
        f"Instructions:\n"
        f"1. Return ONLY a valid JSON object matching this schema:\n"
        f'{{"explanations": [{{"finding_id": "...", "what_is_happening": "...", "why_it_matters": "...", "analogy": null, "learn_more_pointer": "...", "has_sufficient_evidence": true}}]}}\n'
        f"2. {analogy_inst}\n"
        f"3. In learn_more_pointer, suggest only conceptual names/principles. Do NOT include URLs or links.\n"
        f"4. If the reason why it matters cannot be inferred with certainty from the code diff context, set has_sufficient_evidence to false and why_it_matters to empty string.\n\n"
        f"=== FINDINGS ===\n"
        f"{json.dumps(findings_prompt_items, indent=2)}\n"
    )

    cached = get_cached_response(MENTOR_ACTION, prompt)
    if isinstance(cached, dict) and cached.get("explanations"):
        payload = cached
    else:
        response = call_ai_model(
            provider=provider,
            api_key=api_key,
            api_model=api_model,
            prompt=prompt,
            system_instruction=_system_instruction(skill_context, quiet=quiet),
            action=MENTOR_ACTION,
            quiet=quiet,
        )
        if not response or not isinstance(response, dict):
            raise MentorError(
                __("❌ The AI did not return any mentor explanations. Try again or check the provider.")
            )

        payload = {"explanations": response.get("explanations") if isinstance(response.get("explanations"), list) else []}
        save_cached_response(MENTOR_ACTION, MENTOR_ACTION, prompt, payload)

    selected_ids = [c.finding.id for c in selected]
    explanations = parse_mentor_payload(
        payload=payload,
        expected_ids=selected_ids,
        include_analogy=include_analogy,
        insufficient_ids=frozenset(insufficient_ids),
        technical_messages=technical_messages,
        finding_labels=finding_labels,
    )

    if not explanations:
        raise MentorError(__("❌ Failed to parse any mentor explanations from the response."))

    markdown = build_mentor_section(explanations, skipped_ids=skipped_ids)
    return MentorRun(
        explanations=tuple(explanations),
        skipped_ids=skipped_ids,
        markdown=markdown,
    )


def generate_mentor_explanation(
    finding: PatchCandidate,
    diff_text: str,
    ai_provider: str | None = None,
    skill_context: str | None = None,
    include_analogy: bool = True,
    quiet: bool = False,
) -> MentorExplanation | None:
    """Generates an explanation for a single candidate."""
    run = generate_mentor_explanations_for_review(
        candidates=[finding],
        diff_text=diff_text,
        ai_provider=ai_provider,
        skill_context=skill_context,
        include_analogy=include_analogy,
        quiet=quiet,
    )
    return run.explanations[0] if run.explanations else None


def explain_review(
    record: dict,
    finding_id: str | None = None,
    ai_provider: str | None = None,
    include_analogy: bool | None = None,
    quiet: bool = False,
) -> MentorRun:
    """Orchestrates candidate collection from a review record, then generates explanations."""
    from src.config import get_fix_settings
    from src.fix.apply_fix import (
        FixError,
        collect_candidates,
        find_candidate,
        reviewed_diff,
    )

    if include_analogy is None:
        include_analogy = mentor_include_analogy()

    settings = get_fix_settings()
    try:
        candidates = collect_candidates(
            record,
            provider=ai_provider,
            quiet=quiet,
            max_lines_changed=settings["safe_max_lines_changed"],
            excluded_paths=settings["safe_excluded_paths"],
        )
    except FixError as exc:
        raise MentorError(str(exc)) from exc

    if not candidates:
        raise MentorError(__("ℹ️ The review raised no fixable findings."))

    if finding_id:
        try:
            target = find_candidate(candidates, finding_id)
            selected = (target,)
        except FixError as exc:
            raise MentorError(str(exc)) from exc
    else:
        selected = candidates

    diff_text = reviewed_diff(record, quiet=quiet)
    return generate_mentor_explanations_for_review(
        candidates=selected,
        diff_text=diff_text,
        ai_provider=ai_provider,
        include_analogy=include_analogy,
        quiet=quiet,
    )

