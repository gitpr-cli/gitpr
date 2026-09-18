# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.15 (2026-09-17)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.15):**
- **Subcomando `gitpr fix` — o review que vira patch aplicável:** Fecha o ciclo entre o review automático e a correção. O último review do cache alimenta **uma** chamada de IA, que devolve achados em blocos cercados; o extrator valida cada bloco como diff unificado, o `git apply --check` prova que ele encaixa na árvore atual e um classificador **determinístico e sem I/O** rotula cada candidato como `safe`, `review_required` ou `experimental`. Dry run é o default — escrever exige `--apply`. O `--force` nunca contorna a checagem de aplicabilidade, apenas a classificação, e exige frase de confirmação digitada. Tudo que foi aplicado entra em `.gitpr/fix_history.json`, que é o que o `--rollback` lê.
- **Subcomando `gitpr review-pr <n>` — revisar PR de terceiros sem checkout:** O diff vem direto da API da forge e entra **no mesmo motor** que os fluxos locais usam — mesmo relatório, mesmas regras de linter, mesmo `.txt`. Read-only por default: nada é publicado na forge sem `--post-comment` explícito. Amplia o público-alvo de "quem vai abrir um PR" para "quem foi convidado a revisar o PR de outra pessoa".
- **Resolução de identidade do revisor — o attach que não chegava:** As sugestões nascem do `git blame`, então carregam **nomes e e-mails**, não logins. Quando nada resolvia, a UI mostrava o nome puro — e digitar esse nome de volta fazia o GitPR enviá-lo *verbatim* como se fosse login. O GitHub responde **201 sem anexar ninguém**: sucesso aparente, revisor ausente, aviso nenhum. Agora uma camada dedicada resolve a identidade **duas vezes** (antes da TUI e no attach) e fecha também a segunda falha silenciosa da API — o login aceito mas não anexado passou a ser detectado lendo de volta `requested_reviewers`.
- **Camada SCM ganhou as primitivas para revisar uma revisão que não está no disco:** `get_pull_request(repo, pr_id)` virou método **concreto** da ABC (padrão do `create_release`) e foi implementado nas quatro forges — `list_open_pull_requests` pagina uma página só, então filtrá-la por número perde PRs antigos e não distingue fechado de inexistente. O atributo de classe `supports_reviewable_diff` (`False` no Azure DevOps, cuja API devolve lista de arquivos e não diff) barra a revisão **antes de qualquer chamada de rede**.
- **Dois defeitos latentes do GitLab consertados:** `changes[].diff` é um hunk solto, então o caminho do arquivo era descartado — a IA revisaria hunks órfãos e nem o chunker nem o filtro de exclusão funcionariam; os cabeçalhos `diff --git / --- / +++` passaram a ser sintetizados a partir de `old_path`/`new_path`. E `overflow: true` era ignorado: um diff truncado era revisado pela metade e publicado como se fosse inteiro — agora levanta.
- **`gitpr fix` passou a corrigir a revisão que foi revisada:** O diff revisado é gravado no registro de cache (`reviewed_diff`) e o `fix` o prefere, caindo na re-derivação só para registros antigos. É a única fonte correta quando o review veio de um PR remoto ou de um diff de branch inteira.
- **MCP cresceu de 12 para 14 ferramentas e de 17 para 18 recursos:** `list_fix_candidates` (13ª, somente leitura) + `skill://fix`, e `review_remote_pr` (14ª, somente leitura, sem argumento `post_comment`, sem escrever `.txt`).
- **i18n expandida para 1048 chaves:** +93 desde o relatório anterior (955 → 1022 com o `fix` → 1028 com os revisores → 1048 com o `review-pr`); `__lang_version__` subiu de v0.0.25 para **v0.0.28** (cadeia v0.0.25 → v0.0.26 → v0.0.27 → v0.0.28) e os 6 dicionários mantêm **paridade total de key sets**.
- **Documentação:** 2 famílias novas — `fix-command` (5 idiomas) e `review-pr` (EN + PT-BR) — e 9 tópicos atualizados, incluindo `code-review-ia` (modo remoto como §1.4), `suggested-reviewers` (resolução de login) e a §2.2 de `fix-command` reescrita nas 5 versões, porque o diff deixou de ser re-derivado.
- **Higiene de repositório:** uma árvore pip 25.2 auto-vendorizada (`pypa/`, `pip/cache/http-v2/`) tinha sido commitada por engano e foi removida; o `.gitignore` ganhou `pypa/` e `pip/`.
- **Salto de versão para 1.2.0:** o bump está no **working tree e ainda não foi commitado nem tagueado** (HEAD segue em 1.1.0; a última tag é `v1.1.0`), e o `CHANGELOG.md` ainda para em `[1.1.0] - 2026-09-13`.

- **Versão atual:** 1.2.0 (bump no working tree — HEAD em 1.1.0)
- **Versão dos dicionários de idioma:** v0.0.28
- **Versão dos scripts de hook:** v0.0.3
- **Publicação:** PyPI (`pip install gitpr-cli`) — canal binário removido na janela anterior
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal).
* **UI/Terminal:** Textual — TUI para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher, erros do linter (`LinterApp`), configuração (`ConfigApp`) e o novo modal `NoticeScreen` de avisos do PR Publisher 🆕.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API, tokens GitHub e tokens SCM das forges — os segredos editados na TUI de configuração também são cifrados antes de gravar.
* **Configuração:** `python-dotenv`, `pyyaml` (para o linter estático) + schema declarativo próprio (`src/config_schema.py`).
* **IA Providers:** Integração via SDK oficial do Google GenAI (`gemini-2.5-flash`), OpenAI SDK (`DeepSeek`), e OpenAI SDK (`Ollama` local).
* **Forge APIs:** `requests` (REST) — camada de abstração multi-forge em `src/infrastructure/scm/` (GitHub, GitLab, Bitbucket, Azure DevOps); módulo legado `src/github_api.py` mantido como shim deprecado.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — **14 ferramentas anotadas** 🆕, **18 recursos** 🆕, 7 prompts; handlers offloaded para threads via `anyio`.
* **Testes:** Pytest + `unittest.mock` (**64 módulos de teste — 41 na raiz, 9 em `tests/scm/`, 10 em `tests/fix/` e 4 em `tests/review/`** 🆕 —, 1437 cenários coletados) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio) + fixtures de repositório git real em `tests/fix/git_fixture.py` 🆕.
* **Empacotamento:** setuptools/build (PyPI).
* **CI/CD:** GitHub Actions (`pr-review.yml`) + `action.yml` para execução em pipelines.

---

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa ~90k tokens, divide automaticamente em lotes por arquivo (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce). Suporta PRs, commits e Issues.
* **Tokenizador Local:** `tokenizer.json` para estimativa precisa de tokens antes do envio para a IA.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()` com fallback para tokenizador local.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff` para reduzir contexto inútil.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo (system instruction + prompt) em JSON antes de cada chamada à IA.
* **Smart Excludes com Duas Camadas:** Filtro de pathspec inteligente com camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`). Mesclagem em runtime (união, deduplicada). Auto-seeding do arquivo local na primeira execução. `_load_smart_excludes()` aceita `force=` para re-download sob demanda a partir da TUI de configuração. 🆕 O template `templates/gitpr.smart-excludes.json` ganhou `.gitpr/fix_history.json` — um patch aplicado suja um arquivo **rastreado**, então sem isso ele apareceria nos diffs de `gitpr -c` e nas descrições de PR.
* **Métricas com Rastreamento de Tempo:** Injeção de `log_command_metric()` em todos os fluxos com repasse da duração em milissegundos (`duration_ms`) e lazy imports.
* **Resolução Centralizada de Output:** Função `resolve_output_path()` que centraliza a lógica de diretórios de saída — default em `.gitpr/reports/{type}/`.
* **Wizard SCM (`run_scm_init_wizard()`)**: `gitpr --init` — detecta a forge pelo remote origin, solicita extras por forge (org/projeto Azure, usuário Bitbucket), valida o token com `test_connection` (3 tentativas, 401 re-prompt) e persiste `GITPR_SCM_PROVIDER` + `GITPR_SCM_TOKEN_ENCRYPTED` (Fernet) **somente em sucesso**.
* **Skill Template de Release (`ensure_release_skill_template()`)**: Baixa `templates/gitpr.release.*.md` no primeiro uso de `gitpr release` (CLI layer, idioma-aware, nunca sobrescreve; pulado em `--format json`).
* **Registro de Skills Compartilhado:** `SKILL_FILES_BY_TYPE` / `SKILL_TYPES` / `DEFAULT_SKILL_TYPE` vivem em `src/config.py` (a TUI não pode importar `core` no topo — puxa os SDKs de IA); `get_skill_context()` usa `skill_file_for()`. 🆕 O `files_to_download` precisou de entrada própria para `gitpr.fix.md` — mexer só no `SKILL_FILES_BY_TYPE` não bastava para o `--skill` baixar o template.
* **Motor de Review com Escopo de Cache (`generate_pr_content`) 🆕:** Dois parâmetros **aditivos** — `cache_scope` (anexado **só à chave de cache**, nunca ao prompt) e `store_diff` (grava o diff revisado no registro). Os defaults `""`/`False` mantêm o caminho local **byte-idêntico**: zero invalidação de cache para os reviews locais já existentes. É o que permite um review remoto ser escopado por `::diff-source::pr-<n>` sem que um review local do mesmo diff o responda por engano.
* **Trailer de Coautoria:** `COAUTHOR_TRAILER` + `append_coauthor_trailer()` — idempotente, preserva trailers de terceiros.
* **Subprocessos Blindados:** `stdin=subprocess.DEVNULL` + `encoding='utf-8'`/`errors='replace'` em todos os `subprocess.run`; verificação de conexão via socket `8.8.8.8:53` antes de operações de rede.

### **2. Sistema de Plugins Global (`src/plugins.py`)**

* **Arquitetura de Plugins:** Sistema de extensibilidade que carrega plugins do diretório `~/.gitpr/plugins/` aplicando-se a **todos os projetos**.
* **Plugins de Linter (`linter/`):** Arquivos `.yml` com regras de regex adicionais mescladas com o `.gitpr.linter.yml` local.
* **Plugins de Prompt MCP (`prompts/`):** Arquivos `.md` que estendem o contexto do sistema com instruções específicas.
* **Factory Closures:** Funções `get_linter_plugins` e `get_prompt_plugins` com closures para isolar estado entre sessões.
* **Comando `--plugins`:** Lista todos os plugins globais instalados com seus tipos e paths.
* **Documentação Multilíngue:** `docs/plugins-system.md` em 5 idiomas (EN, PT-BR, PT-PT, ES, FR).

### **3. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria a pasta `~/.gitpr/`, e solicita interativamente as chaves de API, preferências e idioma.
* **Routing de Comandos:** Gerencia todas as flags e os **4 subcomandos** — `release`, `config`, `fix` 🆕 e `review-pr` 🆕.
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags (35 opções Click na raiz, inalterado nesta janela):**
  * `--init`: Abre o wizard de configuração SCM multi-forge (detecção da forge + validação do token).
  * `--no-suggest-reviewers`: Desliga a sugestão de revisores no fluxo de publicação de PR.
  * `--no-publish`: Gera a descrição do PR e salva localmente sem abrir o editor interativo.
  * `--no-edit`: Pula a TUI completamente — auto-commit, auto-push e publica direto na forge.
  * `--base <branch>`: Sobrescreve a branch de destino do Pull Request.
  * `--plugins`: Lista plugins globais instalados.
  * `--linter-setup`: Abre o assistente interativo de configuração de linters externos.
  * `--version`: Exibe a versão atual do GitPR (via `@click.version_option`).
* **Subcomando `fix` 🆕 — 8 opções:** `--list` (lista os candidatos do último review — o que o comando faz sem argumento), `--apply` (escreve na árvore; sem ele é dry run), `--all-safe` (seleciona todos os `safe`; escrever ainda exige `--apply`), `--create-branch <name>`, `--no-branch`, `--yes` (pula a confirmação, **nunca** contorna o `--force`) e `--force` (aplica patch não-seguro após frase digitada) e `--rollback <patch-id>`. Argumento opcional `[<finding-id>]`. Molde exato do `release`: imports lazy no corpo e `epilog` para `get_doc_url("fix-command.md")`. Nenhuma flag existente mudou de sentido — o `--force` do `release` ("regerar seção existente") não colide porque namespaces de subcomando são separados.
* **Subcomando `review-pr` 🆕 — 2 opções:** `review-pr <number>` com `--provider <name>` e `--post-comment`; read-only por default, **nunca** chama `check_unstaged_files`, grava `{branch}_{datetime}_PR_REVIEW.txt` com o nome da branch de origem do PR. Rejeita o PR **antes de qualquer chamada de IA** por capacidade, existência, estado, diff vazio/não-revisável e esgotamento dos smart-excludes. Reusa `_resolve_scm_context`.
* **Variáveis de Ambiente (44 chaves no `DEFAULT_CONFIG`, +5 nesta janela 🆕):** as cinco `GITPR_FIX_*` — `GITPR_FIX_SAFE_MAX_LINES_CHANGED`, `GITPR_FIX_SAFE_EXCLUDED_PATHS`, `GITPR_FIX_REQUIRE_CONFIRMATION`, `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE` e `GITPR_FIX_BRANCH_NAME_TEMPLATE`. `get_fix_settings()` devolve o bloco achatado e **falha para o default embutido** quando o valor é esvaziado por acidente — limpar o campo não pode derrubar a proteção em silêncio.
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub. Subcomandos têm `epilog=` próprio (parágrafo `\b` do Click para a URL não ser reembrulhada sob nenhum locale).
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **14 ferramentas anotadas + 18 recursos + 7 prompts** 🆕.
* **--install:** Assistente guiado de 4 etapas que baixa templates de skill, instala Git Hooks, configura MCP nos editores e valida chaves de API.
* **--metrics:** Sistema de telemetria local com escopo por repositório: `--export`, `--purge`, `--dashboard`.
* **--status:** Lista arquivos não commitados categorizados (new/modified/deleted) — rápido, sem IA, sem rede.
* **Camada de escrita do `.env`:** `read_env_file_values()` lê **só o arquivo** via `dotenv_values` (imune a `os.environ`), `save_config_values()` grava com `set_key`, `remove_config_value()` com `unset_key`. `validate_ai_key()` sonda os SDKs Gemini/DeepSeek com timeouts curtos e distingue credencial recusada (`401`/`403`) de rede inalcançável.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI construída com Textual para revisar, editar e publicar Pull Requests diretamente no terminal.
* **7 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen` e **`NoticeScreen`** 🆕.
* **Avisos Bloqueantes (`NoticeScreen`) 🆕:** Um modal que exige reconhecimento (Esc ou Close) antes de o fluxo de merge continuar. É intencional: sem ele o prompt de merge assumiria a tela e os avisos de revisor descartado passariam despercebidos — mas pausa fluxos automatizados quando há avisos.
* **`_attach_reviewers` com resolução 🆕:** Resolve o que o usuário digitou **antes** de enviar, reporta o que foi descartado e, num `422` de lote com vários revisores, **repete um a um** — o GitHub rejeita o lote inteiro quando um único login é inelegível (o autor do PR, um não-colaborador), o que antes derrubava também os revisores válidos.
* **Suggested Reviewers:** O fluxo de publicação consulta a forge por revisores sugeridos e os oferece na TUI; seleção controlada por `--no-suggest-reviewers`, `GITPR_SUGGEST_REVIEWERS`, `GITPR_REVIEWER_SUGGESTION_TOP_N` e `GITPR_REVIEWER_SUGGESTION_EXCLUDED`. 🆕 `_reviewer_suggestion_view()` monta `resolutions` via `resolve_candidates`, pré-preenche `handles` e marca quem não tem conta para as linhas de hint sinalizarem; as `resolutions` viajam na view para o attach não resolver as mesmas pessoas duas vezes.
* **Bindings:** F1 (Help), F2 (Salvar .md local), F3 (Publicar via forge), Esc (Sair).
* **Fluxo de Auto-Commit:** Linter → mensagem IA → confirma → commita → push → publica PR.
* **Verificação de Arquivos Unstaged:** Ao iniciar, verifica `git status --porcelain` e oferece modal para selecionar, pular ou cancelar.
* **Tratamento de PR Existente:** Detecta PRs abertos para a branch atual via API e oferece push ou criar novo.
* **Auto-Upstream:** Detecta falha de `git push` por falta de upstream e automaticamente tenta `--set-upstream origin <branch>`.
* **Merge Flow:** Após criação/atualização do PR, oferece opção de merge. Controlado por `GITPR_AUTO_MERGE`.

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Shim Deprecado:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` e demais funções delegam a `src/infrastructure/scm/github_provider.py`; o módulo emite `DeprecationWarning` e mantém as tuplas legadas `(ok, data, status)` — nenhum código novo pode importá-lo.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no git diff sem gastar cotas de IA.
* **Regras YAML:** Lê o arquivo local `.gitpr.linter.yml` (criado via `--skill`).
* **Plugins de Linter:** Regras adicionais carregadas de `~/.gitpr/plugins/linter/*.yml`.
* **Bridge de Linters Externos:** Executa ESLint/PHPCS/Stylelint nas linhas alteradas do diff, parser Checkstyle XML e cruzamento por linha.
* **`skip_external` — o bridge não pode lintar a árvore errada 🆕:** `parse_diff_and_lint(..., skip_external=False)` ganhou o parâmetro que desliga os **dois** call-sites do bridge externo. O fluxo remoto passa `True`, porque o bridge roda binários **contra arquivos no disco** — a árvore local do usuário, não o PR — e esses alertas seriam publicados como comentário público no PR de outra pessoa.
* **Relatório Consolidado:** `generate_linter_report_content()` consolida erros regex + externos em `.gitpr/reports/linter/` — gerado apenas quando há violações.
* `load_linter_presets()` aceita `force=` para re-download dos presets a partir da TUI.

### **7. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data` e `decrypt_data` para proteger chaves de API de IA, GitHub PAT e tokens SCM das forges (`GITPR_SCM_TOKEN_ENCRYPTED`).
* **Validação Multi-Forge:** `validate_or_request_scm_token(provider, repo_display)` — valida o token na forge configurada com 401 → loop de reautenticação preservando o rascunho; o token GitHub legado (`GITHUB_TOKEN_ENCRYPTED`) permanece funcional até o `--init` rodar.
* **Segredos na TUI de Configuração:** Campos `KIND_SECRET` são editados em campo mascarado, **nunca** exibem o valor em claro e são cifrados com Fernet antes de gravar — nenhum caminho lê o segredo de volta para a tela. `GITPR_SCM_TOKEN` é `read_only` e sua descrição aponta `gitpr --init` como o único caminho que deve escrevê-lo.

### **8. Auto-Updater (`src/updater.py`)**

* **PyPI como Fonte Única:** `get_latest_remote_version()` consulta sempre `https://pypi.org/pypi/gitpr-cli/json`, devolve **string** de versão e grava o cache diário **sem** o campo `download_url`.
* **Portão Obrigatório (`enforce_update_required()`):** Devolve `True` (depois de imprimir as duas versões e o comando pip) quando a versão publicada é mais nova; devolve `False` quando está atualizado, quando a versão remota é **desconhecida (offline — o usuário não teria como atualizar)** ou quando a checagem está desligada. Devolver `bool` em vez de chamar `sys.exit` internamente mantém a função testável.
* **`check_and_update()`:** Só consulta e **informa**, nunca instala.
* **Escape Hatch:** `GITPR_SKIP_UPDATE_CHECK` (qualquer valor não-vazio) — não é advertised como recurso ao usuário; existe para a suíte de testes e automação offline.
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Versionamento Centralizado:** `__version__` (**1.2.0** — bump no working tree), `__lang_version__` (**v0.0.28** — cadeia v0.0.25 → v0.0.26 → v0.0.27 → v0.0.28 nesta janela 🆕), `__scripts_version__` (**v0.0.3**), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`.

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Construída com Textual — histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico de conversa persistido por branch, permitindo continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear` — atalhos para pair programming.
* **Auto-Patching (F5), Atualização de Diff (F2), Exportação de Sessão (F6).**
* **Extrator Compartilhado 🆕:** O bloco da regex estava **duplicado** em F5 e `ctrl+s`; ambos passaram a chamar `patch_extractor.extract_code_blocks()`. O arquivo perdeu 31 linhas e ganhou 3, com **comportamento visível idêntico** (mesmas teclas, mesmo `GITPR_PATCH_SUGGESTION_<key>.txt`, mesmo conteúdo) — por isso não há nota de changelog sobre o chat. É também a razão pela qual o `__init__.py` de `src/fix/` é **só docstring**: o chat o importa em toda sessão, e um `__init__` que reexportasse arrastaria junto as camadas de IA e de git (ver ADR-004, alternativa rejeitada).

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com suporte a placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas, 6 Dicionários:** en_us (padrão/fallback), pt_br, pt_pt, es/es_es, fr/fr_fr.
* **Arquivos Versionados:** `__lang_version__` (**v0.0.28**) controla atualização dos pacotes de idioma (`langs/*.json`) — cadeia de bumps v0.0.25 → v0.0.26 → v0.0.27 → v0.0.28 nesta janela.
* **Cobertura:** **1048 chaves** de tradução em cada um dos 6 arquivos — **paridade total de key sets** (+93 desde o relatório anterior).
* **Snapshot de Ambiente (`AMBIENT_ENV_KEYS`):** `frozenset(os.environ)` capturado em `i18n.py` **imediatamente antes** do `load_dotenv()` de nível de módulo — corrige o badge "⚠ no ambiente" que confirmava tautologicamente que a chave está no arquivo.
* **Chave Reescreita 🆕:** `GitHub usernames, comma separated` → `GitHub login, name or email, comma separated` — o campo deixou de prometer o que não aceitava.
* **Cache com Indexação por Idioma:** Respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas. `_load_thinking_words()` / `reload_thinking_words()` aceitam `force=`.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Modo JSON & Parâmetros Determinísticos:** Outputs estruturados com `temperature=0.0` e `top_p=0.1`; fallback automático entre provedores configurados.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt, com indexação por idioma.
* **Seleção do Último Review (`resolve_last_review()`) 🆕:** Junto com `REVIEW_ACTION_TYPES`, escolhe o registro `review`/`fullreview` **mais novo** para um par repo+branch, **excluindo reviews de escopo de arquivo** (`-i`), que não descrevem a branch. É a porta de entrada do `gitpr fix`.
* **Diff Revisado (`reviewed_diff`) 🆕:** Campo no topo do registro que guarda o diff efetivamente revisado. Preferido por `fix/apply_fix.reviewed_diff()`, com fallback para re-derivação em registros antigos — a única fonte correta quando o review veio de um PR remoto ou de um diff de branch inteira.
* **Telemetria e Duração:** Persistência dos campos `duration_ms` e `meta_raw` em arquivos de cache.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` lê todos os arquivos de cache recursivamente.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`), e Arqueologia por Blame (`-b`).
* **Publicação Multi-Forge:** F3 cria a issue na forge **configurada** (`GITPR_SCM_PROVIDER`) via `provider.create_issue` — Azure DevOps levanta `ScmNotSupportedError` (Work Items dependem do process template).
* **Map-Reduce para Issues:** Quando o contexto excede ~90k tokens, divide automaticamente em chunks e unifica os resultados.
* **Tratamento de 401:** Sinalização de reautenticação sem fechamento da aplicação.

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia a evolução e autoria histórica de trechos de código com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos registrados via `log_blame_metric()` com rastreamento de profundidade e número de commits analisados.

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)**

* **14 Ferramentas MCP Anotadas 🆕:** `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`, **`list_fix_candidates`** (13ª — candidatos do último review com patch, classificação e id; somente leitura) e **`review_remote_pr`** (14ª — review de PR aberto na forge, buscado por número; somente leitura, **nunca** comenta e **nunca** escreve arquivo, resolve a forge sozinho).
* **18 Recursos + 7 Prompts Templatizados 🆕:** `skill://list` + `skill://{pr,commit,review,filereview,issue,blame,release,fix}` (**`skill://fix` é novo**) + `linter://config` + `prompt://list` + 7 prompts.
* **Invocação CLI Direta:** Comando `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool MCP diretamente sem iniciar o servidor stdio JSON-RPC. `gitpr-mcp --list` imprime o registry completo como JSON.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve diretamente no `sys.__stdout__` original, garantindo JSON puro no stdout — razão pela qual o log de uso **nunca** imprime.
* **Offload do Event Loop:** Decorator `_offload` (`anyio.to_thread.run_sync`) aplicado às 14 tools — handlers síncronos não congelam o servidor stdio.
* **Log de Uso:** `main()` do servidor chama `log_usage()` — o console script `gitpr-mcp` nunca carrega `main.py`, então este é o único ponto que o alcança.
* **Testes E2E:** `tests/test_mcp_server_e2e.py` sobe o servidor real como subprocess e fala JSON-RPC stdio.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório (Repo-Scope):** Rótulo `📁 Repository: owner/repo` e filtragem estrita por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com widget `ProgressBar`.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de cache ao totalizador.
* **Exportação Local:** Salvamento de CSV/JSON em `./.gitpr/metrics/export/` — 🆕 os artefatos `gitpr_metrics_2026-09-17.csv`/`.json` entraram **rastreados** pelo PR #171 e são candidatos a `.gitignore`.

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`.
* **Eventos de Hook, Linter e Blame:** `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()`.
* **Exportação e Limpeza:** `--metrics --export` (CSV/JSON) e `--metrics --purge` com confirmação interativa.

### **19. Sincronização de Idiomas dos Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (v0.0.3) controla a versão dos scripts de hook; detecção automática e atualização.
* **Mapeamento de Sufixos (`HOOK_SCRIPT_SUFFIXES`):** Códigos de interface (`es_es`, `fr_fr`) traduzidos para os sufixos realmente publicados (`.es`, `.fr`).
* **Escolha vs. Estado (`SCRIPTS_LANG` / `SCRIPTS_INSTALLED_LANG`):** `SCRIPTS_LANG` é a escolha do usuário; `SCRIPTS_INSTALLED_LANG` é o que está em disco. Separados, a auto-sincronização consegue **detectar a troca de idioma**.
* **`effective_hook_lang()`:** Resolve o idioma efetivo dos hooks; `--lang` deixou de ser descartado nesse caminho (mudança de comportamento documentada).
* **Skip de Merge-Source:** O template `prepare-commit-msg` pula as fontes `message|merge|squash|commit` — commits gerados pelo git preservam a mensagem original.

### **20. Bridge de Linters Externos e Assistente Interativo (`src/linter_wizard.py`, `src/ui/linter_app.py`)**

* **Assistente `--linter-setup`:** Wizard interativo com presets numerados (PHP_CodeSniffer, ESLint, Stylelint) e injeção do bloco `external_linters` no `.gitpr.linter.yml`.
* **Presets Remotos:** `templates/gitpr.linter-presets.json` servido do GitHub com cadeia de resolução local → download → stale → fallback embutido.
* **TUI de Erros do Linter:** `src/ui/linter_app.py` (Textual) exibe erros críticos e warnings; em hook/quiet imprime e faz `sys.exit(1)`.
* **Relatório Markdown:** Consolidado em `.gitpr/reports/linter/` — apenas quando há violações.

### **21. SCM Multi-Forge (`src/infrastructure/scm/`)**

* **Abstração Única (`ScmProvider` ABC):** `base.py` define o contrato (dataclasses `RepoRef`, `PullRequestDraft` etc. e `ScmProviderError(provider, http_status, message)` — `http_status` 0 = falha de rede); um provider concreto por forge em `github_provider.py`, `gitlab_provider.py`, `bitbucket_provider.py`, `azure_devops_provider.py`.
* **Registry e Factory:** `resolve_scm_provider()` seleciona por `GITPR_SCM_PROVIDER` (default `github` — migração zero, fallback do token GitHub legado intacto); `detect_provider_from_remote()` identifica a forge pela URL do origin.
* **Endereçamento de Repositório:** `parse_repo_ref(remote_url) -> RepoRef(raw, workspace, name, provider)` — workspace = owner GitHub / namespace GitLab (subgrupos) / workspace Bitbucket / display `{org}/{project}` do Azure.
* **`get_pull_request(repo, pr_id)` — método concreto da ABC 🆕:** Padrão do `create_release`: default levanta `ScmNotSupportedError` e cada uma das quatro forges implementa. Existe porque `list_open_pull_requests` pagina **uma página só** — filtrá-la por número perde PRs antigos em silêncio e **não distingue fechado de inexistente**, e o `review-pr` precisa rejeitar o PR por motivo certo antes de gastar IA.
* **`supports_reviewable_diff` — portão de capacidade 🆕:** Atributo de classe, `False` no Azure DevOps, checado **antes de qualquer chamada de rede**. A API REST do Azure devolve uma **lista de arquivos**, não um diff unificado — revisar seria inventar conteúdo.
* **Cabeçalhos do GitLab Sintetizados 🆕:** `changes[].diff` é um **hunk solto**; `old_path`/`new_path` eram ignorados, então o caminho do arquivo se perdia — a IA revisaria hunks órfãos e nem o chunker nem o filtro de exclusão teriam em que se apoiar. Agora o provider monta os cabeçalhos `diff --git a/… / --- / +++`, honrando `/dev/null` para arquivos adicionados/removidos.
* **`overflow` do GitLab Levanta 🆕:** Um MR cujo diff estoura o limite da API era revisado **pela metade** e publicado como se fosse inteiro; agora levanta `ScmProviderError` com mensagem clara.
* **`request_pull_request_reviewers` devolve `list[str]` 🆕 (quebra de contrato):** Retornava `None`; agora devolve os logins **efetivamente anexados**, lidos do corpo do `201`. É a única forma de detectar um login aceito e silenciosamente ignorado. `None` continua sendo tratado como "não é possível verificar", nunca como falha — callers antigos não quebram, apenas perdem o read-back. Subclasses de terceiros **precisam** ser atualizadas.
* **Dois Helpers Read-Only do GitHub 🆕:** `get_commit_author_login` (mapeia um SHA ao conta ligada ao e-mail do autor — o caminho confiável para endereços corporativos que a API de busca de usuários não enxerga) e `get_user_login` (valida/canonicaliza um handle digitado, rejeita o que não pode ser login **sem gastar requisição** e distingue 404 de erro transitório).
* **Fail-Fast por Forge:** Azure DevOps exige `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`; Bitbucket exige `GITPR_SCM_USERNAME` (App Password = Basic auth user+token); `create_issue` no Azure levanta `ScmNotSupportedError`.
* **Publicação de Releases:** `provider.create_release()` usado pelo `gitpr release --publish` (GitHub cria a tag no branch default; GitLab exige a tag existente).
* **Artefatos:** Glossário + ADR-001/ADR-005 em `docs/plans/`; família `docs/scm-multiforge.*.md` em 5 idiomas; testes: 9 arquivos, **282 cenários** (+17 nesta janela).

### **22. Subcomando `gitpr release` — Changelog / Release Notes**

* **Fluxo:** `git log` entre `--since` (default: última tag alcançável, ou o primeiro commit) e `HEAD` → classificação por Conventional Commits → bump semântico sugerido (`--version <x.y.z>` sobrescreve) → montagem do changelog → resumo executivo de IA opcional → *prepend* no `CHANGELOG.md`. Geração local é o default — nada é publicado nem tocado sem pedido.
* **Classificador (`src/commit_classifier.py`):** Classifica os commits por tipo Conventional Commits (feat/fix/refactor/docs/chore/etc.) com parser tolerante.
* **Builder com Seções Traduzíveis (`src/changelog_builder.py`):** Seções "✨ Features", "🐛 Bug Fixes", "⚠️ Breaking Changes", "Summary", "Contributors" etc. renderizadas via `__()` em runtime (seguem o `--lang`).
* **Bump Semântico (`src/version_bump.py`):** Sugere a próxima versão a partir dos tipos classificados (major para breaking, minor para feat, patch para fix) e valida alvos `x.y.z`.
* **Publicação:** `--publish` cria a release na forge configurada (com confirmação explícita); `--draft` cria como rascunho (GitHub; GitLab não tem conceito de draft); `--format markdown|json` para saída estruturada; `--force` para regravação. **6 opções no subcomando.**
* **Skill Template:** No primeiro uso baixa `templates/gitpr.release.*.md` (5 idiomas) via `ensure_release_skill_template()` — nunca sobrescreve.
* **Pendência de release 🆕:** O `CHANGELOG.md` **não** foi tocado nesta janela — a última entrada segue sendo `[1.1.0] - 2026-09-13`, enquanto o `__version__` já diz 1.2.0. Rodar `gitpr release` é o passo que falta.
* **Artefatos:** Família `docs/release-notes.*.md` (5 idiomas), spec em `docs/plans/`, ADR-002 e ADR-003, glossário de release notes.

### **23. Subcomando `gitpr config` — TUI de Configuração**

* **Tela Master-Detail (`src/ui/config_app.py`):** Categorias à esquerda, campos da categoria à direita, editados inline. Cabeçalho com busca (`/`) e contador de pendências (`● N não salvas`); rodapé com `F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc`. `Geral` é sempre a primeira entrada do menu.
* **Schema Declarativo (`src/config_schema.py`) — a fonte única de verdade:** 🆕 **13 categorias** (Geral, Provedores de IA, Pull Request, Revisão de Código, Issue, Blame, Linter, Release, SCM / Forge, Filtros de Diff, Skills, **Fix** e Avançado) e **61 `ConfigField`**, dos quais **8 avançados** (+1 categoria e +5 campos nesta janela). Cada campo declara categoria, tipo de widget (`bool`/`int`/`str`/`enum`/`template`/`path`/`secret`/`version`/`words`), `show_if`, validadores, marcadores de versão e ações de download. Rótulos são literais `__()` para o scanner de i18n.
* **Categoria `fix` 🆕:** Os cinco `GITPR_FIX_*` ganharam superfície editável com descrições que explicam a consequência de cada um (orçamento de linhas, globs sensíveis, exigir confirmação, criar branch no lote all-safe e o template do nome da branch).
* **Filtragem por Contexto (`show_if`):** `GEMINI_*` / `DEEPSEEK_*` / `OLLAMA_*` aparecem conforme o `DEFAULT_AI_PROVIDER` selecionado; `GITHUB_TOKEN_ENCRYPTED` aparece com provider vazio ou `github`; `GITPR_SCM_USERNAME` sob `[Bitbucket]`; `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT` sob `[Azure DevOps]`. Trocar o `Select` re-filtra o painel **na hora, sem F2**.
* **Busca Global (`/`):** Casa chave ou rótulo em todas as categorias e **ignora o filtro de visibilidade** — procurar `deepseek` com o Gemini selecionado acha os campos, para permitir pré-preenchê-los.
* **Validação em Duas Camadas:** **Offline** (tipo, enum, template com placeholder conhecido e `{datetime}` obrigatório) bloqueia o `F2` com erro inline; **online** (só para credenciais alteradas na sessão) roda em worker com timeout de 10s e só bloqueia em `401`/`403` — falha de rede permite gravar.
* **Restaurar (`Ctrl+R`):** Remove a linha do `.env` em vez de reescrever o default; **`Esc`** com alterações pendentes pede confirmação; categoria **Desconhecidas** preserva chaves fora do schema em modo leitura.
* **Seção Skills — a única project-scoped:** Painel master-detail inline que edita `.gitpr/skill/*.md` do projeto resolvidos a partir do diretório de chamada, gravando atomicamente e preservando CRLF/LF. `F2` grava o `.env` e os arquivos de skill **na mesma passada**.
* **Downloads com Força:** Botões que forçam re-download de smart-excludes, traduções, presets de linter e thinking words, via parâmetro `force=` encadeado nos loaders.
* **Módulo de Links Leve (`src/doc_links.py`):** `doc_url()` saiu de `core.py` para que a UI obtenha o link da documentação sem importar `core`/SDKs de IA.
* **Testes:** 5 arquivos — `test_config_app.py` (78), `test_config_schema.py` (42), `test_config_validation.py` (40), `test_config_store.py` (22), `test_config_cli.py` (9). 🆕 O `test_config_schema.py` passou a cobrir os campos novos (a asserção de que `advanced` só existe em Avançado continua valendo para os 61).
* **Artefatos:** `docs/config-tui.*.md` em 5 idiomas, plano `docs/plans/20260912_config_tui.md`, glossário `glossary-config-tui.md` (8 termos) e survey do grill.
* **Dívida conhecida:** `gitpr -h config` abre a TUI e ignora o `-h` — o gate `if ctx.invoked_subcommand is not None: return` roda antes do bloco de `help_flag`; corrigir mudaria o comportamento de `-h` para **todos** os subcomandos (documentado em `docs/config-tui.md`).

### **24. Log Geral de Uso (`src/usage_log.py`)**

* **Uma Linha por Comando:** Grava `~/.gitpr/logs/<uuid5>.log`, **um arquivo por dia**, com o comando, argumentos, repositório, usuário e timestamp. Serve para responder "o que eu realmente rodei, e quando?".
* **Nome Derivado da Data:** `uuid5(NAMESPACE_DNS, f"gitpr.usage.{YYYY-MM-DD}")` em vez de aleatório — um nome aleatório exigiria contador ou arquivo de estado para saber qual arquivo é o de hoje, e dois processos concorrentes poderiam discordar.
* **Escrita Síncrona (decisão explícita):** Diferente de `log_local_metric`, que usa thread daemon e por isso perde a gravação se o processo sair antes — inaceitável para um log que promete registrar *todo* comando.
* **Nunca Imprime:** O servidor MCP reserva o stdout para JSON-RPC; um `print` acidental corromperia o protocolo. O módulo também nunca levanta exceção.
* **Um Único Spawn de Git:** `git config --get-regexp '^(remote\.origin\.url|user\.name|user\.email)$'` em vez dos três idiomáticos — ~40 ms em vez de ~150 ms no Windows, em *toda* execução.
* **`_repo_label()` Própria:** Sem reusar `get_repo_name()` de `core.py` (regex fixa em `github.com`, devolveria `unknown/repo` em GitLab/Bitbucket/Azure) e sem `parse_repo_ref`, que é método de provider e exigiria construir um provider (token, `requests`) a cada comando.
* **Controle:** `GITPR_SHOW_LOGS` (default `"true"`); desligado em `tests/conftest.py`.
* **Dogfooding 🆕:** O log de execução de um `pr_desc` anterior foi a evidência que isolou o bug do revisor — a linha `Reviewers requested on PR #1068: ['Eduarda Leal']` provou que o **nome** ia como login e que o `_request()` retornava sem levantar. Sem esse registro, o sintoma ("não aparece no PR") não teria como ser distinguido de uma falha de rede.
* **Artefatos:** `docs/usage-log.*.md` em 5 idiomas; `tests/test_usage_log.py` (27 cenários).

### **25. Subcomando `gitpr fix` — Achados de Review como Patches Revisáveis (`src/fix/`) 🆕**

* **O que é:** Capacidade **nova**, não generalização do chat. A investigação obrigatória (passo 0 do plano) derrubou três premissas da spec: o chat **nunca** aplicou patch nenhum (F5 e `ctrl+s` gravam um `.txt` no CWD, sem `subprocess` e sem diff válido), finding com `id`/`severity`/`file_path` **não existia** em lugar nenhum, e `config.schema.yml` nunca existiu.
* **O Pipeline Real:** último review do cache (`resolve_last_review`) → **uma** chamada de IA (`call_ai_model`, nunca `generate_pr_content`, cujo `else` é o ramo de PR) → extração e validação de diff unificado → `git apply --check` → classificação determinística → dry run ou escrita → histórico.
* **Pacote de 8 arquivos (1147 linhas):**
  * `patch_provenance.py` — contrato de dados puro: `PatchSafety`, `FindingRef`, `PatchCandidate` (com `patch_id` derivado), `PatchProvenance`, `ApplyFixResult`.
  * `patch_extractor.py` — blocos cercados + validação de diff unificado; **compartilhado com o chat**.
  * `patch_safety_classifier.py` — `safe`/`review_required`/`experimental`, lógica **pura, sem I/O e sem IA**; devolve **código de motivo**, nunca frase pronta.
  * `patch_applier.py` — primeiro invólucro de `git apply` do projeto (`--check`, `apply`, `--reverse`, `checkout -b`, `status`).
  * `fix_history.py` — `.gitpr/fix_history.json` com escrita atômica (`.tmp` + `os.replace`).
  * `apply_fix.py` — o caso de uso (470 linhas).
  * `rollback_fix.py` — `git apply --reverse` sobre o diff guardado, com três recusas distintas.
  * `__init__.py` — **só docstring**, e que ordena os módulos de propósito (ver ADR-004).
* **Classificação Determinística:** Recusa patch que atravesse mais de um arquivo ou mais de um hunk, que toque caminho sensível configurado, que estoure o orçamento de linhas adicionadas+removidas, que **apague uma linha com cara de chamada**, declarado de baixa confiança pela IA, ou que falhe no `git apply --check` contra a árvore atual. O `--force` **nunca** contorna a checagem de aplicabilidade — só a classificação.
* **Escrita Opt-In:** Dry run é o default; qualquer mutação exige `--apply` (ou frase de confirmação digitada com `--force`).
* **Suporte:** `src/diff_parser.py` ganhou `summarize_patch()` / `PatchSummary` (puros) — contagem de arquivos, de hunks, delta de linhas e detecção de chamada removida — usados pelo classificador.
* **MCP:** 13ª tool `list_fix_candidates` (somente leitura) e o recurso `skill://fix`.
* **Skill:** `templates/gitpr.fix.md` + `.pt_br.md` (persona: Senior Software Engineer), baixados por `gitpr --skill`.
* **Configuração e Artefatos:** 5 variáveis `GITPR_FIX_*` + categoria `fix` na TUI; `docs/fix-command.*.md` (5 idiomas, 8 seções); ADR-004 e `glossary-gitpr-fix.md`; spec/plano/survey em `docs/plans/` e `docs/survey/`.
* **Testes:** 10 arquivos em `tests/fix/` (**204 cenários**) com fixtures de repositório git real (`tests/fix/git_fixture.py`) — matriz do classificador, applier, histórico, roteamento CLI, rollback, settings e o extrator compartilhado com o chat.

### **26. Subcomando `gitpr review-pr` — Review de PR Remoto (`src/review/`) 🆕**

* **O que é:** Orquestração, **não** um segundo motor de review. O motor existente (`generate_pr_content`), o linter (`parse_diff_and_lint`) e o renderizador são as peças do fluxo local, alimentadas com um diff que veio de outro lugar — um `.txt` de review remoto e um de review local do mesmo diff diferem **só no nome do arquivo**.
* **Pacote de 5 arquivos (560 linhas):**
  * `diff_source.py` — `DiffOrigin` + `DiffSource`: proveniência pura (`cache_scope`, `is_remote`), sem I/O.
  * `diff_normalizer.py` — normalização de newline, validação de diff (`is_reviewable_diff`) e o filtro de smart-excludes **em Python**, para um diff que o git nunca viu.
  * `render.py` — composição e escrita do artefato, **extraída de `main.py`** e agora **compartilhada** com os fluxos locais.
  * `remote_pr.py` — o caso de uso: portão → PR → diff → normalizar → excluir → motor → linter → comentário opcional.
  * `__init__.py` — marcador de pacote.
* **`split_patch_sections` (`src/diff_parser.py`) 🆕:** Devolve o caminho de cada arquivo **ao lado** do próprio texto — base do filtro de exclusão remoto e da síntese de cabeçalhos do GitLab.
* **Read-Only por Default:** `--post-comment` é o **único** caminho que escreve na forge. O mesmo vale para a tool MCP `review_remote_pr`, que sequer recebe o argumento.
* **Interação com o `fix` 🆕:** Como o review remoto não corresponde a nenhuma árvore local, o diff revisado passou a ser guardado no cache (`reviewed_diff`) e o `fix` o prefere — corrigindo um defeito que só apareceria depois desta feature.
* **Artefatos:** `docs/review-pr.md` + `.pt_br.md` (8 seções), `docs/code-review-ia.*.md` (modo remoto como §1.4 + a ressalva do linter externo, nas 5 versões), ADR-005 e `glossary-review-pr.md`; spec, plano e survey em `docs/plans/` e `docs/survey/`.
* **Testes:** 4 arquivos em `tests/review/` (**97 cenários**) — `test_remote_pr.py` (40), `test_review_pr_cli.py` (25), `test_diff_normalizer.py` (20), `test_diff_source.py` (12) — mais 6 cenários novos em `tests/scm/test_gitlab_provider.py` e 11 em `tests/test_mcp_server.py`.

### **27. Resolução de Identidade do Revisor (`src/reviewer_resolution.py`) 🆕**

* **O Bug (duas falhas silenciosas encadeadas):** (1) **Prefill vazio** — `_reviewer_suggestion_view()` montava `handles` só com `provider.email_to_handle()`, que enxerga apenas e-mails `users.noreply.github.com` ou com e-mail **público**; com e-mail corporativo (o caso real: `eduardaleal@grafjb.com.br`) nada resolve, o `Input` nasce vazio e o hint mostra apenas o **nome**. (2) **Attach não verificado** — `_attach_reviewers()` repassava os valores do campo **verbatim**; o GitHub responde **201 sem anexar ninguém**, o `_request()` retorna sem levantar e a linha do log é escrita: sucesso aparente, revisor ausente, aviso nenhum.
* **Módulo Novo (159 linhas):** Plano, sem I/O próprio, **que nunca levanta**. `resolve_candidates()` (antes da TUI) e `resolve_typed_reviewers()` (no attach); `match_candidate()` casa **exato e normalizado** por login, nome ou e-mail.
* **Escada de Resolução:** handle já conhecido (sem requisição) → casamento exato com uma pessoa sugerida → lookup por e-mail (`email_to_handle`) → validação do login na forge (`get_user_login`).
* **O que não resolve nunca é enviado:** Sai em `ResolutionOutcome.dropped` como `(valor, motivo_i18n)` e é descartado com aviso visível, em vez de virar um `201` vazio.
* **Provider Duck-Typed:** O acesso é por `getattr`, então fakes e forges sem os métodos novos continuam funcionando — a suíte existente não precisou de reescrita.
* **Leitura de Volta no GitHub:** `request_pull_request_reviewers` lê `requested_reviewers` do corpo do `201` e devolve os logins **realmente** anexados; um lote rejeitado com `422` (o GitHub rejeita o lote inteiro quando um único login é inelegível) é repetido **um a um**, em vez de derrubar também os revisores válidos.
* **Utilidades Adjacentes:** `_identity_key` → `identity_key` (público), novo `normalize_identity()`, e `ReviewerCandidate` passou a carregar `last_commit_hash` para a agregação guardar o commit do toque mais recente.
* **Diagnóstico:** O log de uso da própria ferramenta foi a evidência de origem — ver §24.
* **Artefatos:** `docs/suggested-reviewers.*.md` re-sincronizado nos 5 idiomas, `ADR-002-reviewer-suggestion.md` e `glossary-reviewer-suggestion.md`, plano e survey do grill de 4 rodadas.
* **Testes:** `tests/test_reviewer_resolution.py` (18, **novo**) + ampliações em `test_github_provider.py` (68), `test_pr_publish_app.py` (45), `test_suggest_reviewers.py` (17), `test_reviewer_suggestion.py` (18) e `test_main_suggest_reviewers.py` (8).

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_blame_engine_ranges.py` | 7 | Blame por faixa de linhas em arquivo |
| `tests/test_blame_metrics.py` | 7 | Métricas de blame: profundidade, commits, duração |
| `tests/test_changelog_builder.py` | 15 | Builder do changelog: seções, headings traduzíveis, contribuidores |
| `tests/test_chat_backend.py` | 19 | Memória de chat, persistência, comandos slash |
| `tests/test_commit_classifier.py` | 23 | Classificação Conventional Commits (tipos, parser tolerante) |
| `tests/test_config_app.py` | 78 | TUI de configuração: montagem, troca de categoria, dirty tracking, F2 bloqueado, Ctrl+R, busca, segredos |
| `tests/test_config_cli.py` | 9 | Registro do subcomando `config`, `-h`, import lazy, stdout limpo |
| `tests/test_config_schema.py` | 42 | Cobertura de `DEFAULT_CONFIG`, sem duplicatas, categorias/kinds, `advanced` só em Avançado |
| `tests/test_config_store.py` | 22 | Round-trip no `.env` temporário, comentários e ordem preservados, `remove_config_value()` idempotente |
| `tests/test_config_suggest_reviewers.py` | 8 | Configuração de suggested reviewers (chaves e defaults) |
| `tests/test_config_validation.py` | 40 | Tipos, enums, templates, `validate_ai_key()` com SDK mockado (401 vs. rede vs. ollama) |
| `tests/test_core.py` | 49 | Fluxos principais, git diff, PR generation, timing, staging, coautoria, idioma dos hooks |
| `tests/test_diff_parser.py` | 26 | Parser de diff por linhas/hunks + `summarize_patch()` e `split_patch_sections()` 🆕 |
| `tests/test_external_linters.py` | 33 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_i18n.py` | 20 | Paridade entre idiomas (1048×6), chaves ausentes/órfãs, identidade |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação |
| `tests/test_issue_engine.py` | 4 | Draft de issue estruturado |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_linter_presets.py` | 5 | Presets de linter: resolução e re-download forçado |
| `tests/test_main_suggest_reviewers.py` | 8 | Flag `--no-suggest-reviewers` na CLI e no help contextual |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 104 🆕 | Ferramentas MCP (14), recursos (18), annotations, patching, CLI direto, offload |
| `tests/test_mcp_server_e2e.py` | 6 | Servidor MCP real via subprocess + JSON-RPC stdio |
| `tests/test_metrics.py` | 34 | Coleta, exportação local, escopo de repo, cache token summary |
| `tests/test_net_timeouts.py` | 12 | Timeouts de rede/IA — **2 asserções desatualizadas (600s)** |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_pr_publish_app.py` | 45 | TUI do PR Publisher: telas, fluxos, suggested reviewers, `NoticeScreen` |
| `tests/test_pr_publish_linter_modal.py` | 4 | Modal de erro do linter: abort, no-verify |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_release_cli.py` | 4 | CLI do release: options, help com epilog documentado |
| `tests/test_release_engine.py` | 27 | Engine de release: intervalo de commits, CHANGELOG, publicação |
| `tests/test_reviewer_resolution.py` | 18 🆕 | Escada de resolução, rejeição de nome parcial, dedup, tolerância a falha |
| `tests/test_reviewer_suggestion.py` | 18 | Lógica de sugestão de revisores (ranking, exclusão, top-N, `last_commit_hash`) |
| `tests/test_skill_command.py` | 10 | Download e validação de templates de skill |
| `tests/test_skill_context.py` | 14 | `get_skill_context()` com `quiet=True`, fallbacks, registro de skills |
| `tests/test_smart_excludes.py` | 15 | Filtro pathspec inteligente e re-download forçado |
| `tests/test_suggest_reviewers.py` | 17 | Suggested reviewers no fluxo de PR (integração, hint `no_login`) |
| `tests/test_thinking_words.py` | 5 | Carregamento, parsing com separador `;` e reload forçado |
| `tests/test_updater.py` | 23 | Gate do PyPI: parsing de versão, cache diário, fetch, decisões do portão, wiring no CLI |
| `tests/test_usage_log.py` | 27 | Log de uso: nome derivado da data, escrita síncrona, silêncio, `_repo_label()` multi-forge |
| `tests/test_version_bump.py` | 17 | Bump semântico: major/minor/patch, alvos e validação |
| `tests/fix/test_apply_fix.py` | 53 🆕 | Caso de uso completo: review → IA → validar → classificar → dry-run/apply |
| `tests/fix/test_chat_shared_extractor.py` | 8 🆕 | Extrator compartilhado entre chat e `fix` (comportamento idêntico) |
| `tests/fix/test_fix_cli.py` | 31 🆕 | Roteamento do subcomando, opções, dry-run default, `--force` |
| `tests/fix/test_fix_history.py` | 21 🆕 | Ledger `.gitpr/fix_history.json`: escrita atômica, leitura |
| `tests/fix/test_fix_settings.py` | 10 🆕 | As cinco `GITPR_FIX_*` e os fallbacks de valor inválido |
| `tests/fix/test_patch_applier.py` | 19 🆕 | Invólucro de `git apply`: check/apply/reverse, branch, status |
| `tests/fix/test_patch_extractor.py` | 13 🆕 | Blocos cercados → diff unificado validado |
| `tests/fix/test_patch_safety_classifier.py` | 22 🆕 | Matriz safe/review_required/experimental e códigos de motivo |
| `tests/fix/test_resolve_last_review.py` | 13 🆕 | Seleção do último review, exclusão de reviews por arquivo |
| `tests/fix/test_rollback_fix.py` | 14 🆕 | `--rollback`: reverse e as três recusas |
| `tests/review/test_diff_normalizer.py` | 20 🆕 | Newlines, validação de diff, smart-excludes em Python |
| `tests/review/test_diff_source.py` | 12 🆕 | `DiffOrigin`/`DiffSource`: proveniência, `cache_scope`, `is_remote` |
| `tests/review/test_remote_pr.py` | 40 🆕 | Orquestração: portões, PR, diff, linter, comentário opcional |
| `tests/review/test_review_pr_cli.py` | 25 🆕 | CLI `review-pr`: opções, rejeições antes da IA, `--post-comment` |
| `tests/scm/test_azure_devops_provider.py` | 43 | Provider Azure DevOps: org/projeto, PRs, `ScmNotSupportedError` |
| `tests/scm/test_bitbucket_provider.py` | 39 | Provider Bitbucket: Basic auth, workspace |
| `tests/scm/test_contract.py` | 38 | Contrato `ScmProvider`: assinaturas, dataclasses, erros |
| `tests/scm/test_factory.py` | 11 | `resolve_scm_provider()` + `detect_provider_from_remote()` |
| `tests/scm/test_github_api_shim.py` | 18 | Shim deprecado `github_api` → delega ao provider |
| `tests/scm/test_github_provider.py` | 68 🆕 | Provider GitHub: REST, headers, PRs, issues, releases, read-back de revisores |
| `tests/scm/test_gitlab_provider.py` | 47 🆕 | Provider GitLab: API v4, namespace, **cabeçalhos sintetizados e `overflow`** |
| `tests/scm/test_init_wizard.py` | 10 | Wizard `--init`: detecção da forge, validação, persistência |
| `tests/scm/test_release_publish.py` | 8 | Publicação de release por forge (GitHub/GitLab) |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (scaffold; nunca executado) |

**Total:** **1437 cenários coletados em 64 módulos de teste** (41 na raiz + 9 em `tests/scm/` + **10 em `tests/fix/`** 🆕 + **4 em `tests/review/`** 🆕; **+377** desde o relatório anterior, com **15 arquivos novos**). Execução completa nesta máquina com `GITPR_LANG=en_us`: **1432 passed / 3 failed / 2 skipped / 81 subtests** em ~347s.

**Notas de qualidade desta versão:**
- **Nenhuma falha nova.** As 3 falhas são exatamente as mesmas do relatório anterior — e as duas de timeout continuam herdadas de antes:
- **2 falhas reais (testes desatualizados, herdadas):** `test_net_timeouts.py::test_ai_timeout_defaults_to_600` e `::test_invalid_ai_timeout_falls_back_to_default` asserem o default de 600s para `GITPR_AI_TIMEOUT`, mas o código usa **180s** desde o fix `681a7fa`. É o mesmo item que já estava nos Próximos Passos de **dois** relatórios anteriores e **continua aberto**.
- **1 falha de locale (herdada, não é regressão):** `test_core.py::TestHooksLanguage::test_the_language_chosen_with_the_lang_flag_is_honoured` assere `i18n.CURRENT_LANG == "pt_br"` — passa com o locale pt-BR da máquina e falha com `GITPR_LANG=en_us`. Continua sendo o único teste sensível ao locale da suíte.
- **Crescimento de 377 cenários com a linha de base de falhas intacta** — o sinal relevante desta janela: as três features novas entraram sem derrubar nem mascarar nada.
- `tests/conftest.py` mantém `GITPR_SHOW_LOGS=false` e `GITPR_SKIP_UPDATE_CHECK=true` — a suíte não escreve no log de uso nem é bloqueada pelo portão de atualização.
- 🆕 **Fixtures de git real:** `tests/fix/git_fixture.py` monta repositórios git de verdade, em vez de mockar `subprocess` — o `patch_applier` só é honesto se o `git apply` for o de verdade.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** **1048 chaves** de tradução em cada um dos 6 dicionários (+93 desde o relatório anterior) com **paridade total de key sets**. A cadeia medida por commit foi 955 → 1022 (`fix`, +67) → 1028 (revisores, +6) → **1048** (`review-pr`, +20). `__lang_version__` subiu v0.0.25 → v0.0.26 → v0.0.27 → **v0.0.28**, disparando o re-download OTA das traduções.
* **Fontes de tradução em lockstep:** uma chave nova precisa existir no código (fonte), em `langs/pt_br.json` (**lista mestra**), nos dicts FR/ES de `scripts/sync_all_langs.py` (segunda fonte) e nos valores curados de `scripts/fix_mangled_i18n_keys.py` (terceira fonte, lida por `tests/test_i18n.py`); a asserção `len(CLEAN_KEYS)` segue em 49.
* **Tópicos novos 🆕 (2):**
  - `docs/fix-command.md` — achados de review como patches: pipeline, classificação de segurança, leitura antes de escrever, histórico e rollback, skill, MCP e variáveis — **em 5 idiomas**
  - `docs/review-pr.md` — review de PR remoto: o que é, quais forges podem ser revisadas, o relatório, publicação, skill, MCP e variáveis — **em EN + PT-BR** (os 3 idiomas restantes ficaram pendentes)
* **Tópicos atualizados nesta janela:** `docs/code-review-ia.*` (5 — modo remoto como §1.4 e a ressalva de que o linter externo não roda), `docs/suggested-reviewers.*` (5 — resolução de identidade), `docs/fix-command.*` (5 — §2.2 reescrita: o diff passou a vir do registro), `docs/commit-message-ia.*` (5), `docs/issue-tui-help.*` (5), `docs/linter-regras-customizadas.*` (5), `docs/providers-ia.*` (5) e `docs/skill-template.*` (5), além de `README.md`/`README.pt_br.md` (2×) e `CLAUDE.md` (tabela de comandos, tools MCP 13 → 14, árvore com `src/review/`).
* **Documentação em 5 idiomas:** **41 tópicos canônicos** em `docs/` — **35 com cobertura completa nos 5 idiomas** (+1 desde o relatório anterior) e **6 tópicos parciais/PT-only** (`como_reverter_commit_git_localmente`, `github-issue-prompt-com-gh`, `otimizacao-de-tokens`, `testar_sem_usar_pypi`, `version-markers` e, agora, `review-pr` com 2 idiomas).
* **Skills locais do Claude Code:** `.claude/skills/` com **29 skills** (contagem inalterada nesta janela).
* **Memory Index:** `.claude/memory/MEMORY.md` com 40 padrões (contagem inalterada nesta janela).
* **Relatórios de tarefas:** `docs/claude-code/reports/develop_natan/` (**93** no total; **+3** na janela — `gitpr fix`, resolução do login do revisor e review de PR remoto) e `docs/gemini/reports/develop_natan/` (5 arquivos; sem novas).
* **Relatórios de status:** `docs/reports/` (14 relatórios; este é o 15º).
* **Planos de desenvolvimento:** 99 arquivos em `docs/plans/` (+10 na janela — specs/planos do `fix` e do `review-pr`, correção da sugestão de revisores, ADR-004, ADR-005 e os glossários `glossary-gitpr-fix` e `glossary-review-pr`) + **6 arquivos em `docs/survey/`** (+3 na janela).

---

## **🔄 Pipeline de Distribuição**

1. **PyPI (canal único):** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **Atualização obrigatória:** a execução verifica o PyPI no startup e **bloqueia com exit code 1** se houver versão mais nova, imprimindo `pip install --upgrade gitpr-cli`; a checagem é cacheada por dia e o `--update` apenas reporta
3. **GitHub Releases:** removido — sem PyInstaller, sem asset `.exe`, sem hot-swap
4. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml` (instala via pip)
5. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`
6. **Templates e idiomas OTA:** `templates/` e `langs/*.json` servidos do GitHub (main) — o bump `v0.0.28` renova as cópias locais de `~/.gitpr/langs/` quando publicado
7. **Estado do release 1.2.0 🆕:** o `__version__` foi para 1.2.0 **no working tree** e ainda não foi commitado nem tagueado (HEAD em 1.1.0, última tag `v1.1.0`); o `CHANGELOG.md` ainda para em `[1.1.0] - 2026-09-13`. O caminho é rodar `gitpr release` e fazer o commit do bump.

---

## **📈 Evolução desde o Relatório Anterior (v0.0.14)**

| Área | v0.0.14 (anterior) | v0.0.15 (atual) |
|------|-------------------|-----------------|
| **Versão GitPR** | 1.1.0 | **1.2.0** (bump **não commitado**; HEAD em 1.1.0, última tag `v1.1.0`, CHANGELOG ainda em `[1.1.0]`) |
| **Versão Idioma** | v0.0.25 | **v0.0.28** (via v0.0.26 e v0.0.27) |
| **Versão Scripts Hook** | v0.0.3 | **v0.0.3** |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 idiomas, 6 dicionários | 5 idiomas, 6 dicionários |
| **Interface** | CLI + TUIs (Issues, Chat, Dashboard, PR Publisher, LinterApp, ConfigApp) + wizards `--init`/`--install` + `gitpr release`/`gitpr config` | **+ `gitpr fix` (patches revisáveis) + `gitpr review-pr` (review de PR remoto) + `NoticeScreen`** |
| **Ferramentas MCP** | 12 tools / 17 recursos / 7 prompts | **14 tools / 18 recursos / 7 prompts** (+`list_fix_candidates`, +`review_remote_pr`, +`skill://fix`) |
| **Flags CLI** | 35 opções na raiz + `release` (6) + `config` (0) | **35 na raiz** + `release` (6) + `config` (0) + **`fix` (8)** + **`review-pr` (2)** |
| **Variáveis de Ambiente** | 39 chaves no `DEFAULT_CONFIG` | **44 chaves** (+5 `GITPR_FIX_*`) |
| **Linter** | Regex + bridge Checkstyle (wizard/TUI/relatório) | Inalterado (+ **`skip_external`**: o review remoto não publica alertas da árvore local) |
| **Hooks Git** | Corrigidos: `HOOK_SCRIPT_SUFFIXES`, `SCRIPTS_LANG`, `effective_hook_lang()` | Inalterado |
| **Mensagens de Commit** | Com trailer `Co-Authored-By` (opt-out) | Inalterado |
| **Camada SCM** | 4 forges, `create_release`, `create_issue` | **+ `get_pull_request` (concreto na ABC) + `supports_reviewable_diff` + read-back de revisores (`list[str]`, quebra de contrato) + correções do GitLab** |
| **i18n (chaves por arquivo)** | 955 × 6 (paridade total) | **1048 × 6 (paridade total) — +93 chaves** |
| **Documentação** | 39 tópicos canônicos (34 completos + 5 parciais) | **41 tópicos canônicos (35 completos + 6 parciais) — 2 famílias novas, 8 atualizadas** |
| **Distribuição** | PyPI exclusivo | Inalterado (release 1.2.0 pendente) |
| **Suíte de Testes** | 1060 cenários (49 arquivos) | **1437 cenários (64 arquivos: 41 + 9 SCM + 10 fix + 4 review) — en_us: 1432 passed / 3 failed (2 desatualizados + 1 de locale) / 2 skipped** |
| **Commits desde o relatório** | 2 commits | **5 commits** (`f4d5186`, `f5bed07`, `b9dd930`, `eb55400`, `a8a7770`) |
| **PRs mergeados** | 2 PRs (#162, #164) | **3 PRs (#167, #171, #173)** |
| **Memory Index** | 40 padrões | **40 padrões** |
| **Relatórios de tarefas** | 90 claude-code, 5 gemini | **93 claude-code (+3 na janela) e 5 gemini** |
| **Planos de desenvolvimento** | 89 planos, 3 surveys | **99 planos (+10), 6 surveys (+3)** |
| **Higiene de repositório** | — | **+ `pypa/`/`pip/` removidos do rastreamento, `.gitignore` atualizado** 🆕 |

---

## **🚧 Próximos Passos**

* **Fechar o release 1.2.0 🆕:** o `__version__` está em 1.2.0 no working tree sem commit, sem tag e **sem entrada no `CHANGELOG.md`** (que para em `[1.1.0]`). Rodar `gitpr release`, commitar o bump e taguear — é o único item desta lista que bloqueia a publicação.
* **Traduzir o que ficou parcial 🆕:** `docs/review-pr.*.md` existe só em EN e PT-BR (faltam pt_pt, es_es, fr_fr) e `templates/gitpr.fix.md` só em EN e PT-BR — é a primeira vez em várias janelas que um tópico novo **não** nasce completo nos 5 idiomas.
* **Documentar a quebra de contrato do `request_pull_request_reviewers` 🆕:** passou de `None` para `list[str]`; subclasses de terceiros de `ScmProvider` precisam ser atualizadas. `docs/scm-multiforge.*.md` é o lugar, nas 5 versões.
* **`.gitpr/metrics/export/` no `.gitignore` 🆕:** o PR #171 commitou `gitpr_metrics_2026-09-17.csv`/`.json` — são artefatos gerados localmente, como os de agosto que já estão rastreados.
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Adicionar histogramas de tempo e gráficos de tendência de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação completa do build e do upload para o PyPI (a geração do changelog agora é local via `gitpr release`).
* **Seed de `.gitpr/conf/` local:** O seed de templates de configuração local (smart-excludes, linter) continua pendente como subcomando próprio ou etapa do wizard; a TUI de configuração oferece os **downloads** desses arquivos, mas não o seed do projeto.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.
* **Extrator de i18n do `sync_i18n.py`:** O regex trunca literais com concatenação implícita (`__("a " "b")`) — migrar para AST (o guard em `test_i18n.py` já usa AST e não depende do script).
* **Corrigir os testes de timeout desatualizados:** `tests/test_net_timeouts.py` assere 600s de default, mas o código usa 180s desde o fix `681a7fa`; alinhar também a docstring stale do `config.py`. **Item herdado, ainda aberto — já são três relatórios.**
* **Reconciliar a versão do projeto:** `CLAUDE.md` ainda diz `Current version: 0.0.37` enquanto o `__version__` está em 1.2.0 — a distância só aumentou (+0.0.37 vs. 1.1.0 no relatório anterior). Definir uma convenção única e atualizar o `CLAUDE.md`. **Item herdado, ainda aberto.**
* **Dívida do índice do README:** os bullets das famílias `suggested-reviewers`, `scm-multiforge`, `config-tui`, `usage-log` **e agora `fix-command` e `review-pr`** não estão no índice — a dívida cresceu nesta janela.
* **Robustez de locale nos testes:** 1 teste é sensível ao locale pt_br da máquina (`test_core.py::TestHooksLanguage`) — fixar `GITPR_LANG=en_us` no setup ou mockar `TRANSLATIONS` para a suíte ficar 100% verde em qualquer máquina/CI.
* **`gitpr -h config` ignora o `-h`:** o subcomando abre a TUI em vez de mostrar a ajuda — o gate `if ctx.invoked_subcommand is not None: return` roda antes do bloco de `help_flag`. Corrigir mudaria o comportamento de `-h` para **todos** os subcomandos, então precisa de decisão.
* **Seção Smart Exclude na TUI:** dos 12 itens reportados após o uso da tela, o item 10 (seção *Smart Exclude*) é a única entrega ainda não iniciada.
* **Dívidas registradas no plano do config TUI:** `DEFAULT_CONFIG` ficou redundante com o schema; o banner de abertura não lista `--dashboard`, `--init`, `--base` nem `--plugins`; o `LinterApp` não desabilita a command palette.

### ✅ Concluídos nesta janela (2026-09-13 → 2026-09-17)

* ~~**Subcomando `gitpr fix`**~~ — pacote `src/fix/` (8 arquivos, 1147 linhas), classificador determinístico `safe`/`review_required`/`experimental`, dry run por default, `.gitpr/fix_history.json` e `--rollback` (PR #167).
* ~~**`resolve_last_review()` + `reviewed_diff` no cache**~~ — o review que alimenta o `fix` passou a ser escolhido por repo+branch, excluindo reviews de escopo de arquivo.
* ~~**Resolução de identidade do revisor**~~ — `src/reviewer_resolution.py`, `request_pull_request_reviewers` devolvendo `list[str]`, read-back do `201`, retry individual no `422` e `NoticeScreen` (PR #171).
* ~~**Subcomando `gitpr review-pr`**~~ — pacote `src/review/` (5 arquivos, 560 linhas), read-only por default, `.txt` nomeado pela branch de origem, `--post-comment` como único caminho de escrita (PR #173).
* ~~**`ScmProvider.get_pull_request` + `supports_reviewable_diff`**~~ — método concreto na ABC implementado nas 4 forges; Azure barrado antes de qualquer chamada de rede.
* ~~**Correções latentes do GitLab**~~ — cabeçalhos `diff --git` sintetizados de `old_path`/`new_path` e `overflow: true` passando a levantar.
* ~~**`skip_external` no linter**~~ — o review remoto deixou de publicar alertas do bridge externo, que roda contra a árvore local.
* ~~**MCP: 12 → 14 tools e 17 → 18 recursos**~~ — `list_fix_candidates` + `skill://fix` e `review_remote_pr`.
* ~~**i18n: +93 chaves e cadeia v0.0.25 → v0.0.28**~~ — paridade total de key sets nos 6 dicionários.
* ~~**Higiene de repositório**~~ — árvore pip 25.2 vendorizada removida do rastreamento; `.gitignore` com `pypa/` e `pip/` (commit `f5bed07`).

---

**Relatório gerado em:** 2026-09-17  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
