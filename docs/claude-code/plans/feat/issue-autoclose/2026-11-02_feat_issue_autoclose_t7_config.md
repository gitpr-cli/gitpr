# Plano — T7: configuração do issue-autoclose

## Contexto

As T1–T6 entregaram a feature ponta a ponta: registro local, gravação após
`gitpr -is`, decisão `resolve_close_issue`, inserção idempotente da closing
line, integração no fluxo do PR, flags `--close-issue` / `--no-close-issue` e
limpeza do registro (ADR-007).

`resolve_close_issue` já aceita `enabled=True` e `timeout=5` (gates do caso de
uso — `enabled=False` devolve `skipped_reason="disabled"` antes de ler o
registro) e o docstring dele diz que o chamador liga
`GITPR_ISSUE_AUTOCLOSE` e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT`. Hoje
`_prepare_close_issue` usa os defaults: a configuração não existe em lugar
nenhum — nem getter, nem schema, nem TUI, nem teste.

A T7 fecha essa lacuna (SPEC T7 + ADR-005 revisão T0): as duas chaves no schema
(exibidas pela TUI `gitpr config`, que é dirigida por dados) e o fluxo
lendo-as.

## Abordagem

### 1. Getters em `src/config.py`

Inserir depois de `risk_scoring_in_review_enabled()` (~linha 505), junto dos
booleanos do fluxo de PR, reutilizando os helpers genéricos do fim do arquivo
(`_env_bool_default_true` ~1012, `_env_positive_int` ~1024 — resolvidos em
tempo de chamada, então a posição posterior não importa; `mentor_include_analogy`
já faz o mesmo):

```python
def issue_autoclose_enabled():
    """Returns True when the PR flow may offer to close the recorded issue.

    Read-only opt-out: set GITPR_ISSUE_AUTOCLOSE=false in ~/.gitpr/.env to
    skip the feature for a run. Never auto-written to .env.
    """
    return _env_bool_default_true("GITPR_ISSUE_AUTOCLOSE")


def get_issue_autoclose_timeout():
    """Returns the forge read timeout in seconds (default 5)."""
    return _env_positive_int("GITPR_ISSUE_AUTOCLOSE_TIMEOUT", 5)
```

- `_env_bool_default_true`: qualquer coisa fora de `false/0/no/off/n`
  (case-insensitive, espaços aparados) mantém ligado — o contrato de opt-out
  de `badge_enabled()`, pelo helper genérico.
- `_env_positive_int` (não `_positive_float`): inteiro > 0; lixo, vazio, zero,
  negativos e `2.5` caem no default 5. É o espelho exato do que
  `validate_field_value` exige de `KIND_INT`, e o `ScmProvider` declara
  `timeout: int`.

### 2. Schema e TUI — `src/config_schema.py`

Dois `ConfigField` na categoria `issue`, logo depois de
`OUTPUT_FILE_NAME_ISSUE` (~linha 679). A TUI é dirigida pelo schema:
`KIND_BOOL` já vira `Switch` (salvo como `"true"`/`"false"`) e `KIND_INT` já
vira `Input` validado no F2 — **nenhuma mudança em `src/ui/config_app.py`**.
`GITPR_BADGE` é o precedente de booleano default-true exibido como `Switch`.

```python
ConfigField(
    key="GITPR_ISSUE_AUTOCLOSE",
    label=__("Close Issue with Pull Request"),
    description=__(
        "Offers to add the closing line (close #N) for the issue created "
        "with gitpr -is to the pull request description. Enabled by "
        "default; false turns it off."
    ),
    category="issue",
    kind=KIND_BOOL,
    default="true",
),
ConfigField(
    key="GITPR_ISSUE_AUTOCLOSE_TIMEOUT",
    label=__("Issue Lookup Timeout"),
    description=__(
        "Maximum time in seconds to wait for the forge when checking the "
        "recorded issue. Invalid or non-positive values fall back to 5."
    ),
    category="issue",
    kind=KIND_INT,
    default="5",
),
```

- Sem `advanced`: `test_config_schema.py` proíbe `advanced=True` fora da
  categoria `advanced`; o toggle precisa ficar visível (Q10 da entrevista).
- Sem `show_if`: o controlador só aceita enums, não bool — o timeout fica
  sempre visível.
- Labels/descrições são literais `__()`; o extrator AST do `sync_i18n.py`
  dobra concatenações implícitas.

### 3. Ligação no fluxo — `src/main.py::_prepare_close_issue`

Ler `enabled` **antes de construir o registro** e curto-circuitar. Importante:
`IssueRegistry.__init__` roda `git rev-parse` (`issue_registry.py` →
`repo_root()`), então um gate de configuração depois do construtor ainda
custaria um subprocesso.

```python
from src.config import get_issue_autoclose_timeout, issue_autoclose_enabled
...
if flags.disabled:
    return None, None, None

if not issue_autoclose_enabled():
    return None, None, None

registry = IssueRegistry()
...
outcome = resolve_close_issue(
    provider,
    registry,
    repo_ref,
    flags=flags,
    is_tty=may_ask,
    target_branch=target_branch,
    ask=lambda question, default=True: click.confirm(question, default=default),
    timeout=get_issue_autoclose_timeout(),
)
```

- **Timeout lido tarde**, só quando um registro existe e o fluxo chegou ao
  caso de uso: os caminhos "sem registro" e "desligado" continuam sem I/O
  extra.
- **`enabled` não é repassado**: depois do curto-circuito ele só poderia ser
  `True`, então passá-lo seria peso morto e sugeriria que o caso de uso é a
  autoridade do switch. O parâmetro `enabled` da T4 e seu teste permanecem
  (contrato válido para outros chamadores); atualizar a frase do docstring
  em `resolve_close_issue.py:83-84` para dizer que o fluxo do PR lê
  `GITPR_ISSUE_AUTOCLOSE` antes e nunca chama a função quando é falso.
- Atualizar o docstring de `_prepare_close_issue` mencionando o gate de
  configuração antes do registro.
- **Desligado vence `--close-issue`**: ordem já fixada na T4 (enabled antes de
  accept); a T7 só a torna configurável. Coberto por teste.
- Desligado **não limpa** o registro (ADR-007): voltar a ligar encontra a
  issue ainda registrada.

### 4. i18n

Quatro chaves novas (labels/descrições acima), traduzidas nos 6 arquivos
`langs/{pt_br,pt_pt,es,es_es,fr,fr_fr}.json`. Fluxo: adicionar os campos,
rodar `python tests/sync_i18n.py` (insere o inglês), substituir os valores;
manter ordem alfabética, `indent=2`, CRLF; `es.json`/`fr.json` idênticos a
`es_es.json`/`fr_fr.json`. `tests/test_i18n.py` reprova chave ausente e
tradução idêntica ao inglês.

### 5. Hermeticidade da suíte

Adicionar em `tests/conftest.py`, **depois** do snapshot de `AMBIENT_ENV_KEYS`
(após `os.environ["LANG_VERSION"] = __lang_version__`), como o pin de
`GITPR_LINTER_SECURITY`:

```python
# Several tests drive the PR flow; a developer profile with the feature off
# would change which path they exercise. Set after the i18n snapshot so the
# configuration screen does not flag the field as "set in the shell".
os.environ["GITPR_ISSUE_AUTOCLOSE"] = "true"
```

O timeout não precisa de pin: todo teste que o afirma patcha o getter.

## Arquivos

| Arquivo | Mudança |
|---|---|
| `src/config.py` | `issue_autoclose_enabled()` e `get_issue_autoclose_timeout()` |
| `src/config_schema.py` | 2 `ConfigField` na categoria `issue` |
| `src/main.py` | `_prepare_close_issue` curto-circuita antes do registro e repassa o timeout |
| `src/issue_autoclose/resolve_close_issue.py` | docstring: quem lê `GITPR_ISSUE_AUTOCLOSE` é o fluxo |
| `langs/{pt_br,pt_pt,es,es_es,fr,fr_fr}.json` | 4 chaves novas traduzidas |
| `tests/test_config_issue_autoclose.py` | novo: parsing dos getters + schema |
| `tests/issue_autoclose/test_close_issue_wiring.py` | config desligada, ordem vs `--close-issue`, repasse do timeout |
| `tests/conftest.py` | pin de `GITPR_ISSUE_AUTOCLOSE` |
| `docs/claude-code/plans/feat/issue-autoclose/2026-11-02_feat_issue_autoclose_t7_config.md` | cópia do plano aprovado |
| `docs/claude-code/reports/feat/issue-autoclose/2026-11-02_t7_issue_autoclose_config.md` | relatório de conclusão obrigatório |

## Testes

**Novo `tests/test_config_issue_autoclose.py`** — `unittest` no padrão de
`tests/test_config_suggest_reviewers.py` (`_env_patch` que patcha
`src.config.load_dotenv` e `src.config.os.getenv`):

- **Schema:** as duas chaves em `FIELDS_BY_KEY`, categoria `issue`,
  `KIND_BOOL`/`KIND_INT`, defaults `"true"`/`"5"`, `advanced is False`,
  `read_only is False`; `validate_field_value` aceita o default e rejeita
  `"0"`, `"-1"`, `"abc"`, `"1.5"` no timeout e `"maybe"` no bool.
- **Não seedadas:** ausentes de `DEFAULT_CONFIG` (documenta a decisão).
- **Booleano:** ausente → `True`; `true/1/yes/y/on/qualquer texto` (caixa e
  espaço) → `True`; `false/0/no/off/n` → `False`.
- **Timeout:** ausente → `5`; `"9"`/`" 9 "` → `9`; `"0"`, `"-3"`, `"abc"`,
  `"2.5"`, `""` → `5`.

**`tests/issue_autoclose/test_close_issue_wiring.py`:**

- `_run` passa a patchar `src.config.issue_autoclose_enabled` e
  `src.config.get_issue_autoclose_timeout` (defaults `True`/`5`) e expõe o
  mock da **classe** `IssueRegistry`;
- **config desligada:** `(None, None, None)`, `registry_cls.assert_not_called()`
  (prova que o `git rev-parse` não roda), zero `load_calls`, SCM/resolve/base
  nunca chamados;
- **config desligada vence `--close-issue`:** `CloseIssueFlags(accept=True)`
  ainda retorna cedo;
- **timeout configurado** (ex.: 17) chega em `resolve.call_args.kwargs["timeout"]`.

## Verificação

1. `python tests/sync_i18n.py`, traduzir, depois
   `python -m pytest tests/test_i18n.py tests/test_config_schema.py -q`.
2. `python -m pytest tests/test_config_issue_autoclose.py tests/issue_autoclose/test_close_issue_wiring.py tests/test_config_validation.py -q`.
3. `python -m pytest tests/issue_autoclose tests/scm -q`.
4. `python -m pytest tests/test_config_app.py -q` (lento e conhecido como
   instável; confirmar `Switch`/`Input` verdes).
5. Suíte ampla como nas T4–T6 (sem `test_config_app.py`/`test_commit_app.py`,
   com a deseleção do teste de baseline que trava sem TTY), documentando as 8
   falhas pré-existentes de `tests/test_plugins.py` se reaparecerem.
6. Relatório com commit sugerido (`feat: add issue autoclose configuration`) e
   parada para confirmação. Nenhum `git add/commit/push`.

## Fora de escopo

- **T8:** métrica `issue_autoclose` e a i18n da pergunta/avisos. Nota: como o
  helper curto-circuita, o fluxo nunca produz `skipped_reason="disabled"`; o
  valor continua válido no caso de uso (teste da T4) e a T8 deve registrar o
  skip no ramo do helper se quiser o evento.
- **T9:** documentação de usuário — README/ajuda, changelog e a atualização da
  linha da categoria Issue, da contagem de campos ("83 fields") e de
  "thirteen categories" em `docs/config-tui.md` + 4 traduções.
- MCP, chat e forges não-GitHub.

## Decisões de desenho

1. **Schema-only, fora do `DEFAULT_CONFIG`** — precedente de `GITPR_BADGE`:
   `setup_environment()` grava toda chave de `DEFAULT_CONFIG` faltante no
   `~/.gitpr/.env` real a cada execução; um opt-out que nasce ligado não deve
   ser escrito no arquivo de ninguém. O getter e a TUI respondem pelo default.
2. **Gate antes do registro** — o construtor do `IssueRegistry` roda
   `git rev-parse`; o curto-circuito custa uma leitura de env, nada de
   subprocesso, YAML, provider ou rede.
3. **Desligado vence `--close-issue`** — ordem herdada da T4; não é contrato
   novo.
4. **Timeout inteiro positivo** — espelha a validação `KIND_INT` da TUI.
5. **Sem tocar `src/ui/config_app.py`** — a tela é dirigida pelo schema.
