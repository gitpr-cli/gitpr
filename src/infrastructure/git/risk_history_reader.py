"""Git history reader for extracting file churn, bug fixes, and revert patterns."""

from dataclasses import dataclass, field
import re
import subprocess
from typing import Optional


@dataclass
class FileHistoryMetrics:
    file_path: str
    total_commits: int = 0
    bug_commits: int = 0
    revert_commits: int = 0
    is_new_file: bool = False
    available: bool = True
    warnings: list[str] = field(default_factory=list)


_REVERT_PATTERN = re.compile(r"^(revert|rollback)\b|this reverts commit", re.IGNORECASE)
_BUG_PATTERN = re.compile(r"^(fix|hotfix|bug)(\([^\)]+\))?\s*:", re.IGNORECASE)
_BUG_KEYWORD_PATTERN = re.compile(r"\b(bugfix|hotfix|fixes\s+#|resolves\s+#)\b", re.IGNORECASE)


def read_file_git_history(
    file_path: str,
    repo_path: Optional[str] = None,
    window_days: int = 90,
    max_commits: int = 50,
) -> FileHistoryMetrics:
    """Safely extracts historical commit statistics for a single file using git log.

    Never raises: any failure to invoke git or parse history degrades to
    available=False with a warning.
    """
    metrics = FileHistoryMetrics(file_path=file_path)

    cmd = [
        "git",
        "log",
        f"-n",
        str(max_commits),
        f"--since={window_days}.days",
        "--follow",
        "--format=%H|%s|%ad",
        "--date=short",
        "--",
        file_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError, ValueError) as err:
        metrics.available = False
        metrics.warnings.append(f"Git history unavailable for '{file_path}': {err}")
        return metrics

    if result.returncode != 0:
        metrics.available = False
        metrics.warnings.append(
            f"Git log returned non-zero code ({result.returncode}) for '{file_path}'"
        )
        return metrics

    lines = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    metrics.total_commits = len(lines)

    if metrics.total_commits == 0:
        # Check if the file is genuinely new or simply has no commits in the window
        metrics.is_new_file = True
        return metrics

    for line in lines:
        parts = line.split("|", 2)
        subject = parts[1].strip() if len(parts) >= 2 else ""

        if _REVERT_PATTERN.search(subject):
            metrics.revert_commits += 1

        if _BUG_PATTERN.search(subject) or _BUG_KEYWORD_PATTERN.search(subject):
            metrics.bug_commits += 1

    return metrics

