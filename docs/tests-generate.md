# Technical Documentation: AI Test Generation (`gitpr tests generate`)

`gitpr tests generate` turns a change set into a complete test file. It detects the project's test framework, computes the conventional destination path, asks the AI for a ready-to-run test suite, validates the syntax with the local toolchain when available, and — only with `--apply` — writes the file to disk.

The command never runs the generated tests and never stages or commits anything.

---

## 1. Overview

```bash
# Generate tests for the whole working tree diff (dry run)
gitpr tests generate

# Generate tests for one file
gitpr tests generate --file src/auth/limiter.py

# Target a finding from the last code review
gitpr tests generate --finding FIX-001

# Force the framework instead of auto-detecting it
gitpr tests generate --framework vitest

# Write the generated file to disk (asks for confirmation)
gitpr tests generate --file src/auth/limiter.py --apply

# Contextual help with the documentation link
gitpr tests generate -h
```

---

## 2. Command Reference

```text
gitpr tests generate [--file PATH] [--finding ID] [--framework NAME] [--apply] [--provider NAME]
```

| Option | Default | Description |
|---|---|---|
| `--file PATH` | — | Generates tests for this file instead of the full diff. |
| `--finding ID` | — | Generates tests for a specific finding of the last code review (for example `FIX-001`). |
| `--framework NAME` | Auto-detected | Forces the framework: `pest`, `phpunit`, `jest`, `vitest`, `pytest`. |
| `--apply` | `false` | Writes the generated file to disk after a dry run and confirmations. |
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Forces the AI provider for this run (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Click help plus the link to this page. |

`--file` and `--finding` are mutually exclusive in practice: `--finding` takes precedence, and `--file` is then overwritten with the finding's file path.

---

## 3. Target Resolution

The command decides what to send to the model before generating anything:

| Invocation | Target content |
|---|---|
| *(no target flags)* | Working tree diff: `git diff HEAD` with the smart excludes. |
| `--file PATH` | `git diff HEAD -- PATH`. If that diff is empty and the file exists, the **full file content** is used instead. |
| `--finding ID` | The last review is loaded (`resolve_review` → `collect_candidates` → `find_candidate`), and the prompt receives the finding metadata, its `suggested_test`, and its `diff_unified` patch. The scaffold uses the finding's `file_path`. |

If the resolved content is empty, the command prints `❌ No changes or target content found to generate tests.` and exits with code `1`.

For `--finding`, the review must exist and be readable. If the candidacy resolution fails, the command prints a warning and falls back to a minimal context containing only `Finding ID: <id>`; in that case the generated test has very little to work with.

---

## 4. Framework Detection

Detection runs against the **repository root** only. The first match wins, in this order:

| Order | Framework | Indicators |
|---|---|---|
| 1 | `pest` | `pest.php`, `tests/Pest.php`, or `pestphp/pest` in `composer.json` (`require` / `require-dev`). |
| 2 | `phpunit` | `phpunit.xml`, `phpunit.dist.xml`, `phpunit.xml.dist`, or `phpunit/phpunit` in `composer.json`. |
| 3 | `vitest` | `vitest.config.{ts,js,mjs,mts}`, `vite.config.{ts,js}`, or `vitest` in `package.json` dependencies or scripts. |
| 4 | `jest` | `jest.config.{js,ts,mjs,cjs,json}`, or `jest` in `package.json` dependencies or scripts. |
| 5 | `pytest` | `pytest.ini`, `conftest.py`, `tox.ini`, `setup.cfg`, a `pyproject.toml` mentioning pytest, or `tests/test_*.py` / `tests/*_test.py`. |
| — | `unknown` | No indicator found. A warning tells you to use `--framework`. |

`--framework` is applied first. The value is matched case-insensitively against the five known names; an unknown value produces a warning and falls back to auto-detection instead of failing.

---

## 5. Scaffold Path Conventions

The destination path is computed before the AI is called, and the prompt receives it as the required target.

### Pest / PHPUnit

- `app/` is stripped from the front of the path.
- The suite is **Feature** when the first remaining segment is `Http`, `Controllers`, `Livewire`, or `Filament`; otherwise it is **Unit**.
- The file name receives a `Test.php` suffix unless the stem already ends with `Test`.

| Source | Destination |
|---|---|
| `app/Http/Controllers/Api/UserController.php` | `tests/Feature/Http/Controllers/Api/UserControllerTest.php` |
| `app/Services/UserService.php` | `tests/Unit/Services/UserServiceTest.php` |
| *(no source file, Pest)* | `tests/Feature/GeneratedTest.php` |
| *(no source file, PHPUnit)* | `tests/Unit/GeneratedTest.php` |

### Jest / Vitest

- `src/` is stripped from the front of the path.
- `.ts` / `.tsx` → `.test.ts`; `.vue` → `.spec.js`; anything else → `.test.js`.

| Source | Destination |
|---|---|
| `src/components/Button.vue` | `tests/components/Button.spec.js` |
| `src/utils/date.ts` | `tests/utils/date.test.ts` |
| `src/lib/api.js` | `tests/lib/api.test.js` |
| *(no source file, Vitest)* | `tests/generated.test.ts` |
| *(no source file, Jest)* | `tests/generated.test.js` |

### pytest

- `src/` or `app/` is stripped from the front of the path.
- `test_` is prepended unless the stem already starts with it.

| Source | Destination |
|---|---|
| `src/core.py` | `tests/test_core.py` |
| `app/services/auth.py` | `tests/services/test_auth.py` |
| *(no source file)* | `tests/test_generated.py` |

### Unknown

| Source | Destination |
|---|---|
| `src/model.py` | `tests/test_model.py` |
| *(no source file)* | `tests/test_generated.txt` |

The scaffold also records `already_exists`, which controls the overwrite confirmation in `--apply`.

---

## 6. Generation Pipeline

1. **Framework detection** — override or repository indicators (section 4).
2. **Scaffold** — conventional destination path (section 5).
3. **Provider and key** — `--provider` or `DEFAULT_AI_PROVIDER`. Without a key, the command adds a warning (`No API key configured for <provider>...`), returns empty content, and exits with code `1`. `ollama` needs no key.
4. **Model** — the advanced/primary model is used (`task_complexity="advanced"`).
5. **Skill** — `get_skill_context("tests", quiet=True)` reads `.gitpr/skill/.gitpr.tests.md`; without it, a built-in instruction equivalent to the English template is used. The skill defines the QA persona and the JSON envelope.
6. **Prompt** — framework, target path, target type, file/finding metadata, and the full diff.
7. **AI call** — `call_ai_model(..., action="tests")`, temperature `0.0`, up to **3** attempts with a **2 s** interval.
8. **Parsing** — the provider returns a parsed **dict**; a raw JSON string is also accepted. A non-JSON string is treated as a code block: fences are stripped and the whole text becomes the test file, with the scenario `Generated from raw model output`.
9. **Syntax validation** — the local toolchain checks the generated code when available (section 7).
10. **Optional write** — only when `--apply` is passed (section 8).

There is no prompt cache and no metrics ledger entry: each run calls the model.

---

## 7. Syntax Validation

Validation is best-effort and never blocks generation:

| Framework | Tool | Command | Notes |
|---|---|---|---|
| Pest / PHPUnit | `php` | `php -l <temp>.php` | Skipped when PHP is not on `PATH`. |
| Jest / Vitest | `node` | `node --check <temp>.js` | The temp file always uses a `.js` suffix, including for TypeScript sources. It catches gross syntax errors, not type errors. |
| pytest | `python` / `python3` | `python -m py_compile <temp>.py` | Skipped when neither binary is on `PATH`. |
| unknown | — | — | No validation. |

A failed validation adds a warning (`Syntax validation failed ... Marked as EXPERIMENTAL / low confidence.`) but the generated content is still returned and can still be written with `--apply`. Empty generated content is reported as invalid.

---

## 8. Writing with `--apply`

The command **always** prints the dry run first: framework, target path, covered scenarios, and the full generated code. Writing only happens after that, and only when `--apply` is present.

| Step | Condition | Default answer |
|---|---|---|
| Overwrite confirmation | The target path already exists (`already_exists`) | **No** |
| Write confirmation | Always | **Yes** |

If either confirmation is declined, the command prints a cancellation message and returns without writing. When accepted, it creates the parent directories and writes the file using UTF-8 with `errors='replace'`, relative to the **current working directory**.

It does **not** run `git add`, does not commit, and does not execute the generated tests.

---

## 9. Output Example

```text
$ gitpr tests generate --file src/auth/limiter.py

🧪 Analyzing diff and generating test file...

📋 Target Framework: PYTEST
📂 Target Test Path: tests/test_limiter.py

🧪 Covered Scenarios:
  • Happy path: request under the limit is allowed
  • Boundary: request exactly at the limit
  • Regression: counter expiration resets the window

--- Generated Test Code ---
def test_request_under_limit_is_allowed():
    ...
---

ℹ️ Dry-run mode. Run with --apply to write to disk.
```

With `--apply`, the same report is followed by the confirmations and by `✅ Test file successfully created at '<path>'!`.

---

## 10. Errors and Exit Codes

| Situation | Behaviour | Exit code |
|---|---|---|
| Tests generated (dry run or applied) | Report and, with `--apply`, the file | `0` |
| No diff / no file content | `❌ No changes or target content found to generate tests.` | `1` |
| No API key | Warning plus `❌ Test generation failed.` (empty content) | `1` |
| Model returned nothing usable | Warning plus `❌ Test generation failed.` | `1` |
| Syntax validation failed | Warning only; content is still shown/applied | `0` |
| User declines a confirmation | Cancellation message | `0` |
| Invalid CLI usage | Click usage error | `2` |

---

## 11. Limitations

- **Root-only detection.** Framework indicators are looked up at the repository root. Monorepos with per-package configs are not supported; use `--framework`.
- **First match wins.** A repository containing both PHP and JS indicators is detected as PHP, because PHP is checked first.
- **The generated test is not executed.** Only syntax is checked, and only when the corresponding binary is installed. A syntactically valid test can still fail at runtime.
- **TypeScript validation is shallow.** `node --check` parses the file as JavaScript; type errors and many TS-specific constructs are not validated.
- **Unknown framework produces a `.txt` file.** Without a framework there is no convention, no syntax check, and the target is `tests/test_generated.txt` (or `tests/test_<stem><ext>`).
- **`--file` without a diff sends the entire file.** For a large untouched file this can consume a significant part of the context window; the command has no chunking.
- **`--finding` depends on the last review.** It reads the review artifact produced by `gitpr -r` / `gitpr -f` through the `fix` machinery. Without a review, the context degrades to the finding ID.
- **Paths are relative to the current directory.** Running from a subdirectory writes the test relative to that subdirectory, not to the repository root.
- **No cache, no ledger.** Repeated runs call the model again, and the run is not recorded in `gitpr metrics`.
- **No git integration.** The new file is left untracked; `git add` and commit are up to you.
- **The chat `/tests` command is separate.** It does not delegate to this engine; use `gitpr tests generate` for structured generation.
- **The generated text follows the skill language**, not the `--lang` interface language.

---

## 12. Related Documentation

- [AI Code Review](code-review-ia.md) — where the findings consumed by `--finding` come from.
- [Fix Command](fix-command.md) — the review findings and patch machinery shared with `--finding`.
- [Skill Templates](skill-template.md) — how `.gitpr.tests.md` is resolved, downloaded, and overridden.
- [AI Providers](providers-ia.md) — providers, models, retries, and key configuration.
- [Reviewer Guide](explain-pr.md) — the other AI generation command.
- [Unified CI Check](check-ci.md) — which validations run in CI instead.
