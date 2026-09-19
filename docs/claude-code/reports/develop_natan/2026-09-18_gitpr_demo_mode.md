## Completion Report — Guided Tour (`gitpr demo`)

### What was done

Implemented `gitpr demo`: a six-step guided tour over an example diff that ships inside the package. The goal is the one the spec asked for — first-contact time-to-value — so the tour needs **no API key, no Git repository and no internet**. It is the only command that shows what GitPR does on a machine where GitPR has never run.

It is not a slideshow: the tour drives the **real** pipeline — `generate_pr_content()`, the linter, `compose_review_content()` — with the model call replaced by a fake that replays recorded answers. What the user sees is what the product produces, minus the key.

- **Two example scenarios** — `laravel-bug-fix` (PHP/Laravel, a profile update that rejects your own e-mail) and `security-issue` (TypeScript/Express, an IDOR in an invoice download). Each is a `.py` module holding the `DIFF` (code, never translated) and the prose in five languages.
- **`FakeAIProvider`** — a class whose `call_ai_model` signature is asserted **equal to the real `ai_providers.call_ai_model`** by `inspect.signature`, so the fake cannot silently drift from the function it replaces (§9.4). It returns a superset of the keys the pipeline reads and records every call.
- **`demo_pipeline()`** — one context manager patching nine names across `src.core` (`call_ai_model`, the two cache calls, both metric calls, `get_api_key`, `get_api_model`, `get_skill_context`) and `src.metrics`. Cache, telemetry and the user's own `.gitpr/skill/` are neutralized without touching production code.
- **`demo_runner.py`** — `DemoStep` / `DemoState` / `load_scenario()` plus the six steps and the text-mode renderer. The three artifacts are generated **once, before the first screen**, so stepping back never regenerates and never shows a different answer.
- **`DemoApp`** (Textual) — single-screen app with a `ModalScreen` help overlay, matching every other app in the product: `n`/`→`/`Enter` forward, `p`/`←` back, `F1` help, `Esc` out. `demo_screens.py` holds per-step **composer functions**, not `Screen` subclasses; the diff renders through `rich.syntax.Syntax`, already available via Textual.
- **CLI** — `@cli.command("demo")` in `src/main.py`. As a subcommand it escapes every startup gate (the PyPI update block, `check_internet_connection()`, `setup_environment()`), which is what makes the no-key/no-network promise structural rather than aspirational. It declares its **own** `--lang`, because the root `--lang` handler sits after the subcommand `return` and never runs for it.
- **First-run suggestion** — `src/config.py` offers the tour as an escape hatch at the moment a user is asked to paste an API key.
- **i18n** — 32 new keys per `langs/*.json` (31 chrome + 1 suggestion) in exact parity across the six files; `__lang_version__` bumped `v0.0.28` → `v0.0.29`.
- **Docs** — new `docs/demo.md` + `.pt_br` / `.pt_pt` / `.es_es` / `.fr_fr`; a "Seeing It Work (No Configuration)" section in `README.md` and its four variants, with the old step 2 renumbered to 3.
- **No new dependency** — `pyproject.toml` and `Pipfile` are untouched, and the watch is that the package ships **zero non-`.py` files**, so the scenarios are modules and nothing needs `package_data` or `MANIFEST.in`.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/demo/__init__.py` | feat | package marker (setuptools discovery) |
| `src/demo/scenarios/__init__.py` | feat | registry: `SCENARIOS`, `load_scenario()`, `DemoScenarioError` |
| `src/demo/scenarios/laravel_bug_fix.py` | feat | `NAME` / `DIFF` / `TEXT[lang]` for the Laravel example |
| `src/demo/scenarios/security_issue.py` | feat | `NAME` / `DIFF` / `TEXT[lang]` for the IDOR example |
| `src/demo/fake_ai_provider.py` | feat | `FakeAIProvider` + `demo_pipeline()` |
| `src/demo/demo_runner.py` | feat | `DemoStep`, `DemoState`, `run_demo()`, `run_demo_text_mode()` |
| `src/ui/demo/demo_app.py` | feat | `DemoApp` (Textual, single-screen + modal) |
| `src/ui/demo/demo_screens.py` | feat | per-step composer functions |
| `src/ui/demo/demo_help_screen.py` | feat | help modal (F1), mirroring `src/ui/help_screen.py` |
| `src/main.py` | feat | `demo` subcommand: `--scenario`, `--lang`, `--no-tui` |
| `src/config.py` | feat | the tour offered at the API-key prompt (first run) |
| `src/updater.py` | chore | `__lang_version__` → `v0.0.29` |
| `langs/*.json` (6) | feat | 32 keys each, parity enforced by `tests/test_i18n.py` |
| `tests/demo/` (6 files + `conftest.py`) | test | 149 new tests |
| `docs/demo.md` + 4 variants | docs | new feature documentation (151 lines each) |
| `README.md` + 4 variants | docs | "Seeing It Work (No Configuration)" section |
| `docs/survey/20260918_gitpr_demo_mode_surveyfacts.md` | docs | the grill survey behind the plan |

### Impact

- **Functionality:** a new top-level command. Nothing existing changed behaviour: the tour reuses the pipeline through `mock.patch` at the `src.core` boundary, so the production path is byte-identical outside the demo. The one non-demo edit with a visible effect is the first-run suggestion — one extra line, printed only when an interactive run has no API key for its provider, and never in CI (the CI shield still exits before it).
- **Performance:** none on any existing path. The tour itself runs in about a second: no network, no model call.
- **Compatibility:** additive. No API, no flag, no environment variable and no output file of any existing command changed. `__lang_version__` moving to `v0.0.29` makes existing installs re-download their language pack, smart-excludes and thinking words once on the next run — that is the mechanism by which the 32 new strings reach them, and the same step the previous feature took.

#### Deviations from the approved plan

1. **The first-run suggestion moved.** The plan anchored it at `config.py:421`, the `if not provider:` branch (now [config.py:427](../../../../src/config.py#L427)). That branch is **unreachable on a first run**: `DEFAULT_CONFIG` seeds `DEFAULT_AI_PROVIDER = "gemini"`, and `setup_environment()` writes missing defaults and reloads `.env` *before* the check, so `provider` is never falsy. Verified against a throwaway `HOME` with an empty `.env` — no welcome banner, no prompt branch, and the fresh `.env` ends with `DEFAULT_AI_PROVIDER=gemini`. The line now lives in the `if not api_key:` branch, which is what a first run actually reaches:

   ```
   💡 Want to see it first? `gitpr demo` walks through the whole tool on a recorded example — no key needed.
   🔑 API Key for Gemini not found.
   ```

   A comment was added at the dead branch documenting why, with no behaviour change.

2. **`__lang_version__` bumped** — not in the plan, but without it the 32 new keys never reach an existing install: the local pack is only refreshed when the marker changes.

3. **`tests/sync_i18n.py` must not be run.** The plan lists it as a verification step. Its regex extractor stops at the first fragment of an implicitly-concatenated literal, so running it would drop 39 keys and add 40 fragments; `tests/test_i18n.py` parses with AST and folds them correctly. The keys were inserted with a one-off sorted-insert script guarded by a byte-identical round-trip check, and parity is enforced by `tests/test_i18n.py`.

4. **`gitpr -h --demo` still errors** (`No such option: --demo`); there is no `HELP_MAP` entry, which the plan explicitly left out of scope. The feature's help is `gitpr demo --help`, and its epilog carries the localized documentation link.

5. **`--lang <code>` inherits the pre-existing import-time i18n fetch.** `src/i18n.py` may download `~/.gitpr/langs/{code}.json` when the local pack is missing or the marker moved. That is Q5a's accepted pre-existing behaviour, affects every command, and is unaffected by this change. Its visible consequence today: with a locally cached pack that predates these keys, the **scenario prose** localizes correctly while the **chrome** falls back to English — verified with `pt_br` and `fr_fr`. That is the designed degradation, and the marker bump resolves it once the packs publish with the release.

### Verification

```
python -m pytest tests/demo -q                    # 149 passed
python -m pytest tests/demo tests/test_i18n.py -q # 169 passed
python -m pytest tests/ -q                        # 25 failed, 1559 passed, 2 skipped
```

The 25 failures are **pre-existing**. A pristine `HEAD` worktree (`git worktree add` at `8920d13`) run side by side with the working tree produces the **identical `FAILED` set, compared name by name** (`diff` of the two sorted lists is empty), and the pass count differs by exactly the new suite: 1410 passed at `HEAD` against 1559 in the working tree — **+149**, the number of tests in `tests/demo`. Families: `test_config_app` (13), `test_suggest_reviewers` (5), `test_net_timeouts` (2), and one each in `test_chat_backend`, `test_mcp_server`, `test_reviewer_resolution`, `test_main_suggest_reviewers` and `fix/test_rollback_fix`.

End-to-end, from a temporary directory with **no `.git`** and no API key:

| Command | Result |
| --- | --- |
| `gitpr demo --no-tui` | six sections in order, exit 0 |
| `gitpr demo --scenario security-issue --no-tui` | the other example, exit 0 |
| `gitpr demo --scenario nao-existe` | exit 1, listing the available scenarios |
| `gitpr demo --lang pt_br --no-tui` | scenario prose in Portuguese, chrome per §5 |
| `gitpr demo --help` | options + localized documentation link |
| `GITPR_LANG=fr_fr gitpr demo --no-tui` | scenario prose in French |

Nothing is written where it matters: `~/.gitpr/metrics/` and `~/.gitpr/cache/` were hashed before and after a run and are **unchanged** (2430 files, identical tree hash). Exactly one line is appended to `~/.gitpr/logs/` — the invocation log written by the root callback for every command, documented in `docs/demo.md` §6 with its `GITPR_SHOW_LOGS=false` off switch.

Packaging: `setuptools.find_packages(include=["src", "src.*"])` resolves `src.demo`, `src.demo.scenarios` and `src.ui.demo`, and there is no non-`.py` file under them to ship.

### Next steps

- **i18n fetch at import** — the root cause behind deviation 5: a command that promises "no network" still inherits a language download from `src/i18n.py` at import. Fixing it properly (lazy fetch, or fetch only when a translated string is actually requested) would benefit every command, not just the tour.
- **`HELP_MAP` entry** for `gitpr -h --demo`, for consistency with the other flags.
- **A scenario default** (`GITPR_DEMO_SCENARIO` or similar) if the Config screen's section for the tour should stop being empty.
- **`sync_i18n.py`** — its regex extractor should be replaced by the AST approach already used in `tests/test_i18n.py`, so the documented verification step stops being unsafe to run.
