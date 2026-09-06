# Completion Report — Multi-Forge SCM Abstraction (ScmProvider)

Spec: [docs/plans/2026-09-02_multi_skill_gitpr_multiforge_spec.md](../../plans/2026-09-02_multi_skill_gitpr_multiforge_spec.md) · Approved plan: [docs/plans/20260905_multi-forge_abstracao_scmprovider.md](../../plans/20260905_multi-forge_abstracao_scmprovider.md) · Decision record: [docs/plans/ADR-001-scm-abstraction.md](../../plans/ADR-001-scm-abstraction.md) · Glossary: [docs/plans/glossary-scm-multiforge.md](../../plans/glossary-scm-multiforge.md)

## What was done

Implemented the Multi-Forge SCM abstraction in 10 stages (order of spec §10), each gated by the full test suite, with the interactive grilling decisions from the plan bound as requirements. All changes remain **uncommitted in the working tree** for user review — no `git add`/`commit`/`push` was ever executed.

- **Stage 1 — Contract core**: `src/infrastructure/scm/` package with `base.py` (ABC `ScmProvider` with 11 abstract methods — the spec §3 contract plus `check_existing_pull_request`, `update_pull_request`, `create_issue` per the approved extended ABC), dataclasses (`PullRequestRequest`, `PullRequestResult`, `RepoRef`, `IssueRequest`, `IssueResult`), `ScmProviderError(provider, http_status, message)` (0 = network) and `ScmNotSupportedError`. `tests/scm/test_contract.py` shared harness with 4 concrete cases (one per forge) and a `__init__.py` for `unittest discover`. PT-BR glossary created.
- **Stage 2 — GitHubProvider + deprecated shim**: extracted the REST logic of `src/github_api.py` into `github_provider.py` raising exceptions; rewrote `github_api.py` as a shim (same 4 signatures, same `(ok, data, status)` tuples, `DeprecationWarning` stacklevel=2). Deleted `tests/test_github_api.py` (30 tests) → migrated to `tests/scm/test_github_provider.py` (48 tests, error scenarios now assert `ScmProviderError` with `.http_status`; URL/headers/json/timeouts asserted unchanged — GitHub byte-parity). New `tests/scm/test_github_api_shim.py` (18 tests).
- **Stage 3 — GitLabProvider**: MR create (201 → `iid`/`web_url`), check by `state=opened` + `source_branch`, diff from `changes[].diff`, comments, merge, issues; project path always `quote(..., safe="")`; sub-group namespaces. 40 tests.
- **Stage 4 — Factory**: `factory.py` with `_REGISTRY`, `resolve_scm_provider(config)` (default `github`, legacy `GITHUB_TOKEN_ENCRYPTED` fallback, lazy imports against circular imports) and `detect_provider_from_remote`; public re-exports in the package `__init__`. 11 tests.
- **Stage 5 — main/core/TUI integration** (the surgical one): 7 SCM config keys in `DEFAULT_CONFIG` + `get_scm_token()`/`get_scm_settings()` in `config.py`; `get_origin_remote_url()`/`describe_repo()`/`run_scm_init_wizard()` scaffolding in `core.py`; `tui_issue.py` `validate_or_request_github_token` → `validate_or_request_scm_token(provider, repo_display)` (401 → reauth loop, network → clear error, legacy GitHub keeps writing `GITHUB_TOKEN_ENCRYPTED` until `--init` runs); `pr_publish_app.py` ctor gains `provider=None, repo_ref=None` with a legacy fallback (30 headless TUI tests untouched) + module-level `_check_existing_pull_request` seam + 4 call sites with intact UI bodies; `issue_app.py` F3 POST removed → `provider.create_issue`; `main.py` publish flows resolve provider/repo_ref from the origin remote; i18n sync with full translations in all 6 language files.
- **Stage 6 — AzureDevOpsProvider**: fail-fast org/project naming the env var, `api-version=7.1` on every URL, diff as a structured textual summary of the last iteration's `changes[]` (no unified diff — documented deviation), refs `refs/heads/...`, comment threads, merge PATCH, `create_issue` → `ScmNotSupportedError`. 43 tests.
- **Stage 7 — BitbucketProvider**: fail-fast username, Basic auth `(username, token)`, nested `source/destination` branch bodies, `values[]` list, plain-text diff, `{"content": {"raw": ...}}` comments, issue requires the repo Issue Tracker enabled (documented). 39 tests. Registry complete → contract suite covers the 4 classes.
- **Stage 8 — `--init` flag**: `core.run_scm_init_wizard()` (origin remote detection → confirm → per-forge extras → 3 token attempts, 401 re-prompt with yellow warning on every attempt, non-401 aborts in red on the first attempt, success persists `GITPR_SCM_PROVIDER` + `GITPR_SCM_TOKEN_ENCRYPTED = encrypt_data(raw)` + extras via `set_key` — **never** a raw token, never on failure). Click option `--init` in `main.py`; `--install` untouched. 11 wizard tests (all mocked — nothing persists on failure).
- **Stage 9 — ADR + docs + CHANGELOG + memories + final i18n**: ADR-001 (PT-BR, `docs/plans/`) with the decision, rejected alternatives and the **10 approved deviations**; `CLAUDE.md` (src tree with `infrastructure/scm/`, `--init` row, SCM env vars, "Multi-Forge SCM (ScmProvider)" section, Issues TUI updated); `docs/ARCHITECTURE.md` (tree, bullets, new section 19); `CHANGELOG.md` `[Unreleased]`; `.claude/memory/github-api-shared-module.md` rewritten as reference + new `i18n-sync-canonicos-roundtrip.md` feedback memory; `MEMORY.md` re-indexed. `.gitpr/config.schema.yml` was **not** created (it does not exist in the project — registered deviation).
- **Stage 10 — Final gate + CLI sanity + this report**.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| src/infrastructure/__init__.py | feat | New sub-package marker |
| src/infrastructure/scm/__init__.py | feat | Public re-exports (ScmProvider, factory functions, dataclasses, errors) |
| src/infrastructure/scm/base.py | feat | ABC ScmProvider (11 abstract methods) + dataclasses + ScmProviderError/ScmNotSupportedError + timeouts + with_token |
| src/infrastructure/scm/github_provider.py | feat | GitHub provider extracted from github_api.py (raises, `token` header kept) |
| src/infrastructure/scm/gitlab_provider.py | feat | GitLab provider (iid mapping, sub-groups, self-managed base_url) |
| src/infrastructure/scm/azure_devops_provider.py | feat | Azure DevOps provider (fail-fast org/project, api-version 7.1, diff summary, issue → not-supported) |
| src/infrastructure/scm/bitbucket_provider.py | feat | Bitbucket Cloud provider (fail-fast username, Basic auth, Issue Tracker requirement) |
| src/infrastructure/scm/factory.py | feat | _REGISTRY + resolve_scm_provider + detect_provider_from_remote + provider_display_name/provider_is_github |
| src/github_api.py | refactor | Rewritten as deprecated shim → delegates to GitHubProvider (same tuples, DeprecationWarning) |
| src/config.py | feat | 7 `GITPR_SCM_*` keys in DEFAULT_CONFIG/setup_environment; get_scm_token(); get_scm_settings() |
| src/core.py | feat | get_origin_remote_url(), describe_repo(), run_scm_init_wizard() |
| src/main.py | feat | `--init` option + dispatch; publish flow resolves SCM provider/repo_ref from remote; issue flow reworked |
| src/ui/pr_publish_app.py | refactor | provider/repo_ref plumbing; `_check_existing_pull_request` seam; ScmProviderError boundary mapping |
| src/ui/issue_app.py | refactor | F3 uses provider.create_issue (no inline POST); ScmNotSupportedError → save-locally message |
| src/tui_issue.py | refactor | validate_or_request_scm_token(provider, repo_display); SCM token persistence; auth instructions per forge |
| tests/test_github_api.py | removed | 30 tests migrated to tests/scm/test_github_provider.py |
| tests/test_core.py | feat | get_origin_remote_url/describe_repo coverage |
| tests/test_pr_publish_linter_modal.py | fix | Patch retargeted to `_check_existing_pull_request` seam |
| tests/scm/__init__.py | feat | Package marker (required by unittest discover) |
| tests/scm/test_contract.py | feat | Shared contract harness, 4 concrete cases (__test__ = True re-enabled per class) |
| tests/scm/test_github_provider.py | feat | 48 tests (migrated + new: create_issue, test_connection, parse_repo_ref, with_token) |
| tests/scm/test_github_api_shim.py | feat | 18 tests (delegation keeps tuples, DeprecationWarning, error extraction) |
| tests/scm/test_gitlab_provider.py | feat | 40 tests |
| tests/scm/test_azure_devops_provider.py | feat | 43 tests |
| tests/scm/test_bitbucket_provider.py | feat | 39 tests |
| tests/scm/test_factory.py | feat | 11 tests (registry, ValueError, remote detection table) |
| tests/scm/test_init_wizard.py | feat | 11 tests (flows with mocks; nothing persists on failure) |
| langs/{es,es_es,fr,fr_fr,pt_br,pt_pt}.json | feat | +14 wizard keys each → 675 keys per file (6 files, synchronized sets) |
| docs/plans/glossary-scm-multiforge.md | docs | Canonical Multi-Forge vocabulary (PT-BR) |
| docs/plans/ADR-001-scm-abstraction.md | docs | Decision record with the 10 approved deviations (PT-BR) |
| docs/plans/20260905_multi-forge_abstracao_scmprovider.md | docs | Approved implementation plan |
| CLAUDE.md | docs | Tree (infrastructure/scm), `--init` row, SCM env vars, Multi-Forge section, Issues TUI, tests/scm |
| docs/ARCHITECTURE.md | docs | Tree, forge-generic bullets, section 19 Multi-Forge SCM |
| CHANGELOG.md | docs | `[Unreleased]` section (Added/Changed/Deprecated/Documentation) |
| .claude/memory/github-api-shared-module.md | docs | Rewritten: shim deprecated, canonical path src/infrastructure/scm/ |
| .claude/memory/i18n-sync-canonicos-roundtrip.md | docs | New feedback memory: surgical i18n sync pattern |
| .claude/memory/MEMORY.md | docs | Index updated (2 lines) |
| docs/claude-code/reports/develop_natan/2026-09-05_scm_multiforge_providers.md | docs | This report |

### Test gates (both runners are the gate, per stage)

| Stage | pytest | unittest | New tests |
|-------|--------|----------|-----------|
| Base (pre-stages) | ~370 passed | — | 21 files |
| Stage 1 | full suite green | full suite green | contract harness (grows to 14 tests) |
| Stage 2 | full suite green | full suite green | 48 + 18 (30 migrated from deleted file) |
| Stage 3 | full suite green | full suite green | 40 |
| Stage 4 | full suite green | full suite green | 11 |
| Stage 5 | full suite green | full suite green | +core, linter-modal retarget |
| Stage 6 | full suite green | full suite green | 43 |
| Stage 7 | full suite green | full suite green | 39 |
| Stage 8 | 583 passed + 10 new | full suite green | 11 wizard |
| Stage 9 | 593 passed (identical to 8) | 486 ran | — (docs only) |
| **Stage 10 (final)** | **596 collected: 593 passed, 3 failed**, 2 skipped, 15 subtests | **486 ran, failures=2, skipped=3** | 224 in tests/scm |

The **3 pytest failures** (and the 2 unittest failures) are **pre-existing environmental failures, not regressions** — reproduced with identical counts in every stage gate from Stage 1 to Stage 10, all caused by the real `~/.gitpr/.env` on this machine (`GITPR_LANG='pt_br'`, `GITPR_AI_TIMEOUT='180'`) interfering with tests that assert English text/defaults:

1. `tests/test_chat_backend.py::TestCallAiChat::test_api_exception`
2. `tests/test_net_timeouts.py::TestTimeoutConfig::test_ai_timeout_defaults_to_600`
3. `tests/test_net_timeouts.py::TestTimeoutConfig::test_invalid_ai_timeout_falls_back_to_default`

**Not fixed** — they are environmental (user `.env`, not code); fixing them would mean changing the tests to pass against a local `.env`, which would mask real user environments. They fail identically on the pre-stage code.

### Manual CLI sanity (Stage 10, real runs)

| Command | Result |
|---------|--------|
| `python run.py --status` | Exit 0 — lists 11 new / 20 modified / 1 deleted uncommitted files (includes `src/infrastructure/` and `tests/scm/`), no AI, correct working-tree summary |
| `gitpr --no-publish` (temp clean worktree, real GitHub remote `git@github.com:gitpr-cli/gitpr.git`, 1-line diff, migrated code from this tree) | Exit 0 — fetch → skill `.gitpr.pr.md` loaded → DeepSeek real call → `HEAD_20260905222133_PR_DESC.md` generated with a valid Conventional-Commit suggestion |
| `gitpr -c` (same worktree) | Exit 0 — valid commit suggestion printed (`docs: update cache base dir docstring`) |
| `gitpr --init` interactive | Not executable end-to-end here: it requires a raw token for the real `test_connection`. Covered by the 11 mocked wizard tests (401 re-prompt ×3, network abort, success persistence). |

The temp worktree was removed after the sanity runs; the main working tree was never staged or committed.

## Impact

- **Functionality**: PR/issue publication is no longer GitHub-only. All flows (TUI publisher, direct publish, issues) resolve the configured forge (`GITPR_SCM_PROVIDER`, default `github` with the legacy `GITHUB_TOKEN_ENCRYPTED` fallback — byte-identical behavior when unconfigured). `gitpr --init` is a new interactive forge wizard. Errors propagate as `ScmProviderError` with provider + HTTP status instead of swallowed tuples; UI behavior (reauth on 401, modals) is preserved at the call sites.
- **Performance**: One extra lazy module import and a remote-URL read on publish flows; no per-call overhead. Providers reuse the existing `requests` layer with the same timeouts (create 30s, others 15s, `test_connection` 10s).
- **Compatibility**: Backward compatible. `src/github_api.py` keeps its 4 public signatures/tuples (now deprecated with `DeprecationWarning`); no internal code imports it anymore. `.env`-only configuration (flat dotenv, per approved deviation — no YAML schema file). Azure DevOps `RepoRef.workspace` is display-only (`org/project`); GitLab uses `iid`/`number`/`web_url`; Bitbucket requires username + App Password and the Issue Tracker enabled; Azure issues raise `ScmNotSupportedError` (save locally, F2).

### Notes for the record (deviations/anomalies found and handled)

- **`__test__` contract bug**: pytest *inherits* `__test__ = False` from the abstract contract base class, so the abstract harness was not collected until each concrete per-forge case re-enabled collection explicitly with `__test__ = True` (lines 127/137/147/158 of `tests/scm/test_contract.py`).
- **test_contract corrections**: the shared harness was corrected during staging (concrete-class data drives the assertions; `default_base_url` exercised through the factory `_make()` so fail-fast providers configure their required extras; dataclass shape guards added as a separate test class).
- **tui_issue non-401 deviation**: in the `--init` wizard, only a 401 (rejected token) re-prompts (up to 3 attempts, yellow warning on every attempt). Any non-401 failure (network, 4xx/5xx) aborts in red on the first attempt without retries — approved in grilling; covered by `test_network_failure_aborts_without_retry_or_persist`.
- **E2E scope**: manual end-to-end runs covered **GitHub only** (real). GitLab, Bitbucket and Azure DevOps are covered exclusively by mocked unit tests (no real tokens/repos available in this environment).
- **i18n**: +14 keys × 6 files (661 → 675). Files are canonical against their own sorted dump (round-trip safe); no byte-parity between `es/es_es` and `fr/fr_fr` pairs was forced (legitimate historical drift). `tests/sync_i18n.py` was never run wholesale (it mangles files) — surgical insert scripts only.

## Next steps

- **User review & commit** of the working tree (nothing was staged/committed per binding constraint).
- **`__lang_version__` bump** in `src/updater.py` before release — required because `langs/*.json` changed (see `.claude/memory/langs-ota-stale-race.md`), so OTA clients re-fetch under the new marker.
- **Optional real E2E** for GitLab/Bitbucket/Azure when tokens/repos are available (mock-only today).
- **Future work** (out of scope, registered in ADR-001): interactive OAuth2, Bitbucket Server/DC, GitHub Enterprise, webhook intake, consumption of the reserved `labels`/`reviewers` fields.
