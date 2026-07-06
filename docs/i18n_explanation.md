# Internationalization (i18n) in GitPR — Developer Guide

## Overview

GitPR uses a custom internationalization (i18n) engine inspired by **Laravel's `__()` helper**. All user-facing strings are written in **English** as keys, and translations are loaded from JSON files at runtime. The system auto-detects the operating system language and falls back to English when no translation is available.

---

## Architecture

### Core files

| File | Purpose |
|---|---|
| `src/i18n.py` | Translation engine: `__()` function, language detection, JSON loading |
| `src/updater.py` | Defines `__lang_version__` — controls translation cache invalidation |
| `langs/pt_br.json` | Portuguese (Brazil) translations — key-value pairs (EN → PT-BR) |
| `~/.gitpr/langs/{lang_code}.json` | User-local translation cache (downloaded on first run) |
| `~/.gitpr/.env` | Stores `GITPR_LANG` (force language) and `LANG_VERSION` (cache version) |

### How it works

```
1. i18n.py loads at module import time
2. get_system_language() detects OS locale (e.g., pt_BR, es_ES) or reads GITPR_LANG from .env
3. get_translations() loads the JSON file from ~/.gitpr/langs/{lang}.json
   - If the file doesn't exist or is outdated (LANG_VERSION != __lang_version__) → downloads from GitHub
   - If the language is English → returns empty dict (no translation needed)
   - If download fails and local file exists → uses the cached version
4. TRANSLATIONS dict is kept in memory for the session
5. __() function: looks up the key → returns translation (or the key itself as fallback)
```

### The `__()` function

```python
def __(key, **kwargs):
    """
    Translation Engine inspired by Laravel.
    Tries to find the key in the dictionary. If not found, returns the key itself (English).
    """
    text = TRANSLATIONS.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
```

**Key features:**
- **Key = English fallback** — if no translation exists, the English string is displayed directly
- **Named placeholders** — supports Python's `str.format()` with keyword arguments
- **Safe formatting** — if a placeholder is missing, it silently falls back to the raw string

---

## How to use `__()` in code

### Basic usage (static strings)

```python
from src.i18n import __

# Before (hardcoded Portuguese):
click.secho("✅ Arquivo salvo com sucesso!", fg="green")

# After (i18n-ready):
click.secho(__("✅ File saved successfully!"), fg="green")
```

### With placeholders (dynamic values)

```python
# Single placeholder
click.echo(__("Downloading {file_name}...", file_name="template.md"))

# Multiple placeholders
click.secho(__("🤖 GitPR is analyzing your code using {provider} ({model})...",
               provider="Gemini", model="gemini-2.5-flash"), fg="cyan")
```

### In Click decorators

```python
@click.option('-c', '--commit', is_flag=True,
              help=__("Generates only the commit message and displays it in the console."))
```

### In class attributes (beware of import order)

```python
class IssueApp(App):
    TITLE = __("GitPR - Issue Generator")  # Works! __() runs at class definition time
```

### In Textual UI components

```python
BINDINGS = [
    Binding("f2", "save_local", __("Save Local")),
    Binding("f3", "create_issue", __("Create on GitHub")),
]
```

### For string comparisons (AI responses, cache keys)

**⚠️ Important:** Never use `__()` for string comparisons! The function returns the translated value (e.g., Portuguese), which would break comparisons. Instead, use a list of possible variations in both languages:

```python
# CORRECT — check multiple language variations
_no_commits = [
    "No exclusive commits",
    "No exclusive commits found",
    "Nenhum commit exclusivo",
    "Nenhum commit exclusivo encontrado",
]
_no_commits_found = any(phrase in context_text for phrase in _no_commits)
```

---

## How to add translations

### 1. Add the translation key to `langs/pt_br.json`

```json
{
    "✅ File saved successfully!": "✅ Arquivo salvo com sucesso!",
    "Downloading {file_name}...": "A descarregar {file_name}..."
}
```

The key is the **exact English string** used in the code. The value is the Portuguese translation.

### 2. Placeholders must match

If the English key has `{file_name}`, the Portuguese translation must also use `{file_name}`:

```json
{
    "Downloading {file_name}...": "A descarregar {file_name}..."
}
```

### 3. No duplicate keys

JSON does not support duplicate keys. Use the verification script:

```bash
python -c "
import json, re
from collections import Counter
with open('langs/pt_br.json', 'r') as f: content = f.read()
keys = []
for i, line in enumerate(content.splitlines(), 1):
    m = re.match(r'^\s*\"(.+?)\"\s*:', line)
    if m: keys.append((m.group(1), i))
dupes = {k: v for k, v in Counter(k for k, _ in keys).items() if v > 1}
print(f'Duplicates: {dupes}' if dupes else 'No duplicates!')
"
```

---

## How to add a new language

1. Create the JSON file: `langs/{lang_code}.json` (e.g., `langs/es_ES.json`)
2. Add all key-value pairs with English keys and translated values
3. Commit the file — it will be served from `https://raw.githubusercontent.com/natanfiuza/gitpr/main/langs/`
4. The i18n engine auto-downloads it on first use for that locale

---

## Language detection priority

1. **`.env` `GITPR_LANG`** — if set, forces a specific language (e.g., `GITPR_LANG=pt_br`)
2. **OS locale** — auto-detected via `locale.getdefaultlocale()` (e.g., `pt_BR`, `es_ES`)
3. **Fallback** — `"en_us"` (English, no translation file needed)

To force English: set `GITPR_LANG=en` in `~/.gitpr/.env` or unset the variable.

---

## Version control of translations

- `__lang_version__` in `src/updater.py` is incremented when translations change
- On each run, if the local `LANG_VERSION` != `__lang_version__`, the translation file is re-downloaded
- This ensures users always have the latest translations without manual updates

---

## Circular import precautions

The i18n module imports `__lang_version__` from `updater.py`. Therefore:

- **`updater.py`** must NOT import `__` at the top level — use lazy imports inside functions
- **`cache.py`** must NOT import `__` at the top level — use lazy imports inside functions that need it
- Other modules can safely import `__` at the top level

```python
# DO NOT do this in updater.py or cache.py:
from src.i18n import __

# DO this instead (inside the function that needs it):
def some_function():
    from src.i18n import __  # lazy import
    click.secho(__("message"))
```

---

## Documentation URL i18n

The `get_doc_url()` function in `core.py` builds language-aware documentation URLs:

```python
from src.i18n import CURRENT_LANG

def get_doc_url(filename):
    if CURRENT_LANG.startswith("en"):
        return f"https://github.com/.../docs/{filename}"
    else:
        base, ext = filename.rsplit(".", 1)
        return f"https://github.com/.../docs/{base}.{CURRENT_LANG}.{ext}"

# Usage:
get_doc_url("issue-tui-help.md")
# EN → "https://github.com/.../docs/issue-tui-help.md"
# PT → "https://github.com/.../docs/issue-tui-help.pt_br.md"
```

---

## Summary checklist for new features

When adding new user-facing text:

- [ ] Use `__("English text here")` for ALL click.secho, click.echo, click.prompt calls
- [ ] Add the English→Portuguese pair to `langs/pt_br.json`
- [ ] Use `{placeholder}` format with keyword arguments (never f-strings inside `__()`)
- [ ] For string comparisons, use lists of variations in multiple languages (not `__()`)
- [ ] Ensure `updater.py` and `cache.py` use lazy imports of `__`
- [ ] Test with `GITPR_LANG=pt_br` and `GITPR_LANG=en` to verify both languages
- [ ] Increment `__lang_version__` in `updater.py` if translations changed significantly
