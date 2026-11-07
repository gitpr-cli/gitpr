## Completion Report — Per-repository forge and per-forge token slots

### What was done

The SCM forge stopped being a machine-wide setting. The bug report behind this
task: configuring a GitLab repository wrote `GITPR_SCM_PROVIDER=gitlab` into
`~/.gitpr/.env`, and from then on every GitHub repository on the same machine was
treated as GitLab — the global key took precedence over the remote detection, so
the GitHub token was never found. A second leak of the same class existed in
`GITPR_SCM_BASE_URL`, which `resolve_scm_provider()` forwarded to *every*
provider.

- **New resolver, `src/scm_settings.py`** ([ADR-016](../../../plans/ADR-016-per-provider-scm-settings.md)).
  It resolves the forge **per repository** — project override in
  `.gitpr/conf/gitpr.config.yml` → `origin` remote detection → `github` — and
  keeps **one encrypted token per forge**: `GITHUB_TOKEN_ENCRYPTED`,
  `GITLAB_TOKEN_ENCRYPTED`, `BITBUCKET_TOKEN_ENCRYPTED`,
  `AZURE_DEVOPS_TOKEN_ENCRYPTED`, each with its own `<PROVIDER>_BASE_URL`.
  `GITPR_SCM_TOKEN` (raw, CI only) stays single and global, consulted first.
  `get_scm_settings()` returns the flat dict the factory already consumed, so
  each consumer changed by one import line.
- **Detection distinguishes "unknown" from "GitHub"**:
  `detect_provider_from_remote(url, default="github")` — `default=None` reports
  "not recognised" so the resolver can fall through instead of assuming GitHub.
- **One-shot migration** (`migrate_legacy_scm_config()`), idempotent, run on the
  first resolver call and by `--init`: moves `GITPR_SCM_PROVIDER` +
  `GITPR_SCM_TOKEN_ENCRYPTED` + `GITPR_SCM_BASE_URL` into the slot of the forge
  the pair names, never overwriting a filled slot, removing the retired lines,
  and degrading to process values (with a warning) when the file cannot be
  written.
- **Retired keys**: `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` and
  `GITPR_SCM_BASE_URL` are gone from the schema, the seed, the config TUI and
  every read. No legacy branch survives in any reader.
- **`gitpr --init` is now a wizard of the repository**: it detects, lets you
  confirm (or choose another forge, or be asked when the host names none),
  validates the token with up to 3 attempts, and persists **only on success** —
  the token into its forge's slot, the extras (`GITPR_SCM_ORGANIZATION`,
  `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME`) and a `scm.provider` override
  committed to the project file **only when the chosen forge differs from the
  detected one**.
- **Interactive vs non-interactive token handling**:
  `validate_or_request_scm_token(provider, repo_display, allow_prompt=...)`. An
  interactive run removes an expired token from *that* forge's slot and asks for
  a new one; hooks, the MCP server and CI never prompt and never delete — they
  stop with a message naming `gitpr --init`.
- **`gitpr config` shows the effective forge** and always lists the four token
  rows plus the four base-URL rows (hiding a forge's slot would recreate the
  original bug); the extras follow the effective provider. Each token row probes
  its own forge.
- Documentation: ADR-016 (new), a "superseded in part" note on ADR-001, the SCM
  glossary, `CLAUDE.md`, `docs/scm-multiforge.md` + 4 translations and
  `docs/ARCHITECTURE.md` + 4 translations; the six `langs/*.json` files got the
  31 new keys and lost the 10 orphaned ones.
- **Test harness — two environment leaks found while validating the suite.**
  (1) The interface language is re-pinned around every test: the configuration
  screen re-reads the `.env` it just saved and the MCP tool path re-applies
  `GITPR_LANG` at every call, and neither puts the previous value back, so a
  developer profile in pt-BR leaked into the assertions of every module
  collected afterwards. (2) `cli()`'s hooks auto-sync is neutralised for the
  whole suite: whenever the markers in the developer's real `~/.gitpr/.env`
  disagree with the shipped version or the wanted hook language, it downloads
  the hook scripts into the current checkout and then re-reads that `.env`
  with `load_dotenv(..., override=True)` — which imported the whole profile
  into the test process, flipping `GITPR_LINTER_SECURITY` from the pinned
  `false` to `true` and failing the eight `test_plugins.py` tests that assert
  exact rule counts (the same run also rewrote the real `.git/hooks`). Both are
  now documented in `tests/conftest.py`, and the four duplicated per-directory
  language fixtures were replaced by the root one.
- No commit was made (`CLAUDE.md` rule).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/scm_settings.py` | feat | New module: per-repository forge resolution, per-forge token/base-URL slots, one-shot legacy migration, `get_scm_settings()` adapter |
| `src/infrastructure/scm/factory.py` | feat | `detect_provider_from_remote(remote_url, default="github")`; module docstring points configuration at `src.scm_settings` |
| `src/project_config.py` | feat | `scm.provider` read/write alongside `pull_request`, `ProjectConfig.provider`, `SCM_PROVIDER_FIELD` / `EFFECTIVE_PROVIDER_FIELD`; structural errors go to `error`, never raise |
| `src/config_schema.py` | refactor | New GitLab group; four token rows and four base-URL rows; extras gated by the effective provider; retired keys removed; `COMPUTED_CONTROLLERS` |
| `src/ui/config_app.py` | feat | Runs the migration once, caches `origin_remote_url()`, computes the effective forge, disables read-only enums, probes each token row against its own forge |
| `src/tui_issue.py` | fix | Token stored in `TOKEN_KEYS[provider.name]`; `allow_prompt` contract; expired token removed only from its own slot |
| `src/core.py` | refactor | `run_scm_init_wizard()` rewritten as a per-repository wizard (detection with "unknown" handling, override written only when it differs, per-forge persistence in one guarded block) |
| `src/main.py` | refactor | `_resolve_scm_context` uses `get_scm_settings()` and prints its warnings; `--init` help rewritten; callers pass `allow_prompt=may_ask` |
| `src/metrics.py` | refactor | Cycle section resolves through `src.scm_settings` with the remote URL |
| `src/release_engine.py` | refactor | Release publishing resolves through `src.scm_settings` with the remote URL |
| `src/mcp_server.py` | refactor | Non-interactive contract: no token means "Run 'gitpr --init'", never a prompt |
| `src/config.py` | refactor | Removed `get_scm_settings()`, `get_scm_token()`, `get_scm_provider()` (`get_github_token()` kept for the factory fallback and the shim) |
| `tests/scm/test_scm_settings.py` | test | New: precedence, per-provider credentials, flat settings, the six migration cases |
| `tests/test_tui_issue_token.py` | test | New: token slot per forge, non-interactive skip, interactive retry after 401 |
| `tests/scm/test_factory.py` | test | `default=None` "unknown" cases and default passthrough |
| `tests/scm/test_init_wizard.py` | test | Per-forge `set_key` targets, override written only when it differs, `PermissionError` path |
| `tests/test_config_app.py` | test | Four token rows always listed, extras follow the effective provider, re-filter before saving |
| `tests/test_config_schema.py` | test | Token/base-URL fields, `COMPUTED_CONTROLLERS` visibility |
| `tests/test_project_config.py` | test | `scm:` section read/write, coexistence with `pull_request:`, malformed YAML |
| `tests/test_metrics.py`, `tests/test_release_engine.py` | test | Patch target moved to `src.scm_settings.get_scm_settings` |
| `tests/conftest.py` | test | Two root autouse guards: the interface language is re-pinned around every test, and `cli()`'s hooks auto-sync is neutralised (it re-read the developer's `~/.gitpr/.env` with `override=True` and rewrote the real `.git/hooks`) |
| `tests/{badge,demo,integration,split}/conftest.py` | test | Their duplicated `english_interface` fixtures removed — the guarantee now lives in the root conftest |
| `langs/{pt_br,pt_pt,es_es,es,fr_fr,fr}.json` | docs | 31 new keys translated, 10 orphaned keys removed |
| `docs/plans/ADR-016-per-provider-scm-settings.md` | docs | New ADR: per-repository forge, per-forge slots, one-shot migration |
| `docs/plans/ADR-001-scm-abstraction.md` | docs | "Superseded in part by ADR-016" note |
| `docs/plans/glossary-scm-multiforge.md` | docs | New terms (token slot, provider override, effective provider, one-shot migration) and the rewritten key tables |
| `docs/scm-multiforge*.md` (5), `docs/ARCHITECTURE*.md` (5) | docs | Per-repository forge, per-forge slots and the new wizard contract in every language |
| `CLAUDE.md` | docs | Env-var list and the Multi-Forge SCM section rewritten |
| `docs/plans/develop_natan/20261107_per_provider_scm_settings_plansfacts.md`, `docs/survey/20261107_per_provider_scm_settings_surveyfacts.md` | docs | Grill artefacts of this session |

### Impact

- **Functionality:** the forge now follows the repository. A machine can serve
  GitHub, GitLab, Bitbucket and Azure DevOps at the same time, each repository
  reading only its own encrypted slot; a token of one forge can no longer answer
  for another, and a base URL no longer leaks across forges. Repositories whose
  remote does not name the forge (self-hosted domains) fall back to `github`
  unless the project override says otherwise — `--init` writes that override and
  the migration warns about it.
- **Compatibility:** intentional break. A pre-existing global
  `GITPR_SCM_TOKEN_ENCRYPTED` was moved by the one-shot migration into the slot
  of the forge `GITPR_SCM_PROVIDER` named; any *other* repository of the same
  forge asks for its token once (interactive) or stops with "run `gitpr --init`"
  (hooks, MCP, CI). The retired keys are removed from the environment after the
  migration, so no reader can silently keep using them. GitHub installations
  without SCM configuration are byte-identical (same `GITHUB_TOKEN_ENCRYPTED`,
  same payload).
- **Performance:** one `git remote get-url origin` per process (cached by the
  consumers); the migration is a single pass with an in-process flag, no network.

### Verification

- `python -m pytest tests -q` — 3401 passed, 2 skipped, 234 subtests passed.
- `python -m pytest tests -q --tb=short` — 3401 passed, 2 skipped, 234 subtests
  passed. This second pass was run with the hooks auto-sync gate *forced open*
  (`USERPROFILE` pointing at a copy of the profile whose
  `SCRIPTS_INSTALLED_LANG` differed from `SCRIPTS_LANG`), which is the state
  that broke the previous runs: the suite stayed green and neither the real
  `.git/hooks` nor the profile markers were touched.
- `python -m unittest discover tests -q` — 1786 tests, `OK (skipped=3)`, with
  the suite's environment pins exported in the shell (`conftest.py` is not read
  by `unittest`): `GITPR_SHOW_LOGS=false GITPR_SKIP_UPDATE_CHECK=true
  GITPR_SKIP_PROJECT_CONFIG_SEED=true GITPR_LANG=en_us
  GITPR_LINTER_SECURITY=false GITPR_ISSUE_AUTOCLOSE=true
  LANG_VERSION=v0.0.41`.
- `python -m pytest tests/test_i18n.py -q` — 22 passed (after the `langs/` update)
- `python scripts/validate_i18n.py` — the only remaining report is the
  pre-existing false positive for the two-literal badge message
  (`"🏷️ Pull requests published by GitPR carry a GitPR badge…\n" "Set
  GITPR_BADGE=false…\n"`), whose runtime key *is* present in all six files; the
  script's regex only reads the first literal.

### Next steps

- Per-repository tokens of the *same* forge still need a keyring (out of scope in
  ADR-016); two Azure organizations on one machine still share
  `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`.
- Manual smoke test on real repositories: `python run.py --init` in a GitLab repo
  and in a GitHub repo on the same machine, then `python run.py --no-edit` in
  each — both tokens must coexist in `~/.gitpr/.env`.
- A manual run in this checkout had recorded a redundant `scm: provider: github`
  override in `.gitpr/conf/gitpr.config.yml`; the file was restored to its
  committed state (the override is only meant to be written when it differs from
  the detected forge).
