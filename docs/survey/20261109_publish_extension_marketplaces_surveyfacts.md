# Survey de Fatos — Publicação da Extensão GitPR (VSIX & Marketplaces)

**Data:** 2026-11-09  
**Branch:** `develop_natan`  
**Task:** `publish_extension_marketplaces`  
**Responsáveis:** Natan Fiuza, Antigravity

---

## 1. Contexto e Motivação da Tarefa

A extensão GitPR para VS Code e Cursor (`extensions/vscode`) foi desenvolvida como um *thin client* MCP sobre `gitpr-mcp` (stdio), com testes unitários mocha, metadados (`package.json`), ícone oficial de 256x256 e licença LGPL-2.1.

No entanto, o item permaneceu aberto como **item herdado** devido ao seguinte bloqueio:
- O workflow `.github/workflows/extension.yml` implementava um **fail-fast secret check** bloqueante: na ausência de `VSCE_PAT` ou `OVSX_PAT`, o job abortava com erro fatal (`missing=1; exit 1`).
- O pacote `.vsix` gerado ficava restrito a artifacts de CI de 90 dias, sem ser anexado a nenhum **GitHub Release** oficial na tag `ext-v*`.
- Usuários finais e desenvolvedores não dispunham de um local permanente para baixar o VSIX pré-compilado, necessitando compilar via npm localmente.
- O cadastro de contas e PATs no Visual Studio Marketplace (Azure DevOps) e Open VSX depende de ações humanas em portais externos.

---

## 2. Levantamento de Fatos Técnicos

| Componente | Fato Levantado | Situação Atual |
|------------|----------------|----------------|
| **VSIX Packaging** | `npm run package` em `extensions/vscode` produz `gitpr-0.1.0.vsix` (~92 KB) contendo 34 arquivos, sem warnings. | Validado e funcional. |
| **Testes da Extensão** | Testes mocha em `extensions/vscode/src/test/` cobrem o cliente MCP e sanitização de segredos. | Aprovados (7 passing). |
| **Pipeline de CI (`extension.yml`)** | Disparado em PRs, tags `ext-v*` e `workflow_dispatch`. Bloqueia se `VSCE_PAT` ou `OVSX_PAT` faltarem. | Requer desacoplamento. |
| **GitHub Releases** | `release.yml` (Python) usa `softprops/action-gh-release@v2` para anexar wheels e sdist. `extension.yml` não possui job de GitHub Release. | Faltava paridade de release. |
| **Tokens e Segredos** | `VSCE_PAT` e `OVSX_PAT` ainda não configurados nos secrets do repositório GitHub. | Requer tratamento granular não-bloqueante. |
| **Glossário (`CONTEXT.md`)** | O termo `Fail-fast secret check` previa abortar em erro fatal. | Deve ser substituído por `Granular marketplace gate`. |
| **Documentação de Instalação** | `docs/editor-extension.md` (e 4 traduções) não explicavam download direto via GitHub Releases nem comandos de 1 clique para Cursor. | Precisa de atualização em 5 idiomas. |

---

## 3. Decisões Consolidadas da Sessão de Grill

### Rodada 1
- **Q1 (Escopo):** Desacoplar e viabilizar a distribuição por VSIX oficial via GitHub Releases + suporte progressivo aos marketplaces.
- **Q2 (Comportamento CI/CD):** Publicação granular e resiliente: o GitHub Release com o `.vsix` sempre é criado na tag `ext-v*`. A publicação em cada marketplace ocorre se o token respectivo existir, emitindo notice informativa se faltar.
- **Q3 (Instalação Local):** Instruções de 1 clique via CLI (`code --install-extension` / `cursor --install-extension`) e menu GUI ("Install from VSIX...") documentadas em 5 idiomas e no README.
- **Q4 (Tag inicial):** Preparar todo o ecossistema para viabilizar a tag `ext-v0.1.0`.

### Rodada 2
- **Q5 (Estrutura de Jobs):** Separar em jobs dedicados: `github-release` (cria release no GitHub e anexa `.vsix` permanentemente) e `publish-marketplaces` (tenta publicar no VS Code Marketplace e Open VSX, gerando tabela de resumo no `$GITHUB_STEP_SUMMARY`).
- **Q6 (Modelo de Domínio):** Substituir `Fail-fast secret check` por `Granular marketplace gate` em `CONTEXT.md`.
- **Q7 (Cobertura de Docs):** Atualizar `docs/editor-extension.md` e suas 4 traduções (`pt_br`, `pt_pt`, `es_es`, `fr_fr`), `README.md` e `docs/marketplace-publishing-guide.md`.
