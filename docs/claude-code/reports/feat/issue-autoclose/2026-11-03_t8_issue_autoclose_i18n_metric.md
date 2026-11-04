## Completion Report — T8: i18n do issue-autoclose e métrica `issue_autoclose`

### What was done

- **Métrica `issue_autoclose`** (`src/main.py::_prepare_close_issue`): uma
  chamada a `log_command_metric(command="issue_autoclose", provider="git",
  asked=..., accepted=..., skipped_reason=...)`, colocada **depois** de
  `resolve_close_issue` retornar e depois de imprimir o aviso, imediatamente
  antes do `return`. Import local (`from src.metrics import log_command_metric`),
  como nos demais pontos de chamada do projeto.
  - **Opção A** (registrada no plano): uma linha só quando o caso de uso
    chegou a uma decisão. Por este helper saem `not-github`,
    `registry-error`, `other-repo`, `issue-missing`, `issue-is-pr`,
    `issue-not-open`, `no-tty`, `declined`, `verify-failed` e o aceite
    (`skipped_reason=""`). Os quatro curto-circuitos do helper
    (`flag-disabled`, config `disabled`, `no-record`, SCM não resolvido) não
    logam: a feature nem foi exercitada, e `no-record` é o caminho dominante
    de quem nunca rodou `gitpr -is` — registrá-lo dobraria as linhas do fluxo
    de PR e distorceria as taxas de conclusão.
  - **Sem `status`**: o default `"success"` (`src/metrics.py:125`) é o Q14
    literal; `skipped_reason` já carrega o desfecho. Nenhum vocabulário novo.
  - **Sem `warning` no payload**: ele interpola texto de exceção e número de
    issue. Vão só três valores de vocabulário fixo — nenhum dado sensível,
    nenhum token, nenhuma URL.
  - `provider="git"` (não `provider.name`), porque a coluna `provider`
    significa provedor de IA no resto do ledger.
  - Nada no caso de uso: `resolve_close_issue` continua puro; `log_command_metric`
    é chamado fora de `try/except`, porque o contrato diz que ele nunca levanta.
  - Docstring de `_prepare_close_issue` ganhou uma frase documentando a linha
    no ledger.
- **i18n — verificação apenas.** A T8 do SPEC pedia questionário/avisos/erro de
  flags nas 6 línguas; o levantamento confirmou que as cinco strings já são
  literais `__()` traduzidos (pergunta, aviso de branch-alvo, aviso de
  verificação, aviso de `.gitignore`, erro de flags conflitantes), com 1694
  chaves por arquivo, paridade exata e sem tradução-identidade. **Nenhuma
  edição em `langs/`** — o diff está limpo nesse diretório. A auditoria
  `tests/test_i18n.py` roda verde como verificação.
- **Testes** (`tests/issue_autoclose/test_close_issue_wiring.py`):
  - `_run` passou a patchar `src.metrics.log_command_metric` (alvo do módulo
    de origem, por causa do import local) e expõe o mock em `self.log_metric`;
  - os cinco testes de curto-circuito ganharam
    `self.log_metric.assert_not_called()` (flags desligadas, config
    desligada, config vencendo `--close-issue`, sem registro, SCM não
    resolvido);
  - quatro testes novos com `assert_called_once_with(...)`, pinando de uma
    vez "exatamente uma linha", o conjunto exato de campos e a ausência de
    `status`/`warning`: pergunta aceita, `--close-issue`, pergunta recusada e
    falha de verificação.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/main.py` | feat | Métrica `issue_autoclose` no helper + frase no docstring |
| `tests/issue_autoclose/test_close_issue_wiring.py` | test | Patch do métrico, gates sem log, 4 testes de decisão |
| `docs/claude-code/plans/feat/issue-autoclose/2026-11-03_feat_issue_autoclose_t8_i18n_metric.md` | docs | Cópia do plano aprovado |

### Impact

- **Functionality:** cada execução do fluxo de PR que chega a uma decisão de
  autoclose grava uma linha `issue_autoclose` no ledger local
  (`~/.gitpr/metrics/telemetry.db`), com o contexto padrão já registrado pelo
  ledger (repo, branch, autor, timestamp) e os três campos no `payload` JSON.
  Comportamento visível ao usuário inalterado.
- **Performance:** uma escrita SQLite síncrona (pequena) por execução que
  chegou ao caso de uso; nenhum custo novo nos caminhos de curto-circuito.
- **Compatibility:** zero mudança de schema no ledger — `asked`/`accepted`/
  `skipped_reason` viajam em `payload` (comportamento já coberto por
  `tests/test_metrics.py:290-312`), então bancos existentes com
  `user_version = 1` continuam válidos. Não aparecem no export CSV
  (colunas fixas), apenas no JSON — documentação fica para a T9.
- **Fronteira preservada:** nenhum `requests` novo; nenhum token no payload;
  nenhum `langs/` tocado.

### Verificação da suíte

- `python -m pytest tests/issue_autoclose/test_close_issue_wiring.py -q`
  → **26 passed** (22 anteriores + 4 novos).
- `python -m pytest tests/issue_autoclose tests/test_i18n.py -q`
  → **142 passed, 56 subtests passed** (auditoria i18n incluída).
- `python -m pytest tests/test_metrics.py -q` → **164 passed** (inalterado).
- Suíte ampla (sem `test_config_app.py`/`test_commit_app.py`, com a
  deseleção do teste de baseline que trava sem TTY):
  **3162 passed, 2 skipped, 1 deselected, 227 subtests passed** e as
  **mesmas 8 falhas pré-existentes de `tests/test_plugins.py`** já
  documentadas nas T1–T7 (`load_dotenv(ENV_FILE, override=True)` traz
  `GITPR_LINTER_SECURITY='true'` quando o sync de hooks dispara). Em
  isolamento: `python -m pytest tests/test_plugins.py -q` → **17 passed**.
- `git status` não mostra `langs/` nem o banco do ledger.

### Divergências em relação ao plano

- Nenhuma divergência de SPEC/ADR. Duas notas de execução:
  - o snippet do plano usava `result = self._run(...)`, mas `_run` devolve a
    6-tupla (tripla do helper + mocks); dois testes novos foram escritos com
    desempacotamento explícito (`result, _, _, _, _, _ =`) e passaram;
  - a parte de i18n da T8 **já estava satisfeita** pelas tarefas anteriores;
    por isso não há chave nova nem diff em `langs/` — a entrega real da T8 é
    a métrica.

### Next steps

- **T9:** documentação de usuário — README/ajuda da CLI, changelog,
  `docs/metricas-telemetria*.md` (exemplo `issue_autoclose`, `asked`/
  `accepted`/`skipped_reason` como campos só de payload, ausentes de
  `CSV_COLUMNS`) e a atualização de `docs/config-tui.md` (linha da categoria
  Issue, "83 fields" → 85, "thirteen categories") nas 4 traduções.
- Commit sugerido (isolado): `feat: add issue autoclose metric`
- Aguardar confirmação do usuário antes da T9.
