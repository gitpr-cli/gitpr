# Plano de Implementação — Formalização e Fechamento do Fallback ES/FR no Site

- **Data:** 2026-11-10
- **Branch:** develop_natan
- **Tarefa:** fallback_es_fr_site

## Objetivo
Formalizar tecnicamente o fechamento do item herdado **"Acompanhar o fallback ES/FR no site: os links dos READMEs já usam `?lang=es` e `?lang=fr`, mas o site ainda pode servir inglês"**. 

A responsabilidade do repositório GitPR CLI (`src/doc_links.py`, `tests/test_doc_links.py`, `README.es_es.md`, `README.fr_fr.md`) está 100% cumprida. O comportamento do site de servir conteúdo canônico em inglês (HTTP 200) na ausência de tradução específica é a definição arquitetural correta de **Degradação Graciosa (Graceful Degradation)**, prevenindo erros 404 para os usuários.

---

## Decisões Alinhadas no Grill
1. **Degradação graciosa**: O fallback para inglês com HTTP 200 é o comportamento de projeto correto para solicitações com `?lang=es` e `?lang=fr` sem tradução equivalente no site.
2. **Fechamento do item**: O item deixa de ser um débito aberto e passa a ser registrado como resolvido por arquitetura no ecossistema GitPR.
3. **Formalização em ADR e Glossário**: Criação da ADR 0017 e inclusão de `Documentation site fallback` no `CONTEXT.md`.

---

## Mudanças Propostas

### 1. Documentação de Arquitetura (ADR)
#### [NEW] `docs/adr/0017-documentation-site-language-fallback.md`
- Formaliza a decisão de arquitetura sobre o contrato entre o GitPR CLI e o site público de documentação.
- Estabelece que os parâmetros `?lang=es`, `?lang=fr`, `?lang=pt_br`, `?lang=pt_pt` devem degradar de forma limpa para inglês com status HTTP 200 caso a tradução da página não esteja presente.
- Registra as opções consideradas e consequências.

### 2. Modelo de Domínio e Glossário
#### [MODIFY] `CONTEXT.md`
- Adiciona o termo canônico ubíquo **Documentation site fallback**:
  > **Documentation site fallback**:
  > The graceful degradation contract of the official documentation website (`https://gitpr.natanfiuza.dev.br/docs/`) where requests carrying localized query parameters (`?lang=es`, `?lang=fr`, `?lang=pt_br`, `?lang=pt_pt`) return HTTP 200 with canonical English content whenever a specific localized translation is pending or not yet published, preventing 404 HTTP errors for users following CLI and README links.
  > _Avoid_: 404 fallback, missing doc error, broken link

### 3. Registros de Fatos e Survey
#### [NEW] `docs/survey/20261110_fallback_es_fr_site_surveyfacts.md`
#### [NEW] `docs/plans/develop_natan/20261110_fallback_es_fr_site_plansfacts.md`

---

## Plano de Verificação
- Executar `tests/test_doc_links.py`.
- Validar coerência textual e integridade das referências cruzadas.
