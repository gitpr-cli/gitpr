# Plan — project-local PR target base branch (`.gitpr/conf/gitpr.config.yml`)

Date: 2026-10-30 · Branch: `develop_natan` · Status: implemented

## Context

The PR target branch came from `--base` → `PR_DEFAULT_BASE` (`~/.gitpr/.env`, machine-wide) → `origin/HEAD` →
`main`. `PR_DEFAULT_BASE` cannot be versioned with the repository, so a project that merges into `develop` needs
the flag on every run and a new contributor has no in-checkout signal of the target.

## Settled decisions (grill rounds)

| # | Decision |
|---|---|
| Q1 | The project file controls **only the PR target**. AI diff base stays `origin/HEAD` (known debt) |
| Q8 | Precedence: `--base` > project file > `PR_DEFAULT_BASE` > `origin/HEAD` > `main` |
| Q9 | Seed value: `PR_DEFAULT_BASE` when non-empty, else literal `main` |
| Q2/Q3 | Seeded on every invocation inside a git repo (subcommands included), except help; never overwritten; never `git add` |
| Q4 | Path: `<git rev-parse --show-toplevel>/.gitpr/conf/gitpr.config.yml`, fallback `cwd` |
| Q5 | Nested YAML: `pull_request.base_branch`, with a header comment |
| Q6 | TUI: new **Project** category; only the YAML is edited there; `PR_DEFAULT_BASE` becomes the global fallback |
| Q10 | One-line hint to version the file; warn when the user's `.gitignore` hides it |
| Q7/Q13 | Invalid YAML → warn and continue down the chain; missing target branch → fail fast (any source). TUI warns but saves |
| Q12 | Consumers: default PR flow, `--no-edit`, `PrPublishApp`, MCP `publish_pull_request` — one resolver. `-f`, MCP diff tools and `check/baseline/risk --base` untouched |
| Q14 | ADR-015 + glossary distinguishing *PR target base* from *diff base* |

## Design

### `src/project_config.py` (new)

No `src.core` import at module level (`get_base_branch` is imported inside the function). Constants
(`DEFAULT_BASE_BRANCH = "main"`, `PROJECT_CONFIG_RELATIVE_PATH`, `HEADER_COMMENT`, schema keys, source tokens),
dataclasses `ProjectConfig`, `SeedResult`, `ResolvedBase`, exception `BaseBranchError`.

- `project_config_path(start_dir=None)` — toplevel via git, fallback `cwd`.
- `read_project_config` / `load_project_field_values` — `yaml.safe_load`; missing file → empty; invalid YAML,
  non-mapping or non-string value → `error`, never raises.
- `write_project_field_values(values, removals=(), ...)` — mutates `pull_request.base_branch`, dumps with
  `sort_keys=False, allow_unicode=True`, writes with `newline="\n"`; refuses to overwrite unparseable YAML.
- `ensure_project_config(...)` — never raises, never overwrites, `git check-ignore -q` for `ignored`.
- `resolve_pull_request_base(cli_base=None, verify=True, ...)` — the single precedence chain.
- `verify_remote_base(branch)` — `git rev-parse --verify --quiet refs/remotes/origin/<branch>`, distinct errors
  for missing `origin` and missing branch, with the `git fetch origin <branch>` hint.
- `describe_base_source(source)` — translated source labels.

### Wiring

- `src/main.py`: seed between `ledger.ensure_ledger` and the subcommand returns, guarded by
  `not help_flag and not _subcommand_help_in_argv() and not GITPR_SKIP_PROJECT_CONFIG_SEED`. Announcement only on
  the interactive root path (never subcommands, `--quiet`, `--hook`, `--mcp`). Target resolved after
  `if no_publish: return`; `BaseBranchError` → red stderr + `Exit(1)`.
- `src/mcp_server.py`: `publish_pull_request` uses the resolver; `BaseBranchError` → JSON error, no create call.
- `src/core.py`: `run_install_wizard()` seeds and reports path / existing / gitignore warning.
- `src/config_schema.py` + `src/ui/config_app.py`: `STORE_ENV`/`STORE_PROJECT`, **Project** category with
  `PROJECT_CONFIG_FILE` (read-only path), `PROJECT_BASE_BRANCH` (editable), `PROJECT_EFFECTIVE_BASE` (read-only,
  value + source). `_build_plan` splits by store; project YAML written before the `.env`; post-save warns (does not
  block) when the branch is missing on `origin`; effective row refreshed after save.

## Tests

- `tests/conftest.py`: `GITPR_SKIP_PROJECT_CONFIG_SEED=true`.
- `tests/test_project_config.py` (29), `tests/test_project_config_cli.py` (6), `TestProjectSection` in
  `tests/test_config_app.py` (5) and in `tests/test_config_schema.py` (4), MCP publish tests updated + 2 new.
- `test_config_app.py` `setUp` patches `project_config_path` and `ensure_project_config` to a temp dir.

## Docs

`docs/config-tui.md`, `docs/pull-request-publication.md`, `docs/pr-descricao-padrao.md`, `docs/install-wizard.md`
each + pt_br/pt_pt/es_es/fr_fr; `docs/plans/ADR-015-project-local-pr-base.md`;
`docs/plans/glossary-config-tui.md`; `CLAUDE.md`; i18n keys in the six `langs/*.json`.

## Risks

1. **pytest contamination** — seed would run in the real checkout for ~49 `CliRunner` tests; mitigated by the env
   escape hatch plus the `ConfigAppTestCase` patches.
2. **Repo whose default is `master`** — the literal `main` seed wins over `origin/HEAD` until edited; accepted
   (Q9), mitigated by the fail-fast message.
3. **stdout of subcommands / hooks / MCP** — no announcement on those paths.
