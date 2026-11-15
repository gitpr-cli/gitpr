# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
test: enforce docs parity for project config seed opt-out
```

---

## 🎯 Summary

ADR-0019 introduced a runtime project configuration seed with an opt-out switch (`GITPR_SKIP_PROJECT_CONFIG_SEED`), but the behavior was only described in the reference English documentation. Translations drifted (the `pull-request-publication` parity exception was masking 54 vs 47 headings and 99 vs 91 table rows), so non-English users could not discover the new section or the opt-out.

This change finishes the documentation rollout in all five language variants and replaces the manual parity exception with executable tests, so the ADR-0019 contract cannot silently regress again.

## 🛠️ Technical Changes

- Added `tests/unit/test_project_config_seed_docs.py` covering four contract points:
  - Presence of section `9.4`, a `[!IMPORTANT]` callout, and `GITPR_SKIP_PROJECT_CONFIG_SEED` in all five `pull-request-publication` variants.
  - Existence of the same env var in all five `config-tui` variants, plus a validated cross-document anchor link to section `9.4` (slug computed with a GitHub-style `_github_heading_slug` helper, so renamed headings break the test instead of producing dead links).
  - Existence of `docs/adr/0019-project-configuration-seed-segregation.md` and its cross-references to `pull-request-publication.md` and `config-tui.md`.
  - Domain term definitions (`Runtime project configuration seed`, `Project configuration seed opt-out`) in `CONTEXT.md`.
- Removed the `pull-request-publication` entry from `_PARITY_EXCEPTIONS` in `tests/unit/test_docs_translation_parity.py`, since parity is now real rather than suppressed.
- Updated translations: `docs/config-tui.{pt_br,pt_pt,es_es,fr_fr}.md` and `docs/pull-request-publication.{pt_br,pt_pt,es_es,fr_fr}.md`.
- Documented the decision in `docs/adr/0019-project-configuration-seed-segregation.md` and propagated terminology to `CLAUDE.md`, `GEMINI.md`, `CHANGELOG.md`, plus status/plan/report artifacts under `docs/`.

## ⚠️ Impact/Warnings

- **Environment variable:** `GITPR_SKIP_PROJECT_CONFIG_SEED` is now documented as the supported opt-out. No runtime code changes are included here — this PR is documentation and test coverage only.
- **CI behavior change:** removing the parity exception means translation drift in `pull-request-publication` will now fail the build. Intentional, but it raises the maintenance bar for future doc edits.
- **Test coupling:** the new tests resolve paths relative to the repository root via `Path(__file__).resolve().parent.parent.parent` and read files from disk, so they must run from a full checkout (they will fail in an isolated package install or partial source distribution).
- **No database, dependency, or API changes.**

close #326

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)