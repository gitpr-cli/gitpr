Design an implementation plan for adding contextual help to a Python Click CLI. 

## Current State
- Single `@click.command()` in `src/main.py` (no groups, no custom classes)
- Help is handled by `@click.help_option('-h', '--help')` — Click intercepts it before the function body runs
- 14 CLI options total (2 hidden)
- The `cli()` function body routes to different actions via if/elif chains
- Some flags short-circuit (linter, update, skill, installhooks)
- Some flags interact (issue+history, issue+blame, input+review)

## Requirements
1. `gitpr -h` alone → shows standard help with ALL options (current behavior)
2. `gitpr -h --issue` → shows help specific to `--issue` + link to `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/issue-tui-help.md`
3. `gitpr -h --linter` → shows help specific to `--linter` + link to `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/linter-regras-customizadas.md`
4. `gitpr -h --installhooks` → shows help specific to `--installhooks` + link to `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/git-hooks-locais.md`
5. Same pattern for all other non-hidden options: `--commit`, `--review`, `--fullreview`, `--blame`, `--skill`, `--update`, `--input`, `--provider`, and the default PR mode

## Docs that already exist
- `docs/issue-tui-help.md` (covers --issue, recently improved with 3 context engines)
- `docs/linter-regras-customizadas.md` (covers --linter, static analysis rules)
- `docs/git-hooks-locais.md` (covers --installhooks, local git hooks)

## Docs that need to be created
For each remaining non-hidden option, a new markdown doc needs to be created. Group them logically:
- `--commit` (`-c`): commit message generation
- `--review` (`-r`) / `--fullreview` (`-f`) / `--input` (`-i`): code review (they work together — `--input` requires review)
- `--blame` (`-b`): archaeological code analysis
- `--skill` (`-s`): template/skill download
- `--update` (`-u`): auto-updater
- default (no flags): PR description generation
- `--provider` (`-p`): AI provider selection (very small feature, could be part of PR doc)

## Technical challenge
Click's `@click.help_option` intercepts `-h` before the CLI function body runs, so the current mechanism can't detect which other flags are combined with `-h`. 

## Proposed approach
1. Remove `@click.help_option('-h', '--help')` from line 38
2. Add `-h`/`--help` as a regular `is_flag=True` boolean option
3. In the `cli()` function body, add help handling as the FIRST check (before banner suppression)
4. Help logic:
   - If `help` is True and NO other non-help flags are set → print standard Click help and exit
   - If `help` is True and another flag IS set → print contextual help for that feature + GitHub docs link and exit
   - If multiple flags are set with help, prioritize the most specific one
5. For printing standard help, use `click.Context` programmatically to invoke the default help formatter

## Additional consideration
The `--provider` flag is a modifier, not a standalone feature. It could share a doc with the PR default mode or get a very small doc.

Please provide a detailed implementation plan including:
- Exact code changes to `src/main.py`
- List of new doc files to create with their content outline
- The mapping dictionary structure (flag → doc URL)
- How to handle edge cases (multiple flags with -h, no flags with -h, etc.)
- How to invoke Click's standard help programmatically when only -h is used
