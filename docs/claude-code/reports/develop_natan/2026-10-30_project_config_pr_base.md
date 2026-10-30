## Completion Report — Project-local Pull Request base branch

### What was done

- Added a second configuration store, versioned with the repository:
  `.gitpr/conf/gitpr.config.yml`, holding `pull_request.base_branch`. The file is
  seeded on every invocation inside a git repository (subcommands and `--install`
  included), seeded with `PR_DEFAULT_BASE` when one is configured and literal
  `main` otherwise, and **never overwritten**.
- Introduced one resolver for the PR target —
  `--base` > project file > `PR_DEFAULT_BASE` > auto-detected `origin/HEAD` >
  `main` — used by the default flow, `--no-edit`, the publish TUI and the MCP
  `publish_pull_request` tool. The AI diff base is unchanged (`origin/HEAD`,
  ADR-015 decision 8).
- Target verification is fail-fast on every source: a branch missing from
  `origin` stops the run with a `git fetch origin <branch>` hint. A malformed
  project file warns and falls through the chain instead of stopping.
- Added the **Project** category to `gitpr config`: read-only file path,
  editable base branch (written to the YAML, never to `.env`), and a read-only
  effective branch with its source. `PR_DEFAULT_BASE` was relabelled
  **Global Default Base Branch**.
- `--install` reports whether the project file was created or already existed
  and warns when the user's `.gitignore` keeps it out of the repository.
- Fixed during verification: the seed and the resolver read `PR_DEFAULT_BASE`
  with `os.getenv()` only, but they run before `setup_environment()` — and the
  `config` subcommand never loads the dotenv file at all — so a default saved
  through the TUI was invisible and the seed wrote `main` instead. The new
  `_global_default()` reads the variable first, then `~/.gitpr/.env`; a
  variable present but empty still means "no global default".
- Documentation: four English pages + four translations each (config TUI,
  pull-request publication, default PR description, install wizard), ADR-015,
  the configuration glossary, `CLAUDE.md`, plus the grill survey, the
  plansfacts artefact and the mandated plan copy.
- No commit was made (`CLAUDE.md` rule).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/project_config.py` | feat | New module: project path resolution, seed, YAML read/write, `_global_default()`, the precedence resolver and `verify_remote_base()` |
| `src/main.py` | feat | Seed in the root callback; target resolution moved after the `--no-publish` return, via `resolve_pull_request_base()`; `--base` help updated |
| `src/core.py` | feat | `run_install_wizard()` seeds and reports the project file |
| `src/mcp_server.py` | feat | `publish_pull_request` resolves through the shared resolver; `BaseBranchError` returns a JSON error |
| `src/config_schema.py` | feat | `STORE_ENV`/`STORE_PROJECT`, `ConfigField.store`, the `project` category and its three fields; `PR_DEFAULT_BASE` relabelled |
| `src/ui/config_app.py` | feat | Project state, store-aware rows/plan/save, project YAML written first, effective-branch row, save-time warning |
| `tests/conftest.py` | test | `GITPR_SKIP_PROJECT_CONFIG_SEED` pinned so the suite never seeds the checkout |
| `tests/test_project_config.py` | test | New unit suite over real temporary repositories; `PR_DEFAULT_BASE` and `ENV_FILE` pinned per test |
| `tests/test_project_config_cli.py` | test | New CLI suite: seed on root run and subcommands, silence under `--quiet`, never on help, outside a repository, existing file untouched, global default read from `~/.gitpr/.env` |
| `tests/test_config_app.py` | test | `TestProjectSection`: effective row, save writes only the YAML, missing branch warns without blocking |
| `tests/test_config_schema.py` | test | Project category shape; no `PROJECT_*` key in `DEFAULT_CONFIG` |
| `tests/test_mcp_server.py` | test | `publish_pull_request` parity with the project file and the verification failure |
| `langs/*.json` (6) | docs | Translations for the new keys |
| `docs/config-tui.md` +4 | docs | Project category, §1.8, FIELDS count, `project_config.py` row |
| `docs/pull-request-publication.md` +4 | docs | Precedence table, project file sections, verification, relabelled global default |
| `docs/install-wizard.md` +4 | docs | Seed paragraph |
| `docs/pr-descricao-padrao.md` +4 | docs | Resolution chain sentence |
| `docs/plans/ADR-015-project-local-pr-base.md` | docs | New ADR: nine decisions, consequences, rejected alternatives |
| `docs/plans/glossary-config-tui.md` | docs | Project configuration file, PR target base, diff base, effective base branch |
| `CLAUDE.md` | docs | `--base` row, project file bullet, `GITPR_SKIP_PROJECT_CONFIG_SEED` |
| `docs/survey/20261030_project_pr_base_surveyfacts.md` | docs | Grill survey |
| `docs/plans/develop_natan/20261030_project_pr_base_plansfacts.md` | docs | Approved execution plan |
| `docs/claude-code/plans/develop_natan/2026-10-30_develop_natan_project_config_pr_base.md` | docs | Plan in the `CLAUDE.md` location |

### Verification

- `tests/test_project_config.py` + `tests/test_project_config_cli.py`: **39
  passed**.
- `tests/test_config_app.py` + `tests/test_config_schema.py`: **129 passed**.
- `tests/test_mcp_server.py -k "publish or base"`: **11 passed**.
- Full suite (one test deselected, see below): **3053 passed, 4 failed, 2
  skipped, 1 deselected** in 436 s.
- Three of the four are the known `tests/test_i18n.py` failures (11 missing keys
  per language for commit/publish/MCP strings and two `pt_br` orphans),
  verified before this change; no new key is involved.
- The fourth is a Textual timing flake in
  `tests/test_commit_app.py::TestCommitAppHeadlessFlow::test_headless_full_flow`
  — a five-second wait for the commit screen to close. The test module and
  `src/ui/commit_app.py` are identical to `HEAD`, and the test also fails two of
  three times when run alone, so it is not related to this change.
- An earlier run of this working tree also produced eight intermittent failures
  in `tests/test_plugins.py::TestLoadLinterRulesWithPlugins`. Those tests assert
  that no linter rules load; the seven embedded secret rules appeared because
  `GITPR_LINTER_SECURITY` had leaked into the process environment from the
  machine's real `~/.gitpr/.env` (`true` there, `false` in
  `tests/conftest.py`). Every file involved — the test module, `src/config.py`,
  `src/linter_engine.py`, `src/security_ruleset.py` — is untouched by this
  change, and the final run, instrumented to watch that variable after every
  test, saw it never leave `false` and those tests pass. It is the same kind of
  live-profile leakage the suite already documents for the locale.
- One environment-level hang was isolated and excluded with `--deselect`:
  `TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched`
  runs `gitpr -c` under `CliRunner`, opens `CommitApp` and waits for keyboard
  input that never arrives. The same command hangs on a clean worktree checked
  out at `HEAD` (652e99c), so it is **not** caused by this change; the run above
  is the suite minus that test.

### Impact

- **Functionality:** the target branch of a pull request is now a property of
  the repository, versioned and shared by the whole team. The global default
  still applies to repositories without a value. Nothing about the AI diff
  changed.
- **Performance:** one `git rev-parse --show-toplevel`, one file existence
  check and, on a missing branch, one extra `git rev-parse` per run — no
  network access beyond the existing `git fetch`.
- **Compatibility:** a repository whose default branch is not `main` gets a
  seeded `main`, which then fails verification until edited — accepted
  consequence of the settled seed rule, mitigated by the error message and the
  versioning hint. Malformed project files are never overwritten by the TUI.

### Next steps

- Review the working-tree diff and commit with:
  `feat: add project-local pull request base branch configuration`
- Decide whether the AI diff base should follow the project file too
  (the deliberate debt named in ADR-015).
