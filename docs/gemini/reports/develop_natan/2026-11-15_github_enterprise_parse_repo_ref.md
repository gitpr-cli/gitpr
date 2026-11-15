## Completion Report — Support GitHub Enterprise Custom Domains in `GitHubProvider.parse_repo_ref` (Etapa 6)

### What was done
- Added host-agnostic `_REMOTE_RE` pattern in `src/infrastructure/scm/github_provider.py` (aligned with `GitLabProvider`) and refactored `GitHubProvider.parse_repo_ref` to accept custom GitHub Enterprise domains (e.g., `github.acme.com`) across HTTPS, HTTP, SCP (`git@host:owner/repo.git`), `ssh://` (with optional port), and embedded credentials, while strictly enforcing a 2-segment `owner/repo` path.
- Added `TestParseRepoRef` in `tests/scm/test_github_provider.py` covering `github.com` variants, GitHub Enterprise custom domain variants, and `ValueError` rejection for empty, single-segment, 3+ segment, and malformed URLs.
- Updated §1.2 (line 61 and example block) and §3 (`GITHUB_BASE_URL` row) in all 5 language variants of `docs/scm-multiforge.*` (`.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) while preserving exact structural parity.
- Ran the verification suite (`tests/scm/test_github_provider.py`, `tests/scm/test_contract.py`, `tests/scm/test_factory.py`, `tests/unit/test_docs_translation_parity.py`, `tests/unit/test_scm_multiforge_docs_parity.py`): `146 passed, 2 skipped, 39 subtests passed in 3.59s`.

### Changed files
| File | Change type | Description |
| --- | --- | --- |
| `src/infrastructure/scm/github_provider.py` | feat | Added `_REMOTE_RE` and refactored `GitHubProvider.parse_repo_ref` to support GitHub Enterprise custom hosts with 2-segment `owner/repo` validation |
| `tests/scm/test_github_provider.py` | test | Added `TestParseRepoRef` covering `github.com`, GitHub Enterprise hosts, and invalid URL rejection |
| `docs/scm-multiforge.md` | docs | Updated §1.2 and §3 to reflect GitHub Enterprise remote parsing support |
| `docs/scm-multiforge.pt_br.md` | docs | Synchronized §1.2 and §3 in Portuguese (Brazil) |
| `docs/scm-multiforge.pt_pt.md` | docs | Synchronized §1.2 and §3 in Portuguese (Portugal) |
| `docs/scm-multiforge.es_es.md` | docs | Synchronized §1.2 and §3 in Spanish (Spain) |
| `docs/scm-multiforge.fr_fr.md` | docs | Synchronized §1.2 and §3 in French (France) |

### Impact
- **Functionality:** Repositories hosted on GitHub Enterprise Server (e.g., `github.acme.com`) now parse `RepoRef(workspace, name)` cleanly instead of failing with `ValueError`. Arbitrary domains without `github` in the hostname (e.g., `git.acme.com`) still require `scm.provider: github` in `.gitpr/conf/gitpr.config.yml` alongside `GITHUB_BASE_URL`.
- **Performance:** Negligible (single compiled regex match per `parse_repo_ref` call).
- **Compatibility:** Backward-compatible with all `github.com` remote formats; `ValueError` continues to be raised for malformed URLs or invalid path depths.

### Next steps (if applicable)
- Proceed to Etapa 7 (`claude-code` in `_install_for_editor` error message and i18n sync) when ready.
