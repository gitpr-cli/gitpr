# Plan: `--lang` CLI flag for per-execution language override

## Context

The `CURRENT_LANG` module variable in `src/i18n.py:82` is set once at import time from `GITPR_LANG` env var or OS locale. There is no way to change the language at runtime — users must edit `~/.gitpr/.env` and restart the tool. We need a `--lang` flag (like `--lang pt_br` or `--lang en_us`) that overrides the language for a single execution without persisting to `.env`, working with ALL existing commands.

Two categories of lang-dependent code exist:
- **Runtime references**: `core.py` (`get_doc_url`), `ai_providers.py` (`load_chat_commands`), `tui_issue.py`, `help_screen.py` — these re-read `CURRENT_LANG` at call time, so mutating the module var works transparently
- **Module-level frozen constants**: `spinner.py` (`THINKING_WORDS`, `THINKING_WORDS_URL`, `_LANG_SUFFIX`) — these must be explicitly recomputed

## Files to modify

### 1. `src/i18n.py` — Add `set_lang()` function

**Where:** Between line 83 (`TRANSLATIONS = get_translations(CURRENT_LANG)`) and line 85 (`def __():`)

**What:**
```python
def set_lang(lang: str) -> None:
    """Override session language at runtime. Does NOT persist to .env."""
    global CURRENT_LANG, TRANSLATIONS
    lang = lang.lower().replace("-", "_")  # normalize pt-BR → pt_br
    CURRENT_LANG = lang
    TRANSLATIONS = get_translations(lang)
```

- Uses `global` to mutate module-level `CURRENT_LANG` and `TRANSLATIONS`
- `get_translations()` handles download/cache/fallback for unknown languages
- Python's `from i18n import CURRENT_LANG` binds to the module attribute, so all importing modules see the mutation

### 2. `src/spinner.py` — Add `reload_thinking_words()` function

**Where:** Between line 96 (end of `_load_thinking_words()`) and line 97 (`THINKING_WORDS = _load_thinking_words()`)

**What:**
```python
def reload_thinking_words(lang: str) -> None:
    """Recompute spinner constants for the given language."""
    global _LANG_SUFFIX, THINKING_WORDS_URL, THINKING_WORDS
    _LANG_SUFFIX = "" if lang.startswith("en") else f".{lang}"
    THINKING_WORDS_URL = (
        "https://raw.githubusercontent.com/natanfiuza/gitpr/"
        f"refs/heads/main/templates/gitpr.thinking-words{_LANG_SUFFIX}.md"
    )
    THINKING_WORDS = _load_thinking_words()
```

- Must update `THINKING_WORDS_URL` BEFORE calling `_load_thinking_words()` because the function references it internally
- No Spinner instances exist yet at this point in execution (lang override runs before any command logic)

### 3. `src/main.py` — Add Click option and wiring

**3a. New `@click.option`** (after line 145, after `--provider`, before `--help`):
```python
@click.option('--lang', type=str, help=__("Forces the interface language for this execution (e.g.: en_us, pt_br)."))
```

**3b. Add `lang` parameter** to `cli()` signature (line 147):
```python
def cli(commit, ..., help_flag, lang):
```

**3c. Language initialization block** (after line 207 `ctx.exit()`, before line 209 commented section, before `print_banner()`):
```python
    # Language override via --lang flag (one-shot, does not persist)
    if lang:
        from src.i18n import set_lang
        from src.spinner import reload_thinking_words
        set_lang(lang)
        reload_thinking_words(lang)
```

**Placement rationale:**
- AFTER the help handler (line 207 `ctx.exit()`) — `-h` should exit before any lang override
- BEFORE `print_banner()` (line 211) — banner and all subsequent `__()` calls need correct lang
- BEFORE any spinner/AI logic — spinner words must be loaded in the correct language

## Files NOT modified

`core.py`, `ai_providers.py`, `tui_issue.py`, `help_screen.py`, `config.py`, `updater.py`, any JSON/template/doc files — all work transparently via the mutated `CURRENT_LANG`

## Edge cases

| Case                     | Behavior                                                                                                 |
| ------------------------ | -------------------------------------------------------------------------------------------------------- |
| `--lang en_us`           | `get_translations("en_us")` returns `{}`; spinner uses English (no suffix)                               |
| `--lang pt_br`           | Downloads/loads `pt_br.json`; spinner downloads `gitpr.thinking-words.pt_br.md`                          |
| `--lang xx_yy` (unknown) | `get_translations()` returns `{}` → English fallback for `__()`; spinner falls back to `_FALLBACK_WORDS` |
| `--lang pt-BR` (hyphen)  | Normalized to `pt_br` by `.replace("-", "_")`                                                            |
| No `--lang` flag         | Current behavior unchanged — `GITPR_LANG` from `.env` or OS locale                                       |

## Verification

1. `pipenv run python run.py --lang en_us -c` — commit message appears in English
2. `pipenv run python run.py --lang pt_br -c` — commit message appears in Portuguese
3. `pipenv run python run.py --lang pt_br -ch` — chat TUI loads with Portuguese translations and spinning words
4. `pipenv run python run.py -c` (no `--lang`) — uses existing `GITPR_LANG`/OS locale (no regression)
5. Verify `.env` is NOT modified after any `--lang` execution
