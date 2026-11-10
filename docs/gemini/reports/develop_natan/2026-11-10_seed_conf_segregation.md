## Completion Report — Segregação entre Auto-Seed de Runtime e Provisionamento de Projeto (`gitpr seed`)

### What was done
- Conduzida sessão de alinhamento com a skill `grill-with-docs` para confirmar o encerramento da dívida histórica de `relatorio_estado_v0.0.22.md:898`.
- Formalizado o [ADR-0019](file:///docs/adr/0019-project-configuration-seed-segregation.md) documentando a fronteira de responsabilidades entre o auto-seed silencioso de primeiro uso (restrito a `.gitpr/conf/gitpr.config.yml` para a PR target base) e o provisionamento deliberado de projeto (`gitpr seed`, wizard de 5 etapas `--install` e download via `--skill`).
- Refinado o modelo de domínio no `CONTEXT.md`, eliminando a sobrecarga de termos e estabelecendo claramente as definições de `Runtime project configuration seed` e `Project configuration seed`.
- Gerados e registrados os artefatos automatizados de planejamento e levantamento:
  - `docs/plans/develop_natan/20261110_seed_conf_segregation_plansfacts.md`
  - `docs/survey/20261110_seed_conf_segregation_surveyfacts.md`
  - `docs/gemini/plans/develop_natan/2026-11-10_develop_natan_seed_conf_segregation.md`
- Validação completa com 57 testes automatizados passando em `tests/test_seed_command.py` e `tests/test_project_config.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/adr/0019-project-configuration-seed-segregation.md` | docs | Registro formal de decisão de arquitetura sobre a segregação do auto-seed de runtime e provisionamento explícito |
| `CONTEXT.md` | docs | Desambiguação de termos ubíquos entre auto-seed de runtime e provisionamento explícito de projeto |
| `docs/plans/develop_natan/20261110_seed_conf_segregation_plansfacts.md` | docs | Artefato automático de plano de execução conforme contrato do grill |
| `docs/survey/20261110_seed_conf_segregation_surveyfacts.md` | docs | Artefato automático de levantamento e decisões de rodadas conforme contrato do grill |
| `docs/gemini/plans/develop_natan/2026-11-10_develop_natan_seed_conf_segregation.md` | docs | Cópia do plano de desenvolvimento no padrão Gemini |
| `docs/gemini/walkthrough/develop_natan/2026-11-10_seed_conf_segregation.md` | docs | Walkthrough do alinhamento e documentação da segregação |

### Impact
- **Functionality:** Nenhuma alteração funcional que quebre o comportamento do runtime. Fica formalmente documentado que `gitpr.config.yml` é o único arquivo auto-semeado no primeiro uso para evitar poluição da árvore de trabalho Git, enquanto `smart-excludes` e `linter` pertencem exclusivamente a `gitpr seed` e ao wizard de 5 etapas.
- **Performance:** Nulo (nenhum overhead introduzido).
- **Compatibility:** Total compatibilidade mantida.

### Next steps (if applicable)
- Nenhuma ação pendente referente ao seed de `.gitpr/conf/` local.
