# Plano de Implementação — Etapa 8: Tradução `pt-pt` na Extensão VS Code

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Referência:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (Etapa 8)

## Objetivo

Adicionar cobertura completa de Português Europeu (`pt-pt`) aos bundles de localização da extensão VS Code (`extensions/vscode/`), equiparando-a aos idiomas já existentes (`en`, `pt-br`, `es`, `fr`).

## Alterações Propostas

1. **Criar `extensions/vscode/package.nls.pt-pt.json`**
   - Espelhar as 14 chaves de `extensions/vscode/package.nls.json`.
   - Manter termos técnicos/UI em inglês (`Thin client MCP`, `Code Review`, `Full Review`, `Pull Request`, `Problems`, `Check`) conforme padrão de `package.nls.pt-br.json`, com redação em Português Europeu (`predefinição`, `fornecedor`/`provedor`, `A sua...`).
2. **Criar `extensions/vscode/l10n/bundle.l10n.pt-pt.json`**
   - Espelhar as 26 chaves de `extensions/vscode/l10n/bundle.l10n.json`.
   - Preservar integralmente os placeholders `{0}`, `{1}`, `{2}`.
   - Adotar construções idiomáticas de PT-PT (`A gerar...`, `A executar...`, `A publicar...`, `Controlo de Código-Fonte`, `A sua versão`, `ferramentas MCP em falta`, `Reveja ou edite`).

## Verificação

1. Validação Python de JSON, paridade de chaves (14 e 26 chaves), paridade de placeholders `{n}` e verificação de tradução efetiva face ao inglês.
2. Execução de `npm test` em `extensions/vscode/`.
3. Geração do relatório obrigatório em `docs/gemini/reports/develop_natan/2026-11-15_vscode_pt_pt_l10n.md`.
