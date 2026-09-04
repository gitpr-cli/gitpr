# Completion Report — Map-Reduce diff documentation + i18n

## What was done

Created full documentation for the Map-Reduce diff-chunking feature in all 5 supported languages, wired it into the console output via the existing `get_doc_url()`/`"Understand why:"` i18n pattern, and added a section to both READMEs.

### Documentation

New files, all following the style of the existing `docs/untracked-files.md` (friendly tone, emoji headers, code examples, "Good to know" tips):

| File | Language |
| ---- | -------- |
| docs/map-reduce-diff.md | English (base) |
| docs/map-reduce-diff.pt_br.md | Portuguese (Brazil) |
| docs/map-reduce-diff.pt_pt.md | Portuguese (Portugal) |
| docs/map-reduce-diff.fr_fr.md | French |
| docs/map-reduce-diff.es_es.md | Spanish |

Each explains the 3-stage pipeline (Split → Map → Reduce), the 90k-token threshold, and practical notes (automatic, no flags, rate limiting, smart-excludes, quality trade-off).

### Console output

When the Map-Reduce path activates in `generate_pr_content()` ([core.py:318](src/core.py#L318)), the user now sees a documentation link immediately after the "Huge diff detected" banner:

```text
📦 Huge diff detected! Processing in 4 batches (Map-Reduce)...
📚 Understand why: https://github.com/gitpr-cli/gitpr.git/blob/main/docs/map-reduce-diff.md

⏳ Analyzing batch 1/4...
```

This reuses the existing `__("Understand why:")` i18n key (already present in all 4 language files) and `get_doc_url("map-reduce-diff.md")` (which adds the language suffix automatically), so **no new translation keys** were needed.

### README updates

Both [README.md](README.md) and [README.pt_br.md](README.pt_br.md) gained a new `### 📦 Huge Diffs (Map-Reduce)` subsection under *Advanced Options*, with a brief feature summary and a link to the full docs.

## Changed files

| File | Change type | Description |
| ---- | ----------- | ----------- |
| docs/map-reduce-diff.md | feat | New EN documentation |
| docs/map-reduce-diff.pt_br.md | feat | New PT-BR documentation |
| docs/map-reduce-diff.pt_pt.md | feat | New PT-PT documentation |
| docs/map-reduce-diff.fr_fr.md | feat | New FR documentation |
| docs/map-reduce-diff.es_es.md | feat | New ES documentation |
| src/core.py | feat | `get_doc_url('map-reduce-diff.md')` line after the chunking banner |
| README.md | docs | Map-Reduce section + link |
| README.pt_br.md | docs | Map-Reduce section + link |
| CLAUDE.md | docs | `map-reduce-diff.md` in the docs/ tree |

## Impact

- **Functionality:** Console now shows a documentation link when chunking activates. No other behavior changes.
- **i18n:** Reused the existing `"Understand why:"` key — zero new keys needed across the 4 language JSONs.
- **Performance:** Negligible (one `get_doc_url` call, pure string formatting).

## Verification performed

1. All 5 doc files exist and `get_doc_url("map-reduce-diff.md")` resolves to the correct file for each of the 5 supported languages (`en_us`, `pt_br`, `pt_pt`, `fr_fr`, `es_es`).
2. `python -m pytest tests/ -v` → **33 passed**.
