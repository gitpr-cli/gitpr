import subprocess
import re
import time
import click
from src.ai_providers import call_ai_model
from src.cache import get_cached_response, save_cached_response
from src.config import get_api_key, get_api_model, get_ai_provider
from src.ai_providers import call_ai_model
from src.i18n import __
from src.core import (
    estimate_token_count,
    split_diff_into_chunks,
    get_doc_url,
    get_skill_context,
    get_changed_docs_list,
)


def get_github_repo_info():
    """Extracts the owner/repo format from git remote -v."""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"], capture_output=True, text=True, check=True
        )

        # Search for patterns like git@github.com:owner/repo.git or https://github.com/owner/repo.git
        match = re.search(
            r"github\.com[:/](.+?)/(.+?)(\.git)?\s+\(push\)", result.stdout
        )

        if match:
            owner = match.group(1)
            repo = match.group(2).replace(".git", "")
            return f"{owner}/{repo}"

        return None
    except subprocess.CalledProcessError:
        return None


def generate_issue_content(context_text, context_type="diff"):
    """Sends the context (diff, blame, or history) to the AI and returns an issue dictionary."""
    from src.metrics import log_command_metric

    if not context_text or not str(context_text).strip():
        return None

    t_start = time.perf_counter()

    provider = get_ai_provider()
    api_key = get_api_key(provider)

    if not api_key:
        click.secho(__("❌ Error: API Key not found."), fg="red")
        duration_ms = int((time.perf_counter() - t_start) * 1000)
        log_command_metric(
            command="issue", status="error", provider=provider, duration_ms=duration_ms
        )
        return None

    # Use the advanced model to ensure Issue structure quality
    api_model = get_api_model(provider, task_complexity="advanced")

    # Load the issue skill with visual feedback (parity with the PR flow);
    # the default Software Architect persona remains the fallback.
    sys_inst = get_skill_context("issue")
    if not sys_inst:
        sys_inst = __(
            "You are a Software Architect. Follow the What / Why / Where / How format to document the Issue."
        )

    # ── Inject changed documentation file list as metadata (no content) ──
    # Parity with the PR flow: the diff excludes docs via Smart Excludes
    # pathspec, so the AI must know which docs were touched without their
    # full prose/markup content (excluded from the diff).
    if context_type == "diff":
        try:
            changed_docs = get_changed_docs_list()
            if changed_docs:
                docs_section = __(
                    "Changed documentation (content excluded from diff):\n"
                )
                for doc in changed_docs:
                    docs_section += f"- {doc}\n"
                sys_inst = docs_section + "\n" + sys_inst
                click.secho(
                    __(
                        "📄 {count} documentation file(s) excluded from diff (Smart Excludes).",
                        count=len(changed_docs),
                    ),
                    fg="blue",
                    dim=True,
                )
                click.secho(
                    f"📚 {__('Learn more:')} {get_doc_url('smart-excludes.md')}",
                    fg="blue",
                    underline=True,
                )
        except Exception:
            pass  # Non-critical — never block the main flow for this metadata

    # Adaptive Brain (Dynamic Prompt)
    if context_type == "blame":
        target_action = __(
            "document the architectural evolution, refactoring, and technical debt of this business rule based on the commit history."
        )
        data_label = __("RULE TIMELINE (FROM OLDEST TO NEWEST):")
    elif context_type == "history":
        target_action = __(
            "document the Epic/Release detailing all implemented features based on the full branch history."
        )
        data_label = __("CONSOLIDATED BRANCH HISTORY (COMMITS + OLD PRS):")
    else:
        target_action = __("document the following recently introduced code change.")
        data_label = __("DIFF FOR ANALYSIS:")

    prompt = (
        __(
            "Generate the requested JSON object following the system instructions to {target_action}\n\n",
            target_action=target_action,
        )
        + f"{data_label}\n{context_text}"
    )

    # Try to retrieve from Cache
    cached_data = get_cached_response("issue", prompt)
    if cached_data:
        click.secho(
            __("⚡ Issue response retrieved from local cache."), fg="green", dim=True
        )
        duration_ms = int((time.perf_counter() - t_start) * 1000)
        log_command_metric(
            command="issue",
            status="success",
            provider=provider,
            duration_ms=duration_ms,
            cache_hit=True,
        )
        return cached_data

    click.secho(
        __(
            "🤖 Structuring Issue using {provider} ({api_model})...",
            provider=provider.capitalize(),
            api_model=api_model,
        ),
        fg="cyan",
        dim=True,
    )

    # ── Map-Reduce: chunk large diffs to avoid token limit errors ──
    # Only applies to diff context; history and blame are compact by nature.
    total_meta = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "duration_ms": 0,
    }

    def _aggregate_meta(new_meta):
        if new_meta:
            total_meta["prompt_tokens"] += new_meta.get("prompt_tokens", 0)
            total_meta["completion_tokens"] += new_meta.get("completion_tokens", 0)
            total_meta["total_tokens"] += new_meta.get("total_tokens", 0)
            total_meta["duration_ms"] += new_meta.get("duration_ms", 0)

    if context_type == "diff":
        chunks = split_diff_into_chunks(context_text, max_tokens=90000)
    else:
        chunks = [context_text]

    if len(chunks) == 1:
        result_json = call_ai_model(
            provider, api_key, api_model, prompt, sys_inst, action="issue"
        )
        if result_json:
            _aggregate_meta(result_json.pop("_telemetry_meta", None))
    else:
        from src.metrics import log_local_metric

        log_local_metric(
            command="map_reduce",
            status="triggered",
            map_reduce_triggered=True,
            chunks_count=len(chunks),
        )

        click.secho(
            __(
                "📦 Huge diff detected! Processing in {count} batches (Map-Reduce)...",
                count=len(chunks),
            ),
            fg="yellow",
            bold=True,
        )
        click.secho(
            f"📚 {__('Understand why:')} {get_doc_url('map-reduce-diff.md')}\n",
            fg="blue",
            underline=True,
        )
        resumos_parciais = []

        for i, chunk in enumerate(chunks, 1):
            click.secho(
                __(
                    "⏳ Analyzing batch {current}/{total}...",
                    current=i,
                    total=len(chunks),
                ),
                fg="cyan",
                dim=True,
            )

            prompt_parcial = (
                __(
                    "Generate ONLY a JSON object in the format {json_format} containing a technical summary of what was changed in this part ({idx}) of the diff:\n",
                    json_format='{"resumo": "..."}',
                    idx=i,
                )
                + chunk
            )

            resposta_parcial = call_ai_model(
                provider,
                api_key,
                api_model,
                prompt_parcial,
                sys_inst,
                quiet=True,
                action=f"issue_chunk_{i}",
            )

            if resposta_parcial:
                _aggregate_meta(resposta_parcial.pop("_telemetry_meta", None))
                if "resumo" in resposta_parcial:
                    resumos_parciais.append(
                        f"### Batch {i}\n{resposta_parcial['resumo']}"
                    )

            time.sleep(1)

        if not resumos_parciais:
            click.secho(
                __("❌ Failed to extract context from the partial batches."), fg="red"
            )
            duration_ms = int((time.perf_counter() - t_start) * 1000)
            log_command_metric(
                command="issue",
                status="error",
                provider=provider,
                duration_ms=duration_ms,
                map_reduce_triggered=True,
            )
            return {
                "titulo": __("Error generating title"),
                "corpo": __("Could not generate issue body by AI."),
            }

        click.secho(
            __("🔄 Unifying intelligence and generating the final issue..."),
            fg="yellow",
        )
        diff_unificado = "\n\n".join(resumos_parciais)

        prompt = (
            __(
                "Generate the requested JSON object following the system instructions to {target_action}\n\n",
                target_action=target_action,
            )
            + f"{data_label}\n{diff_unificado}"
        )

        result_json = call_ai_model(
            provider, api_key, api_model, prompt, sys_inst, action="issue"
        )
        if result_json:
            _aggregate_meta(result_json.pop("_telemetry_meta", None))

    if result_json and "titulo" in result_json and "corpo" in result_json:
        # Save to cache with aggregated token counts from all chunks
        map_reduce_used = len(chunks) > 1
        save_cached_response("issue", "issue", prompt, result_json, meta_raw=total_meta)
        duration_ms = int((time.perf_counter() - t_start) * 1000)
        log_command_metric(
            command="issue",
            status="success",
            provider=provider,
            tokens_estimated=total_meta.get("total_tokens", 0),
            duration_ms=duration_ms,
            map_reduce_triggered=map_reduce_used,
        )
        return result_json

    duration_ms = int((time.perf_counter() - t_start) * 1000)
    log_command_metric(
        command="issue",
        status="error",
        provider=provider,
        duration_ms=duration_ms,
        map_reduce_triggered=(len(chunks) > 1),
    )
    return {
        "titulo": __("Error generating title"),
        "corpo": __("Could not generate issue body by AI."),
    }
