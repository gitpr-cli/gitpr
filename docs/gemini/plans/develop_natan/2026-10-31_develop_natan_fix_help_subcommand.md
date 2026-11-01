# Implementation Plan - Subcommand Help Dispatch Fix (`gitpr -h <subcommand>`)

## Goal Description
Fix an issue where executing `gitpr -h <subcommand>` (e.g. `gitpr -h config`) ignores the `-h` flag and executes the subcommand (such as opening the TUI) instead of displaying the subcommand's help message.

In `src/main.py`, Click parses options on the root `@click.group` before dispatching to the subcommand. Because `-h` and `--help` are mapped to the custom option `help_flag`, Click marks `help_flag = True` on the root context and sets `ctx.invoked_subcommand = "config"`. However, the root callback `cli()` contains:
```python
if ctx.invoked_subcommand is not None:
    ...
    return
```
Because of the early `return`, control is transferred directly to Click's subcommand runner, invoking the subcommand without help. The root `if help_flag:` handler at line 770 is never reached.

The fix will intercept `if help_flag:` before the subcommand dispatch returns, resolve the target subcommand (and nested subcommands if present), render its native Click help text, and cleanly exit (`ctx.exit(0)`).

## User Review Required
> [!NOTE]
> All design decisions were aligned during grilling:
> - **Q1**: Native Click help format for subcommands (`subcmd.get_help(sub_ctx)`) identical to `gitpr <subcommand> -h`.
> - **Q2**: Universal behavior for all subcommands and groups (`config`, `release`, `metrics`, `check`, `split`, etc.).
> - **Q3**: Resolves nested subcommands when extra tokens are provided (e.g., `gitpr -h metrics export`).
> - **Q4**: Subcommand takes precedence if explicitly passed alongside flags.

## Proposed Changes

### `src/main.py`
#### [MODIFY] `src/main.py`
- In `cli()` function, right before or at `if ctx.invoked_subcommand is not None:`:
  - If `help_flag` is True (or `-h`/`--help` is in argv):
    - Retrieve the command via `cli.get_command(ctx, ctx.invoked_subcommand)`.
    - If command is found:
      - If it is a group/multicommand and `ctx.args` contains a valid nested subcommand, resolve down to the leaf command.
      - Create the proper `click.Context` with parent hierarchy.
      - Output `cmd.get_help(sub_ctx)`.
      - Call `ctx.exit(0)`.
    - If no command is found (invalid subcommand), fallback to default group help and exit.

### `tests/test_cli_help.py`
#### [NEW] `tests/test_cli_help.py`
- Add unit tests using `click.testing.CliRunner`:
  - Test `gitpr -h config` outputs `gitpr config` help, mentions `config-tui.md`, and exits with code 0 without launching the TUI.
  - Test `gitpr --help config` produces identical output.
  - Test `gitpr -h release` displays release help and exits with code 0.
  - Test `gitpr -h metrics export` displays `metrics export` help.
  - Test `gitpr -h` alone still displays root help.
  - Test `gitpr -h -c` still displays contextual help for commit.

## Verification Plan

### Automated Tests
Run unit tests with pytest:
```bash
python -m pytest tests/test_cli_help.py -v
```
Run the full test suite to guarantee zero regression:
```bash
python -m pytest tests/ -v
```

### Manual Verification
- Run `gitpr -h config`: verify that the terminal displays the help for `config` (including options and the doc URL link) and does NOT launch the Textual configuration TUI.
- Run `gitpr config -h`: verify that it displays identical output.
- Run `gitpr -h metrics export`: verify it displays help for `metrics export`.
- Run `gitpr -h`: verify that standard root help is displayed.
