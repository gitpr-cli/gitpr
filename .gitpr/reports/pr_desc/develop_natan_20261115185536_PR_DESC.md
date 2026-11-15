# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat(vscode): add pt-PT l10n and claude-code editor option
```

---

## 🎯 Summary

Adds European Portuguese (pt-PT) localization to the VS Code extension and fixes an inconsistency in the "unknown editor" error message: the CLI already supports `claude-code`, but the message did not advertise it. pt-PT users now get the commands, settings, and runtime notifications in their own locale, and anyone who mistypes or uses `gitpr --install claude-code` receives accurate guidance instead of a list that omits a valid option. Documentation (plans, reports, walkthroughs, and surveys) was produced for the Etapa 7 install error and the VS Code pt-PT localization work.

## 🛠️ Technical Changes

- Added `extensions/vscode/l10n/bundle.l10n.pt-pt.json` with pt-PT translations for runtime strings (commit generation, code review, PR draft/publish flow, authentication prompts, and GitPR Check notifications).
- Added `extensions/vscode/package.nls.pt-pt.json` translating the extension `displayName`, `description`, command titles, and configuration descriptions (`mcpCommand`, `mcpArgs`, `provider`, `checkUseAI`).
- Updated the unknown-editor message in `src/mcp_server.py` (`_install_for_editor`) to list `vscode, cursor, claude-code, claude, zed, auto`.
- Propagated the same option list to the translated strings in `langs/es.json`, `langs/es_es.json`, `langs/fr.json`, `langs/fr_fr.json`, `langs/pt_br.json`, and `langs/pt_pt.json` so localized errors stay in sync with the source message.
- Added `test_install_for_unknown_editor_lists_all_valid_options` in `tests/test_mcp_server.py`, asserting the error is returned as a failure and that every valid option (`vscode`, `cursor`, `claude-code`, `claude`, `zed`, `auto`) appears in the message.
- Added supporting documentation for the Etapa 7 install error and the VS Code pt-PT localization, including plans, facts surveys, reports, walkthroughs, and the PR description report.

## ⚠️ Impact/Warnings

- **No breaking API changes.** No database migrations, environment variables, or new dependencies were introduced.
- **User-facing message change:** the unknown-editor error text now includes `claude-code`. Any external tests, snapshots, or documentation quoting the previous string must be updated.
- **Packaging check:** verify the VS Code extension build includes the new `l10n/bundle.l10n.pt-pt.json` and `package.nls.pt-pt.json` files so pt-PT is actually activated at runtime.
- **Translation consistency:** the locale files were edited only for the affected key; a broader re-translation pass was intentionally not performed.
- **Documentation-only files:** the listed docs under `docs/` and `.gitpr/reports/` contain content excluded from the diff and carry no runtime impact.

close #334

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)