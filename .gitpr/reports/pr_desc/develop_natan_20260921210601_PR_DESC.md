# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add embedded secret scanning ruleset to linter
```

---

## 🎯 Summary

Introduces an embedded secret-scanning ruleset in the static linter, closing the gap where hardcoded credentials could reach a commit or PR unnoticed. Until now the local rule catalogue was entirely user-managed: it could be overwritten by the download, rewritten by the `--linter-setup` wizard (losing comments), or extended only through per-machine plugins. A secret gate has to behave identically on every developer machine and in every CI run, so the rules now ship inside the package.

The ruleset is on by default and can be turned off entirely, or trimmed rule by rule, through configuration. Alongside the feature, this change hardens the test suite against local-machine state (language and profile) and adds the first CI workflow, which is what made those drifts visible.

## 🛠️ Technical Changes

- Add `src/security_ruleset.py` with seven rules: AWS Access Key ID, GitHub token, Slack token, Google API key, private key block (all `error`), plus database connection string with credentials and generic credential assignment (both `warning`).
- Support a `"*"` extension wildcard in `src/linter_engine.py` so rules match files with no suffix and dotfiles (`.env`, `id_rsa`, `credentials`, `Dockerfile`) — the very files secrets leak from.
- Merge the ruleset into `load_linter_rules()` in `src/config.py`, applied after project and plugin rules, honoring the disabled-rules list.
- Expose two new settings in `src/config_schema.py` and `DEFAULT_CONFIG`: `GITPR_LINTER_SECURITY` (default `true`) and `GITPR_LINTER_SECURITY_DISABLED_RULES` (default empty, `;`-separated).
- Ensure rule messages never interpolate the matched value — alerts carry only `{file_name}` and `{line_number}`, keeping secrets out of console output, Markdown reports and PR bodies.
- Translate all new keys in the six language catalogues (`pt_br`, `pt_pt`, `es`, `es_es`, `fr`, `fr_fr`).
- Add `tests/test_security_ruleset.py` covering regex compilation, positive/negative detection, placeholder filtering, level routing, wildcard application, merge behavior and translation completeness.
- Make `tests/conftest.py` hermetic by pinning `GITPR_LANG=en_us` and disabling the ruleset by default, preventing the suite from writing into the developer's real `~/.gitpr/.env` and from rendering translated assertions.
- Fix `src/i18n.py` to create the profile directory before persisting the detected language, avoiding a crash on first run.
- Add `.github/workflows/tests.yml` running the suite on Python 3.10 (declared floor) and 3.13.
- Stabilize worker-thread-dependent UI tests in `test_config_app.py` and `test_metrics.py` by awaiting `workers.wait_for_complete()` before assertions.

## ⚠️ Impact/Warnings

- **Behavior change:** the AI SDK request timeout default (`GITPR_AI_TIMEOUT`) drops from **600s to 180s**. Long-running generations on slow models may now time out where they previously completed. Set the variable explicitly to retain the old value.
- **New environment variables:** `GITPR_LINTER_SECURITY` and `GITPR_LINTER_SECURITY_DISABLED_RULES`. Secret scanning is **enabled by default**, so existing users will start seeing new blocking alerts on diffs containing credential-like patterns; the two `warning` rules report without blocking the commit.
- **CI dependency:** the new workflow requires the `~/.gitpr/.env` profile to exist; it is created explicitly during the job.
- No database migrations. No public API changes.

close #183

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_1_warning-yellow)](https://gitpr.natanfiuza.dev.br/)