# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: collapse binary hunks and expand smart excludes
```

---

## 🎯 Summary

Binary blobs without a NUL byte in their first 8KB (or forced to text via `.gitattributes`) were being diffed as text, flooding AI prompts with U+FFFD replacement-character streams. This wasted tokens, degraded model output quality, and occasionally produced garbled PR descriptions and reviews. This change adds a defensive guard at the diff-parsing layer and broadens the default exclusion list so binary files never reach the model in the first place.

## 🛠️ Technical Changes

- Added `collapse_binary_hunks` in `src/diff_parser.py`, a new **Binary hunk guard** that detects suspicious hunks (contiguous runs of ≥8 U+FFFD, or ≥32 U+FFFD at ≥10% density) and rewrites them into git's standard `Binary files ... differ` marker.
- Implemented an O(1) fast path that returns the diff unchanged when no U+FFFD is present, preserving legitimate Latin-1 / Windows-1252 source files byte for byte.
- Wired the guard into every diff entry point: `get_git_diff`, `get_git_staged_diff`, `get_unstaged_diff`, `get_git_full_diff`, `current_diff` (baseline), `get_check_diff`, `tests_generate`, and `risk`.
- Updated `filter_excluded_sections` to always apply the guard (including the empty-patterns and no-sections early exits) so remote PR diffs also benefit.
- Expanded `_FALLBACK_SMART_EXCLUDES` and `templates/gitpr.smart-excludes.json` with 100+ patterns across 8 binary families: images/design, documents/Office, archives/packages, fonts, audio/video, compiled binaries/bytecode, databases/ML weights/raw binary, and certificates/keystores — plus additional lockfiles (`bun.lockb`, `uv.lock`, `Cargo.lock`, `mix.lock`, `Podfile.lock`, etc.).
- Added unit and integration tests covering the fast path, Latin-1 preservation, contiguous-run collapse, density collapse, remote filtering, template parity, and binary-family coverage.

## ⚠️ Impact/Warnings

- **Behavioral change:** diffs containing binary-like content now return a `Binary files a/... and b/... differ` line instead of raw hunks. Any downstream consumer relying on binary hunk content will see the marker instead.
- **Configuration:** default smart-excludes were expanded significantly. Existing user overrides remain honored, but projects relying on the fallback list will now see many more files filtered.
- **Dependency:** `__lang_version__` bumped from `v0.0.38` to `v0.0.39` to track updated language assets (independent of package version `1.5.0`).
- **Database:** no schema or migration changes.
- **Maintenance:** `_FALLBACK_SMART_EXCLUDES` and `templates/gitpr.smart-excludes.json` are now enforced as 1:1 parity by tests — both must be updated together.

close #271

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_10_warnings-yellow)](https://gitpr.natanfiuza.dev.br/)