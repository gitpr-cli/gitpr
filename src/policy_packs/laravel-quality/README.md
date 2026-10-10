# gitpr/laravel-quality

A quality gate for Laravel applications. It extends
[`gitpr/php-security`](../php-security/) and inherits everything that pack adds.

## What it changes

| Surface | Effect |
|---|---|
| Review | Adds the Laravel checklist to the review prompt: authorisation, mass assignment, transactions, N+1, reversible migrations, queue idempotency, logs and personal data |
| PR description | Adds the rollback-plan requirement and the meaning of "test evidence" |
| Commit | Asks for a Conventional Commits scope from the Laravel vocabulary |
| Linter | 7 rules (`laravel-*`), on top of the 8 inherited from `php-security` |
| Linter severity | Hardens `sec-generic-credential-assignment` from warning to error |
| Risk | 10 critical paths, `database_migration` weight 25, `no_test_change` weight 20, PHP test patterns |
| PR shape | 5 required sections |
| Commit types | `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `build`, `ci` |
| Protected paths | `.env.example`, `config/**`, `database/migrations/**`, `routes/**` |

## Activate

```bash
gitpr policy use gitpr/laravel-quality
```

This writes `.gitpr/policy.lock.yml`, which belongs in version control. Everyone
on the team then runs under the same policy without installing anything.

## What it does not assume

The paths are the default Laravel skeleton. A project that moved its controllers
or keeps its tests elsewhere should correct them in
`.gitpr/policy.overrides.yml` rather than fork the pack — see
`docs/policy-packs.md`.

## Levels

Rules that a legitimate Laravel codebase can trip on a valid line are warnings.
The three that are errors — `env()` outside `config/`, an open mass assignment
and `$request->all()` written straight to a model — are wrong in every Laravel
version and every project layout.
