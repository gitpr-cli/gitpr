# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: recognise GitHub remotes and warn on unknown forge fallback
```

---

## 🎯 Summary

Self-hosted forge detection introduced a regression: when a caller passed `default=None` to distinguish "recognised" from "unrecognised", a plain `github.com` remote was treated as unknown because the `default is None` early return ran before the GitHub check. Every GitHub repository would then be flagged as an unrecognised host, prompting users to pick a forge and writing a spurious `scm.provider` override.

This fixes the detection order and, in parallel, makes the silent GitHub fallback explicit: when a remote exists but names no known forge, GitPR now warns the user that it is defaulting to GitHub and points them to `gitpr --init`.

## 🛠️ Technical Changes

- Reorder `detect_provider_from_remote` so the `github` match is evaluated before the `default=None` return, ensuring `github.com` (HTTPS and SSH forms) is reported as a recognised forge.
- Add `_default_provider_warning()` and emit it from `resolve_scm_settings` when a remote is present but the resolved provider comes from the default source.
- Keep the missing-remote case silent, since call sites already raise their own error for an absent remote.
- Add the new warning string to all supported locales (`es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt`).
- Add regression tests: GitHub detection with `default=None`, the init wizard recognising a real `github.com` remote without writing an override, and the warning behaviour (unknown remote warns, missing remote is silent, GitHub remote is silent, project override silences the warning).

## ⚠️ Impact/Warnings

- **Behaviour change:** users with a remote that names no known forge will now see an additional warning on SCM setting resolution. No functional break, but messaging output changes.
- **No database, environment variable, or dependency changes.**
- **Translation requirement:** new i18n key added; any future locale must include it.

close #323

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)