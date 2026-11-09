# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
docs: reference unified check migration guide in action yml
```

---

## 🎯 Summary

Guides users through the transition from legacy text-file outputs (`*_PR_FULLREVIEW.txt`) to the unified `gitpr check` pipeline, which now produces SARIF 2.1.0, JSON, or JUnit XML artifacts. This change surfaces the migration path directly in `action.yml` and locks it down with a documentation-parity test to prevent regressions.

## 🛠️ Technical Changes

- Added a header migration note to `action.yml` documenting the switch to the `gitpr check` pipeline and linking to the migration guide (`https://gitpr.natanfiuza.dev.br/docs/check-ci#7-migration-guide`).
- Added `test_action_yml_and_adr_0011_reference_migration_guide` in `tests/unit/test_check_ci_docs_parity.py` to enforce that ADR-0011 exists and references `action.yml`, `gitpr check`, `--linter`, `--fullreview`, `SARIF`, and `docs/check-ci.md`.
- Extended the same parity test to assert `action.yml` mentions `gitpr check` and `docs/check-ci`.

## ⚠️ Impact/Warnings

- No runtime behavior change: `action.yml` modification is limited to comments.
- Documentation-only and test-only change; no database, environment variable, or dependency changes.
- Consumers using legacy `*_PR_FULLREVIEW.txt` outputs must migrate to the new SARIF/JSON/JUnit artifacts following the guide.

close #300

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)