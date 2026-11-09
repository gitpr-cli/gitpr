# Implementation Plan — Auditoria e Validação da Seção Smart Excludes na TUI

## Goal Description
Auditar e validar tecnicamente a implementação da seção dedicada **Smart Excludes** na TUI de configuração (`gitpr config`), formalizando o encerramento do **Item 10** herdado do survey original.

Nas versões anteriores do GitPR (até a `v0.0.22`), o item apontava que os campos `GITPR_SMART_EXCLUDES_*` estavam sob uma categoria provisória `diff`. O PR #263 (`b3e547d`, 04/11/2026) implementou integralmente a categoria `smart_excludes`, o agrupamento dos campos e o painel especializado `#excludes_pane`. Esta tarefa formaliza a validação funcional, a rastreabilidade e o fechamento do item.

## User Review Required
> [!NOTE]
> Conforme alinhado na Rodada 1 do Grill (`Q1=Opção A`, `Q2=Opção A`, `Q3=Opção A`), a base de código já contém 100% da implementação requerida em perfeito estado e coberta por testes automatizados. Nenhuma alteração destrutiva ou funcional adicional de código é necessária.

## Proposed Components and Status

### Componente 1: Schema de Configuração (`src/config_schema.py`)
- Categoria `smart_excludes` declarada com label, descrição e documentação (`doc="smart-excludes.md"`).
- Campos `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL` e `SMART_EXCLUDES_VERSION` alocados em `smart_excludes`.
- Status: **Implementado e Validado**.

### Componente 2: TUI de Configuração (`src/ui/config_app.py`)
- Painel `#excludes_pane` renderizado com seletor de 3 fontes (Projeto, Core, Docs).
- Editor `TextArea` com modo de edição para projeto e somente-leitura para globais.
- Criação de arquivo local via botão `#excludes_create`.
- Salvamento coordenado via atalho `F2`.
- Status: **Implementado e Validado**.

### Componente 3: Glossário de Domínio (`CONTEXT.md`)
- Termo `Smart Excludes` devidamente registrado com as 3 camadas e termos a serem evitados.
- Status: **Implementado e Validado**.

### Componente 4: Documentação Técnica Multilíngue
- Páginas de documentação em `docs/smart-excludes.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`.
- Status: **Implementado e Validado**.

## Verification Plan

### Automated Tests
1. **Schema de Configuração**:
   ```bash
   python -m unittest tests.test_config_schema
   ```
   - 55 testes executados com 100% de sucesso.
   - Assert explícito: `test_smart_excludes_category_replaces_diff` assegura presença de `smart_excludes` e ausência de `diff`.

2. **Testes da Interface (TUI)**:
   - Casos de teste em `TestSmartExcludesSection` (`tests/test_config_app.py`):
     - `test_sidebar_lists_smart_excludes_section`
     - `test_the_three_sources_are_listed`
     - `test_switching_sources_changes_editor_read_only`
     - `test_project_file_creation_and_saving_with_f2`

### Manual Verification
1. Executar `python run.py config`.
2. Navegar no menu lateral até a opção **Smart Excludes**.
3. Inspecionar o formulário com os switches e caminhos.
4. Alternar entre as 3 fontes do painel inferior (Projeto, Core, Docs).
5. Observar o estado de leitura/edição e o botão de criação do arquivo local caso ausente.
