## Completion Report — T2: leitura de issue no `ScmProvider`

### What was done

- `IssueInfo` adicionado ao contrato em `src/infrastructure/scm/base.py`, com
  os campos da SPEC: `number`, `title`, `url`, `state`, `is_pull_request`.
- Três métodos concretos adicionados ao `ScmProvider` (não abstratos, para não
  obrigar os quatro providers existentes a mudar):
  - `get_issue(repo, number, timeout=5) -> IssueInfo`
  - `get_default_branch(repo, timeout=5) -> str`
  - `closing_line(number) -> str`
- `GitHubProvider` implementa os três:
  - `get_issue`: `GET /repos/{owner}/{repo}/issues/{n}`, status 200; o campo
    `pull_request` do payload é o discriminante (`is_pull_request`), porque o
    endpoint de issues também responde números de PR.
  - `get_default_branch`: `GET /repos/{owner}/{repo}`, devolve
    `default_branch`; campo ausente vira `""` (desconhecido, nunca inventado).
  - `closing_line`: sintaxe do GitHub, `close #N`.
- Os demais forges herdam o default do contrato: `ScmNotSupportedError`, que o
  chamador lê como "feature inativa" — nenhum deles ganhou código novo.
- Timeout padrão de 5 s nos dois métodos HTTP, sobrescrevível por parâmetro.
- Erros HTTP e de transporte continuam saindo como `ScmProviderError` com
  `http_status` (404/401/403/5xx) ou 0 (sem resposta), como todo o contrato.
- 14 testes novos no provider (aberta, fechada, PR, número ausente, timeout
  customizado, 404, 403, 5xx, timeout, 401, branch padrão, linha de
  fechamento) e 2 no contrato (`IssueInfo` e o default dos outros forges, com
  3 subtestes).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/infrastructure/scm/base.py` | feat | `IssueInfo` + `get_issue`, `get_default_branch`, `closing_line` com defaults `ScmNotSupportedError` |
| `src/infrastructure/scm/github_provider.py` | feat | Implementação GitHub dos três métodos, timeout padrão 5 s |
| `tests/scm/test_github_provider.py` | test | 17 testes HTTP mockados do novo contrato |
| `tests/scm/test_contract.py` | test | Forma de `IssueInfo` + default `ScmNotSupportedError` dos demais forges |
| `CONTEXT.md` | docs | Glossário: "Closing line" (Q15) |

### Divergências em relação à SPEC (decididas na T0)

| # | SPEC (T2) | Implementado | Por quê |
|---|---|---|---|
| 1 | Exceções tipadas `IssueNotFound`, `ProviderUnavailable`, `ProviderAuthError` | `ScmProviderError` com `http_status` | Decisão Q7: sem classes novas; 404 limpa o registro, 401/403/0/5xx avisam e mantêm |
| 2 | Demais providers levantam `NotImplementedError` | O default do contrato levanta `ScmNotSupportedError` | É a convenção já usada por `create_release`, `get_pull_request`, `list_pull_requests` e `request_pull_request_reviewers`; o chamador pode degradar com um `except ScmProviderError` |
| 3 | "Timeout configurável" | Parâmetro `timeout=5` nos dois métodos; a chave `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` entra na T7 | T7 é a tarefa dona do schema de configuração e do getter em `config.py`; a T2 deixa a costura pronta |

### Impact

- **Functionality:** nenhuma mudança no comportamento atual — nenhum fluxo de
  produção chama os métodos novos ainda. A T3 fará a primeira ligação (gravar
  o registro) e a T4/F6 consumirão `get_issue`/`get_default_branch`.
- **Performance:** nenhuma chamada extra de rede fora dos métodos novos. Quando
  chamados, o timeout padrão curto (5 s) limita a espera.
- **Compatibility:** aditiva. `IssueInfo` é um dataclass novo; os métodos são
  concretos no ABC, então nenhum provider externo quebra. `get_default_branch`
  devolve `""` para forges/ payloads que não informam a branch — o chamador
  deve tratar vazio como "não sei" e não emitir aviso.
- **Segurança:** nenhum token é impresso ou transportado para fora do header;
  os testes usam token fictício e HTTP mockado.

### Verification

- `python -m pytest tests/scm -q` → **321 passed, 2 skipped, 18 subtests
  passed**.
- Suíte completa sem os dois arquivos de UI instáveis
  (`test_config_app.py`, `test_commit_app.py`) e com a deseleção de **um**
  teste pré-existente que trava sem TTY
  (`tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched`):
  **3062 passed, 2 skipped, 1 deselected, 146 subtests passed** (380,88 s).
- Os dois arquivos de UI isolados: **101 passed, 1 failed** — a mesma falha
  intermitente já registrada na T1 (`test_headless_full_flow`, timeout do
  Textual em `CommitMessageScreen`). O teste **passa sozinho em 4,91 s**,
  confirmando flakiness de isolamento e não regressão.
- Diagnóstico do travamento (faulthandler): a pilha mostra um app Textual
  rodando em `src/main.py:1596` dentro do teste de baseline, sem TTY no
  Windows — mesmo problema pré-existente da T1, sem relação com o SCM.

### Next steps

- T3: `register_created_issue` chamado por `IssueApp.action_create_issue` após
  sucesso, só GitHub, falha como aviso.
- T4: `resolve_close_issue` (árvore do passo 2.2 do fluxo).
- Aguardar confirmação do usuário antes da T3.
