# Completion Report — PR Publication Directly to GitHub (`--publish`)

## What was done
- Created a new `--publish` CLI flag that opens an interactive Textual TUI for reviewing, editing, and publishing Pull Requests directly to GitHub via REST API
- Created a shared GitHub API module (`src/github_api.py`) with `create_pull_request()` for reuse across TUI and direct-publish paths
- Added `--base` and `--no-edit` companion flags for branch selection and editor-less publishing
- Added `PR_DEFAULT_BASE` and `PR_AUTO_PUBLISH` environment variables for persistent configuration
- Added full i18n coverage (29 new keys) across all 4 language files (pt_br, pt_pt, es_es, fr_fr)
- Created technical documentation in 5 languages
- Updated all 5 README variants and CLAUDE.md

## Changed files

| File | Change type | Description |
|------|-------------|-------------|
| src/github_api.py | feat (new) | Shared `create_pull_request()` function with full error extraction |
| src/ui/pr_publish_app.py | feat (new) | Textual TUI app for PR editing and publishing (mirrors issue_app.py) |
| src/ui/pr_publish_help.py | feat (new) | Help modal for PR publisher TUI (mirrors help_screen.py) |
| src/main.py | feat | Added `--publish`, `--base`, `--no-edit` flags, HELP_MAP entry, publish dispatch logic with reauth loop, `--no-edit` guard, updated banner |
| src/config.py | feat | Added `PR_DEFAULT_BASE` and `PR_AUTO_PUBLISH` to DEFAULT_CONFIG, added `get_pr_auto_publish()` helper |
| langs/pt_br.json | feat | Added 29 translation keys (520 total) |
| langs/pt_pt.json | feat | Added 29 translation keys (515 total) |
| langs/es_es.json | feat | Added 29 translation keys (515 total) |
| langs/fr_fr.json | feat | Added 29 translation keys (515 total) |
| docs/pull-request-publication.md | feat (new) | Technical documentation (EN) |
| docs/pull-request-publication.pt_br.md | feat (new) | Technical documentation (PT-BR) |
| docs/pull-request-publication.pt_pt.md | feat (new) | Technical documentation (PT-PT) |
| docs/pull-request-publication.es_es.md | feat (new) | Technical documentation (ES) |
| docs/pull-request-publication.fr_fr.md | feat (new) | Technical documentation (FR) |
| README.md | docs | Added `--publish` bullet + documentation link |
| README.pt_br.md | docs | Added `--publish` bullet + documentation link (PT-BR) |
| README.pt_pt.md | docs | Added `--publish` bullet + documentation link (PT-PT) |
| README.es_es.md | docs | Added `--publish` bullet + documentation link (ES) |
| README.fr_fr.md | docs | Added `--publish` bullet + documentation link (FR) |
| CLAUDE.md | docs | Added `--publish` to command flow table, env vars list, and stack table |

## Impact
- **Functionality:** Users can now publish PRs directly to GitHub from the terminal via `gitpr --publish`. The TUI allows editing all fields before publishing. `--no-edit` enables CI/CD scenarios. `PR_AUTO_PUBLISH=true` enables always-on publisher mode.
- **Performance:** No impact on existing flows. The publish path reuses existing PR generation, only adding the API call and TUI launch when explicitly requested.
- **Compatibility:** Fully backward compatible. Default `gitpr` behavior unchanged. New flags are additive. Existing token validation flow (`validate_or_request_github_token`) is reused without modification. All 130 existing tests continue to pass.

## Verification
- `from src.main import cli` imports successfully
- All 4 language JSONs valid (520/515/515/515 keys)
- 130/131 tests pass (1 pre-existing failure in `test_chat_backend.py::test_api_exception` — pt_BR locale mismatch, unrelated)
- Publish flow follows same reauth loop pattern as Issue TUI (lines 563-583 in main.py)
- `--no-edit` guard warns when used without publish trigger
