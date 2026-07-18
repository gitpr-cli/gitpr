import subprocess
import click
import re
import os
from datetime import datetime
from src.core import get_current_branch
from src.config import get_api_key, get_api_model, get_ai_provider, resolve_skill_path
from src.ai_providers import call_ai_model
from src.i18n import __

def execute_git_blame(file_path, start_line, end_line, commit_hash=None):
    """Runs git blame and returns a list of unique hashes."""
    cmd = ["git", "blame", f"-L", f"{start_line},{end_line}"]
    if commit_hash:
        cmd.append(commit_hash)
    cmd.extend(["--", file_path])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
        )
        hashes = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                match = re.match(r'^([a-fA-F0-9]+)\s', line)
                if match:
                    commit = match.group(1)
                    if not commit.startswith('000000'):
                        hashes.add(commit)
        return list(hashes)
    except subprocess.CalledProcessError as e:
        # If it fails (e.g.: file didn't exist in that old commit), silently return empty
        return []

def execute_git_show(commit_hash, file_path):
    """Runs git show to get the exact diff."""
    cmd = ["git", "show", commit_hash, "--", file_path]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None

def get_commit_info(commit_hash):
    """Fetches commit author, date, and message."""
    cmd = ["git", "show", "-s", "--format=%an|%ad|%s", "--date=short", commit_hash]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
        parts = res.stdout.strip().split('|', 2)
        if len(parts) == 3:
            return {"author": parts[0], "date": parts[1], "message": parts[2]}
    except:
        pass
    return {"author": __("Unknown"), "date": __("Unknown"), "message": __("No message")}

def analyze_commit_with_ai(commit_hash, file_path):
    """Uses AI to read the diff and classify as ORIGIN or REFACTORING."""
    diff = execute_git_show(commit_hash, file_path)
    if not diff:
        return {"status": "ORIGIN", "reason": __("Diff not found (file possibly created here).")}

    provider = get_ai_provider()
    api_key = get_api_key(provider)
    if not api_key:
        return {"status": "ORIGIN", "reason": __("No API key. Assuming origin.")}

    # Use the 'simple' model (Flash/Lite) to save money in the loop
    api_model = get_api_model(provider, task_complexity="simple")

    skill_path = resolve_skill_path(".gitpr.blame.md")
    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8") as f:
            sys_inst = f.read()
    else:
        sys_inst = __('You are a Software Architect. Analyze the diff and determine if it is the ORIGIN of the rule (new logic) or REFACTORING. Respond ONLY with JSON: {"status": "ORIGIN", "reason": "Explain what was introduced"} or {"status": "REFACTORING", "reason": "Explain what was changed"}')

    prompt = (
        __("Analyze the diff of commit {commit_hash} and return the requested JSON.\n\n", commit_hash=commit_hash) +
        f"DIFF:\n{diff[:4000]}"
    )

    click.secho(__("  🤖 Consulting AI ({api_model}) about commit {commit_hash}...", api_model=api_model, commit_hash=commit_hash[:8]), fg="cyan", dim=True)

    result_json = call_ai_model(provider, api_key, api_model, prompt, sys_inst, action="blame")

    if result_json and "status" in result_json:
        return result_json

    return {"status": "ORIGIN", "reason": __("AI did not return a valid format.")}

def run_blame_analysis(file_path, start_line, end_line, return_data=False):
    """Temporal Loop Engine that builds the consolidated Timeline."""

    # If triggered for data return (via --issue), suppress console output
    if not return_data:
        click.secho(__("\n🔍 Starting Code Archeology..."), fg="cyan", bold=True)
        click.echo(__("📍 File: {file_path} (Lines: {start_line} to {end_line})", file_path=file_path, start_line=start_line, end_line=end_line))

    initial_commits = execute_git_blame(file_path, start_line, end_line)

    if not initial_commits:
        if not return_data:
            click.secho(__("⚠️ No traceable commits found in these lines."), fg="yellow")
        return [] if return_data else None

    if not return_data:
        click.secho(__("✅ Found {count} commit(s) on the surface. Starting time travel...\n", count=len(initial_commits)), fg="green")
    master_timeline = []
    seen_hashes = set()

    # DATA COLLECTION LOOP
    for base_commit in initial_commits:
        current_commit = base_commit
        depth = 0
        max_depth = 4  # Safety lock to avoid infinite loops in legacy code

        while depth < max_depth:
            # If we already analyzed this commit in another trail, don't waste a request
            if current_commit in seen_hashes:
                break

            seen_hashes.add(current_commit)
            info = get_commit_info(current_commit)
            ai_analysis = analyze_commit_with_ai(current_commit, file_path)

            status = str(ai_analysis.get("status", "ORIGIN")).upper()
            reason = str(ai_analysis.get("reason", ""))

            master_timeline.append({
                "hash": current_commit[:8],
                "info": info,
                "status": status,
                "reason": reason,
                "raw_date": info["date"]  # Used for sorting
            })

            if status == "ORIGIN":
                break

            # It's a refactoring, let's look for the parent commit in the past
            depth += 1
            parent_hash = f"{current_commit}^"
            parent_commits = execute_git_blame(file_path, start_line, end_line, parent_hash)

            if not parent_commits:
                break
            current_commit = parent_commits[0]

    # CHRONOLOGICAL SORTING (From oldest to newest)
    master_timeline.sort(key=lambda x: x["raw_date"])

    # Direct Return to AI
    if return_data:
        return master_timeline

    # VISUAL DISPLAY IN TERMINAL (SINGLE)
    click.secho(__("\n📜 Consolidated Rule History (Lines {start_line}-{end_line}):", start_line=start_line, end_line=end_line), fg="magenta", bold=True)
    
    for item in master_timeline:
        cor = "green" if item["status"] == "ORIGIN" else "yellow"
        icone = "👶" if item["status"] == "ORIGIN" else "🔧"
        
        click.secho(__("\n[{date}] {icon} {status}: By {author} (Commit: {hash})", date=item['info']['date'], icon=icone, status=__(item['status']), author=item['info']['author'], hash=item['hash']), fg=cor, bold=True)
        click.echo(__("   └─ Message: \"{message}\"", message=item['info']['message']))
        if item["reason"]:
            click.secho(__("   └─ AI Analysis: {reason}", reason=item['reason']), fg="cyan", dim=True)
            
    click.echo("\n" + "-"*60 + "\n")
    
    # MARKDOWN REPORT GENERATION (UNIFIED)
    click.secho(__("📝 Generating unified Markdown report with AI summary..."), fg="cyan")

    branch_name = get_current_branch()
    safe_branch_name = branch_name.replace("/", "-").replace("\\", "-")
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    pattern = os.getenv("OUTPUT_FILE_NAME_BLAME", "{branch}_{datetime}_BLAME_REPORT.md")
    output_filename = pattern.format(branch=safe_branch_name, datetime=current_time)

    # Build the Markdown Table
    md_content = __("# Timeline of the investigated rule\n\n")
    md_content += __("**File:** `{file_path}` (Lines {start_line}-{end_line})\n\n", file_path=file_path, start_line=start_line, end_line=end_line)
    md_content += __("| Data | Commit | Author | What |\n")
    md_content += "|---|---|---|---|\n"

    for item in master_timeline:
        data_fmt = item['info']['date']
        hash_curto = item['hash']
        autor = item['info']['author']
        msg_commit = item['info']['message']

        # Get AI explanation or use a safe fallback
        explicacao_ia = item['reason'] if item['reason'] else __("Change identified in the rule")

        # Combine AI explanation with commit message (Reference Table Style)
        reason_end = f"{explicacao_ia} — *\"{msg_commit}\"*"

        md_content += f"| {data_fmt} | `{hash_curto}` | {autor} | {reason_end} |\n"

    # AI generates the Final Analytical Summary
    summary_prompt = __("Based on the following commit timeline of a business rule, write a single paragraph summarizing the age of the rule, the original author, the number of refactorings, and deduce what the original business intention was (the real reason the rule exists in the system).\n\n")
    for item in master_timeline:
        summary_prompt += f"[{item['info']['date']}] {item['info']['author']} ({item['hash']}) - {item['status']}: {item['reason']}\n"

    provider = get_ai_provider()
    api_key = get_api_key(provider)
    api_model = get_api_model(provider, task_complexity="advanced")
    sys_inst = __('You are a Software Architect. Generate ONLY a JSON object in the format {"resumo": "summary text"}.')

    click.secho(__("  🤖 Consulting AI ({api_model}) for the Executive Summary...", api_model=api_model), fg="cyan", dim=True)
    summary_json = call_ai_model(provider, api_key, api_model, summary_prompt, sys_inst, action="blame_summary")

    resumo_texto = summary_json.get("resumo", __("Summary not available.")) if summary_json else __("Summary not available.")

    md_content += __("\n**Summary:** {summary}\n", summary=resumo_texto)

    # Save to disk
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(md_content)
        click.secho(__("✅ Unified report successfully saved: '{output_filename}'", output_filename=output_filename), fg="green", bold=True)
    except Exception as e:
        click.secho(__("❌ Error saving report: {error}", error=str(e)), fg="red")