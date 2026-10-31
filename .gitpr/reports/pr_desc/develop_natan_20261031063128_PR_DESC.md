# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: extend secret detection ruleset coverage
```

---

## 🎯 Summary

The secret scanning ruleset was missing several real-world credential formats (AWS STS keys, fine-grained GitHub PATs, Slack client/cookie tokens) and only detected generic credentials when the value was quoted. It also produced false positives on identifiers that merely ended with a secret-like word (e.g. `bypassword`) and on runtime expressions such as `os.getenv(...)`.

This change widens detection coverage without increasing noise, so leaked secrets in configuration files, unquoted `.env`-style assignments, and JS/Shell/Python runtime references are correctly classified.

## 🛠️ Technical Changes

- **AWS access keys**: regex now matches both `AKIA` and `ASIA` (temporary STS credentials) and adds a `(?<![A-Z0-9])` lookbehind to prevent matches inside contiguous alphanumeric strings (e.g. `MALAYSIA1234...`).
- **GitHub tokens**: adds support for fine-grained personal access tokens (`github_pat_` with 82+ chars) alongside the existing `gh[pousr]_` pattern, with a `github_pat_`-short near-miss guard.
- **Slack tokens**: extends the prefix class to `xox[baprscd]`, covering client (`xoxc`) and cookie (`xoxd`) tokens.
- **Generic credential assignment rule**:
  - Introduces a left boundary `(?<![a-zA-Z0-9])` so prefixed snake_case keys (`db_password`, `MY_API_KEY`, `auth-token`) match while suffix-only identifiers (`bypassword`, `antisensha`) do not.
  - Adds an unquoted value branch `[^\s'\"#;,]{6,}`, enabling detection of `.env`-style lines like `API_KEY=abc123xyz`.
  - Uses a backreference (`\1`) so quoted values only match when the closing quote matches the opening quote.
  - Extends the placeholder filter with `true|false|null|none` and runtime-expression prefixes (`$`, `${`, `process.`, `os.`, `env(`) to avoid flagging environment variable references and templates.
- **Tests**: adds positive cases for STS keys, GitHub PATs, Slack client/cookie tokens, unquoted assignments and prefixed snake_case keys; expands near-miss/negative sets and parametrizes unquoted placeholder filtering, including the `your_password_here2` boundary case.

## ⚠️ Impact/Warnings

- **Behavioral change**: security scanning results may change — previously undetected secrets are now reported, and some previously flagged strings (unquoted placeholders, runtime expressions) are no longer reported. Consumers relying on exact match counts should update expectations.
- **False-negative risk**: the unquoted branch requires a minimum value length of 6 characters and stops at whitespace or `#;,`, so very short or space-containing unquoted secrets will not be detected.
- No database, dependency, or environment variable changes.

close #242

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)