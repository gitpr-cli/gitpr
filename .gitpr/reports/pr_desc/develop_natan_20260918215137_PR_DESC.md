# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add gitpr demo guided tour over recorded examples
```

---

## 🎯 Summary

Adds `gitpr demo`, an interactive guided tour that shows what GitPR does — commit message, code review and pull request description — without requiring an API key, a Git repository or a network connection.

The goal is to answer "what does this tool do?" at the one moment it matters most: the first run, before the user has committed a provider key. The tour replays a recorded example through the *real* generation pipeline, so what is shown is what the tool actually produces, while every outward effect (prompt cache, metrics, disk writes, network, API-key lookups) is neutralized.

## 🛠️ Technical Changes

- Add `src/demo/` package:
  - `demo_runner.py` — UI-free `DemoState` state machine (advance/back/completed tracking) plus the plain-text front end (`--no-tui`) for CI and recordings.
  - `fake_ai_provider.py` — `FakeAIProvider` mirrors `src.ai_providers.call_ai_model` argument-for-argument; `demo_pipeline()` patches `src.core` and `src.metrics` so the production pipeline (prompt assembly, diff chunking, response parsing) runs untouched and only the answer source is swapped.
  - `scenarios/` — registry with two shipped examples (a Laravel profile-update bug and an Express cross-tenant IDOR), each localized in `en`, `pt_br`, `pt_pt`, `es_es` and `fr_fr`, with English fallback. Stored as Python modules, not JSON, so they ship inside the wheel.
- Add `src/ui/demo/` Textual front end (single-screen, matching existing apps) with a help modal; the diff is fenced as ```` ```diff ```` and the commit message rendered as plain text.
- Add the `gitpr demo` CLI command with `--scenario`, `--lang` and `--no-tui` options; `--lang` is applied inside the subcommand since the root callback returns before its handler.
- Add a first-run hint in `src/config.py` pointing the user to `gitpr demo`.
- Add 30+ new i18n keys to all six language dictionaries and bump `__lang_version__` to `v0.0.29`.
- Add `tests/demo/` suite: state machine and artifact generation, scenario/diff integrity (hunk arithmetic), TUI navigation, text-mode output, fake-provider contract, and isolation guards (network ban, no repository, no configuration, nothing written to `~/.gitpr`).
- Add demo metrics export fixtures and documentation (`docs/demo.md` and localized variants, README updates).

## ⚠️ Impact/Warnings

- **No database or environment-variable changes.** The demo reads no API keys and no `.env`; `DEFAULT_AI_PROVIDER` and any configured key are ignored by design.
- **No new dependencies.** The Textual UI reuses the existing stack.
- **i18n:** the language dictionary version moves to `v0.0.29`; clients will pick up the new keys on their next sync. Missing translations fall back to English.
- **Isolation guarantee:** the tour must not touch the user's `~/.gitpr` (cache, metrics, logs) or the network — enforced by `tests/demo/conftest.py`. A regression here would silently poison a real cache with demo content.
- Documentation files (READMEs, `docs/demo.*`) are updated in this same change and are not part of the code diff shown.


close #177