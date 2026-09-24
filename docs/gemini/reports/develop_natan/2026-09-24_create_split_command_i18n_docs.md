## Completion Report — Criação dos Documentos do Comando Split nos Idiomas Suportados

### What was done
- Created technical documentation for `gitpr split` across all remaining supported languages:
  - `docs/split-command.pt_pt.md` (Português de Portugal)
  - `docs/split-command.es_es.md` (Espanhol)
  - `docs/split-command.fr_fr.md` (Francês)
- Updated documentation links in `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, and `README.fr_fr.md` to reference their localized documentation pages.
- Verified all 101 tests in `tests/split/` with 100% success.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/split-command.pt_pt.md` | feat (docs) | Technical documentation of `gitpr split` in European Portuguese |
| `docs/split-command.es_es.md` | feat (docs) | Technical documentation of `gitpr split` in Spanish |
| `docs/split-command.fr_fr.md` | feat (docs) | Technical documentation of `gitpr split` in French |
| `README.pt_br.md` | docs | Updated detailed documentation link to `docs/split-command.pt_br.md` |
| `README.pt_pt.md` | docs | Updated catalog and documentation links to `docs/split-command.pt_pt.md` |
| `README.es_es.md` | docs | Updated catalog and documentation links to `docs/split-command.es_es.md` |
| `README.fr_fr.md` | docs | Updated catalog and documentation links to `docs/split-command.fr_fr.md` |

### Impact
- **Functionality:** Users executing `gitpr split -h` or navigating documentation in PT-PT, ES-ES, and FR-FR locales now have complete localized documentation matching the canonical English and PT-BR versions.
- **Performance:** No runtime or performance impact (documentation only).
- **Compatibility:** 100% backward-compatible.

### Next steps (if applicable)
- None. Full 5-language parity achieved for `split-command`.
