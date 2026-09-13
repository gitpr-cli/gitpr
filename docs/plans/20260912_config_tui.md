# `gitpr config` — TUI Master-Detail de Configuração

## Context

O GitPR expõe hoje **~50 variáveis** em `~/.gitpr/.env` (`DEFAULT_CONFIG` em [src/config.py:16-63](src/config.py#L16-L63) tem 39, e ~18 a mais são lidas sem serem semeadas). Não existe nenhuma interface: para mudar `GITPR_AUTO_STAGE` o usuário precisa saber o nome exato da variável, abrir o arquivo à mão, e adivinhar se o valor é `true`, `1` ou `yes`. Pior: os getters têm fallbacks **silenciosos** — `_positive_float()` ([src/config.py:124](src/config.py#L124)) engole lixo e volta ao default sem avisar, então um `GITPR_AI_TIMEOUT=abc` nunca se manifesta como erro.

**Resultado pretendido:** `gitpr config` abre uma TUI master-detail — menu lateral por categoria, campos editáveis inline à direita — que cobre todo o `.env` com defaults visíveis, validação por tipo, validação de credencial antes de persistir, e busca global.

> **Divergência do pedido original:** foi pedida uma *flag* `--config`; o grill fechou em **subcomando** `gitpr config` (mais idiomático para Click, e não disputa espaço no callback gigante de `src/main.py`). O molde é o subcomando `release` ([src/main.py:1607](src/main.py#L1607)).

---

## Decisões fechadas no grill

| #   | Decisão                                                                                                                                       |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Persistência:** buffer + `F2` explícito; `Esc` com alterações pendentes pede confirmação                                                    |
| 2   | **Segredos:** editáveis com input mascarado; **nunca** exibem o valor em claro (placeholder `•••••••• (definido)`)                            |
| 3   | **Fonte da verdade:** schema declarativo único                                                                                                |
| 4   | **Edição:** campos inline (`Switch` / `Input` / `Select`), sem modal                                                                          |
| 5   | **Taxonomia:** uma categoria por comando/flag                                                                                                 |
| 6   | **Catálogo:** tudo, com internas/marcadores atrás do toggle "Mostrar avançadas"                                                               |
| 7   | **`GITPR_LANG`:** aplica na hora + avisa "reinicie o GitPR para efeito completo"                                                              |
| 8   | **Entrada:** só `gitpr config`                                                                                                                |
| 9   | **Schema:** módulo novo `src/config_schema.py`; `src/config.py` ganha só funções novas — os 9 call-sites de escrita existentes ficam intactos |
| 10  | **Restaurar padrão:** `Ctrl+R` no campo focado, remove a linha do `.env`                                                                      |
| 11  | **Validar segredo:** sim, antes de persistir                                                                                                  |
| 12  | **Banner:** não mexer                                                                                                                         |
| 13  | **Quando valida:** só os segredos que **mudaram** nesta sessão                                                                                |
| 14  | **Falha de validação:** bloqueia só em `401`; erro de rede (`http_status == 0`) permite gravar                                                |
| 15  | **Tipo inválido:** bloqueia o `F2` com erro inline                                                                                            |
| 16  | **Env var do processo:** mostra o valor do arquivo **+** marcador `⚠ ambiente`                                                                |
| 17  | **`GITPR_SCM_TOKEN` cru:** fora da TUI (vence o criptografado e grava em texto plano)                                                         |
| 18  | **Chaves desconhecidas:** categoria `Desconhecidas`, criada só quando existirem                                                               |
| 19  | **Busca:** global com `/`, casa chave ou label em todas as categorias                                                                         |
| 20  | **Templates `OUTPUT_FILE_NAME*`:** bloqueia placeholder desconhecido (evita `KeyError`) **e** exige `{datetime}` (evita sobrescrita)          |
| 21  | **Validação de IA:** função nova em `config.py`, no molde de `validate_github_token()`                                                        |
| 22  | **Entrega:** completa — código + testes + docs + i18n                                                                                         |

---

## Fatos que moldam a implementação

Verificados no código, não presumidos:

- **`set_key()` é atômico** (temp file + `os.replace`, mesmo diretório), cria o arquivo se não existir, e **preserva comentários e ordem**. Só exige que o diretório pai exista — e [src/config.py:247](src/config.py#L247) já faz `os.makedirs`.
- **`unset_key()` existe** no python-dotenv 1.2.3 e **apaga a linha inteira**. Logo `remove_config_value()` é um wrapper fino — **não** precisa do `open(ENV_FILE, "w")` cru que [src/tui_issue.py:16-31](src/tui_issue.py#L16-L31) faz hoje.
- **`call_ai_model()` é inutilizável para validar credencial:** engole toda exceção num `except Exception` ([src/ai_providers.py:218](src/ai_providers.py#L218)) e retorna `None` após 3 tentativas com sleep de 2s. Um `401` viraria ~6s de espera reportados como falha genérica. O precedente correto é `validate_github_token()` ([src/config.py:545](src/config.py#L545)): retorna `(is_valid, error_message)` e separa `401` de rede.
- **`load_dotenv(ENV_FILE)` roda com `override=False`** em todo lugar: variável de ambiente do processo **vence** o `.env`. Por isso o valor exibido não pode sair de `os.getenv()` — precisa de `dotenv_values(ENV_FILE)`, que lê só o arquivo.
- **`gitpr -h config` vai abrir a TUI ignorando o `-h`**, porque o gate `if ctx.invoked_subcommand is not None: return` ([src/main.py:541](src/main.py#L541)) roda **antes** do bloco de `help_flag` ([src/main.py:547](src/main.py#L547)). Não vou mexer no roteamento global — `gitpr config -h` funciona e fica documentado.
- **`tests/test_i18n.py` quebra a suíte** se uma chave `__()` não existir nos 6 JSONs, ou se sobrar chave órfã. Os labels do schema **precisam** ser chamadas literais `__("...")` para o scanner de `tests/sync_i18n.py` encontrá-las.
- **Nenhum layout master-detail existe no repo** — todos os 5 apps Textual são `Header → Vertical → Footer`. APIs confirmadas no Textual 8.2.8: `Switch`, `Select` (`allow_blank=True` por padrão), `Input`, `ListView`, `ContentSwitcher`.
- **`ctrl+r` está livre** nos 5 apps e nos widgets nativos. Ocupados: `f1`/`f2`/`f3`, `f5`-`f8` (chat), `ctrl+s`/`ctrl+e` (chat), `ctrl+p` (paleta — exceto `LinterApp`, que esquece de desabilitá-la), e `Input`/`TextArea` capturam `backspace`, `delete`, `ctrl+d`, `ctrl+w`, `ctrl+k`, `ctrl+u`.

---

## Entregáveis

| Arquivo                                                | Tipo     | O quê                                                                                          |
| ------------------------------------------------------ | -------- | ---------------------------------------------------------------------------------------------- |
| `docs/survey/20260911_gitpr_config_tui_surveyfacts.md` | novo     | Survey completo deste grill (contexto, decisões, fatos)                                        |
| `src/config_schema.py`                                 | novo     | `ConfigField` + `CATEGORIES` + `FIELDS` (dado puro)                                            |
| `src/ui/config_app.py`                                 | novo     | `ConfigApp` + modais de confirmação e ajuda                                                    |
| `src/config.py`                                        | alterado | `read_env_file_values()`, `save_config_values()`, `remove_config_value()`, `validate_ai_key()` |
| `src/main.py`                                          | alterado | Subcomando `config`                                                                            |
| `src/updater.py`                                       | alterado | Bump de `__lang_version__`                                                                     |
| `langs/*.json` (6)                                     | alterado | Chaves novas de i18n                                                                           |
| `docs/config-tui.md` + 4 traduções                     | novo     | Documentação da feature                                                                        |
| `docs/plans/glossary-config-tui.md`                    | novo     | Glossário: os termos que esta feature introduz                                                 |
| `tests/test_config_schema.py` e +4                     | novo     | Testes                                                                                         |

---

## Design

### 1. Schema — `src/config_schema.py`

Dado puro, sem imports pesados (importante: `src/i18n.py` escreve no `.env` no import).

```python
@dataclass(frozen=True)
class ConfigField:
    key: str                    # "GITPR_AUTO_STAGE"
    label: str                  # __("Auto Stage")  — literal, o scanner de i18n precisa ver
    description: str            # __("Automatically stages...")
    category: str               # id da categoria
    kind: str                   # bool|int|float|str|enum|template|path|secret
    default: str                # espelha DEFAULT_CONFIG
    choices: tuple[str, ...] = ()
    advanced: bool = False
    validator: str | None = None   # "ai_key" | "scm_token"
```

Categorias (ordem do menu): `Geral`, `Provedores de IA`, `Pull Request`, `Commit`, `Code Review`, `Issue`, `Blame`, `Linter`, `Release`, `SCM/Forge`, `Filtros de Diff`, `Avançado`.

Distribuição das chaves que exigem decisão explícita:
- **`Geral`** — `GITPR_LANG`, `GITPR_COAUTHOR`
- **`Provedores de IA`** — `DEFAULT_AI_PROVIDER`, `GITPR_AI_TIMEOUT`, os 6 `*_API_MODEL_*`, `GEMINI_API_KEY_ENCRYPTED`, `DEEPSEEK_API_KEY_ENCRYPTED` (ambos `secret=True`, `validator="ai_key"`)
- **`Pull Request`** — `OUTPUT_FILE_NAME`, `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`, `GITPR_AUTO_MERGE`, `GITPR_SUGGEST_REVIEWERS`, `GITPR_REVIEWER_SUGGESTION_TOP_N`, `GITPR_REVIEWER_SUGGESTION_EXCLUDED`
- **`Commit`** — (nenhuma própria; existe para a taxonomia ficar completa e previsível)
- **`Code Review`** — `OUTPUT_FILE_NAME_REVIEW`, `OUTPUT_FILE_NAME_FULLREVIEW`, `OUTPUT_FILE_NAME_FILEREVIEW`
- **`Issue`** / **`Blame`** — `OUTPUT_FILE_NAME_ISSUE` / `OUTPUT_FILE_NAME_BLAME`
- **`Linter`** — `OUTPUT_FILE_NAME_LINTER`, `GITPR_LINTER_TIMEOUT`
- **`Release`** — `GITPR_RELEASE_*` (×4) + `OUTPUT_FILE_NAME_RELEASE`
- **`SCM/Forge`** — `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` (`secret`, `validator="scm_token"`), `GITHUB_TOKEN_ENCRYPTED` (`secret`, `validator="scm_token"`), `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME`
- **`Filtros de Diff`** — `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`
- **`Avançado`** (`advanced=True`) — `SCRIPTS_LANG`, `LANG_VERSION`, `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `SCRIPTS_VERSION`, `LINTER_PRESETS_VERSION`, `SPINNER_THINKING_WORDS`

**Fora da tela** (não são `ConfigField`): `GITPR_SCM_TOKEN` (token cru de CI — vence o criptografado e grava em claro), `GITPR_SHOW_LOGS` (chave morta — ver Dívidas), e `CI`/`GITHUB_ACTIONS` (variáveis de ambiente do processo, não do `.env`).

### 2. Camada de escrita — `src/config.py`

Quatro funções novas, todas append-only no arquivo:

- `read_env_file_values() -> dict[str, str]` — `dotenv_values(ENV_FILE)`. Lê **só o arquivo**, imune à poluição de `os.environ`. É o que alimenta a tela e o marcador `⚠ ambiente` (que compara com `os.getenv`).
- `save_config_values(values: dict[str, str]) -> None` — `os.makedirs` + `set_key` por chave. Segredos chegam aqui **já criptografados** via `encrypt_data()`.
- `remove_config_value(key: str) -> bool` — wrapper de `unset_key()`.
- `validate_ai_key(provider: str, api_key: str) -> tuple[bool, str]` — no molde de `validate_github_token()`: `ollama` → `(True, "")` sem rede; `gemini`/`deepseek` usam `_make_gemini_client`/`_make_openai_client` de [src/ai_providers.py](src/ai_providers.py) e fazem uma **listagem de modelos** (nunca `call_ai_model`, que engole o erro). Deixa a exceção do SDK subir e classifica: auth → `(False, "401 ...")`; rede/`gaierror` → `(False, "network ...")`.

Os 9 call-sites existentes de `set_key` **não são tocados**.

### 3. TUI — `src/ui/config_app.py`

Segue as convenções de [src/ui/issue_app.py](src/ui/issue_app.py): `TITLE`, `ENABLE_COMMAND_PALETTE = False`, `CSS` inline, `BINDINGS`, `Header`/`Footer`, lazy import no `main.py`, resultado exposto em `final_action`/`final_message`.

```
┌ Header ──────────────────────────────────────────┐
│ Configurações        [/ buscar...]  [ ] avançadas│
├──────────────┬───────────────────────────────────┤
│ Geral        │  Idioma                           │
│ Provedores IA│  [ pt_br            ▾ ]  ⚠ ambiente│
│ Pull Request │                                   │
│ ...          │  Co-autor                         │
│              │  [ ●] habilitado                  │
├──────────────┴───────────────────────────────────┤
│ Footer: F1 Ajuda · F2 Salvar · ^R Restaurar · …  │
└──────────────────────────────────────────────────┘
```

- **Layout:** `Horizontal` com `ListView` (sidebar, `width: 30`) + `VerticalScroll` (área principal).
- **Controles por `kind`:** `Switch` (bool) · `Input` (str/int/float/template/path) · `Select` (enum, `allow_blank=False`) · `Input(password=True)` (secret).
- **Segredos:** o widget nunca recebe o valor real. Mostra `••••••••  (definido)` quando a chave existe no arquivo; só entra no diff do save se o usuário digitar algo.
- **Dirty state:** dicionário `key → novo valor`, comparado contra o snapshot de `read_env_file_values()`. Alimenta o `Esc` (confirmação), o `F2` (validação) e o indicador visual.
- **`Ctrl+R`:** marca o campo para remoção (renderiza `— remover (padrão)`); o save chama `remove_config_value()`.
- **`/`:** foca um `Input` de busca; filtra por chave ou label em **todas** as categorias e troca a área principal por uma lista plana de resultados.
- **Toggle "avançadas":** `Switch` no cabeçalho; mostra/esconde os campos `advanced=True` e a categoria `Avançado`.
- **Categoria `Desconhecidas`:** montada dinamicamente só quando `read_env_file_values()` tem chaves fora do schema; campos em modo leitura.
- **`F2` (save):** valida os campos sujos → se algum falhar, erro inline (borda vermelha + mensagem) e o save não acontece. Se houver segredo sujo, roda a validação de rede num worker `@work(thread=True)` com spinner, depois `call_from_thread`. `401` bloqueia; rede permite. Sucesso → grava, `load_dotenv(ENV_FILE, override=True)`, limpa o dirty, `self.notify(...)` e **permanece na tela**.
- **`GITPR_LANG`:** ao salvar, chama `set_lang()`, recarrega as traduções e avisa que o efeito completo exige reiniciar.

**Atenção obrigatória:** o Textual substitui `sys.stdout` por um `_PrintCapture` sem fd válido. Qualquer `click.secho`/`echo` chamado de dentro do app quebra o layout. Copiar o padrão `_with_suppressed_stdout()` de [src/ui/pr_publish_app.py:72-142](src/ui/pr_publish_app.py#L72-L142) — incluindo o `_clear_click_cache()` que invalida o `lru_cache` de `_default_text_stdout`.

### 4. CLI — `src/main.py`

Subcomando `config` no molde de `release` ([src/main.py:1607](src/main.py#L1607)):

```python
@cli.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog="\b\n" + __(">> Full documentation:") + "\n" + get_doc_url("config-tui.md"),
)
def config():
    """Opens the interactive configuration screen for ~/.gitpr/.env. ..."""
    from src.ui.config_app import launch_config_app
    launch_config_app()
```

- **Não** chama `setup_environment()` — ela dispara `click.prompt` para API key, o que seria hostil dentro de uma TUI. A tela funciona em máquina limpa mostrando os defaults do schema.
- Sem entrada no `HELP_MAP`/`HELP_PRIORITY` (é subcomando, não flag) e sem mexer no banner.
- `launch_config_app()` (espelhando `launch_metrics_dashboard`, [src/ui/metrics_app.py:447](src/ui/metrics_app.py#L447)) faz `app.run()` e depois o `click.secho` do resultado.

### 5. i18n e docs

- Rodar `python tests/sync_i18n.py` para propagar as chaves novas aos 6 JSONs, depois traduzir os valores (o script preenche com o texto em inglês).
- Bump de `__lang_version__` em [src/updater.py:13](src/updater.py#L13) para o OTA de traduções disparar.
- `docs/config-tui.md` + `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md` — seguindo o padrão dos outros 37 docs.
- `docs/plans/glossary-config-tui.md` — os termos que esta feature introduz e que são ambíguos sem definição: **valor do arquivo** vs **valor efetivo**, **campo avançado**, **restaurar** (remover a linha, não reescrever o default).

---

## Passos

1. Salvar o survey em `docs/survey/20260911_gitpr_config_tui_surveyfacts.md`.
2. `src/config_schema.py` — `ConfigField`, `CATEGORIES`, `FIELDS` (labels como literais `__()`).
3. Teste de sincronia primeiro (`tests/test_config_schema.py`): falha enquanto o schema não cobrir `DEFAULT_CONFIG`.
4. `src/config.py` — as 4 funções novas + testes de round-trip em `.env` temporário.
5. `validate_ai_key()` + testes com SDK mockado.
6. `src/ui/config_app.py` — layout, navegação, dirty state.
7. Validação no `F2` (tipo, template, segredo) com worker.
8. Busca global, toggle de avançadas, categoria `Desconhecidas`, `Ctrl+R`.
9. Subcomando em `src/main.py` + `launch_config_app()`.
10. `python tests/sync_i18n.py`, traduzir os 6 JSONs, bump do `__lang_version__`.
11. `docs/config-tui.md` + 4 traduções + glossário.
12. Suíte inteira verde.

---

## Verificação

**Automatizada** — `pipenv run pytest tests/ -v` (a suíte inteira, não só os testes novos: `tests/test_i18n.py` é o gate que pega chave faltante ou órfã).

Testes novos:
- `test_config_schema.py` — toda chave de `DEFAULT_CONFIG` está no schema; sem chaves duplicadas; toda `category` resolve; todo `kind` é conhecido; `advanced` só em `Avançado`.
- `test_config_store.py` — round-trip `save` → `read` num `.env` temporário (patch de `ENV_FILE`); comentários e ordem preservados; `remove_config_value()` apaga a linha e é idempotente.
- `test_config_validation.py` — template: `{foo}` rejeitado, `{datetime}` ausente rejeitado, default aceito; tipo: `abc` em `GITPR_AI_TIMEOUT` rejeitado; `validate_ai_key` classifica `401` vs rede com SDK mockado.
- `test_config_app.py` — `App.run_test()`: monta, troca de categoria, dirty tracking, `F2` bloqueado por tipo inválido, `Ctrl+R` marca remoção, busca filtra.
- `test_config_cli.py` — `CliRunner`: `config` registrado, `gitpr config -h` mostra o help com a URL de doc.

**Manual** — `pipenv run python run.py config`:
1. Abre na categoria `Geral`; o `.env` real é lido e os valores aparecem.
2. Alterar `GITPR_AUTO_STAGE` → `F2` → conferir a linha no `~/.gitpr/.env` e que os comentários em volta sobreviveram.
3. `Ctrl+R` num campo alterado → salvar → a linha some do arquivo.
4. Digitar `abc` em `GITPR_AI_TIMEOUT` → `F2` é bloqueado com erro inline.
5. Apagar `{datetime}` de `OUTPUT_FILE_NAME` → `F2` bloqueado.
6. `GEMINI_API_KEY` com valor inválido → `F2` bloqueia com erro `401`. Desconectar a rede → o mesmo save **passa**.
7. `export GITPR_AUTO_STAGE=true` no shell, reabrir → o campo mostra `false` do arquivo **+** o marcador `⚠ ambiente`.
8. `/` e digitar `timeout` → aparecem as chaves de timeout de todas as categorias.
9. `Esc` com alterações pendentes → pede confirmação.
10. Adicionar `FOO=bar` ao `.env` à mão → categoria `Desconhecidas` aparece.

---

## Fora de escopo / limitações conhecidas

- **`gitpr -h config` abre a TUI e ignora o `-h`** — consequência do gate em [src/main.py:541](src/main.py#L541). Usar `gitpr config -h`. Documentado, não corrigido (mexer ali mudaria o comportamento de `-h` para todos os subcomandos).
- **Sem validação de conexão no save em v1** para segredos **já configurados e não alterados** (decisão 13). O `.env` pode conter um token velho antes da tela abrir.
- **Reset por categoria** adiado — `remove_config_value()` já fica genérica para que seja só UI depois.
- **Sem ação de "revelar" segredo.**

## Dívidas registradas (não fazem parte desta feature)

- **`GITPR_SHOW_LOGS` é uma chave morta**: declarada em [src/config.py:34](src/config.py#L34), semeada em todo `.env`, prometida no `CHANGELOG.md:174` e documentada em [docs/pull-request-publication.md:414](docs/pull-request-publication.md#L414) — e **lida em lugar nenhum**. Não entra na TUI (mostrar um toggle que não faz nada é pior que não mostrar). Decidir: implementar ou remover do `DEFAULT_CONFIG`.
- **O banner de abertura está desatualizado** ([src/main.py:64-70](src/main.py#L64-L70)): não lista `--dashboard`, `--init`, `--base` nem `--plugins`.
- **`DEFAULT_CONFIG` derivado do schema**: com o schema no lugar, o dict de seeding passa a ser redundante. Refactor mecânico, mas toca um arquivo importado por tudo — fica para depois.
- **`get_ai_timeout()` tem docstring mentindo**: diz "default 600" ([src/config.py:134](src/config.py#L134)), o fallback real é `180.0`.
- **`LinterApp` não desabilita a command palette** ([src/ui/linter_app.py](src/ui/linter_app.py)) — os outros 4 apps setam `ENABLE_COMMAND_PALETTE = False`. Provável `ctrl+p` preso à toa.
