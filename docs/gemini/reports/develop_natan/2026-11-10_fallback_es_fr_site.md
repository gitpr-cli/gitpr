## Completion Report — Formalização e Fechamento do Fallback ES/FR no Site

### What was done
- Conduzida sessão estruturada de `/grill-with-docs` e `/plan` para análise da pendência histórica de fallback ES/FR no portal de documentação.
- Confirmado que o GitPR CLI cumpre integralmente o contrato através de `src/doc_links.py`, `tests/test_doc_links.py`, `README.es_es.md` e `README.fr_fr.md`.
- Formalizado o entendimento de que a entrega de documentação canônica em inglês (HTTP 200) na ausência de tradução é a especificação correta de Degradação Graciosa (Graceful Degradation), prevenindo erros 404 para os usuários.
- Criada a **ADR 0017** (`docs/adr/0017-documentation-site-language-fallback.md`) documentando oficialmente a decisão arquitetural e o encerramento do item herdado.
- Atualizado o glossário ubíquo do projeto (`CONTEXT.md`) com o termo canônico `Documentation site fallback`.
- Gerados os relatórios de survey e fatos do plano (`docs/survey/` e `docs/plans/develop_natan/`) conforme a skill `grill-with-docs`.
- Declarado o item formalmente **CONCLUÍDO (FECHADO POR PROJETO)**.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/adr/0017-documentation-site-language-fallback.md` | feat | Decisão formal de arquitetura documentando o contrato de fallback multilíngue e fechamento do item |
| `CONTEXT.md` | docs | Adição do conceito ubíquo `Documentation site fallback` no glossário |
| `docs/survey/20261110_fallback_es_fr_site_surveyfacts.md` | docs | Levantamento completo de fatos e survey da sessão de grill |
| `docs/plans/develop_natan/20261110_fallback_es_fr_site_plansfacts.md` | docs | Plano de execução e matriz de rastreabilidade arquivados |
| `docs/gemini/plans/develop_natan/2026-11-10_develop_natan_fallback_es_fr_site.md` | docs | Plano de desenvolvimento conforme diretrizes do `GEMINI.md` |
| `docs/gemini/walkthrough/develop_natan/2026-11-10_fallback_es_fr_site.md` | docs | Walkthrough do encerramento da tarefa conforme diretrizes do `GEMINI.md` |

### Impact
- **Functionality:** O item herdado deixa de ser um débito aberto nos relatórios de auditoria do CLI; os links de documentação mantêm comportamento resiliente e estável.
- **Performance:** Nulo (alterações restritas à documentação e governança arquitetural).
- **Compatibility:** Nenhuma quebra de API ou alteração de comportamento de código.

### Next steps (if applicable)
- Nenhuma pendência técnica em aberto referente a este item no GitPR CLI.
