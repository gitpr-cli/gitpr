# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
docs: document scm read-only .env fallback and assert parity
```

---

## 🎯 Summary

The SCM multiforge documentation now describes the read-only/ephemeral credential fallback path introduced by the per-repo SCM provisioning migration, and the test suite enforces that this behavior stays documented across every localized guide and the architectural decision record. Without this, operators could assume credentials are always persisted to disk and be surprised when a read-only CI/container environment silently falls back to in-memory environment variables.

## 🛠️ Technical Changes

- Extend `test_scm_multiforge_files_exist_and_have_migration_note_section` in `tests/unit/test_scm_multiforge_docs_parity.py` to require `persisted=False` and `os.environ` in section 3.1 of each `docs/scm-multiforge*.md` file, guaranteeing the read-only/ephemeral fallback is documented in all locale variants.
- Extend `test_adr_0020_exists_and_references_docs_and_adr_016` to assert ADR-0020 mentions `persisted=False`, `os.environ`, and `PermissionError`, keeping the decision record aligned with the fallback contract.
- Update the SCM multiforge guides (`docs/scm-multiforge.md` and the `es_es`, `fr_fr`, `pt_br`, `pt_pt` translations) to describe the read-only provisioning path and the in-memory fallback when the credentials file cannot be written.
- Update `docs/adr/0020-per-repo-scm-provisioning-migration.md` to capture the fallback semantics and the `PermissionError` handling rationale.
- Refresh supporting planning/report artifacts (plans, surveys, walkthroughs, PR description draft) to reflect the Etapa 5 read-only migration.

## ⚠️ Impact/Warnings

- **No runtime behavior change:** this diff is limited to documentation and documentation-parity tests; production code paths are untouched.
- **No database, environment variable, or dependency changes.**
- **Documentation contract is now enforced:** contributors editing `docs/scm-multiforge*.md` or ADR-0020 must keep the `persisted=False`, `os.environ`, and `PermissionError` references, otherwise the unit test suite will fail.
- **Translation parity required:** any future wording change to the fallback section must be applied to all five locale files simultaneously.

close #330

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)