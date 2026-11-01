# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: show subcommand help when -h precedes it
```

---

## 🎯 Summary
Fixes help resolution when `-h`/`--help` is provided before a subcommand. Previously, commands such as `gitpr -h config` could fail to show the intended subcommand help and could risk entering normal command execution paths. This change ensures the requested help is displayed and the CLI exits successfully without launching the config TUI or other command behavior.

## 🛠️ Technical Changes
- Added `_resolve_subcommand_tokens` to recover raw argument tokens after Click clears group context arguments.
- Updated the CLI callback to resolve the invoked subcommand, traverse nested command groups, and print the target command’s help when `help_flag` is set.
- Removed the redundant `help_flag` exclusion from the update-gate condition after introducing early help handling.
- Added CLI help tests covering root help, subcommand help, nested subcommands, and `-h`/`--help` before and after subcommands.
- Added documentation logo assets in `docs/`.

## ⚠️ Impact/Warnings
- No database, environment variable, or dependency changes.
- Behavior change: `-h`/`--help` before a subcommand now exits early with contextual help instead of continuing through normal subcommand execution.
- The token resolver uses frame inspection and `sys.argv` fallback, which may be sensitive to future Click internals; the added tests help guard the expected behavior.

close #252

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)