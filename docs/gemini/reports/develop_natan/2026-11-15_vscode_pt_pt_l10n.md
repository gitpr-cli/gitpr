## Completion Report — Etapa 8: Tradução `pt-pt` na Extensão VS Code

### What was done
- Created `extensions/vscode/package.nls.pt-pt.json` with European Portuguese (`pt-pt`) translations for all 14 manifest keys from `extensions/vscode/package.nls.json`.
- Created `extensions/vscode/l10n/bundle.l10n.pt-pt.json` with European Portuguese (`pt-pt`) translations for all 26 runtime localization keys from `extensions/vscode/l10n/bundle.l10n.json`, preserving `{0}`, `{1}`, and `{2}` placeholders.
- Validated 100% key parity, placeholder parity (`{n}`), and non-English translated values via Python.
- Executed `npm --prefix extensions/vscode test` (`tsc -p ./` + Mocha): all 7 tests passed.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `extensions/vscode/package.nls.pt-pt.json` | feat | Added PT-PT localization for the 14 VS Code extension manifest strings |
| `extensions/vscode/l10n/bundle.l10n.pt-pt.json` | feat | Added PT-PT localization for the 26 VS Code extension runtime strings |

### Impact
- **Functionality:** Users running VS Code in European Portuguese (`pt-pt`) now receive localized command titles, configuration descriptions, prompts, notifications, and status messages instead of falling back to English.
- **Performance:** None (static JSON localization bundles).
- **Compatibility:** Fully backwards-compatible; `extensions/vscode/gitpr-0.1.0.vsix` was left untouched for the release packaging workflow.

### Next steps (if applicable)
- Run the global Python test suite (`python -m pytest -v`) when concluding all stages of `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md`.
