# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: honor release skill language declaration
```

---

## 🎯 Summary

The release skill (`.gitpr.release.md`) can now declare the language of the generated section through a YAML front matter block (`language: pt_br`). Previously the release notes always followed the interface language, so a team working in English but publishing a Portuguese changelog had no per-repository control over the output. This change lets the repository own that decision, applying it both to the rendered headings/labels and to the language requested from the AI prompt — even when the AI summary is disabled.

## 🛠️ Technical Changes

- Add `src/skill_frontmatter.py` with `split_front_matter()`, a defensive parser that only treats a leading bare `---` fence (with optional BOM, CRLF supported) plus a matching closing fence as front matter, and never raises on malformed or non-mapping YAML.
- Add `_SKILL_LANGUAGES` allowlist (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`), preventing `set_lang()` from attempting to download a dictionary that does not exist.
- Add `_load_release_skill()` to read the skill once and return `(body, language)`, stripping the front matter so the AI receives only the persona body.
- Add `_declared_language()` context manager that switches i18n for the duration of the release generation and restores `CURRENT_LANG`/`TRANSLATIONS` directly, avoiding a second translation lookup on exit.
- Make `_language_for_prompt()` import `CURRENT_LANG` lazily (a top-level import would pin the value read at module load) and normalize `-` to `_` in language codes.
- Move skill loading into `generate_release_notes()` so the declared language also drives the headings when `ai_summary` is off; `_generate_summary()` now receives the persona body via a new `system_instruction` parameter.
- Add unit tests for the front matter splitter and for the engine (prompt language, heading translation, front matter stripping, fallback on malformed/unsupported declarations, i18n restoration, and distinct cache keys per language); the test base class now patches `get_skill_context` so unit tests never read the repository's real skill file.

## ⚠️ Impact/Warnings

- **Behavior change:** a release skill that starts with a valid `---` block now has that block removed from the AI system instruction. Skills without front matter behave exactly as before.
- **No database, environment variable, or dependency changes.** `PyYAML`, already used by the project, backs the new module.
- Unsupported or malformed `language:` values are silently ignored and fall back to the interface language — no error is surfaced to the user.
- Language switching is scoped: the process-wide i18n state is restored after generation, so callers are unaffected.

close #291

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)