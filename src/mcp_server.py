"""
MCP (Model Context Protocol) Server for GitPR.

Exposes GitPR's AI-powered capabilities as MCP tools and resources,
enabling integration with VS Code, Cursor, Claude Desktop, and other
MCP-compatible editors and AI agents.

Usage:
    gitpr-mcp                        # Start the MCP server (stdio transport)
    gitpr-mcp --list                 # Print the complete tools catalog as JSON
    gitpr-mcp --install vscode       # Install MCP config for VS Code
    gitpr-mcp --install cursor       # Install MCP config for Cursor
    gitpr-mcp --install claude-code  # Install MCP config for Claude Code
    gitpr-mcp --install claude       # Install MCP config for Claude Desktop
    gitpr-mcp --install zed          # Install MCP config for Zed
    gitpr-mcp --install auto         # Auto-detect and install for all found
    gitpr-mcp --tool get_git_context  # Invoke a single tool directly (CLI)
    gitpr-mcp --tool                 # List available tools for --tool
    gitpr --mcp                      # Alias via the main CLI (always starts server)

Transport: stdio (standard for local CLI-tool MCP servers).

Architecture:
    The biggest challenge is that GitPR's existing code uses click.secho(),
    click.echo(), sys.stdout.write() (spinner), and sys.exit() — all of which
    corrupt the JSON-RPC protocol on stdout or kill the server process.

    Solution: monkey-patching applied at main() entry, redirecting ALL
    application output to stderr while preserving sys.__stdout__.buffer
    for the MCP transport layer. This touches ZERO existing modules.
"""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path


# =============================================================================
# Early Stdout Guard
# =============================================================================
# The MCP stdio transport owns stdout.  Any write to stdout that is not a
# JSON-RPC message corrupts the protocol.
#
# THE CRITICAL INSIGHT: some of GitPR's modules (e.g. src.i18n) call
# load_dotenv() at *module level*, which runs during import — BEFORE main()
# and BEFORE _patch_output() have a chance to redirect.  The guard below
# is applied BEFORE any src.* import so those early writes land on stderr
# instead of stdout, keeping the MCP transport clean.
# =============================================================================


class _MCPStdout:
    """A stdout-like object that sends all writes to stderr.

    Exposes the *real* stdout buffer via a .buffer property so the MCP
    stdio_server transport can open its own TextIOWrapper around the
    raw OS-level stdout file descriptor — bypassing this redirect entirely.
    """

    def write(self, text):
        sys.stderr.write(text)

    def flush(self):
        sys.stderr.flush()

    @property
    def buffer(self):
        # The MCP transport needs raw binary access to the real stdout FD.
        # sys.__stdout__ is the original, unpatched stdout object.
        return sys.__stdout__.buffer

    def isatty(self):
        return False


# Apply the stdout guard IMMEDIATELY, before any src.* imports.
# _patch_output() (called later in main()) handles the remaining patches
# (click.secho, click.echo, sys.exit, etc.).
_original_stdout = sys.stdout
sys.stdout = _MCPStdout()

# =============================================================================
# Imports that may write to stdout at module level
# =============================================================================

import click
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from src.i18n import __, CURRENT_LANG

# =============================================================================
# Output Patching System (remaining patches)
# =============================================================================

_original_stdout_write = None
_original_stdout_flush = None
_original_secho = None
_original_echo = None
_original_exit = None
_original_prompt = None
_original_style = None


def _patch_output():
    """Apply remaining output patches: click functions, exit, and prompt.

    sys.stdout is redirected to _MCPStdout at module level (before any
    src.* imports), but this function re-applies the redirect in case
    _unpatch_output() was called (e.g. during testing).
    """
    global _original_stdout_write, _original_stdout_flush
    global _original_secho, _original_echo, _original_style
    global _original_exit, _original_prompt

    # --- Re-apply stdout guard (idempotent — safe if already applied) ---
    if not isinstance(sys.stdout, _MCPStdout):
        sys.stdout = _MCPStdout()

    # --- Save originals ---
    _original_stdout_write = sys.stdout.write
    _original_stdout_flush = sys.stdout.flush
    _original_secho = click.secho
    _original_echo = click.echo
    _original_style = click.style
    _original_exit = sys.exit
    _original_prompt = click.prompt

    # --- Patch click output functions to write to stderr ---
    def _mcp_secho(message=None, **kwargs):
        kwargs.pop("fg", None)
        kwargs.pop("bg", None)
        kwargs.pop("bold", None)
        kwargs.pop("dim", None)
        kwargs.pop("underline", None)
        kwargs.pop("blink", None)
        kwargs.pop("reverse", None)
        kwargs.pop("reset", None)
        kwargs["err"] = True
        try:
            _original_secho(message, **kwargs)
        except Exception:
            # If click internals fail (e.g. no context), fall back to print
            if message is not None:
                print(message, file=sys.stderr)

    def _mcp_echo(message=None, **kwargs):
        kwargs["err"] = True
        try:
            _original_echo(message, **kwargs)
        except Exception:
            if message is not None:
                print(message, file=sys.stderr)

    def _mcp_style(text, **kwargs):
        # In MCP mode, strip all styling — return plain text
        return text

    click.secho = _mcp_secho
    click.echo = _mcp_echo
    click.style = _mcp_style

    # Neutralise sys.exit
    def _mcp_exit(code=0):
        raise SystemExit(code)

    sys.exit = _mcp_exit

    # Block interactive prompts
    def _mcp_prompt(*args, **kwargs):
        raise RuntimeError(
            __(
                "Interactive prompt is unavailable in MCP mode. "
                "Configure your API keys in ~/.gitpr/.env before using MCP tools."
            )
        )

    click.prompt = _mcp_prompt


def _unpatch_output():
    """Restore originals (useful for testing and clean shutdown)."""
    global _original_stdout
    if _original_stdout is not None:
        sys.stdout = _original_stdout
    if _original_secho is not None:
        click.secho = _original_secho
    if _original_echo is not None:
        click.echo = _original_echo
    if _original_style is not None:
        click.style = _original_style
    if _original_exit is not None:
        sys.exit = _original_exit
    if _original_prompt is not None:
        click.prompt = _original_prompt


# =============================================================================
# Silent Configuration Initialization
# =============================================================================

ENV_FILE = Path.home() / ".gitpr" / ".env"


def _init_config():
    """Load .env silently.  Do NOT call setup_environment() which prompts."""
    load_dotenv(ENV_FILE)

    # Apply language from .env if present
    lang = os.getenv("GITPR_LANG")
    if lang:
        try:
            from src.i18n import set_lang
            from src.spinner import reload_thinking_words

            set_lang(lang)
            reload_thinking_words(lang)
        except Exception:
            pass  # Translation is best-effort; the tool still works without it


# =============================================================================
# Safe Call Wrapper
# =============================================================================


def _safe_call(fn, *args, **kwargs):
    """Call a GitPR function, catching SystemExit and unexpected errors.

    Returns:
        The function's return value, or None if an error occurred.
    """
    try:
        return fn(*args, **kwargs)
    except SystemExit:
        return None
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return None


# =============================================================================
# Helper: resolve the active AI provider
# =============================================================================


def _resolve_provider(requested: str) -> str:
    """Return the effective provider: explicit override or the .env default."""
    if requested:
        return requested
    try:
        from src.config import get_ai_provider

        return _safe_call(get_ai_provider) or "gemini"
    except Exception:
        return "gemini"


# =============================================================================
# FastMCP Application
# =============================================================================

mcp = FastMCP(
    "gitpr",
    instructions=__(
        "GitPR — Intelligent PR Automation and AI Code Review. "
        "Generate commit messages, review code, run linters, "
        "trace code origins, and create issues — all from your IDE."
    ),
)


# =============================================================================
# Tools — Git Context
# =============================================================================


@mcp.tool(
    description=__(
        "Get the current git branch, repository name, and remote origin URL."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def get_git_context() -> str:
    """Return JSON with branch name and repository info."""
    from src.core import get_current_branch, get_repo_name

    branch = _safe_call(get_current_branch) or "unknown"
    repo = _safe_call(get_repo_name) or "unknown/repo"

    return json.dumps(
        {
            "branch": branch,
            "repository": repo,
        }
    )


# =============================================================================
# Tools — Diff Inspection
# =============================================================================


@mcp.tool(
    description=__(
        "Get the current uncommitted git diff (git diff HEAD — "
        "includes both staged and unstaged changes). "
    )
    + __("Lists all changed files and their line-level modifications."),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def analyze_diff() -> str:
    """Return the raw git diff for uncommitted local changes."""
    from src.core import get_git_diff

    diff = _safe_call(get_git_diff, quiet=True)
    if not diff or not diff.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("No uncommitted changes detected."),
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "status": "changes_found",
            "diff": diff,
        },
        ensure_ascii=False,
    )


@mcp.tool(
    description=__(
        "List uncommitted file changes categorized as new (untracked), "
        "modified (unstaged modifications) or deleted. Returns structured JSON."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def list_unstaged_files() -> str:
    """Return JSON with new/modified/deleted lists of unstaged files."""
    from src.core import get_unstaged_categorized

    data = _safe_call(get_unstaged_categorized) or {}
    new_files = data.get("new", [])
    modified_files = data.get("modified", [])
    deleted_files = data.get("deleted", [])
    total = len(new_files) + len(modified_files) + len(deleted_files)
    files = []
    for f in new_files:
        files.append({"path": f, "type": "new"})
    for f in modified_files:
        files.append({"path": f, "type": "modified"})
    for f in deleted_files:
        files.append({"path": f, "type": "deleted"})
    return json.dumps(
        {
            "status": "changes_found" if total else "no_changes",
            "new": new_files,
            "modified": modified_files,
            "deleted": deleted_files,
            "files": files,
            "total": total,
            "message": "" if total else __("No unstaged files found."),
        },
        ensure_ascii=False,
    )


@mcp.tool(
    description=__(
        "Get only the unstaged git diff (git diff without HEAD — "
        "compares the index against the working tree). Excludes staged "
        "changes. Untracked files are not shown; use list_unstaged_files for them."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def analyze_unstaged_diff() -> str:
    """Return the raw git diff for unstaged changes only (index vs working tree)."""
    from src.core import get_unstaged_diff

    diff = _safe_call(get_unstaged_diff, quiet=True)
    if not diff or not diff.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("No unstaged changes detected."),
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "status": "changes_found",
            "diff": diff,
        },
        ensure_ascii=False,
    )


@mcp.tool(
    description=__(
        "Get the full diff of the current branch against the remote "
        "base branch (origin/main or origin/master). Runs git fetch first."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=False
    ),
)
def get_full_diff() -> str:
    """Return the full diff between the current branch and origin/main."""
    from src.core import get_git_full_diff

    diff = _safe_call(get_git_full_diff)
    if not diff or not diff.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("No changes detected against the base branch."),
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "status": "changes_found",
            "diff": diff,
        },
        ensure_ascii=False,
    )


# =============================================================================
# Tools — AI-Powered Analysis
# =============================================================================


@mcp.tool(
    description=__(
        "Generate a Conventional Commits commit message from the "
        "current git diff using AI. "
        "Returns a message like 'feat: add user authentication'."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=False
    ),
)
def generate_commit_message(
    provider: str = "",
    diff_text: str = "",
) -> str:
    """Generate an AI commit message from a diff.

    Args:
        provider: Override AI provider (gemini, deepseek, ollama).
                  Empty uses the default from ~/.gitpr/.env.
        diff_text: Optional diff text. If empty, auto-detects from git.
    """
    from src.core import generate_pr_content, get_git_diff

    if not diff_text:
        diff_text = _safe_call(get_git_diff, quiet=True) or ""

    if not diff_text.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("No diff to analyze. Make some changes first."),
            },
            ensure_ascii=False,
        )

    active_provider = _resolve_provider(provider)
    result = _safe_call(
        generate_pr_content, "commit", "commit", diff_text, active_provider
    )

    if result and "commit_message" in result:
        return json.dumps(
            {
                "status": "success",
                "commit_message": result["commit_message"],
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "error",
            "message": __("AI failed to generate a commit message."),
        },
        ensure_ascii=False,
    )


@mcp.tool(
    description=__(
        "Perform an AI code review on uncommitted local changes "
        "(git diff HEAD). Returns structured feedback with issues "
        "and improvement suggestions."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=False
    ),
)
def review_code(
    provider: str = "",
    diff_text: str = "",
) -> str:
    """AI code review of local (uncommitted) changes.

    Args:
        provider: Override AI provider (gemini, deepseek, ollama).
        diff_text: Optional diff text. If empty, auto-detects from git.
    """
    from src.core import generate_pr_content, get_git_diff

    if not diff_text:
        diff_text = _safe_call(get_git_diff, quiet=True) or ""

    if not diff_text.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("No diff to review."),
            },
            ensure_ascii=False,
        )

    active_provider = _resolve_provider(provider)
    result = _safe_call(
        generate_pr_content, "review", "review", diff_text, active_provider
    )

    if result and "review" in result:
        return json.dumps(
            {
                "status": "success",
                "review": result["review"],
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "error",
            "message": __("AI failed to generate a review."),
        },
        ensure_ascii=False,
    )


@mcp.tool(
    description=__(
        "Perform a full AI code review comparing the entire current "
        "branch against origin/main. Runs git fetch automatically."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=False
    ),
)
def full_review(provider: str = "") -> str:
    """AI code review of all changes since origin/main.

    Args:
        provider: Override AI provider (gemini, deepseek, ollama).
    """
    from src.core import generate_pr_content, get_git_full_diff

    diff_text = _safe_call(get_git_full_diff) or ""
    if not diff_text.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("No changes against the base branch."),
            },
            ensure_ascii=False,
        )

    active_provider = _resolve_provider(provider)
    result = _safe_call(
        generate_pr_content, "fullreview", "fullreview", diff_text, active_provider
    )

    if result and "review" in result:
        return json.dumps(
            {
                "status": "success",
                "review": result["review"],
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "error",
            "message": __("AI failed to generate a full review."),
        },
        ensure_ascii=False,
    )


@mcp.tool(
    description=__(
        "Generate a complete Pull Request description (title + body) "
        "from the full diff against origin/main. Uses AI to create a "
        "structured, professional PR document."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=False
    ),
)
def generate_pr_description(provider: str = "") -> str:
    """Generate a full PR description from the branch diff.

    Args:
        provider: Override AI provider (gemini, deepseek, ollama).
    """
    from src.core import generate_pr_content, get_git_full_diff

    diff_text = _safe_call(get_git_full_diff) or ""
    if not diff_text.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("No changes against the base branch."),
            },
            ensure_ascii=False,
        )

    active_provider = _resolve_provider(provider)
    result = _safe_call(generate_pr_content, "pr", "pr", diff_text, active_provider)

    if result:
        return json.dumps(
            {
                "status": "success",
                "commit_message": result.get("commit_message", ""),
                "pr_description": result.get("pr_description", ""),
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "error",
            "message": __("AI failed to generate a PR description."),
        },
        ensure_ascii=False,
    )


# =============================================================================
# Tools — Linter
# =============================================================================


@mcp.tool(
    description=__(
        "Run the static local linter (regex-based rules from "
        ".gitpr.linter.yml) on the current git diff. "
        "Returns error and warning counts with detailed messages."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def run_linter() -> str:
    """Analyze the current diff against .gitpr.linter.yml rules."""
    from src.core import get_git_diff
    from src.linter_engine import parse_diff_and_lint

    diff_text = _safe_call(get_git_diff, quiet=True) or ""
    if not diff_text.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("Empty diff — nothing to lint."),
            },
            ensure_ascii=False,
        )

    results = _safe_call(parse_diff_and_lint, diff_text) or {
        "errors": [],
        "warnings": [],
    }

    return json.dumps(
        {
            "status": "success",
            "error_count": len(results.get("errors", [])),
            "warning_count": len(results.get("warnings", [])),
            "errors": results.get("errors", []),
            "warnings": results.get("warnings", []),
            "passed": len(results.get("errors", [])) == 0,
        },
        ensure_ascii=False,
    )


# =============================================================================
# Tools — Code Archaeology (Blame)
# =============================================================================


@mcp.tool(
    description=__(
        "Run AI-powered git blame analysis on a file region to trace "
        "the origin of business rules. Classifies each commit as "
        "ORIGIN (first introduction) or REFACTORING (later change)."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=False
    ),
)
def analyze_blame(
    file_path: str,
    start_line: str,
    end_line: str,
) -> str:
    """Trace the history of a code region through git blame + AI classification.

    Args:
        file_path: Path to the source file (relative to the repository root).
        start_line: Starting line number (as a string, e.g. "42").
        end_line: Ending line number (as a string, e.g. "58").
    """
    from src.blame_engine import run_blame_analysis

    if not os.path.exists(file_path):
        return json.dumps(
            {
                "status": "error",
                "message": __("File not found: {file_path}", file_path=file_path),
            },
            ensure_ascii=False,
        )

    timeline = _safe_call(
        run_blame_analysis, file_path, start_line, end_line, return_data=True
    )

    if not timeline:
        return json.dumps(
            {
                "status": "no_data",
                "message": __("No traceable commits found for this region."),
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "success",
            "entries": timeline,
        },
        ensure_ascii=False,
        default=str,
    )


# =============================================================================
# Tools — Issue Generation
# =============================================================================


@mcp.tool(
    description=__(
        "Generate a structured Issue (What / Why / Where / How) from "
        "code context using AI. Supports three modes: diff (current "
        "changes), history (branch history), or blame (file region)."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=False
    ),
)
def generate_issue(context_type: str = "diff") -> str:
    """Generate an issue from code context.

    Args:
        context_type: Context source — "diff" (default), "history", or "blame".
    """
    from src.core import get_git_diff, get_branch_history_text
    from src.issue_engine import generate_issue_content

    if context_type == "history":
        context_text = _safe_call(get_branch_history_text) or ""
    else:
        context_text = _safe_call(get_git_diff, quiet=True) or ""

    if not context_text.strip():
        return json.dumps(
            {
                "status": "no_changes",
                "message": __("No context available for issue generation."),
            },
            ensure_ascii=False,
        )

    result = _safe_call(generate_issue_content, context_text, context_type=context_type)

    if result:
        return json.dumps(
            {
                "status": "success",
                "title": result.get("titulo", ""),
                "body": result.get("corpo", ""),
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "error",
            "message": __("AI failed to generate an issue."),
        },
        ensure_ascii=False,
    )


# =============================================================================
# Resources — Skill Templates & Linter Config
# =============================================================================

SKILL_FILES = {
    "pr": ".gitpr.pr.md",
    "commit": ".gitpr.commit.md",
    "review": ".gitpr.review.md",
    "filereview": ".gitpr.filereview.md",
    "issue": ".gitpr.issue.md",
    "blame": ".gitpr.blame.md",
}

# Prompt template files (message templates for common MCP flows).
# Each prompt has a base English file and optional language variants
# (e.g. gitpr.prompt.review.pt_br.md).
PROMPT_FILES = {
    "review": "gitpr.prompt.review.md",
    "commit": "gitpr.prompt.commit.md",
    "pr": "gitpr.prompt.pr.md",
    "linter": "gitpr.prompt.linter.md",
    "issue": "gitpr.prompt.issue.md",
    "blame": "gitpr.prompt.blame.md",
    "explore": "gitpr.prompt.explore.md",
}


def _read_resource_file(filename: str) -> str:
    """Read a skill or config file from the project's .gitpr/skill/ directory.

    Returns the file contents or a JSON error object.
    """
    try:
        from src.config import resolve_skill_path

        path = resolve_skill_path(filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except Exception:
        pass
    return json.dumps(
        {
            "status": "not_found",
            "message": __(
                "Resource '{filename}' not found. Run 'gitpr --skill' to download templates.",
                filename=filename,
            ),
        }
    )


def _read_prompt_file(prompt_name: str) -> str:
    """Load prompt content from a template file with language fallback.

    Tries the language-specific variant first (e.g.
    gitpr.prompt.review.pt_br.md), falling back to the English base
    file (gitpr.prompt.review.md).  Returns an empty string when
    neither file can be found.

    Search order (first match wins):
      1. <cwd>/templates/          — development / project-local
      2. <cwd>/.gitpr/skill/       — downloaded via --skill
      3. <package>/templates/      — bundled with the installation
    """
    base_filename = PROMPT_FILES.get(prompt_name)
    if not base_filename:
        return ""

    # Build language-specific filename
    if not CURRENT_LANG.startswith("en"):
        name_part, ext = base_filename.rsplit(".", 1)
        lang_filename = f"{name_part}.{CURRENT_LANG}.{ext}"
    else:
        lang_filename = base_filename

    # Search directories in priority order
    search_dirs = [
        os.path.join(os.getcwd(), "templates"),  # dev / project-local
        os.path.join(os.getcwd(), ".gitpr", "skill"),  # downloaded
        os.path.join(os.path.dirname(__file__), "..", "templates"),  # bundled
    ]

    def _try_read(search_dir, filename):
        path = os.path.join(search_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read().strip()
            except Exception:
                pass
        return None

    for search_dir in search_dirs:
        # Try language variant first
        result = _try_read(search_dir, lang_filename)
        if result:
            return result

    # Fallback to English base in all directories
    for search_dir in search_dirs:
        result = _try_read(search_dir, base_filename)
        if result:
            return result

    return ""


@mcp.resource(
    uri="skill://list",
    name=__("Available Skill Templates"),
    description=__("Lists all available skill template resource URIs."),
    mime_type="application/json",
)
def list_skills() -> str:
    """Return a JSON list of available skill and config resource URIs."""
    return json.dumps(
        {
            "skills": [f"skill://{name}" for name in SKILL_FILES],
            "linter": "linter://config",
        }
    )


@mcp.resource(
    uri="skill://pr",
    name=__("PR Description Template"),
    description=__("Custom AI instructions for generating Pull Request descriptions."),
    mime_type="text/markdown",
)
def get_skill_pr() -> str:
    return _read_resource_file(".gitpr.pr.md")


@mcp.resource(
    uri="skill://commit",
    name=__("Commit Message Template"),
    description=__("Custom AI instructions for generating commit messages."),
    mime_type="text/markdown",
)
def get_skill_commit() -> str:
    return _read_resource_file(".gitpr.commit.md")


@mcp.resource(
    uri="skill://review",
    name=__("Code Review Template"),
    description=__("Custom AI instructions for code reviews."),
    mime_type="text/markdown",
)
def get_skill_review() -> str:
    return _read_resource_file(".gitpr.review.md")


@mcp.resource(
    uri="skill://filereview",
    name=__("File Review Template"),
    description=__("Custom AI instructions for full-file audits."),
    mime_type="text/markdown",
)
def get_skill_filereview() -> str:
    return _read_resource_file(".gitpr.filereview.md")


@mcp.resource(
    uri="skill://issue",
    name=__("Issue Template"),
    description=__("Custom AI instructions for generating issues."),
    mime_type="text/markdown",
)
def get_skill_issue() -> str:
    return _read_resource_file(".gitpr.issue.md")


@mcp.resource(
    uri="skill://blame",
    name=__("Blame Analysis Template"),
    description=__("Custom AI instructions for code archaeology (blame)."),
    mime_type="text/markdown",
)
def get_skill_blame() -> str:
    return _read_resource_file(".gitpr.blame.md")


@mcp.resource(
    uri="linter://config",
    name=__("Linter Configuration"),
    description=__("YAML rules for the static local linter."),
    mime_type="text/yaml",
)
def get_linter_config() -> str:
    return _read_resource_file(".gitpr.linter.yml")


# =============================================================================
# Resources — Prompt Templates
# =============================================================================


@mcp.resource(
    uri="prompt://list",
    name=__("Available Prompt Templates"),
    description=__("Lists all available MCP prompt template URIs."),
    mime_type="application/json",
)
def list_prompts() -> str:
    """Return a JSON list of available prompt resource URIs."""
    prompts = [f"prompt://{name}" for name in PROMPT_FILES]

    try:
        from src.config import get_prompt_plugins
        import os as _os

        for plugin_path in get_prompt_plugins():
            plugin_name = _os.path.basename(plugin_path).replace(".md", "")
            prompts.append(f"prompt://plugin/{plugin_name}")
    except Exception:
        pass

    return json.dumps(
        {
            "prompts": prompts,
        }
    )


@mcp.resource(
    uri="prompt://review",
    name=__("Review PR Prompt"),
    description=__("Prompt template: full code review of the current branch."),
    mime_type="text/markdown",
)
def get_prompt_review() -> str:
    return _read_prompt_file("review")


@mcp.resource(
    uri="prompt://commit",
    name=__("Commit Message Prompt"),
    description=__("Prompt template: generate a Conventional Commits message."),
    mime_type="text/markdown",
)
def get_prompt_commit() -> str:
    return _read_prompt_file("commit")


@mcp.resource(
    uri="prompt://pr",
    name=__("PR Description Prompt"),
    description=__("Prompt template: generate a Pull Request description."),
    mime_type="text/markdown",
)
def get_prompt_pr() -> str:
    return _read_prompt_file("pr")


@mcp.resource(
    uri="prompt://linter",
    name=__("Linter Prompt"),
    description=__("Prompt template: run the static linter on changes."),
    mime_type="text/markdown",
)
def get_prompt_linter() -> str:
    return _read_prompt_file("linter")


@mcp.resource(
    uri="prompt://issue",
    name=__("Issue Prompt"),
    description=__("Prompt template: generate a structured issue from changes."),
    mime_type="text/markdown",
)
def get_prompt_issue() -> str:
    return _read_prompt_file("issue")


@mcp.resource(
    uri="prompt://blame",
    name=__("Blame Prompt"),
    description=__("Prompt template: trace code origin with git blame + AI."),
    mime_type="text/markdown",
)
def get_prompt_blame() -> str:
    return _read_prompt_file("blame")


@mcp.resource(
    uri="prompt://explore",
    name=__("Explore Prompt"),
    description=__("Prompt template: explore project context and available skills."),
    mime_type="text/markdown",
)
def get_prompt_explore() -> str:
    return _read_prompt_file("explore")


# =============================================================================
# Prompts — Message Templates for Common Flows
# =============================================================================
# Prompts are pre-defined message templates that users can select in their
# editor's AI chat. Unlike tools (which execute automatically), prompts are
# starter messages that guide the AI to invoke the right GitPR tools.
#
# Prompt content is loaded from template files in templates/ (with language
# variants), so translations can be updated independently of the Python code.
# =============================================================================


@mcp.prompt(
    name=__("Review PR"),
    description=__(
        "Full code review of all changes in the current branch against origin/main. "
        "Runs the full review tool and linter, then composes a comprehensive report."
    ),
)
def review_pr_prompt() -> str:
    """Prompt: full code review of the current branch."""
    return _read_prompt_file("review")


@mcp.prompt(
    name=__("Generate Commit Message"),
    description=__(
        "Generate a Conventional Commits message (e.g., 'feat: add user auth') "
        "from the current uncommitted changes."
    ),
)
def generate_commit_message_prompt() -> str:
    """Prompt: generate a commit message from uncommitted changes."""
    return _read_prompt_file("commit")


@mcp.prompt(
    name=__("Create PR Description"),
    description=__(
        "Generate a complete Pull Request description (title + body) "
        "from all changes in the current branch."
    ),
)
def create_pr_description_prompt() -> str:
    """Prompt: generate a full PR description."""
    return _read_prompt_file("pr")


@mcp.prompt(
    name=__("Run Code Linter"),
    description=__(
        "Run the static linter (.gitpr.linter.yml rules) on current "
        "uncommitted changes and report violations."
    ),
)
def run_linter_prompt() -> str:
    """Prompt: run the static linter on current changes."""
    return _read_prompt_file("linter")


@mcp.prompt(
    name=__("Create Issue from Diff"),
    description=__(
        "Generate a structured issue (What / Why / Where / How) from "
        "the current uncommitted changes."
    ),
)
def create_issue_prompt() -> str:
    """Prompt: generate an issue from the current diff."""
    return _read_prompt_file("issue")


@mcp.prompt(
    name=__("Trace Code Origin"),
    description=__(
        "Investigate the history of a specific file region using git "
        "blame + AI to trace where business rules came from."
    ),
)
def trace_code_origin_prompt() -> str:
    """Prompt: trace the origin of code in a file region."""
    return _read_prompt_file("blame")


@mcp.prompt(
    name=__("Explore Project Context"),
    description=__(
        "Get current branch info, repository name, and list available "
        "skill templates for the project."
    ),
)
def explore_project_prompt() -> str:
    """Prompt: explore the current git context and available skills."""
    return _read_prompt_file("explore")


def _register_plugin_prompts():
    """Dynamically registers custom user prompts from plugins folder as MCP resources and prompts."""
    try:
        from src.config import get_prompt_plugins
        import os as _os

        for plugin_path in get_prompt_plugins():
            plugin_name = _os.path.basename(plugin_path).replace(".md", "")
            uri_string = f"prompt://plugin/{plugin_name}"

            # Using closures to prevent late-binding issues in loops
            def make_resource_handler(path, uri, name):
                @mcp.resource(
                    uri=uri,
                    name=f"Plugin: {name}",
                    description=f"Custom plugin prompt: {name}",
                    mime_type="text/markdown",
                )
                def resource_handler() -> str:
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read()
                    except Exception:
                        return ""

                return resource_handler

            def make_prompt_handler(path, name):
                @mcp.prompt(
                    name=f"Plugin: {name}",
                    description=f"Custom AI prompt loaded from plugins: {name}",
                )
                def prompt_handler() -> str:
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read()
                    except Exception:
                        return ""

                return prompt_handler

            make_resource_handler(plugin_path, uri_string, plugin_name)
            make_prompt_handler(plugin_path, plugin_name)

    except Exception:
        pass  # Silently skip if plugins fail to load so the MCP server boots normally


# Fire the dynamic registration immediately
_register_plugin_prompts()


# =============================================================================
# Tools Catalog — metadata for gitpr-mcp --list
# =============================================================================
# This catalog mirrors the @mcp.tool(), @mcp.resource(), and @mcp.prompt()
# decorators above.  It is used by the --list CLI flag to print a complete
# inventory of the server's capabilities as JSON, so that editors, IDEs and
# AI agents can discover available tools without having to connect to the
# running MCP server via stdio.


def _build_tools_catalog() -> dict:
    """Return a complete catalog of all MCP tools, resources, and prompts.

    The returned dict is JSON-serialisable and safe for printing to stdout
    (no stdio-patching required — --list runs BEFORE the MCP transport).
    """
    from src.updater import __version__

    return {
        "server": "gitpr",
        "version": __version__,
        "tools": [
            {
                "name": "get_git_context",
                "description": "Get the current git branch, repository name, and remote origin URL.",
                "parameters": {},
                "annotations": {"readOnlyHint": True, "idempotentHint": True},
            },
            {
                "name": "analyze_diff",
                "description": "Get the current uncommitted git diff (git diff HEAD — includes both staged and unstaged changes). Lists all changed files and their line-level modifications.",
                "parameters": {},
                "annotations": {"readOnlyHint": True, "idempotentHint": True},
            },
            {
                "name": "list_unstaged_files",
                "description": "List uncommitted file changes categorized as new (untracked), modified (unstaged modifications) or deleted. Returns structured JSON.",
                "parameters": {},
                "annotations": {"readOnlyHint": True, "idempotentHint": True},
            },
            {
                "name": "analyze_unstaged_diff",
                "description": "Get only the unstaged git diff (git diff without HEAD — compares the index against the working tree). Excludes staged changes. Untracked files are not shown; use list_unstaged_files for them.",
                "parameters": {},
                "annotations": {"readOnlyHint": True, "idempotentHint": True},
            },
            {
                "name": "get_full_diff",
                "description": "Get the full diff of the current branch against the remote base branch (origin/main or origin/master). Runs git fetch first.",
                "parameters": {},
                "annotations": {
                    "readOnlyHint": False,
                    "destructiveHint": False,
                    "idempotentHint": False,
                },
            },
            {
                "name": "generate_commit_message",
                "description": "Generate a Conventional Commits commit message from the current git diff using AI. Returns a message like 'feat: add user authentication'.",
                "parameters": {
                    "provider": {
                        "type": "string",
                        "required": False,
                        "description": "AI provider override: gemini, deepseek, or ollama. Empty uses default from ~/.gitpr/.env.",
                    },
                    "diff_text": {
                        "type": "string",
                        "required": False,
                        "description": "Optional diff text. If empty, auto-detects from git.",
                    },
                },
                "annotations": {
                    "readOnlyHint": False,
                    "destructiveHint": False,
                    "idempotentHint": False,
                },
            },
            {
                "name": "review_code",
                "description": "Perform an AI code review on uncommitted local changes (git diff HEAD). Returns structured feedback with issues and improvement suggestions.",
                "parameters": {
                    "provider": {
                        "type": "string",
                        "required": False,
                        "description": "AI provider override: gemini, deepseek, or ollama.",
                    },
                    "diff_text": {
                        "type": "string",
                        "required": False,
                        "description": "Optional diff text. If empty, auto-detects from git.",
                    },
                },
                "annotations": {
                    "readOnlyHint": False,
                    "destructiveHint": False,
                    "idempotentHint": False,
                },
            },
            {
                "name": "full_review",
                "description": "Perform a full AI code review comparing the entire current branch against origin/main. Runs git fetch automatically.",
                "parameters": {
                    "provider": {
                        "type": "string",
                        "required": False,
                        "description": "AI provider override: gemini, deepseek, or ollama.",
                    },
                },
                "annotations": {
                    "readOnlyHint": False,
                    "destructiveHint": False,
                    "idempotentHint": False,
                },
            },
            {
                "name": "generate_pr_description",
                "description": "Generate a complete Pull Request description (title + body) from the full diff against origin/main. Uses AI to create a structured, professional PR document.",
                "parameters": {
                    "provider": {
                        "type": "string",
                        "required": False,
                        "description": "AI provider override: gemini, deepseek, or ollama.",
                    },
                },
                "annotations": {
                    "readOnlyHint": False,
                    "destructiveHint": False,
                    "idempotentHint": False,
                },
            },
            {
                "name": "run_linter",
                "description": "Run the static local linter (regex-based rules from .gitpr.linter.yml) on the current git diff. Returns error and warning counts with detailed messages.",
                "parameters": {},
                "annotations": {"readOnlyHint": True, "idempotentHint": True},
            },
            {
                "name": "analyze_blame",
                "description": "Run AI-powered git blame analysis on a file region to trace the origin of business rules. Classifies each commit as ORIGIN (first introduction) or REFACTORING (later change).",
                "parameters": {
                    "file_path": {
                        "type": "string",
                        "required": True,
                        "description": "Path to the source file (relative to the repository root).",
                    },
                    "start_line": {
                        "type": "string",
                        "required": True,
                        "description": "Starting line number (as a string, e.g. '42').",
                    },
                    "end_line": {
                        "type": "string",
                        "required": True,
                        "description": "Ending line number (as a string, e.g. '58').",
                    },
                },
                "annotations": {
                    "readOnlyHint": False,
                    "destructiveHint": False,
                    "idempotentHint": False,
                },
            },
            {
                "name": "generate_issue",
                "description": "Generate a structured Issue (What / Why / Where / How) from code context using AI. Supports three modes: diff (current changes), history (branch history), or blame (file region).",
                "parameters": {
                    "context_type": {
                        "type": "string",
                        "required": False,
                        "description": "Context source: 'diff' (default), 'history', or 'blame'.",
                    },
                },
                "annotations": {
                    "readOnlyHint": False,
                    "destructiveHint": False,
                    "idempotentHint": False,
                },
            },
        ],
        "resources": [
            {
                "uri": "skill://list",
                "name": "Available Skill Templates",
                "description": "Lists all available skill template resource URIs.",
                "mimeType": "application/json",
            },
            {
                "uri": "skill://pr",
                "name": "PR Description Template",
                "description": "Custom AI instructions for generating Pull Request descriptions.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "skill://commit",
                "name": "Commit Message Template",
                "description": "Custom AI instructions for generating commit messages.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "skill://review",
                "name": "Code Review Template",
                "description": "Custom AI instructions for code reviews.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "skill://filereview",
                "name": "File Review Template",
                "description": "Custom AI instructions for full-file audits.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "skill://issue",
                "name": "Issue Template",
                "description": "Custom AI instructions for generating issues.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "skill://blame",
                "name": "Blame Analysis Template",
                "description": "Custom AI instructions for code archaeology (blame).",
                "mimeType": "text/markdown",
            },
            {
                "uri": "linter://config",
                "name": "Linter Configuration",
                "description": "YAML rules for the static local linter.",
                "mimeType": "text/yaml",
            },
            {
                "uri": "prompt://list",
                "name": "Available Prompt Templates",
                "description": "Lists all available MCP prompt template URIs.",
                "mimeType": "application/json",
            },
            {
                "uri": "prompt://review",
                "name": "Review PR Prompt",
                "description": "Prompt template: full code review of the current branch.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "prompt://commit",
                "name": "Commit Message Prompt",
                "description": "Prompt template: generate a Conventional Commits message.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "prompt://pr",
                "name": "PR Description Prompt",
                "description": "Prompt template: generate a Pull Request description.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "prompt://linter",
                "name": "Linter Prompt",
                "description": "Prompt template: run the static linter on changes.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "prompt://issue",
                "name": "Issue Prompt",
                "description": "Prompt template: generate a structured issue from changes.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "prompt://blame",
                "name": "Blame Prompt",
                "description": "Prompt template: trace code origin with git blame + AI.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "prompt://explore",
                "name": "Explore Prompt",
                "description": "Prompt template: explore project context and available skills.",
                "mimeType": "text/markdown",
            },
        ],
        "prompts": [
            {
                "name": "Review PR",
                "description": "Full code review of all changes in the current branch against origin/main. Runs the full review tool and linter, then composes a comprehensive report.",
            },
            {
                "name": "Generate Commit Message",
                "description": "Generate a Conventional Commits message (e.g., 'feat: add user auth') from the current uncommitted changes.",
            },
            {
                "name": "Create PR Description",
                "description": "Generate a complete Pull Request description (title + body) from all changes in the current branch.",
            },
            {
                "name": "Run Code Linter",
                "description": "Run the static linter (.gitpr.linter.yml rules) on current uncommitted changes and report violations.",
            },
            {
                "name": "Create Issue from Diff",
                "description": "Generate a structured issue (What / Why / Where / How) from the current uncommitted changes.",
            },
            {
                "name": "Trace Code Origin",
                "description": "Investigate the history of a specific file region using git blame + AI to trace where business rules came from.",
            },
            {
                "name": "Explore Project Context",
                "description": "Get current branch info, repository name, and list available skill templates for the project.",
            },
        ],
    }


def _get_tools_catalog_json() -> str:
    """Return the tools catalog as a JSON string with indentation."""
    return json.dumps(_build_tools_catalog(), indent=2, ensure_ascii=False)


def _get_compact_tools() -> list[dict]:
    """Return a compact tool list (name + description only) for embedding in config files.

    Each entry: {"name": "...", "description": "..."}
    Used by --install to enrich editor config files with tool metadata.
    """
    catalog = _build_tools_catalog()
    return [
        {"name": t["name"], "description": t["description"]} for t in catalog["tools"]
    ]


def _write_real_stdout(text: str) -> None:
    """Write *text* to the real OS-level stdout, bypassing the _MCPStdout guard.

    Used by --list and --tool modes so that JSON output lands on actual
    stdout, where human users and scripts can capture it.  All application
    noise (spinners, banners, click output) has already been routed to
    stderr by the guard + _patch_output().

    Falls back to a plain ``print()`` if neither ``sys.__stdout__`` nor
    ``_original_stdout`` is available.
    """
    real_stdout = getattr(sys, "__stdout__", None)
    if real_stdout is None:
        real_stdout = _original_stdout
    try:
        real_stdout.write(text)
        real_stdout.flush()
    except Exception:
        # Last resort: print normally (may end up on stderr but won't crash)
        print(text)


def _run_list() -> None:
    """Handle the --list command: print the tools catalog to stdout as JSON.

    Writes directly to the *real* stdout (bypassing the _MCPStdout guard
    that redirects application output to stderr) so that agents can call
    ``gitpr-mcp --list``, capture stdout, and parse the JSON without
    needing to connect to the stdio MCP transport.
    """
    _write_real_stdout(_get_tools_catalog_json() + "\n")


# =============================================================================
# Direct Tool Invocation (gitpr-mcp --tool <name> [--tool-args <json>])
# =============================================================================

# Map tool name → callable.  Built from the @mcp.tool() functions above.
# The parameter metadata lives in _build_tools_catalog()["tools"] and is
# merged at runtime by _get_tool_registry() — keeping callables and
# metadata in separate dicts means --list can still json.dumps the catalog.
_TOOL_FUNCS = {
    "get_git_context": get_git_context,
    "analyze_diff": analyze_diff,
    "list_unstaged_files": list_unstaged_files,
    "analyze_unstaged_diff": analyze_unstaged_diff,
    "get_full_diff": get_full_diff,
    "generate_commit_message": generate_commit_message,
    "review_code": review_code,
    "full_review": full_review,
    "generate_pr_description": generate_pr_description,
    "run_linter": run_linter,
    "analyze_blame": analyze_blame,
    "generate_issue": generate_issue,
}


def _get_tool_registry() -> dict:
    """Return ``{name: {name, description, parameters, func}, ...}``.

    Merges the hand-maintained catalog (parameter metadata) with the
    ``_TOOL_FUNCS`` dict (actual callables).  The two are kept separate
    so that ``_build_tools_catalog()`` remains JSON-serialisable for
    ``--list``.
    """
    registry = {}
    catalog_tools = _build_tools_catalog()["tools"]
    for tool in catalog_tools:
        name = tool["name"]
        registry[name] = {
            "name": name,
            "description": tool["description"],
            "parameters": tool.get("parameters", {}),
            "func": _TOOL_FUNCS.get(name),
        }
    return registry


def _prettify_result(raw: str) -> str:
    """Try to parse *raw* as JSON and re-dump with indentation.

    Returns *raw* unchanged if it is not valid JSON — some tools return
    plain-text diffs rather than JSON objects.
    """
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return raw


def _print_tool_help() -> None:
    """Print a human-readable list of available tools to real stdout."""
    registry = _get_tool_registry()
    lines = [
        "",
        "Available tools - gitpr-mcp --tool <name> [--tool-args '<json>']",
        "=" * 72,
        "",
    ]
    for name in sorted(registry):
        entry = registry[name]
        params = entry["parameters"]
        if params:
            required = [p for p, m in params.items() if m.get("required")]
            optional = [p for p, m in params.items() if not m.get("required")]
            tags = []
            if required:
                tags.append("(required) " + ", ".join(required))
            if optional:
                tags.append("(optional) " + ", ".join(optional))
            param_str = "  ".join(tags)
            lines.append(f"  {name:28s} {param_str}")
        else:
            lines.append(f"  {name}")
        # Wrap description to ~70 chars
        desc = entry["description"]
        lines.append(f"      {desc}")
        lines.append("")
    lines.append("Example:")
    lines.append(
        '  gitpr-mcp --tool analyze_blame --tool-args \'{"file_path":"src/main.py","start_line":"10","end_line":"20"}\''
    )
    lines.append("")
    _write_real_stdout("\n".join(lines))


def _run_tool(tool_name: str, tool_args_json: str = "") -> int:
    """Invoke a single MCP tool and print its JSON result to real stdout.

    Parameters:
        tool_name: Name of the tool (must be in ``_get_tool_registry()``).
        tool_args_json: JSON object string with tool parameters (may be empty).

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    # --- Help mode: bare --tool (no name) ---
    if not tool_name:
        _print_tool_help()
        return 0

    # --- Look up the tool ---
    registry = _get_tool_registry()
    if tool_name not in registry:
        _write_real_stdout(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Unknown tool: '{tool_name}'.",
                    "available_tools": sorted(registry.keys()),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        _print_tool_help()
        return 1

    entry = registry[tool_name]

    # --- Parse --tool-args ---
    tool_args = {}
    if tool_args_json and tool_args_json.strip():
        try:
            tool_args = json.loads(tool_args_json)
        except json.JSONDecodeError as e:
            _write_real_stdout(
                json.dumps(
                    {
                        "status": "error",
                        "message": f"Invalid --tool-args JSON: {e}",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            return 1
        if not isinstance(tool_args, dict):
            _write_real_stdout(
                json.dumps(
                    {
                        "status": "error",
                        "message": "--tool-args must be a JSON object.",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            return 1

    # --- Validate required parameters ---
    params_meta = entry["parameters"]
    missing = [
        p
        for p, meta in params_meta.items()
        if meta.get("required") and p not in tool_args
    ]
    if missing:
        msg = f"Missing required argument(s): {', '.join(missing)}. "
        msg += f"Pass them via --tool-args, e.g. "
        msg += f'--tool {tool_name} --tool-args \'{{"{missing[0]}": "..."}}\'.'
        _write_real_stdout(
            json.dumps(
                {
                    "status": "error",
                    "message": msg,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        return 1

    # --- Execute: mirror server mode (patch output → load .env → safe call) ---
    _patch_output()
    _init_config()
    try:
        result = _safe_call(entry["func"], **tool_args)
    finally:
        _unpatch_output()

    if result is None:
        _write_real_stdout(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Tool '{tool_name}' failed. See stderr for details.",
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        return 1

    _write_real_stdout(_prettify_result(str(result)) + "\n")
    return 0


# =============================================================================
# MCP Config Installer (gitpr-mcp --install <editor>)
# =============================================================================

# Config templates for each supported editor.
# Each template includes a "description" field so that editors, IDEs,
# and AI agents can understand what the server does without connecting.
_GITPR_MCP_DESCRIPTION = (
    "GitPR MCP Server — AI-powered PR automation: generate commit messages, "
    "review code, run linters, trace code origins with git blame, create "
    "structured issues, and generate PR descriptions. "
    "Run 'gitpr-mcp --list' for the complete tools catalog."
)

_CONFIG_TEMPLATES = {
    "vscode": {
        "dir": ".vscode",
        "file": "mcp.json",
        "key": "servers",
        "entry": {
            "gitpr": {
                "type": "stdio",
                "command": "gitpr-mcp",
                "args": [],
                "description": _GITPR_MCP_DESCRIPTION,
            }
        },
    },
    "cursor": {
        "dir": ".cursor",
        "file": "mcp.json",
        "key": "mcpServers",
        "entry": {
            "gitpr": {
                "type": "stdio",
                "command": "gitpr-mcp",
                "args": [],
                "description": _GITPR_MCP_DESCRIPTION,
            }
        },
    },
    "claude-code": {
        "dir": ".",
        "file": ".mcp.json",
        "key": "mcpServers",
        "entry": {
            "gitpr": {
                "command": "gitpr-mcp",
                "args": [],
                "description": _GITPR_MCP_DESCRIPTION,
            }
        },
    },
    "claude": {
        # OS-specific path resolved at runtime
        "dir": None,
        "file": "claude_desktop_config.json",
        "key": "mcpServers",
        "entry": {
            "gitpr": {
                "command": "gitpr-mcp",
                "args": [],
                "description": _GITPR_MCP_DESCRIPTION,
            }
        },
    },
    "zed": {
        # OS-specific path resolved at runtime
        "dir": None,
        "file": "settings.json",
        "key": "context_servers",
        "entry": {
            "gitpr": {
                "command": {
                    "path": "gitpr-mcp",
                    "args": [],
                    "description": _GITPR_MCP_DESCRIPTION,
                }
            }
        },
    },
}


def _get_claude_config_dir():
    """Return the Claude Desktop config directory for the current OS."""
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / "Claude"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude"
    else:
        return Path.home() / ".config" / "Claude"


def _get_zed_config_dir():
    """Return the Zed config directory for the current OS."""
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", "")) / "Zed"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Zed"
    else:
        return Path.home() / ".config" / "zed"


def _resolve_editor_config(editor: str) -> dict:
    """Resolve the config template for an editor, filling OS-specific paths."""
    template = _CONFIG_TEMPLATES.get(editor)
    if template is None:
        return None

    result = dict(template)  # shallow copy
    if editor == "claude":
        result["dir"] = str(_get_claude_config_dir())
    elif editor == "zed":
        result["dir"] = str(_get_zed_config_dir())
    return result


def _merge_json_file(filepath: Path, key: str, entry: dict) -> dict:
    """Read existing JSON, merge the entry under key, return the merged object."""
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = {}
    else:
        existing = {}

    if not isinstance(existing, dict):
        existing = {}

    # Merge: preserve existing entries, add/update gitpr
    section = existing.get(key, {})
    if not isinstance(section, dict):
        section = {}
    section.update(entry)
    existing[key] = section
    return existing


def _install_for_editor(editor: str, project_root: Path) -> tuple[bool, str]:
    """Install MCP config for a single editor.

    Enriches the config entry with a compact ``_tools`` array so that
    editors, IDEs, and AI agents can discover available tools just by
    reading the config file — no need to connect to the MCP server or
    run ``gitpr-mcp --list``.

    Args:
        editor: One of vscode, cursor, claude, zed, claude-code.
        project_root: Project root directory (used for vscode/cursor/claude-code;
                      ignored for claude/zed which use global paths).

    Returns:
        (success: bool, message: str)
    """
    config = _resolve_editor_config(editor)
    if config is None:
        return (
            False,
            f"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude, zed, auto",
        )

    config_dir = Path(config["dir"])
    if not config_dir.is_absolute():
        # Project-local editor (vscode, cursor, claude-code): resolve relative to project root
        config_dir = project_root / config_dir
    config_file = config_dir / config["file"]

    # Ensure directory exists
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, f"Failed to create directory '{config_dir}': {e}"

    # --- Enrich the entry with dynamic tool metadata ---
    entry = dict(config["entry"])  # shallow copy to avoid mutating the template
    gitpr_entry = dict(entry["gitpr"])
    gitpr_entry["_tools"] = _get_compact_tools()

    # Zed nests the config under a "command" key — enrich inside it
    if editor == "zed" and "command" in gitpr_entry:
        gitpr_entry["command"]["_tools"] = _get_compact_tools()

    entry["gitpr"] = gitpr_entry

    # Merge with existing config
    merged = _merge_json_file(config_file, config["key"], entry)

    # Write
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        return True, str(config_file)
    except OSError as e:
        return False, f"Failed to write '{config_file}': {e}"


def _detect_editors(project_root: Path) -> list[str]:
    """Auto-detect which editors have existing config directories.

    Checks for project-local (.vscode, .cursor) and global (Claude, Zed).
    """
    found = []

    # Project-local editors
    if (project_root / ".vscode").exists():
        found.append("vscode")
    if (project_root / ".cursor").exists():
        found.append("cursor")
    if (project_root / ".mcp.json").exists():
        found.append("claude-code")

    # Global editors
    if _get_claude_config_dir().exists():
        found.append("claude")
    if _get_zed_config_dir().exists():
        found.append("zed")

    return found


def _run_install(editor: str) -> None:
    """Handle the --install command: install MCP config for the given editor.

    Prints results to stdout (no patching — this runs before the server starts).
    """
    project_root = Path.cwd()

    if editor == "auto":
        editors = _detect_editors(project_root)
        if not editors:
            # No editors detected — install for vscode and cursor by default
            # (they are project-local and most commonly used)
            editors = ["vscode", "cursor"]
            print(f"No editor config directories detected.")
            print(f"Installing for: {', '.join(editors)}")
        else:
            print(f"Detected editors: {', '.join(editors)}")
    else:
        editors = [editor]

    success_count = 0
    for ed in editors:
        ok, msg = _install_for_editor(ed, project_root)
        if ok:
            print(f"  [OK] {ed}: {msg}")
            success_count += 1
        else:
            print(f"  [FAIL] {ed}: {msg}")

    print(f"\nInstalled for {success_count}/{len(editors)} editor(s).")

    if success_count > 0:
        print("Restart your editor for the changes to take effect.")


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Entry point for gitpr-mcp and gitpr --mcp.

    When called with --list, prints the complete tools catalog as JSON.
    When called with --install, sets up MCP config files for the chosen editor.
    When called with --tool, invokes a single MCP tool directly (CLI mode).
    Otherwise, starts the MCP server on stdio transport.
    """
    # --- Parse CLI args before starting the server ---
    parser = argparse.ArgumentParser(
        prog="gitpr-mcp",
        description="GitPR MCP Server — integrate GitPR with AI-powered editors.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--list",
        action="store_true",
        help="Print the complete tools catalog as JSON (tools, resources, and prompts). "
        "Use this to discover available capabilities without starting the server.",
    )
    mode_group.add_argument(
        "--install",
        nargs="?",
        const="auto",
        choices=["vscode", "cursor", "claude-code", "claude", "zed", "auto"],
        help="Install MCP configuration for an editor (vscode, cursor, claude-code, claude, zed, or auto-detect).",
    )
    mode_group.add_argument(
        "--tool",
        nargs="?",
        const="",
        default=None,
        metavar="NAME",
        help="Invoke a single MCP tool directly and print its JSON result to stdout. "
        "Use --tool-args to pass parameters as a JSON object. "
        "Use '--tool' alone (no NAME) to list available tools.",
    )
    parser.add_argument(
        "--tool-args",
        type=str,
        default="",
        metavar="JSON",
        help="JSON object with tool parameters, e.g. "
        '\'{"file_path": "src/main.py", "start_line": "10", "end_line": "20"}\'. '
        "Only meaningful with --tool.",
    )
    args, _ = parser.parse_known_args()

    # --- List mode: print tools catalog and exit ---
    if args.list:
        _run_list()
        return

    # --- Install mode: set up config and exit ---
    if args.install:
        _run_install(args.install)
        return

    # --- Tool mode: invoke a single tool directly (CLI) ---
    if args.tool is not None:
        sys.exit(_run_tool(args.tool, args.tool_args))

    # --- Server mode: patch output and start MCP transport ---
    try:
        _patch_output()
        _init_config()
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        _unpatch_output()


if __name__ == "__main__":
    main()
