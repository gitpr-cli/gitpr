# Implementation Plan — Unrecognised self-hosted forge host

- **Branch:** `develop_natan`
- **Date:** 2026-11-14
- **Task:** `self_hosted_forge_detection`

## Context

Per-repository forge resolution matches a forge name as a case-insensitive substring of
the whole `origin` URL. A self-managed host such as `git.acme.com` names no forge, so the
repository silently resolves to the `github` default (`src/scm_settings.py`) and the
publish fails later with `Could not parse GitHub repository from remote URL: …`, because
`github_provider.parse_repo_ref` requires the literal `github.com`. Nothing documented
the symptom or warned the user before the failure.

A prerequisite surfaced while designing the warning: `detect_provider_from_remote(url,
default=None)` returned `None` even for `github.com`, because the `default is None`
early return preceded the `"github" in url` check. That made the wizard label every
GitHub repository "not recognised" and commit a spurious `scm.provider: github`, and it
would have made any `source == default` warning a false alarm on every GitHub repo.

## Steps

1. **Detector** — `src/infrastructure/scm/factory.py`: move the `"github" in url` test
   above `if default is None: return None`; update the docstring to say `github.com` is a
   recognised forge even when the caller asks to distinguish an unknown host.
2. **Warning** — `src/scm_settings.py`: add `_default_provider_warning()` next to
   `_ignored_provider_warning`, and append it in `resolve_scm_settings` when `remote` is
   present and `choice.source == SOURCE_DEFAULT` (the absent-remote case has its own
   error at the call sites).
3. **i18n** — add the new key to the 6 files in `langs/` with real translations
   (no identity keys), in the same ordered position.
4. **Docs** — add `### 1.2` to `docs/scm-multiforge.md` and its four translations:
   one intro paragraph (name heuristic, whole-URL matching, fallback and warning), a
   three-row symptom/cause/fix table, one repo-vs-machine paragraph, and a `text` block
   quoting the warning and the parse error. Add a short caveat to the `GITHUB_BASE_URL`
   row of §3 pointing to §1.2.
5. **Tests** — factory: `github.com` (https and ssh) with `default=None` returns
   `"github"`. Settings: exactly one warning for an unknown remote; none without a
   remote, on `github.com`, or with a project override. Wizard: one test with the real
   detector proving `github.com` shows "Detected forge: GitHub" and writes no override.
6. **Design records** — `CONTEXT.md` (Provider detection, Default fallback),
   `docs/plans/glossary-scm-multiforge.md` (corrected detector row),
   `docs/plans/ADR-016-per-provider-scm-settings.md` (per-run warning),
   `CLAUDE.md` (Multi-Forge SCM clause).
7. **Artifacts** — plansfacts, surveyfacts, this plan, completion report.

## Structural contract for §1.2 (per file)

1 `###` heading, 5 table lines, 0 bullets, 2 fences. `scm-multiforge` is not in
`_PARITY_EXCEPTIONS`, so any deviation breaks `test_docs_translation_parity`.

## Verification

```bash
python -m pytest tests/scm/test_factory.py tests/scm/test_scm_settings.py tests/scm/test_init_wizard.py -q
python -m pytest tests/test_i18n.py tests/unit/test_docs_translation_parity.py tests/unit/test_scm_multiforge_docs_parity.py tests/test_doc_links.py -q
python -m pytest tests -q
```

## Accepted limits

- The warning repeats on every publication command until `--init` records the override.
- GitHub Enterprise hosts still fail to parse; now documented as a known limitation.
- Whole-URL matching still misreads a path that names another forge; documented.
