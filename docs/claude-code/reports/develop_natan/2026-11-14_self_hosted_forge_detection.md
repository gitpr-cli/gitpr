## Completion Report — Unrecognised self-hosted forge host

### What was done

- Documented the symptom of a self-managed forge host whose domain names no forge: a new
  §1.2 in `docs/scm-multiforge.md` and its four translations, plus a caveat on the
  `GITHUB_BASE_URL` row of §3.
- Added a runtime warning in `resolve_scm_settings`: an existing `origin` remote that
  names no forge and resolves to the `github` default now prints a yellow warning on every
  console-facing run until an override is recorded.
- Fixed the detector ordering bug that made `detect_provider_from_remote(url,
  default=None)` report `None` for `github.com` — a recognised forge is now recognised
  even when the caller asks to distinguish an unknown host, so the warning does not
  false-alarm on GitHub and the wizard no longer commits a spurious `scm.provider:
  github`.
- Added the warning key to all six `langs/*.json` files with real translations.
- Added tests for the detector, the resolver warning conditions and a wizard test that
  uses the real detector.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/infrastructure/scm/factory.py` | fix | GitHub check moved above the `default is None` return; docstring updated |
| `src/scm_settings.py` | feat | `_default_provider_warning()` and the conditional append in `resolve_scm_settings` |
| `langs/pt_br.json` | feat | New warning key (PT-BR) |
| `langs/pt_pt.json` | feat | New warning key (PT-PT) |
| `langs/es.json` | feat | New warning key (ES) |
| `langs/es_es.json` | feat | New warning key (ES-ES) |
| `langs/fr.json` | feat | New warning key (FR) |
| `langs/fr_fr.json` | feat | New warning key (FR-FR) |
| `docs/scm-multiforge.md` | docs | §1.2 + `GITHUB_BASE_URL` caveat |
| `docs/scm-multiforge.pt_br.md` | docs | §1.2 + caveat, localized |
| `docs/scm-multiforge.pt_pt.md` | docs | §1.2 + caveat, localized |
| `docs/scm-multiforge.es_es.md` | docs | §1.2 + caveat, localized |
| `docs/scm-multiforge.fr_fr.md` | docs | §1.2 + caveat, localized |
| `tests/scm/test_factory.py` | test | `github.com` recognized with `default=None` (https and ssh) |
| `tests/scm/test_scm_settings.py` | test | Warning on unknown remote; silent without remote, on `github.com`, and with an override |
| `tests/scm/test_init_wizard.py` | test | Real detection: `github.com` shows "Detected forge: GitHub", no override written |
| `CONTEXT.md` | docs | Terms **Provider detection** and **Default fallback** |
| `docs/plans/glossary-scm-multiforge.md` | docs | Corrected `detect_provider_from_remote` row |
| `docs/plans/ADR-016-per-provider-scm-settings.md` | docs | Per-run warning consequence; `github.com` never triggers it |
| `CLAUDE.md` | docs | Multi-Forge SCM clause on detection and the fallback warning |
| `docs/plans/develop_natan/20261114_self_hosted_forge_detection_plansfacts.md` | docs | Session plan |
| `docs/survey/20261114_self_hosted_forge_detection_surveyfacts.md` | docs | Session survey |
| `docs/claude-code/plans/develop_natan/2026-11-14_develop_natan_self_hosted_forge_detection.md` | docs | Implementation plan |

### Impact

- **Functionality:** a self-managed host that names no forge now warns on every
  publication flow before the parse failure, naming `gitpr --init` as the fix. A
  `github.com` remote is recognised by detection, so the wizard neither asks for the forge
  nor records a `scm.provider: github` override. The effective-provider source for a
  `github.com` remote changes from `default` to `remote` in the config TUI label.
- **Performance:** no measurable impact — one string check reordered and one warning
  appended to an existing list.
- **Compatibility:** no API break. GitHub Enterprise hosts (`github.acme.com`) remain
  unsupported because `parse_repo_ref` requires the literal `github.com`; now documented
  in §1.2. Whole-URL matching still lets a path that names another forge win (e.g.
  `github.com/acme/gitlab-mirror` → gitlab); documented as a known limitation.

### Verification

- `python -m pytest tests/scm/test_factory.py tests/scm/test_scm_settings.py tests/scm/test_init_wizard.py -q` → 64 passed, 17 subtests passed.
- `python -m pytest tests/test_i18n.py tests/unit/test_docs_translation_parity.py tests/unit/test_scm_multiforge_docs_parity.py tests/test_doc_links.py -q` → 39 passed.
- `python -m pytest tests -q` → 3466 passed, 3 skipped, 12 warnings, 236 subtests passed (10m34s). The warnings are the pre-existing `DeprecationWarning`s from the `github_api` shim tests.

### Next steps (if applicable)

- GitHub Enterprise support would require `parse_repo_ref` to derive the owner/repo from
  any host and `BASE_URL` to travel with the remote — out of scope for this task.
- Scoping detection to the host component instead of the whole URL would remove the
  `gitlab-mirror` false positive — also out of scope.
