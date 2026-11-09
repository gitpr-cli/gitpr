# Survey — Auditoria e Encerramento das Dívidas da TUI de Configuração

- **Data:** 2026-11-09
- **Branch:** `develop_natan`
- **Origem:** Grill `/plan /grill-with-docs` (1 rodada, 3 decisões)
- **Objeto:** Auditoria técnica e encerramento formal do item herdado de dívidas registradas no plano do config TUI
- **Estado:** Confirmado e Validado

---

## 1. Contexto da Tarefa

No relatório de estado `docs/reports/relatorio_estado_v0.0.22.md`, constava como débito aberto:
> *Dívidas registradas no plano do config TUI: `DEFAULT_CONFIG` ficou redundante com o schema; o banner de abertura não lista `--init`, `--base` nem `--plugins`; o `LinterApp` é o **único** app Textual que ainda não desabilita a command palette; e as **9 `GITPR_CHECK_*`** ainda **não** têm categoria no schema. **Item herdado, ainda aberto.***

Esta sessão realizou a averiguação detalhada do codebase, da suíte de testes e do histórico de commits para formalizar o encerramento do item com rastreabilidade auditável.

---

## 2. Decisões Confirmadas no Grill (Rodada 1)

| # | Tema | Decisão |
|---|------|---------|
| **Q1** | Objetivo da Sessão | **Auditoria e Encerramento Formal (Opção A):** Fatos comprovam que todos os 4 sub-itens já foram codificados, testados e integrados na versão `v0.0.23` via PR #265 (commit `74f8c38`). O objetivo é auditar formalmente e confirmar a cobertura e o encerramento definitivo do item. |
| **Q2** | Escopo dos Testes e Domínio | **Manter como está (Opção A):** As definições de domínio em `CONTEXT.md` (`Seeded configuration field` e `CI Check`) e as suítes de testes automatizados (`TestCheckCategory`, `TestTUIDebtsResolved`, `TestSchemaCoversDefaults` em `tests/test_config_schema.py`) cobrem integralmente o contrato sem necessidade de alterações adicionais no código. |
| **Q3** | Formalização Documental | **Roteiro Completo de Governança (Opção A):** Registrar os artefatos de governança em `docs/survey/`, `docs/plans/`, `docs/gemini/plans/`, `docs/gemini/reports/` e `docs/gemini/walkthrough/` para manter a rastreabilidade histórica do repositório. |

---

## 3. Fatos do Código Levantados e Auditados

1. **`DEFAULT_CONFIG` derivado do schema (SSOT):**
   - Em `src/config_schema.py`:
     - O dataclass `ConfigField` possui `seeded: bool = False`.
     - Exatamente 55 campos ativos possuem `seeded=True`.
     - `DEFAULT_CONFIG = {field.key: field.default for field in FIELDS if field.seeded}` é derivado dinamicamente.
   - Em `src/config.py`:
     - O bloco de 90+ linhas de dicionário manual estático foi totalmente removido.
     - A importação direta `from src.config_schema import DEFAULT_CONFIG` garante compatibilidade retroativa.
   - Teste: `TestSchemaCoversDefaults::test_default_config_derived_from_seeded_fields` valida a derivação.

2. **Opções no banner de abertura:**
   - Em `src/main.py:254`, a função `print_banner()` inclui expressamente `--init`, `--base` e `--plugins`:
     `"  Options: -c,--commit | -r,--review | -f,--fullreview | -l,--linter | -s,--skill | -u,--update | -ih,--installhooks | --install | --init | -is,--issue | --no-publish | --no-edit | --base | --plugins | -h,--help (use -h --flag for contextual help)\n"`
   - As 6 matrizes de internacionalização em `langs/` (`pt_br.json`, `pt_pt.json`, `es_es.json`, `es.json`, `fr_fr.json`, `fr.json`) foram atualizadas.
   - Teste: `TestTUIDebtsResolved::test_banner_includes_init_and_base` captura o stdout de `print_banner()` e valida a presença de `--init`, `--base` e `--plugins`.

3. **Desativação da command palette no `LinterApp`:**
   - Em `src/ui/linter_app.py:53`, a classe `LinterApp` define explicitamente:
     `ENABLE_COMMAND_PALETTE = False`
   - Teste: `TestTUIDebtsResolved::test_linter_app_disables_command_palette` valida que `getattr(LinterApp, "ENABLE_COMMAND_PALETTE", True)` é falso, garantindo paridade com todos os outros 9 apps Textual do GitPR.

4. **Categoria `check` e as 9 variáveis `GITPR_CHECK_*` no schema:**
   - Em `src/config_schema.py`:
     - Categoria `Category("check", __("CI Check"), __("Unified pipeline checks, output formats, thresholds, and execution limits."), doc="check-ci.md")` declarada.
     - 9 campos declarados com `category="check"` e `seeded=False` (para evitar geração desnecessária no `.env` do usuário):
       - `GITPR_CHECK_BASE`
       - `GITPR_CHECK_FORMAT`
       - `GITPR_CHECK_OUTPUT`
       - `GITPR_CHECK_FAIL_ON`
       - `GITPR_CHECK_NO_IA`
       - `GITPR_CHECK_IA_ONLY_HIGH_RISK`
       - `GITPR_CHECK_BASELINE_PATH`
       - `GITPR_CHECK_POLICY`
       - `GITPR_CHECK_TIMEOUT_SECONDS`
   - Testes: `TestCheckCategory::test_check_category_declared_and_documented` e `TestCheckCategory::test_check_fields_present_and_not_seeded`.

5. **Glossário de Domínio em `CONTEXT.md`:**
   - Termos canônicos `Seeded configuration field` e `CI Check` devidamente formalizados com termos recomendados e banidos.

6. **Status no Relatório Oficial:**
   - Em `docs/reports/relatorio_estado_v0.0.23.md`, o item já foi registrado formalmente como:
     `* **Dívidas registradas no plano do config TUI:** ✅ **concluído** — DEFAULT_CONFIG derivado, banner com --init/--base, palette desabilitada no LinterApp e as 9 GITPR_CHECK_* na categoria check.`
