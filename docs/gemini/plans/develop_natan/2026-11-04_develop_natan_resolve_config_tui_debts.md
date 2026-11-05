# Implementation Plan — Resolve Config TUI Technical Debts

**Branch**: `develop_natan`  
**Date**: `2026-11-04`  
**Task**: `resolve_config_tui_debts`

## Goal Description
Resolve the four inherited technical debts recorded in `docs/reports/relatorio_estado_v0.0.22.md` regarding configuration, CLI banner, and Textual UI consistency:
1. **`DEFAULT_CONFIG` redundancy with schema**: Eliminate manual maintenance of the 55-key default dictionary in `src/config.py` by making `src/config_schema.py` the Single Source of Truth (SSOT). Add `seeded: bool = False` to `ConfigField` and derive `DEFAULT_CONFIG = {f.key: f.default for f in FIELDS if f.seeded}`.
2. **Opening banner options**: Add `--init` and `--base` to `print_banner()` in `src/main.py` and update the translations across all 5 language files in `langs/`.
3. **Command palette disabled in `LinterApp`**: Set `ENABLE_COMMAND_PALETTE = False` on `LinterApp` in `src/ui/linter_app.py`, ensuring 100% uniformity across all Textual apps in GitPR.
4. **9 `GITPR_CHECK_*` variables in schema**: Register the `check` category (`doc="check-ci.md"`) and all 9 `GITPR_CHECK_*` fields in `src/config_schema.py`.

## User Review Required
> [!NOTE]
> All 4 decisions were reviewed and confirmed during Round 1 of the grilling interview:
> - `DEFAULT_CONFIG` derived from `FIELDS` where `seeded=True`.
> - `--init` and `--base` added to `print_banner()` with full i18n sync.
> - `LinterApp.ENABLE_COMMAND_PALETTE = False`.
> - `check` category placed after `baseline` with all 9 fields having `seeded=False`.

## Proposed Changes

### Configuration Core & Schema (SSOT)

#### [MODIFY] `src/config_schema.py`
1. Add `seeded: bool = False` to dataclass `ConfigField`:
```python
@dataclass(frozen=True)
class ConfigField:
    key: str
    label: str
    description: str
    category: str
    kind: str
    default: str = ""
    choices: tuple = ()
    choice_labels: tuple = ()
    advanced: bool = False
    validator: str = ""
    read_only: bool = False
    group: str = ""
    show_if: tuple = ()
    version_source: str = ""
    action: str = ""
    store: str = STORE_ENV
    seeded: bool = False
```
2. Mark `seeded=True` on the 55 fields that constitute `DEFAULT_CONFIG`.
3. Add `Category("check", ...)` to `CATEGORIES` right after `"baseline"`:
```python
    Category(
        "check",
        __("CI Check"),
        __("Unified pipeline checks, output formats, thresholds, and execution limits."),
        doc="check-ci.md",
    ),
```
4. Define the 9 `GITPR_CHECK_*` fields under category `"check"` with `seeded=False`:
   - `GITPR_CHECK_BASE` (str, default "")
   - `GITPR_CHECK_FORMAT` (enum: sarif, json, junit; default "sarif")
   - `GITPR_CHECK_OUTPUT` (path, default "")
   - `GITPR_CHECK_FAIL_ON` (enum: info, warning, error, minor, major, critical, blocker; default "error")
   - `GITPR_CHECK_NO_IA` (bool, default "false")
   - `GITPR_CHECK_IA_ONLY_HIGH_RISK` (bool, default "false")
   - `GITPR_CHECK_BASELINE_PATH` (path, default "")
   - `GITPR_CHECK_POLICY` (str, default "")
   - `GITPR_CHECK_TIMEOUT_SECONDS` (int, default "300")
5. Export `DEFAULT_CONFIG`:
```python
DEFAULT_CONFIG = {field.key: field.default for field in FIELDS if field.seeded}
```

#### [MODIFY] `src/config.py`
Replace the 90-line static `DEFAULT_CONFIG = { ... }` block with an import from `src.config_schema`:
```python
from src.config_schema import DEFAULT_CONFIG
```
This preserves full backward compatibility for any callers importing `from src.config import DEFAULT_CONFIG`.

---

### Main CLI & Internationalization (Banner Options)

#### [MODIFY] `src/main.py`
In `print_banner()`:
```python
    click.secho(
        __(
            "  Options: -c,--commit | -r,--review | -f,--fullreview | -l,--linter | -s,--skill | -u,--update | -ih,--installhooks | --install | --init | -is,--issue | --no-publish | --no-edit | --base | --plugins | -h,--help (use -h --flag for contextual help)\n"
        ),
        fg="white",
        dim=True,
    )
```

#### [MODIFY] `langs/pt_br.json`, `langs/pt_pt.json`, `langs/es_es.json`, `langs/fr_fr.json`
Update the translation key to include `--init` and `--base` in all locale dictionaries.

---

### UI Consistency (Command Palette)

#### [MODIFY] `src/ui/linter_app.py`
Add `ENABLE_COMMAND_PALETTE = False`:
```python
class LinterApp(App):
    """TUI for displaying Linter errors."""

    ENABLE_COMMAND_PALETTE = False
```

---

### Tests & Documentation

#### [MODIFY] `tests/test_config_schema.py`
Verify that all 55 existing seeded fields remain present in `DEFAULT_CONFIG`, test that `DEFAULT_CONFIG` is derived from `FIELDS` where `seeded=True`, and confirm the 9 `GITPR_CHECK_*` fields and the `check` category pass all integrity tests.

#### [MODIFY] `CONTEXT.md`
Add definitions for `CI Check configuration` and `Seeded configuration fields`.

---

## Verification Plan

### Automated Tests
Run pytest across the affected test suites:
- `pytest tests/test_config_schema.py -v`
- `pytest tests/test_i18n.py -v`
- `pytest tests/test_core.py -v`

### Manual Verification
1. Run `python run.py` and verify `--init` and `--base` appear in the banner.
2. Run `python run.py config` and verify the `CI Check` section appears in the sidebar with all 9 fields editable and documented.
3. Trigger `LinterApp` (or test in Python REPL) to verify command palette (Ctrl+P) is disabled.
