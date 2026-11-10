# Survey Facts — Tradução do Marketplace Publishing Guide

**Data:** 2026-11-10  
**Branch:** `develop_natan`  
**Identificador da Tarefa:** `translate_marketplace_publishing_guide`  

---

## 1. Contexto da Tarefa
- O arquivo `docs/marketplace-publishing-guide.md` foi introduzido para documentar passo a passo a publicação automatizada e configuração de publishers e tokens (`VSCE_PAT`, `OVSX_PAT`) para a extensão do GitPR para VS Code e Cursor.
- Até o momento, o guia existia exclusivamente em inglês (`.md`), constando como um dos 2 tópicos com cobertura parcial em `docs/reports/relatorio_estado_v0.0.24.md` (junto a `github-issue-prompt-com-gh.md`).
- A tarefa consiste em traduzir o guia para os 4 idiomas adicionais suportados pelo ecossistema GitPR:
  - Português do Brasil (`pt_br`): `docs/marketplace-publishing-guide.pt_br.md`
  - Português de Portugal (`pt_pt`): `docs/marketplace-publishing-guide.pt_pt.md`
  - Espanhol (`es_es`): `docs/marketplace-publishing-guide.es_es.md`
  - Francês (`fr_fr`): `docs/marketplace-publishing-guide.fr_fr.md`
- Além disso, atualizar os links relativos em `docs/editor-extension.*.md` para apontarem para suas respectivas versões localizadas e criar teste unitário de paridade.

---

## 2. Decisões do Alinhamento (Grill Frontier)

| Decisão | Pergunta / Fronteira | Decisão Selecionada |
|---------|-----------------------|---------------------|
| **Q1** | Links cruzados em `docs/editor-extension.*.md` | Atualizar os 4 arquivos (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) para apontarem para `marketplace-publishing-guide.<lang>.md`. |
| **Q2** | Teste de paridade documental automatizado | Criar `tests/unit/test_marketplace_publishing_guide_docs_parity.py` validando existência dos 5 arquivos, seções/cabeçalhos, identificadores técnicos e links de `docs/editor-extension.*.md`. |
| **Q3** | Convenção de tradução de termos técnicos e de portais | Manter literais segredos (`VSCE_PAT`, `OVSX_PAT`), tags (`ext-v*`), flags, comandos CLI, arquivos (`package.json`, `.vsix`) e escopos/rótulos oficiais dos portais (`Acquire`, `Manage`, `Create publisher`), vertendo com naturalidade o texto em prosa. |
| **Q4** | Promoção de status documental | Formalizar a promoção do tópico de parcial para completo nos 5 idiomas nos artefatos de planejamento (`plansfacts`, `surveyfacts`, relatórios), mantendo o relatório histórico `relatorio_estado_v0.0.24.md` intacto como registro fechado. |

---

## 3. Fatos Técnicos Levantados
1. **Estrutura Canônica do Documento Original (`docs/marketplace-publishing-guide.md`):**
   - 128 linhas, 6 seções principais numeradas:
     - Título principal e subtítulo introdutório
     - `## Overview` (Visão Geral / Aperçu)
     - `## 1. Visual Studio Marketplace Setup (Microsoft / VS Code)`
       - `### Step 1.1: Azure DevOps Organization`
       - `### Step 1.2: Generate Personal Access Token (PAT)`
       - `### Step 1.3: Create Visual Studio Marketplace Publisher`
       - `### Step 1.4: Add Secret to GitHub`
     - `## 2. Open VSX Registry Setup (Eclipse Foundation / Cursor)`
       - `### Step 2.1: Create Account`
       - `### Step 2.2: Register the Namespace`
       - `### Step 2.3: Generate Access Token`
       - `### Step 2.4: Add Secret to GitHub`
     - `## 3. Local Verification & Dry-Run (Optional)`
       - `### Verify PATs with CLIs`
       - `### Local Packaging Test`
     - `## 4. Triggering the Automated Release`
     - `## 5. Maintenance & Future Releases`
2. **Links Referenciadores Atuais:**
   - `docs/editor-extension.pt_br.md:58` -> `[Guia de Publicação nos Marketplaces](marketplace-publishing-guide.md)`
   - `docs/editor-extension.pt_pt.md:58` -> `[Guia de Publicação nos Marketplaces](marketplace-publishing-guide.md)`
   - `docs/editor-extension.es_es.md:58` -> `[Guía de Publicación en Marketplaces](marketplace-publishing-guide.md)`
   - `docs/editor-extension.fr_fr.md:58` -> `[Guide de publication sur les marketplaces](marketplace-publishing-guide.md)`
3. **Padrão de Testes Unitários de Paridade:**
   - `tests/unit/test_scm_multiforge_docs_parity.py` e `tests/unit/test_check_ci_docs_parity.py` utilizam `Path(__file__).resolve().parent.parent.parent` e asserções direcionadas em Python puro com `pytest`.
