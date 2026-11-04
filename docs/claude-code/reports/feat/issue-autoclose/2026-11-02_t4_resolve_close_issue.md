## Completion Report — T4: decisão de fechamento automático (`resolve_close_issue`)

### What was done

- Criado `src/issue_autoclose/resolve_close_issue.py`, o caso de uso puro que
  o fluxo `gitpr` (T6) chamará antes da TUI de stage: lê o registro local,
  verifica no forge se a issue ainda está aberta e devolve a decisão — ou o
  motivo de não haver decisão — como dado. Nada é impresso no módulo.
  - `CloseIssueFlags(accept=False, disabled=False)` — `--close-issue` e
    `--no-close-issue` (a exclusão mútua fica na CLI, T6).
  - `CloseIssueDecision(number, title, line, target_branch_warning="")` — a
    linha de fechamento e o aviso de branch de destino que já apareceu na
    pergunta.
  - `CloseIssueOutcome(decision=None, warning="", skipped_reason="", asked=False,
    accepted=False)` — o que a T6 imprime/mede; `warning` é a linha única de
    falha de verificação ou de registro ilegível; `skipped_reason` é o
    vocabulário da métrica da T8.
- Árvore implementada, na ordem do passo 2.2 da SPEC:
  - gates sem disco e sem rede: `--no-close-issue`, `GITPR_ISSUE_AUTOCLOSE`
    desligado, forge não-GitHub;
  - leitura única do registro: corrompido → aviso de uma linha +
    `registry-error`, sem rede e sem limpar; ausente → `no-record`; de outro
    repositório → `other-repo`, **sem limpar** (ADR-007);
  - `get_issue` com o timeout da config: `is_pull_request` vence o estado;
    estado normalizado (`strip().lower() == "open"`); fechada/PR/404 limpam o
    registro em silêncio; 401/403/0/5xx/timeout/exceção inesperada viram aviso
    e mantêm o registro (`verify-failed`);
  - decisão: `--close-issue` aceita sem perguntar (verificando a issue antes);
    sem TTY ou sem `ask` → `no-tty`; no caminho de pergunta,
    `get_default_branch` só é consultada ali, falha/vazio degrada em silêncio,
    e `ask(question, default=True)` decide entre `declined` e a decisão;
  - a linha vem de `provider.closing_line(number)` (ADR-006).
- `ask` fica fora de todo `try`: Abort do Click (Ctrl+C) propaga como em
  qualquer outro prompt, e uma decisão nunca limpa o registro — limpar depois
  que o PR existe é responsabilidade da T6.
- Quatro chaves i18n novas, criadas via `python tests/sync_i18n.py` e
  traduzidas nos 6 arquivos de idioma (`es`, `es_es`, `fr`, `fr_fr`, `pt_br`,
  `pt_pt`): pergunta, aviso de branch de destino, falha de verificação e
  registro ilegível.
- `CONTEXT.md`: termo **Close issue decision** (a decisão em memória, não o
  corpo do PR). Docstring de `src/issue_autoclose/__init__.py` atualizado com
  os três módulos do pacote.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/issue_autoclose/resolve_close_issue.py` | feat | Contratos (`CloseIssueFlags`, `CloseIssueDecision`, `CloseIssueOutcome`) e a árvore de decisão |
| `langs/es.json`, `es_es.json`, `fr.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json` | i18n | 4 chaves novas traduzidas |
| `tests/issue_autoclose/test_resolve_close_issue.py` | test | 40 testes (gates, registro, verificação, decisão e aviso de branch) |
| `CONTEXT.md` | docs | Termo **Close issue decision** |
| `src/issue_autoclose/__init__.py` | docs | Lista de módulos do pacote completa |

### Impact

- **Functionality:** nenhuma mudança de comportamento ainda — o módulo ainda
  não é chamado pelo `cli()` (T6). A feature continua inativa para o usuário.
- **Performance:** no caminho comum (sem registro ou sem permissão de
  pergunta) não há rede; a verificação é uma chamada com timeout padrão de
  5 s; `get_default_branch` só é chamada quando a pergunta será feita.
- **Compatibility:** nenhuma assinatura pública existente mudou. A função é
  isolada e só depende de `ScmProvider`, do contrato `load()`/`clear()` do
  registro e de um `ask` injetado.
- **Fronteira preservada:** o módulo não imprime, não importa `click` nem
  `requests`; `warning` volta para o chamador imprimir, e o aviso de branch
  viaja dentro da decisão porque já foi mostrado na pergunta (a T6 não deve
  imprimi-lo de novo).
- **Testes:** 40 novos; nenhuma regressão.

### Verificação da suíte

- `python -m pytest tests/issue_autoclose -q` → **75 passed, 15 subtests
  passed**.
- `python -m pytest tests/issue_autoclose tests/scm -q` → **396 passed,
  2 skipped, 33 subtests passed**.
- `python -m pytest tests/test_i18n.py -q` → **22 passed** (paridade, chaves
  órfãs e tradução idêntica ao inglês).
- Suíte ampla sem os dois arquivos de UI instáveis (`test_config_app.py`,
  `test_commit_app.py`) e com a deseleção do teste pré-existente que trava sem
  TTY: **3114 passed, 2 skipped, 1 deselected, 156 subtests passed**
  (301,76 s).
  - A primeira execução da suíte ampla teve 8 falhas em `tests/test_plugins.py`
    (`len(rules)` 8 em vez de 1). Causa: o `check_and_update_hooks_scripts()`
    chama `load_dotenv(ENV_FILE, override=True)` quando o
    `SCRIPTS_VERSION` local está defasado, e o `~/.gitpr/.env` real traz
    `GITPR_LINTER_SECURITY='true'`, sobrescrevendo o pin do `conftest.py`
    pelo resto do processo — o vazamento já documentado nos relatórios de
    2026-10-30. É pré-existente, alheio à T4 (os testes passam isolados e na
    reexecução após a marcação ser regravada).
- Nenhum `git add`, `git commit` ou `git push` — tudo permanece na árvore de
  trabalho.

### Divergências em relação ao plano (detalhes internos)

- O plano previa usar `registry.matches_repo(owner_repo)`; a implementação lê
  o registro uma única vez e compara `repo_ref.display` com `issue.repo` via
  `casefold()`. `matches_repo()` relê o arquivo e devolve `False` tanto para
  "outro repositório" quanto para "registro corrompido", o que tornaria o
  ramo `registry-error` inalcançável depois do `load()`.
- `closing_line` só é chamada quando uma decisão é possível (aceite ou
  pergunta), não nos caminhos de pulo.
- Nenhuma divergência de SPEC/ADR; `CloseIssueFlags` entrou como aprovado.

### Next steps

- T5: inserção idempotente da closing line logo antes do badge, depois da
  seção Explain e antes de gravar o `.md`.
- T6: integração no `cli()` antes da TUI de stage, com `--close-issue` /
  `--no-close-issue` mutuamente exclusivos; imprimir `outcome.warning` e
  limpar o registro quando o PR for criado (ADR-007).
- T7: `GITPR_ISSUE_AUTOCLOSE` / `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` no schema e na
  TUI de configuração.
- T8: métrica `issue_autoclose` (`asked`, `accepted`, `skipped_reason`).
- T9: documentação do usuário.
- Aguardar confirmação do usuário antes da T5.
