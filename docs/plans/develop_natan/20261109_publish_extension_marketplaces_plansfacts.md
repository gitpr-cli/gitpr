# Plano de Execução — Publicação da Extensão GitPR (VSIX & Marketplaces)

**Data:** 2026-11-09  
**Branch:** `develop_natan`  
**Task:** `publish_extension_marketplaces`  
**Referência Survey:** `docs/survey/20261109_publish_extension_marketplaces_surveyfacts.md`

---

## 1. Objetivos

1. **Desacoplar a distribuição do VSIX**: Garantir que o workflow de release da extensão (`.github/workflows/extension.yml`) crie um GitHub Release oficial na tag `ext-v*` com o arquivo `.vsix` anexado como asset permanente para download de qualquer usuário, sem depender de secrets de marketplace.
2. **Implementar o Granular Marketplace Gate**: Permitir que a publicação nos marketplaces (VS Code Marketplace e Open VSX) ocorra de forma granular e independente:
   - Se `VSCE_PAT` estiver presente: publica no VS Code Marketplace via `@vscode/vsce publish`. Se ausente: emite aviso informativo (notice) e registra no `$GITHUB_STEP_SUMMARY`.
   - Se `OVSX_PAT` estiver presente: publica no Open VSX via `ovsx publish`. Se ausente: emite aviso informativo (notice) e registra no `$GITHUB_STEP_SUMMARY`.
   - Em nenhum cenário a ausência de um token falha o release do GitHub ou impede o deploy no outro marketplace.
3. **Atualizar o Glossário de Domínio (`CONTEXT.md`)**:
   - Substituir o termo legado `Fail-fast secret check` pelo conceito canônico `Granular marketplace gate`.
4. **Atualizar Documentações em 5 Idiomas**:
   - `docs/editor-extension.md` (EN) e traduções (`pt_br`, `pt_pt`, `es_es`, `fr_fr`): adicionar instruções claras de download do VSIX pré-compilado nos GitHub Releases e comandos de instalação via CLI (`code --install-extension <arquivo.vsix>`, `cursor --install-extension <arquivo.vsix>`) e GUI.
   - `README.md`: incluir seção direta sobre a instalação da extensão via VSIX do GitHub Releases.
   - `docs/marketplace-publishing-guide.md`: documentar a ativação incremental dos segredos de repositório.

---

## 2. Detalhamento das Alterações

### A. CI/CD (`.github/workflows/extension.yml`)
- Manter o job `build-and-test` que valida a tag vs `package.json`, instala o CLI editable, compila TypeScript, roda os testes e empacota o VSIX.
- Criar o job `github-release`:
  - `needs: build-and-test`
  - `if: startsWith(github.ref, 'refs/tags/ext-v')`
  - `permissions: contents: write`
  - Faz download do artifact `gitpr-vscode-vsix` e executa `softprops/action-gh-release@v2` anexando `extensions/vscode/*.vsix`.
- Atualizar o job `publish-marketplaces` (renomeado de `publish`):
  - `needs: build-and-test`
  - `if: startsWith(github.ref, 'refs/tags/ext-v') || (github.event_name == 'workflow_dispatch' && !inputs.dry_run)`
  - `permissions: contents: read`
  - Avalia individualmente `VSCE_PAT` e `OVSX_PAT`:
    - Publica no VS Code se `VSCE_PAT` estiver preenchido, ou emite notice e marca como skipped.
    - Publica no Open VSX se `OVSX_PAT` estiver preenchido, ou emite notice e marca como skipped.
  - Gera tabela formatada no `$GITHUB_STEP_SUMMARY` com o status de cada marketplace.

### B. Modelo de Domínio (`CONTEXT.md`)
- Remover a definição de `Fail-fast secret check`.
- Adicionar o termo `Granular marketplace gate`:
  ```markdown
  **Granular marketplace gate**:
  The non-blocking credential evaluation mechanism in the marketplace publication workflow
  that checks each marketplace secret (VSCE_PAT, OVSX_PAT) independently. It publishes to
  services with active tokens while emitting informative step notices and summary status
  for missing credentials, ensuring official VSIX GitHub Releases are never obstructed by
  absent third-party marketplace tokens.
  _Avoid_: fail-fast secret check, all-or-nothing check, blocking token validation
  ```

### C. Documentação (`docs/` e `README.md`)
- Adicionar nos guias de extensão instruções completas de instalação por VSIX em VS Code e Cursor.
- Atualizar o guia de publicação nos marketplaces com a visão granular.
- Adicionar link no README para download direto do release da extensão.

---

## 3. Validação e Testes

1. **Validação do Workflow YAML**:
   - Verificar sintaxe do arquivo `.github/workflows/extension.yml`.
2. **Empacotamento VSIX Local**:
   - Rodar `npm run compile && npm test && npm run package` em `extensions/vscode` para confirmar geração limpa do VSIX.
3. **Suite de Testes Python**:
   - Rodar `pytest tests/ -v` para assegurar que nada foi quebrado no core e nos testes de MCP.
