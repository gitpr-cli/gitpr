## Completion Report — Documentação do desenho de secret scanning no linter

### What was done

Sessão de grill (`grill-with-docs`) sobre a spec `docs/plans/20260921_skill_gitpr_secret_scanning_spec.md`, com três agentes de exploração read-only mapeando o código real antes de qualquer pergunta. Resultado: a spec partia de sete premissas falsas sobre este repositório e foi substituída por quatro documentos.

- Levantamento verificado de primeira mão (motor do linter, registro de skills e wiring do CLI, smart excludes, fluxo de bloqueio, i18n, empacotamento).
- Dez decisões de produto fechadas em três rodadas (Q1–Q10), todas registradas.
- **Nenhum arquivo de código foi alterado pela sessão de grill** — a implementação da feature é uma sessão separada, por decisão Q1. Uma correção colateral autorizada depois, já fora do escopo do grill, está em [2026-09-21_ai_timeout_default_drift.md](2026-09-21_ai_timeout_default_drift.md).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `docs/survey/20260921_gitpr_secret_scanning_surveyfacts.md` | docs | Survey da sessão: contexto, 13 blocos de fatos com referência verificada, as três rodadas de decisão e a síntese do desenho |
| `docs/plans/20260921_skill_gitpr_secret_scanning_plan.md` | docs | Plano de implementação que substitui a spec: as sete regras com regex final, as duas mudanças no motor, nove etapas com verificação e o critério de pronto |
| `docs/plans/glossary-gitpr-secret-scanning.md` | docs | Glossário canônico: 19 termos, as duas chaves de config e 15 notas de fidelidade (spec × código) |
| `docs/plans/ADR-007-secret-ruleset-location-and-severity.md` | docs | ADR: dois níveis de severidade, ruleset embutido em `src/`, escape por config e a extensão `extensions: ["*"]` |
| `docs/claude-code/reports/develop_natan/2026-09-21_gitpr_secret_scanning.md` | docs | Este relatório |

### Impact

- **Functionality:** nenhuma — somente documentação. O desenho aprovado, quando implementado, adiciona sete regras regex, duas chaves de config e duas linhas de mudança no motor (`extensions: ["*"]` e o merge em `load_linter_rules()`).
- **Performance:** nenhuma. O ruleset é regex local, sem rede e sem IA.
- **Compatibility:** a implementação futura muda comportamento por padrão (`GITPR_LINTER_SECURITY=true`) — commits que passavam podem passar a ser bloqueados nas cinco categorias de padrão determinístico. Registrado como nota de release obrigatória no plano §7. Nenhuma mudança quebra o schema de regra existente: regras antigas continuam válidas e `extensions` sem `"*"` se comporta como antes.

### Premissas da spec que o código contradiz

`severity`/`id`/`category`/`exclude_values` não existem no schema de regra (a chave é `level`, a identidade é `name`); não há três níveis de severidade (só `error`/`warning`, e qualquer outro valor bloqueia); a lista fixa de skills está em `src/config.py`, não em `core.py`; `config.schema.yml`, `presets/linter/` e `src/domain/` não existem; `gitpr --linter security` é impossível (`-l` é flag booleana); não há override por regra nem supressão inline; o motor casa linha a linha, então "contexto próximo" é inexprimível.

### Next steps

1. Implementar seguindo `docs/plans/20260921_skill_gitpr_secret_scanning_plan.md` §3, um commit por etapa.
2. `python tests/sync_i18n.py` antes da etapa 5 (as mensagens usam `__()`, e `tests/test_i18n.py` exige paridade e tradução nos seis arquivos de idioma).
3. Follow-ups registrados no plano §6: supressão inline, proximidade entre linhas, entropia/SAST, varredura retroativa e objeto de finding estruturado.
