# Survey — GitPR `demo` Mode (tour guiado sem API key)

> Levantamento completo da sessão de grill da skill `grill-with-docs`.
> Task: executar o plano `docs/plans/20260918_skill_gitpr_demo_mode_spec.md`.
> Data: 2026-09-18 · Branch: `develop_natan`

---

## 1. Contexto da tarefa

A spec `docs/plans/20260918_skill_gitpr_demo_mode_spec.md` (235 linhas, até então untracked) pede um comando `gitpr demo`: um tour guiado com diff de exemplo embutido no pacote, que roda logo após `pip install gitpr-cli` **sem API key, sem repositório Git e sem internet**, com o objetivo de reduzir o time-to-value do primeiro contato a segundos.

Enquadramento comercial (spec §11): Tier 1 (alto impacto, baixo esforço), tier Free/Community, função exclusiva de aquisição. Todas as análises de monetização anteriores identificaram a fricção "precisar de API key no primeiro uso" como o principal filtro que afasta usuários casuais antes de verem valor.

Escopo pedido: percurso de 6 etapas (boas-vindas → diff → commit → review → PR → próximos passos), `--scenario <nome>`, `--no-tui`, testes de isolamento de rede/repositório/config, documentação e empacotamento das fixtures.

---

## 2. Relatório de fatos levantados

Levantamento feito com agentes de exploração read-only sobre o repositório. **Sete premissas da spec não correspondem ao código.**

### 2.1 A camada de IA não tem classes

`src/ai_providers.py` contém **zero classes**, zero ABCs, zero Protocol. A superfície é de funções de módulo:

```python
def call_ai_model(provider, api_key, api_model, prompt, system_instruction,
                  quiet=False, action="ai_call"):   # ai_providers.py:101
```

Retorna `dict | None` (JSON já parseado internamente em `ai_providers.py:203`, com desembrulho de lista em `206-207` e injeção de `_telemetry_meta` em `213`). O despacho de provider é um `if provider == "gemini"` / `elif provider in ["deepseek", "ollama"]` inline (`:140`, `:168`), com branch final imprimindo "Unknown AI provider" (`:194`).

**Não existe mecanismo de fallback entre providers.** A docstring de `get_ai_provider()` (`config.py:267`) diz "or 'gemini' as fallback", mas isso é o *valor default*, não failover. A única resiliência é o retry 3× contra o mesmo provider dentro de `call_ai_model` (`:116-118`, `:137`).

A spec §4 assume `GeminiProvider`/`DeepSeekProvider`/`OllamaProvider` e pede que `FakeAIProvider` implemente "a mesma interface abstrata". **Não há interface para implementar.**

### 2.2 O pipeline real e seus pontos de interceptação

Toda a operação de commit/review/PR passa por uma função:

```
core.generate_pr_content(action_folder, action_type, diff_text,
                         provider="gemini", cache_scope="", store_diff=False)
```
`src/core.py:762`

Estágios internos, em ordem:

| Linhas | O que acontece |
|---|---|
| 786-791 | Guarda de diff vazio → `None` |
| 796-803 | `action_folder_map`: `pr`→`pr_desc`, `commit`→`commit`, `review`/`fullreview`/`filereview`→`review`, default `misc` — **reatribui `action_folder`** |
| 806 | `get_skill_context(action_type)` — injeção de skill |
| 810 | `task_complexity = "simple" if action_type == "commit" else "advanced"` |
| 813-864 | Montagem de prompt e system instruction por tipo de ação |
| 869-909 | Metadados de docs alterados prependidos em `instrucao_sistema` |
| **912** | **Leitura de cache:** `get_cached_response(action_folder, prompt + cache_scope)` |
| 913-925 | Hit → `log_command_metric(..., cache_hit=True)` → `return cached_data` |
| **928-937** | `get_api_key(provider)` — **desiste se ausente** |
| **941-950** | `get_api_model(provider, task_complexity)` — **desiste se ausente** |
| 962 | `chunks = split_diff_into_chunks(diff_text, max_tokens=90000)` |
| 978-985 | Chamada de IA (single-chunk) |
| 991-996 | `log_local_metric(command="map_reduce", status="triggered")` direto se chunked |
| 1033-1041 | Chamadas de chunk do map-reduce (`quiet=True`) |
| 1089-1096 | Chamada de reduce do map-reduce |
| **1102-1109** | **Gravação de cache:** `save_cached_response(...)` |
| 1110-1122 | `log_command_metric(...)` → `return result_json` |
| 1124-1131 | Métrica de falha → `None` |

Formato das respostas por operação:

| Operação | `action` | Chaves da resposta |
|---|---|---|
| commit | `"commit"` | `dict["commit_message"]` |
| review | `"review"`/`"fullreview"`/`"filereview"` | `dict["review"]` (**markdown, não findings estruturados**) |
| PR | `"pr"` | `dict["commit_message"]` **e** `dict["pr_description"]` numa só chamada |

Chamadas de IA **fora** de `core.py` (cada uma resolve provider e cache próprios): `issue_engine.py:173`/`:273`, `release_engine.py:195`/`:266`, `blame_engine.py:242`/`:448`, `fix/apply_fix.py:343`, `ui/chat_app.py:544`.

### 2.3 Cache MD5

`src/cache.py`:
- `get_cache_base_dir()` → `Path.home()/".gitpr"/"cache"/"prompts"` (`:9`), **caminho hardcoded, sem override por env**
- `generate_md5(text)` → `hashlib.md5(text.encode("utf-8")).hexdigest()` (`:15`)
- **Chave = MD5 só do `prompt_text`** (`:36-37`); como os chamadores passam `prompt + cache_scope` (`core.py:912`, `:1105`), a chave efetiva é `md5(prompt + cache_scope)`
- `get_cached_response(action_folder, prompt_text)` (`:34`) → devolve `data.get("response")`, o dict já parseado
- `save_cached_response(action_folder, action_type, prompt_text, response_dict, meta_raw=None, reviewed_diff=None)` (`:49`) — **muta o dict recebido** (`cache.py:77-78` seta `response_dict["meta_raw"]`)

### 2.4 Spinner

`src/spinner.py:150 class Spinner`, `__init__(quiet=False)` (`:153`), `start()` (`:242`), `stop()` (`:250`). É **interno à camada de IA** — os chamadores nunca o tocam. Construído e iniciado em `ai_providers.py:131-132` antes do retry loop. **Não existe flag global para desligá-lo**; o único controle é o kwarg `quiet` por chamada. `generate_pr_content` nunca passa `quiet` (`core.py:978`, `:1089`), então o spinner anima no commit/review/PR.

### 2.5 CLI — o subcomando escapa de todos os gates

`src/main.py` é um híbrido: grupo Click com `invoke_without_command=True` (`:271`) carregando ~29 flags legadas, mais **quatro** subcomandos reais (`release` `:1572`, `config` `:1823`, `fix` `:1944`, `review-pr` `:2218`).

**O gate mestre está em `main.py:548-549`:**

```python
    log_usage()                                    # :543
    if ctx.invoked_subcommand is not None:
        return
```

Tudo abaixo só roda sem subcomando. Consequência direta para `gitpr demo`:

| Item | Roda em subcomando? |
|---|---|
| Banner ASCII (`:747-748`) | ❌ |
| Gate PyPI `enforce_update_required()` (`:621-623`) | ❌ |
| `check_and_update_hooks_scripts()` (`:628-629`) | ❌ |
| `check_internet_connection()` (`:852`) — socket a 8.8.8.8:53 | ❌ |
| `setup_environment()` / prompt de API key (`:1257`) | ❌ |
| `log_usage()` (`:543`) | ✅ (uma linha em `~/.gitpr/logs/`, silenciosa) |
| Init de `src.i18n` no import | ✅ (ver 2.8) |

**`--lang` não chega no subcomando.** O handler está em `main.py:609-614`, 60 linhas depois do `return`; e a flag só está declarada no grupo raiz (`:397`), então `gitpr demo --lang pt_br` falha no parse do Click ("No such option") e `gitpr --lang pt_br demo` é silenciosamente descartado. O `release` tem a mesma lacuna.

### 2.6 Não existe detecção de primeira execução

Nenhum marcador, nenhum "bem-vindo, rode X". O mais próximo é `setup_environment()` (`config.py:393-472`), que auto-semeia defaults e então:

- `if not provider:` (`:421`) → imprime "🤖 Welcome to GitPR! Let's configure your AI engine." e pede o provider
- `if not api_key:` (`:438`) → escudo de CI/CD (`sys.exit(1)` se `CI`/`GITHUB_ACTIONS`), senão pede a chave com `hide_input=True`

### 2.7 Não existe flag offline/sem-rede

Grep por `offline`/`no_network`/`air_gapped` não encontra nada. O único switch relacionado é `GITPR_SKIP_UPDATE_CHECK` (`updater.py:22`, lido em `:46`), que silencia só o check de PyPI.

A camada de rede real é `src/net.py`: `bounded_urlopen(url, timeout=3, hard_timeout=10.0, headers=None)` (`:22`) devolve `None` em qualquer falha, e `bounded_resolve(host, timeout=10.0)` (`:49`) levanta `socket.gaierror`. Não há booleano "estou offline" reutilizável — `check_internet_connection()` (`config.py:475-496`) faz `sys.exit(1)` em vez de devolver `False`, e muta o `socket.setdefaulttimeout` global.

### 2.8 Fetch de rede no import do i18n

`src/i18n.py` é importado no start do processo. Ao final do módulo (`:128-132`):

```python
CURRENT_LANG = get_system_language()
TRANSLATIONS = get_translations(CURRENT_LANG)
```

`get_system_language()` (`:24-47`): sem `GITPR_LANG` no ambiente, detecta o locale do SO e **escreve `GITPR_LANG` em `~/.gitpr/.env`** (`:42`).

`get_translations()` (`:132`) tenta `bounded_urlopen(remote_url, timeout=3)` contra `raw.githubusercontent.com/.../langs/{code}.json` (`:76`) quando o marker `LANG_VERSION` não bate. **Numa máquina limpa em pt_BR, isso é um HTTPS com `hard_timeout` de 10s antes de qualquer código do demo rodar.**

`set_lang(lang)` (`:100-109`) faz `global CURRENT_LANG, TRANSLATIONS` e **reatribui** (nunca muta). Consequência documentada três vezes no código (`core.py:1363-1374`, `config.py:178-180`, `ui/config_app.py:160-169`): quem faz `from src.i18n import CURRENT_LANG` congela a cópia. Já `__()` (`:112-125`) lê o global no momento da chamada, então `from src.i18n import __` **é** reativo.

### 2.9 i18n — o teste é rígido

`tests/test_i18n.py` (20 testes):

- **Extração por AST**, não regex (`:51-71`), varrendo **todo** `src/` recursivamente + `run.py` (`SCAN_ROOTS`, `:26`)
- Só casa chamadas onde `node.func` é `ast.Name` com `id == "__"` → **`i18n.__("...")` é invisível**; se a chave for adicionada aos `langs/` mesmo assim, falha por órfã
- `test_key_parity_and_count` (`:125-136`): o conjunto de chaves precisa ser **idêntico** nos seis arquivos, tendo `pt_br.json` como referência, com `> 500` chaves
- `TestNoMissingKeys` (`:233-254`): toda chave `__()` do código precisa existir em **todos os seis**; e nenhuma chave dos `langs/` pode ser órfã
- `test_identity_keys_with_braces_allowlist` (`:38-48`): chave igual ao valor **e** contendo `{` só passa se estiver em allowlist — identidade sem `{` é permitida
- Arquivos: `pt_br.json`, `pt_pt.json`, `es_es.json`, `es.json`, `fr_fr.json`, `fr.json` (`:19-20`)

`scripts/validate_i18n.py` audita **apenas** `src/core.py` e `src/updater.py` (`SRC_FILES`, `:21`) — não alcança `src/demo/`. `scripts/sync_langs.py` é migração one-off, não referenciado por nada.

### 2.10 Telemetria — sem desligamento

`log_command_metric(command, status="success", provider=None, tokens_estimated=0, duration_ms=0, cache_hit=False, map_reduce_triggered=False, **kwargs)` — `src/metrics.py:72`.

Grava em `~/.gitpr/metrics/{owner}/{branch}/{uuid15}_{YYYYMMDD}.json` (`:36-41`), via daemon thread (`:30-48`), com `except Exception: pass` no corpo da thread (`:47-48`).

**Nenhum gate**: sem `GITPR_METRICS`, sem `--no-metrics`, sem parâmetro de supressão. `**kwargs` só permite *marcar*, não silenciar. `export_metrics` filtra apenas por `repo_filter` (`:283`), e o CSV tem colunas fixas sem coluna de origem — **não há como filtrar execuções de demo depois**.

Risco não-engolido: `log_local_metric` chama `get_repo_name()`/`get_current_branch()` na thread chamadora (`:62-63`) antes de iniciar a daemon; esses fazem `subprocess` para git e só capturam `subprocess.CalledProcessError` — um `git` ausente levantaria `FileNotFoundError`, que escaparia de `generate_pr_content` (nenhum dos call sites em `core.py:918/1114/1128` está envolvido em try/except).

`log_usage()` (`src/usage_log.py`), chamado incondicionalmente em `main.py:543`: gate `GITPR_SHOW_LOGS` (default **ligado**, `:37-39`), grava `~/.gitpr/logs/{uuid5}.log` com o **argv completo**, roda `git config --get-regexp` com `timeout=5` (`:100-107`), e é totalmente envolvido em try/except (`:149`, `:174-175`). Precedente de supressão: `tests/conftest.py:22`.

### 2.11 TUIs Textual

**Nenhuma subclasse de `Screen`** em todo o repositório. Todo app é single-screen com `ModalScreen` por cima; `install_screen`/`switch_screen`/`push_screen_wait` nunca são usados — só `push_screen`/`pop_screen`.

**Não existe arquivo `.tcss`/`.css`, nem `CSS_PATH`, nem tema registrado.** Todo App define `CSS = """..."""` inline, usando os tokens do Textual (`$surface`, `$accent`, `$panel`, `$error`, `$warning`, `$text-muted`).

**Não existe widget de diff** (nenhum `rich.syntax.Syntax`, nenhum `TextArea` de diff) nem **widget de findings** (o único `DataTable` é o de telemetria em `metrics_app.py:88`; o linter renderiza `Label`s soltos em `linter_app.py:28-40`).

Convenção de teclas: `escape` = sair e `f1` = ajuda em todos os apps; `f2` = Save, `f3` = Publish/Create. **Não há convenção de avançar/voltar.**

Os três wizards existentes (`--install`, `--init`, `--linter-setup`) são todos Click puro (`prompt`/`confirm`/`echo`), **nenhum Textual**. Não existe nenhum fluxo multi-etapa em Textual.

### 2.12 Reuso de apresentação — não há formatador único

| Artefato | Situação |
|---|---|
| Review | ✅ `compose_review_content(content, linter_results)` é **pura** e devolve string (`read.py:15`). `render_review_result(content, linter_results, output_filename)` (`:37`) imprime status e **escreve arquivo** |
| Linter | ✅ `generate_linter_report_content(alerts)` (`linter_engine.py:334`), usado só pelo `gitpr --linter` |
| Commit | ❌ Inline 2× (`main.py:1363-1369`, `main.py:2496-2498`) — `click.secho` + `click.echo`, **nunca vai a arquivo** |
| PR | ❌ Wrapper Markdown inline **3×** (`main.py:1416-1422`, `pr_publish_app.py:772-778`, `main.py:2638-2644`), e **duas já divergem no título** |
| Contrato do PR | ✅ `pr_data = {"commit_message", "pr_description"}` — produtor em `main.py:1449-1452`, consumidor em `pr_publish_app.py:735-736` |

`PrPublishApp.__init__(pr_data, repo_info, github_token, base_branch, output_filename, provider=None, repo_ref=None, reviewer_suggestion=None, **kwargs)` (`pr_publish_app.py:685`).

`append_coauthor_trailer(message)` (`core.py:2044`) é aplicado pelos **chamadores** (`main.py:1341`, `main.py:2490`), nunca dentro de `generate_pr_content` — um demo que pare no JSON está seguro.

### 2.13 Empacotamento

`pyproject.toml`: `[tool.setuptools.packages.find] where = ["."]`, `include = ["src", "src.*"]`. **Não há `package-data`, `include-package-data`, `data-files`, nem `MANIFEST.in`, nem `setup.py`/`setup.cfg`.**

Verificação do wheel buildado (`dist/gitpr_cli-1.2.0-py3-none-any.whl`, 67 entradas): os únicos arquivos não-`.py` são metadata de `dist-info` + LICENSE. **Nenhum arquivo de dados nunca viajou no pacote.**

`importlib.resources` não é usado em lugar nenhum. O único `os.path.dirname(__file__)` do `src/` está em `mcp_server.py:1196` e aponta para `src/../templates`, que **não está no wheel**.

**Não existe build PyInstaller** — nenhum `.spec` no working tree nem em nenhum commit do histórico; `*.spec` está no `.gitignore`; o release binário foi removido em `f108c4c` com dois planos de remoção documentados.

### 2.14 Testes e CI

~1.400 funções de teste em 70 arquivos. `tests/README.md` é o guia de estilo autoritativo.

`tests/conftest.py` completo (único conftest, sem fixtures):
```python
os.environ["GITPR_SHOW_LOGS"] = "false"
os.environ["GITPR_SKIP_UPDATE_CHECK"] = "true"
```

Estilo de fixture: constantes de módulo (`DIFF = (...)`) + patch da função que chamaria o modelo (`patch("src.core.generate_pr_content", return_value={"review": REVIEW})`), não fake de client SDK. Fakes duck-typed inline nos testes, sem base compartilhada.

**Não existe teste de contrato para providers de IA.** O padrão existe só para SCM (`tests/scm/test_contract.py`, base `ProviderContractCase` com `__test__ = False`, parametrizada por `MODULE`/`CLASS`/`KEY`).

**`tests/test_i18n.py` é o único teste que varre todo `src/`** — vai enxergar o código novo.

**CI (`.github/workflows/pr-review.yml`, 20 linhas) não roda pytest.** Só `gitpr --linter` + `gitpr --fullreview` via `action.yml`. Nenhum lint, nenhum build, nenhuma validação de i18n.

---

## 3. Decisões tomadas

### Rodada 1

| # | Questão | Decisão |
|---|---|---|
| Q1 | De onde vem o conteúdo do demo | **(b)** `FakeAIProvider` como classe com `call_ai_model` de assinatura idêntica à real, injetado em `src.core`, com contrato verificado por `inspect.signature`. Pipeline real preservado (skill, prompt, parsing, renderização) |
| Q2 | Formato das fixtures | **(a)** Módulos `.py` — não introduzir o primeiro arquivo de dados não-`.py` do wheel |
| Q3 | Quantos cenários | **(b)** Dois: `laravel-bug-fix` (nicho de autoridade) e `security-issue` (melhor demonstra o valor do review) |
| Q4 | Navegação da TUI | **(a)** `enter`/`n`/`→` avança, `p`/`←` volta, `f1` ajuda, `escape` sai. `enter` casa com o modo texto; não sequestra F2/F3 |
| Q5 | Alcance do "zero rede" | **(a)** Fetch de i18n no import aceito como pré-existente, documentado. Causa raiz (`check_internet_connection` faz `sys.exit` em vez de devolver bool) vira follow-up |
| Q6 | Idiomas do conteúdo | **(c)** Chrome **e** prosa das fixtures nas 5 línguas |
| Q7 | Spec §8 (sugestão de primeiro uso) | **(b)** Entra no escopo |
| Q8 | Granularidade da entrega | **(a)** Ordem da spec §10, entrega na árvore de trabalho, sem commits (repo proíbe) |

### Rodada 2

| # | Questão | Decisão |
|---|---|---|
| Q9 | Isolamento de efeitos colaterais | **(a)** Patch de 7 nomes em `src.core` (ver §4). `log_usage()` é o único efeito não-suprimível, aceito |
| Q10 | Fronteira de reuso | **(a)** Zero edição em produção. Reusar `compose_review_content`, `generate_linter_report_content` e o contrato `pr_data` |
| Q11 | Idioma de exibição | **`--lang` próprio no subcomando**; sem a flag, segue `CURRENT_LANG`. O diff nunca é traduzido |
| Q12 | Onde mora a prosa traduzida | **(a) + (c)** Um módulo por cenário com as 5 línguas dentro; língua ausente cai no inglês |
| Q13 | Teste de empacotamento | **(a)** Guarda unitária. O CI não roda pytest e `.py` é coletado por `packages.find` |
| Q14 | Escopo da documentação | **(a)** `docs/demo.md` ×5 + seção no README ×5. Sem variável de ambiente nova, então §12.3 fica vazia |
| Q15 | Gatilho da sugestão | **(a)** Ramo `if not provider:` (`config.py:421`) — primeira execução absoluta |
| Q16 | Estrutura da TUI | **(a)** `DemoApp` single-screen com compositores por etapa, alinhado ao que o produto realmente faz |

---

## 4. Síntese do desenho aprovado

**Premissas da spec substituídas:** `FixedFinding` descartado (o pipeline devolve prosa, não findings estruturados); cenários são `.py` e não `.json`; o fake precisa de **7 stubs** e não 1; `--lang` próprio no subcomando; validação de PyInstaller não tem sujeito.

**Stubs em `src.core` via `demo_pipeline()`:**

| Nome | Motivo |
|---|---|
| `call_ai_model` | fonte de dados trocada |
| `get_cached_response` | leitura em `core.py:912` devolveria review real de cache antigo |
| `save_cached_response` | gravação em `core.py:1102` envenenaria o cache real |
| `log_command_metric` | grava em `~/.gitpr/metrics/` sem desligamento |
| `log_local_metric` | chamada direta de map-reduce em `core.py:991` |
| `get_api_key` | sem isso o pipeline **desiste antes** de chamar a IA |
| `get_api_model` | idem |
| `get_skill_context` | determinismo — o tour não pode variar com `.skill/` local |

**DemoState** ganha `artifacts` com os três resultados gerados no início, para que "voltar" nunca regenere nem perca estado.

**Risco principal:** ~60 blocos de prosa escritos à mão (2 cenários × 5 línguas × ~6 blocos), mais o chrome. É a maior parte do trabalho — mais que todo o código. O fallback inglês (Q12c) faz entrega parcial degradar em vez de quebrar.

**Registrado como follow-up (fora desta entrega):** correção da causa raiz do fetch de i18n no import; extração de um `compose_pr_markdown()` compartilhado para eliminar as 3 cópias divergentes do wrapper de PR; sugestão de `gitpr demo` também no ramo `if not api_key:`.
