## Completion Report — T3: gravação da issue criada (`register_created_issue`)

### What was done

- Criado `src/issue_autoclose/register_created_issue.py`, o único ponto que
  transforma a resposta de `create_issue` no registro local que o fluxo de PR
  lê de volta (ADR-001, Q9 da T0).
  - `RegistrationOutcome` (frozen): `recorded`, `skipped_reason`
    (`not-github`, `no-repo`, `invalid-result`, `write-failed`),
    `gitignore_updated`, `error`.
  - Gate `provider_is_github(provider)`: outro forge não toca em disco.
  - `repo` vem de `RepoRef.display` e precisa ser `owner/name`.
  - `number` precisa ser inteiro positivo (bool recusado) e `url` não vazio —
    gravar algo que o próprio `load()` rejeitaria seria pior que não gravar.
  - `created_at` em ISO 8601 com `timespec="seconds"`, o precedente de
    `create_baseline.py`/`release_engine.py`; `branch` vem do TUI.
  - **Nunca levanta:** `IssueRegistryError` e qualquer exceção viram
    `write-failed` + `error`, porque a issue já existe no forge e uma falha de
    bookkeeping não pode transformar um sucesso em erro.
- `IssueApp` (`src/ui/issue_app.py`): guarda a branch já calculada em
  `__init__` (`self.branch`) e, após `final_action = "created"` num fluxo
  GitHub, chama `register_created_issue(...)`.
  - `final_action` continua `"created"` em qualquer desfecho do registro.
  - `.gitignore` alterado → uma linha informativa anexada a `final_message`.
  - Registro não gravado → uma linha de aviso anexada; a criação continua
    reportada como sucesso e a métrica segue `status="success"`.
- Duas chaves i18n novas (aviso de `.gitignore` e aviso de falha), criadas via
  `python tests/sync_i18n.py` e traduzidas nos 6 arquivos de idioma.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/issue_autoclose/register_created_issue.py` | feat | `RegistrationOutcome` + `register_created_issue` (validação, gate GitHub, falha silenciosa) |
| `src/ui/issue_app.py` | feat | Guarda `self.branch`; grava o registro após criação bem-sucedida no GitHub e anexa os avisos |
| `langs/es.json`, `es_es.json`, `fr.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json` | i18n | 2 chaves novas traduzidas (`.gitignore` e falha de registro) |
| `tests/issue_autoclose/test_register_created_issue.py` | test | 12 testes: unidade (7), round-trip com `IssueRegistry` real (1), wiring do `IssueApp` (4) |

### Impact

- **Functionality:** só o caminho `gitpr -is` → F3 → GitHub muda: a issue
  criada passa a ser gravada em `.gitpr/conf/github.yml`. Forges não-GitHub,
  `-is` salvo localmente (F2) e o MCP não mudam. Nada ainda lê o registro — é
  a T4 que começa a consumi-lo.
- **Performance:** uma validação em memória e uma escrita atômica pequena por
  criação de issue; sem rede.
- **Compatibility:** nenhuma assinatura pública mudou. O arquivo de registro é
  criado só na primeira criação; `.gitpr/conf/gitpr.config.yml` continua
  versionado. Nenhum token, URL autenticada ou segredo entra no registro.
- **Fronteira preservada:** `register_created_issue` não imprime nada — devolve
  dados; `IssueApp` é quem monta as mensagens i18n.
- **Testes:** 12 novos, todos passando; a suíte existente não regride.

### Verificação da suíte

- `python -m pytest tests/issue_autoclose -q` → **35 passed, 9 subtests
  passed**.
- `python -m pytest tests/issue_autoclose tests/scm -q` → **356 passed,
  2 skipped, 27 subtests passed**.
- `python -m pytest tests/test_i18n.py -q` → **22 passed** (paridade, chaves
  órfãs e tradução idêntica ao inglês).
- Suíte completa sem os dois arquivos de UI instáveis (`test_config_app.py`,
  `test_commit_app.py`) e com a deseleção do teste pré-existente que trava sem
  TTY (`tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched`):
  **3074 passed, 2 skipped, 1 deselected, 150 subtests passed** (469,66 s).
- Nenhum `git add`, `git commit` ou `git push` — tudo permanece na árvore de
  trabalho.

### Next steps

- T4: `resolve_close_issue` — ler o registro, perguntar ao forge se a issue
  ainda está aberta (`get_issue`) e decidir o que oferecer ao usuário.
- T5: inserção idempotente da closing line logo antes do badge do PR.
- T6: integração no `cli()` com `--close-issue`/`--no-close-issue`.
- Aguardar confirmação do usuário antes da T4.
