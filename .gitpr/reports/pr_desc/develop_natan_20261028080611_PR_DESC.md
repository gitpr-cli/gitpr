# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: refresh stale update cache by TTL and gate subcommands
```

---

## 🎯 Summary

The update gate was unreliable in two directions: it could miss a freshly published release and it could block users on commands they never intended to run online.

The PyPI cache was keyed on the calendar day, so a release published after the first run of the day stayed invisible until midnight, while an offline run kept serving an answer with no way to know how old it was. The cache is now a rolling one-hour window with an explicit `checked_at` timestamp, written atomically and validated on read, so a corrupt file, a future timestamp from a clock jump, or a leftover of the legacy schema simply expires instead of poisoning the answer.

The version comparison moved to PEP 440 (`packaging.version.Version`) instead of tuple math. That fixes ordering for multi-digit segments, stops a remote pre-release from blocking a stable install on a `pip install --upgrade` that would refuse to install it, and treats an unparseable version on either side as "unknown" rather than "newer". The mandatory gate also now covers subcommands (`gitpr badge`, `gitpr release`), but only when the run may stop and ask the user: a CI job, a pipe or a hook is never blocked, and `-h`/`--help` is detected from the raw `argv` because Click clears the context arguments before the group callback runs.

## 🛠️ Technical Changes

- Replace the daily update cache with a rolling `UPDATE_CACHE_TTL_SECONDS = 3600` window keyed on an ISO `checked_at` field; legacy `date`-based documents are treated as expired and rewritten.
- Validate the cached document on read (`dict` check, timestamp parse, non-empty string version); a timestamp in the future counts as stale to survive clock rollbacks.
- Write the cache through a `tempfile.NamedTemporaryFile` plus `os.replace`, cleaning the temporary file on failure; a read-only home no longer hides the fetched version.
- Route the PyPI request through `src.net.bounded_urlopen` with `UPDATE_FETCH_HARD_TIMEOUT = 3.0`, gaining DNS-inclusive wall-clock bounding.
- Reject non-JSON bodies and non-version payloads before caching, so a captive portal or a malformed mirror cannot be persisted.
- Parse versions with `packaging.version.Version` through `_coerce_version()`, handling the leading `v` and PEP 440 suffixes; `parse_version()` keeps its tuple contract for outside callers.
- Add `_is_newer()` for the gate and `--update` comparison, ignoring remote pre-releases on a stable install.
- Add `force=True` to `get_latest_remote_version()`; `check_and_update()` uses it so `--update` always hits PyPI.
- Parse `GITPR_SKIP_UPDATE_CHECK` as a strict boolean against `_SKIP_TRUTHY_VALUES`, so `false`/`0`/`no` no longer mute the check.
- Add `_subcommand_help_in_argv()` and extend the mandatory gate to subcommands when `may_ask and not update and not help_flag`.
- Bump `__version__` to `1.4.3` and expand the test suite to cover TTL boundaries, legacy/corrupt caches, atomic writes, force mode and the subcommand gate.

## ⚠️ Impact/Warnings

- **Cache format change:** `update_cache.json` now stores `checked_at` instead of `date`. Existing caches are ignored on first run and overwritten after the next successful fetch — no migration is needed.
- **Environment variable semantics:** `GITPR_SKIP_UPDATE_CHECK` now only disables the check for `1`, `true`, `yes`, `on`, `y` (case-insensitive). Automation that set `GITPR_SKIP_UPDATE_CHECK=false` expecting the check to be muted will now see the check run.
- **Dependency:** relies on `packaging` and on `src.net.bounded_urlopen`; ensure both ship with the distribution.
- **Behavior change:** interactive subcommands can now exit with code `1` when the local install is outdated; non-interactive runs, hooks, `--update` and help invocations are exempt.
- No database changes.

close #227

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)