# Plans Facts — Tradução do Marketplace Publishing Guide

**Data:** 2026-11-10  
**Branch:** `develop_natan`  
**Identificador da Tarefa:** `translate_marketplace_publishing_guide`  

---

## 1. Escopo e Objetivos
- Traduzir `docs/marketplace-publishing-guide.md` para os 4 idiomas suportados pelo GitPR:
  - `docs/marketplace-publishing-guide.pt_br.md` (Português - Brasil)
  - `docs/marketplace-publishing-guide.pt_pt.md` (Português - Portugal)
  - `docs/marketplace-publishing-guide.es_es.md` (Espanhol)
  - `docs/marketplace-publishing-guide.fr_fr.md` (Francês)
- Atualizar os links de referência na linha 58 de `docs/editor-extension.*.md` em `pt_br`, `pt_pt`, `es_es` e `fr_fr` para apontar diretamente para os respectivos arquivos traduzidos.
- Implementar suite de testes de paridade documental automatizada em `tests/unit/test_marketplace_publishing_guide_docs_parity.py`.
- Promover a contagem de cobertura da documentação do GitPR para 51 tópicos com 100% de cobertura nos 5 idiomas (restando apenas 1 tópico parcial).

---

## 2. Ordem de Execução

1. **Criação das Traduções em `docs/`:**
   - Criar `docs/marketplace-publishing-guide.pt_br.md` preservando blocos de código, comandos bash (`npx @vscode/vsce`, `npx ovsx`), nomes de segredos (`VSCE_PAT`, `OVSX_PAT`), tags (`ext-v*`) e estrutura de seções.
   - Criar `docs/marketplace-publishing-guide.pt_pt.md` com ortografia e terminologia natural em Português de Portugal.
   - Criar `docs/marketplace-publishing-guide.es_es.md` com redação técnica fluida em Espanhol da Espanha.
   - Criar `docs/marketplace-publishing-guide.fr_fr.md` com redação técnica fluida em Francês da França.

2. **Atualização de Links Cruzados em `docs/editor-extension.*.md`:**
   - Em `docs/editor-extension.pt_br.md`: `(marketplace-publishing-guide.md)` -> `(marketplace-publishing-guide.pt_br.md)`.
   - Em `docs/editor-extension.pt_pt.md`: `(marketplace-publishing-guide.md)` -> `(marketplace-publishing-guide.pt_pt.md)`.
   - Em `docs/editor-extension.es_es.md`: `(marketplace-publishing-guide.md)` -> `(marketplace-publishing-guide.es_es.md)`.
   - Em `docs/editor-extension.fr_fr.md`: `(marketplace-publishing-guide.md)` -> `(marketplace-publishing-guide.fr_fr.md)`.

3. **Criação do Teste de Paridade:**
   - Criar `tests/unit/test_marketplace_publishing_guide_docs_parity.py` validando:
     - Existência dos 5 arquivos (`.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`).
     - Presença de todos os cabeçalhos de seção e subseções (`## Overview`, `## 1.`, `## 2.`, `## 3.`, `## 4.`, `## 5.`).
     - Presença dos comandos e segredos canônicos (`VSCE_PAT`, `OVSX_PAT`, `ext-v*`, `@vscode/vsce`, `ovsx`, `package.json`, `.vsix`).
     - Presença dos links atualizados em `docs/editor-extension.*.md`.

4. **Verificação Automatizada:**
   - Executar `pytest tests/unit/test_marketplace_publishing_guide_docs_parity.py -v`.
   - Executar a suíte de testes de documentação existente (`pytest tests/test_doc_links.py -v`).

5. **Relatórios Finais:**
   - Gerar `docs/gemini/reports/develop_natan/2026-11-10_translate_marketplace_publishing_guide.md`.
   - Gerar `docs/gemini/walkthrough/develop_natan/2026-11-10_translate_marketplace_publishing_guide.md`.
