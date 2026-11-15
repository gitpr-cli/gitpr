# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
test: drop english-only exemption for github issue prompt guide
```

---

## 🎯 Summary

The documentation translation parity test kept a hardcoded exemption list (`_EN_ONLY`) marking `github-issue-prompt-com-gh` as intentionally English-only. Since that how-to now ships localized variants like the rest of the doc set, the exemption is obsolete and was actively hiding missing translations. Removing it makes the parity guard uniform: any new or modified document must exist in `pt_br`, `pt_pt`, `es_es`, and `fr_fr`, or the test fails.

This closes the gap where a single document could silently drift out of the i18n contract without any test signal.

## 🛠️ Technical Changes

- Emptied the `_EN_ONLY` mapping in `tests/unit/test_docs_translation_parity.py`, removing the `github-issue-prompt-com-gh` exemption and its inline justification comment.
- Kept the `_EN_ONLY` data structure in place so future intentional English-only documents can still be declared explicitly, preserving an escape hatch without ad-hoc logic.
- The parity check now enforces all four language variants (`_LANGS`) for every document in the tracked scope, with no special cases.

## ⚠️ Impact/Warnings

- No runtime, database, environment variable, or dependency changes; test-only modification.
- The parity test is now stricter: any documentation file still lacking a translation in one of the four locales will fail CI. The corresponding localized versions must already be present before this lands.
- Contributors must keep the exemption list empty (or add a documented entry) when introducing docs that are intentionally English-only, otherwise the suite breaks.

close #328

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)