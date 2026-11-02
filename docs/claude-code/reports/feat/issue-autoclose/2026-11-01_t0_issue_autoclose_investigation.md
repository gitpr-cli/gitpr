## Completion Report — T0: investigação do fechamento automático de issue (`close #N`)

### What was done

- Lido o pacote completo da SPEC (`glossario.md`, ADR-001..007, `entrevista.md`, `00-SPEC.md`,
  `PROMPT-CLAUDE-CODE.md`).
- Levantados no código real os dez pontos pedidos pela T0, com caminho e linha:
  criação de issue, contrato SCM, montagem do corpo do PR, início do fluxo `gitpr`,
  branch de destino, TUI `config`, i18n, TTY, YAML/estado local, testes e métricas.
- Levadas ao usuário, em quatro rodadas de grill, as 16 decisões do protocolo e das
  divergências; todas confirmadas antes de qualquer alteração.
- Criada a branch `feat/issue-autoclose` a partir de `develop_natan`.
- Gravados o survey e o plano da sessão; emendados os ADRs afetados com nota datada.
- Nenhum código de produção foi escrito.
- Executada a suíte de base:
  `python -m pytest tests/ -q --deselect "tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched"`
  → **3125 passed, 2 skipped, 1 deselected, 138 subtests passed** em 442 s.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `docs/survey/20261101_issue_autoclose_surveyfacts.md` | docs | Levantamento completo da T0 + decisões das quatro rodadas |
| `docs/plans/feat/issue-autoclose/20261101_issue_autoclose_plansfacts.md` | docs | Plano de execução e roadmap T1–T9 |
| `docs/specs/issue-autoclose/adrs/ADR-001-local-formato-registro.md` | docs | Nota T0: `.gitignore` recebe só `github.yml` |
| `docs/specs/issue-autoclose/adrs/ADR-004-insercao-e-idempotencia.md` | docs | Nota T0: ponto físico de inserção antes do `.md` |
| `docs/specs/issue-autoclose/adrs/ADR-005-momento-da-pergunta-e-modos.md` | docs | Nota T0: resolução lazy de provider/branch-alvo |
| `docs/claude-code/reports/feat/issue-autoclose/2026-11-01_t0_issue_autoclose_investigation.md` | docs | Este relatório |

### Impact

- **Functionality:** nenhuma mudança de comportamento; a T0 é somente investigação.
- **Performance:** nenhuma.
- **Compatibility:** nenhuma. A branch nova contém apenas documentação.
- **Suíte de base:** verde, exceto o teste desselecionado. Ele invoca `gitpr -c` sem
  `--hook`, e o CLI abre a TUI `CommitApp` (`src/main.py:1591-1596`); neste ambiente
  Windows sem TTY o driver Textual fica bloqueado em `wait_for_handles`, travando a
  execução. É pré-existente e independente desta branch (o pipeline de CI roda em Linux);
  o restante da suíte passa integralmente.
- **Divergências decididas:** badge real é o shields.io do linter (não "Reviewed by");
  pergunta antes da TUI de stage exige resolução lazy de provider/base; o `.md` e o
  `--no-publish` não passam pelo badge; a T3 tem um único caminho de criação de issue
  (`IssueApp`); exceções tipadas não serão criadas (usa-se `ScmProviderError.http_status`);
  `.gitignore` ignora só `.gitpr/conf/github.yml`; configuração usa `GITPR_*` plano;
  i18n cobre 6 arquivos; `PrContext` não será criado.

### Next steps

- Aguardar confirmação do usuário para iniciar a T1 (`IssueRegistry`).
- Cada tarefa seguinte termina com testes verdes e a mensagem Conventional Commits
  sugerida; nenhum commit será criado (regra do `CLAUDE.md`).
- O teste manual da seção 12 da SPEC depende de um repositório real no GitHub e fica
  para o usuário ao final da T9.
