# Implementation Plan — Support GitHub Enterprise custom domains in `GitHubProvider.parse_repo_ref` (Etapa 6)

- **Date:** 2026-11-15
- **Branch:** `develop_natan`
- **Reference:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (Etapa 6)

## Goal Description

`GitHubProvider.parse_repo_ref` currently hardcodes `github.com`, causing remotes on GitHub Enterprise Server (e.g., `github.acme.com`) to fail with `ValueError` even when `GITHUB_BASE_URL` is configured and `detect_provider_from_remote()` already detects them as `github`. This plan refactors `GitHubProvider.parse_repo_ref` to be host-agnostic (aligned with `GitLabProvider.parse_repo_ref` while enforcing `owner/repo` 2-segment paths), adds comprehensive unit tests, and updates `docs/scm-multiforge.*` across all 5 languages.

## Proposed Changes

### 1. SCM Provider (`src/infrastructure/scm/github_provider.py`)
#### [MODIFY] `src/infrastructure/scm/github_provider.py`
- Add module-level `_REMOTE_RE`:
  ```python
  _REMOTE_RE = re.compile(
      r"^(?:[^/@]+@)?(?P<host>[^/:]+(?::\d+)?)[:/](?P<path>.+?)(?:\.git)?/?$"
  )
  ```
- Update `GitHubProvider.parse_repo_ref` to:
  1. Strip whitespace and optional scheme (`if "://" in url: url = url.split("://", 1)[1]`).
  2. Match `_REMOTE_RE`.
  3. Split `path.strip("/")` by `"/"` and require `len(parts) == 2` with both parts non-empty; otherwise raise `ValueError(f"Could not parse GitHub repository from remote URL: {remote_url}")`.
  4. Return `RepoRef(raw=remote_url, workspace=workspace, name=name, provider=self.name)`.

### 2. Unit Tests (`tests/scm/test_github_provider.py`)
#### [MODIFY] `tests/scm/test_github_provider.py`
- Add `TestParseRepoRef(unittest.TestCase)` covering:
  - `github.com` HTTPS, HTTPS without `.git`, trailing slash, SCP (`git@github.com:owner/repo.git`), `ssh://`.
  - GitHub Enterprise (`github.acme.com`) HTTPS, HTTP, SCP (`git@github.acme.com:owner/repo.git`), `ssh://` with port (`ssh://git@github.acme.com:2222/owner/repo.git`), and embedded credentials (`https://user:token@github.acme.com/owner/repo.git`).
  - `ValueError` on empty/whitespace string, single-segment path, 3+ segment path, and malformed URLs.

### 3. Documentation (`docs/scm-multiforge.*`)
#### [MODIFY] `docs/scm-multiforge.md`, `docs/scm-multiforge.pt_br.md`, `docs/scm-multiforge.pt_pt.md`, `docs/scm-multiforge.es_es.md`, `docs/scm-multiforge.fr_fr.md`
- **§1.2 line 61**: Update the table row for GitHub Enterprise (`github.acme.com`) to explain that hosts containing `github` are detected and parsed normally, requiring only `GITHUB_BASE_URL` in `~/.gitpr/.env` for API calls (while arbitrary domains without `github`, e.g., `git.acme.com`, still require `scm.provider: github` in `.gitpr/conf/gitpr.config.yml` + `GITHUB_BASE_URL`).
- **§1.2 lines 65–68**: Remove the `Could not parse GitHub repository from remote URL: https://github.acme.com/owner/repo.git` line from the example code block, keeping only the unrecognized-host warning.
- **§3 line 104**: Remove the claim that custom GitHub domains fail to parse; document that `GITHUB_BASE_URL` targets the GitHub Enterprise API (e.g., `https://github.acme.com/api/v3`).
- Preserve exact structural parity (`headings`, `table_rows`, `bullets`, `fences`) across all 5 language files.

## Verification Plan

```bash
python -m pytest tests/scm/test_github_provider.py tests/scm/test_contract.py tests/scm/test_factory.py tests/unit/test_docs_translation_parity.py tests/unit/test_scm_multiforge_docs_parity.py -v
```
