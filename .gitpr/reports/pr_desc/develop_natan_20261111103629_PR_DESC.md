# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
docs: document GITPR_SKIP_UPDATE_CHECK migration and add parity tests
```

---

## 🎯 Summary

The auto-update switch `GITPR_SKIP_UPDATE_CHECK` moved to strict boolean evaluation, which is a breaking behavioral change: values that were previously treated as "truthy" by loose parsing (e.g. arbitrary non-empty strings) are no longer accepted the same way. Users relying on the old lenient parsing could silently lose the ability to skip the update check.

This change documents the migration path across every supported language and locks that documentation in place with automated parity tests, so the guidance cannot drift or be dropped in one locale while the others are updated.

## 🛠️ Technical Changes

- Add `tests/unit/test_auto_update_docs_parity.py` verifying all 5 `docs/auto-update.*` variants (en, pt_br, pt_pt, es_es, fr_fr) exist and contain:
  - a `> [!WARNING]` callout,
  - explicit mention of `GITPR_SKIP_UPDATE_CHECK`,
  - the accepted truthy/falsey literals (`1`, `true`, `false`, `0`),
  - a cross-reference to ADR-0021.
- Add parity assertions for all 5 `docs/tutorial/install-from-source.*` variants, ensuring the Section 5 migration note, warning callout, env var, and ADR link are present in each locale.
- Assert `docs/adr/0021-strict-boolean-update-check-migration.md` exists and references `GITPR_SKIP_UPDATE_CHECK`, the `_SKIP_TRUTHY_VALUES` implementation constant, both documentation entry points, and ADR-0014 (canonical package version SSOT).
- Assert `CONTEXT.md` defines the domain term **Update check switch** and ties it to `GITPR_SKIP_UPDATE_CHECK`.
- Update the ADR, both documentation families (all locales), and the survey/plan/report artifacts that back this work.

## ⚠️ Impact/Warnings

- **Environment variable behavior:** `GITPR_SKIP_UPDATE_CHECK` now uses strict boolean parsing. Previously accepted loose/truthy strings may no longer disable the update check — users must migrate to `1`/`true` or `0`/`false`. This is documented in ADR-0021 and in the warning callouts added to all auto-update and install-from-source docs.
- **No database or dependency changes.**
- **Test coupling:** the new parity tests assert on exact documentation strings (warning markers, ADR filename, env var name). Future doc rewrites in any single locale will fail CI until all locales are kept in sync — intentional, but worth noting for contributors.

close #315

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)