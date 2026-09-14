import os
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path


def get_cache_base_dir():
    """Returns the ~/.gitpr/cache/prompts/ path."""
    path = Path.home() / ".gitpr" / "cache" / "prompts"
    return path


def generate_md5(text):
    """Generates the MD5 hash of a string."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_git_user_info():
    """Recupera o nome e email configurados no git local."""
    try:
        name = subprocess.run(
            ["git", "config", "user.name"], capture_output=True, text=True, check=True
        ).stdout.strip()
        email = subprocess.run(
            ["git", "config", "user.email"], capture_output=True, text=True, check=True
        ).stdout.strip()
        return name, email
    except subprocess.CalledProcessError:
        return "unknown", "unknown"


def get_cached_response(action_folder, prompt_text):
    """Checks if a valid cache exists for the prompt and returns the content."""
    md5_hash = generate_md5(prompt_text)
    cache_file = get_cache_base_dir() / action_folder / f"{md5_hash}.json"

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("response")
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_cached_response(
    action_folder, action_type, prompt_text, response_dict, meta_raw=None
):
    """Saves the AI response to the local cache."""
    md5_hash = generate_md5(prompt_text)
    folder_path = get_cache_base_dir() / action_folder
    folder_path.mkdir(parents=True, exist_ok=True)

    cache_file = folder_path / f"{md5_hash}.json"
    from src.core import get_current_branch, get_repo_name

    current_branch = get_current_branch()
    repo_name = get_repo_name()
    user_name, user_email = get_git_user_info()

    if meta_raw is not None:
        response_dict["meta_raw"] = meta_raw

    cache_data = {
        "md5": md5_hash,
        "repo": repo_name,
        "branch": current_branch,
        "author_name": user_name,
        "author_email": user_email,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action_type": action_type,
        "prompt": prompt_text,
        "response": response_dict,
    }

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except IOError:
        pass  # Silent cache failure to avoid crashing the tool


# Review action types whose prompt is a branch diff. `filereview` is left out
# on purpose: it audits a single file and has no diff to re-derive.
REVIEW_ACTION_TYPES = ("review", "fullreview")


def resolve_last_review(repo_name, branch_name):
    """The most recent cached review for *repo_name* and *branch_name*, or None.

    All three review modes write into the same ``review/`` folder (see
    ``core.generate_pr_content``), so ``action_type`` is what tells them apart —
    without that filter a file audit would be mistaken for a branch review.

    Returns the cache record itself: the caller reads
    ``record["response"]["review"]`` for the text and ``record["action_type"]``
    to know which diff produced it, so the patch can be re-derived against
    today's tree rather than the tree of the day the review ran.
    """
    review_folder = get_cache_base_dir() / "review"
    if not review_folder.exists():
        return None

    newest = None
    for cache_file in review_folder.glob("*.json"):
        try:
            with open(cache_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        if not isinstance(data, dict):
            continue
        if data.get("repo") != repo_name or data.get("branch") != branch_name:
            continue
        if data.get("action_type") not in REVIEW_ACTION_TYPES:
            continue
        if not (data.get("response") or {}).get("review"):
            continue

        # Timestamps are '%Y-%m-%d %H:%M:%S', so string order is date order.
        if newest is None or data.get("datetime", "") > newest.get("datetime", ""):
            newest = data

    return newest


def get_cached_pr_descriptions(repo_name, branch_name):
    """Searches the cache for all historically generated PRs for this repository and branch."""
    from src.i18n import __

    pr_cache_folder = get_cache_base_dir() / "pr_desc"
    history_texts = []

    if not pr_cache_folder.exists():
        return ""

    for cache_file in pr_cache_folder.glob("*.json"):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Filter by repository AND branch (avoids mixing different projects)
                if data.get("repo") == repo_name and data.get("branch") == branch_name:
                    response_dict = data.get("response", {})
                    pr_desc = response_dict.get("pr_description")
                    if pr_desc:
                        date_str = data.get("datetime", __("Unknown date"))
                        history_texts.append(f"[{date_str}]\n{pr_desc}\n")
        except (json.JSONDecodeError, IOError):
            continue

    if history_texts:
        # Sort chronologically (using the date extracted from the bracket)
        history_texts.sort()
        return __("=== AI PR HISTORY ===\n") + "\n".join(history_texts)

    return ""
