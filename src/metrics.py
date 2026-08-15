import os
import json
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from src.chat_memory import gerar_uuid_base_15
from src.core import get_current_branch, get_repo_name


def _get_owner_name():
    """Returns the repository owner or the local username as fallback."""
    repo = get_repo_name()
    if repo and repo != "unknown/repo":
        return repo.split("/")[0]

    try:
        name = subprocess.run(
            ["git", "config", "user.name"], capture_output=True, text=True, check=True
        ).stdout.strip()
        return name.replace(" ", "_") if name else "local_user"
    except Exception:
        return "local_user"


def _save_metric_async(payload):
    """Saves the JSON payload to the correct directory silently and asynchronously."""
    try:
        owner = _get_owner_name()
        branch = get_current_branch().replace("/", "-")

        metrics_dir = Path.home() / ".gitpr" / "metrics" / owner / branch
        metrics_dir.mkdir(parents=True, exist_ok=True)

        uuid_str = gerar_uuid_base_15()
        date_str = datetime.now().strftime("%Y%m%d")
        file_name = f"{uuid_str}_{date_str}.json"

        file_path = metrics_dir / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Fire-and-forget: failures must never break the CLI


def log_local_metric(
    command, status, provider="local", tokens_estimated=0, duration_ms=0, **kwargs
):
    """Fires a local metric log in a separate daemon thread."""
    payload = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "status": status,
        "provider": provider,
        "tokens_estimated": tokens_estimated,
        "duration_ms": duration_ms,
        "repo": get_repo_name(),
        "branch": get_current_branch(),
        **kwargs,
    }

    thread = threading.Thread(target=_save_metric_async, args=(payload,))
    thread.daemon = True
    thread.start()


def log_command_metric(
    command,
    status="success",
    provider=None,
    tokens_estimated=0,
    duration_ms=0,
    cache_hit=False,
    map_reduce_triggered=False,
    **kwargs,
):
    """High-level metric logger for CLI commands.

    Args:
        command: Command name ('commit', 'review', 'fullreview', 'linter', etc.)
        status: 'success', 'error', 'triggered', 'no_changes'
        provider: AI provider used (None = local/no AI)
        tokens_estimated: Estimated token count from AI usage metadata
        duration_ms: Command duration in milliseconds
        cache_hit: True if result was served from cache
        map_reduce_triggered: True if map-reduce chunking was activated
        **kwargs: Extra fields (linter_errors, linter_warnings, chunks_count, etc.)
    """
    if provider is None:
        # Auto-detect: try config, fallback to 'local'
        try:
            from src.config import get_ai_provider

            provider = get_ai_provider()
        except Exception:
            provider = "local"

    log_local_metric(
        command=command,
        status=status,
        provider=provider,
        tokens_estimated=tokens_estimated,
        duration_ms=duration_ms,
        cache_hit=cache_hit,
        map_reduce_triggered=map_reduce_triggered,
        **kwargs,
    )


def get_metrics_dir():
    """Returns the path to the local metrics directory (~/.gitpr/metrics/)."""
    return os.path.join(Path.home(), ".gitpr", "metrics")


def get_metrics_state_file():
    """Returns the path to the metrics state file (~/.gitpr/metrics/config.json)."""
    return os.path.join(get_metrics_dir(), "config.json")


def enrich_metrics_from_cache(events):
    """Augments metric events with real token usage from AI response cache files.

    Scans ~/.gitpr/cache/prompts/{action_folder}/{md5}.json and matches
    cache entries to events by (repo, branch, action type, datetime minute).
    Returns the enriched event list. Never raises — failures are silent.
    """
    import os as _os

    cache_base = Path.home() / ".gitpr" / "cache" / "prompts"
    if not cache_base.is_dir():
        return events

    # Collect cache entries: (repo, branch, action_type, dt_minute, meta)
    cache_entries = []
    for cache_file in cache_base.glob("*/*.json"):
        try:
            with open(cache_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                continue
            response = data.get("response") or {}
            if not isinstance(response, dict):
                continue  # Skip list-typed responses (legacy format)
            meta = response.get("meta_raw") or response.get("_telemetry_meta")
            if not isinstance(meta, dict):
                continue
            dt = (data.get("datetime") or "").replace("T", " ")[:16]
            entry = (
                data.get("repo", ""),
                data.get("branch", ""),
                data.get("action_type", ""),
                dt,
                meta,
            )
            cache_entries.append(entry)
        except Exception:
            continue  # Corrupt cache files must never break export

    if not cache_entries:
        return events

    # Map command names to cache action_type folders
    _action_type_map = {
        "pr": "pr_desc",
        "commit": "commit",
        "review": "review",
        "fullreview": "fullreview",
        "filereview": "filereview",
        "issue": "issue",
    }
    used = [False] * len(cache_entries)

    enriched = []
    for evt in events:
        e = dict(evt)
        cmd = e.get("command", "")
        cache_action = _action_type_map.get(cmd, cmd)
        repo = e.get("repo", "")
        branch = e.get("branch", "")
        ts = (e.get("timestamp") or "").replace("T", " ")[:16]
        tokens_est = e.get("tokens_estimated", 0)

        best_match = None
        best_idx = -1
        for i, ce in enumerate(cache_entries):
            if used[i]:
                continue
            if ce[0] != repo or ce[1] != branch or ce[2] != cache_action or ce[3] != ts:
                continue
            total = ce[4].get("total_tokens", 0)
            if best_match is None:
                best_match = ce
                best_idx = i
            if tokens_est > 0 and total == tokens_est:
                best_match = ce
                best_idx = i
                break  # Exact token match — best possible

        if best_match is not None:
            used[best_idx] = True
            meta = best_match[4]
            e["prompt_tokens"] = meta.get("prompt_tokens", 0)
            e["completion_tokens"] = meta.get("completion_tokens", 0)
            e["tokens_actual"] = meta.get("total_tokens", 0)

        enriched.append(e)

    return enriched


def load_cache_token_summary(repo_name=None):
    """Scans ~/.gitpr/cache/prompts/ and aggregates token usage from all cache files.

    Reads every *.json in every subfolder, extracts response.meta_raw
    (or response._telemetry_meta as fallback), and returns a summary dict.

    Args:
        repo_name: If set, filters by data["repo"] == repo_name.
                   If None, aggregates across all repositories.

    Returns:
        dict with keys:
          - total_prompt_tokens, total_completion_tokens, total_tokens
          - by_action: dict of action_type -> {"count": N, "tokens": N}
          - file_count: number of cache files processed
    """
    cache_base = Path.home() / ".gitpr" / "cache" / "prompts"
    summary = {
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0,
        "by_action": {},
        "file_count": 0,
    }

    if not cache_base.is_dir():
        return summary

    for cache_file in cache_base.glob("*/*.json"):
        try:
            with open(cache_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        # Filter by repo if requested
        if repo_name is not None and data.get("repo", "") != repo_name:
            continue

        response = data.get("response") or {}
        if not isinstance(response, dict):
            continue  # Skip list-typed responses (legacy format)
        meta = response.get("meta_raw") or response.get("_telemetry_meta")
        if not isinstance(meta, dict):
            continue

        prompt_tokens = meta.get("prompt_tokens", 0)
        completion_tokens = meta.get("completion_tokens", 0)
        total_tokens = meta.get("total_tokens", 0)

        summary["total_prompt_tokens"] += prompt_tokens
        summary["total_completion_tokens"] += completion_tokens
        summary["total_tokens"] += total_tokens
        summary["file_count"] += 1

        action = data.get("action_type", "unknown")
        if action not in summary["by_action"]:
            summary["by_action"][action] = {"count": 0, "tokens": 0}
        summary["by_action"][action]["count"] += 1
        summary["by_action"][action]["tokens"] += total_tokens

    return summary


def export_metrics(output_dir=None, repo_filter=None):
    """Scans ~/.gitpr/metrics/, consolidates all JSON files into a CSV + JSON report.

    Skips files already processed (tracked via config.json UUID list).
    Filters events by repo_filter when provided.
    Returns (csv_path, json_path, event_count).
    """
    import click
    from datetime import date

    metrics_dir = get_metrics_dir()
    state_file = get_metrics_state_file()

    if not os.path.isdir(metrics_dir):
        return None, None, 0

    # Load already-exported UUIDs
    exported_uuids = set()
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                exported_uuids = set(json.load(f).get("exported", []))
        except Exception:
            pass

    # Collect all unexported metric files
    all_files = []
    for root, dirs, files in os.walk(metrics_dir):
        # Skip the export subdirectory
        if "export" in root.replace(metrics_dir, "").split(os.sep):
            continue
        for fname in files:
            if fname.endswith(".json") and not fname.startswith("config"):
                fpath = os.path.join(root, fname)
                # Check UUID (first part of filename before _YYYYMMDD)
                uuid_part = fname.split("_")[0]
                if uuid_part not in exported_uuids:
                    all_files.append(fpath)

    if not all_files:
        return None, None, 0

    # Consolidate all payloads
    events = []
    with click.progressbar(all_files, label="Exporting metrics") as bar:
        for fpath in bar:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    events.append(json.load(f))
            except Exception:
                pass

    if not events:
        return None, None, 0

    # Filter by repo if requested
    if repo_filter is not None:
        events = [e for e in events if e.get("repo", "") == repo_filter]
        if not events:
            return None, None, 0

    # Enrich events with real token usage from AI response cache files
    events = enrich_metrics_from_cache(events)

    # Determine output directory (project-local by default)
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), ".gitpr", "metrics", "export")
    os.makedirs(output_dir, exist_ok=True)

    today_str = date.today().strftime("%Y-%m-%d")
    csv_path = os.path.join(output_dir, f"gitpr_metrics_{today_str}.csv")
    json_path = os.path.join(output_dir, f"gitpr_metrics_{today_str}.json")

    # Write CSV
    csv_columns = [
        "timestamp",
        "command",
        "status",
        "provider",
        "tokens_estimated",
        "duration_ms",
        "repo",
        "branch",
        "prompt_tokens",
        "completion_tokens",
        "tokens_actual",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(csv_columns) + "\n")
        for evt in events:
            row = [str(evt.get(col, "")) for col in csv_columns]
            f.write(",".join(f'"{v}"' for v in row) + "\n")

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    # Update state file with newly exported UUIDs
    new_uuids = set()
    for fpath in all_files:
        uuid_part = os.path.basename(fpath).split("_")[0]
        new_uuids.add(uuid_part)
    exported_uuids.update(new_uuids)

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "exported": sorted(exported_uuids),
                "last_export": datetime.now().isoformat(),
                "total_events": len(events) + len(exported_uuids),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return csv_path, json_path, len(events)


def purge_metrics():
    """Deletes all metric JSON files in ~/.gitpr/metrics/ (preserves config.json).

    Returns the number of files removed.
    """
    import click

    metrics_dir = get_metrics_dir()
    if not os.path.isdir(metrics_dir):
        return 0

    removed = 0
    for root, dirs, files in os.walk(metrics_dir):
        for fname in files:
            if fname.endswith(".json") and fname != "config.json":
                fpath = os.path.join(root, fname)
                try:
                    os.remove(fpath)
                    removed += 1
                except Exception:
                    pass

    return removed


def show_metrics_summary():
    """Prints a summary of the local metrics directory."""
    metrics_dir = get_metrics_dir()
    state_file = get_metrics_state_file()

    if not os.path.isdir(metrics_dir):
        return {
            "total_files": 0,
            "total_events": 0,
            "disk_usage": "0 KB",
            "path": metrics_dir,
        }

    total_files = 0
    exported_count = 0
    disk_bytes = 0

    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                exported_count = len(state.get("exported", []))
        except Exception:
            pass

    for root, dirs, files in os.walk(metrics_dir):
        for fname in files:
            if fname.endswith(".json"):
                total_files += 1
                fpath = os.path.join(root, fname)
                try:
                    disk_bytes += os.path.getsize(fpath)
                except Exception:
                    pass

    if disk_bytes < 1024:
        disk_usage = f"{disk_bytes} B"
    elif disk_bytes < 1024 * 1024:
        disk_usage = f"{disk_bytes / 1024:.1f} KB"
    else:
        disk_usage = f"{disk_bytes / (1024 * 1024):.1f} MB"

    return {
        "total_files": total_files,
        "total_events": exported_count,
        "disk_usage": disk_usage,
        "path": metrics_dir,
    }


# ---------------------------------------------------------------------------
# Dashboard unified cache scanning + processed-file tracking (per-repo)
# ---------------------------------------------------------------------------


def get_project_metrics_dir():
    """Returns the project-local .gitpr/metrics/ directory path."""
    return os.path.join(os.getcwd(), ".gitpr", "metrics")


def get_processed_cache_file(repo_name):
    """Returns the path to the per-repo processed-cache tracking file.

    The file lives at ./.gitpr/metrics/{repo_safe}/processed_cache.json
    where {repo_safe} is the repo name with '/' replaced by '-'.
    """
    repo_safe = repo_name.replace("/", "-") if repo_name else "unknown"
    return os.path.join(get_project_metrics_dir(), repo_safe, "processed_cache.json")


def load_processed_cache_list(repo_name):
    """Loads the set of absolute cache-file paths already processed for this repo.

    Returns an empty set on any failure (missing file, corrupt JSON, etc.).
    """
    state_file = get_processed_cache_file(repo_name)
    if not os.path.exists(state_file):
        return set()
    try:
        with open(state_file, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        return set(data.get("processed", []))
    except Exception:
        return set()


def save_processed_cache_list(paths, repo_name):
    """Saves the list of processed cache-file paths for the given repo.

    Fire-and-forget — failures are silently ignored.
    """
    state_file = get_processed_cache_file(repo_name)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        payload = {
            "processed": sorted(paths),
            "last_scan": datetime.now().isoformat(),
            "count": len(paths),
        }
        with open(state_file, "w", encoding="utf-8", errors="replace") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Never break the dashboard for a state-file write failure


# Map command names to cache action_type folders (mirrors enrich_metrics_from_cache)
_ACTION_TYPE_TO_CACHE_FOLDER = {
    "pr": "pr_desc",
    "commit": "commit",
    "review": "review",
    "fullreview": "review",
    "filereview": "review",
    "issue": "issue",
}


def scan_cache_files_for_dashboard(repo_filter=None, progress_cb=None, since_date=None):
    """Scans ALL ~/.gitpr/cache/prompts/*/*.json files and returns enriched rows.

    Each row is a dict suitable for direct display in the DataTable:

        {
            "timestamp": "2026-08-02 10:30:00",
            "command": "commit",
            "status": "success",
            "provider": "",
            "tokens": 1266,
            "duration_ms": 2340,
            "repo": "owner/repo",
            "branch": "main",
            "source": "cache",
            "md5": "00502e4...",
            "path": "/home/user/.gitpr/cache/prompts/commit/00502e4....json",
        }

    Args:
        repo_filter: If set, only includes rows whose repo matches.
        progress_cb: Optional callback(done: int, total: int) called per file.
        since_date: Minimum datetime string (YYYY-MM-DD) for cache files.
                    Defaults to January 1st of the current year.
    """
    from datetime import date as _date

    if since_date is None:
        since_date = _date.today().replace(month=1, day=1).strftime("%Y-%m-%d")

    cache_base = Path.home() / ".gitpr" / "cache" / "prompts"
    rows = []

    if not cache_base.is_dir():
        return rows

    # Collect all cache file paths first so we know the total for progress
    all_files = sorted(cache_base.glob("*/*.json"))
    total = len(all_files)

    for idx, cache_file in enumerate(all_files, 1):
        if progress_cb:
            progress_cb(idx, total)

        try:
            with open(cache_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        # Date filter: skip files older than since_date
        file_dt = (data.get("datetime") or "")[:10]
        if file_dt and file_dt < since_date:
            continue

        # Filter by repo when requested (include files without 'repo' — they may belong)
        file_repo = data.get("repo", "")
        if repo_filter is not None and file_repo and file_repo != repo_filter:
            continue

        response = data.get("response") or {}
        if not isinstance(response, dict):
            continue  # Skip list-typed responses (legacy format)
        meta = response.get("meta_raw") or response.get("_telemetry_meta") or {}

        row = {
            "timestamp": (data.get("datetime") or "").replace("T", " ")[:19],
            "command": data.get("action_type", "unknown"),
            "status": "success",
            "provider": meta.get("provider", ""),
            "tokens": meta.get("total_tokens", 0),
            "duration_ms": meta.get("duration_ms", 0),
            "repo": file_repo,
            "branch": data.get("branch", ""),
            "source": "cache",
            "md5": data.get("md5", ""),
            "path": str(cache_file),
        }
        rows.append(row)

    # Sort by timestamp, newest first
    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    return rows
