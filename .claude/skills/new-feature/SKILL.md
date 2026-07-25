---
name: new-feature
description: >-
  Workflow especializado para implementar novas funcionalidades no GitPR CLI.
  Abrange documentação multi-idioma, i18n, READMEs, docs técnicos, instalação de
  dependências e relatórios. Use esta skill sempre que for adicionar um novo
  comando, flag, módulo ou capacidade ao GitPR.
---

# New Feature Implementation Workflow

This skill defines the mandatory workflow for implementing new features in the
GitPR CLI project. Follow these steps in order when building a new flag, command,
module, or capability.

## Step 1 — Read Context Reports

Read the latest status reports in `docs/reports/` to understand the current
project state, recent changes, and architectural decisions:

```
docs/reports/relatorio_estado_v0.0.*.md
```

Also check `docs/claude-code/reports/develop_natan/` for task-specific reports
that may be relevant to the feature being implemented. This provides continuity
across development sessions and ensures you don't duplicate or contradict
previous work.

## Step 2 — Technical Documentation (`docs/`)

Create a **dedicated technical documentation file** for the new feature:

- **English base:** `docs/<feature-name>.md` — the primary reference
- **All supported languages:** create `.pt_br.md`, `.pt_pt.md`, `.es_es.md`,
  `.fr_fr.md` variants
- Follow the structure of existing docs (e.g., `docs/mcp-integration.md`,
  `docs/install-wizard.md`): purpose, prerequisites, usage, step-by-step,
  links to related docs

When the documentation references other doc pages, **use the `get_doc_url()`
function** from `src/core.py` to build URLs dynamically — this ensures the links
point to the official documentation website (`https://gitpr.natanfiuza.dev.br/docs/`)
with proper language handling via the `?lang=` query parameter:

```python
from src.core import get_doc_url
url = get_doc_url('commit-message-ia.md')  # language-aware URL
```

At the end of the feature execution (e.g., after a setup wizard or success
message), display the documentation URL to the user:

```python
click.secho(f"  {get_doc_url('install-wizard.md')}", fg="blue", underline=True)
```

## Step 3 — README Update (All Languages)

Add the new feature to **every** README variant:

| File | Language |
|---|---|
| `README.md` | English |
| `README.pt_br.md` | Portuguese (Brazil) |
| `README.pt_pt.md` | Portuguese (Portugal) |
| `README.es_es.md` | Spanish |
| `README.fr_fr.md` | French |

Two changes per README:

1. **"Advanced Options and Commands" section** — add a new bullet describing the
   flag/command. Match the existing style: `* \`--flag\` or \`-f\`: **Bold title.**
   Description of what it does.`
2. **"Technical Documentation and Advanced Guides" section** — add a link to the
   new doc file in the appropriate subsection, using the GitHub blob URL format
   (the README is static markdown and does not use `get_doc_url()`).

## Step 4 — Dependencies

If the feature introduces a **new third-party library**:

1. Add it to `pyproject.toml` under `[project] dependencies` (or
   `[project.optional-dependencies]` if optional)
2. Add it to `Pipfile` for the dev environment
3. Run the installation:
   ```bash
   pipenv install --dev
   ```
   Or for a single package:
   ```bash
   pipenv install <package-name>
   ```

Verify the import works before proceeding:
```bash
pipenv run python -c "import <package>; print('OK')"
```

## Step 5 — Internationalization (i18n)

Every user-facing message **must** be wrapped with the `__()` translation
function:

```python
from src.i18n import __

click.secho(__("✅ Feature successfully configured!"), fg="green", bold=True)
click.echo(__("The {feature} will now run automatically.", feature="Linter"))
```

After adding new `__(...)` calls, populate the translation keys in **all four**
language JSON files:

| File | Language |
|---|---|
| `langs/pt_br.json` | Portuguese (Brazil) |
| `langs/pt_pt.json` | Portuguese (Portugal) |
| `langs/es_es.json` | Spanish |
| `langs/fr_fr.json` | French |

Keys are the **exact English string**; values are the localized translation.
Placeholders use `{name}` syntax (Python `str.format`). Insert new entries
alphabetically or grouped logically with related keys. Ensure valid JSON after
editing (no trailing commas on the last item before `}`).

Refer to existing translations for terminology consistency:
- PT-BR: "arquivo", "baixar", "hooks", "template"
- PT-PT: "ficheiro", "descarregar", "hooks", "template"
- ES: "archivo", "descargar", "hooks", "plantilla"
- FR: "fichier", "télécharger", "hooks", "template"

## Step 6 — Documentation URL Display

When the feature execution completes, **display the technical documentation URL**
using `get_doc_url()`:

```python
click.echo(__("For more details, see the full documentation:"))
click.secho(f"  {get_doc_url('my-new-feature.md')}", fg="blue", underline=True)
```

This ensures users can find the full guide after running the feature for the
first time.

## Step 7 — HELP_MAP and HELP_PRIORITY

If the new feature is a CLI flag, add entries to both `HELP_MAP` and
`HELP_PRIORITY` in `src/main.py`:

```python
# HELP_MAP — maps flag name to doc URL, title, and description
'myflag': {
    'url': get_doc_url('my-new-feature.md'),
    'title': __('My New Feature (--myflag)'),
    'description': __('Brief description of what the feature does.'),
},

# HELP_PRIORITY — lower number = higher priority for contextual help
'myflag': 14,
```

This enables `gitpr -h --myflag` to display contextual help with a direct link
to the full documentation.

## Step 8 — Tests

Write tests in `tests/` following the project's `unittest` + `unittest.mock`
pattern:

```python
import unittest
from unittest.mock import patch

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        # Common mocks
        ...

    @patch("src.core.some_dependency")
    def test_happy_path(self, mock_dep):
        """Feature works correctly under normal conditions."""
        ...

if __name__ == "__main__":
    unittest.main()
```

Run the tests to verify:
```bash
pipenv run python -m pytest tests/test_my_feature.py -v
```

## Step 9 — Final Verification

Before considering the feature complete:

1. **All tests pass:** `pipenv run pytest tests/ -v`
2. **Import check:** `pipenv run python -c "from src.main import cli; print('CLI OK')"`
3. **Help works:** `pipenv run python run.py -h --<newflag>` displays contextual help
4. **i18n coverage:** all new `__()` calls have entries in all 4 language files
5. **Docs exist:** all 5 language variants of the documentation file are present
