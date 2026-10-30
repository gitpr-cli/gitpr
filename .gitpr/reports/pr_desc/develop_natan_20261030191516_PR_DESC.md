# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
chore(i18n): sync es/fr locales and localize CLI help
```

---

## 🎯 Summary

This PR closes the remaining gaps in GitPR's internationalization. Spanish and French dictionaries were synced with features shipped recently (policy packs, baseline management, Mentor mode, local risk scoring, MCP server, PR target base branch, project configuration and chat shortcuts), and the last hardcoded English strings on the support surface — the MCP server's `argparse` help and the chat help screen — are now routed through `__()` so they can be translated at runtime.

The dictionary version is bumped so clients know the `pt_br`/`pt_pt` resources changed and must be re-synced, and a new CI guard prevents future regressions where a key silently keeps its English value. The goal is consistent localized UX and a test-enforced translation contract, not new behavior.

## 🛠️ Technical Changes

- Update `langs/es.json` with new Spanish entries for policy packs, baseline management, Mentor mode, local risk scoring, MCP server, PR target base branch, project configuration, chat shortcuts and risk/debt reporting; translate remaining English strings and normalize terminology.
- Update `langs/fr.json` and `langs/fr_fr.json` (identical content): restore alphabetical ordering by re-inserting the previously appended unsorted block into its correct position, add new keys (policy packs, baseline, `gitpr risk`, Junior Mentor, base-branch resolution, project config, MCP tool catalog, unified `check` pipeline, keyboard shortcuts) and localize strings that were still in English.
- Apply minor terminology fixes (e.g. `=== AI PR HISTORY ===` → `HISTORIQUE DU PR PAR IA`, singular `⚡ Performance`, translated `🧪 Covered Scenarios:`).
- Wrap all `argparse` help strings in `src/mcp_server.py` (`description`, `--list-tools`, `--install-mcp`, `--tool`, `--tool-args`) with `__()`.
- Refactor `ChatHelpScreen` in `src/ui/chat_app.py` to compose its content line-by-line through `__()` instead of static literals, and correct shortcut labels to `Ctrl+Shift+S` and `Ctrl+Shift+E`.
- Bump `__lang_version__` in `src/updater.py` from `v0.0.36` to `v0.0.37` to signal the expanded `pt_br`/`pt_pt` dictionaries.
- Strengthen `tests/test_i18n.py`: allowlist the `Based on the following commit timeline…` AI prompt fragment, introduce `ALLOWED_IDENTITY_TERMS` (technical acronyms, universal TUI categories and legitimate cognates such as Downloads, Cycle and Suppression) and add `test_all_identity_keys_are_allowlisted`, which fails whenever a key whose value equals English is not an AI prompt, a state marker or an explicitly allowed term.

## ⚠️ Impact/Warnings

- **No database, dependency or environment-variable changes.**
- **Dictionary version bump:** `__lang_version__` moves to `v0.0.37`; clients must re-sync `pt_br`/`pt_pt` resources, otherwise translations may lag behind.
- **New CI gate:** `test_all_identity_keys_are_allowlisted` will fail future PRs that introduce untranslated identity values without adding them to the allowlist — expected behavior, but it can block builds until updated.
- **Residual translation risk:** a missing or mismatched placeholder would surface as an untranslated English fallback rather than a functional failure; no runtime or business-logic impact is expected.

close #236

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)