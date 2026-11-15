# Plan Facts — VS Code Extension `pt-pt` Localization (Etapa 8)

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `vscode_pt_pt_l10n`

## Ficheiros a Criar

1. `extensions/vscode/package.nls.pt-pt.json` — tradução PT-PT das 14 chaves de `extensions/vscode/package.nls.json`.
2. `extensions/vscode/l10n/bundle.l10n.pt-pt.json` — tradução PT-PT das 26 chaves de `extensions/vscode/l10n/bundle.l10n.json`, preservando placeholders `{0}`, `{1}`, `{2}`.

## Ficheiros Intocados

- `extensions/vscode/gitpr-0.1.0.vsix` (não regerar).
- Ficheiros de código-fonte e testes existentes (nenhum novo ficheiro de teste).

## Verificação

1. Script Python validando JSON válido, 100% de igualdade de chaves, igualdade exata de placeholders `{n}` e valores traduzidos em relação ao inglês base.
2. `npm test` dentro de `extensions/vscode/` (`npm run compile && mocha ./out/test/**/*.test.js`).
3. `python -m pytest -v` (se aplicável conforme verificação global).
4. Relatório final obrigatório em `docs/gemini/reports/develop_natan/2026-11-15_vscode_pt_pt_l10n.md`.
