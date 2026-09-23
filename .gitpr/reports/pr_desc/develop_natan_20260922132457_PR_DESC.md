# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add AI-powered test generation command
```

---

## 🎯 Summary

Introduces a new `tests` capability that generates complete, executable test files from the current git diff, a specific source file, or a code review finding. The goal is to shorten the feedback loop between writing production code and getting meaningful test coverage, while respecting each repository's existing conventions (Pest, PHPUnit, Jest, Vitest, Pytest) instead of imposing a single style.

The feature follows the project's existing layered architecture (domain / application / presentation) so the same core logic is shared between the CLI and the interactive chat UI.

## 🛠️ Technical Changes

- **Domain layer (`src/domain/tests_generation/`)**:
  - Added `TestFramework` enum and dataclasses (`TestGenerationTarget`, `TestScaffold`, `GeneratedTest`) as the shared contract.
  - Added `detect_test_framework` to auto-detect the framework from config files, dependency manifests, and test directory contents, with support for an explicit override and warnings when detection fails.
  - Added `build_test_scaffold` to compute the conventional destination path per framework (e.g. Laravel `Feature`/`Unit` split, Pytest `tests/**/test_*.py`, JS/TS `.test`/`.spec` conventions).
- **Application layer (`src/application/use_cases/generate_test_file.py`)**:
  - Orchestrates framework detection, scaffold resolution, prompt construction, AI invocation, JSON parsing, and optional file writing.
  - Added `validate_test_syntax` which runs the local toolchain (`php -l`, `node --check`, `python -m py_compile`) when available; validation failures are surfaced as warnings rather than hard errors.
  - Gracefully degrades when no API key is present or when the model returns non-JSON output (strips markdown fences and marks the result as low confidence).
- **Presentation layer**:
  - New CLI group `tests` with a `generate` subcommand supporting `--file`, `--finding`, `--framework`, `--apply`, and `--provider`. Defaults to a safe dry-run and prompts before overwriting an existing test file.
  - Chat UI now delegates `/tests` (and localized aliases) to the same use case instead of forwarding to the generic chat model.
- **Configuration**: registered the new `tests` skill file (`.gitpr.tests.md`) in `SKILL_FILES_BY_TYPE`.
- **Tests**: added unit coverage for the framework detector, scaffold builder, syntax validation, dry-run/apply flows, and CLI invocation.

## ⚠️ Impact/Warnings

- **No database changes** and **no new environment variables**; the feature reuses the existing AI provider configuration (`get_ai_provider`, `get_api_key`, `get_api_model`).
- **New external runtime dependencies (optional)**: syntax validation spawns local `php`, `node`, or `python` binaries when present. If a toolchain is missing, validation is skipped with a warning instead of failing.
- **Filesystem writes**: only performed with `--apply` (CLI) and after explicit user confirmation. Existing test files trigger an overwrite prompt defaulting to **No**.
- **New skill file**: a `.gitpr.tests.md` skill template is expected to exist for the `tests` action; a built-in fallback instruction is used when it is absent.

close #187

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_11_warnings-yellow)](https://gitpr.natanfiuza.dev.br/)