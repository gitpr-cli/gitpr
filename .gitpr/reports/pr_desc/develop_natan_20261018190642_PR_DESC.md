# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: support parsed AI responses in explain and tests commands
```

---

## 🎯 Summary

The AI provider layer (`call_ai_model`) already returns parsed dictionaries, but the explanation and test-generation use cases still assumed raw JSON strings. This mismatch caused silent failures, placeholder output, and stale parsing paths that could break on `None` or unexpected payload types. This change aligns the domain and application layers with the provider contract while keeping backward compatibility for cached or legacy string responses.

Additionally, missing API keys now fail loudly on stderr instead of rendering a fake reviewer guide, and the `--finding` flow for `tests generate` was corrected to read the right candidate attributes. Documentation links for `--explain` and `tests generate` now point to their dedicated guides.

## 🛠️ Technical Changes

- Accept both `dict` and `str` payloads in `parse_explain_payload`, with `_as_text` and `_empty_explanation` helpers to normalize `None` and non-string fields.
- Validate `reviewer_focus_points` entries and coerce `description`, `file_path`, and `related_line` to the expected types.
- Update `generate_pr_explanation` to print a translated error to stderr when no API key is configured and return an empty explanation instead of a misleading placeholder.
- Harden `generate_test_file` parsing: handle parsed dict responses, coerce `content`, `covered_scenarios`, and `warnings` safely, and return a warning-only result for unsupported response types.
- Rename the CLI option parameter `explain_flag` to `explain` for consistency with the flag name.
- Fix `tests generate --finding` to use `candidate.suggested_test` and `candidate.diff_unified`.
- Add `epilog` documentation links to `tests` and `tests generate`, and repoint the `--explain` help URL to `explain-pr.md`.
- Add tests covering dict payloads, `None` normalization, missing API key behavior, raw JSON string compatibility, `--finding` prompt content, and help documentation links.

## ⚠️ Impact/Warnings

- Behavior change: with no API key, `gitpr explain` now emits an error to stderr, returns empty markdown, and exits non-zero instead of producing a placeholder reviewer guide. Any automation relying on the old placeholder output must be updated.
- No database, environment variable, or dependency changes.
- Backward compatibility preserved for string-based AI responses (cached/legacy), with added coverage.

close #219

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_1_warning-yellow)](https://gitpr.natanfiuza.dev.br/)