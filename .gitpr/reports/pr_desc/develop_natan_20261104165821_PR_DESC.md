# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
docs: add issue-autoclose docs and update help links
```

---

## 🎯 Summary

Users invoking contextual help for `--close-issue` and `--no-close-issue` were being pointed to the generic TUI help page, which did not cover automatic issue closure in depth. This change introduces dedicated `issue-autoclose` documentation across all supported languages and updates the CLI help links and tests to reference the correct page. The goal is to improve discoverability, keep documentation aligned with the feature set, and ensure localized content remains consistent.

## 🛠️ Technical Changes

- Add dedicated `issue-autoclose` documentation in English, Portuguese (Brazil and Portugal), Spanish, and French.
- Update `HELP_MAP` entries for `close_issue` and `no_close_issue` in `src/main.py` to point to `docs/issue-autoclose.md`.
- Update `test_contextual_help_flag_close_issue` assertions in `tests/test_cli_help.py` to expect the new documentation path.
- Refresh README files and related documentation/report artifacts to reference the new issue-autoclose docs.
- Preserve existing localized help titles while correcting their destination URLs.

## ⚠️ Impact/Warnings

- No database, environment variable, or dependency changes.
- CLI contextual help output now references `docs/issue-autoclose`; ensure the new documentation files are included in packaging and published deployments to avoid broken links.
- Test expectations were updated to match the new documentation path, so downstream references to the old `issue-tui-help` URL for these flags should be reviewed.

close #261

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)