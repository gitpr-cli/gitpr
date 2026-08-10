import os
from datetime import datetime
import click
import sys

# Reconfigure stdout to utf-8 to prevent UnicodeEncodeError with emojis on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Internal module imports
from src.config import setup_environment, check_internet_connection, get_ai_provider
from src.updater import check_and_update, __version__, print_update_notice
from src.core import (
    get_git_diff,
    get_git_full_diff,
    get_current_branch,
    generate_pr_content,
    generate_skill_template,
    install_git_hooks,
    get_branch_history_text,
    get_doc_url,
    run_install_wizard,
    check_and_update_hooks_scripts,
    resolve_output_path,
)
from src.linter_engine import parse_diff_and_lint
from src.i18n import __
import subprocess
from src.chat_memory import ChatMemoryManager
from src.ui.chat_app import ChatApp

def print_banner():
    """Displays the project ASCII Art signature"""
    banner = r"""
 ,----.   ,--.  ,--.  ,------. ,------.
'  .-./   `--',-'  '-.|  .--. '|  .--. '
|  | .---.,--.'-.  .-'|  '--' ||  '--'.'
'  '--'  ||  |  |  |  |  | --' |  |\  \
 `------' `--'  `--'  `--'     `--' '--'

"""
    click.secho(banner, fg="cyan", bold=True)
    click.secho(__("  🚀 Intelligent PR Automation with AI (v{version})", version=__version__), fg="yellow", bold=True)
    click.secho(__("  Options: -c,--commit | -r,--review | -f,--fullreview | -l,--linter | -s,--skill | -u,--update | -ih,--installhooks | --install | -is,--issue | --no-publish | --no-edit | --plugins | -h,--help (use -h --flag for contextual help)\n"), fg="white", dim=True)


# ============================================================
# Contextual help mapping (flag -> doc URL and description)
# ============================================================
HELP_MAP: dict[str, dict[str, str]] = {
    'commit': {
        'url': get_doc_url('commit-message-ia.md'),
        'title': __('AI Commit Message Generation'),
        'description': __('Generates commit messages in the Conventional Commits format automatically using AI. Supports integration with Git Hooks (prepare-commit-msg) for direct injection into the editor.'),
    },
    'review': {
        'url': get_doc_url('code-review-ia.md'),
        'title': __('AI Code Review (Local Changes)'),
        'description': __('Performs smart code review of uncommitted local changes (git diff HEAD). Automatically integrates the Static Linter (.gitpr.linter.yml) at the top of the report.'),
    },
    'fullreview': {
        'url': get_doc_url('code-review-ia.md'),
        'title': __('Full AI Code Review (Full Diff)'),
        'description': __('Performs a deep review comparing the current branch with the remote main branch (origin/main). Runs git fetch before analysis. Ideal for reviewing before opening a Pull Request.'),
    },
    'input': {
        'url': get_doc_url('code-review-ia.md'),
        'title': __('Specific File Analysis (--input)'),
        'description': __('Analyzes an entire file from the local system, ignoring the Git diff. REQUIRES --review (-r) or --fullreview (-f) to work. Excellent for auditing legacy code and refactoring.'),
    },
    'linter': {
        'url': get_doc_url('linter-regras-customizadas.md'),
        'title': __('Customizable Static Linter'),
        'description': __('Local static analysis engine that checks rules defined in the .gitpr.linter.yml file. Does not consume AI quotas or require internet. Ideal for CI/CD and pre-commit hooks.'),
    },
    'skill': {
        'url': get_doc_url('skill-template.md'),
        'title': __('Skills and Templates System (--skill)'),
        'description': __('Downloads template files (.gitpr.*.md and .gitpr.linter.yml) from the official repository into the project\'s .gitpr/skill/ folder. These files allow customizing the AI behavior according to your team\'s rules. NEVER overwrites existing local files.'),
    },
    'update': {
        'url': get_doc_url('auto-update.md'),
        'title': __('GitPR Auto-Update'),
        'description': __('Checks and automatically installs the latest version of GitPR. Supports update via pip (PyPI) and standalone binary (GitHub Releases) with hot-swap and automatic rollback in case of failure.'),
    },
    'installhooks': {
        'url': get_doc_url('git-hooks-locais.md'),
        'title': __('Install Local Git Hooks'),
        'description': __('Installs pre-commit (automatic static linter) and prepare-commit-msg (AI message generation) hooks in the local repository. Adopts the Shift Left practice for pre-push validation.'),
    },
    'install': {
        'url': get_doc_url('install-wizard.md'),
        'title': __('Interactive Setup Wizard (--install)'),
        'description': __('Guided setup that downloads skill templates, installs Git hooks, configures MCP for your editors, and verifies your AI provider API key.'),
    },
    'blame': {
        'url': get_doc_url('blame-arqueologo.md'),
        'title': __('Code Archeologist (AI Git Blame)'),
        'description': __('Tracks the origin and evolution of business rules in the code using git blame with AI classification (ORIGIN vs REFACTORING). Supports direct mode (file:10-20) and interactive mode. Can feed technical debt Issues context with --issue.'),
    },
    'issue': {
        'url': get_doc_url('issue-tui-help.md'),
        'title': __('Issue Generation with Interactive TUI'),
        'description': __('Generates standardized issues (What / Why / Where / How) using AI and opens an interactive terminal interface (Textual) for review. Has 3 context engines: current diff, branch history (--history), and code archeology (--blame). Allows saving local .md or publishing directly to GitHub via API.'),
    },
    'history': {
        'url': get_doc_url('issue-tui-help.md'),
        'title': __('History Context for Issues (--history)'),
        'description': __('Modifier for --issue (-is): uses the entire history of the current branch (git log + previous PRs cache) as context to generate the issue. Ideal for documenting epics, releases, and large features with multiple commits over days.'),
    },
    'provider': {
        'url': get_doc_url('providers-ia.md'),
        'title': __('AI Provider Selection (--provider)'),
        'description': __('Forces the use of a specific AI provider for this execution: gemini (Google Gemini), deepseek (DeepSeek) or ollama (Local). Temporarily overrides the default provider defined in the .env file.'),
    },
    'chat': {
        'url': get_doc_url('chat-interativo.md'),
        'title': __('Interactive Pair Programming Chat (--chat)'),
        'description': __('Opens an interactive terminal (TUI) to chat with the AI about the current uncommitted changes. Features memory, auto-patching (F5), and live diff refresh (F2).'),
    },
    'lang': {
        'url': get_doc_url('providers-ia.md'),
        'title': __('Language Override (--lang)'),
        'description': __('Forces the interface language for this execution (e.g.: en_us, pt_br). Overrides the GITPR_LANG environment variable and OS locale detection.'),
    },
    'metrics': {
        'url': get_doc_url('metricas_analytics_dashboard.md'),
        'title': __('Metrics & Analytics (--metrics)'),
        'description': __('Export or purge local telemetry data for team analytics.'),
    },
    'no-publish': {
        'url': get_doc_url('pull-request-publication.md'),
        'title': __('Skip Interactive Publisher (--no-publish)'),
        'description': __('Generates the PR description and saves it locally without opening the interactive TUI.'),
    },
    'no-edit': {
        'url': get_doc_url('pull-request-publication.md'),
        'title': __('Direct Publish with Auto-Commit (--no-edit)'),
        'description': __('Generates the PR, auto-commits pending changes (with lint validation), and publishes directly to GitHub without opening the TUI.'),
    },
    'plugins': {
        'url': get_doc_url('plugins-system.md'),
        'title': __('Plugin System (--plugins)'),
        'description': __('Lists all globally installed custom linter packs and MCP prompts loaded from ~/.gitpr/plugins/.'),
    },
    'status': {
        'url': get_doc_url('git-status.md'),
        'title': __('Uncommitted File Status (--status)'),
        'description': __('Lists uncommitted file changes categorized as new (untracked), modified (unstaged edits) and deleted — fast, no AI, no network.'),
    },
    'no-unstaged-check': {
        'url': get_doc_url('git-status.md'),
        'title': __('Skip Unstaged Check (--no-unstaged-check)'),
        'description': __('Skips the unstaged-files verification that runs before PR, commit, review, full review and issue generation. Equivalent to GITPR_SKIP_UNSTAGED_CHECK=true for one run.'),
    },
}

# Priority for contextual help when multiple flags are used with -h
# Lower value = higher priority
HELP_PRIORITY: dict[str, int] = {
    'linter': 1,
    'skill': 2,
    'update': 3,
    'installhooks': 4,
    'install': 14,
    'issue': 5,
    'blame': 6,
    'commit': 7,
    'fullreview': 8,
    'review': 9,
    'input': 10,
    'history': 11,
    'provider': 12,
    'lang': 13,
    'metrics': 15,
    'no-publish': 16,
    'no-edit': 17,
    'plugins': 18,
    'status': 19,
    'no-unstaged-check': 20,
}


# Native Click configuration to accept -h in addition to --help
@click.command()
@click.option('-c', '--commit', is_flag=True, help=__("Generates only the commit message and displays it in the console."))
@click.option('-r', '--review', is_flag=True, help=__("Performs a code review of local changes (git diff)."))
@click.option('-f', '--fullreview', is_flag=True, help=__("Performs a code review of all changes since the remote main branch (origin/main)."))
@click.option('-l', '--linter', is_flag=True, help=__("Runs only the local static linter (ideal for CI/CD)."))
@click.option('-s', '--skill', is_flag=True, help=__("Downloads the skill template files into the .gitpr/skill/ folder."))
@click.option('-u', '--update', is_flag=True, help=__("Checks and installs the latest version of GitPR."))
@click.option('-ih', '--installhooks', is_flag=True, help=__("Automatically installs validation Git Hooks in the project."))
@click.option('--install', is_flag=True, help=__("Interactive setup wizard: downloads templates, installs hooks, configures MCP, and checks API key."))
@click.option('--hook', type=click.Path(), hidden=True, help=__("Commit file path (internal hook use)."))
@click.option('-q', '--quiet', is_flag=True, hidden=True, help=__("Hides banner and non-essential logs (internal use)."))
@click.option('--pre-save', is_flag=True, hidden=True, help=__("Saves the full AI payload (system + prompt) to a JSON file before each AI call (debug)."))
@click.option('-i', '--input', type=click.Path(), help=__("Path to a specific file for full analysis."))
@click.option('-b', '--blame', type=str, help=__("Analyzes the origin of a business rule (e.g., file.py:10-20 or just file.py)."))
@click.option('-ht', '--history', is_flag=True, help=__("Uses the entire branch history (Git Log + PR Cache) as context to generate the issue."))
@click.option('-is', '--issue', is_flag=True, help=__("Generates a standardized Issue from current changes and opens the interactive interface."))
@click.option('-ch', '--chat', is_flag=True, help=__("Opens the interactive Pair Programming chat with AI."))
@click.option('-p', '--provider', type=click.Choice(['gemini', 'deepseek', 'ollama']), help=__("Forces the use of a specific AI provider for this execution."))
@click.option('--lang', type=str, help=__("Forces the interface language for this execution (e.g.: en_us, pt_br)."))
@click.option('--mcp', is_flag=True, hidden=True, help=__("Start the MCP server for integration with VS Code, Cursor, Claude Desktop, etc."))
@click.option('--metrics', is_flag=True, help=__("Shows local telemetry summary. Use --export to consolidate, --purge to clean."))
@click.option('--export', is_flag=True, help=__("Exports consolidated metrics to CSV and JSON in the current folder."))
@click.option('--purge', is_flag=True, help=__("Deletes all local metric files (~/.gitpr/metrics/). Requires confirmation."))
@click.option('--hook-event', type=str, hidden=True, help=__("Internal: logs a git hook event name."))
@click.option('--dashboard', 'show_dashboard', is_flag=True, help=__("Opens the interactive metrics dashboard (TUI)."))
@click.option('--base', type=str, help=__("Target base branch for the Pull Request (overrides PR_DEFAULT_BASE)."))
@click.option('--no-publish', is_flag=True, help=__("Saves the PR file locally without opening the interactive publisher."))
@click.option('--no-edit', is_flag=True, help=__("Skips the interactive editor and publishes the Pull Request directly (with auto-commit)."))
@click.option('--plugins', is_flag=True, help=__("Lists all active global plugins (linters and prompts)."))
@click.option('--status', is_flag=True, help=__("Lists uncommitted file changes (new/modified/deleted) without AI processing."))
@click.option('--no-unstaged-check', is_flag=True, help=__("Skips the unstaged files verification before AI processing."))
@click.option('-h', '--help', 'help_flag', is_flag=True, help=__("Shows this message and exits. Use with another flag for contextual help (e.g., -h --issue)."))
def cli(commit, review, fullreview, linter, skill, update, installhooks, install, hook, quiet, pre_save, provider, input, blame, history, issue, chat, help_flag, lang, mcp, metrics, export, purge, hook_event, show_dashboard, base, no_publish, no_edit, plugins, status, no_unstaged_check):
    """
    GitPR CLI - Intelligent PR Automation and AI Code Review.

    DEFAULT BEHAVIOR (No options):
    Fetches, compares with the remote main branch, generates a Markdown (.md) file, and opens an interactive TUI to review, edit, and publish the Pull Request directly to GitHub.
    """

    # ============================================================
    # CONTEXTUAL HELP HANDLER
    # ============================================================
    if help_flag:
        # Identifica quais outras flags estao ativas (excluindo hidden: hook, quiet)
        active_flags: list[str] = []
        for param_name, help_info in HELP_MAP.items():
            value = locals().get(param_name)
            # Trata tanto flags booleanas (True) quanto parametros string (blame, input, provider)
            if value:
                active_flags.append(param_name)

        if not active_flags:
            # gitpr -h puro (sem outras flags): mostra help padrao do Click
            ctx = click.get_current_context()
            click.echo(ctx.get_help())
            ctx.exit()

        # Ordena por prioridade e seleciona a flag mais especifica
        active_flags.sort(key=lambda f: HELP_PRIORITY.get(f, 99))
        primary_flag = active_flags[0]
        help_info = HELP_MAP.get(primary_flag)

        if help_info:
            click.secho(f"\n{'=' * 60}", bold=True)
            click.secho(f"  {help_info['title']}", fg="cyan", bold=True)
            click.secho(f"{'=' * 60}\n", bold=True)
            click.echo(help_info['description'])
            click.echo("")
            click.secho(__(">> Full documentation:"), fg="green")
            click.secho(f"  {help_info['url']}", fg="blue", underline=True)
            click.echo("")

            if len(active_flags) > 1:
                click.secho(
                    __(">> Tip: For help on a single option, use -h with it only."),
                    fg="yellow", dim=True,
                )

            # Display the main GitPR documentation URL as a footer
            click.secho(
                __(">> Repository: https://github.com/natanfiuza/gitpr"),
                fg="bright_black",
            )
            click.echo("")
        else:
            # Fallback: mostra help padrao (nao deveria acontecer)
            ctx = click.get_current_context()
            click.echo(ctx.get_help())

        # Garante saida limpa apos exibir ajuda contextual
        ctx = click.get_current_context()
        ctx.exit()

    # Language override via --lang flag (one-shot, does not persist to .env)
    if lang:
        from src.i18n import set_lang
        from src.spinner import reload_thinking_words
        set_lang(lang)
        reload_thinking_words(lang)

    # Auto-sync Git hooks (version + language gated — silent when up to date).
    # Skipped for internal invocations (--quiet, --hook, --mcp) so hooks
    # never update themselves mid-flight and MCP startup stays fast.
    if not quiet and not hook and not mcp:
        check_and_update_hooks_scripts()

    # MCP Server Mode — start stdio MCP server (handled before any interactive setup)
    if hook_event:
        # Hidden: fire-and-forget git hook event logging
        from src.metrics import log_command_metric
        log_command_metric(command=f"hook:{hook_event}", status="fired", provider="git")
        return

    if metrics and export:
        from src.metrics import export_metrics
        from src.core import get_repo_name
        csv_path, json_path, count = export_metrics(repo_filter=get_repo_name())
        if count > 0:
            click.secho(__("✅ Metrics exported: {count} events.", count=count), fg="green", bold=True)
            if csv_path:
                click.echo(f"  CSV: {csv_path}")
            if json_path:
                click.echo(f"  JSON: {json_path}")
        else:
            click.secho(__("No new metrics to export."), fg="yellow")
        return

    if metrics and purge:
        from src.metrics import purge_metrics
        if click.confirm(__("⚠ This will permanently delete all local metric files. Continue?")):
            removed = purge_metrics()
            click.secho(__("✅ Metrics purged ({count} files removed).", count=removed), fg="green")
        else:
            click.secho(__("Purge cancelled."), fg="yellow")
        return

    if show_dashboard:
        from src.ui.metrics_app import launch_metrics_dashboard
        from src.core import get_repo_name
        launch_metrics_dashboard(repo_filter=get_repo_name())
        return

    if metrics:
        from src.metrics import show_metrics_summary
        summary = show_metrics_summary()
        click.secho(__("\n📊 Local Telemetry Summary"), fg="cyan", bold=True)
        click.echo(f"  {__('Path')}: {summary['path']}")
        click.echo(f"  {__('Files')}: {summary['total_files']}")
        click.echo(f"  {__('Disk usage')}: {summary['disk_usage']}")
        click.echo()
        click.echo(__("Use --metrics --export to consolidate, --metrics --purge to clean."))
        return

    if mcp:
        from src.mcp_server import main as mcp_main
        mcp_main()
        return

    if plugins:
        from src.config import get_linter_plugins, get_prompt_plugins
        linter_plugins = get_linter_plugins()
        prompt_plugins = get_prompt_plugins()

        click.secho(__("\n🧩 GitPR Plugin System"), fg="cyan", bold=True)

        click.secho(__("\n🔍 Linter Packs ({count}):", count=len(linter_plugins)), fg="yellow", bold=True)
        if linter_plugins:
            for p in linter_plugins:
                click.echo(f"  - {os.path.basename(p)}")
        else:
            click.echo(__("  No global linter plugins installed."))

        click.secho(__("\n💬 Custom Prompts ({count}):", count=len(prompt_plugins)), fg="yellow", bold=True)
        if prompt_plugins:
            for p in prompt_plugins:
                click.echo(f"  - {os.path.basename(p)}")
        else:
            click.echo(__("  No global prompt plugins installed."))

        click.secho(f"\n💡 {__('Plugin directory:')} ~/.gitpr/plugins/", dim=True)
        return

    if status:
        from src.core import get_unstaged_categorized
        data = get_unstaged_categorized()
        if not any(data.values()):
            click.secho(__("✅ Working tree clean. No uncommitted changes found."), fg="green")
            return
        click.secho(__("📂 Uncommitted changes (no AI):"), fg="cyan", bold=True)
        _print_unstaged_summary(data, quiet=quiet)
        return

    # Silencia o banner se estiver no modo quiet ou via hook
    if not quiet and not hook:
        print_banner()

    # Detects if the tool is running as a binary (PyInstaller) or via PIP
    is_compiled = getattr(sys, 'frozen', False)

    # Hot-Swap cleanup (Binary mode only)
    if is_compiled:
        old_exe = sys.executable + ".old"
        if os.path.exists(old_exe):
            try:
                os.remove(old_exe)
            except OSError:
                pass

    # Enable AI payload dump for inspection (hidden debug flag)
    if pre_save:
        from src.ai_providers import set_pre_save
        set_pre_save(True)

    if linter:
        diff_text = get_git_diff()
        
        if not diff_text or not diff_text.strip():
            if not quiet: click.secho(__("✅ Nothing to validate (empty diff)."), fg="green")
            return

        linter_results = parse_diff_and_lint(diff_text)
        
        has_warnings = len(linter_results["warnings"]) > 0
        has_errors = len(linter_results["errors"]) > 0

        # Warning processing (best-practice advisories only)
        if has_warnings:
            # Warnings MUST always appear, even in quiet mode
            click.secho(__("\n⚠️ The Linter generated {count} best practice warning(s):", count=len(linter_results['warnings'])), fg="yellow", bold=True)
            for alert in linter_results["warnings"]:
                click.echo(f"  - {alert}")

        # Error Processing (Critical, Block the Commit)
        if has_errors:
            # Errors MUST always appear, even in quiet mode
            click.secho(__("\n🚨 Validation failed! Found {count} critical error(s):", count=len(linter_results['errors'])), fg="red", bold=True)
            for alert in linter_results["errors"]:
                click.echo(f"  - {alert}")
            # Locks Git only if there are critical errors
            sys.exit(1)

        # Silent success (No critical errors found)
        if not quiet: 
            if has_warnings:
                click.secho(__("\n✅ Code approved with warnings. The commit will proceed."), fg="green")
            else:
                click.secho(__("\n✅ Clean code! No violations found by the local Linter."), fg="green", bold=True)

        # Fire-and-forget linter metric
        from src.metrics import log_command_metric
        log_command_metric(
            command="linter",
            status="error" if has_errors else "success",
            linter_errors=len(linter_results.get("errors", [])),
            linter_warnings=len(linter_results.get("warnings", [])),
        )
        return

    # Connection Guardian (Failing Fast)
    check_internet_connection()

    # Update Module (Pip-Aware)
    if update:
        click.secho(__("🔍 Checking for updates..."), fg="cyan")
        check_and_update()
        from src.metrics import log_command_metric
        log_command_metric(command="update", status="success", provider="git")
        return

    # --install option: Interactive setup wizard
    if install:
        run_install_wizard()
        from src.metrics import log_command_metric
        log_command_metric(command="install", status="success", provider="git")
        return

    # --skill option: Generate template and exit
    if skill:
        generate_skill_template()
        from src.metrics import log_command_metric
        log_command_metric(command="skill", status="success", provider="git")
        return
    
    if installhooks:
        hooks_ok = install_git_hooks()
        if hooks_ok:
            click.secho("\n" + __("✅ Git Hooks successfully installed!"), fg="green", bold=True)
            click.echo(__("The Linter will now run automatically before each commit."))

            click.echo("\n---")
            click.echo(__(">> Usage Guides:"))

            # General Hooks documentation link
            click.echo(__("• How to use Git Hooks:"))
            click.secho(f"  {get_doc_url("git-hooks-locais.md")}", fg="blue")

            # New link: Custom Rules Documentation
            click.echo(__("• How to create new Linter rules (.gitpr.linter.yml):"))
            click.secho(f"  {get_doc_url("linter-regras-customizadas.md")}", fg="blue")
            click.echo("---\n")
        from src.metrics import log_command_metric
        log_command_metric(command="installhooks", status="success" if hooks_ok else "error", provider="git")
        return

    # Archaeologist Module (--blame)
    if blame and not issue:
        # Parser to separate file from lines
        if ":" in blame:
            # Direct Mode: gitpr --blame file:10-20
            file_path, lines = blame.split(":", 1)
            try:
                if "-" in lines:
                    start_line, end_line = lines.split("-")
                else:
                    start_line = end_line = lines
            except ValueError:
                click.secho(__("❌ Invalid line format. Use start-end (e.g., 10-20)."), fg="red")
                return
        else:
            # Interactive Mode: gitpr --blame file
            file_path = blame
            if not os.path.exists(file_path):
                click.secho(__("❌ The file '{file_path}' was not found.", file_path=file_path), fg="red")
                return

            click.secho(__(">> Selected file: {file_path}", file_path=file_path), fg="cyan", bold=True)
            lines_input = click.prompt(__("Which lines do you want to investigate? (E.g., 10-20 or just 45)"))

            if "-" in lines_input:
                start_line, end_line = lines_input.split("-")
            else:
                start_line = end_line = lines_input

        # Final file validation
        if not os.path.exists(file_path):
            click.secho(__("❌ The file '{file_path}' was not found.", file_path=file_path), fg="red")
            return

        # Trigger the engine
        from src.blame_engine import run_blame_analysis
        run_blame_analysis(file_path.strip(), start_line.strip(), end_line.strip())
        from src.metrics import log_command_metric
        log_command_metric(command="blame", status="success", provider="git")
        return

    # Issue Module (Hybrid)
    if issue:
        from src.issue_engine import generate_issue_content, get_github_repo_info
        from src.tui_issue import validate_or_request_github_token, IssueApp

        setup_environment()

        # ── Unstaged files check (all 3 modes: diff, history, blame) ──
        if not check_unstaged_files("issue", skip_check=no_unstaged_check, quiet=quiet, interactive=False):
            return

        context_text = ""
        context_type = "diff"

        # Intelligent Context Router
        if history:
            context_type = "history"
            context_text = get_branch_history_text()
            # Check if history is empty by comparing against possible EN variations
            _no_commits = [
                __("No exclusive commits"), 
                __("No exclusive commits found"),
                __("No unique commits found."),                
            ]
            _no_prs = [
                __("No previous PR"), 
                __("No previous Pull Request"),
                __("No previous AI-generated PR"),
                __("No AI-generated PR found in cache"),
                
            ]
            _no_commits_found = any(phrase in context_text for phrase in _no_commits)
            _no_prs_found = any(phrase in context_text for phrase in _no_prs)
            if not context_text or (_no_commits_found and _no_prs_found):
                click.secho(__("\n⚠️ No history found for this branch.\n"), fg="yellow")
                return

        elif blame:
            context_type = "blame"
            # Reuse the file/line parser from the blame option
            if ":" in blame:
                file_path, lines = blame.split(":", 1)
                try:
                    start_line, end_line = lines.split("-") if "-" in lines else (lines, lines)
                except ValueError:
                    click.secho(__("❌ Invalid line format. Use start-end (e.g., 10-20)."), fg="red")
                    return
            else:
                file_path = blame
                if not os.path.exists(file_path):
                    click.secho(__("❌ The file '{file_path}' was not found.", file_path=file_path), fg="red")
                    return
                click.secho(__(">> Selected file: {file_path}", file_path=file_path), fg="cyan", bold=True)
                lines_input = click.prompt(__("Which lines do you want to investigate? (E.g.: 10-20)"))
                start_line, end_line = lines_input.split("-") if "-" in lines_input else (lines_input, lines_input)

            if not os.path.exists(file_path.strip()):
                click.secho(__("❌ The file '{file_path}' was not found.", file_path=file_path), fg="red")
                return

            from src.blame_engine import run_blame_analysis
            click.secho(__("🔍 Extracting archaeological timeline in background..."), fg="cyan")

            # Trigger the archaeologist in silent mode
            timeline = run_blame_analysis(file_path.strip(), start_line.strip(), end_line.strip(), return_data=True)

            if not timeline:
                click.secho(__("\n⚠️ No traceable history to feed the issue.\n"), fg="yellow")
                return

            # Translate the dictionary list into AI-readable text
            formatted_timeline = []
            for item in timeline:
                formatted_timeline.append(
                    f"{__('[{date}] Commit {hash} by {author}:', date=item['raw_date'], hash=item['hash'], author=item['info']['author'])}\n"
                    f"{__('Action: {status}', status=item['status'])}\n"
                    f"{__('AI Reason: {reason}', reason=item['motivo'])}\n"
                )
            context_text = "\n".join(formatted_timeline)

        else:
            context_type = "diff"
            context_text = get_git_diff()
            if not context_text or not context_text.strip():
                click.secho(__("\n⚠️ No new code found. Make some changes before generating the issue.\n"), fg="yellow")
                return

        # Generate content with AI using the correct language
        issue_data = generate_issue_content(context_text, context_type=context_type)
        if not issue_data:
            return

        # Get repository information
        repo_info = get_github_repo_info()

        # Validate or request PAT Token
        github_token = validate_or_request_github_token(repo_info)

        if not github_token:
            click.secho(__("❌ Access canceled. GitHub Token is mandatory for this action."), fg="red")
            return

        # Run the Terminal Graphical Interface (with reauth loop for expired tokens)
        while True:
            app = IssueApp(issue_data=issue_data, repo_info=repo_info, github_token=github_token)
            app.run()

            # If token expired during the TUI session, re-prompt and relaunch
            if app.final_action == "reauth":
                click.secho(f"\n{app.final_message}\n", fg="yellow")
                github_token = validate_or_request_github_token(repo_info)
                if not github_token:
                    click.secho(__("❌ Access canceled. GitHub Token is mandatory for this action."), fg="red")
                    return
                # Restart TUI with the same issue data and new token
                continue

            # Display return message after closing the TUI
            if app.final_message:
                cor = "green" if app.final_action in ["saved", "created"] else "red"
                click.secho(f"\n{app.final_message}\n", fg=cor, bold=True)

            break

        return

# Chat Module (Pair Programming TUI)
    if chat:
        from src.issue_engine import get_github_repo_info
        from src.config import get_api_key
        
        setup_environment()
        
        diff_text = get_git_diff()
        if not diff_text or not diff_text.strip():
            click.secho(__("\n⚠️ No new code found. Make some changes before starting the chat.\n"), fg="yellow")
            click.secho(f"📚 {__('Chat documentation:')} {get_doc_url('understanding_chat_functionality.md')}", fg="cyan")
            return
            
        active_provider = provider if provider else get_ai_provider()
        api_key = get_api_key(active_provider)
        
        if not api_key:
            click.secho(__("❌ AI Provider API Key missing or invalid."), fg="red")
            return
        
        repo_info = get_github_repo_info() or "local-repo"
        branch_name = get_current_branch()
        
        try:
            git_user = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
            git_email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True).stdout.strip()
        except Exception:
            git_user, git_email = "Dev", "dev@local"
            
        memory = ChatMemoryManager(repo_info, branch_name, diff_text, git_user, git_email)
        
        system_instruction = __("You are a Senior Software Engineer acting as a Pair Programmer. Analyze the code provided and answer the user's questions clearly, objectively, and technically. Use Markdown to format code blocks. The current git diff is:\n\n{diff}", diff=diff_text)
        
        # Use the primary model configured in .env
        env_model_key = f"{active_provider.upper()}_API_MODEL_PRIMARY"
        api_model = os.getenv(env_model_key)
        if not api_model:
            click.secho(__("❌ Model configuration not found for provider {provider}.", provider=active_provider), fg="red")
            return
        
        app = ChatApp(
            memory_manager=memory,
            provider=active_provider,
            api_key=api_key,
            api_model=api_model,
            system_instruction=system_instruction
        )
        app.run()
        from src.metrics import log_command_metric
        log_command_metric(command="chat", status="success", provider=active_provider)
        click.secho(f"📚 {__('Chat documentation:')} {get_doc_url('understanding_chat_functionality.md')}", fg="cyan")
        return

    # Input Mode validation (with guard to not interfere with contextual -h)
    if input and not help_flag:
        if not os.path.exists(input):
            click.secho(
                __("\n❌ Error: The file '{input}' was not found.", input=input),
                fg="red", bold=True,
            )
            return

        if not (review or fullreview):
            click.secho(__("\n❌ Error: The --input (-i) option can only be used with --review (-r) or --fullreview (-f)."), fg="red", bold=True)
            return

    # Ensure environment and keys are configured
    setup_environment()

    # Determine the AI provider to use (command line option takes priority)
    active_provider = provider if provider else get_ai_provider()

    # Determine the action type and which diff to capture
    action_type = "pr"
    diff_text = ""

    if input:
        # FILE REVIEW MODE: Read the physical file instead of git diff
        action_type = "filereview"
        try:
            with open(input, "r", encoding="utf-8") as f:
                diff_text = f.read()
            click.secho(__("📄 File Mode: Analyzing full content of '{input}'...", input=input), fg="blue")
        except Exception as e:
            click.secho(__("❌ Error reading file: {error}", error=str(e)), fg="red")
            return
    elif commit:
        action_type = "commit"
        if not hook and not check_unstaged_files("commit", skip_check=no_unstaged_check, quiet=quiet, interactive=False):
            return
        diff_text = get_git_diff()
    elif review:
        action_type = "review"
        if not hook and not check_unstaged_files("review", skip_check=no_unstaged_check, quiet=quiet, interactive=False):
            return
        diff_text = get_git_diff()
    elif fullreview:
        action_type = "fullreview"
        if not hook and not check_unstaged_files("fullreview", skip_check=no_unstaged_check, quiet=quiet, interactive=False):
            return
        diff_text = get_git_full_diff()
    else:
        # Default: PR Description using Full Diff against the remote main
        action_type = "pr"
        if not check_unstaged_files("pr", skip_check=no_unstaged_check, quiet=quiet, interactive=True):
            return
        click.secho(__("🚀 Starting pull request generation..."), fg="cyan")
        diff_text = get_git_full_diff()

    # CRITICAL: Warn the user before exiting if there are no changes
    if not diff_text or not diff_text.strip():
        click.secho(__("\n⚠️ No new code found. Make some changes or check your branch before running the command.\n"), fg="yellow")
        return

    # Call AI according to active_provider using the new function signature
    data = generate_pr_content(action_type, action_type, diff_text, active_provider)
    if not data:
        return

    # Output Processing
    branch_name = get_current_branch()
    safe_branch_name = branch_name.replace("/", "-").replace("\\", "-")
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    # Commit only in console
    if action_type == "commit":
        msg = data.get('commit_message', __('Code update'))

        if hook:
            # HOOK MODE: Inject message directly into Git file
            try:
                with open(hook, "r", encoding="utf-8") as f:
                    original_content = f.read()

                # Place suggestion at the top, keeping original Git comments below
                with open(hook, "w", encoding="utf-8") as f:
                    f.write(f"{msg}\n\n{original_content}")

                click.secho(__("✅ Message successfully injected into the editor!"), fg="green")
            except Exception as e:
                click.secho(__("❌ Error injecting into hook: {error}", error=str(e)), fg="red")
        else:
            # CONSOLE MODE: The original existing behavior
            click.secho(__("\n>> Tip: Use without --commit to generate the full PR.\n"), fg="yellow")
            click.secho(__("\n📝 Commit Suggestion:\n"), fg="green", bold=True)
            click.echo(msg)
            click.echo("\n")
        return

    # Code Review and File Review  
    if action_type in ["review", "fullreview", "filereview"]:
        
        if fullreview:
            output_filename = resolve_output_path(
                "OUTPUT_FILE_NAME_FULLREVIEW",
                "{branch}_{datetime}_PR_FULLREVIEW.txt",
                safe_branch_name, current_time,
            )
        elif action_type == "filereview":
            output_filename = resolve_output_path(
                "OUTPUT_FILE_NAME_FILEREVIEW",
                "{branch}_{datetime}_FILE_REVIEW.txt",
                safe_branch_name, current_time,
            )
        else:
            output_filename = resolve_output_path(
                "OUTPUT_FILE_NAME_REVIEW",
                "{branch}_{datetime}_PR_REVIEW.txt",
                safe_branch_name, current_time,
            )
        content = data.get('review', __('No analysis generated.'))
        
        # Run the Linter. If "filereview", enable full-file mode.
        if action_type == "filereview":
            linter_results = parse_diff_and_lint(diff_text, is_full_file=True, file_path=input)
        else:
            linter_results = parse_diff_and_lint(diff_text)
            
        all_alerts = linter_results["errors"] + linter_results["warnings"]
        
        if all_alerts:
            
            click.secho(__("⚠️ Attention! Found {count} alerts in the Linter rules.", count=len(all_alerts)), fg="yellow")
            
            # Build header with linter errors
            linter_header = __("## 🚨 Local Static Analysis Alerts (YAML Rules)\n\n")
            for alert in all_alerts:
                linter_header += f"- {alert}\n"
            linter_header += __("\n---\n\n## 🤖 AI Code Review\n\n")

            # Inject header at the top of AI-generated content
            content = linter_header + content
        else:
            click.secho(__("✅ Local Linter passed with no rule violations!"), fg="green")

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(content)
            click.secho(__("\n✅ Code Review successfully generated: '{output_filename}'", output_filename=output_filename), fg="green", bold=True)
        except Exception as e:
            click.secho(__("\n❌ Error saving review: {error}", error=str(e)), fg="red")
        return

    # Default Pull Request (.md file)
    output_filename = resolve_output_path(
        "OUTPUT_FILE_NAME",
        "{branch}_{datetime}_PR_DESC.md",
        safe_branch_name, current_time,
    )

    markdown_content = (
        __("# 🚀 Pull Request Suggestion\n\n**Recommended Commit Message:**\n")
        + "```text\n"
        + f"{data.get('commit_message', __('Code update'))}\n"
        + "```\n\n---\n\n"
        + data.get('pr_description', __('No detailed description.'))
    )

    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        click.secho(__("\n✅ Success! The file '{output_filename}' was generated in the current folder.", output_filename=output_filename), fg="green", bold=True)
    except Exception as e:
        click.secho("\n" + __("❌ Error saving file: {error}", error=str(e)), fg="red")

    # ── PR Publisher logic ──
    from src.core import get_repo_name, get_base_branch

    repo_info = get_repo_name()
    if not repo_info or repo_info == "unknown/repo":
        click.secho(__("❌ Remote repository not identified to create the pull request via API."), fg="red")
        if not quiet:
            print_update_notice()
        return

    head_branch = branch_name
    target_base = base or os.getenv("PR_DEFAULT_BASE") or get_base_branch()

    pr_data = {
        "commit_message": data.get('commit_message', ''),
        "pr_description": data.get('pr_description', __('No detailed description.')),
    }

    # ── --no-publish: save locally and exit ──
    if no_publish:
        if not quiet:
            print_update_notice()
        return

    # ── --no-edit: auto-commit + direct publish ──
    if no_edit:
        if not _run_auto_commit_cli(active_provider):
            return

        github_token = _get_github_token_for_publish(repo_info)
        if not github_token:
            return

        _publish_pr_directly(pr_data, repo_info, github_token, target_base, output_filename)
        if not quiet:
            print_update_notice()
        return

    # ── Default: Open TUI ──
    from src.tui_issue import validate_or_request_github_token
    from src.ui.pr_publish_app import PrPublishApp

    github_token = validate_or_request_github_token(repo_info)
    if not github_token:
        click.secho(__("❌ Access canceled. GitHub Token is mandatory for this action."), fg="red")
        if not quiet:
            print_update_notice()
        return

    # Interactive TUI with reauth loop
    while True:
        app = PrPublishApp(
            pr_data=pr_data,
            repo_info=repo_info,
            github_token=github_token,
            base_branch=target_base,
            output_filename=output_filename,
        )
        app.run()

        if app.final_action == "reauth":
            click.secho(f"\n{app.final_message}\n", fg="yellow")
            github_token = validate_or_request_github_token(repo_info)
            if not github_token:
                click.secho(__("❌ Access canceled. GitHub Token is mandatory for this action."), fg="red")
                break
            continue

        if app.final_message:
            cor = "green" if app.final_action in ["saved", "created"] else "red"
            click.secho(f"\n{app.final_message}\n", fg=cor, bold=True)

        if app.final_action == "created" and app.final_pr_url:
            if click.confirm(__("🔗 Open the Pull Request in your browser?")):
                import webbrowser
                webbrowser.open(app.final_pr_url)
        click.secho(f"📚 {__('PR publication documentation:')} {get_doc_url('pull-request-publication.md')}", fg="cyan")
        break

    if not quiet:
        print_update_notice()


def _env_flag(name, default="false"):
    """Reads a boolean environment variable (true/1/yes/y)."""
    return os.getenv(name, default).lower() in ("true", "1", "yes", "y")


def _print_unstaged_summary(categorized, quiet=False):
    """Prints the 3-category unstaged summary to the console. No AI, no network."""
    if not any(categorized.values()):
        return
    for label, emoji, fg in (
        ("new", __("➕ New files"), "green"),
        ("modified", __("✏️ Modified files"), "yellow"),
        ("deleted", __("🗑️ Deleted files"), "red"),
    ):
        items = categorized.get(label, [])
        if items:
            click.secho(f"  {emoji} ({len(items)}):", fg=fg, bold=True)
            for f in items:
                click.echo(f"    - {f}")


def check_unstaged_files(action_type, skip_check=False, quiet=False, interactive=True):
    """Unstaged-files verification run before AI commands.

    Returns True to proceed, False to abort (only a TUI cancel aborts).

    - skip_check=True or GITPR_SKIP_UNSTAGED_CHECK=true → no-op, return True.
    - 'pr'/'issue' → interactive TUI/auto-stage flow.
    - 'commit' → warn that the commit will NOT include unstaged files;
      auto-stages when GITPR_AUTO_STAGE=true.
    - 'review'/'fullreview' → informational warn only, never stages.
    """
    if skip_check or _env_flag("GITPR_SKIP_UNSTAGED_CHECK"):
        return True

    from src.core import get_unstaged_files, stage_files, get_unstaged_categorized
    unstaged = get_unstaged_files()
    if not unstaged:
        if not quiet:
            click.secho(__("✅ No unstaged files found. Proceeding..."), fg="green", dim=True)
        return True

    if action_type in ("pr", "issue"):
        # ── Interactive flow (TUI or auto-stage) ──
        click.secho(__("🔍 Checking unversioned files..."), fg="cyan")
        if _env_flag("GITPR_AUTO_STAGE"):
            click.secho(__("📋 Auto-staging {count} file(s)...", count=len(unstaged)), fg="cyan")
            stage_files([f for f, _ in unstaged])
            click.secho(__("✅ Files added to stage."), fg="green")
            return True
        click.secho(__("📋 Opening file selection..."), fg="cyan")
        from src.ui.pr_publish_app import StageFilesApp
        app = StageFilesApp(unstaged_files=unstaged)
        app.run()
        if app.result == "cancel":
            click.secho(__("❌ Operation cancelled by user."), fg="red")
            return False
        if app.result == "stage":
            stage_files(app.selected_files)
            count = len(app.selected_files) if app.selected_files else 0
            click.secho(
                __("✅ {count} file(s) added to stage.", count=count) if count
                else __("⏭️ No files selected. Proceeding..."), fg="green" if count else "yellow")
        else:
            click.secho(__("⏭️ Files ignored. Proceeding..."), fg="yellow")
        return True

    # ── Non-interactive informational path for commit/review/fullreview ──
    categorized = get_unstaged_categorized()
    if action_type == "commit":
        click.secho(
            __("⚠️ {count} file(s) are not staged and will NOT be included in the commit.",
               count=len(unstaged)), fg="yellow", bold=True)
        if _env_flag("GITPR_AUTO_STAGE"):
            click.secho(__("📋 Auto-staging {count} file(s)...", count=len(unstaged)), fg="cyan")
            stage_files([f for f, _ in unstaged])
            click.secho(__("✅ Files added to stage."), fg="green")
            return True
    else:
        click.secho(
            __("ℹ️ {count} file(s) are not staged. They will still be included in this analysis.",
               count=len(unstaged)), fg="yellow")
    _print_unstaged_summary(categorized, quiet=quiet)
    click.secho(
        __("💡 Tip: Use 'git add <file>' to stage them, or pass --no-unstaged-check to skip this verification."),
        fg="cyan", dim=True)
    return True


def _run_auto_commit_cli(provider):
    """Auto-commit flow for --no-edit mode. Returns True if commit succeeded or no changes."""
    from src.core import has_uncommitted_changes, execute_git_commit, get_git_diff
    from src.linter_engine import parse_diff_and_lint

    if not has_uncommitted_changes():
        return True  # nothing to commit, proceed

    skip_lint = os.getenv("GITPR_SKIP_LINT", "false").lower() in ("true", "1", "yes", "y")
    auto_commit = os.getenv("GITPR_AUTO_COMMIT", "false").lower() in ("true", "1", "yes", "y")

    # ── Linter ──
    no_verify = False
    if not skip_lint:
        click.secho("🔍 " + __("Running linter..."), fg="cyan")
        diff_text = get_git_diff()
        linter_results = parse_diff_and_lint(diff_text)
        has_errors = len(linter_results["errors"]) > 0
        has_warnings = len(linter_results["warnings"]) > 0

        if has_warnings:
            click.secho(__("\n⚠️ Linter generated {count} warning(s):", count=len(linter_results['warnings'])), fg="yellow")
            for w in linter_results["warnings"]:
                click.echo(f"  - {w}")

        if has_errors:
            click.secho(__("\n🚨 Linter found {count} error(s):", count=len(linter_results['errors'])), fg="red")
            for e in linter_results["errors"]:
                click.echo(f"  - {e}")
            if click.confirm(__("\n⚠ Commit with --no-verify anyway?"), default=False):
                no_verify = True
            else:
                click.secho(__("❌ Commit aborted by user."), fg="red")
                return False
        else:
            if has_warnings:
                click.secho(__("✅ Linter passed with warnings."), fg="green")
            else:
                click.secho(__("✅ Linter passed — no violations."), fg="green")

    # ── Generate commit message via AI ──
    click.secho("📝 " + __("Generating commit message..."), fg="cyan")
    from src.core import generate_pr_content
    diff_text = get_git_diff()
    commit_data = generate_pr_content("commit", "commit", diff_text, provider)
    commit_msg = commit_data.get("commit_message", __("Code update")) if commit_data else __("Code update")

    click.secho(__("\n📝 Commit Message:\n"), fg="green", bold=True)
    click.echo(commit_msg)
    click.echo("")

    if not auto_commit:
        if not click.confirm(__("Proceed with this commit message?"), default=True):
            click.secho(__("❌ Commit cancelled by user."), fg="red")
            return False

    # ── Execute commit ──
    click.secho("📦 " + __("Executing commit..."), fg="cyan")
    success, output = execute_git_commit(commit_msg, no_verify=no_verify)
    if success:
        click.secho(__("✅ Commit executed successfully!"), fg="green")
        return True
    else:
        click.secho(__("❌ Commit failed: {output}", output=output), fg="red")
        return False


def _get_github_token_for_publish(repo_info):
    """Get or request a GitHub token for PR publication. Returns token or None."""
    from src.tui_issue import validate_or_request_github_token
    token = validate_or_request_github_token(repo_info)
    if not token:
        click.secho(__("❌ Access canceled. GitHub Token is mandatory for this action."), fg="red")
    return token


def _publish_pr_directly(pr_data, repo_info, github_token, target_base, output_filename):
    """Publish PR directly to GitHub without TUI (for --no-edit mode)."""
    from src.github_api import create_pull_request
    from src.core import get_current_branch

    commit_msg = pr_data.get("commit_message", "")
    pr_body = pr_data.get("pr_description", "")

    full_body = (
        __("**Recommended Commit Message:**\n")
        + "```text\n"
        + f"{commit_msg}\n"
        + "```\n\n---\n\n"
        + pr_body
    )

    head_branch = get_current_branch()
    click.secho("🚀 " + __("Publishing Pull Request to GitHub..."), fg="cyan")

    ok, data, status = create_pull_request(
        repo_info, github_token, commit_msg, full_body, head_branch, target_base
    )

    if ok:
        pr_url = data.get("url")
        click.secho(__("✅ PR successfully created on GitHub:\n👉 {pr_url}", pr_url=pr_url), fg="green", bold=True)
        from src.metrics import log_command_metric
        log_command_metric(command="pr:publish", status="success", provider="github")
        if click.confirm(__("🔗 Open the Pull Request in your browser?")):
            import webbrowser
            webbrowser.open(pr_url)
        click.secho(f"📚 {__('PR publication documentation:')} {get_doc_url('pull-request-publication.md')}", fg="cyan")
    elif status == 401:
        click.secho(__("🔐 GitHub token expired or invalid. Use 'gitpr' (without --no-edit) to re-authenticate interactively."), fg="red")
    else:
        click.secho(__("❌ GitHub API Error ({code}): {msg}", code=status, msg=data.get("message", "")), fg="red")


if __name__ == "__main__":
    cli()