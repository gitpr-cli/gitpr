# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add versioned policy packs system with CLI and tests
```

---

## 🎯 Summary

Introduces **Policy Packs** to GitPR: versioned (YAML) packs that standardize skills, linter rules, rule severity, risk scoring, and PR/commit conventions for a repository. Today each repository configures these concerns ad hoc, which makes behavior hard to reproduce, share, and lock across environments. Policy Packs make that configuration declarative, versioned, composable, and reproducible — while remaining fully opt-in so existing behavior is preserved when no pack is active.

## 🛠️ Technical Changes

- **Domain layer** (`src/domain/policy/*`): types, closed-schema manifest parsing, compatibility/credential checks, SHA-256 checksum, and a graph resolver with precedence and composition.
- **Infrastructure layer** (`src/infrastructure/policy/*`): local repository with three lookup origins (`.gitpr/policies`, `~/.gitpr/policies`, bundled package) plus a pack loader.
- **Use cases**: `activate_policy_pack`, `install_policy_pack`, `resolve_effective_policy`, and `validate_policy_pack`.
- **Bundled packs**: four built-in packs (`laravel-quality`, `node-quality`, `php-security`, `vue-quality`) with `policy.yml` and `linter.yml`.
- **Consumption integration**: `calculate_risk` (applies policy over base config), `config.load_linter_rules` (layered rule merge + severity overrides), `core.get_skill_context` (injects pack context), and PR cache-key (`cache_scope()`).
- **Risk rules**: support for `test_patterns` in `risk_rules` and `test_matcher`.
- **CLI**: new `gitpr policy {list,validate,show,use,off,install,init}` commands with confirmation (`--yes`/`--force`), plus stack detection and policy resolution in `main.py`.
- **Global config**: new `GITPR_POLICY_ENABLED` and `GITPR_POLICY_CONTEXT_MAX_CHARACTERS` exposed in `config.py`/`config_schema.py`.
- **Internationalization**: ~130 new keys across `es/es_es/fr/fr_fr/pt_br/pt_pt` for error messages, CLI, and policy context.
- **Packaging**: added `packaging` dependency for SemVer/PEP 440 parsing and bundled pack distribution via `package-data`.
- **Tests**: unit tests for the resolver/composition (`test_policy_resolver.py`), integration tests for real-repo effects (`test_policy_effect_on_review_linter_risk.py`), CLI coverage (`test_policy_cli.py`), and an autouse guard blocking non-loopback network access in integration fixtures.

## ⚠️ Impact/Warnings

- **Dependencies**: new `packaging` dependency declared in both `Pipfile` and `pyproject.toml`.
- **Environment variables**: two new optional globals — `GITPR_POLICY_ENABLED` and `GITPR_POLICY_CONTEXT_MAX_CHARACTERS`. Defaults preserve current behavior (policy disabled).
- **Packaging**: bundled packs are shipped via `package-data`; build/publish steps must include them.
- **Backward compatibility**: with no active pack, behavior is preserved (covered by test §12.10). Activating a pack changes the prompt cache-key scope and may alter linter/risk output.
- **No database changes.**

close #202

---

[![GitPR](https://img.shields.io/badge/GitPR-2_errors_%C2%B7_2_warnings-red)](https://gitpr.natanfiuza.dev.br/)