"""What the local working copy says about itself: repo label, branch, author.

Two features ask this question and they must get the same answer:

* ``src/usage_log.py`` writes one audit line per command.
* ``src/ledger.py`` writes one telemetry row per execution.

Before this module each had its own way of answering, and they disagreed on
every forge that is not GitHub — the exact "three diverging copies of one map"
shape that the metrics audit found elsewhere. One grammar, one place.

Deliberately **not** ``ScmProvider.parse_repo_ref()``: that is a provider method,
so reaching it here would mean building a provider — token, base URL, extras —
on every command, including the ones that never touch the network. Bitbucket and
Azure DevOps refuse to construct without their extras configured, and a
telemetry write must not be able to fail for that reason.

The parsing here is a subset of the provider grammar on purpose: it answers
"which repository is this", not "how do I address its API". On all four forges
the label it produces is ``workspace/name`` — the same string the providers
derive — so the two agree without sharing code.
"""

import subprocess
from dataclasses import dataclass, replace

# The three config keys the working context is built from, read in a single
# `git config --get-regexp`. Three separate lookups cost roughly 150 ms on
# Windows; one costs about 40 ms.
_GIT_KEYS = ("remote.origin.url", "user.name", "user.email")
_GIT_REGEX = "^(%s)$" % "|".join(key.replace(".", r"\.") for key in _GIT_KEYS)


@dataclass(frozen=True)
class GitContext:
    """The working copy's identity at the moment it was read."""

    repo: str = ""
    branch: str = ""
    author_name: str = ""
    author_email: str = ""

    @property
    def author(self) -> str:
        """The author as the audit log renders it: ``Name <email>``.

        The ledger uses ``author_name`` alone — the e-mail stays out of the
        telemetry database, which is the one that travels between machines.
        """
        if self.author_name and self.author_email:
            return f"{self.author_name} <{self.author_email}>"
        return self.author_name or self.author_email


def repo_label(remote_url) -> str:
    """Reduces any forge's remote URL to a readable ``workspace/name`` label.

    Deliberately not ``core.get_repo_name()``: that one hardcodes github.com and
    answers ``unknown/repo`` on every other forge.

    Returns ``""`` for an empty or unparsable URL. Callers treat that as "no
    remote configured" and keep it distinct from a repository that merely has an
    unusual name.
    """
    url = " ".join(str(remote_url or "").split())
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


def _read_git_config() -> dict:
    """The three identity keys from git config, or an empty dict."""
    try:
        proc = subprocess.run(
            ["git", "config", "--get-regexp", _GIT_REGEX],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
    except Exception:
        return {}

    # git config exits 1 when nothing matched — no repository, or no identity
    if proc.returncode != 0:
        return {}

    values = {}
    for line in (proc.stdout or "").splitlines():
        key, _, value = line.partition(" ")
        values[key.strip().lower()] = value.strip()
    return values


def _read_branch() -> str:
    """The current branch name, or ``""`` when git cannot say."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    # A detached HEAD answers "HEAD", which names no branch — report nothing
    # rather than a branch that does not exist.
    branch = (proc.stdout or "").strip()
    return "" if branch == "HEAD" else branch


def git_identity() -> GitContext:
    """Repository label and configured author — one ``git`` spawn.

    Never raises and never prints: a read-only home, a missing git or a
    repository-less directory all degrade to empty fields. ``branch`` is left
    empty here because reading it costs a second spawn, and the audit log does
    not need it.
    """
    values = _read_git_config()
    return GitContext(
        repo=repo_label(values.get("remote.origin.url", "")),
        author_name=values.get("user.name", ""),
        author_email=values.get("user.email", ""),
    )


def working_context() -> GitContext:
    """``git_identity()`` plus the current branch — two ``git`` spawns.

    Nothing is memoized: the answer depends on the working directory, callers
    move between repositories, and a stale label is worse than a repeated
    spawn. Callers that write several records in one run resolve this once
    themselves.
    """
    return replace(git_identity(), branch=_read_branch())
