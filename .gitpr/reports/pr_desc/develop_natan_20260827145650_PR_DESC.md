# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: harden timeouts and external linter security
```

---

🎯 Summary

This change prevents the CLI from hanging indefinitely on stalled DNS or provider calls, and removes a shell-injection vector in external linter execution. It also fixes false-positive linter alerts caused by cross-file line-number collisions, adds full-file external linting for `--input`, and expands test coverage. Temporary i18n repair scripts were deleted.

🛠️ Technical Changes

- Add `bounded_urlopen()` with a hard wall-clock timeout to bound DNS resolution, and use it for chat-command and language file downloads.
- Add configurable `GITPR_AI_TIMEOUT` (default 600s) and `GITPR_LINTER_TIMEOUT` (default 120s) with safe fallbacks for invalid values.
- Refactor AI client creation to pass explicit timeouts to Gemini (milliseconds) and OpenAI-compatible DeepSeek/Ollama clients.
- Execute external linters as an argument list without `shell=True`; resolve executables via `shutil.which()` for Windows PATHEXT support and pass the configurable timeout.
- Parse Checkstyle XML file attributes and filter violations by file and diff lines to avoid false positives; run full-file external linters in `--input` mode.
- Delete one-off i18n maintenance scripts; ignore coverage artifacts; add `pytest-cov` dependency.
- Add tests for network timeouts, linter security/attribution, GitHub API, PR publish UI, and i18n missing/orphan key detection.

⚠️ Impact/Warnings

- New environment variables: `GITPR_AI_TIMEOUT` and `GITPR_LINTER_TIMEOUT` can be set in `.env`; invalid values fall back to defaults.
- External linter command parsing changed: commands are no longer run through a shell, and backslash escaping is disabled to preserve Windows paths. Shell metacharacters are treated literally; review complex commands.
- New dependency: `pytest-cov` added to `Pipfile`.
- Network fetches now have a hard timeout (default 10s) and fail over to offline/default data if a resolver stalls.

close #143