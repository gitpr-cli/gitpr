"""
MCP (Model Context Protocol) Server for GitPR.

Exposes GitPR's AI-powered capabilities as MCP tools and resources,
enabling integration with VS Code, Cursor, Claude Desktop, and other
MCP-compatible editors and AI agents.

Usage:
    gitpr-mcp                        # Start the MCP server (stdio transport)
    gitpr-mcp --install vscode       # Install MCP config for VS Code
    gitpr-mcp --install cursor       # Install MCP config for Cursor
    gitpr-mcp --install claude-code  # Install MCP config for Claude Code
    gitpr-mcp --install claude       # Install MCP config for Claude Desktop
    gitpr-mcp --install zed          # Install MCP config for Zed
    gitpr-mcp --install auto         # Auto-detect and install for all found
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

import click
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.i18n import __

# =============================================================================
# Output Patching System
# =============================================================================
# The MCP stdio transport owns stdout.  Any write to stdout that is not a
# JSON-RPC message corrupts the protocol.  GitPR's existing code writes
# banners, spinners, and colored messages to stdout via click and direct
# sys.stdout.write().  The patching below redirects all of that to stderr.
# =============================================================================

_original_stdout = None
_original_stdout_write = None
_original_stdout_flush = None
_original_secho = None
_original_echo = None
_original_exit = None
_original_prompt = None
_original_style = None


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


def _patch_output():
    """Redirect all application-level stdout to stderr; neutralise exit/prompt."""
    global _original_stdout, _original_stdout_write, _original_stdout_flush
    global _original_secho, _original_echo, _original_style
    global _original_exit, _original_prompt

    # --- Save originals ---
    _original_stdout = sys.stdout
    _original_stdout_write = sys.stdout.write
    _original_stdout_flush = sys.stdout.flush
    _original_secho = click.secho
    _original_echo = click.echo
    _original_style = click.style
    _original_exit = sys.exit
    _original_prompt = click.prompt

    # --- Replace sys.stdout ---
    sys.stdout = _MCPStdout()

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
            __("Interactive prompt is unavailable in MCP mode. "
               "Configure your API keys in ~/.gitpr/.env before using MCP tools.")
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
    instructions=__("GitPR — Intelligent PR Automation and AI Code Review. "
                     "Generate commit messages, review code, run linters, "
                     "trace code origins, and create issues — all from your IDE."),
)


# =============================================================================
# Tools — Git Context
# =============================================================================

@mcp.tool(
    description=__("Get the current git branch, repository name, and remote origin URL.")
)
def get_git_context() -> str:
    """Return JSON with branch name and repository info."""
    from src.core import get_current_branch, get_repo_name

    branch = _safe_call(get_current_branch) or "unknown"
    repo = _safe_call(get_repo_name) or "unknown/repo"

    return json.dumps({
        "branch": branch,
        "repository": repo,
    })


# =============================================================================
# Tools — Diff Inspection
# =============================================================================

@mcp.tool(
    description=__("Get the current unstaged git diff (git diff HEAD). ")
                + __("Lists all changed files and their line-level modifications.")
)
def analyze_diff() -> str:
    """Return the raw git diff for uncommitted local changes."""
    from src.core import get_git_diff

    diff = _safe_call(get_git_diff, quiet=True)
    if not diff or not diff.strip():
        return json.dumps({
            "status": "no_changes",
            "message": __("No uncommitted changes detected."),
        }, ensure_ascii=False)
    return json.dumps({
        "status": "changes_found",
        "diff": diff,
    }, ensure_ascii=False)


@mcp.tool(
    description=__("Get the full diff of the current branch against the remote "
                    "base branch (origin/main or origin/master). Runs git fetch first.")
)
def get_full_diff() -> str:
    """Return the full diff between the current branch and origin/main."""
    from src.core import get_git_full_diff

    diff = _safe_call(get_git_full_diff)
    if not diff or not diff.strip():
        return json.dumps({
            "status": "no_changes",
            "message": __("No changes detected against the base branch."),
        }, ensure_ascii=False)
    return json.dumps({
        "status": "changes_found",
        "diff": diff,
    }, ensure_ascii=False)


# =============================================================================
# Tools — AI-Powered Analysis
# =============================================================================

@mcp.tool(
    description=__("Generate a Conventional Commits commit message from the "
                    "current git diff using AI. "
                    "Returns a message like 'feat: add user authentication'.")
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
        return json.dumps({
            "status": "no_changes",
            "message": __("No diff to analyze. Make some changes first."),
        }, ensure_ascii=False)

    active_provider = _resolve_provider(provider)
    result = _safe_call(generate_pr_content, "commit", "commit", diff_text, active_provider)

    if result and "commit_message" in result:
        return json.dumps({
            "status": "success",
            "commit_message": result["commit_message"],
        }, ensure_ascii=False)

    return json.dumps({
        "status": "error",
        "message": __("AI failed to generate a commit message."),
    }, ensure_ascii=False)


@mcp.tool(
    description=__("Perform an AI code review on uncommitted local changes "
                    "(git diff HEAD). Returns structured feedback with issues "
                    "and improvement suggestions.")
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
        return json.dumps({
            "status": "no_changes",
            "message": __("No diff to review."),
        }, ensure_ascii=False)

    active_provider = _resolve_provider(provider)
    result = _safe_call(generate_pr_content, "review", "review", diff_text, active_provider)

    if result and "review" in result:
        return json.dumps({
            "status": "success",
            "review": result["review"],
        }, ensure_ascii=False)

    return json.dumps({
        "status": "error",
        "message": __("AI failed to generate a review."),
    }, ensure_ascii=False)


@mcp.tool(
    description=__("Perform a full AI code review comparing the entire current "
                    "branch against origin/main. Runs git fetch automatically.")
)
def full_review(provider: str = "") -> str:
    """AI code review of all changes since origin/main.

    Args:
        provider: Override AI provider (gemini, deepseek, ollama).
    """
    from src.core import generate_pr_content, get_git_full_diff

    diff_text = _safe_call(get_git_full_diff) or ""
    if not diff_text.strip():
        return json.dumps({
            "status": "no_changes",
            "message": __("No changes against the base branch."),
        }, ensure_ascii=False)

    active_provider = _resolve_provider(provider)
    result = _safe_call(generate_pr_content, "fullreview", "fullreview", diff_text, active_provider)

    if result and "review" in result:
        return json.dumps({
            "status": "success",
            "review": result["review"],
        }, ensure_ascii=False)

    return json.dumps({
        "status": "error",
        "message": __("AI failed to generate a full review."),
    }, ensure_ascii=False)


@mcp.tool(
    description=__("Generate a complete Pull Request description (title + body) "
                    "from the full diff against origin/main. Uses AI to create a "
                    "structured, professional PR document.")
)
def generate_pr_description(provider: str = "") -> str:
    """Generate a full PR description from the branch diff.

    Args:
        provider: Override AI provider (gemini, deepseek, ollama).
    """
    from src.core import generate_pr_content, get_git_full_diff

    diff_text = _safe_call(get_git_full_diff) or ""
    if not diff_text.strip():
        return json.dumps({
            "status": "no_changes",
            "message": __("No changes against the base branch."),
        }, ensure_ascii=False)

    active_provider = _resolve_provider(provider)
    result = _safe_call(generate_pr_content, "pr", "pr", diff_text, active_provider)

    if result:
        return json.dumps({
            "status": "success",
            "commit_message": result.get("commit_message", ""),
            "pr_description": result.get("pr_description", ""),
        }, ensure_ascii=False)

    return json.dumps({
        "status": "error",
        "message": __("AI failed to generate a PR description."),
    }, ensure_ascii=False)


# =============================================================================
# Tools — Linter
# =============================================================================

@mcp.tool(
    description=__("Run the static local linter (regex-based rules from "
                    ".gitpr.linter.yml) on the current git diff. "
                    "Returns error and warning counts with detailed messages.")
)
def run_linter() -> str:
    """Analyze the current diff against .gitpr.linter.yml rules."""
    from src.core import get_git_diff
    from src.linter_engine import parse_diff_and_lint

    diff_text = _safe_call(get_git_diff, quiet=True) or ""
    if not diff_text.strip():
        return json.dumps({
            "status": "no_changes",
            "message": __("Empty diff — nothing to lint."),
        }, ensure_ascii=False)

    results = _safe_call(parse_diff_and_lint, diff_text) or {"errors": [], "warnings": []}

    return json.dumps({
        "status": "success",
        "error_count": len(results.get("errors", [])),
        "warning_count": len(results.get("warnings", [])),
        "errors": results.get("errors", []),
        "warnings": results.get("warnings", []),
        "passed": len(results.get("errors", [])) == 0,
    }, ensure_ascii=False)


# =============================================================================
# Tools — Code Archaeology (Blame)
# =============================================================================

@mcp.tool(
    description=__("Run AI-powered git blame analysis on a file region to trace "
                    "the origin of business rules. Classifies each commit as "
                    "ORIGIN (first introduction) or REFACTORING (later change).")
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
        return json.dumps({
            "status": "error",
            "message": __("File not found: {file_path}", file_path=file_path),
        }, ensure_ascii=False)

    timeline = _safe_call(run_blame_analysis, file_path, start_line, end_line, return_data=True)

    if not timeline:
        return json.dumps({
            "status": "no_data",
            "message": __("No traceable commits found for this region."),
        }, ensure_ascii=False)

    return json.dumps({
        "status": "success",
        "entries": timeline,
    }, ensure_ascii=False, default=str)


# =============================================================================
# Tools — Issue Generation
# =============================================================================

@mcp.tool(
    description=__("Generate a structured Issue (What / Why / Where / How) from "
                    "code context using AI. Supports three modes: diff (current "
                    "changes), history (branch history), or blame (file region).")
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
        return json.dumps({
            "status": "no_changes",
            "message": __("No context available for issue generation."),
        }, ensure_ascii=False)

    result = _safe_call(generate_issue_content, context_text, context_type=context_type)

    if result:
        return json.dumps({
            "status": "success",
            "title": result.get("titulo", ""),
            "body": result.get("corpo", ""),
        }, ensure_ascii=False)

    return json.dumps({
        "status": "error",
        "message": __("AI failed to generate an issue."),
    }, ensure_ascii=False)


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
    return json.dumps({
        "status": "not_found",
        "message": __("Resource '{filename}' not found. Run 'gitpr --skill' to download templates.",
                       filename=filename),
    })


@mcp.resource(
    uri="skill://list",
    name=__("Available Skill Templates"),
    description=__("Lists all available skill template resource URIs."),
    mime_type="application/json",
)
def list_skills() -> str:
    """Return a JSON list of available skill and config resource URIs."""
    return json.dumps({
        "skills": [f"skill://{name}" for name in SKILL_FILES],
        "linter": "linter://config",
    })


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
# Prompts — Message Templates for Common Flows
# =============================================================================
# Prompts are pre-defined message templates that users can select in their
# editor's AI chat. Unlike tools (which execute automatically), prompts are
# starter messages that guide the AI to invoke the right GitPR tools.
# =============================================================================

@mcp.prompt(
    name=__("Review PR"),
    description=__("Full code review of all changes in the current branch against origin/main. "
                    "Runs the full review tool and linter, then composes a comprehensive report."),
)
def review_pr_prompt() -> str:
    """Prompt: full code review of the current branch."""
    return __(
        "Please review all changes in my current branch by running a full code "
        "review against origin/main. Also run the static linter to check for "
        "code quality issues. Combine the results into a single comprehensive "
        "review report with: 1) summary of changes, 2) critical issues found, "
        "3) linter violations, and 4) suggested improvements."
    )


@mcp.prompt(
    name=__("Generate Commit Message"),
    description=__("Generate a Conventional Commits message (e.g., 'feat: add user auth') "
                    "from the current uncommitted changes."),
)
def generate_commit_message_prompt() -> str:
    """Prompt: generate a commit message from uncommitted changes."""
    return __(
        "Please generate a commit message for my current uncommitted changes. "
        "Use the Conventional Commits format (e.g., 'feat:', 'fix:', 'refactor:'). "
        "The message should be short, imperative, and describe what the change does."
    )


@mcp.prompt(
    name=__("Create PR Description"),
    description=__("Generate a complete Pull Request description (title + body) "
                    "from all changes in the current branch."),
)
def create_pr_description_prompt() -> str:
    """Prompt: generate a full PR description."""
    return __(
        "Please create a complete Pull Request description for my current branch. "
        "Generate a clear title and a structured body that includes: 1) what was "
        "changed, 2) why the change was made, 3) any important implementation "
        "details, and 4) testing instructions."
    )


@mcp.prompt(
    name=__("Run Code Linter"),
    description=__("Run the static linter (.gitpr.linter.yml rules) on current "
                    "uncommitted changes and report violations."),
)
def run_linter_prompt() -> str:
    """Prompt: run the static linter on current changes."""
    return __(
        "Please run the static linter on my current uncommitted changes to check "
        "for code quality violations. Report any errors or warnings found, and "
        "suggest how to fix them."
    )


@mcp.prompt(
    name=__("Create Issue from Diff"),
    description=__("Generate a structured issue (What / Why / Where / How) from "
                    "the current uncommitted changes."),
)
def create_issue_prompt() -> str:
    """Prompt: generate an issue from the current diff."""
    return __(
        "Please create a structured issue from my current uncommitted changes. "
        "Use the What / Why / Where / How format to document the task clearly."
    )


@mcp.prompt(
    name=__("Trace Code Origin"),
    description=__("Investigate the history of a specific file region using git "
                    "blame + AI to trace where business rules came from."),
)
def trace_code_origin_prompt() -> str:
    """Prompt: trace the origin of code in a file region."""
    return __(
        "Please help me trace the origin of a specific code region. First, check "
        "the current git context to understand the project structure. Then I'll "
        "provide the file path and line range I want to investigate."
    )


@mcp.prompt(
    name=__("Explore Project Context"),
    description=__("Get current branch info, repository name, and list available "
                    "skill templates for the project."),
)
def explore_project_prompt() -> str:
    """Prompt: explore the current git context and available skills."""
    return __(
        "Please explore my current project context. Tell me what branch I'm on, "
        "what repository I'm working in, and what skill templates and linter "
        "configurations are available."
    )


# =============================================================================
# MCP Config Installer (gitpr-mcp --install <editor>)
# =============================================================================

# Config templates for each supported editor
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

    Args:
        editor: One of vscode, cursor, claude, zed.
        project_root: Project root directory (used for vscode/cursor;
                      ignored for claude/zed which use global paths).

    Returns:
        (success: bool, message: str)
    """
    config = _resolve_editor_config(editor)
    if config is None:
        return False, f"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude, zed, auto"

    config_dir = Path(config["dir"])
    if not config_dir.is_absolute():
        # Project-local editor (vscode, cursor): resolve relative to project root
        config_dir = project_root / config_dir
    config_file = config_dir / config["file"]

    # Ensure directory exists
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, f"Failed to create directory '{config_dir}': {e}"

    # Merge with existing config
    merged = _merge_json_file(config_file, config["key"], config["entry"])

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

    When called with --install, sets up MCP config files for the chosen editor.
    Otherwise, starts the MCP server on stdio transport.
    """
    # --- Parse CLI args before starting the server ---
    parser = argparse.ArgumentParser(
        prog="gitpr-mcp",
        description="GitPR MCP Server — integrate GitPR with AI-powered editors.",
    )
    parser.add_argument(
        "--install",
        nargs="?",
        const="auto",
        choices=["vscode", "cursor", "claude-code", "claude", "zed", "auto"],
        help="Install MCP configuration for an editor (vscode, cursor, claude, zed, or auto-detect).",
    )
    args, _ = parser.parse_known_args()

    # --- Install mode: set up config and exit ---
    if args.install:
        _run_install(args.install)
        return

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
