# Plano de Execução — Etapa 2: Sincronizar `docs/config-tui.*` e `docs/pull-request-publication.*` + Testes ADR-0019

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Referência:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (L74–L99)

## Escopo Acordado (após `/grill-with-docs`)
1. Atualizar `docs/config-tui.{pt_br,pt_pt,es_es,fr_fr}.md` (§1.8) com `GITPR_SKIP_PROJECT_CONFIG_SEED=true` e link localizado para `#94-<slug>` exato de `pull-request-publication.<lang>.md`.
2. Sincronizar integralmente `docs/pull-request-publication.{pt_br,pt_pt,es_es,fr_fr}.md` (§4, §9.1 `[!IMPORTANT]`, §9.4 completa, §14 e §15 Ex. 9–10 + renumeração do Ex. 11) atingindo assinatura estrutural idêntica ao inglês (`headings=54`, `table_rows=99`, `bullets=16`, `fences=58`).
3. Adicionar referências cruzadas em `docs/adr/0019-project-configuration-seed-segregation.md` para `docs/pull-request-publication.md` (§9.4) e `docs/config-tui.md` (§1.8).
4. Remover `"pull-request-publication"` de `_PARITY_EXCEPTIONS` em `tests/unit/test_docs_translation_parity.py`.
5. Criar `tests/unit/test_project_config_seed_docs.py` validando os 5 idiomas de ambos os guias, `> [!IMPORTANT]`, âncoras `#94-...`, ADR-0019 e termos de `CONTEXT.md`.

## Verificação
- `python -m pytest tests/unit/test_project_config_seed_docs.py tests/unit/test_docs_translation_parity.py -v`
