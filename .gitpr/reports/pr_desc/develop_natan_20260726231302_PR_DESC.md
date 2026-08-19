# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: implement local offline metrics and telemetry system
```

---

## 🎯 Summary

This PR adds a fully local, offline telemetry system to GitPR, enabling team analytics without external services. Every CLI command, AI call, linter run, and git hook now emits anonymous usage events, stored in `~/.gitpr/metrics/`. A new `--metrics` flag with sub‑options (`--export`, `--purge`, `--dashboard`) allows teams to consolidate data into CSV/JSON reports and explore usage patterns through an interactive TUI dashboard. Three additional git hooks (`post‑checkout`, `pre‑push`, `post‑merge`) collect behavioral telemetry. The thinking‑words spinners also gain 62 new phrases across all languages, and all internal comments/docblocks are now in English.

## 🛠️ Technical Changes
- New telemetry engine in `src/metrics.py` with `log_command_metric()`, `export_metrics()`, `purge_metrics()`, and summary functions
- New TUI dashboard (`src/ui/metrics_app.py`) built with Textual, showing an events table and aggregate stats
- New CLI flags: `--metrics`, `--export`, `--purge`, `--dashboard`, `--hook-event` (hidden) with handlers in `main.py`
- Updated `src/core.py`: fire‑and‑forget metric calls in all AI‑powered command paths (single‑chunk and map‑reduce), lazy imports to avoid circular dependencies
- Updated `src/core.py`: added `post‑checkout`, `pre‑push`, `post‑merge` hook templates to `install_git_hooks()`
- Updated `src/ai_providers.py`: injection of `_telemetry_meta` with token usage into AI responses
- Updated `src/cache.py`: author info capture and `meta_raw` storage in cache files
- Updated `src/main.py`: linter handler now logs error/warning metrics
- New hook scripts: `post-checkout-template.sh`, `pre-push-template.sh`, `post-merge-template.sh`
- Comprehensive i18n: +83 translation keys per language for metrics, dashboard, and new messages
- Documentation: new `docs/metricas-telemetria.md` in 5 languages, updated READMEs in all 5 languages with links
- Version bump: `0.0.29` → `0.0.30`, language pack version `v0.0.7` → `v0.0.8`

## ⚠️ Impact/Warnings
- **No external dependencies** – all telemetry data stays in `~/.gitpr/metrics/` and is never sent off‑machine
- **No environment variable changes** – the system uses existing configuration
- **No database changes** – data is stored as flat JSON files
- **Opt‑in git hooks** – the three new hooks are only installed when running `gitpr --installhooks`
- **Privacy** – event payloads contain only command/usage metadata; no file contents, diffs, or sensitive data are recorded
- **Performance** – all metric writes run in daemon threads (fire‑and‑forget), adding zero perceptible latency to CLI commands

close #67