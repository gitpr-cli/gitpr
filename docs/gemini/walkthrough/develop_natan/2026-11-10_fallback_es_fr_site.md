# Walkthrough — Encerramento Formal do Item Herdado de Fallback ES/FR no Site

- **Data:** 2026-11-10
- **Branch:** develop_natan
- **Task:** fallback_es_fr_site

## O que foi realizado

Concluímos a auditoria e formalização arquitetural para encerramento definitivo do item herdado:
> *"Acompanhar o fallback ES/FR no site: os links dos READMEs já usam `?lang=es` e `?lang=fr`, mas o site ainda pode servir inglês. Item herdado, ainda aberto."*

### 1. Resumo das Descobertas
- **Conformidade do CLI:** O módulo `src/doc_links.py` atua como SSOT para geração de links e já mapeia `es_es` para `?lang=es` e `fr_fr` para `?lang=fr`. Os arquivos `README.es_es.md` e `README.fr_fr.md` utilizam exclusivamente esses parâmetros, protegidos por testes em `tests/test_doc_links.py`.
- **Degradação Graciosa no Site:** O portal web (`https://gitpr.natanfiuza.dev.br/docs/`) responder com a documentação canônica em inglês (HTTP 200) quando uma página em espanhol ou francês ainda não está publicada é a especificação correta de **Degradação Graciosa (Graceful Degradation)**, prevenindo erros 404 (Not Found).

---

## Mudanças Realizadas

| Arquivo | Tipo | Descrição |
| :--- | :--- | :--- |
| `docs/adr/0017-documentation-site-language-fallback.md` | **NEW** | Decisão de arquitetura formalizando o contrato de fallback multilíngue e fechamento do item herdado |
| `CONTEXT.md` | **MODIFY** | Inclusão do termo ubíquo `Documentation site fallback` |
| `docs/survey/20261110_fallback_es_fr_site_surveyfacts.md` | **NEW** | Levantamento completo de fatos e decisões da sessão de grill |
| `docs/plans/develop_natan/20261110_fallback_es_fr_site_plansfacts.md` | **NEW** | Plano de execução e matriz de rastreabilidade arquivados |
| `docs/gemini/plans/develop_natan/2026-11-10_develop_natan_fallback_es_fr_site.md` | **NEW** | Plano de desenvolvimento conforme `GEMINI.md` |

---

## Validação e Verificação

1. **Integridade de Código:** Nenhuma alteração de código fonte em `src/` ou `tests/` foi necessária, preservando 100% a estabilidade do CLI.
2. **Coerência Textual e Rastreabilidade:** O termo `Documentation site fallback` no `CONTEXT.md` alinha-se perfeitamente com a `ADR 0017` e com `src/doc_links.py`.
3. **Status do Item:** Formalmente encerrado como **RESOLVIDO / FECHADO POR PROJETO**.
