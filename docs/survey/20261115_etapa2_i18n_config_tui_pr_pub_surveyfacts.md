# Survey Facts — Etapa 2 (`docs/config-tui.*`, `docs/pull-request-publication.*`, ADR-0019)

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Skill:** `grill-with-docs`

## Fatos Levantados no Repositório
1. `docs/config-tui.*`: todas as 5 variantes possuem assinatura `(headings=17, table_rows=92, bullets=8, fences=4)`. As 4 traduções ainda não mencionam `GITPR_SKIP_PROJECT_CONFIG_SEED` nem linkam para `pull-request-publication.<lang>.md#94-...` na §1.8.
2. `docs/pull-request-publication.md`: assinatura `(headings=54, table_rows=99, bullets=16, fences=58)`. As 4 traduções (`.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`) possuem `(headings=47, table_rows=91, bullets=13, fences=46)` — faltam tabela/atualizações da §4 (+7 table rows), callout `> [!IMPORTANT]` na §9.1, subseção `### 9.4` completa (+5 headings, +3 bullets, +8 fences), linha na §14 (+1 table row) e Exemplos 9–10 na §15 (+2 headings, +4 fences, renumerando Exemplo 9 → 11).
3. `src/main.py:1419`: `and not os.getenv("GITPR_SKIP_PROJECT_CONFIG_SEED")` — qualquer valor não vazio suprime o runtime seed.
4. `CONTEXT.md` (L103–114): já define `**Runtime project configuration seed**:` e `**Project configuration seed opt-out**:`.
5. `docs/adr/0019-project-configuration-seed-segregation.md`: existe, mas não cita `pull-request-publication.md` nem `config-tui.md`.
6. `tests/unit/test_docs_translation_parity.py`: passa atualmente com `"pull-request-publication"` em `_PARITY_EXCEPTIONS` (L27).

## Decisões das Rodadas
- **Q1:** Adicionar referências cruzadas em `docs/adr/0019-project-configuration-seed-segregation.md` apontando para `docs/pull-request-publication.md` (§9.4) e `docs/config-tui.md` (§1.8), validando-as em `tests/unit/test_project_config_seed_docs.py`.
- **Q2:** Usar o slug exato de âncora `#94-...` correspondente ao título traduzido de `### 9.4` em cada idioma em `docs/config-tui.<lang>.md`.
- **Q3:** Validar também `> [!IMPORTANT]` em `pull-request-publication.*` e os termos de domínio em `CONTEXT.md` dentro de `tests/unit/test_project_config_seed_docs.py`.
