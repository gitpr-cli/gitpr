# Walkthrough — Etapa 8: Tradução `pt-pt` na Extensão VS Code

## Changes Made
- Added [package.nls.pt-pt.json](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/extensions/vscode/package.nls.pt-pt.json) with all 14 manifest keys translated to European Portuguese (`pt-pt`).
- Added [bundle.l10n.pt-pt.json](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/extensions/vscode/l10n/bundle.l10n.pt-pt.json) with all 26 runtime strings translated to European Portuguese (`pt-pt`), preserving `{0}`, `{1}`, and `{2}` placeholders.

## What Was Tested & Validation Results
1. **Python l10n parity & placeholder check:**
   - Verified 100% key parity (14 keys in `package.nls.pt-pt.json`, 26 keys in `l10n/bundle.l10n.pt-pt.json`), exact `{n}` placeholder matching, and non-English translated values (`VS Code pt-pt l10n parity & placeholders OK`).
2. **VS Code Extension Test Suite (`npm --prefix extensions/vscode test`):**
   - TypeScript compilation (`tsc -p ./`) succeeded with 0 errors.
   - Mocha suite passed: `7 passing (13s)`.
