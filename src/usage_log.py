"""General usage log: one line per GitPR command, one file per day.

Only two places call log_usage() — the root CLI callback in main.py and the MCP
server entry point in mcp_server.py. Every flag, every subcommand and every
`ctx.exit()` path goes through one of those two, so a single call each is
enough to record every run.

Three decisions worth knowing about:

* The write is synchronous. src.metrics.log_local_metric uses a daemon thread,
  which loses the entry whenever the process exits before the thread is
  scheduled — unacceptable for a log whose whole promise is that every command
  gets recorded.
* Nothing here ever prints. The MCP server runs on stdio and reserves stdout
  for JSON-RPC, so a stray print would corrupt the protocol.
* The daily filename is a uuid5 derived from the date, which yields one stable
  name per day with no state file to keep in sync and no way for two concurrent
  gitpr processes to disagree about which file today is.
"""

import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

# The literals every boolean reader in the project agrees on. Same set the
# sibling PR publish log accepts, so the two logs agree on what "on" means.
_BOOL_TRUE = ("true", "1", "yes", "y")

# What the log line needs from git. Fetched together — see _git_identity().
_GIT_KEYS = ("remote.origin.url", "user.name", "user.email")
_GIT_REGEX = "^(%s)$" % "|".join(key.replace(".", r"\.") for key in _GIT_KEYS)


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

    Deliberately not core.get_repo_name(): that one hardcodes github.com and
    answers "unknown/repo" on every other forge. Deliberately not
    parse_repo_ref() either — that is a provider method, so reaching it here
    would mean building a provider (token, HTTP session) on every command.
    """
    url = _flat(remote_url)
    if not url:
        return ""
    if url.endswith(".git"):
        url = url[:-4]

    if "://" in url:
        # https://host/path, ssh://host:2222/path — drop scheme and host
        path = url.split("://", 1)[1]
        path = path.split("/", 1)[1] if "/" in path else ""
    elif ":" in url and "@" in url.split(":", 1)[0]:
        # scp-like shorthand: git@host:path
        path = url.split(":", 1)[1]
    else:
        # A plain local path, or a host with nothing after it
        path = url

    # "_git" is an Azure DevOps URL artifact, not part of the repository's
    # identity — the project and the repo are what identify it there.
    return "/".join(seg for seg in path.strip("/").split("/") if seg and seg != "_git")


def _git_identity():
    """(repository label, configured author) for the current directory.

    One `git config --get-regexp` instead of the idiomatic three lookups
    (user.name, user.email and remote -v). Three process spawns cost roughly
    150 ms on Windows on every command; one costs about 40 ms.
    """
    try:
        proc = subprocess.run(
            ["git", "config", "--get-regexp", _GIT_REGEX],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
    except Exception:
        return "", ""

    # git config exits 1 when nothing matched — no repository, or no identity
    if proc.returncode != 0:
        return "", ""

    values = {}
    for line in (proc.stdout or "").splitlines():
        key, _, value = line.partition(" ")
        values[key.strip().lower()] = value.strip()

    name = values.get("user.name", "")
    email = values.get("user.email", "")
    if name and email:
        author = f"{name} <{email}>"
    else:
        author = name or email

    return _repo_label(values.get("remote.origin.url", "")), author


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
