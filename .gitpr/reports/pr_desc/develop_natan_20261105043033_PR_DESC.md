# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
test: add docs parity checks for gitpr check migration notes
```

---

## 🎯 Summary

This change locks in the documentation contract for the `gitpr check` command migration. As the CI check action contract evolves (from the legacy `action.yml`-based flow toward the new CLI flags `--linter` and `--fullreview`, with SARIF output), the documentation was updated across all supported languages. Without automated verification, these localized docs silently drift apart — sections get dropped, translation variants fall behind, and the migration guidance disappears. These new unit tests act as a guardrail ensuring all language variants stay structurally aligned and that the migration notes remain discoverable.

## 🛠️ Technical Changes

- Add `tests/unit/test_check_ci_docs_parity.py` to enforce documentation parity for the `gitpr check` command.
- Assert existence of all 5 language variants: `docs/check-ci.md`, `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`.
- Verify each variant contains all 7 required sections (`## 1.` through `## 7.`), preventing structural drift between translations.
- Validate that section 7 (migration guide) references the key contract terms: `action.yml`, `--linter`, `--fullreview`, `gitpr check`, and `SARIF`.
- Add `test_context_md_defines_legacy_ci_action_contract` to ensure `CONTEXT.md` documents the **Legacy CI action contract** domain concept, referencing `action.yml` and `CI Check`.

## ⚠️ Impact/Warnings

- **No runtime impact**: changes are test-only and do not affect production behavior.
- **Contributor impact**: future documentation edits that remove sections, drop a language variant, or omit the migration guidance will fail CI. Update the docs and the corresponding translation variants together.
- **No database, environment variable, or dependency changes**.
- The tests assume a fixed repository layout (`repo_root` resolved three levels up from the test file); relocating the test file requires adjusting that path resolution.

close #267

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)