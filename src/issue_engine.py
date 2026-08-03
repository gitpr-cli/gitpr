import subprocess
import re
import os
import time
import click
from src.ai_providers import call_ai_model
from src.cache import get_cached_response, save_cached_response
from src.config import get_api_key, get_api_model, get_ai_provider, resolve_skill_path
from src.ai_providers import call_ai_model
from src.i18n import __

def get_github_repo_info():
    """Extracts the owner/repo format from git remote -v."""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            check=True
        )

        # Search for patterns like git@github.com:owner/repo.git or https://github.com/owner/repo.git
        match = re.search(r'github\.com[:/](.+?)/(.+?)(\.git)?\s+\(push\)', result.stdout)
        
        if match:
            owner = match.group(1)
            repo = match.group(2).replace('.git', '')
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
        log_command_metric(command="issue", status="error", provider=provider, duration_ms=duration_ms)
        return None

    # Use the advanced model to ensure Issue structure quality
    api_model = get_api_model(provider, task_complexity="advanced")

    skill_path = resolve_skill_path(".gitpr.issue.md")
    sys_inst = ""

    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8") as f:
            sys_inst = f.read()
    else:
        sys_inst = __("You are a Software Architect. Follow the What / Why / Where / How format to document the Issue.")

    # Adaptive Brain (Dynamic Prompt)
    if context_type == "blame":
        target_action = __("document the architectural evolution, refactoring, and technical debt of this business rule based on the commit history.")
        data_label = __("RULE TIMELINE (FROM OLDEST TO NEWEST):")
    elif context_type == "history":
        target_action = __("document the Epic/Release detailing all implemented features based on the full branch history.")
        data_label = __("CONSOLIDATED BRANCH HISTORY (COMMITS + OLD PRS):")
    else:
        target_action = __("document the following recently introduced code change.")
        data_label = __("DIFF FOR ANALYSIS:")

    prompt = (
        __("Generate the requested JSON object following the system instructions to {target_action}\n\n", target_action=target_action) +
        f"{data_label}\n{context_text}"
    )

    # Try to retrieve from Cache
    cached_data = get_cached_response("issue", prompt)
    if cached_data:
        click.secho(__("⚡ Issue response retrieved from local cache."), fg="green", dim=True)
        duration_ms = int((time.perf_counter() - t_start) * 1000)
        log_command_metric(command="issue", status="success", provider=provider, duration_ms=duration_ms, cache_hit=True)
        return cached_data

    click.secho(__("🤖 Structuring Issue using {provider} ({api_model})...", provider=provider.capitalize(), api_model=api_model), fg="cyan", dim=True)

    result_json = call_ai_model(provider, api_key, api_model, prompt, sys_inst, action="issue")

    if result_json and "titulo" in result_json and "corpo" in result_json:
        # Extract telemetry metadata and save to cache with real token counts
        meta = result_json.pop("_telemetry_meta", None)
        save_cached_response("issue", "issue", prompt, result_json, meta_raw=meta)
        duration_ms = int((time.perf_counter() - t_start) * 1000)
        log_command_metric(
            command="issue",
            status="success",
            provider=provider,
            tokens_estimated=(meta or {}).get("total_tokens", 0),
            duration_ms=duration_ms,
        )
        return result_json

    duration_ms = int((time.perf_counter() - t_start) * 1000)
    log_command_metric(command="issue", status="error", provider=provider, duration_ms=duration_ms)
    return {"titulo": __("Error generating title"), "corpo": __("Could not generate issue body by AI.")}