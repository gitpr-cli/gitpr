import os
import re
import json
import stat
import time
import fnmatch
import click
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from google import genai
from dotenv import load_dotenv, set_key
from src.security import decrypt_data
from src.cache import get_cached_response, save_cached_response, get_cached_pr_descriptions
from src.config import get_api_key, get_api_model, get_skill_dir, resolve_skill_path, get_ai_provider, setup_environment, ENV_FILE
from src.ai_providers import call_ai_model
from src.i18n import __, CURRENT_LANG
from src.updater import __lang_version__, __scripts_version__
# Metrics are imported lazily inside generate_pr_content() to avoid circular imports

# Smart Diff filter: files that consume AI tokens without adding semantic value.
# The pattern list is managed remotely (templates/gitpr.smart-excludes.json) and
# cached at ~/.gitpr/conf/ — see _load_smart_excludes() for the update logic.
_FALLBACK_SMART_EXCLUDES = [
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "composer.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Gemfile.lock",
    "go.sum",
    "*.min.js",
    "*.min.css",
    "*.svg"
]

SMART_EXCLUDES_URL = "https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/gitpr.smart-excludes.json"

# Documentation file extensions excluded from AI diffs to avoid wasting tokens
# on prose/markup. Changed doc paths are still reported as metadata.
# The pattern list is managed remotely (templates/gitpr.docs-smart-excludes.json).
_FALLBACK_DOCS_SMART_EXCLUDES = [
    "*.md", "*.txt", "*.rst", "*.adoc", "*.asciidoc",
    "*.org", "*.textile", "*.wiki", "*.pod", "*.tex",
    "*.rtf", "*.markdown", "*.rdoc", "*.mdx", "*.rest",
    "*.man", "*.1", "*.2", "*.3", "*.4", "*.5", "*.6", "*.7", "*.8",
]

DOCS_SMART_EXCLUDES_URL = "https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/gitpr.docs-smart-excludes.json"

# Hook scripts: language suffixes with shipped translations.
# English is the default (no suffix) — fallback for any language not listed here.
_SCRIPT_LANG_SUFFIXES = {"pt_br", "pt_pt", "fr", "es"}
SCRIPTS_BASE_URL = "https://raw.githubusercontent.com/natanfiuza/gitpr/main/scripts/"


def _seed_local_smart_excludes(project_root=None):
    """
    Create a template local smart-excludes file in the project's .gitpr/conf/ directory.

    The file starts with an empty exclude list and a comment explaining its purpose.
    Merged with the global list at load time — project-specific exclusions only.
    Only creates the file if it does NOT already exist (never overwrites user config).
    """
    try:
        root = Path(project_root) if project_root else Path.cwd()
        local_dir = root / ".gitpr" / "conf"
        local_file = local_dir / "gitpr.smart-excludes.json"
        if not local_file.exists():
            local_dir.mkdir(parents=True, exist_ok=True)
            template = {
                "_comment": (
                    "Project-specific Smart Excludes. "
                    "Merged with the global list (~/.gitpr/conf/gitpr.smart-excludes.json) at runtime. "
                    "Add extensions or folder names to exclude from AI diffs for this project only. "
                    "Example: \"*.pyc\", \"dist/\", \"node_modules/\""
                ),
                "excludes": []
            }
            with open(local_file, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Best-effort — never block the main flow for file seeding


def _load_smart_excludes():
    """
    Load the smart-exclude patterns and return them as git pathspec exclusions.

    Resolution order:
    1. Local copy at ~/.gitpr/conf/gitpr.smart-excludes.json when its version
       marker (SMART_EXCLUDES_VERSION in ~/.gitpr/.env) matches __lang_version__.
    2. Fresh download from the remote template (saved locally + marker updated).
    3. Stale local copy when the download fails.
    4. _FALLBACK_SMART_EXCLUDES as last resort.
    5. Project-local file at ./.gitpr/conf/gitpr.smart-excludes.json (merged on top).

    The global and project-local lists are merged (union) at the end.
    Silent on failure — diff generation must never break because of this list.

    Env vars:
      GITPR_SKIP_SMART_EXCLUDES  — set to "1"/"true" to disable all smart excludes
      GITPR_SMART_EXCLUDES_GLOBAL — override path to the global excludes file
      GITPR_SMART_EXCLUDES_LOCAL  — override path to the project-local excludes file
    """
    # --- Global skip switch ---
    if os.getenv("GITPR_SKIP_SMART_EXCLUDES", "").lower() in ("1", "true", "yes"):
        return []

    env_file = Path.home() / ".gitpr" / ".env"
    load_dotenv(env_file)

    # Resolve global file path (env override or default)
    global_path_override = os.getenv("GITPR_SMART_EXCLUDES_GLOBAL")
    if global_path_override:
        global_file = Path(global_path_override)
        conf_dir = global_file.parent
    else:
        conf_dir = Path.home() / ".gitpr" / "conf"
        global_file = conf_dir / "gitpr.smart-excludes.json"

    needs_update = os.getenv("SMART_EXCLUDES_VERSION") != __lang_version__

    def _to_pathspecs(data):
        return [f":(exclude){pattern}" for pattern in data.get("excludes", [])]

    def _load_patterns_set(path):
        """Load exclude patterns from a JSON file and return them as a set."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return set(json.load(f).get("excludes", []))
        except Exception:
            return set()

    # 1. Local copy is present and up to date
    if global_file.exists() and not needs_update:
        try:
            with open(global_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except Exception:
            data = None
    else:
        data = None

    # 2. Download the updated list from the remote template
    if data is None:
        try:
            with urllib.request.urlopen(SMART_EXCLUDES_URL, timeout=3) as response:
                data = json.loads(response.read().decode("utf-8"))
            conf_dir.mkdir(parents=True, exist_ok=True)
            with open(global_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            set_key(str(env_file), "SMART_EXCLUDES_VERSION", __lang_version__)
            # Seed the local project file as a convenience (idempotent)
            _seed_local_smart_excludes()
        except Exception:
            pass

    # 3. Offline fallback: reuse the local copy even if outdated
    if data is None and global_file.exists():
        try:
            with open(global_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except Exception:
            pass

    # 4. Last resort: built-in defaults
    if data is None:
        global_pathspecs = [f":(exclude){p}" for p in _FALLBACK_SMART_EXCLUDES]
    else:
        global_pathspecs = _to_pathspecs(data)

    # --- 5. Load and merge project-local exclusions ---
    local_path_override = os.getenv("GITPR_SMART_EXCLUDES_LOCAL")
    if local_path_override:
        local_file = Path(local_path_override)
    else:
        local_file = Path(".gitpr") / "conf" / "gitpr.smart-excludes.json"

    if local_file.exists():
        local_set = _load_patterns_set(local_file)
        if local_set:
            # Build a set from global pathspecs for dedup, then merge
            global_set = set(
                p.replace(":(exclude)", "", 1) for p in global_pathspecs
            )
            merged = sorted(global_set | local_set)
            global_pathspecs = [f":(exclude){p}" for p in merged]
    else:
        local_set = set()

    return global_pathspecs


def _load_docs_smart_excludes():
    """
    Load the doc-smart-exclude patterns and return them as git pathspec exclusions.

    Resolution order (same as _load_smart_excludes, shares SMART_EXCLUDES_VERSION):
    1. Local copy at ~/.gitpr/conf/gitpr.docs-smart-excludes.json when up to date.
    2. Fresh download from the remote template (saved locally).
    3. Stale local copy when the download fails.
    4. _FALLBACK_DOCS_SMART_EXCLUDES as last resort.

    Also respects GITPR_SKIP_SMART_EXCLUDES — returns empty list when set.
    """
    # --- Global skip switch ---
    if os.getenv("GITPR_SKIP_SMART_EXCLUDES", "").lower() in ("1", "true", "yes"):
        return []

    env_file = Path.home() / ".gitpr" / ".env"
    load_dotenv(env_file)

    conf_dir = Path.home() / ".gitpr" / "conf"
    local_file = conf_dir / "gitpr.docs-smart-excludes.json"
    needs_update = os.getenv("SMART_EXCLUDES_VERSION") != __lang_version__

    def _to_pathspecs(data):
        return [f":(exclude){pattern}" for pattern in data.get("excludes", [])]

    # 1. Local copy is present and up to date
    if local_file.exists() and not needs_update:
        try:
            with open(local_file, "r", encoding="utf-8", errors="replace") as f:
                return _to_pathspecs(json.load(f))
        except Exception:
            pass

    # 2. Download the updated list from the remote template
    try:
        with urllib.request.urlopen(DOCS_SMART_EXCLUDES_URL, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        conf_dir.mkdir(parents=True, exist_ok=True)
        with open(local_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        set_key(str(env_file), "SMART_EXCLUDES_VERSION", __lang_version__)
        return _to_pathspecs(data)
    except Exception:
        pass

    # 3. Offline fallback: reuse the local copy even if outdated
    if local_file.exists():
        try:
            with open(local_file, "r", encoding="utf-8", errors="replace") as f:
                return _to_pathspecs(json.load(f))
        except Exception:
            pass

    # 4. Last resort: built-in defaults
    return [f":(exclude){pattern}" for pattern in _FALLBACK_DOCS_SMART_EXCLUDES]


SMART_EXCLUDES = _load_smart_excludes() + _load_docs_smart_excludes()


def _get_raw_docs_patterns():
    """
    Returns raw glob patterns for documentation extensions (e.g. ['*.md', '*.txt']).

    Uses the same resolution chain as _load_docs_smart_excludes but returns
    plain patterns without the :(exclude) prefix — suitable for fnmatch filtering.
    """
    env_file = Path.home() / ".gitpr" / ".env"
    load_dotenv(env_file)

    conf_dir = Path.home() / ".gitpr" / "conf"
    local_file = conf_dir / "gitpr.docs-smart-excludes.json"
    needs_update = os.getenv("SMART_EXCLUDES_VERSION") != __lang_version__

    # 1. Local copy is present and up to date
    if local_file.exists() and not needs_update:
        try:
            with open(local_file, "r", encoding="utf-8", errors="replace") as f:
                return json.load(f).get("excludes", [])
        except Exception:
            pass

    # 2. Download
    try:
        with urllib.request.urlopen(DOCS_SMART_EXCLUDES_URL, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        conf_dir.mkdir(parents=True, exist_ok=True)
        with open(local_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        set_key(str(env_file), "SMART_EXCLUDES_VERSION", __lang_version__)
        return data.get("excludes", [])
    except Exception:
        pass

    # 3. Stale local copy
    if local_file.exists():
        try:
            with open(local_file, "r", encoding="utf-8", errors="replace") as f:
                return json.load(f).get("excludes", [])
        except Exception:
            pass

    # 4. Fallback
    return list(_FALLBACK_DOCS_SMART_EXCLUDES)


def get_changed_docs_list(ancestor_hash=None):
    """
    Returns a list of changed documentation file paths (names only, no content).

    Runs ``git diff --name-only`` and filters by the documentation extensions
    defined in gitpr.docs-smart-excludes.json.  This lets the AI know which
    docs were touched without consuming tokens with their full content.

    Args:
        ancestor_hash: Optional merge-base hash for full-diff mode.
                       When None, diffs against HEAD (local mode).
    """
    raw_patterns = _get_raw_docs_patterns()
    if not raw_patterns:
        return []

    try:
        if ancestor_hash:
            cmd = ["git", "diff", "--name-only", ancestor_hash, "--"]
        else:
            cmd = ["git", "diff", "--name-only", "HEAD", "--"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )

        all_files = result.stdout.splitlines()
        doc_files = []
        for f in all_files:
            if not f.strip():
                continue
            for pattern in raw_patterns:
                if fnmatch.fnmatch(f, pattern):
                    doc_files.append(f)
                    break

        return doc_files
    except Exception:
        return []


# Mapping from env var to subfolder inside .gitpr/reports/
_OUTPUT_FOLDER_MAP = {
    "OUTPUT_FILE_NAME": "pr_desc",
    "OUTPUT_FILE_NAME_REVIEW": "review",
    "OUTPUT_FILE_NAME_FULLREVIEW": "full_review",
    "OUTPUT_FILE_NAME_FILEREVIEW": "file_review",
    "OUTPUT_FILE_NAME_BLAME": "blame",
    "OUTPUT_FILE_NAME_ISSUE": "issue",
    "OUTPUT_FILE_NAME_LINTER": "linter",
}


def resolve_output_path(env_var, default_pattern, safe_branch_name, current_time):
    """
    Resolve the output file path for a given action.

    Behaviour (per the plan):
    - If the env-var value contains a directory separator (``/`` or ``\\``),
      use it as-is → backwards-compatible with user-configured custom paths.
    - If it contains only a filename (no slash), prepend
      ``.gitpr/reports/<folder>/`` so generated artefacts stay out of the
      project root.
    - If the env var is empty / not set, use *default_pattern* and place it
      inside ``.gitpr/reports/<folder>/``.

    Returns the final *relative* path (ready to pass to ``open()``).
    """
    raw = os.getenv(env_var, "")
    pattern = raw.strip() if raw else default_pattern
    filename = pattern.format(branch=safe_branch_name, datetime=current_time)

    # Already contains a directory — honour the user's custom path as-is
    if "/" in pattern or "\\" in pattern:
        return filename

    # Plain filename → place it inside .gitpr/reports/<folder>/
    folder = _OUTPUT_FOLDER_MAP.get(env_var, "misc")
    reports_dir = os.path.join(os.getcwd(), ".gitpr", "reports", folder)
    os.makedirs(reports_dir, exist_ok=True)

    return os.path.join(reports_dir, filename)


def get_doc_url(filename):
    """Returns the complete URL for the official GitPR documentation website.

    Transforms a docs/ filename like 'commit-message-ia.md' into a clean website
    URL with language query parameter. English is the site default (no ?lang=).

    Examples:
        get_doc_url("untracked-files.md")  -> "https://gitpr.natanfiuza.dev.br/docs/untracked-files"
        get_doc_url("untracked-files.md")  -> "https://gitpr.natanfiuza.dev.br/docs/untracked-files?lang=pt_br"  (when CURRENT_LANG is pt_br)
    """
    base, _ = filename.rsplit(".", 1)
    url = f"https://gitpr.natanfiuza.dev.br/docs/{base}"
    if not CURRENT_LANG.startswith("en"):
        url += f"?lang={CURRENT_LANG}"
    return url


def get_git_diff(quiet=False):
    """Runs 'git diff HEAD' and returns the output, warning about untracked files."""
    try:
        # Check if there are new untracked files
        untracked_process = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        untracked_files = untracked_process.stdout.strip()

        # If there are new files, display an educational warning in the console
        if untracked_files and not quiet:
            click.secho(__("⚠️ Warning: Git detected new untracked files:"), fg="yellow")
            for file in untracked_files.split('\n'):
                click.secho(f"  - {file}", fg="yellow", dim=True)
            click.secho(__("💡 Tip: Use 'git add <file>' to include them in the GitPR analysis."), fg="cyan")
            click.secho(f"📚 {__('Understand why:')} {get_doc_url('untracked-files.md')}\n", fg="blue", underline=True)

        # Run the normal diff that captures tracked and staged files
        cmd = ["git", "diff", "-U1", "-w", "-M", "-B", "HEAD", "--"] + SMART_EXCLUDES
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        if not quiet:
            click.secho(__("❌ Error running Git: {error}", error=e.stderr), fg="red")
        return None
    except FileNotFoundError:
        if not quiet:
            click.secho(__("❌ Git not found. Make sure it is installed and in the PATH."), fg="red")
        return None


def is_merge_in_progress():
    """Returns True when a merge is in progress (MERGE_HEAD exists).

    Used to skip AI commit-message generation for merge commits
    (git pull, git merge, conflicted-merge finalization), where the
    message must come from git, not from AI.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode == 0
    except Exception:
        return False  # git missing/unavailable — never block the commit


def get_unstaged_diff(quiet=False):
    """Runs 'git diff' (index vs working tree) — returns ONLY unstaged changes,
    excluding staged ones. Untracked files are never shown by git diff.

    Unlike get_git_diff() which uses 'git diff HEAD' (includes staged+unstaged),
    this command compares the index (staging area) against the working tree.
    """
    try:
        cmd = ["git", "diff", "-U1", "-w", "-M", "-B", "--"] + SMART_EXCLUDES
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        if not quiet:
            click.secho(__("❌ Error running Git: {error}", error=e.stderr), fg="red")
        return None
    except FileNotFoundError:
        if not quiet:
            click.secho(__("❌ Git not found. Make sure it is installed and in the PATH."), fg="red")
        return None


def get_current_branch():
    """Returns the current branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "main" # Fallback


def get_repo_name():
    """Extracts the owner/repo name from git remote origin."""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        match = re.search(r'github\.com[:/](.+?)/(.+?)(\.git)?\s+\(push\)', result.stdout)
        if match:
            owner = match.group(1)
            repo = match.group(2).replace('.git', '')
            return f"{owner}/{repo}"
        return "unknown/repo"
    except subprocess.CalledProcessError:
        return "unknown/repo"


def get_skill_context(action_type="pr"):
    """Reads the correct context file based on the action (PR/Commit or Review)."""

    # Define which file to look for
    if action_type == "commit":
        target_file = ".gitpr.commit.md"
    elif action_type == "pr":
        target_file = ".gitpr.pr.md"
    elif action_type == "filereview":  # NEW!
        target_file = ".gitpr.filereview.md"
    elif action_type == "issue":
        target_file = ".gitpr.issue.md"
    else:  # review or fullreview
        target_file = ".gitpr.review.md"

    skill_file = resolve_skill_path(target_file)

    # Fallback to the old file (for backward compatibility with previous version users)
    legacy_file = resolve_skill_path(".gitpr.md")

    # Check the new one first; if not found, try the old one
    file_to_load = skill_file if os.path.exists(skill_file) else (legacy_file if os.path.exists(legacy_file) else None)

    if file_to_load:
        try:
            with open(file_to_load, "r", encoding="utf-8") as f:
                conteudo = f.read()
                nome_arquivo = os.path.basename(file_to_load)
                click.secho(__("🧠 File {file_name} (Skill) found and loaded!", file_name=nome_arquivo), fg="blue")
                return conteudo
        except Exception as e:
            click.secho(__("⚠️ Warning: Failed to read file {file_name} ({error})", file_name=nome_arquivo, error=str(e)), fg="yellow")

    # Return empty if it does not exist
    return ""

def estimate_token_count(text):
    """Estimates the token count using the safe rule of 4 characters per token."""
    return len(text) // 4

def split_diff_into_chunks(diff_text, max_tokens=90000):
    """Splits the diff based on the token limit while preserving file header integrity."""
    if estimate_token_count(diff_text) <= max_tokens:
        return [diff_text]
    
    parts = re.split(r'(^diff --git a/)', diff_text, flags=re.MULTILINE)
    chunks = []
    current_chunk = ""
    
    for i in range(1, len(parts), 2):
        file_diff = parts[i] + parts[i+1] if i + 1 < len(parts) else parts[i]
        
        if estimate_token_count(current_chunk + file_diff) > max_tokens and current_chunk:
            chunks.append(current_chunk)
            current_chunk = file_diff
        else:
            current_chunk += file_diff
            
    if current_chunk:
        chunks.append(current_chunk)
        
    if not chunks:
        chunks = [diff_text]
        
    return chunks

def generate_pr_content(action_folder, action_type, diff_text, provider="gemini"):
    """Sends the diff to the AI using System Instruction and returns a parsed JSON."""
    if not diff_text or not diff_text.strip():
        click.secho(__("⚠️ No diff found. Make some changes before running the command."), fg="yellow")
        return None

    t_start = time.perf_counter()

    # Cache folder configuration
    action_folder_map = {
        "pr": "pr_desc",
        "commit": "commit",
        "review": "review",
        "fullreview": "review",
        "filereview": "review",
    }
    action_folder = action_folder_map.get(action_type, "misc")

    # Fetch the context from the file corresponding to the action (PR, Commit, or Review)
    skill_context = get_skill_context(action_type)

    # Task Complexity Definition (NEW)
    # Commits use faster/cheaper models. Reviews and PRs use advanced models.
    task_complexity = "simple" if action_type == "commit" else "advanced"

    # System Instruction Definition (Persona and Rules)
    if action_type == "commit":
        instrucao_sistema = skill_context if skill_context else __("You are a Git expert. Generate concise commit messages.")
        prompt = __("Generate ONLY a JSON object in the format {json_format} for this diff:\n", json_format='{"commit_message": "..."}') + f"{diff_text}"

    elif action_type in ["review", "fullreview", "filereview"]:
        instrucao_sistema = skill_context if skill_context else __("You are a Senior Software Architect. Focus on pointing out improvements.")

        if action_type == "filereview":
            prompt = __("Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n", json_format='{"review": "..."}') + f"{diff_text}"
        else:
            prompt = __("Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n", json_format='{"review": "..."}') + f"{diff_text}"
    else:  # pr
        instrucao_sistema = skill_context if skill_context else __("You are a Tech Lead writing clean and technical PR descriptions.")
        prompt = __("Generate ONLY a JSON object in the format {json_format} for this diff:\n", json_format='{"commit_message": "...", "pr_description": "..."}') + f"{diff_text}"

    # ── Inject changed documentation file list as metadata (no content) ──
    # This lets the AI know which docs were touched without consuming tokens
    # on their full prose/markup content (they are excluded from the diff).
    try:
        if action_type in ("pr", "fullreview"):
            # Full diff: compute merge-base to match the diff scope
            base_branch = get_base_branch()
            merge_base_res = subprocess.run(
                ["git", "merge-base", f"origin/{base_branch}", "HEAD"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if merge_base_res.returncode == 0 and merge_base_res.stdout.strip():
                ancestor = merge_base_res.stdout.strip()
            else:
                ancestor = None
            changed_docs = get_changed_docs_list(ancestor)
        else:
            # Local diff: compare against HEAD
            changed_docs = get_changed_docs_list()

        if changed_docs:
            docs_section = __("Changed documentation (content excluded from diff):\n")
            for doc in changed_docs:
                docs_section += f"- {doc}\n"
            instrucao_sistema = docs_section + "\n" + instrucao_sistema
            click.secho(
                __("📄 {count} documentation file(s) excluded from diff (Smart Excludes).",
                   count=len(changed_docs)),
                fg="blue", dim=True,
            )
            click.secho(
                f"📚 {__('Learn more:')} {get_doc_url('smart-excludes.md')}",
                fg="blue", underline=True,
            )
    except Exception:
        pass  # Non-critical — never block the main flow for this metadata

    # TRY TO RETRIEVE FROM CACHE
    cached_data = get_cached_response(action_folder, prompt)
    if cached_data:
        click.secho(__("⚡ Response retrieved from local cache."), fg="green", dim=True)
        from src.metrics import log_command_metric
        duration_ms = int((time.perf_counter() - t_start) * 1000)
        log_command_metric(
            command=action_type,
            status="success",
            provider=provider,
            duration_ms=duration_ms,
            cache_hit=True,
        )
        return cached_data

    # Key Preparation (Now dynamic per Provider)
    api_key = get_api_key(provider)
    if not api_key:
        click.secho(__("❌ Error: API Key for provider '{provider}' not found.", provider=provider.capitalize()), fg="red")
        return None

    # Fetch the Smart Model (NEW)
    # Send complexity to config.py to return the primary or secondary model
    api_model = get_api_model(provider, task_complexity)
    if not api_model:
        click.secho(__("❌ Error: Could not determine model for provider '{provider}'.", provider=provider), fg="red")
        return None

    # API CALL
    click.secho(__("🤖 GitPR is analyzing your code using {provider} ({model})...\n", provider=provider.capitalize(), model=api_model), fg="cyan")
    
    chunks = split_diff_into_chunks(diff_text, max_tokens=90000)
    total_meta = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "duration_ms": 0}

    def _aggregate_meta(new_meta):
        if new_meta:
            total_meta["prompt_tokens"] += new_meta.get("prompt_tokens", 0)
            total_meta["completion_tokens"] += new_meta.get("completion_tokens", 0)
            total_meta["total_tokens"] += new_meta.get("total_tokens", 0)
            total_meta["duration_ms"] += new_meta.get("duration_ms", 0)
            
    if len(chunks) == 1:
        result_json = call_ai_model(provider, api_key, api_model, prompt, instrucao_sistema, action=action_folder)
        if result_json:
            _aggregate_meta(result_json.pop("_telemetry_meta", None))
    else:
        from src.metrics import log_local_metric
        log_local_metric(command="map_reduce", status="triggered", map_reduce_triggered=True, chunks_count=len(chunks))
        
        click.secho(__("📦 Huge diff detected! Processing in {count} batches (Map-Reduce)...", count=len(chunks)), fg="yellow", bold=True)
        click.secho(f"📚 {__('Understand why:')} {get_doc_url('map-reduce-diff.md')}\n", fg="blue", underline=True)
        resumos_parciais = []

        for i, chunk in enumerate(chunks, 1):
            click.secho(__("⏳ Analyzing batch {current}/{total}...", current=i, total=len(chunks)), fg="cyan", dim=True)

            prompt_parcial = __("Generate ONLY a JSON object in the format {json_format} containing a technical summary of what was changed in this part ({idx}) of the diff:\n", json_format='{"resumo": "..."}', idx=i) + chunk

            resposta_parcial = call_ai_model(provider, api_key, api_model, prompt_parcial, instrucao_sistema, quiet=True, action=f"{action_folder}_chunk_{i}")
            
            if resposta_parcial:
                _aggregate_meta(resposta_parcial.pop("_telemetry_meta", None))
                if "resumo" in resposta_parcial:
                    resumos_parciais.append(f"### Batch {i}\n{resposta_parcial['resumo']}")
            
            time.sleep(1)
            
        if not resumos_parciais:
            click.secho(__("❌ Failed to extract context from the partial batches."), fg="red")
            return None

        click.secho(__("🔄 Unifying intelligence and generating the final analysis..."), fg="yellow")
        diff_unificado = "\n\n".join(resumos_parciais)

        if action_type == "commit":
            prompt = __("Generate ONLY a JSON object in the format {json_format} for the commit message, unifying these technical summaries:\n", json_format='{"commit_message": "..."}') + diff_unificado
        elif action_type in ["review", "fullreview", "filereview"]:
            prompt = __("Generate ONLY a JSON object in the format {json_format} with a code review focused on improvements, using these summaries:\n", json_format='{"review": "..."}') + diff_unificado
        else:
            prompt = __("Unify these technical summaries and generate ONLY a JSON object in the format {json_format} describing the Pull Request:\n", json_format='{"commit_message": "...", "pr_description": "..."}') + diff_unificado
            
        result_json = call_ai_model(provider, api_key, api_model, prompt, instrucao_sistema, action=action_folder)
        if result_json:
            _aggregate_meta(result_json.pop("_telemetry_meta", None))

    # SAVE TO CACHE AND RETURN
    if result_json:
        save_cached_response(action_folder, action_type, prompt, result_json, meta_raw=total_meta)
        # Fire-and-forget metric for successful AI-powered command
        from src.metrics import log_command_metric
        duration_ms = int((time.perf_counter() - t_start) * 1000)
        log_command_metric(
            command=action_type,
            status="success",
            provider=provider,
            tokens_estimated=total_meta.get("total_tokens", 0),
            duration_ms=duration_ms,
            map_reduce_triggered=(len(chunks) > 1),
        )
        return result_json

    # Command failed (AI returned None)
    from src.metrics import log_command_metric
    duration_ms = int((time.perf_counter() - t_start) * 1000)
    log_command_metric(command=action_type, status="error", provider=provider, duration_ms=duration_ms)
    return None


def generate_skill_template():
    """
    Downloads templates directly from the official repository.
    Now dynamically supports languages.
    """
    click.secho(__("\n📥 Starting GitPR templates configuration..."), fg="cyan", bold=True)
    
    base_url = "https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/"
    
    # Language logic:
    # - English (en) = original file without suffix (e.g.: gitpr.issue.md)
    # - Other languages = file with suffix (e.g.: gitpr.issue.pt_br.md)
    # - Linter and thinking-words are language-independent
    if CURRENT_LANG.startswith("en"):
        lang_suffix = ""  # english is the default, no suffix
    else:
        lang_suffix = f".{CURRENT_LANG}"  # e.g.: .pt_br

    files_to_download = {
        ".gitpr.commit.md": f"gitpr.commit{lang_suffix}.md",
        ".gitpr.pr.md": f"gitpr.pr{lang_suffix}.md",
        ".gitpr.review.md": f"gitpr.review{lang_suffix}.md",
        ".gitpr.linter.yml": f"gitpr.linter{lang_suffix}.yml",
        ".gitpr.filereview.md": f"gitpr.filereview{lang_suffix}.md",
        ".gitpr.blame.md": f"gitpr.blame{lang_suffix}.md",
        ".gitpr.issue.md": f"gitpr.issue{lang_suffix}.md",
    }
    
    success_count = 0

    # Templates now live inside the project's .gitpr/skill/ folder
    skill_dir = get_skill_dir()
    os.makedirs(skill_dir, exist_ok=True)

    for local_name, remote_name in files_to_download.items():
        # Migrate any legacy root file into .gitpr/skill/ and resolve final path
        file_path = resolve_skill_path(local_name)
        url = base_url + remote_name

        if os.path.exists(file_path):
            click.secho(__("⚠️ File {local_name} already exists in this directory. It will not be overwritten.", local_name=local_name), fg="yellow")
            continue
            
        try:
            click.echo(__("Downloading {local_name}...", local_name=local_name))
            with urllib.request.urlopen(url, timeout=5) as response:
                content = response.read().decode('utf-8')
                
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            success_count += 1
            
        except urllib.error.URLError as e:
            click.secho(__("❌ Network error while downloading {local_name}: {error}", local_name=local_name, error=e.reason), fg="red")
        except Exception as e:
            click.secho(__("❌ Failed to process {local_name}: {error}", local_name=local_name, error=str(e)), fg="red")

    if success_count > 0:
        click.secho(__("\n✅ Base templates successfully configured!"), fg="green", bold=True)
        click.echo(__("You can now open the generated files in '.gitpr/skill/' and customize the tool's behavior for your project:\n"))
        click.echo(__("  1. Architecture rules for AI in '.gitpr/skill/.gitpr.pr.md' and '.gitpr/skill/.gitpr.review.md'\n"))
        click.echo(__("  2. Local regex rules in '.gitpr/skill/.gitpr.linter.yml'\n"))
    else:
        click.echo(__("\nNo new files were downloaded."))


def get_base_branch():
    """Discovers the remote main branch (e.g.: main or master)."""
    try:
        # Fetch the default branch reference from the remote
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True, text=True, check=True
        )
        # The return is something like 'refs/remotes/origin/main', so we get the last part
        return result.stdout.strip().split('/')[-1]
    except subprocess.CalledProcessError:
        click.secho(__("⚠️ Warning: Remote main branch not detected. Assuming 'main' as default fallback."), fg="yellow")
        return "main"  # Default fallback if not found


def get_git_full_diff():
    """Fetches and captures the diff between the remote main branch and the current state."""
    click.secho(__("🔄 Synchronizing with remote repository (git fetch)..."), fg="cyan")
    try:
        # Fetch to ensure we know where origin/main is
        subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
        
        base_branch = get_base_branch()
        
        # Find the commit HASH where your branch was born (the common ancestor)
        merge_base_res = subprocess.run(
            ["git", "merge-base", f"origin/{base_branch}", "HEAD"],
            capture_output=True, text=True, check=True
        )
        ancestor_hash = merge_base_res.stdout.strip()

        # Diff between that HASH and your CURRENT WORKSPACE (without using HEAD)
        # By passing only the hash, Git compares that commit with the files on your disk.
        cmd = ["git", "diff", "-U1", "-w", "-M", "-B", ancestor_hash, "--"] + SMART_EXCLUDES
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding="utf-8",
            check=True
        )
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        click.secho(__("❌ Error calculating diff: {error}", error=e.stderr), fg="red")
        return None
    
def install_git_hooks():
    """Downloads and installs Git hook scripts with i18n support.

    Detects the current language (CURRENT_LANG) and tries to download
    language-specific scripts first (e.g. pre-commit-template.pt_br.sh).
    Falls back to the English base version when a translation is unavailable.

    After a successful install, stamps SCRIPTS_VERSION and SCRIPTS_LANG
    in ~/.gitpr/.env so the auto-sync check can skip network calls.
    """
    hooks_dir = os.path.join(os.getcwd(), ".git", "hooks")

    if not os.path.exists(hooks_dir):
        click.secho(__("❌ Error: .git folder not found. Run at the project root."), fg="red")
        return False

    # Build language suffix (e.g. ".pt_br", ".fr") — English = no suffix
    lang_suffix = ""
    if CURRENT_LANG in _SCRIPT_LANG_SUFFIXES:
        lang_suffix = f".{CURRENT_LANG}"

    # Mapping: Hook Name in Git -> Template Name on GitHub
    hooks_to_install = {
        "pre-commit": "pre-commit-template.sh",
        "prepare-commit-msg": "prepare-commit-msg-template.sh",
        "post-checkout": "post-checkout-template.sh",
        "pre-push": "pre-push-template.sh",
        "post-merge": "post-merge-template.sh",
    }

    success_count = 0

    for hook_name, template_name in hooks_to_install.items():
        hook_path = os.path.join(hooks_dir, hook_name)

        # Try language-specific URL first, fall back to base (English)
        urls_to_try = []
        if lang_suffix:
            # Insert suffix before .sh: "pre-commit-template" + ".pt_br" + ".sh"
            base_name = template_name[:-3]  # strip .sh
            urls_to_try.append(f"{SCRIPTS_BASE_URL}{base_name}{lang_suffix}.sh")
        urls_to_try.append(f"{SCRIPTS_BASE_URL}{template_name}")

        downloaded = False
        for url in urls_to_try:
            try:
                click.secho(__("📥 Downloading {hook_name}...", hook_name=hook_name), fg="cyan")

                with urllib.request.urlopen(url) as response:
                    content = response.read().decode('utf-8')

                with open(hook_path, "w", encoding="utf-8") as f:
                    f.write(content)

                # Apply execution permission (chmod +x)
                st = os.stat(hook_path)
                os.chmod(hook_path, st.st_mode | stat.S_IEXEC)

                success_count += 1
                downloaded = True
                break  # success — skip fallback URLs
            except urllib.error.HTTPError as e:
                # 404 on language variant is expected — silently try fallback
                if e.code == 404 and url != urls_to_try[-1]:
                    continue
                click.secho(__("⚠️ Failed to install {hook_name}: HTTP {code}", hook_name=hook_name, code=e.code), fg="yellow")
            except Exception as e:
                click.secho(__("⚠️ Failed to install {hook_name}: {error}", hook_name=hook_name, error=str(e)), fg="yellow")

        # If the first URL (language-specific) failed and we're about to try the fallback,
        # the loop continues naturally. If the last URL also fails, we just move on.

    # Only stamp the version marker when ALL hooks installed successfully,
    # so a partial failure is retried on the next run.
    if success_count == len(hooks_to_install):
        try:
            os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)
            set_key(ENV_FILE, "SCRIPTS_VERSION", __scripts_version__)
            set_key(ENV_FILE, "SCRIPTS_LANG", lang_suffix.lstrip("."))
        except Exception:
            pass  # non-fatal — will retry next run

    if success_count == len(hooks_to_install):
        click.secho(f"📚 {__('Documentation:')} {get_doc_url('hooks-versioning.md')}", fg="blue", underline=True)

    return success_count == len(hooks_to_install)


def check_and_update_hooks_scripts():
    """Silent auto-sync of installed Git hooks (version + language gated).

    Called on every gitpr execution.  Compares SCRIPPS_VERSION and
    SCRIPPS_LANG in ~/.gitpr/.env against the shipped constants.  When
    they match the check is a single .env read with no network I/O.

    When they differ (or are missing) and the current project has a
    .git/hooks directory, hooks are re-downloaded in the current language.
    On success the markers are stamped so future runs skip the network.
    """
    # Fast path: version + language already match (pure .env read, no network)
    load_dotenv(ENV_FILE)
    env_version = os.getenv("SCRIPTS_VERSION")
    env_lang = os.getenv("SCRIPTS_LANG", "")

    # Compute expected language suffix (empty for English / unsupported langs)
    expected_lang = CURRENT_LANG if CURRENT_LANG in _SCRIPT_LANG_SUFFIXES else ""

    if env_version == __scripts_version__ and env_lang == expected_lang:
        return  # up to date — nothing to do

    # Only sync projects that actually have hooks installed (or could have them)
    hooks_dir = os.path.join(os.getcwd(), ".git", "hooks")
    if not os.path.exists(hooks_dir):
        return  # not a git project or no hooks dir — keep gate open (don't stamp)

    # Versions differ or missing → re-download
    click.secho(__("🔍 Checking hook scripts version..."), fg="cyan", dim=True)
    click.secho(__("   Current: {current} (from .env)", current=env_version or __("none")), fg="white", dim=True)
    click.secho(__("   Latest: {latest} (from code)", latest=__scripts_version__), fg="white", dim=True)
    click.secho(__("📦 Updating scripts to {version}...", version=__scripts_version__), fg="cyan")
    if expected_lang:
        click.secho(__("   Detected language: {lang}", lang=expected_lang), fg="white", dim=True)

    install_git_hooks()

    # Re-read to confirm stamping
    load_dotenv(ENV_FILE, override=True)
    if os.getenv("SCRIPTS_VERSION") == __scripts_version__:
        click.secho(__("✅ Scripts synced successfully!"), fg="green")
        click.secho(f"📚 {__('Documentation:')} {get_doc_url('hooks-versioning.md')}", fg="blue", underline=True)


def run_install_wizard():
    """
    Interactive setup wizard combining --skill, --installhooks, MCP install, and API key check.

    Asks for confirmation before each step and prints a documentation URL at the end.
    """
    click.secho(__("\n🔧 Starting GitPR Interactive Setup Wizard..."), fg="cyan", bold=True)
    click.echo(__("This wizard will guide you through the essential GitPR setup steps.\n"))

    # ------------------------------------------------------------------
    # Step 1: Skill Templates (equivalent to --skill)
    # ------------------------------------------------------------------
    click.secho(__("Step 1 of 4: Skill Templates"), fg="yellow", bold=True)
    click.echo(__("Downloads template files (.gitpr.*.md, .gitpr.linter.yml) into the .gitpr/skill/ folder."))
    click.echo(__("These files allow customizing AI behavior for your team's conventions."))
    if click.confirm(__("Proceed with downloading skill templates?"), default=True):
        generate_skill_template()
    else:
        click.echo(__("Skipped.\n"))

    # ------------------------------------------------------------------
    # Step 2: Git Hooks (equivalent to --installhooks)
    # ------------------------------------------------------------------
    click.secho(__("\nStep 2 of 4: Git Hooks"), fg="yellow", bold=True)
    click.echo(__("Installs pre-commit (static linter) and prepare-commit-msg (AI commit messages) hooks."))
    click.echo(__("This enables automatic validation and AI assistance before every commit."))
    if click.confirm(__("Proceed with installing Git hooks?"), default=True):
        if install_git_hooks():
            click.secho(__("✅ Git Hooks successfully installed!"), fg="green", bold=True)
        else:
            click.secho(__("⚠️ Some hooks could not be installed."), fg="yellow")
    else:
        click.echo(__("Skipped.\n"))

    # ------------------------------------------------------------------
    # Step 3: MCP Configuration (equivalent to gitpr-mcp --install auto)
    # ------------------------------------------------------------------
    click.secho(__("\nStep 3 of 4: MCP Configuration"), fg="yellow", bold=True)
    click.echo(__("Auto-detects and configures GitPR for VS Code, Cursor, Claude Desktop, and Zed."))
    click.echo(__("This lets AI-powered editors use GitPR tools directly without the terminal."))
    if click.confirm(__("Proceed with MCP configuration?"), default=True):
        # Lazy import to avoid circular dependency at module level
        from src.mcp_server import _run_install
        _run_install("auto")
    else:
        click.echo(__("Skipped.\n"))

    # ------------------------------------------------------------------
    # Step 4: API Key Check
    # ------------------------------------------------------------------
    click.secho(__("\nStep 4 of 4: API Key Configuration"), fg="yellow", bold=True)
    provider = get_ai_provider()
    existing_key = get_api_key(provider)
    if existing_key:
        click.secho(
            __("✅ API key for {provider} is already configured.", provider=provider.capitalize()),
            fg="green",
        )
    else:
        click.echo(__("No API key found for {provider}.", provider=provider.capitalize()))
        if click.confirm(__("Would you like to configure it now?"), default=True):
            setup_environment()
        else:
            click.echo(__("You can configure it later by running 'gitpr' or editing ~/.gitpr/.env manually."))

    # ------------------------------------------------------------------
    # Final: documentation URL
    # ------------------------------------------------------------------
    click.echo("")
    click.secho(__("\n✅ Setup wizard complete!"), fg="green", bold=True)
    click.echo(__("For more details, see the full documentation:"))
    click.secho(f"  {get_doc_url('install-wizard.md')}", fg="blue", underline=True)
    click.echo("")


def get_branch_history_text():
    """Compiles the Git Log and PR Cache of the current branch to generate the epic context."""
    branch = get_current_branch()
    base_branch = get_base_branch()
    repo_name = get_repo_name()

    click.secho(__("🔄 Compiling history of repository '{repo_name}', branch '{branch}' against '{base_branch}'...", repo_name=repo_name, branch=branch, base_branch=base_branch), fg="cyan")

    hybrid_context = __("Repository: {repo_name}\nBranch History Summary: {branch}\n\n", repo_name=repo_name, branch=branch)

    # Get the real Git Commits
    try:
        # Get the timeline since the merge base
        merge_base_res = subprocess.run(
            ["git", "merge-base", f"origin/{base_branch}", "HEAD"],
            capture_output=True, text=True, check=True
        )
        ancestor_hash = merge_base_res.stdout.strip()
        
        # Format: Hash | Date | Author | Message
        git_log_res = subprocess.run(
            ["git", "log", f"{ancestor_hash}..HEAD", "--format=%h | %ad | %an | %s", "--date=short"],
            capture_output=True, text=True, encoding="utf-8", check=True
        )
        git_log = git_log_res.stdout.strip()
        
        hybrid_context += __("=== REGISTERED COMMITS ===\n")
        if git_log:
            hybrid_context += f"{git_log}\n\n"
        else:
            hybrid_context += __("No exclusive commits found in this branch.\n\n")
            
    except subprocess.CalledProcessError as e:
        click.secho(__("⚠️ Warning: Could not get Git Log: {error}", error=e.stderr), fg="yellow")
    
    # Get the historical AI memory (Cache of old PRs from this repo + branch)
    cached_prs = get_cached_pr_descriptions(repo_name, branch)
    if cached_prs:
        hybrid_context += f"{cached_prs}\n"
    else:
        hybrid_context += __("=== AI PR HISTORY ===\nNo previous AI-generated PR found in cache for this branch.\n")
        
    return hybrid_context


def has_uncommitted_changes():
    """Returns True if there are uncommitted changes (staged or unstaged)."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--stat"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def get_uncommitted_summary():
    """Returns {'staged': [...], 'unstaged': [...], 'untracked': [...]} path lists
    parsed from 'git status --porcelain'.

    A file may appear in both 'staged' and 'unstaged' when it has staged changes
    AND additional unstaged modifications (e.g. 'MM' = staged mod + unstaged mod,
    'AM' = staged add + unstaged mod).
    """
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotepath=false", "status", "--porcelain"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        summary = {"staged": [], "unstaged": [], "untracked": []}
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            x, y = line[0], line[1]
            path = line[3:].strip()
            if x == "?" and y == "?":
                summary["untracked"].append(path)
            else:
                if x in ("M", "D", "A", "R", "C"):
                    summary["staged"].append(path)
                if y in ("M", "D"):
                    summary["unstaged"].append(path)
        return summary
    except Exception:
        return {"staged": [], "unstaged": [], "untracked": []}


def get_unstaged_files():
    """Returns list of (filepath, status_label) for files with working-tree changes.

    status_label: 'new' (untracked '??'), 'mod' (any unstaged modification:
    ' M', 'MM', 'AM', 'RM', ...), 'del' (any unstaged deletion: ' D', 'MD', 'AD', ...).
    Staged-only changes ('M ', 'A ', 'D ') are NOT returned.
    """
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotepath=false", "status", "--porcelain"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        files = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            status_x = line[0] if len(line) > 0 else ""
            status_y = line[1] if len(line) > 1 else ""
            filepath = line[3:].strip()
            if status_y in ("M", "D") or (status_x == "?" and status_y == "?"):
                if status_x == "?" and status_y == "?":
                    status_label = "new"
                elif status_y == "M":
                    status_label = "mod"
                else:  # status_y == "D"
                    status_label = "del"
                files.append((filepath, status_label))
        return files
    except Exception:
        return []


def get_unstaged_categorized():
    """Returns {'new': [...], 'modified': [...], 'deleted': [...]} with unstaged
    file paths, using the canonical labels from get_unstaged_files()."""
    result = {"new": [], "modified": [], "deleted": []}
    for filepath, label in get_unstaged_files():
        if label == "new":
            result["new"].append(filepath)
        elif label == "mod":
            result["modified"].append(filepath)
        else:  # label == "del"
            result["deleted"].append(filepath)
    return result


def stage_files(filepaths):
    """Run git add on the given file paths.

    Returns (success, message): on failure, message carries git's error
    output so callers can surface the real reason instead of a generic
    warning (empty string when the staging succeeded).
    """
    if not filepaths:
        return True, ""
    try:
        result = subprocess.run(
            ["git", "add"] + filepaths,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            return True, ""
        return False, (result.stderr or result.stdout).strip()
    except Exception as e:
        return False, str(e)


def execute_git_commit(message, no_verify=False):
    """Executes git commit -m with optional --no-verify. Returns (success: bool, output: str)."""
    cmd = ["git", "commit", "-m", message]
    if no_verify:
        cmd.insert(2, "--no-verify")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return (result.returncode == 0, result.stdout + result.stderr)
    except Exception as e:
        return (False, str(e))