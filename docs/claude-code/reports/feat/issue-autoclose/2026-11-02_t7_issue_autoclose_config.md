## Completion Report — T7: configuração do issue-autoclose

### What was done

- **Getters** (`src/config.py`), inseridos depois de
  `risk_scoring_in_review_enabled()` e reutilizando os helpers genéricos do
  fim do arquivo:
  - `issue_autoclose_enabled()` → `_env_bool_default_true("GITPR_ISSUE_AUTOCLOSE")`
    (opt-out: só `false/0/no/off/n` desliga, como `badge_enabled()`);
  - `get_issue_autoclose_timeout()` → `_env_positive_int("GITPR_ISSUE_AUTOCLOSE_TIMEOUT", 5)`
    (inteiro > 0; lixo, vazio, zero, negativos e `2.5` caem em 5 — o mesmo
    contrato do validador `KIND_INT` da TUI).
- **Schema e TUI** (`src/config_schema.py`): dois `ConfigField` na categoria
  `issue`, logo após `OUTPUT_FILE_NAME_ISSUE`:
  - `GITPR_ISSUE_AUTOCLOSE` — `KIND_BOOL`, default `"true"`;
  - `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` — `KIND_INT`, default `"5"`.
  Sem `advanced` (proibido fora da categoria `advanced`), sem `group` e sem
  `show_if` (o controlador só aceita enums). **Nenhuma mudança em
  `src/ui/config_app.py`**: a tela é dirigida pelo schema, então o toggle
  aparece como `Switch` e o timeout como `Input` validado no F2, exatamente
  como `GITPR_BADGE` e `GITPR_REVIEWER_SUGGESTION_TOP_N`.
- **Ligação no fluxo** (`src/main.py::_prepare_close_issue`):
  - `GITPR_ISSUE_AUTOCLOSE` é lido **antes de construir o `IssueRegistry`** —
    o construtor roda `git rev-parse`, então um gate depois dele ainda
    custaria um subprocesso. Desligado → `(None, None, None)` com uma única
    leitura de env, sem YAML, provider ou rede.
  - O timeout é lido **tarde**, já na chamada de `resolve_close_issue`, para
    que os caminhos "sem registro" e "desligado" não paguem nem essa leitura.
  - `enabled` **não** é repassado ao caso de uso: depois do curto-circuito ele
    só poderia ser `True`; o parâmetro da T4 e seu teste continuam válidos
    para outros chamadores. O docstring de `resolve_close_issue` foi ajustado
    para dizer que quem lê a chave é o fluxo do PR.
  - Desligado **não limpa** o registro (ADR-007): ao religar, a issue ainda
    registrada continua disponível.
- **i18n**: 4 chaves novas nos 6 arquivos `langs/*.json` (1694 chaves por
  arquivo), inseridas pelo `tests/sync_i18n.py` e traduzidas de verdade, com
  ordem alfabética, `indent=2` e CRLF preservados; `es.json`/`fr.json`
  idênticos a `es_es.json`/`fr_fr.json`:
  - `Close Issue with Pull Request`
  - `Offers to add the closing line (close #N) for the issue created with gitpr -is to the pull request description. Enabled by default; false turns it off.`
  - `Issue Lookup Timeout`
  - `Maximum time in seconds to wait for the forge when checking the recorded issue. Invalid or non-positive values fall back to 5.`
- **Hermeticidade** (`tests/conftest.py`): pin de `GITPR_ISSUE_AUTOCLOSE`
  para `"true"`, **depois** do snapshot de `AMBIENT_ENV_KEYS` — um perfil de
  desenvolvedor com a feature desligada não muda o caminho exercitado pelos
  testes do fluxo de PR, e a tela de configuração não marca o campo como
  definido no shell. O timeout não é pinado: todo teste que o afirma patcha o
  getter.
- **Testes**:
  - novo `tests/test_config_issue_autoclose.py` (10 testes + subtests):
    parsing dos dois getters (variantes true/false, timeout válido/inválido),
    presença no schema com `KIND_BOOL`/`KIND_INT`, defaults, `advanced`/
    `read_only` falsos, `validate_field_value` aceitando o default e
    rejeitando `0`, `-1`, `abc`, `1.5` e `maybe`, e ausência das chaves em
    `DEFAULT_CONFIG` (documenta a decisão de não semear);
  - `tests/issue_autoclose/test_close_issue_wiring.py` ganhou 3 testes e o
    `_run` passou a patchar os getters e a expor o mock da **classe**
    `IssueRegistry`: config desligada retorna cedo com
    `registry_cls.assert_not_called()` (prova que o `git rev-parse` não roda),
    config desligada vence `--close-issue`, e o timeout configurado (17)
    chega em `resolve_close_issue(...)`. O teste de encaminhamento agora
    confere também `kwargs["timeout"] == 5`.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/config.py` | feat | `issue_autoclose_enabled()` e `get_issue_autoclose_timeout()` |
| `src/config_schema.py` | feat | 2 `ConfigField` na categoria `issue` |
| `src/main.py` | feat | Gate de configuração antes do registro; timeout repassado ao caso de uso; docstring |
| `src/issue_autoclose/resolve_close_issue.py` | docs | Docstring: quem lê `GITPR_ISSUE_AUTOCLOSE` é o fluxo |
| `langs/{es,es_es,fr,fr_fr,pt_br,pt_pt}.json` | feat | 4 chaves novas traduzidas |
| `tests/conftest.py` | test | Pin de `GITPR_ISSUE_AUTOCLOSE` |
| `tests/test_config_issue_autoclose.py` | test | Novo: getters + schema |
| `tests/issue_autoclose/test_close_issue_wiring.py` | test | Config desligada, ordem vs `--close-issue`, timeout |
| `docs/claude-code/plans/feat/issue-autoclose/2026-11-02_feat_issue_autoclose_t7_config.md` | docs | Cópia do plano aprovado |

### Impact

- **Functionality:** a TUI `gitpr config` passa a exibir, na categoria Issue,
  o switch "Close Issue with Pull Request" e o campo "Issue Lookup Timeout";
  o fluxo do PR respeita o switch e usa o timeout configurado nas leituras do
  forge. Com a feature desligada, o custo é uma leitura de env — nenhum
  subprocesso, YAML, provider ou rede.
- **Performance:** uma leitura de env a mais por execução do ramo PR; o
  timeout só é lido quando um registro existe e o caso de uso é chamado.
- **Compatibility:** nenhuma assinatura pública mudou. `resolve_close_issue`
  continua aceitando `enabled`/`timeout`; o fluxo apenas deixa de passar
  `enabled`. As chaves novas não são semeadas em `~/.gitpr/.env`
  (`setup_environment()` escreveria em todo perfil), seguindo `GITPR_BADGE`.
- **Fronteira preservada:** nenhum `requests` novo; o registro continua sem
  token; nenhuma chave é impressa em log.

### Verificação da suíte

- `python -m pytest tests/test_config_issue_autoclose.py tests/issue_autoclose/test_close_issue_wiring.py -q`
  → **32 passed, 30 subtests passed**.
- `python -m pytest tests/test_i18n.py tests/test_config_schema.py tests/test_config_validation.py -q`
  → **108 passed, 18 subtests passed**.
- `python -m pytest tests/issue_autoclose tests/scm -q`
  → **437 passed, 2 skipped, 74 subtests passed**.
- `python -m pytest tests/test_config_app.py -q`
  → **88 passed** (9 min 48 s, suíte lenta).
- Suíte ampla (sem `test_config_app.py`/`test_commit_app.py` e com a
  deseleção do teste de baseline que trava sem TTY):
  **3158 passed, 2 skipped, 1 deselected, 227 subtests passed** e as
  **mesmas 8 falhas pré-existentes de `tests/test_plugins.py`** já
  documentadas nas T1–T6 (`load_dotenv(ENV_FILE, override=True)` em
  `check_and_update_hooks_scripts()` traz `GITPR_LINTER_SECURITY='true'` para
  o processo quando o sync de hooks dispara). Em isolamento,
  `python -m pytest tests/test_plugins.py -q` → **17 passed**.

### Divergências em relação ao plano

- Nenhuma divergência de SPEC/ADR. Duas decisões registradas:
  - o fluxo **não** repassa `enabled` ao caso de uso (o plano admitia as
    duas formas); preferiu-se não passar um valor que só pode ser `True` e
    ajustar o docstring da T4;
  - a atualização da linha da categoria Issue e da contagem de campos em
    `docs/config-tui.md` (+4 traduções) permanece na T9, junto do
    README/ajuda e do changelog, porque a T7 do SPEC pede apenas o schema.
- **Nota para a T8:** como `_prepare_close_issue` curto-circuita, o fluxo
  nunca produz `CloseIssueOutcome(skipped_reason="disabled")`; o valor segue
  válido no caso de uso (teste da T4). Se a métrica `issue_autoclose` quiser
  registrar esse skip, o evento precisa nascer no ramo do helper.

### Next steps

- T8: métrica `issue_autoclose` (`asked`, `accepted`, `skipped_reason`) e a
  i18n restante da pergunta/avisos.
- T9: documentação de usuário — README/ajuda da CLI, changelog e atualização
  de `docs/config-tui.md` (linha da categoria Issue, "FIELDS (83 fields)" →
  85 e "thirteen categories") nas 4 traduções.
- Commit sugerido (isolado):
  `feat: add issue autoclose configuration`
- Aguardar confirmação do usuário antes da T8.
