# Glossary — `gitpr check`

- **Check run** — one execution of the unified pipeline against a diff base, producing exactly one artifact and one exit code.
- **Artifact** — the structured result of a check run, in SARIF, JSON or JUnit.
- **Fail threshold** (`--fail-on`) — the minimum severity at which a countable finding fails the run.
- **Countable finding** — a finding that can fail the run: baseline status `new`, or any finding when no baseline exists.
- **Incomplete run** — a check run that hit its deadline; its artifact is partial and its exit code is 2.
- **High-risk file** — a file whose risk level is `high` or above; the only files sent to AI under `--ia-only-high-risk`.
- **Severity aliases** — the spec names `minor`, `major`, `critical`, `blocker`, accepted by `--fail-on` and folded onto `warning`/`error`.

