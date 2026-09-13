# Survey — `gitpr config` (TUI Master-Detail de Configuração)

- **Data:** 2026-09-12
- **Task:** `gitpr_config_tui`
- **Skill de origem:** `grill-with-docs` (6 rodadas de perguntas, 22 decisões)
- **Objeto:** feature nova — superfície de configuração para `~/.gitpr/.env`
- **Estado:** planejado, não implementado

## Contexto da tarefa

Pedido original do usuário (verbatim):

> Cria uma funcionalidade para a nova flag `--config`
> Esta flag exibe uma tela TUI (estilo Master-Detail) onde um menu lateral esquerdo e ao lado direito a area main com a lista de configurações existentes
> - No menu a primeira opção e Geral
> - Da segunda opção do menu em seguida as opções de cada flag que gera uma variavel no `~/.gitpr/.env`
>
> Exemplo:
> Geral -> Configurações de idioma, preferencias etc..
> Pull Request -> Configurações especificas do comportamento padrão do gitpr exemplo: `GITPR_SKIP_UNSTAGED_CHECK`, `GITPR_AUTO_STAGE`, `OUTPUT_FILE_NAME`, etc..
>
> Assim todas as opções do .env tem um interface facil de usar para o Usuário

**Problema que a feature resolve:** o GitPR expõe ~50 variáveis em `~/.gitpr/.env` sem nenhuma interface. Não existe `--config` nem `gitpr config`. Para mudar `GITPR_AUTO_STAGE` o usuário precisa saber o nome exato da variável, abrir o arquivo à mão, e adivinhar se o valor é `true`, `1` ou `yes`. Pior: os getters têm fallbacks **silenciosos** — `_positive_float()` engole lixo e volta ao default sem avisar, então um `GITPR_AI_TIMEOUT=abc` nunca se manifesta como erro.

**Divergências aprovadas do pedido original:**

1. Virou **subcomando** `gitpr config`, não flag `--config` (decisão 8) — mais idiomático para Click e não disputa espaço no callback monolítico de `src/main.py`.
2. `GITPR_SCM_TOKEN` cru ficou **fora** da TUI (decisão 17) — vence o token criptografado e grava em texto plano.
3. O menu **não** é literalmente "Geral + uma por flag": foram adicionadas as categorias `Filtros de Diff` (decisão Q3/R6) e `Avançado`, além de uma categoria condicional `Desconhecidas`.

## Decisões das rodadas

### Rodada 1 — fundação

| # | Decisão | Escolha |
|---|---------|---------|
| 1 | Persistência no `.env` | **Save explícito (`F2`)** com buffer e dirty-state; `Esc` com alterações pendentes pede confirmação. Consistente com o `IssueApp`, que já usa `F2 = salvar` |
| 2 | Segredos (`*_ENCRYPTED`) | **Editáveis mascarados**; nunca exibem o valor em claro — placeholder `•••••••• (definido)`, só sobrescreve se digitar algo novo |
| 3 | Fonte da verdade | **Schema declarativo único** (não widgets hardcoded por categoria) |
| 4 | Layout | **Campos inline**: `Switch` p/ bool, `Input` p/ texto/número, `Select` p/ enum. Sem modal |

### Rodada 2 — taxonomia e escopo

| # | Decisão | Escolha |
|---|---------|---------|
| 5 | Agrupamento do menu | **Uma categoria por comando/flag** (~11) |
| 6 | Catálogo de chaves | **Tudo**, com marcadores de versão e chaves internas atrás do toggle "Mostrar avançadas". `GITPR_SHOW_LOGS` fica de fora (chave morta — vira bug separado) |
| 7 | `GITPR_LANG` na TUI | **Aplica + avisa reinício** — grava, chama `set_lang()`, e informa que o efeito completo exige reiniciar |
| 8 | Invocação | **Só subcomando** `gitpr config` |

### Rodada 3 — arquitetura

| # | Decisão | Escolha |
|---|---------|---------|
| 9 | Onde mora o schema | **Módulo novo `src/config_schema.py`** (dado puro). `src/config.py` ganha só funções novas; os 9 call-sites de escrita existentes ficam intactos |
| 10 | Restaurar padrão | **`Ctrl+R`** no campo focado remove a linha do `.env` (só por campo na v1) |
| 11 | Validar segredo ao salvar | **Sim, antes de persistir** (contra a recomendação do grill, que sugeria adiar) |
| 12 | Banner de abertura | **Não mexer** |

### Rodada 4 — o que a validação implica

| # | Decisão | Escolha |
|---|---------|---------|
| 13 | Quando valida | **Só os segredos que mudaram** nesta sessão |
| 14 | Falha de validação | **Bloqueia só em `401`**; erro de rede (`http_status == 0`) permite gravar |
| 15 | Tipo inválido | **Bloqueia o `F2`** com erro inline no campo |
| 16 | Env var do processo sobrescreve o `.env` | **Mostra os dois**: valor do arquivo (editável) + marcador `⚠ ambiente` |

### Rodada 5 — casos de borda

| # | Decisão | Escolha |
|---|---------|---------|
| 17 | `GITPR_SCM_TOKEN` cru | **Fora da TUI** — é caminho de credencial de CI, não preferência |
| 18 | Chaves fora do schema | **Categoria `Desconhecidas`**, criada só quando existirem, em modo leitura |
| 19 | Busca | **Global com `/`**, casando chave ou label em todas as categorias |
| 20 | Templates `OUTPUT_FILE_NAME*` | **Bloqueia placeholder desconhecido** (evita `KeyError`) **e exige `{datetime}`** (evita sobrescrita silenciosa) |

### Rodada 6 — fechamento

| # | Decisão | Escolha |
|---|---------|---------|
| 21 | Validação de API key de IA | **Função nova `validate_ai_key()` em `config.py`**, no molde de `validate_github_token()` |
| 22 | O que conta como pronto | **Completo**: código + testes + docs (5 idiomas) + i18n + glossário |

## Fatos levantados (relatório)

Levantados por 4 sub-agentes de exploração sobre o código real. **Não são suposições.**

### Sistema de configuração

1. **`DEFAULT_CONFIG` tem 39 chaves** (`src/config.py:16-63`) e é a **única enumeração** de configuração que existe no projeto. É iterado exatamente uma vez, em `setup_environment()` (`config.py:264-267`).
2. **~18 chaves são lidas e nunca semeadas**: `GITPR_COAUTHOR`, `<PROVIDER>_API_KEY`, `GEMINI_API_KEY_ENCRYPTED`, `DEEPSEEK_API_KEY_ENCRYPTED`, `GITHUB_TOKEN_ENCRYPTED`, `GITPR_LANG`, `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`, `SCRIPTS_LANG`, `SPINNER_THINKING_WORDS` e os 5 marcadores de versão.
3. **40 call-sites de `os.getenv("LITERAL")`** espalhados por 9 módulos. Não há dataclass, `BaseSettings` nem `__all__` para config.
4. **Não existe `save_config()` genérico.** A escrita está em 9 lugares; `setup_environment()` é o único escritor em massa. O único `open(ENV_FILE, "w")` cru do projeto é `_remove_expired_token()` (`src/tui_issue.py:16-31`).
5. **Precedência de segredos:** `<PROVIDER>_API_KEY` cru vence o `*_ENCRYPTED` (`config.py:211-213`); `GITPR_SCM_TOKEN` cru vence `GITPR_SCM_TOKEN_ENCRYPTED` (`config.py:480-486`, via `if raw_token:` — logo o `""` semeado é inofensivo). `get_github_token()` **não** tem fallback cru.
6. **`decrypt_data()` engole toda exceção** e devolve `""` (`src/security.py:43-45`) — cifra corrompida ou chave rotacionada são indistinguíveis de "não configurado".
7. **`load_dotenv(ENV_FILE)` roda com `override=False`** em ~15 pontos. **Variável de ambiente do processo vence o `.env`** — é o que faz o padrão CI/CD funcionar. Consequência: o valor exibido na tela **não pode** sair de `os.getenv()`.

### python-dotenv 1.2.3 (verificado no pacote instalado)

8. **`set_key()` é atômico**: temp file criado no **mesmo diretório** + `os.replace`. Preserva modo POSIX do arquivo original. Em falha, faz `unlink` do temp e a origem fica intacta.
9. **`set_key()` preserva comentários e ordem**: streama as linhas originais (`mapping.original.string`) e substitui só a linha da chave casada. Chave nova é **anexada no fim**.
10. **`set_key()` cria o arquivo se não existir** (trata `FileNotFoundError` com `io.StringIO("")`), mas **levanta `FileNotFoundError` se o diretório pai não existir** — não há `os.makedirs` dentro dele. `src/config.py:247` já cobre isso.
11. **`unset_key()` existe** e **apaga a linha inteira** (não esvazia o valor), preservando comentários e ordem. Retorna `(None, key)` — sem exceção — para "arquivo ausente" e "chave ausente". **Logo `remove_config_value()` é um wrapper fino**, sem precisar do hack de reescrita crua do `tui_issue.py`.

### Validação de credencial

12. **`call_ai_model()` é inutilizável para validar key**: engole toda exceção num `except Exception` (`src/ai_providers.py:218`) e retorna `None` depois de **3 tentativas com sleep de 2s**. Um `401` viraria ~6s de espera reportados como falha genérica, indistinguível de rede caída.
13. **Não existe nenhum `list_models`/`test_connection`/`ping` em `ai_providers.py`** — só `call_ai_model` (linha 101) e `call_ai_chat` (linha 311), ambos gerando conteúdo real.
14. **O precedente correto é `validate_github_token()`** (`src/config.py:545`): `GET https://api.github.com/user` com timeout de 10s, retorna `(is_valid, error_message)` e separa explicitamente `401` de `ConnectionError`/`Timeout`.
15. **`ScmProviderError` carrega `http_status`** (`src/infrastructure/scm/base.py:95-108`) — código real para 4xx/5xx, **`0` para falha de rede**. É o discriminador que a regra da decisão 14 usa. `test_connection()` existe nos 4 providers.
16. **`ollama` não tem chave**: `config.py:219-220` devolve o literal `"ollama-local"` — fica fora da validação.

### TUI (Textual 8.2.8)

17. **Nenhum layout master-detail existe no repo.** Os 5 apps (`IssueApp`, `ChatApp`, `MetricsApp`, `LinterApp`, `PrPublishApp`) são todos `Header → Vertical → Footer`. O único uso de `dock` é no `chat_app`.
18. **Widgets nunca usados nesta base**: `Switch`, `Select`, `OptionList`, `Tree`, `TabbedContent`, `ContentSwitcher`, `Collapsible`, `RadioSet`. O idioma de seleção estabelecido é `SelectionList` (`pr_publish_app.py:244`).
19. **APIs confirmadas presentes no 8.2.8**: `Switch`, `Select` (`allow_blank=True` por padrão), `Input`, `ListView`, `ContentSwitcher`, `Collapsible`.
20. **`ctrl+r` está livre** nos 5 apps e nos widgets nativos. Ocupados: `f1`/`f2`/`f3`, `f5`-`f8`, `ctrl+s`/`ctrl+e` (chat), `ctrl+p` (paleta — exceto no `LinterApp`, que esquece de desabilitá-la). `Input`/`TextArea` capturam `backspace`, `delete`, `ctrl+d`, `ctrl+w`, `ctrl+k`, `ctrl+u`.
21. **Convenções obrigatórias**: `ENABLE_COMMAND_PALETTE = False`, `CSS` inline (nunca `CSS_PATH`), `Header(show_clock=True)` … `Footer()`, todo texto via `__()`, import lazy dentro do branch do Click, `app.run()` na main thread, resultado em `final_action`/`final_message`.
22. **O Textual substitui `sys.stdout` por um `_PrintCapture` sem fd válido** — qualquer `click.secho`/`echo` de dentro do app quebra o layout. `pr_publish_app.py:72-142` resolve com `_with_suppressed_stdout()` + `_clear_click_cache()` (invalida o `lru_cache` de `_default_text_stdout`).

### CLI e i18n

23. **A raiz é um `@click.group(invoke_without_command=True)`** (`main.py:269`) com o gate `if ctx.invoked_subcommand is not None: return` (`main.py:541-542`) rodando **antes** do bloco de `help_flag` (`main.py:547`). Consequência: **`gitpr -h config` abre a TUI ignorando o `-h`**; `gitpr config -h` funciona. Não será corrigido (mudaria o comportamento de `-h` para todos os subcomandos).
24. **Nenhuma colisão com `--config`**: `grep` retorna zero ocorrências. O `-c` pertence a `--commit`. Click 8.3.3 faz match exato de opção longa, sem prefix-abbreviation.
25. **`HELP_MAP`/`HELP_PRIORITY`** (`main.py:76-263`) são keyed por *flag strings* e resolvidos via `locals().get(...)` no callback do grupo — **subcomandos não passam por lá**. `--init` já não tem entrada. O `release` usa `epilog` + `get_doc_url()` no próprio `@cli.command(...)`.
26. **O banner está desatualizado** (`main.py:64-70`): não lista `--dashboard`, `--init`, `--base` nem `--plugins`. É uma string i18n única, traduzida nos 6 JSONs.
27. **`tests/test_i18n.py` é um gate rígido**: exige paridade de chaves entre os 6 arquivos (742 chaves em pt_br), zero chaves faltantes para todo `__()` literal em `src/`, e zero órfãs. **Baseline verificado verde no HEAD (20 passed).**
28. **`tests/sync_i18n.py` é DESTRUTIVO e não deve ser executado** — o scanner por regex trunca chaves com concatenação implícita (`__("a " "b")`) que o AST de `test_i18n.py` dobra corretamente. Chaves novas devem ser adicionadas por **edição JSON direta** (`indent=2`, `ensure_ascii=False`). *(Este fato corrige o passo 10 do plano, que previa rodar o script.)*
29. **Os labels do schema precisam ser chamadas literais `__("...")`** para o scanner de `test_i18n.py` encontrá-las. Labels montados dinamicamente viram chaves órfãs e quebram a suíte.
30. **`src/core.py:32` faz `from src.i18n import __, CURRENT_LANG`** — binding congelado no import. `set_lang()` só rebinda dentro do módulo `i18n`. É a razão da decisão 7 (avisar reinício).

### Pré-existências (fora de escopo, registradas)

31. **`GITPR_SHOW_LOGS` é uma chave morta**: declarada (`config.py:34`), semeada em todo `.env`, prometida no `CHANGELOG.md:174` e documentada em `docs/pull-request-publication.md:414` — e **lida em lugar nenhum**. O toggle real de logs na TUI é `PR_PUBLISH_LOG`, que controla escrita de arquivo, não exibição.
32. **`get_ai_timeout()` tem docstring mentindo**: diz "default 600" (`config.py:134`), o fallback real é `180.0` (`config.py:66`).
33. **`LinterApp` não desabilita a command palette** — os outros 4 apps setam `ENABLE_COMMAND_PALETTE = False`. `ctrl+p` fica preso à toa.
34. **`CLAUDE.md:294` lista `PR_AUTO_PUBLISH`**, que não existe em nenhum arquivo do `src/`. A documentação de env vars também está fragmentada em 6 documentos, sem tabela canônica.

## Artefato produzido

- Plano de implementação aprovado: `C:\Users\nataniel\.claude\plans\cria-uma-funcionalidade-para-clever-pelican.md`

## Entregáveis previstos

| Arquivo | Tipo |
|---|---|
| `src/config_schema.py` | novo — `ConfigField`, `CATEGORIES`, `FIELDS` |
| `src/ui/config_app.py` | novo — `ConfigApp` + modais |
| `src/config.py` | alterado — `read_env_file_values()`, `save_config_values()`, `remove_config_value()`, `validate_ai_key()` |
| `src/main.py` | alterado — subcomando `config` |
| `src/updater.py` | alterado — bump de `__lang_version__` |
| `langs/*.json` (6) | alterado — edição JSON direta, **não** via `sync_i18n.py` |
| `docs/config-tui.md` + 4 traduções | novo |
| `docs/plans/glossary-config-tui.md` | novo |
| `tests/test_config_{schema,store,validation,app,cli}.py` | novo |
