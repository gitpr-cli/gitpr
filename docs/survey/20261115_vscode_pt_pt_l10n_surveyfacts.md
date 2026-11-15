# Survey Facts — VS Code Extension `pt-pt` Localization (Etapa 8)

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Origem:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (Etapa 8, linhas 214–232)

## Contexto da Tarefa

A extensão VS Code em `extensions/vscode/` já possui localização para inglês (`en`, base), português do Brasil (`pt-br`), espanhol (`es`) e francês (`fr`), mas ainda não possui os ficheiros de localização para português europeu (`pt-pt`). A Etapa 8 consiste em criar `extensions/vscode/package.nls.pt-pt.json` (14 chaves) e `extensions/vscode/l10n/bundle.l10n.pt-pt.json` (26 chaves) com 100% de paridade de chaves e placeholders `{n}`.

## Fatos Levantados no Repositório

1. **Estrutura de localização existente em `extensions/vscode/`:**
   - Manifesto: `extensions/vscode/package.nls.json` (14 chaves) e `package.nls.{pt-br,es,fr}.json`.
   - Runtime (`vscode.l10n.t`): `extensions/vscode/l10n/bundle.l10n.json` (26 chaves) e `bundle.l10n.{pt-br,es,fr}.json`.
   - `extensions/vscode/package.json` define `"l10n": "./l10n"` e scripts `"compile"`, `"watch"`, `"test"` (`npm run compile && mocha ./out/test/**/*.test.js`) e `"package"`.
2. **Convenções PT-PT no projeto:**
   - `langs/pt_pt.json` adota formas progressivas com `"A <infinitivo>..."` (`"A iniciar..."`, `"A consultar..."`), léxico europeu (`"predefinições"`, `"executar"`, `"descarregado"`, `"ficheiro"`, `"em falta"`).
3. **Artefacto `.vsix` existente:**
   - `extensions/vscode/gitpr-0.1.0.vsix` está presente localmente na pasta da extensão.

## Decisões Confirmadas na Sessão de Grill

- **Q1 (Terminologia PT-PT):** Manter os termos técnicos/UI em inglês tal como em `pt-br` (`Thin client MCP`, `Code Review`, `Full Review`, `Pull Request`, `Problems`, `workspace`), adaptando toda a gramática e léxico envolvente para português europeu natural (`A gerar...`, `A executar...`, `Controlo de Código-Fonte`, `A sua versão`, `predefinição`, `em falta`).
- **Q2 (Testes):** Executar a validação pontual em Python (paridade de chaves, placeholders `{0}`/`{1}`/`{2}`, valores distintos do inglês) e `npm test` em `extensions/vscode/`, sem adicionar novos ficheiros de teste permanentes.
- **Q3 (Empacotamento):** Não alterar nem regerar `extensions/vscode/gitpr-0.1.0.vsix`.
