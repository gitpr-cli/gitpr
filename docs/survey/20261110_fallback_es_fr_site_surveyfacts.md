# Survey Facts — Fallback ES/FR no Site de Documentação

- **Data:** 2026-11-10
- **Task:** `fallback_es_fr_site`
- **Branch:** `develop_natan`
- **Status:** CONCLUÍDO (FECHADO POR PROJETO)

## 1. Contexto da Tarefa
O item *"Acompanhar o fallback ES/FR no site: os links dos READMEs já usam `?lang=es` e `?lang=fr`, mas o site ainda pode servir inglês. Item herdado, ainda aberto."* vinha sendo mantido como observação nos relatórios e planos de auditoria do GitPR CLI.

O objetivo desta sessão foi investigar o ecossistema, mapear os arquivos envolvidos, determinar a fronteira de responsabilidade entre o CLI e o site público de documentação, e formalizar o encerramento da pendência.

## 2. Fatos Levantados na Codebase
1. **Contrato de URLs Canônicas (`src/doc_links.py`)**:
   - `DOC_LANG_PARAMS` mapeia internamente os locales do GitPR para os parâmetros aceitos pelo site de documentação:
     - `es_es` / `es` → `?lang=es`
     - `fr_fr` / `fr` → `?lang=fr`
     - `pt_br` → `?lang=pt_br`
     - `pt_pt` → `?lang=pt_pt`
     - `en_us` → sem parâmetro (padrão)
2. **READMEs e Pontos de Integração**:
   - `README.es_es.md` e `README.fr_fr.md` utilizam rigorosamente `?lang=es` e `?lang=fr`.
   - Modais de ajuda da TUI (`src/ui/help_screen.py`, `src/ui/chat_app.py`, `src/ui/config_app.py`) utilizam `doc_url()`.
3. **Trava de Regressão Automatizada (`tests/test_doc_links.py`)**:
   - `test_readme_es_and_fr_use_site_lang_params` proíbe explicitamente a presença de `?lang=es_es` e `?lang=fr_fr` nos READMEs.
   - `test_localized_languages_use_site_query_param` valida a conformidade dos parâmetros para todos os idiomas suportados.
4. **Comportamento do Portal Web em Produção**:
   - O portal `https://gitpr.natanfiuza.dev.br/docs/` está ativo e funcional.
   - Quando uma requisição com `?lang=es` ou `?lang=fr` solicita uma página cuja tradução ainda não foi publicada, o portal degrada graciosamente para a versão canônica em inglês retornando status HTTP 200, sem quebrar o link com erro 404.

## 3. Decisões Tomadas nas Rodadas de Grill
- **Rodada 1 / Q1 (Objetivo)**: Auditar o comportamento do site, validar que o fallback é 200 (degradação graciosa sem 404), e formalizar o encerramento do item herdado com ADR e relatório.
- **Rodada 1 / Q2 (Definição de Aceite)**: A degradação graciosa para inglês na ausência de tradução é o comportamento correto, resiliente e esperado de um sistema de documentação técnica multilíngue.
- **Rodada 1 / Q3 (Artefatos de Formalização)**: Criar a ADR `0017-documentation-site-language-fallback.md` em `docs/adr/`, registrar o conceito ubíquo `Documentation site fallback` em `CONTEXT.md` e documentar o fechamento definitivo da pendência.

## 4. Conclusão e Resolução
O item herdado está formalmente **RESOLVIDO E ENCERRADO**. Não restam débitos ou pendências técnicas pendentes no CLI em relação a este tópico.
