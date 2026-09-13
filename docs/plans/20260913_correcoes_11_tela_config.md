# Tela `gitpr config` — 11 itens: seções filtradas, sub-cabeçalhos, botões de download e link de doc

## Context

A tela `gitpr config` foi usada de verdade e expôs 11 problemas de **organização**. Nenhum é bug de lógica: a tela mostra a configuração de um jeito que não corresponde ao modelo mental de quem usa — variável na seção errada (1), seções misturando forges/providers diferentes (2, 3), campo de versão vazio (4), lista ilegível (5), campo que deveria ser escolhível e não é (6), falta de botões para forçar download (5, 7, 8), ordem dos campos (9), falta da seção Smart Exclude (10) e falta de link para a doc técnica em cada seção (11).

**Entrega 1 = itens 1–9 e 11** (esta). **Entrega 2 = item 10** (Smart Exclude), esboçada no fim.

### Quatro fatos medidos que mudam o desenho

1. **`GITPR_SCM_TOKEN` é universal, não do GitHub.** `config.get_scm_token()` a lê para *toda* forge ([config.py:474-484](src/config.py#L474-L484)). Ela vai para **SCM / Forge solta, sempre visível** (sua decisão), fora dos sub-grupos por forge.

2. **`SCRIPTS_LANG` não é campo de usuário — é marcador documentado.** O instalador o grava ([core.py:1407](src/core.py#L1407)) e o auto-sync o compara ([core.py:1435-1440](src/core.py#L1435-L1440)); 15 arquivos de doc (README, ARCHITECTURE, hooks-versioning ×5 idiomas) o descrevem como "idioma dos scripts instalados". Mas a tela o expõe como "Hooks Language" e o item 6 quer escolhê-lo. **Uma chave só não consegue ser ao mesmo tempo "o que eu quero" e "o que está instalado"** — a comparação viraria tautologia. Solução: `SCRIPTS_LANG` passa a ser a **escolha** (editável, `""` = automático) e nasce `SCRIPTS_INSTALLED_LANG` com o **registro do que está em disco** (read-only, visível).

3. **O bug de idioma dos hooks é pior do que "não baixa".** `_SCRIPT_LANG_SUFFIXES = {"pt_br","pt_pt","fr","es"}` ([core.py:90](src/core.py#L90)) é comparado contra `CURRENT_LANG`, que produz `es_es`/`fr_fr` — nunca casa. Traço real: para um usuário `fr_fr`, o instalador grava `SCRIPTS_LANG=""` e o gate compara `""` com `""` → **estável e silencioso**: ele recebe hooks em inglês para sempre, mesmo com `scripts/*.fr.sh` publicados. (Não é loop de re-download; é nunca baixar a tradução.)

4. **Os loaders já sabem baixar — falta só o `force`.** Nenhum dos cinco tem parâmetro de força; todos são gateados por `os.getenv("*_VERSION") != constante`. Forçar = curto-circuitar o gate, e a **única prova honesta de sucesso é reler o ARQUIVO** (`read_env_file_values()`), nunca `os.getenv` — `load_dotenv(override=False)` já copiou o valor antigo para o processo.

### Fatos do Textual (medidos, não supostos — evita retrabalho)

| Questão                                | Resultado medido                                                   |
| -------------------------------------- | ------------------------------------------------------------------ |
| altura de `Button`                     | padrão **3 linhas**; `compact=True` → **1 linha**                  |
| `line-pad: 0`                          | CSS **inválido** no Textual 8 — afinar botão só com `compact=True` |
| `[link=https://x]texto[/link]`         | **`MarkupError`** — o parser do Textual não é o do Rich            |
| `Select(value="", allow_blank=False)`  | **`InvalidSelectValueError` no mount, a tela inteira cai**         |
| widget focado recebe `display=False`   | o foco é **perdido** (`app.focused = None`)                        |
| `sys.stdout` redirecionado numa worker | seguro: `WindowsDriver._file = sys.__stdout__`                     |

Consequências diretas: o link de doc vira **`Button` + `webbrowser.open`** (precedente: `chat_app.py:88-94`, "Online Help"); o botão de ação vai numa **linha própria**, nunca dentro de `.field-head` (`height: 1`); e `""` precisa entrar em `DEFAULT_AI_PROVIDER.choices` **antes** de o filtro do item 3 tornar esse caminho alcançável de propósito.

---

## Entrega 1

### Etapa 1 — `src/doc_links.py` + `core.get_doc_url` delegando (base do item 11)

Novo módulo com `DOCS_BASE_URL` e `doc_url(filename)` — mesma URL de hoje, com `?lang=` só quando o idioma não é inglês. `core.get_doc_url()` ([core.py:455](src/core.py#L455)) passa a delegar, **sem mudar nenhum dos 11 call sites**. Separado de `core.py` de propósito: `config_app.py` não pode importar `src.core` (puxa `google.genai` a cada abertura da tela).

O *mapeamento* categoria→arquivo fica no schema (`Category.doc`), junto dos outros rótulos.

### Etapa 2 — schema (itens 1, 2, 3, 4, 6, 9)

**`src/config_schema.py`** — quatro atributos novos em `ConfigField` (todos com default, nada quebra):

```python
group: str = ""            # sub-cabeçalho dentro da categoria ("" = sem)
show_if: tuple = ()        # ((chave_controladora, valores_permitidos), ...) — AND
version_source: str = ""   # constante de fallback quando o marcador falta
action: str = ""           # botão de ação (ACTION_DOWNLOAD / ACTION_DOWNLOAD_WORDS)
```

Mais: `Category.doc` (nome do arquivo em `docs/`), o dataclass `Group(id, label)` e `GROUPS`, o kind `KIND_WORDS`, e as constantes `ACTION_*`, `VERSION_LANG`/`VERSION_SCRIPTS`, `GROUP_LABELS`. Rótulos de grupo genéricos passam por `__()`; nomes de produto/forge ficam literais (precedente: `_DISPLAY_NAMES` em `infrastructure/scm/factory.py:82-85`).

**Ordens exatas** (só dado — a tela ignora os atributos novos até a Etapa 3):

| Seção                | Ordem                                                                                                                                                                                                                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **AI Providers** (3) | `DEFAULT_AI_PROVIDER`, `GITPR_AI_TIMEOUT`, depois `GEMINI_*` `show_if=("gemini",)`, `DEEPSEEK_*` `show_if=("deepseek",)`, `OLLAMA_*` `show_if=("ollama",)` — sem sub-cabeçalho (o rótulo de cada campo já diz a qual provider pertence)                                  |
| **SCM / Forge** (2)  | soltos: `GITPR_SCM_PROVIDER`, **`GITPR_SCM_TOKEN`**, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`; `[GitHub]` `GITHUB_TOKEN_ENCRYPTED` `show_if=("", "github")`; `[Bitbucket]` `GITPR_SCM_USERNAME`; `[Azure DevOps]` `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT` |
| **Advanced** (9)     | `[Spinner]` `SPINNER_THINKING_WORDS` → `THINKING_WORDS_VERSION`; `[Git Hooks]` `SCRIPTS_LANG` → `SCRIPTS_INSTALLED_LANG` → `SCRIPTS_VERSION`; `[Downloads]` `LANG_VERSION`, `SMART_EXCLUDES_VERSION`, `LINTER_PRESETS_VERSION`                                           |

`GITPR_SCM_TOKEN`: `KIND_SECRET` (**nunca `KIND_STR`** — `KIND_STR` renderiza o token cru em texto claro, justamente o que motivou escondê-lo), `read_only=True`, descrição apontando `gitpr --init` como o caminho para configurá-lo. `read_only` já é respeitado pelo save (`_build_plan` pula) e o Ctrl+R responde com a mensagem existente.

`DEFAULT_AI_PROVIDER` ganha `""` em `choices` com rótulo `__("(not configured)")` — não `(automatic)`: `config.get_ai_provider()` só cai no fallback `gemini` quando a chave está **ausente**; vazia manda o `setup_environment()` para o prompt interativo. Isso exige a correção de uma linha no `Select` ([config_app.py:236](src/ui/config_app.py#L236)): hoje `_AUTOMATIC_LABEL` é incondicional para `""` e `choice_labels` nunca consegue sobrescrevê-lo.

**`SCRIPTS_LANG`** vira `KIND_ENUM` editável (rótulos reaproveitados de `GITPR_LANG`, `""` = segue o idioma da interface) e **`SCRIPTS_INSTALLED_LANG`** nasce `KIND_ENUM` read-only. Sem o segundo, `unknown_keys = set(file_values) - KNOWN_KEYS` ([config_app.py:331](src/ui/config_app.py#L331)) jogaria a chave nova direto na seção **Desconhecido** — exatamente o defeito do item 1.

### Etapa 3 — filtro por seleção + sub-cabeçalhos (itens 2, 3)

`_show_if_satisfied(field)` compara contra o valor **efetivo** — `pending` primeiro, arquivo depois (`effective_value()` já existe, [config_app.py:530-532](src/ui/config_app.py#L530-L532)). Só `on_select_changed` dispara `_render_view()`, e só quando a chave está em `VISIBILITY_CONTROLLERS` (derivado do schema, não uma lista à mão): trocar o provider/forge re-filtra o painel **na hora**, sem salvar.

`_render_view()` só alterna `row.display` e reescreve `Static`s — nunca escreve valor de widget — então não há `Changed` em cascata nem risco de laço. Duas decisões embutidas:

- **A busca ignora o filtro.** Procurar "deepseek" com o provider em Gemini acha os campos (e permite pré-preenchê-los: campo sujo é salvo independente de visibilidade — `_build_plan` já é cego a visibilidade e **não deve** ser "otimizado" para iterar só os visíveis).
- **Cabeçalho de grupo só aparece em vista de categoria**, e só se sobrou algum campo dele no filtro. Na busca os resultados são uma lista plana em ordem de `FIELDS`, então um cabeçalho rotularia só o primeiro pedaço do grupo: todos ficam ocultos.

`_mount_rows()` continua montando cada linha **uma vez** (nada de reconstruir), inserindo o `Static(id="grp_<id>")` imediatamente antes do primeiro campo de cada grupo; `_render_view()` só alterna `display`. Um id de grupo pertence a **uma** categoria só (o id do widget é derivado dele) — travado por teste.

Rede de segurança: se o foco se perder (só acontece se o widget focado for escondido), `_render_view()` devolve o foco à lista de categorias se `self.focused is None` — nunca rouba o foco da busca.

**Lacuna fechada:** `_reveal()` navega para a *categoria*, o que não basta quando o campo está escondido pelo filtro (F2 diria "1 campo precisa de atenção" e o usuário não veria nada). Passa a usar a busca — a única vista que ignora `show_if` — quando `_show_if_satisfied(field)` for falso.

### Etapa 4 — valor automático nos campos de versão (item 4)

`VERSION_SOURCES` mapeia cada `version_source` para a constante de código; em `_make_row`, campo `KIND_VERSION` **sem marcador no arquivo** mostra a constante e ganha a anotação `__("code version — not set in the file")`, com `is_set=False` e `pending` intocado (nada disso é gravável). O caso concreto é `LINTER_PRESETS_VERSION`, que só é gravado por `load_linter_presets()` ([linter_wizard.py:80](src/linter_wizard.py#L80)) — alcançável apenas por `gitpr --linter-setup`, que você nunca rodou: a caixa vazia era verdadeira e inútil.

| Campo                    | Marcador                 | Constante                 |
| ------------------------ | ------------------------ | ------------------------- |
| `LANG_VERSION`           | `LANG_VERSION`           | `__lang_version__`        |
| `SMART_EXCLUDES_VERSION` | `SMART_EXCLUDES_VERSION` | `__lang_version__`        |
| `THINKING_WORDS_VERSION` | `THINKING_WORDS_VERSION` | `__lang_version__`        |
| `LINTER_PRESETS_VERSION` | `LINTER_PRESETS_VERSION` | `__lang_version__`        |
| `SCRIPTS_VERSION`        | `SCRIPTS_VERSION`        | **`__scripts_version__`** |

`src.updater` entra por import de módulo em `config_app.py`: só stdlib + `click` + `i18n`, sem I/O no import ([updater.py:1-21](src/updater.py#L1-L21)).

### Etapa 5 — botões de download (itens 4, 5, 7, 8)

**Onde:** `Horizontal(classes="field-actions")` entre o controle e a ajuda — linha própria. `.field-head { height: 1 }` fica **intocado**, e a anotação é um `Static` 1fr que empurraria o botão para a lateral direita.

**Como:** `Button(compact=True, id=f"act_{key}")` + um `Static` de status ao lado. O id carrega **só a chave**; a ação é lida de volta do schema (`field.action` → `_ACTION_HANDLERS`), uma fonte de verdade só. `on_button_pressed` **precisa** do prefixo `act_`/`doc_open` como guarda: os modais tratam os próprios botões sem `stop()`, então `btn_discard`/`btn_keep`/`help_close` chegam neste handler também.

**`_focused_field()`** ([config_app.py:627-634](src/ui/config_app.py#L627-L634)) passa a reconhecer também o prefixo `row_`: clicar num botão foca o botão, e sem isso o Ctrl+R morreria em silêncio.

**Quatro botões**, todos `KIND_VERSION` exceto a lista de palavras:

| Campo                    | Ação              | Loader (import preguiçoso, dentro da worker)      |
| ------------------------ | ----------------- | ------------------------------------------------- |
| `LANG_VERSION`           | force download    | `i18n.get_translations(lang, force=True)`         |
| `SMART_EXCLUDES_VERSION` | force download    | `core._load_smart_excludes(force=True)`           |
| `LINTER_PRESETS_VERSION` | force download    | `linter_wizard.load_linter_presets(force=True)`   |
| `THINKING_WORDS_VERSION` | force download    | `spinner.reload_thinking_words(lang, force=True)` |
| `SPINNER_THINKING_WORDS` | download da lista | idem                                              |

`force=False` adicionado a: `i18n.get_translations`, `spinner._load_thinking_words` + `reload_thinking_words` (que passa a **retornar** a lista), `core._load_smart_excludes`, `linter_wizard.load_linter_presets`. Todos aditivos — nenhum call site existente muda.

**Worker:** `@work(thread=True)` **sem** `exclusive` (o `exclusive=True` cancela a worker anterior do mesmo método, e os botões compartilham `_download_marker` — um cancelaria o outro). Sucesso é verificado relendo o **arquivo** (`read_env_file_values()`), nunca `os.getenv`. O caso "inglês não tem o que baixar" é recusado no despachante, com mensagem própria, antes de a worker começar.

**Import preguiçoso é obrigatório:** `src.spinner` roda `THINKING_WORDS = _load_thinking_words()` **no import** ([spinner.py:137](src/spinner.py#L137)) — ou seja, download de rede ao abrir a tela. `src.core` puxa `google.genai`. Nenhum dos dois pode entrar no escopo de módulo de `config_app.py`.

**Saída padrão:** context manager local `_quiet_output()` (redirect de `sys.stdout` + `click._compat._default_text_stdout.cache_clear()`, como `pr_publish_app.py:116-142` já faz na thread de publicação). **Duplicado de propósito**, não importado: importar `src.ui.pr_publish_app` arrastaria `src.core` para o grafo da tela. Os loaders são silenciosos hoje; isso é seguro contra o import do `core` e contra falas futuras.

**Feedback:** o `Static` de status é curto (`✔ {version}` / `✖ not updated` / `Downloading…`); a frase inteira vai por `self.notify(...)` — canal de relato já usado pela tela, e a linha pode estar fora da vista. O botão fica desabilitado durante a execução (segundo clique impossível, não apenas ignorado). Ao terminar, `load_dotenv(ENV_FILE, override=True)` + releitura do arquivo, porque o loader gravou por trás da tela via `set_key`.

### Etapa 6 — Spinner Words como lista (item 5)

`KIND_WORDS` renderiza um `VerticalScroll` (id `value_<KEY>`) com **um** `Static` dentro, as ~263 entradas separadas por `·`, `max-height: 12` com borda: rola dentro de si mesmo, sem estourar a linha. Um `ListView` com 263 itens exigiria `clear()` assíncrono — exatamente o entrelaçamento que o docstring de `_mount_rows` proíbe — e 263 `Static`s quase dobrariam a árvore de widgets da tela. Um `Static.update()` é síncrono e atômico.

A lista vem de `self.raw_value` (**o arquivo**), coerente com a regra da tela ("o valor exibido vem do ARQUIVO, nunca de `os.getenv()`"), sem rede ao abrir. O separador é reimplementado localmente (`_split_words`) espelhando `spinner._parse_env_words` ([spinner.py:64](src/spinner.py#L64)) — importar `src.spinner` baixaria a lista ao abrir a tela. A anotação leva a contagem (`__("{count} word(s)")`) e `KIND_WORDS` implica `read_only`.

Após o download, `_load_thinking_words` **grava** `SPINNER_THINKING_WORDS` no `.env` ([spinner.py:107](src/spinner.py#L107)) — então a releitura do arquivo já traz a lista nova, e `set_words()` só precisa atualizar o `Static` e a anotação.

### Etapa 7 — Hooks Language editável (item 6)

Em `src/core.py`:

- `_SCRIPT_LANG_SUFFIXES` → **`HOOK_SCRIPT_SUFFIXES = {"pt_br": "pt_br", "pt_pt": "pt_pt", "es_es": "es", "fr_fr": "fr"}`**, com o comentário dizendo que a chave é o código do `GITPR_LANG` e o valor o sufixo publicado em `scripts/`. É a correção do bug do fato 3.
- `effective_hook_lang()` → `SCRIPTS_LANG` (a escolha) ou `CURRENT_LANG`; `""` é o "automático" do `Select`.
- `install_git_hooks()` passa a instalar no idioma **efetivo** (não em `CURRENT_LANG`) e grava `SCRIPTS_INSTALLED_LANG` = idioma efetivo, mantendo `SCRIPTS_VERSION`. `SCRIPTS_LANG` deixa de ser escrito pelo instalador — agora é do usuário.
- `check_and_update_hooks_scripts()` compara `SCRIPTS_INSTALLED_LANG` (o que está em disco) com `effective_hook_lang()` (o que se quer): os dois lados vêm de fontes independentes, então não há tautologia, a troca de idioma força a reinstalação e uma edição manual do `.env` também se resolve sozinha. O marcador de versão só é gravado quando **todos os 5 hooks** entram ([core.py:1403](src/core.py#L1403)), comportamento mantido.

### Etapa 8 — link de documentação por seção (item 11)

`Horizontal(id="category_doc")` no topo do painel direito: `Button(__("📚 Documentation"), compact=True, id="doc_open")` + o `Static` com a URL visível (para ler/copiar, como o CLI já imprime). `webbrowser.open` preguiçoso. A linha some na busca e na categoria sintetizada `unknown` (que não tem `Category`, portanto não tem doc) — e o `#category_help` continua sendo só a descrição.

| Categoria    | Documento                       | Observação                                                         |
| ------------ | ------------------------------- | ------------------------------------------------------------------ |
| General      | `config-tui.md`                 |                                                                    |
| AI Providers | `providers-ia.md`               |                                                                    |
| Pull Request | `pull-request-publication.md`   |                                                                    |
| Code Review  | `code-review-ia.md`             |                                                                    |
| Issue        | `gitpr-issue-option.md`         |                                                                    |
| Blame        | `blame-arqueologo.md`           |                                                                    |
| Linter       | `linter-regras-customizadas.md` |                                                                    |
| Release      | `release-notes.md`              |                                                                    |
| SCM / Forge  | `scm-multiforge.md`             |                                                                    |
| Diff Filters | `smart-excludes.md`             |                                                                    |
| Advanced     | `version-markers.md`            | **única sem traduções** — `?lang=` é inofensivo, serve a página EN |

### Etapa 9 — testes

**Quebram e precisam de ajuste** (`tests/test_config_schema.py`): `DELIBERATELY_HIDDEN` perde `GITPR_SCM_TOKEN` (o teste que trava a ausência falharia no instante em que o campo existir) — a constante vira um dict `chave → motivo`, hoje **vazio por desenho**: toda chave de `~/.gitpr/.env` passou a ter linha. `test_secret_fields_declare_a_validator` ganha `or field.read_only` (validador existe para provar valor *a ser gravado*; um segredo read-only nunca é gravado).

**Novas regras de schema:** grupo de um campo existe em `GROUPS`; um grupo pertence a **uma** categoria; campos de um grupo são contíguos; `show_if` aponta para `KIND_ENUM` e cada valor permitido está em `choices` (é o que pega um typo tipo `("DEFAULT_AI_PROVIDER", ("gemeni",))`); `KIND_VERSION ⇒ version_source` conhecido e vice-versa; `KIND_WORDS ⇒ read_only + ACTION_DOWNLOAD_WORDS`; toda `action` é conhecida e compatível com o kind; toda `Category.doc` termina em `.md`; toda `action` tem handler.

**Novos testes de tela** (`tests/test_config_app.py`, que **não quebra**: os ordinais fixos de `ListView.index` são ≤ 2 e a entrega 1 não cria categoria; `app.query("#value_X")` acha a linha mesmo com `display=False`): filtro por provider/forge (com o caso `DEFAULT_AI_PROVIDER=` vazio, regressão do crash), cabeçalhos de grupo aparecendo/sumindo, fallback de versão, a lista de palavras (sem `Input`, `Static` com as palavras e a contagem), os botões (patch no ponto de import, `await app.workers.wait_for_complete()` — `pilot.pause()` não basta para `@work(thread=True)` —, botão desabilitado durante, marcador relido, notify de sucesso **e** de falha), link de doc (`patch("webbrowser.open")`, some em `unknown` e na busca), e `_reveal` de campo filtrado.

`tests/test_core.py` ganha a classe do idioma dos hooks (`fr_fr` → `…-template.fr.sh`, `es_es` → `….es.sh`, `SCRIPTS_LANG` vencendo `CURRENT_LANG`, reinstalação exatamente quando o instalado difere do pedido). `test_smart_excludes.py` / `test_thinking_words.py` / `test_linter_presets` ganham um caso `force=True` cada (baixa mesmo com marcador igual; marcador regravado; cópia velha mantida na falha).

### Etapa 10 — i18n

~22 chaves novas: `(not configured)`, `Spinner`, `Git Hooks`, `Downloads`, `CI/CD Token (raw)` + descrição, `Installed Hooks Language` + descrição, `Installed Hooks Language`, `📥 Force download`, `📥 Download the word list`, `📚 Documentation`, `{count} word(s)`, `code version — not set in the file`, `Downloading…`, `✔ {version}`, `✖ not updated`, `{name} updated to {version}.`, `Could not download {name}. The previous copy stays in use.`, `English needs no translation pack — there is nothing to download.`, `•••••••• (set)`, mais a descrição reescrita de `SPINNER_THINKING_WORDS` e `SCRIPTS_LANG`.

Fluxo: escrever as chamadas `__()` em **linha única literal** (o scanner AST de `tests/test_i18n.py` e o regex de `tests/sync_i18n.py` não resolvem concatenação implícita), rodar o sync (que **poda órfãs** — não editar os JSON à mão antes), traduzir os 5 arquivos. Paridade nos 6 é obrigatória.

### Etapa 11 — docs e relatório

- 5 × `docs/config-tui*.md`: tabela de categorias da §1.1 com os sub-grupos novos, etiqueta de "Hooks Language" agora editável, `Spinner Words` como lista read-only, e o link de doc por seção.
- 5 × `docs/hooks-versioning*.md` + 1 linha em `docs/ARCHITECTURE*.md` e `README*.md`: `SCRIPTS_LANG` (escolha) vs `SCRIPTS_INSTALLED_LANG` (instalado) e o mapa de sufixos — 15 arquivos citam o marcador.
- Relatório obrigatório em `docs/claude-code/reports/develop_natan/2026-09-13_config_tui_layout_sections_downloads.md`.

### Ordem de execução

Cada passo deixa a suíte verde: (1) `doc_links` → (2) schema + testes de schema → (3) filtro + cabeçalhos → (4) fallback de versão → (5) botões + workers + `force=` nos loaders → (6) `KIND_WORDS` → (7) link de doc → (8) idioma dos hooks → (9) i18n + docs → (10) relatório.

---

## Entrega 2 — seção Smart Exclude (item 10), esboço

Os mecanismos que ela precisa **já existem** ao fim da entrega 1: `show_if` (gate por enum), `group` (sub-cabeçalhos), `action` (botão com canal de status), `KIND_WORDS` (lista read-only renderizada), `Category.doc` + botão de doc.

- Categoria nova **inserida imediatamente antes de `advanced`** (índice 10): todos os ordinais fixos da suíte são ≤ 2 e as referências a `advanced` já são dinâmicas, então essa posição mantém `test_config_app.py` válido.
- Três fontes: `~/.gitpr/conf/gitpr.docs-smart-excludes.json` e `~/.gitpr/conf/gitpr.smart-excludes.json` (globais, **somente leitura**, com botão de forçar download) e `.gitpr/conf/gitpr.smart-excludes.json` do projeto (editável, criável se não existir — `_seed_local_smart_excludes` já faz isso, [core.py:94](src/core.py#L94)).
- Explicação de como funciona + `Category.doc = "smart-excludes.md"` (mesmo documento que a categoria `diff` já aponta).
- Editor: outra leitura de `KIND_WORDS` generalizada para lista de padrões, com adicionar/alterar valores.

---

## Verificação

1. `pytest tests/ -q` — baseline atual **6 falhas pré-existentes** (`test_chat_backend::test_api_exception`, `test_main_suggest_reviewers::test_flag_appears_in_contextual_help`, `test_suggest_reviewers::TestFormatHelpers` ×2, `test_net_timeouts::TestTimeoutConfig` ×2), 938 passed, 2 skipped. Nenhuma nova é aceitável.
2. **Sonda headless** (`App.run_test(size=(w,h))`, como nas tarefas anteriores), com o `.env` real: provider `deepseek` → Gemini/Ollama ocultos e DeepSeek visível; trocar o `Select` para `ollama` re-filtra **sem F2**; forge `""` → `[GitHub]` visível e `[Azure DevOps]` não; sub-cabeçalhos presentes uma única vez; `THINKING_WORDS_VERSION` **imediatamente depois** de `SPINNER_THINKING_WORDS`; palavras renderizadas como lista com a contagem.
3. **Itens 4, 7, 8:** `LINTER_PRESETS_VERSION` vazio mostra `v0.0.24` + "code version — not set in the file"; apertar cada botão baixa de verdade e regrava o marcador em `~/.gitpr/.env` (conferir o arquivo, não `os.getenv`); desabilitar a rede e confirmar o notify de falha com a cópia anterior intacta.
4. **Regressão do crash do `Select`:** `.env` de teste com `DEFAULT_AI_PROVIDER=` (vazio) e a tela monta mostrando `(not configured)`, sem `InvalidSelectValueError`.
5. **Item 6 ponta a ponta:** num repo de rascunho, `SCRIPTS_LANG=fr_fr` → os hooks instalados vêm de `scripts/*.fr.sh` e `SCRIPTS_INSTALLED_LANG=fr_fr`; trocar para `es_es` no `.env` → o próximo `gitpr` reinstala uma vez e depois **estabiliza**; `SCRIPTS_LANG=` vazio segue `GITPR_LANG`.
6. **Item 11:** `patch("webbrowser.open")` e conferir a URL de cada uma das 11 seções (incluindo `?lang=pt_br`), e que a linha some em `unknown` e na busca.
7. **Visual:** `gitpr config` — rolagem da coluna direita preservada, Ctrl+R com um botão focado, Esc com pendências abrindo o modal, e a busca ainda achando um campo escondido pelo filtro.

## Fora de escopo

- Item 10 em si (entrega 2) e o marker `LINTER_PRESETS_VERSION` subir sozinho — ele continua dependendo de `gitpr --linter-setup` ou do botão novo.
- Nenhum `git commit`/`git add`/`git push` (regra do CLAUDE.md); tudo fica na working tree.

---

## Status da execução — 2026-09-13

**Entrega 1 concluída** (itens 1–9 e 11). Relatório: `docs/claude-code/reports/develop_natan/2026-09-13_config_tui_layout_sections_downloads.md`.

| Verificação | Resultado |
|---|---|
| 1. Suíte completa | **998 passed, 6 failed, 2 skipped** — as 6 são exatamente as pré-existentes. Baseline 938 → +60 testes passando |
| 2. Sonda headless do filtro e dos sub-cabeçalhos | Feita, incluindo o caso `DEFAULT_AI_PROVIDER=` vazio e o re-filtro sem F2 |
| 3. Botões de download contra o `~/.gitpr/.env` real | Os cinco terminam em `✔ v0.0.24`; `LINTER_PRESETS_VERSION` **ABSENT → v0.0.24**; o caminho de falha (URL inválida + marcador velho) reporta `✖ not updated` com a cópia anterior intacta |
| 4. Regressão do crash do `Select` | Coberta por `test_an_empty_provider_mounts_and_reads_as_not_configured` |
| 5. Item 6 ponta a ponta | Feita: `fr_fr`, `es_es`, `pt_br`, vazio (`GITPR_LANG`) e inglês, com `SCRIPTS_INSTALLED_LANG` correto e reinstalação única na troca |
| 6. Link de documentação das 11 seções | Coberta por testes (`test_every_section_shows_its_page`, `test_the_button_opens_the_page_of_the_section`, `test_the_unknown_section_shows_no_link`, `test_the_search_hides_the_link`) |
| 7. Passada visual | **Parcial** — a rolagem, o Ctrl+R com o botão focado, o Esc com pendências e a busca achando um campo filtrado têm teste; falta a conferência na máquina, com a janela real |

**Desvios deliberados do plano** (detalhados no relatório): a frase de sucesso é `"{name} is up to date ({version})."` (um download que falha e cai numa cópia já atual é indistinguível de um que deu certo) e `load_dotenv(ENV_FILE, override=True)` **não** é chamado depois do download. **Correção extra fora do plano:** `_interface_lang()` em `src/core.py` — `--lang` não chegava à instalação dos hooks por causa da cópia congelada de `CURRENT_LANG`.

**Entrega 2 (item 10) não iniciada.**
