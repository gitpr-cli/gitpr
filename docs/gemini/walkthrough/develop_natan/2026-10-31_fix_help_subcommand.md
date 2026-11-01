# Walkthrough - Subcommand Help Dispatch Fix (`gitpr -h <subcommand>`)

## Problem Solved
Running `gitpr -h <subcommand>` (e.g. `gitpr -h config` or `gitpr --help release`) was ignoring the `-h` flag and executing the subcommand directly (such as opening the interactive TUI configuration app) instead of showing the subcommand's help.

## Root Cause
In `src/main.py`, Click parsed `-h` on the root `@click.group` setting `help_flag = True`, and recognized the subcommand setting `ctx.invoked_subcommand = "<name>"`. In the root callback `cli()`, an early return `if ctx.invoked_subcommand is not None: return` was reached before the contextual `help_flag` handler, prematurely delegating execution to the subcommand without the help request.

## Changes Made
1. **Helper `_resolve_subcommand_tokens(ctx)` in [`src/main.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/main.py)**:
   - Recovers trailing tokens from `Group.invoke` caller frame or `sys.argv` so nested subcommands (e.g. `gitpr -h metrics export`) can be determined.
2. **Subcommand Help Interception in [`src/main.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/main.py)**:
   - When `ctx.invoked_subcommand` is not None and `help_flag` is True:
     - Resolves the command via `cli.get_command(ctx, ctx.invoked_subcommand)`.
     - Creates the context using `cmd.make_context(ctx.invoked_subcommand, [], parent=ctx)` (preserving `context_settings` and `help_option_names`).
     - Traverses nested subcommands if present (e.g. `metrics export`).
     - Prints the resolved command's help text via `curr_cmd.get_help(curr_ctx)` and cleanly exits with `ctx.exit(0)`.
3. **Automated Test Suite in [`tests/test_cli_help.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/test_cli_help.py)**:
   - Tests `gitpr -h config` (shows help and prevents TUI launch).
   - Tests `gitpr --help config`.
   - Tests `gitpr config -h`.
   - Tests `gitpr -h release`.
   - Tests `gitpr -h metrics export`.
   - Tests `gitpr -h metrics`.
   - Tests `gitpr -h` alone.
   - Tests `gitpr -h -c` contextual help.

## Verification Results
- `python -m pytest tests/test_cli_help.py -v`: 8/8 tests passed.
- Full unit test suite (`240 tests`): 100% passed in 14.96s with zero regressions.
