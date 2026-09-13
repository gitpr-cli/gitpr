# Completion Report — Tela `gitpr config`: 11 itens — seções filtradas, sub-cabeçalhos, botões de download e link de documentação

## What was done

Onze itens relatados depois de usar a tela de verdade. Nenhum era bug de lógica: a tela mostrava a configuração num arranjo que não corresponde ao modelo mental de quem usa — variável na seção errada, seções misturando forges e providers, campo de versão em branco, lista ilegível, campo que deveria ser escolhível e não era, falta de botões para forçar download, ordem dos campos e falta de link para a documentação técnica.

**Esta entrega cobre os itens 1–9 e 11.** O item 10 (seção **Smart Exclude**) é a Entrega 2, ainda não iniciada — o esboço está na §"Next steps".

O que a tela ganhou, em uma frase: **quatro atributos novos no schema** (`group`, `show_if`, `version_source`, `action`) transformaram "esconder/mostrar/ordenar/oferecer um botão" em **dado**, não em código de interface.

### Item 1 — `GITPR_SCM_TOKEN` sai de *Desconhecido* e vai para **SCM / Forge**

Medido antes de mover: `config.get_scm_token()` ([config.py:474-484](src/config.py#L474-L484)) lê essa chave para **toda** forge, então ela não pertence a nenhum sub-grupo de forge — vai **solta, sempre visível**, depois de `GITPR_SCM_PROVIDER`.

É `KIND_SECRET` (**nunca `KIND_STR`**, que renderiza o token cru em texto claro — exatamente o que motivou escondê-lo) e `read_only=True`, com a descrição apontando `gitpr --init` como o único caminho que deve escrevê-lo. Como `read_only` já era respeitado pelo save (`_build_plan` pula) e pelo Ctrl+R, nada mais precisou mudar.

### Item 2 — **SCM / Forge** separado por forge

`show_if` na prática: `GITHUB_TOKEN_ENCRYPTED` aparece com `GITPR_SCM_PROVIDER` vazio ou `github` (vazio = GitHub, que é o default do `resolve_scm_provider`); `GITPR_SCM_USERNAME` sob `[Bitbucket]`; `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT` sob `[Azure DevOps]`. Os campos comuns (provider, token CI/CD, token cifrado, base URL) ficam fora dos sub-grupos, sempre visíveis.

### Item 3 — **AI Providers** separado por provider, filtrado pela seleção

`GEMINI_*`, `DEEPSEEK_*` e `OLLAMA_*` ganharam `show_if=("DEFAULT_AI_PROVIDER", (…))`; com nenhum provider selecionado, **nenhum** bloco de provider aparece. Trocar o `Select` re-filtra o painel **na hora**, sem F2: só `on_select_changed` dispara `_render_view()`, e só quando a chave está em `VISIBILITY_CONTROLLERS` (derivado do schema, não uma lista à mão).

Duas decisões embutidas, ambas testadas:

- **A busca ignora o filtro.** Procurar `deepseek` com o Gemini selecionado **acha** os campos, para permitir pré-preenchê-los. Campo sujo é salvo independente de visibilidade — `_build_plan` é cego a visibilidade e **não deve** ser "otimizado" para iterar só os visíveis.
- **`DEFAULT_AI_PROVIDER` ganhou a opção vazia** (`(not configured)`), o que exigiu a correção de uma linha em [config_app.py:236](src/ui/config_app.py#L236): `_AUTOMATIC_LABEL` era incondicional para `""` e `choice_labels` nunca conseguia sobrescrevê-lo. Sem essa opção, o filtro do item 3 tornaria alcançável de propósito um valor que o `Select` não aceitava — `Select(value="", allow_blank=False)` levanta `InvalidSelectValueError` **no mount** e derruba a tela inteira. Há teste de regressão com `.env` contendo `DEFAULT_AI_PROVIDER=`.

### Item 4 — **Linter Presets Version** com valor automático

`LINTER_PRESETS_VERSION` só é gravado por `load_linter_presets()` ([linter_wizard.py:80](src/linter_wizard.py#L80)), alcançável apenas por `gitpr --linter-setup`: a caixa vazia era verdadeira e inútil. Agora um `KIND_VERSION` **sem marcador no arquivo** mostra a constante de `version_source` e ganha a anotação `code version — not set in the file`, com `is_set=False` e `pending` intocado (nada disso é gravável).

Medido no `.env` real, antes → depois: `LINTER_PRESETS_VERSION` **ABSENT** → `v0.0.24`, e a anotação `'read only   code version — not set in the file'` → `'read only'`.

### Item 5 — **Spinner Words** como lista + botão de download

`KIND_WORDS` renderiza um `VerticalScroll` (id `words_<KEY>`) com **um** `Static` dentro, entradas separadas por `·`, `max-height: 12` com borda: rola dentro de si mesmo. Um `ListView` com 263 itens exigiria `clear()` assíncrono — exatamente o entrelaçamento que o docstring de `_mount_rows` proíbe — e 263 `Static`s quase dobrariam a árvore de widgets; um `Static.update()` é síncrono e atômico.

A lista vem do **arquivo** (`self.raw_value`), coerente com a regra da tela ("o valor exibido vem do ARQUIVO, nunca de `os.getenv()`") e **sem rede ao abrir**: o separador é reimplementado localmente (`_split_words`), porque importar `src.spinner` baixaria a lista no import ([spinner.py:137](src/spinner.py#L137)). Verificado com o `.env` real: 263 entradas, começando em `Fabuloso · Pensando · Analisando · Raciocinando · Elaborando`.

### Item 6 — **Hooks Language** escolhível (e o defeito que estava por baixo)

Aqui o item virou correção de defeito. `_SCRIPT_LANG_SUFFIXES = {"pt_br","pt_pt","fr","es"}` ([core.py:90](src/core.py#L90)) era comparado contra `CURRENT_LANG`, que produz `es_es`/`fr_fr` — **nunca casava**. Um usuário `fr_fr` recebia hooks em inglês para sempre, silenciosamente, mesmo com `scripts/*.fr.sh` publicados.

- `HOOK_SCRIPT_SUFFIXES = {"pt_br": "pt_br", "pt_pt": "pt_pt", "es_es": "es", "fr_fr": "fr"}` — a chave é o código do `GITPR_LANG`, o valor é o sufixo publicado. O mapa é explícito porque os dois lados escrevem o mesmo idioma de formas diferentes.
- **Uma chave não pode ser ao mesmo tempo "o que eu quero" e "o que está instalado".** `SCRIPTS_LANG` passou a ser **a escolha** (editável, `""` = segue o idioma da interface) e nasceu `SCRIPTS_INSTALLED_LANG` com **o registro do que está em disco** (read-only, visível). O instalador **nunca** escreve a escolha — escrevê-la tornaria a comparação do auto-sync uma tautologia, e a troca de idioma nunca seria detectada. Sem a chave nova, `unknown_keys = set(file_values) - KNOWN_KEYS` jogaria `SCRIPTS_INSTALLED_LANG` direto na seção **Desconhecido** — o defeito do item 1 de novo.
- `effective_hook_lang()` = `SCRIPTS_LANG` (lido do **arquivo**) ou o idioma da interface; `install_git_hooks()` instala no idioma efetivo e grava `SCRIPTS_VERSION` + `SCRIPTS_INSTALLED_LANG`; `check_and_update_hooks_scripts()` compara **instalado** contra **desejado**.

Verificado ponta a ponta, num repo de rascunho: `SCRIPTS_LANG=fr_fr` → header `# Hook Linter GitPR - Validation pré-commit` e `SCRIPTS_INSTALLED_LANG=fr_fr`; trocar para `es_es` reinstala **uma vez** (`# Hook Linter de GitPR - Validación pre-commit`) e depois **estabiliza** (arquivo de hook byte a byte idêntico); vazio segue `GITPR_LANG`; inglês instala o script base.

### Itens 7 e 8 — botões de forçar download

`LANG_VERSION` (**Translation Pack Version**), `SMART_EXCLUDES_VERSION` (**Filters List Version**), `LINTER_PRESETS_VERSION` e `THINKING_WORDS_VERSION` — os quatro com **📥 Force download**, mais **📥 Download the word list** ao lado da lista de palavras: **cinco botões**. Cada um chama o loader com `force=True`, que só curto-circuita o gate de versão; todos aditivos, nenhum call site existente mudou (`i18n.get_translations`, `core._load_smart_excludes`, `linter_wizard.load_linter_presets`, `spinner._load_thinking_words`/`reload_thinking_words`).

Detalhes que a tela exigiu, todos por medição, não por suposição:

- **Worker sem `exclusive=True`** — os botões compartilham `_download_marker`, e um worker exclusivo cancela o anterior do mesmo método: clicar num segundo botão mataria o download em curso.
- **Import preguiçoso dentro da worker** — `src.spinner` baixa a lista **no import** e `src.core` puxa `google.genai`; nenhum dos dois pode entrar no escopo de módulo de `config_app.py`.
- **`_quiet_output()` local** (redirect de `sys.stdout` + `cache_clear()` do Click), **duplicado de propósito** em vez de importado: importar `src.ui.pr_publish_app` arrastaria `src.core` para o grafo da tela.
- **O veredito vem de reler o ARQUIVO**, nunca de `os.getenv()`: todo `load_dotenv()` do projeto roda com `override=False`, então o processo ainda guarda o valor de antes do download e reportaria como atual um marcador que já era velho.
- Botão desabilitado durante a execução (segundo clique impossível, não apenas ignorado); frase inteira no `self.notify(...)`, com um `Static` curto (`✔ v0.0.24` / `✖ not updated` / `Downloading…`) na linha.

Evidência no `.env` real: os cinco botões terminam em `✔ v0.0.24`, reabilitados, e `SPINNER_THINKING_WORDS` com 263 palavras.

### Item 9 — ordem dos campos em **Advanced**

Três sub-cabeçalhos por tema: `[Spinner]` `SPINNER_THINKING_WORDS` → `THINKING_WORDS_VERSION` (o marcador **imediatamente depois** da lista, que era o pedido), `[Git Hooks]` `SCRIPTS_LANG` → `SCRIPTS_INSTALLED_LANG` → `SCRIPTS_VERSION`, `[Downloads]` os três marcadores restantes. O `_mount_rows()` continua montando cada linha **uma vez** (nada de reconstruir); o `Static(id="grp_<id>")` entra imediatamente antes do primeiro campo do grupo e o `_render_view()` só alterna `display`. Um id de grupo pertence a **uma** categoria só — travado por teste.

Cabeçalho de grupo só aparece em **vista de categoria**, e só se sobrou algum campo dele no filtro: na busca os resultados são uma lista plana em ordem de `FIELDS`, então um cabeçalho rotularia só o primeiro pedaço do grupo.

### Item 11 — link para a documentação técnica em cada seção

**📚 Documentation** no topo do painel direito, com a URL impressa ao lado (para ler ou copiar antes, como o CLI já faz). `Button` + `webbrowser.open` preguiçoso, não `[link=…]`: o parser de markup do Textual **não é o do Rich** e levanta `MarkupError`. Onze categorias, cada uma com seu documento, seguindo o idioma da interface (`?lang=pt_br`); a linha **some** na busca e em **Unknown**, que é uma categoria sintetizada e não tem documento.

`src/doc_links.py` (novo) guarda a URL base e a regra do `?lang=`; `core.get_doc_url()` passou a **delegar**, sem mudar nenhum dos 11 call sites. Fica separado de `core.py` de propósito: `config_app.py` não pode importar `src.core`, que puxa os SDKs de IA a cada abertura da tela.

### Achado fora do plano: `--lang` não chegava à instalação dos hooks

Durante a verificação do item 6, `gitpr --lang fr_fr` instalou hooks em **inglês**. Causa: `core.py` guarda uma cópia congelada de `CURRENT_LANG` (`from src.i18n import CURRENT_LANG`) e `i18n.set_lang()` — que é o que `--lang` chama — **rebinda** o atributo do módulo em vez de mutá-lo, então a cópia nunca vê a troca.

Corrigido com `_interface_lang()`, que lê `CURRENT_LANG` **no momento da chamada** ([core.py](src/core.py)), com o docstring explicando por quê; os dois patches de `tests/test_core.py` passaram de `src.core.CURRENT_LANG` para `src.i18n.CURRENT_LANG` e um teste de regressão trava o comportamento.

### i18n

Os seis arquivos estão em **944 chaves cada** (eram 931). Nesta rodada: 14 chaves que o scanner AST acusou como faltantes (13 líquidas, depois de remover a órfã `   Detected language: {lang}`) e a tradução das strings da tela que ainda estavam em inglês nos cinco arquivos não-ingleses.

Das 203 chaves que a tela introduziu, **9 permanecem em inglês** de propósito, e são as mesmas nos seis arquivos: `Blame`, `Git Hooks`, `Issue`, `Linter`, `Pull Request`, `Release`, `SCM / Forge`, `Spinner` (nomes de produto, precedente de `_DISPLAY_NAMES` em [factory.py:82-85](src/infrastructure/scm/factory.py#L82-L85)) e `✔ {version}` (um sinal de conferido mais a versão literal — não há prosa para traduzir; allowlist documentada em `test_identity_keys_with_braces_allowlist`).

A inserção foi **cirúrgica**, por round-trip de `json.dumps` (`indent=2`, CRLF, `ensure_ascii=False`), depois de **provar** que o round-trip é byte a byte idêntico nos seis arquivos — o `sync_i18n.py` é destrutivo e não foi rodado. `tests/test_i18n.py` (paridade, chaves faltantes, órfãs) passa.

### Documentação

- `docs/config-tui.md` + os 4 espelhos: §1.1 reescrita com os sub-grupos, **novas §1.2 Controls** (linha da lista de palavras), **§1.3 Filtered by the Selected Value**, **§1.4 Download Buttons** (tabela de feedback), **§1.5 Documentation Link** (tabela das 11 categorias), §1.6 (o toggle), §5 (`GITPR_SCM_TOKEN`) e §6 (55 campos, `src/doc_links.py`, os atributos do `ConfigField`).
- `docs/hooks-versioning.md` + os 4 espelhos: §2.1 quatro marcadores, §2.2 fluxo + a leitura viva, §2.3 o mapa código↔sufixo, §3.1/§3.2, §5.1–5.3, §6, §7 (três docstrings) e §8 (cinco decisões de desenho).
- `docs/ARCHITECTURE*.md` ×5 e `README*.md` ×5: a linha que citava `SCRIPTS_LANG` como marcador do que está instalado.

Os quatro espelhos foram conferidos por comparação de **forma** linha a linha (linha em branco / fence / aridade de tabela / nível de título / lista / texto) contra o original inglês: **0 divergências** em `config-tui` (216/216) e em `hooks-versioning` (250/250), nos 4 idiomas. As strings de UI citadas nos textos foram conferidas contra `langs/*.json` — são os valores reais, não traduções soltas.

## Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/doc_links.py` | feat (novo) | `DOCS_BASE_URL` + `doc_url(filename)`, com `?lang=` só fora do inglês. Separado de `core.py` para não arrastar os SDKs de IA |
| `src/config_schema.py` | feat | `ConfigField.group/show_if/version_source/action/choice_labels`, `Group`/`GROUPS`, `Category.doc`, `KIND_WORDS`, `ACTION_*`, `VERSION_*`; nova ordem de Advanced, `show_if` por provider e por forge, linha do `GITPR_SCM_TOKEN`, par `SCRIPTS_LANG`/`SCRIPTS_INSTALLED_LANG` |
| `src/ui/config_app.py` | feat | Filtro de visibilidade + sub-cabeçalhos, fallback de versão, workers de download e a linha de status, linha `KIND_WORDS`, botão de documentação, `_focused_field` reconhecendo `row_`, `_reveal` pela busca quando o campo está filtrado, `_quiet_output()` |
| `src/core.py` | fix/feat | `HOOK_SCRIPT_SUFFIXES` (corrige `es_es`/`fr_fr`), `effective_hook_lang()`, `_interface_lang()` (cópia congelada de `CURRENT_LANG`), `install_git_hooks()` no idioma efetivo + `SCRIPTS_INSTALLED_LANG`, `check_and_update_hooks_scripts()` comparando instalado × desejado, `_load_smart_excludes(force=)` |
| `src/i18n.py` | feat | `get_translations(..., force=)` |
| `src/spinner.py` | feat | `_load_thinking_words(force=)`; `reload_thinking_words()` passa a devolver a lista |
| `src/linter_wizard.py` | feat | `load_linter_presets(force=)` |
| `langs/{pt_br,pt_pt,es_es,es,fr_fr,fr}.json` | feat | 944 chaves em cada; 14 inseridas, 1 órfã removida, strings da tela traduzidas |
| `tests/test_config_schema.py` | test | Regras novas: grupo existe e é único, campos contíguos, `show_if` aponta para enum com valores válidos, `KIND_VERSION ⇔ version_source`, `KIND_WORDS ⇒ read_only + ação`, toda ação tem handler, `Category.doc` termina em `.md`; `DELIBERATELY_HIDDEN` agora vazio por desenho |
| `tests/test_config_app.py` | test | 62 testes: filtro por provider/forge, cabeçalhos, fallback de versão, lista de palavras, os cinco botões (sucesso, falha, desabilitado), link de doc, Ctrl+R com o botão focado, e a rolagem do painel sobre as linhas novas |
| `tests/test_linter_presets.py` | test (novo) | 5 testes de `load_linter_presets`, incluindo `force=True` e a cópia velha preservada na falha |
| `tests/test_core.py` | test | Classe do idioma dos hooks (`fr_fr`→`.fr`, `es_es`→`.es`, escolha vencendo a interface, reinstalação só quando instalado ≠ pedido) + regressão do `--lang` |
| `tests/test_smart_excludes.py`, `tests/test_thinking_words.py` | test | Casos `force=True`: baixa mesmo com o marcador igual; mantém a cópia anterior quando a rede falha |
| `tests/test_i18n.py` | test | `✔ {version}` entra na allowlist documentada de chaves identidade com chaves de formatação |
| `docs/config-tui.md` + `.{pt_br,pt_pt,es_es,fr_fr}.md` | docs | §1.1–1.6, §5, §6 (arquivos novos da tela) |
| `docs/hooks-versioning.md` + 4 espelhos | docs | §2.1–2.3, §3.1/3.2, §5–§8 |
| `docs/ARCHITECTURE.{md,pt_br,pt_pt,es_es,fr_fr}.md`, `README.{md,pt_br,pt_pt,es_es,fr_fr}.md` | docs | Uma/duas linhas cada, com o par de marcadores de idioma |

Arquivos temporários de verificação, **removidos** ao fim: `tests/_probe_downloads_real.py`, `tests/_probe_hooks_e2e.py`, `tests/_apply_i18n_etapa10.py`, `.env_probe_tmp`.

## Impact

- **Funcionalidade:** a tela passa a mostrar a configuração no lugar onde o recurso está. Ver a seção do provider selecionado, a do forge configurado, o marcador de versão com valor mesmo antes do primeiro download, a lista de palavras legível, e poder forçar o download sem apagar linha do `.env`. **Defeito real corrigido:** hooks em espanhol e francês nunca eram instalados, em nenhuma circunstância, e `--lang` não afetava a instalação dos hooks — os dois silenciosos.
- **Performance:** nenhuma regressão. O filtro e os cabeçalhos só alternam `display` (as linhas continuam sendo montadas uma vez), a lista de palavras é um único `Static`, e os imports pesados continuam fora do escopo de módulo da tela — abrir `gitpr config` não baixa a lista de palavras nem carrega os SDKs de IA. Os downloads só rodam quando um botão é apertado.
- **Compatibilidade:** nenhuma migração. Nenhum call site dos loaders mudou (`force` é parâmetro novo com default `False`); `core.get_doc_url()` mantém assinatura e URL; os arquivos de idioma continuam com as mesmas chaves nos seis arquivos. `SCRIPTS_LANG` **muda de significado** (era o registro do instalador, agora é a escolha do usuário) — para quem nunca escolheu, o valor em disco é `""` e o comportamento segue o de antes, com uma única reinstalação dos hooks na próxima execução de `gitpr` num repo com `.git/hooks`.

### Desvios do plano, deliberados

1. **A frase de sucesso é `"{name} is up to date ({version})."`, não `"{name} updated to {version}."`.** Um download que falha e cai na cópia já atual é **indistinguível** de um download bem-sucedido no único lugar onde a tela pode olhar (o marcador do arquivo). O texto honesto é o que descreve o que a tela sabe: o arquivo carrega a versão corrente. A alternativa seria inventar uma distinção que o código não tem. Conferido com URL inválida e marcador corrente: `✔ v0.0.24` + "is up to date"; e com o marcador propositalmente velho: `✖ not updated` + "Could not download Filters List Version. The previous copy stays in use." (`severity=error`), cópia anterior intacta e o marcador restaurado.
2. **`load_dotenv(ENV_FILE, override=True)` **não** é chamado depois do download.** O plano o previa, mas ele dessincronizaria as anotações de "⚠ in environment" para nenhum ganho: a tela lê o **arquivo** por definição (§2 da doc), e é justamente essa leitura que produz o veredito.
3. **Correção extra:** o `_interface_lang()` do `core.py`, descrito acima — não estava no plano, foi encontrado pela verificação do item 6.

### Efeitos colaterais no ambiente real (a sonda rodou contra o `~/.gitpr/.env` de verdade)

- Os marcadores do arquivo foram regravados com **os mesmos valores** (todos `v0.0.24`), e `LINTER_PRESETS_VERSION=v0.0.24` foi acrescentado — o item 4 em ação. Backup do arquivo anterior: `/tmp/gitpr_env_backup_before_probe` (11212 bytes).
- `SCRIPTS_LANG='pt_br'` com `SCRIPTS_INSTALLED_LANG` **ausente**: a próxima execução de `gitpr` num repositório com `.git/hooks` reinstala os hooks uma vez e depois volta ao caminho rápido. É o desenho, não um incidente.

## Next steps

- **Entrega 2 — item 10, seção Smart Exclude.** Os mecanismos que ela precisa já existem: `show_if` (gate por enum), `group` (sub-cabeçalhos), `action` (botão com canal de status), `KIND_WORDS` (lista read-only renderizada), `Category.doc` (link de doc). Desenho esboçado: categoria nova **inserida imediatamente antes de `advanced`** (índice 10) — todos os ordinais fixos de `ListView.index` na suíte são ≤ 2 e as referências a `advanced` já são dinâmicas, então essa posição mantém `tests/test_config_app.py` válido. Três fontes: `~/.gitpr/conf/gitpr.docs-smart-excludes.json` e `~/.gitpr/conf/gitpr.smart-excludes.json` (globais, somente leitura, com botão de forçar download) e o `.gitpr/conf/gitpr.smart-excludes.json` do projeto (editável, criável se não existir — `_seed_local_smart_excludes` já faz isso em [core.py:94](src/core.py#L94)), com explicação de como funciona e `Category.doc = "smart-excludes.md"`. O editor é uma generalização do `KIND_WORDS` para lista de padrões, com adicionar/alterar valores.
- **Divergências de tradução pré-existentes, deixadas como estão** (fora do escopo desta entrega, sinalizadas pelos próprios revisores): `docs/ARCHITECTURE.pt_pt.md` não tem a seção `### **19. Multi-Forge SCM (ScmProvider)**` (25 títulos contra 26 no inglês, 236 contra 252 linhas) e `docs/ARCHITECTURE.fr_fr.md` não tem o parágrafo autônomo do `version-markers.md` que o inglês tem. Nenhuma das duas tem relação com as mudanças de hoje.
- **Nada foi commitado** — nem `git add`, nem `git commit`, nem `git push`: tudo fica na working tree para revisão, conforme a regra do `CLAUDE.md`.

### Verificação

- Suíte completa: **998 passed, 6 failed, 2 skipped** (33 subtests). As 6 falhas são exatamente as pré-existentes do baseline (`test_chat_backend::test_api_exception`, `test_main_suggest_reviewers::test_flag_appears_in_contextual_help`, `test_net_timeouts::TestTimeoutConfig` ×2, `test_suggest_reviewers::TestFormatHelpers` ×2). Baseline da mesma branch medida no início desta task: 938 passed → **+60 testes passando**, nenhuma falha nova.
- Sondas headless contra o ambiente real (`.env` real, `ConfigApp` real): os cinco botões baixam de verdade e regravam o marcador **no arquivo**; o filtro por provider e por forge re-filtra sem salvar; o valor de fallback aparece no lugar da caixa vazia; a lista de palavras mostra as 263 entradas; o caminho de falha é reportado como falha com a cópia anterior intacta.
- Verificação ponta a ponta do item 6 num repositório de rascunho, com `HOME` isolado: `fr_fr`, `es_es`, `pt_br`, vazio (segue `GITPR_LANG`) e inglês.
- **Falta a passada visual manual** (`gitpr config` na máquina, para conferir a rolagem com o mouse, o Ctrl+R sobre um botão e o modal de descarte no tamanho real da janela). O que é verificável sem interação já tem teste: `test_the_pane_still_scrolls_over_the_new_rows`, `test_ctrl_r_reaches_the_field_when_its_button_has_the_focus`, `test_escape_asks_before_discarding_pending_changes` e `test_the_search_still_finds_an_unselected_provider`.
