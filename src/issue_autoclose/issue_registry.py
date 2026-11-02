"""The local record of the issue created with ``gitpr -is`` (ADR-001).

``gitpr -is`` creates an issue and the number is otherwise lost; the next pull
request is the first place that could close it. The record is therefore one
small file, ``.gitpr/conf/github.yml``, holding the issue that is still a
candidate — the last one wins, which is all a single-PR workflow needs.

The file is local state, not project content: ``record()`` makes sure
``git check-ignore`` sees it before the first write and adds exactly one line
to the repository's ``.gitignore`` when it does not. ``.gitpr/conf/`` is not
ignored wholesale because ``gitpr.config.yml`` in the same folder is versioned
on purpose (ADR-015).

Serialization is YAML with ``schema_version: 1``; a file that cannot be read
back is reported through ``RegistryLoad.error`` and then overwritten by the
next ``record()``. Nothing here touches the network or the SCM provider — that
is the provider's job when the PR flow asks whether the issue is still open.
"""
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from src.infrastructure.git.patch_applier import repo_root, run_git

REGISTRY_RELATIVE_PATH = Path(".gitpr") / "conf" / "github.yml"

#: The only version this module writes and the only one it reads.
SCHEMA_VERSION = 1

#: The single line the first write adds to the user's .gitignore.
GITIGNORE_ENTRY = ".gitpr/conf/github.yml"


class IssueRegistryError(Exception):
    """The record exists but cannot be written or removed."""


@dataclass(frozen=True)
class RegisteredIssue:
    """One issue below ``last_issue`` — the shape the PR flow reads back."""

    repo: str  # "owner/name"
    number: int
    title: str
    url: str
    created_at: str  # ISO 8601
    branch: str | None = None


@dataclass(frozen=True)
class RegistryLoad:
    """What ``load()`` found: the issue, or why the file could not be used."""

    issue: RegisteredIssue | None = None
    error: str = ""


@dataclass(frozen=True)
class RecordResult:
    """Outcome of one write, including whether .gitignore had to change."""

    path: Path
    gitignore_updated: bool = False


def registry_path(start_dir=None):
    """Absolute path of the record, anchored at the repository root.

    Falls back to *start_dir* (or the working directory) outside a git
    repository, so tests and callers with an explicit path keep working.
    """
    root = repo_root(start_dir)
    base = Path(root) if root else Path(start_dir or os.getcwd())
    return base / REGISTRY_RELATIVE_PATH


def _registered_issue(raw):
    """Validates one ``last_issue`` mapping. Raises ValueError when corrupt."""
    if not isinstance(raw, dict):
        raise ValueError("'last_issue' must be a mapping")

    repo = raw.get("repo")
    if not isinstance(repo, str) or not repo.strip():
        raise ValueError("'last_issue.repo' must be text")

    number = raw.get("number")
    if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
        raise ValueError("'last_issue.number' must be a positive integer")

    for field in ("title", "url", "created_at"):
        value = raw.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"'last_issue.{field}' must be text")

    branch = raw.get("branch")
    if branch is not None and not isinstance(branch, str):
        raise ValueError("'last_issue.branch' must be text or empty")

    return RegisteredIssue(
        repo=repo.strip(),
        number=number,
        title=raw["title"],
        url=raw["url"],
        created_at=raw["created_at"],
        branch=branch,
    )


class IssueRegistry:
    """Reads and writes the record at ``.gitpr/conf/github.yml``.

    The class carries the path so the PR flow can hold one instance while the
    tests point it at a temporary repository. It never prints: ``load()``
    returns the problem and ``record()`` says whether .gitignore changed, and
    the command that owns the screen decides how to report either.
    """

    def __init__(self, path=None, start_dir=None):
        self.path = Path(path) if path else registry_path(start_dir)

    def load(self):
        """The recorded issue, or ``RegistryLoad(error=...)`` when unreadable.

        A missing file is not an error — it is simply "no issue recorded".
        """
        if not self.path.exists():
            return RegistryLoad()

        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as handle:
                data = yaml.safe_load(handle)
            if not isinstance(data, dict):
                raise ValueError("the file is not a YAML mapping")
            version = data.get("schema_version")
            if version != SCHEMA_VERSION:
                raise ValueError(f"unsupported schema_version {version!r}")
            return RegistryLoad(issue=_registered_issue(data.get("last_issue")))
        except Exception as exc:
            return RegistryLoad(error=str(exc))

    def record(self, issue):
        """Writes *issue* atomically and ensures .gitignore covers the file.

        A file already there is replaced — including one ``load()`` reported as
        corrupt. The write goes to a sibling temporary file and is moved into
        place, so an interrupted run can never leave a truncated record.
        """
        if not isinstance(issue, RegisteredIssue):
            raise TypeError("record() expects a RegisteredIssue")

        body = yaml.safe_dump(
            {"schema_version": SCHEMA_VERSION, "last_issue": asdict(issue)},
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                errors="replace",
                newline="\n",
                dir=self.path.parent,
                prefix=".gitpr-issue-",
                suffix=".tmp",
                delete=False,
            )
            try:
                with handle:
                    handle.write(body)
                os.replace(handle.name, self.path)
            except Exception:
                try:
                    os.unlink(handle.name)
                except OSError:
                    pass
                raise
        except OSError as exc:
            raise IssueRegistryError(f"cannot write {self.path}: {exc}") from exc

        return RecordResult(path=self.path, gitignore_updated=self._ensure_gitignored())

    def clear(self):
        """Removes the record. False when there was nothing to remove."""
        try:
            self.path.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise IssueRegistryError(f"cannot remove {self.path}: {exc}") from exc

    def matches_repo(self, owner_repo):
        """True when the recorded issue belongs to *owner_repo*.

        GitHub owner and repository names are case-insensitive, so the
        comparison is too; a corrupt or absent record never matches.
        """
        loaded = self.load()
        if loaded.issue is None:
            return False
        expected = (owner_repo or "").strip().casefold()
        return bool(expected) and loaded.issue.repo.casefold() == expected

    def _ensure_gitignored(self):
        """Adds GITIGNORE_ENTRY once when git does not already ignore it.

        Returns True only when a line was appended. Outside a repository, or
        when .gitignore cannot be written, nothing changes and the record is
        still valid: the user can add the line by hand.
        """
        root = repo_root(self.path.parent)
        if root is None:
            return False

        check = run_git(["check-ignore", "-q", GITIGNORE_ENTRY], cwd=root)
        if check.returncode == 0:
            return False

        target = Path(root) / ".gitignore"
        try:
            existing = ""
            if target.exists():
                existing = target.read_text(encoding="utf-8", errors="replace")
            separator = "" if not existing or existing.endswith("\n") else "\n"
            with open(target, "a", encoding="utf-8", newline="\n") as handle:
                handle.write(f"{separator}{GITIGNORE_ENTRY}\n")
        except OSError:
            return False
        return True
