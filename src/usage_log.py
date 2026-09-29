"""General usage log: one line per GitPR command, one file per day.

Only two places call log_usage() — the root CLI callback in main.py and the MCP
server entry point in mcp_server.py. Every flag, every subcommand and every
`ctx.exit()` path goes through one of those two, so a single call each is
enough to record every run.

Three decisions worth knowing about:

* The write is synchronous. The audit log carries the promise that every command
  gets recorded, and a write deferred to a background thread breaks exactly that
  promise whenever the process exits before the thread is scheduled — which is
  the whole lifecycle of `gitpr --hook-event`. src.metrics.log_local_metric made
  the same choice for the same reason, after the same defect was found there.
* Nothing here ever prints. The MCP server runs on stdio and reserves stdout
  for JSON-RPC, so a stray print would corrupt the protocol.
* The daily filename is a uuid5 derived from the date, which yields one stable
  name per day with no state file to keep in sync and no way for two concurrent
  gitpr processes to disagree about which file today is.
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from src.infrastructure.git.identity import git_identity, repo_label

# The literals every boolean reader in the project agrees on. Same set the
# sibling PR publish log accepts, so the two logs agree on what "on" means.
_BOOL_TRUE = ("true", "1", "yes", "y")


def _enabled():
    """Reads GITPR_SHOW_LOGS, defaulting to on (the seeded value)."""
    return os.getenv("GITPR_SHOW_LOGS", "true").strip().lower() in _BOOL_TRUE


def _log_dir():
    """~/.gitpr/logs — already GitPR's, and already holding pr_desc/."""
    return Path(os.path.expanduser("~")) / ".gitpr" / "logs"


def _log_path(day):
    """The log file for a YYYY-MM-DD day.

    Derived from the date rather than counted or remembered, so the same day
    always resolves to the same file.
    """
    return _log_dir() / f"{uuid.uuid5(uuid.NAMESPACE_DNS, f'gitpr.usage.{day}')}.log"


def _flat(value):
    """Collapses whitespace: the format is strictly one command per line."""
    if value is None:
        return ""
    return " ".join(str(value).split())


def _repo_label(remote_url):
    """Reduces any forge's remote URL to a readable "owner/repo" label.

    Thin alias for src.infrastructure.git.identity.repo_label — the grammar is
    shared with the telemetry ledger, which needs the same answer for the same
    remote so the two records can be joined.
    """
    return repo_label(remote_url)


def _git_identity():
    """(repository label, configured author) for the current directory.

    One `git config --get-regexp` instead of the idiomatic three lookups
    (user.name, user.email and remote -v). Three process spawns cost roughly
    150 ms on Windows on every command; one costs about 40 ms.
    """
    context = git_identity()
    return context.repo, context.author


def _command():
    """The invocation as typed, e.g. "gitpr -c" — program name plus its flags."""
    args = list(sys.argv)
    if not args:
        return "gitpr"

    name = os.path.basename(args[0]) or "gitpr"
    if name.lower().endswith(".exe"):
        name = name[:-4]
    return _flat(" ".join([name] + args[1:]))


def log_usage():
    """Appends one line describing this invocation.

    Best-effort by design — it returns the file it wrote, or None when logging
    is off or anything at all went wrong, and never raises. A read-only home, a
    missing git or a locked file must never turn into a failed command.
    """
    try:
        if not _enabled():
            return None

        try:
            from src.updater import __version__ as version
        except Exception:
            version = ""

        now = datetime.now()
        path = _log_path(now.strftime("%Y-%m-%d"))
        repo, author = _git_identity()

        line = "[{}] | v{} | {} | {} | {}\n".format(
            now.strftime("%Y-%m-%d %H:%M:%S"),
            version.lstrip("v"),
            _command(),
            repo or "-",
            _flat(author) or "-",
        )

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8", errors="replace") as handle:
            handle.write(line)
        return path
    except Exception:
        return None
