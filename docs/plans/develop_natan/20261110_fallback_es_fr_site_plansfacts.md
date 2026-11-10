# Plano de Execução & Fatos — Fallback ES/FR no Site

- **Data:** 2026-11-10
- **Task:** `fallback_es_fr_site`
- **Branch:** `develop_natan`
- **Skill acionada:** `grill-with-docs` (Grill + Domain Modeling)

## 1. Escopo da Sessão
Encerrar a pendência histórica *"Acompanhar o fallback ES/FR no site: os links dos READMEs já usam `?lang=es` e `?lang=fr`, mas o site ainda pode servir inglês"*, delimitando fronteiras entre o CLI e o site de documentação e registrando formalmente a decisão arquitetural de Degradação Graciosa.

## 2. Ações Executadas
1. **Auditoria da Codebase**:
   - Mapeamento de `src/doc_links.py`, `tests/test_doc_links.py`, `README.es_es.md`, `README.fr_fr.md` e referências de chamadas em `src/`.
   - Constatação de 100% de conformidade do código do CLI em relação ao contrato canônico `?lang=es` e `?lang=fr`.
2. **Registro de Arquitetura**:
   - Criação da **ADR 0017** (`docs/adr/0017-documentation-site-language-fallback.md`) documentando o status de aceito, o contexto, as opções consideradas e as consequências da degradação graciosa.
3. **Modelagem de Domínio**:
   - Atualização do `CONTEXT.md` com o conceito `Documentation site fallback`.
4. **Encerramento do Item Herdado**:
   - Item declarado formalmente concluído e fechado.

## 3. Matriz de Rastreabilidade
| Artefato | Papel | Status |
| :--- | :--- | :--- |
| `docs/adr/0017-documentation-site-language-fallback.md` | Decisão formal de arquitetura (ADR) | Criado |
| `CONTEXT.md` | Glossário ubíquo com `Documentation site fallback` | Atualizado |
| `docs/survey/20261110_fallback_es_fr_site_surveyfacts.md` | Relatório completo de fatos e levantamento | Criado |
| `docs/plans/develop_natan/20261110_fallback_es_fr_site_plansfacts.md` | Plano arquivado na branch | Criado |
| `docs/gemini/reports/develop_natan/2026-11-10_fallback_es_fr_site.md` | Relatório de conclusão obrigatório | Criado |
| `docs/gemini/walkthrough/develop_natan/2026-11-10_fallback_es_fr_site.md` | Walkthrough obrigatório da tarefa | Criado |
