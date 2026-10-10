# gitpr/php-security

A security baseline for PHP projects, framework-agnostic. It is the dependency of
[`gitpr/laravel-quality`](../laravel-quality/), and stands on its own for a
Symfony, Slim or plain PHP codebase.

## What it changes

| Surface | Effect |
|---|---|
| Review | Adds the six-point security checklist to the review prompt |
| PR description | Asks for a security-impact section whenever the change touches the request path, a query, auth, session or configuration |
| Linter | 8 rules: raw SQL interpolation, `eval`, weak password hashing, `unserialize`, dynamic include, `extract` from input, wildcard CORS, insecure session cookie |
| Linter severity | Hardens `sec-generic-credential-assignment` from warning to error |
| Risk | 6 critical paths, `security_sensitive` weight 30, PHP test patterns |

## Activate

```bash
gitpr policy use gitpr/php-security
```

## On the embedded secret ruleset

GitPR ships seven secret-scanning rules that run on every invocation, in every
repository, with or without a pack. This pack does not duplicate them — it only
raises one of them to a blocking error, because adopting a security pack is a
decision to hold the stronger gate.

The rules that are warnings here (`unserialize`, dynamic include, `extract`,
session cookie) are warnings because a single line cannot tell whether the data
is trusted. A repository that knows its own answers should tighten them in
`.gitpr/policy.overrides.yml`.
