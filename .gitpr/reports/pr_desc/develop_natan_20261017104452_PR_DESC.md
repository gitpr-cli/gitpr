# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: strip corrupted skill artifact from pr prompt
```

---

## 🎯 Summary

A stray JSON fragment (`".gitpr.commit.md": "gitpr.commit.md",`) was accidentally pasted into the required-structure rule of the `pt_br` PR skill template. Because a skill file is a prompt, the model read that fragment as mandated PR content and echoed it into every generated `pr_description`. Fixing the template alone was not enough: skill downloads never overwrite an existing `.gitpr/skill/` file, so installs that already fetched the corrupted version would stay broken. This change sanitizes the prompt at read time and adds an integrity guard so a similar paste cannot reach users again.

## 🛠️ Technical Changes

- `get_skill_context` now strips the known corrupted fragment from PR skill content in memory, leaving the user's file on disk untouched.
- Added the `_CORRUPTED_PR_SKILL_ARTIFACT` constant, documenting the exact pasted fragment and why it is removed on read.
- Sanitization is scoped to `action_type == "pr"`; other actions (e.g. `commit`) return the file verbatim.
- New tests in `tests/test_skill_context.py`: fragment removed from the prompt, file preserved byte-for-byte, other actions unaffected.
- New `tests/test_skill_templates.py`: parametrized scan of every shipped `.md`/`.yml` template for embedded skill-file references, preventing regressions at the source.
- Corrected `templates/gitpr.pr.pt_br.md` so fresh downloads are clean.

## ⚠️ Impact/Warnings

- No database, environment variable, or dependency changes.
- Behavior change: for the `pr` action, the prompt may differ from the on-disk skill file when the corrupted fragment is present — intentional and documented in code.
- Existing installations are healed at read time; users do not need to delete `.gitpr/skill/` or re-download.
- The template guard is regex-based; future templates must not use `.gitpr.<name>.md":` as a key pattern, even in illustrative JSON.

close #213

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)