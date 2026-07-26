# Plan: MCP Prompts — Template-Based Refactoring

## Context

MCP prompts in `src/mcp_server.py:708-806` are hardcoded Python strings returned via
`__()`. There are 7 prompts, each a `@mcp.prompt()` function with translated name,
description, and body. The user wants prompt content moved to `templates/` files
with 5-language i18n (EN, PT-BR, PT-PT, ES, FR), mirroring how skill resources
already load from `.gitpr.*.md` template files.

## Design

### Template files (35 new + prompt resource = 36+ new files)

Naming: `gitpr.prompt.<name>.md` (EN base), `gitpr.prompt.<name>.<lang>.md` (other langs).

**7 prompts to externalize (already exist as hardcoded strings):**

| Prompt key | Template file             | Current name              |
| ---------- | ------------------------- | ------------------------- |
| `review`   | `gitpr.prompt.review.md`  | "Review PR"               |
| `commit`   | `gitpr.prompt.commit.md`  | "Generate Commit Message" |
| `pr`       | `gitpr.prompt.pr.md`      | "Create PR Description"   |
| `linter`   | `gitpr.prompt.linter.md`  | "Run Code Linter"         |
| `issue`    | `gitpr.prompt.issue.md`   | "Create Issue from Diff"  |
| `blame`    | `gitpr.prompt.blame.md`   | "Trace Code Origin"       |
| `explore`  | `gitpr.prompt.explore.md` | "Explore Project Context" |

### New loading mechanism in `src/mcp_server.py`

Model after existing `_read_resource_file()` (lines 596-613) and `SKILL_FILES` (lines 586-593):

```python
# New: prompt template file mapping
PROMPT_FILES = {
    "review": "gitpr.prompt.review.md",
    "commit": "gitpr.prompt.commit.md",
    "pr": "gitpr.prompt.pr.md",
    "linter": "gitpr.prompt.linter.md",
    "issue": "gitpr.prompt.issue.md",
    "blame": "gitpr.prompt.blame.md",
    "explore": "gitpr.prompt.explore.md",
}

def _read_prompt_file(prompt_name):
    """Loads prompt content from a template file with language fallback.

    Tries <lang> variant first (e.g. gitpr.prompt.review.pt_br.md),
    falls back to the English base file (gitpr.prompt.review.md).
    """
    base_filename = PROMPT_FILES.get(prompt_name)
    if not base_filename:
        return ""

    # Build language-specific filename
    if not CURRENT_LANG.startswith("en"):
        name_part, ext = base_filename.rsplit(".", 1)
        lang_filename = f"{name_part}.{CURRENT_LANG}.{ext}"
    else:
        lang_filename = base_filename

    # Search: project templates/ first, then the GitPR global config
    from src.config import resolve_skill_path  # reuse existing resolver
    path = resolve_skill_path(lang_filename)
    if path:
        return path.read_text(encoding="utf-8", errors="replace").strip()

    # Fallback to English base
    path = resolve_skill_path(base_filename)
    if path:
        return path.read_text(encoding="utf-8", errors="replace").strip()

    return ""
```

### Refactored prompt functions

Each prompt function changes from returning `__("hardcoded text...")` to
`_read_prompt_file("key")`. The `name=` and `description=` stay as `__()`
wrappers (they're UI metadata displayed in the editor).

Example:
```python
@mcp.prompt(
    name=__("Review PR"),
    description=__(...),
)
def review_pr_prompt() -> str:
    return _read_prompt_file("review")
```

### New resource: `prompt://list`

Add a resource listing all available prompt template files (similar to `skill://list`),
exposing prompt template URIs like `prompt://review`, `prompt://commit`, etc.
Each prompt resource returns the same content as the prompt function.

## Implementation Steps (following /new-feature skill)

### Step 1 — Read context reports
- Check `docs/reports/relatorio_estado_v0.0.*.md` for current state

### Step 2 — Create 35 prompt template files
- Write 7 EN base templates with the current prompt body text (extracted from mcp_server.py)
- Write 28 translated variants (PT-BR, PT-PT, ES, FR for each of 7 prompts)
- Each file is a single block of text (no YAML frontmatter, just the prompt message)

### Step 3 — Modify `src/mcp_server.py`
- Add `PROMPT_FILES` dict (after existing `SKILL_FILES`)
- Add `_read_prompt_file()` function (after existing `_read_resource_file()`)
- Refactor 7 prompt functions to call `_read_prompt_file()`
- Add `prompt://list` resource
- Add `prompt://<name>` resources for each prompt
- Update the MCP server instructions string if needed

### Step 4 — i18n keys (`langs/*.json`)
- Prompt name and description keys already exist in all 4 language files
- No new `__()` calls needed — the body text is now loaded from files, not `__()`
- Check that all existing prompt-related keys are present in all 4 files

### Step 5 — Documentation (`docs/`)
- Update `docs/mcp-prompts.md` (EN) documenting the new template system
- Create/update `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md` variants
- Use `get_doc_url()` for cross-references

### Step 6 — README update (all 5 variants)
- Add mention of MCP prompts in "Advanced Options" section
- Add link to `docs/mcp-prompts.md` in "Technical Documentation" section

### Step 7 — Tests (`tests/test_mcp_prompts.py`)
- Update existing tests: mock `_read_prompt_file()` instead of checking hardcoded strings
- Add test for `_read_prompt_file()` with language fallback
- Add test for `PROMPT_FILES` dict completeness
- Add test that all prompt functions return non-empty strings

### Step 8 — Verification
1. `pipenv run pytest tests/test_mcp_prompts.py -v` → all pass
2. `pipenv run pytest tests/ -v` → no regressions
3. Each of 5 languages has all 7 prompt templates (35 files total)
4. Prompt content is readable and matches the original hardcoded text
5. `gitpr --mcp` starts without errors (smoke test)

## Files summary

| Action | Count | Pattern                                                      |
| ------ | ----- | ------------------------------------------------------------ |
| NEW    | 35    | `templates/gitpr.prompt.<name>.{lang}.md`                    |
| MODIFY | 1     | `src/mcp_server.py`                                          |
| CHECK  | 4     | `langs/pt_br.json`, `pt_pt.json`, `es_es.json`, `fr_fr.json` |
| UPDATE | 10    | `docs/mcp-prompts*.md` (5) + `README*.md` (5)                |
| MODIFY | 1     | `tests/test_mcp_prompts.py`                                  |
