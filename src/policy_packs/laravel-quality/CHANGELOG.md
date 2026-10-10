# Changelog — gitpr/laravel-quality

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
the version follows [SemVer](https://semver.org/). A pack's version is part of
the repository's lockfile, so a change here is a change every adopting
repository has to review.

## [1.0.0] — 2026-10-09

### Added

- Review context: authorisation, mass assignment, transactions, N+1, reversible
  migrations, queue idempotency, logs and personal data.
- PR context and the five required sections, including what a rollback plan has
  to name.
- Commit context for the Laravel scope vocabulary.
- Linter rules: `laravel-env-outside-config`, `laravel-unguarded`,
  `laravel-request-all-to-model`, `laravel-log-sensitive`,
  `laravel-db-transaction-in-test`, `laravel-migration-drop-column`,
  `laravel-raw-response`.
- Inheritance of `gitpr/php-security` `>=1.0.0 <2.0.0`, including its severity
  override of `sec-generic-credential-assignment`.
- Risk configuration: 10 critical paths, two weights, three test patterns.
- Protected paths: `.env.example`, `config/**`, `database/migrations/**`,
  `routes/**`.
