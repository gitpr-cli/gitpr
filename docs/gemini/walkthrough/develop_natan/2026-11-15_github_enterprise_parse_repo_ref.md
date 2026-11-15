# Walkthrough — Support GitHub Enterprise Custom Domains in `GitHubProvider.parse_repo_ref` (Etapa 6)

## Changes Made
1. **`src/infrastructure/scm/github_provider.py`**:
   - Added `_REMOTE_RE` to parse host-agnostic git remote URLs (`https://`, `http://`, `ssh://`, `git://`, and SCP `git@host:owner/repo.git`, with optional `user@` and `:port`).
   - Updated `GitHubProvider.parse_repo_ref` to strip any URL scheme, match `_REMOTE_RE`, and enforce a strict 2-segment `owner/repo` path, raising `ValueError` for invalid formats or depths.
2. **`tests/scm/test_github_provider.py`**:
   - Added `TestParseRepoRef` with unit tests for `github.com`, GitHub Enterprise custom domains (`github.acme.com`), and malformed/invalid-depth URLs.
3. **`docs/scm-multiforge.{md,pt_br.md,pt_pt.md,es_es.md,fr_fr.md}`**:
   - Updated §1.2 (table row 3 and example block) and §3 (`GITHUB_BASE_URL` row) across all 5 languages while preserving structural parity.

## What Was Tested
Executed:
```bash
python -m pytest tests/scm/test_github_provider.py tests/scm/test_contract.py tests/scm/test_factory.py tests/unit/test_docs_translation_parity.py tests/unit/test_scm_multiforge_docs_parity.py -v
```

## Validation Results
- `146 passed, 2 skipped, 39 subtests passed in 3.59s` (the 2 skipped tests are contract base-class skips for providers without `REQUIRED_EXTRA` in `tests/scm/test_contract.py`).
