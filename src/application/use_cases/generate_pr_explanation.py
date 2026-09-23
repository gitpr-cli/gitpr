import json
from src.ai_providers import call_ai_model
from src.config import get_ai_provider, get_api_key, get_api_model
from src.core import get_skill_context
from src.domain.pr.explain_section_builder import PrExplanation, parse_explain_payload


def generate_pr_explanation(
    diff_content: str,
    ai_provider: str | None = None,
    skill_context: str | None = None,
    quiet: bool = False,
) -> PrExplanation:
    """Generates a structured reviewer explanation for the current PR diff."""
    if not diff_content or not diff_content.strip():
        return PrExplanation(
            what_changes="",
            why_it_changes="",
            reviewer_focus_points=[],
            regression_risk="",
            has_sufficient_evidence=False,
            markdown="",
        )

    provider = ai_provider or get_ai_provider()
    api_key = get_api_key(provider)
    if not api_key:
        return PrExplanation(
            what_changes="No API key configured.",
            why_it_changes="No API key configured.",
            reviewer_focus_points=[],
            regression_risk="No API key configured.",
            has_sufficient_evidence=False,
            markdown="⚠️ No API key configured for AI provider.",
        )

    api_model = get_api_model(provider, task_complexity="advanced")

    # Load skill context
    skill_instruction = skill_context or get_skill_context("explain", quiet=True)
    if not skill_instruction:
        skill_instruction = (
            "You are an expert Code Reviewer and Software Architect. "
            "Explain this pull request diff from the reviewer's perspective: What changes, Why it changes, Where to focus review, and Regression risk. "
            "You MUST ONLY return a valid JSON object matching this schema:\n"
            '{"what_changes": "2-4 plain language sentences", "why_it_changes": "motivation or [FILL: question]", '
            '"reviewer_focus_points": [{"description": "...", "file_path": "...", "related_line": 0}], '
            '"regression_risk": "short assessment of potential regressions"}'
        )

    user_prompt = (
        "Generate a reviewer guide for the following diff changes:\n\n"
        f"Diff:\n```diff\n{diff_content}\n```\n\n"
        "Instructions:\n"
        "1. In 'what_changes', provide 2-4 plain sentences describing the functional changes without excessive jargon.\n"
        "2. In 'why_it_changes', explain the inferred motivation. If motivation cannot be determined with certainty, use '[FILL: What is the primary business motivation for this change?]'.\n"
        "3. In 'reviewer_focus_points', list 2-5 concrete points requiring specific review attention.\n"
        "4. In 'regression_risk', state any objective risks (critical files, missing tests, auth changes).\n"
        "5. Return strictly JSON with 'what_changes', 'why_it_changes', 'reviewer_focus_points', 'regression_risk'."
    )

    ai_raw = call_ai_model(
        provider=provider,
        api_key=api_key,
        api_model=api_model,
        prompt=user_prompt,
        system_instruction=skill_instruction,
        quiet=quiet,
        action="explain",
    )

    return parse_explain_payload(ai_raw or "")

