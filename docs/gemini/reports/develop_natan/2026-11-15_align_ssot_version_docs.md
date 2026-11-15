## Completion Report — Align SSOT Version in CLAUDE.md and GEMINI.md

### What was done
- Verified `__version__ = "1.8.0"` in `src/updater.py` (line 12).
- Updated `- **Current version:**` from `1.7.0` to `1.8.0` in `CLAUDE.md` (line 8) and `GEMINI.md` (line 8), preserving surrounding formatting.
- Executed `python -m pytest tests/unit/test_version_consistency.py -v` and confirmed all 5 tests pass (`5 passed in 0.26s`).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `CLAUDE.md` | fix | Updated `Current version` header entry from `1.7.0` to `1.8.0` |
| `GEMINI.md` | fix | Updated `Current version` header entry from `1.7.0` to `1.8.0` |

### Impact
- **Functionality:** Eliminates documentation version drift between `src/updater.py` and project instruction files (`CLAUDE.md`, `GEMINI.md`).
- **Performance:** None.
- **Compatibility:** Fully compatible; satisfies `tests/unit/test_version_consistency.py` without skips or failures.

### Next steps (if applicable)
- Proceed to Etapa 2 in `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` when ready.
