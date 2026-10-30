"""Project-local configuration, versioned with the repository.

The only setting so far is the pull request target base branch: the branch the
forge is asked to merge into. The AI diff baseline is a different concept and
stays in ``core.get_git_full_diff()``, which always compares against
``origin/HEAD`` (ADR-015). A project may therefore target ``develop`` while its
description and review are still built against the detected default branch.
That divergence is known and deliberate for now.

Why a separate module instead of ``src/config.py``: the project file has its own
path resolution (the repository root, not the working directory), its own
serialization (YAML, not dotenv) and its own failure rules (a missing target
fails fast). Keeping it apart means the ``~/.gitpr/.env`` layer and the project
layer cannot borrow each other's semantics by accident.
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.i18n import __

DEFAULT_BASE_BRANCH = "main"

# Relative to the repository root. The rest of .gitpr/ resolves from the
# working directory; this file is the repository's configuration, so it lives
# where the repository starts.
PROJECT_CONFIG_RELATIVE_PATH = Path(".gitpr") / "conf" / "gitpr.config.yml"

HEADER_COMMENT = (
    "# Project configuration for GitPR — versioned with the repository.\n"
    "# The pull request target base branch for this repository.\n"
)

# Keys used by the `gitpr config` TUI. They are project-file keys, not
# ~/.gitpr/.env keys: config_schema.ConfigField.store decides where a value is
# written.
BASE_BRANCH_FIELD = "PROJECT_BASE_BRANCH"
CONFIG_FILE_FIELD = "PROJECT_CONFIG_FILE"
EFFECTIVE_BASE_FIELD = "PROJECT_EFFECTIVE_BASE"

SOURCE_CLI = "cli"
SOURCE_PROJECT = "project"
SOURCE_ENV = "env"
SOURCE_AUTO = "auto"

_SOURCE_LABELS = {
    SOURCE_CLI: __("CLI flag"),
    SOURCE_PROJECT: __("project file"),
    SOURCE_ENV: __("global default"),
    SOURCE_AUTO: __("auto-detection"),
}


class BaseBranchError(Exception):
    """The resolved pull request target cannot be used."""


class CurrentBranchError(BaseBranchError):
    """The target is the branch checked out — a pull request cannot target itself."""


@dataclass(frozen=True)
class ProjectConfig:
    """The project file as read: a value, and the reason it could not be read."""

    path: Path
    base_branch: str = ""
    error: str = ""


@dataclass(frozen=True)
class SeedResult:
    """Outcome of ensuring the project file exists."""

    created: bool
    path: Path
    ignored: bool = False
    error: str = ""


@dataclass(frozen=True)
class ResolvedBase:
    """The branch a pull request will target, and where it came from."""

    branch: str
    source: str
    warnings: tuple = ()


def _run_git(args, cwd=None):
    """Runs a git command and returns (returncode, stdout). Never raises."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return result.returncode, result.stdout


def project_config_path(start_dir=None):
    """Absolute path of the project file, anchored at the repository root."""
    start = Path(start_dir) if start_dir else Path.cwd()
    code, output = _run_git(["rev-parse", "--show-toplevel"], cwd=start)
    root = Path(output.strip()) if code == 0 and output.strip() else start
    return root / PROJECT_CONFIG_RELATIVE_PATH


def list_branches(start_dir=None):
    """Branch names a pull request can target, for the configuration screen.

    Local branches plus the ones that already exist on ``origin`` — the only
    place ``verify_remote_base()`` looks. A repository whose target branch is
    not checked out locally (the usual case for a shared ``develop``) still
    offers it, and ``origin/HEAD`` is dropped: it names a default, not a
    branch. Never raises; an unavailable repository yields an empty list.
    """
    names = set()

    code, output = _run_git(["branch", "--format=%(refname:short)"], cwd=start_dir)
    if code == 0:
        for line in output.splitlines():
            line = line.strip()
            # A detached HEAD lists as "(HEAD detached at ...)".
            if line and not line.startswith("("):
                names.add(line)

    code, output = _run_git(
        ["branch", "-r", "--format=%(refname:short)"], cwd=start_dir
    )
    if code == 0:
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("origin/") and not line.endswith("/HEAD"):
                names.add(line[len("origin/"):])

    return sorted(names)


def read_project_config(path=None, start_dir=None):
    """Reads the project file without ever raising.

    A missing file, an empty file and a file without the key all mean "no
    project value". Anything malformed lands in ``error`` so the caller can
    warn and keep walking the precedence chain.
    """
    target = Path(path) if path else project_config_path(start_dir)
    try:
        if not target.exists():
            return ProjectConfig(path=target)
        with open(target, "r", encoding="utf-8", errors="replace") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        return ProjectConfig(path=target, error=str(exc))

    if data is None:
        return ProjectConfig(path=target)
    if not isinstance(data, dict):
        return ProjectConfig(
            path=target, error=__("The file must contain a YAML mapping.")
        )

    pull_request = data.get("pull_request")
    if pull_request is None:
        return ProjectConfig(path=target)
    if not isinstance(pull_request, dict):
        return ProjectConfig(
            path=target, error=__("'pull_request' must be a mapping.")
        )

    value = pull_request.get("base_branch")
    if value is None:
        return ProjectConfig(path=target)
    if not isinstance(value, str):
        return ProjectConfig(
            path=target, error=__("'pull_request.base_branch' must be text.")
        )
    return ProjectConfig(path=target, base_branch=value.strip())


def load_project_field_values(path=None, start_dir=None):
    """Values for the project-store rows of the configuration screen."""
    config = read_project_config(path=path, start_dir=start_dir)
    if config.error or not config.base_branch:
        return {}
    return {BASE_BRANCH_FIELD: config.base_branch}


def write_project_field_values(values, removals=(), path=None, start_dir=None):
    """Writes project values, preserving every other key already in the file.

    An empty value is a removal: the key disappears, and the repository falls
    back to the global default. Unparsable YAML is never overwritten — the
    caller reports the failure instead of destroying the user's file.
    """
    target = Path(path) if path else project_config_path(start_dir)

    data = {}
    if target.exists():
        with open(target, "r", encoding="utf-8", errors="replace") as handle:
            loaded = yaml.safe_load(handle)
        if loaded is None:
            loaded = {}
        if not isinstance(loaded, dict):
            raise ValueError(
                __("Refusing to overwrite {path}: it is not a YAML mapping.", path=target)
            )
        data = loaded

    pull_request = data.get("pull_request")
    if pull_request is None:
        pull_request = {}
    if not isinstance(pull_request, dict):
        raise ValueError(
            __(
                "Refusing to overwrite {path}: 'pull_request' is not a mapping.",
                path=target,
            )
        )

    if BASE_BRANCH_FIELD in values:
        branch = (values[BASE_BRANCH_FIELD] or "").strip()
        if branch:
            pull_request["base_branch"] = branch
        else:
            pull_request.pop("base_branch", None)
    if BASE_BRANCH_FIELD in removals:
        pull_request.pop("base_branch", None)

    if pull_request:
        data["pull_request"] = pull_request
    else:
        data.pop("pull_request", None)

    target.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.safe_dump(
        data, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(HEADER_COMMENT)
        if body.strip():
            handle.write(body)
    return target


def _is_ignored(target):
    """True when the user's .gitignore keeps the file out of the repository."""
    code, _ = _run_git(["check-ignore", "-q", str(target)], cwd=target.parent)
    return code == 0


def _global_default():
    """PR_DEFAULT_BASE from the environment, or from ~/.gitpr/.env.

    The seed and the resolver run before ``setup_environment()`` — and the
    ``config`` subcommand never runs it at all — so ``os.getenv()`` alone
    would miss a value the user saved through the configuration screen. The
    variable, when present, wins even as an empty string: that is how the
    environment overrides the file everywhere else in GitPR, and an explicitly
    empty value means "no global default".
    """
    if "PR_DEFAULT_BASE" in os.environ:
        return os.environ["PR_DEFAULT_BASE"].strip()
    try:
        # Imported here so a missing or unreadable configuration never stops
        # the project file from resolving.
        from dotenv import dotenv_values

        from src.config import ENV_FILE

        return (dotenv_values(ENV_FILE).get("PR_DEFAULT_BASE") or "").strip()
    except Exception:
        return ""


def ensure_project_config(path=None, start_dir=None, default_branch=None):
    """Creates the project file when absent. Never raises, never overwrites.

    Without an explicit ``path`` the function is a no-op outside a git
    repository — the file belongs to a repository, and the fallback directory
    of ``project_config_path()`` exists only so readers can still resolve a
    path. An explicit path bypasses that check, which is what tests use.
    """
    explicit = path is not None
    target = Path(path) if explicit else project_config_path(start_dir)

    if not explicit:
        code, _ = _run_git(["rev-parse", "--git-dir"], cwd=start_dir)
        if code != 0:
            return SeedResult(created=False, path=target)

    if target.exists():
        return SeedResult(created=False, path=target)

    branch = (default_branch or _global_default() or "").strip()
    if not branch:
        branch = DEFAULT_BASE_BRANCH

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        body = yaml.safe_dump(
            {"pull_request": {"base_branch": branch}},
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(HEADER_COMMENT)
            handle.write(body)
    except Exception as exc:
        return SeedResult(created=False, path=target, error=str(exc))

    return SeedResult(created=True, path=target, ignored=_is_ignored(target))


def current_branch(start_dir=None):
    """The branch checked out right now; "" on a detached HEAD.

    A pull request is opened *from* this branch, so it can never be the target
    of that same request: merging a branch into itself is not a pull request.
    """
    code, output = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=start_dir)
    if code != 0:
        return ""
    name = output.strip()
    return "" if name == "HEAD" else name


def verify_remote_base(branch, start_dir=None):
    """Raises BaseBranchError unless origin/<branch> resolves.

    ``CurrentBranchError`` (a narrower ``BaseBranchError``) has its own type so
    the CLI can offer the picker instead of just refusing.
    """
    branch = (branch or "").strip()
    if not branch:
        raise BaseBranchError(__("No pull request base branch could be determined."))

    if branch == current_branch(start_dir):
        raise CurrentBranchError(
            __(
                "The pull request target branch '{branch}' is the branch you are on. A pull request cannot target itself — choose another base branch.",
                branch=branch,
            )
        )

    code, _ = _run_git(
        ["rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        cwd=start_dir,
    )
    if code == 0:
        return

    remote_code, _ = _run_git(["remote", "get-url", "origin"], cwd=start_dir)
    if remote_code != 0:
        raise BaseBranchError(
            __(
                "The repository has no 'origin' remote, so the pull request base branch '{branch}' cannot be verified.",
                branch=branch,
            )
        )
    raise BaseBranchError(
        __(
            "The base branch '{branch}' does not exist on origin. Run 'git fetch origin {branch}' and try again, or change the configured base branch.",
            branch=branch,
        )
    )


def resolve_pull_request_base(
    cli_base=None, verify=True, start_dir=None, config_path=None
):
    """Resolves the PR target: --base > project file > env > detection > main.

    ``config_path`` lets the configuration screen point at the same file it
    displays; the CLI and the MCP tool leave it unset.
    """
    warnings = []
    branch = (cli_base or "").strip()
    source = SOURCE_CLI if branch else ""

    if not branch:
        project = read_project_config(path=config_path, start_dir=start_dir)
        if project.error:
            warnings.append(
                __(
                    "⚠️ Ignoring project configuration at {path}: {error}",
                    path=project.path,
                    error=project.error,
                )
            )
        if project.base_branch:
            branch, source = project.base_branch, SOURCE_PROJECT

    if not branch:
        env_value = _global_default()
        if env_value:
            branch, source = env_value, SOURCE_ENV

    if not branch:
        # Imported here so this module stays importable without the AI stack.
        # quiet=True keeps the fallback warning out of the TUI and the MCP
        # JSON-RPC stream; the PR flow still prints it from the diff builder.
        from src.core import get_base_branch

        branch, source = get_base_branch(quiet=True), SOURCE_AUTO

    if verify:
        verify_remote_base(branch, start_dir=start_dir)

    return ResolvedBase(branch=branch, source=source, warnings=tuple(warnings))


def describe_base_source(source):
    """Human-readable label for a ResolvedBase source token."""
    return _SOURCE_LABELS.get(source, source)
