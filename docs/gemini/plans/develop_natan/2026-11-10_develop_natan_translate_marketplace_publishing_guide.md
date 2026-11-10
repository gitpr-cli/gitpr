# Implementation Plan — Tradução do Marketplace Publishing Guide para 5 Idiomas

Traduzir o tópico `docs/marketplace-publishing-guide.md` (atualmente disponível apenas em inglês) para **Português do Brasil (`pt_br`)**, **Português de Portugal (`pt_pt`)**, **Espanhol (`es_es`)** e **Francês (`fr_fr`)**, atualizar os links relativos em `docs/editor-extension.*.md` e adicionar teste unitário de paridade documental.

## User Review Required

> [!NOTE]
> Todas as 4 questões da fronteira de design foram aprovadas pelo usuário (Q1: recomendado, Q2: recomendado, Q3: recomendado, Q4: recomendado).
> Não há alterações de código em tempo de execução nem alterações de comportamento na CLI do GitPR. A mudança é 100% de documentação e teste unitário de paridade.

## Proposed Changes

### Documentação (`docs/`)

#### [NEW] `docs/marketplace-publishing-guide.pt_br.md`
- Tradução fiel e idiomática para Português do Brasil.
- Preservação estrita de todos os blocos de código bash, snippets JSON, tokens de segredo (`VSCE_PAT`, `OVSX_PAT`), tags (`ext-v*`) e rotulagem de interface do Azure DevOps e Open VSX.

#### [NEW] `docs/marketplace-publishing-guide.pt_pt.md`
- Tradução fiel e idiomática para Português de Portugal (ex.: "ecrã", "guardar", "palavra-passe/tokens", "publicação nos entrepostos/mercados digitais").
- Paridade estrutural idêntica com o original em inglês.

#### [NEW] `docs/marketplace-publishing-guide.es_es.md`
- Tradução fiel e idiomática para Espanhol da Espanha.
- Paridade estrutural idêntica com o original em inglês.

#### [NEW] `docs/marketplace-publishing-guide.fr_fr.md`
- Tradução fiel e idiomática para Francês da França.
- Paridade estrutural idêntica com o original em inglês.

#### [MODIFY] `docs/editor-extension.pt_br.md`
- Atualizar linha 58 para `[Guia de Publicação nos Marketplaces](marketplace-publishing-guide.pt_br.md)`.

#### [MODIFY] `docs/editor-extension.pt_pt.md`
- Atualizar linha 58 para `[Guia de Publicação nos Marketplaces](marketplace-publishing-guide.pt_pt.md)`.

#### [MODIFY] `docs/editor-extension.es_es.md`
- Atualizar linha 58 para `[Guía de Publicación en Marketplaces](marketplace-publishing-guide.es_es.md)`.

#### [MODIFY] `docs/editor-extension.fr_fr.md`
- Atualizar linha 58 para `[Guide de publication sur les marketplaces](marketplace-publishing-guide.fr_fr.md)`.

---

### Testes Automatizados (`tests/`)

#### [NEW] `tests/unit/test_marketplace_publishing_guide_docs_parity.py`
- Testar a existência dos 5 arquivos:
  - `docs/marketplace-publishing-guide.md`
  - `docs/marketplace-publishing-guide.pt_br.md`
  - `docs/marketplace-publishing-guide.pt_pt.md`
  - `docs/marketplace-publishing-guide.es_es.md`
  - `docs/marketplace-publishing-guide.fr_fr.md`
- Validar seções e títulos correspondentes (Overview, VS Marketplace, Open VSX, Local Verification, Release Trigger, Maintenance).
- Validar preservação de segredos e comandos essenciais (`VSCE_PAT`, `OVSX_PAT`, `ext-v*`, `@vscode/vsce`, `ovsx`).
- Validar que `docs/editor-extension.*.md` apontam para os arquivos localizados corretos.

---

## Verification Plan

### Automated Tests
```bash
python -m pytest tests/unit/test_marketplace_publishing_guide_docs_parity.py -v
python -m pytest tests/test_doc_links.py -v
```

### Manual Verification
1. Inspecionar visualmente os 4 novos arquivos gerados em `docs/` quanto à formatação Markdown, tabelas, blocos de código e clareza de leitura.
2. Inspecionar o diff em `docs/editor-extension.*.md` garantindo que apenas os links alvo foram ajustados.
