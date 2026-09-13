# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.14 (2026-09-13)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.14):**
- **Subcomando `gitpr config` — TUI interativa de configuração:** Tela master-detail (Textual) sobre `~/.gitpr/.env` com menu lateral de categorias, campos editados inline, busca global (`/`), `F2` salvar, `Ctrl+R` restaurar e `Esc` com confirmação de descarte. Um **schema declarativo** (`src/config_schema.py` — 12 categorias, 56 `ConfigField`, 8 avançados) é a fonte única de verdade: o menu, os widgets, os defaults e a validação derivam todos dele, então adicionar uma configuração passou a ser mudança de **dado**, não de interface.
- **Seção Skills — a primeira superfície project-scoped da tela:** Painel master-detail inline que edita os arquivos `.gitpr/skill/*.md` do projeto (atomicamente, preservando CRLF/LF) na mesma passada de `F2` que grava o `.env`, com um contador único de pendências. O registro dos tipos suportados (`SKILL_FILES_BY_TYPE`) foi unificado em `src/config.py`, onde antes estava repetido em 6+ lugares.
- **Log geral de uso (`src/usage_log.py`):** Uma linha por comando em `~/.gitpr/logs/<uuid5-da-data>.log` — **um arquivo por dia** — escrita síncrona, nunca imprime e nunca levanta exceção. Chamado só em dois pontos (callback raiz do `cli()` e `main()` do servidor MCP), que juntos alcançam todas as flags, os dois subcomandos e todo caminho de `ctx.exit()`. Controlado por `GITPR_SHOW_LOGS` (nasce ligado em toda instalação existente).
- **Correção de idioma dos hooks:** O idioma escolhido pelo usuário passou a valer de verdade — `HOOK_SCRIPT_SUFFIXES` mapeia códigos de interface (`es_es`, `fr_fr`) para os sufixos publicados (`.es`, `.fr`), `SCRIPTS_LANG` (escolha do usuário) foi separado de `SCRIPTS_INSTALLED_LANG` (estado em disco) para a auto-sincronização detectar troca de idioma, e `--lang` deixou de ser ignorado.
- **Distribuição exclusiva via PyPI com portão de atualização obrigatória:** O canal binário foi extinto — sem geração, sem upload, sem fallback. `src/updater.py` foi reescrito em torno de uma única fonte de verdade (a API do PyPI): `enforce_update_required()` bloqueia a execução com **exit code 1** quando existe versão mais nova publicada, imprimindo `pip install --upgrade gitpr-cli`. Saíram a consulta à API de Releases do GitHub, a resolução de asset, o hot-swap com rollback e a dependência `pyinstaller`.
- **Log de uso, telemetria e dogfooding:** O próprio GitPR gerou as release notes desta janela (`gitpr release` em `.gitpr/reports/release/`), usou o log de uso para reconstruir a atividade e as skills locais `.gitpr.release.md` / `.gitpr.filereview.md` como system instructions.
- **i18n expandida para 955 chaves:** +213 chaves desde o relatório anterior, cobrindo as superfícies da TUI de configuração e do gate do PyPI; `__lang_version__` subiu de v0.0.23 para **v0.0.25** (cadeia v0.0.23 → v0.0.24 → v0.0.25) e os 6 dicionários mantêm **paridade total de key sets**.
- **Documentação Multilíngue Expandida:** 2 famílias novas completas em 5 idiomas — `config-tui` e `usage-log` — e 7 tópicos atualizados (`ARCHITECTURE`, `auto-update`, `hooks-versioning`, `mcp-integration`, `skill-template`, `testar_sem_usar_pypi`, `version-markers`).
- **Remoção de chave morta `PR_AUTO_PUBLISH`:** Provada inexistente em `src/` (zero ocorrências) e removida da lista de env vars do `CLAUDE.md` e do `.env` do usuário; a §5 da doc da TUI foi corrigida nas 5 versões, porque prometia "fora da tela" para chaves que na verdade aparecem read-only em *Desconhecidas*.
- **Salto de versão:** `__version__` foi de 1.0.0 para **1.1.0**; o `CHANGELOG.md` registra `[1.1.0] - 2026-09-13`, gerado pela própria feature de release.

- **Versão atual:** 1.1.0
- **Versão dos dicionários de idioma:** v0.0.25
- **Versão dos scripts de hook:** v0.0.3
- **Publicação:** PyPI (`pip install gitpr-cli`) — **canal binário removido nesta janela**
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal).
* **UI/Terminal:** Textual — TUI para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher, erros do linter (`LinterApp`) e **configuração (`ConfigApp`)** 🆕.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API, tokens GitHub e tokens SCM das forges — os segredos editados na TUI de configuração também são cifrados antes de gravar.
* **Configuração:** `python-dotenv`, `pyyaml` (para o linter estático) + **schema declarativo próprio (`src/config_schema.py`)** 🆕.
* **IA Providers:** Integração via SDK oficial do Google GenAI (`gemini-2.5-flash`), OpenAI SDK (`DeepSeek`), e OpenAI SDK (`Ollama` local).
* **Forge APIs:** `requests` (REST) — camada de abstração multi-forge em `src/infrastructure/scm/` (GitHub, GitLab, Bitbucket, Azure DevOps); módulo legado `src/github_api.py` mantido como shim deprecado.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — 12 ferramentas anotadas, 17 recursos, 7 prompts; handlers offloaded para threads via `anyio`.
* **Testes:** Pytest + `unittest.mock` (49 arquivos de teste — 40 na raiz + 9 em `tests/scm/` —, 1060 cenários coletados) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio).
* **Empacotamento:** setuptools/build (PyPI). **PyInstaller saiu do projeto nesta janela** — não há mais binário standalone.
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
* **Smart Excludes com Duas Camadas:** Filtro de pathspec inteligente com camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`). Mesclagem em runtime (união, deduplicada). Auto-seeding do arquivo local na primeira execução. 🆕 `_load_smart_excludes()` aceita `force=` para re-download sob demanda a partir da TUI de configuração.
* **Métricas com Rastreamento de Tempo:** Injeção de `log_command_metric()` em todos os fluxos com repasse da duração em milissegundos (`duration_ms`) e lazy imports.
* **Resolução Centralizada de Output:** Função `resolve_output_path()` que centraliza a lógica de diretórios de saída — default em `.gitpr/reports/{type}/`.
* **Wizard SCM (`run_scm_init_wizard()`)**: `gitpr --init` — detecta a forge pelo remote origin, solicita extras por forge (org/projeto Azure, usuário Bitbucket), valida o token com `test_connection` (3 tentativas, 401 re-prompt) e persiste `GITPR_SCM_PROVIDER` + `GITPR_SCM_TOKEN_ENCRYPTED` (Fernet) **somente em sucesso**.
* **Skill Template de Release (`ensure_release_skill_template()`)**: Baixa `templates/gitpr.release.*.md` no primeiro uso de `gitpr release` (CLI layer, idioma-aware, nunca sobrescreve; pulado em `--format json`).
* **Registro de Skills Compartilhado 🆕:** `SKILL_FILES_BY_TYPE` / `SKILL_TYPES` / `DEFAULT_SKILL_TYPE` saíram de `core.py` para `src/config.py` (a TUI não pode importar `core` no topo — puxa os SDKs de IA); `get_skill_context()` passou a usar `skill_file_for()`.
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
* **Routing de Comandos:** Gerencia todas as flags e os **2 subcomandos** — `release` e `config` 🆕.
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
* **Subcomando `config` 🆕:** 0 opções — abre a TUI de configuração. Deliberadamente **não** chama `setup_environment()`, para não haver `click.prompt` disputando o terminal com a TUI. Import lazy; epilog com `get_doc_url("config-tui.md")`.
* **Portão de Atualização Obrigatória 🆕:** No início do callback `cli()`, **depois** do handler de `--lang` (para a mensagem sair no idioma pedido) e **antes** do despacho de flags (porque `--linter` retorna antes do `check_internet_connection()`) — sem isso, a maioria dos comandos ficaria sem guarda. Pula `--quiet`, `--hook`, `--mcp`, `--update` e `-h/--help`; `--help`/`--version` são opções *eager* do Click e nem chegam ao corpo.
* **Log de Uso 🆕:** `log_usage()` no topo do callback, antes do `if ctx.invoked_subcommand is not None: return` — as 35 flags, os 2 subcomandos e os `ctx.exit()` do `-h` passam todos por ali.
* **Variáveis de Ambiente (39 chaves no `DEFAULT_CONFIG`, inalterado):** `GITPR_SKIP_UPDATE_CHECK` 🆕 (qualquer valor não-vazio desliga o portão; usada pela suíte de testes) e `GITPR_SHOW_LOGS` (declarada, semeada como `"true"` e desligada em `tests/conftest.py`) — esta última saiu da sombra e ganhou campo próprio na categoria Geral da TUI.
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub. Subcomandos têm `epilog=` próprio (parágrafo `\b` do Click para a URL não ser reembrulhada sob nenhum locale).
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração — 🆕 e passou a valer também para a resolução dos scripts de hook.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **12 ferramentas anotadas + 17 recursos + 7 prompts**.
* **--install:** Assistente guiado de 4 etapas que baixa templates de skill, instala Git Hooks, configura MCP nos editores e valida chaves de API.
* **--metrics:** Sistema de telemetria local com escopo por repositório: `--export`, `--purge`, `--dashboard`.
* **--status:** Lista arquivos não commitados categorizados (new/modified/deleted) — rápido, sem IA, sem rede.
* **Camada de escrita do `.env` 🆕:** `read_env_file_values()` lê **só o arquivo** via `dotenv_values` (imune a `os.environ`), `save_config_values()` grava com `set_key`, `remove_config_value()` com `unset_key` — os 9 call-sites de `set_key` pré-existentes ficaram intactos. `validate_ai_key()` sonda os SDKs Gemini/DeepSeek com timeouts curtos e distingue credencial recusada (`401`/`403`) de rede inalcançável.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI construída com Textual para revisar, editar e publicar Pull Requests diretamente no terminal.
* **6 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen`.
* **Suggested Reviewers:** O fluxo de publicação consulta a forge por revisores sugeridos e os oferece na TUI; seleção controlada por `--no-suggest-reviewers`, `GITPR_SUGGEST_REVIEWERS`, `GITPR_REVIEWER_SUGGESTION_TOP_N` e `GITPR_REVIEWER_SUGGESTION_EXCLUDED`.
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
* **Relatório Consolidado:** `generate_linter_report_content()` consolida erros regex + externos em `.gitpr/reports/linter/` — gerado apenas quando há violações.
* 🆕 `load_linter_presets()` aceita `force=` para re-download dos presets a partir da TUI.

### **7. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data` e `decrypt_data` para proteger chaves de API de IA, GitHub PAT e tokens SCM das forges (`GITPR_SCM_TOKEN_ENCRYPTED`).
* **Validação Multi-Forge:** `validate_or_request_scm_token(provider, repo_display)` — valida o token na forge configurada com 401 → loop de reautenticação preservando o rascunho; o token GitHub legado (`GITHUB_TOKEN_ENCRYPTED`) permanece funcional até o `--init` rodar.
* **Segredos na TUI de Configuração 🆕:** Campos `KIND_SECRET` são editados em campo mascarado, **nunca** exibem o valor em claro e são cifrados com Fernet antes de gravar — nenhum caminho lê o segredo de volta para a tela. `GITPR_SCM_TOKEN` é `read_only` e sua descrição aponta `gitpr --init` como o único caminho que deve escrevê-lo.

### **8. Auto-Updater (`src/updater.py`) — reescrito nesta janela 🆕**

* **PyPI como Fonte Única:** `get_latest_remote_version()` consulta sempre `https://pypi.org/pypi/gitpr-cli/json`, devolve **string** de versão e grava o cache diário **sem** o campo `download_url`. Perdeu o parâmetro `is_compiled` e todo o ramo da API de Releases do GitHub.
* **Portão Obrigatório (`enforce_update_required()`):** Devolve `True` (depois de imprimir as duas versões e o comando pip) quando a versão publicada é mais nova; devolve `False` quando está atualizado, quando a versão remota é **desconhecida (offline — o usuário não teria como atualizar)** ou quando a checagem está desligada. Devolver `bool` em vez de chamar `sys.exit` internamente mantém a função testável.
* **`check_and_update()`:** Reescrito para o `--update` — só consulta e **informa**, nunca instala.
* **Removidos:** `GITHUB_API_URL`, `_perform_hot_swap()` (renomeava o `.exe` para `.old`, baixava o novo, fazia rollback), `print_update_notice()` e seus 5 call-sites, o bloco de limpeza `.old` do `main.py` e a dependência `pyinstaller` do `Pipfile`. O `icon.ico` foi deletado.
* **Escape Hatch:** `GITPR_SKIP_UPDATE_CHECK` (qualquer valor não-vazio) — não é advertised como recurso ao usuário; existe para a suíte de testes e automação offline.
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Versionamento Centralizado:** `__version__` (**1.1.0**), `__lang_version__` (**v0.0.25**), `__scripts_version__` (**v0.0.3**), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`.
* **Defeitos que a mudança encerra:** o `urlretrieve` antigo não tinha timeout nem checksum, e o `main.py` apagava o backup `.old` na execução seguinte sem condição — um download truncado era irrecuperável.

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Construída com Textual — histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico de conversa persistido por branch, permitindo continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear` — atalhos para pair programming.
* **Auto-Patching (F5), Atualização de Diff (F2), Exportação de Sessão (F6).**

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com suporte a placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas, 6 Dicionários:** en_us (padrão/fallback), pt_br, pt_pt, es/es_es, fr/fr_fr.
* **Arquivos Versionados:** `__lang_version__` (**v0.0.25**) controla atualização dos pacotes de idioma (`langs/*.json`) — cadeia de bumps v0.0.23 → v0.0.24 → v0.0.25 nesta janela.
* **Cobertura:** **955 chaves** de tradução em cada um dos 6 arquivos — **paridade total de key sets** (+213 desde o relatório anterior).
* **Snapshot de Ambiente (`AMBIENT_ENV_KEYS`) 🆕:** `frozenset(os.environ)` capturado em `i18n.py` **imediatamente antes** do `load_dotenv()` de nível de módulo. Era a raiz de um defeito silencioso da TUI: como `config.py` importa de `i18n.py`, o `.env` inteiro já estava dentro de `os.environ` antes de a tela existir, então o badge "⚠ no ambiente" confirmava tautologicamente que a chave está no arquivo. Medido: **0 campos com badge** num processo limpo, **40 de 49** depois de importar a tela. Corrigido nos três pontos de uso.
* **Chaves Renomeadas/Removidas 🆕:** `Detected language: {lang}` → `Hooks language: {lang}`; 6 chaves obsoletas de update/binário removidas e 3 novas do gate do PyPI adicionadas.
* **Cache com Indexação por Idioma:** Respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas. 🆕 `_load_thinking_words()` / `reload_thinking_words()` aceitam `force=`.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Modo JSON & Parâmetros Determinísticos:** Outputs estruturados com `temperature=0.0` e `top_p=0.1`; fallback automático entre provedores configurados.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt, com indexação por idioma.
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

* **12 Ferramentas MCP Anotadas:** `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`.
* **17 Recursos + 7 Prompts Templatizados:** `skill://list` + `skill://{pr,commit,review,filereview,issue,blame,release}` + `linter://config` + `prompt://list` + 7 prompts.
* **Invocação CLI Direta:** Comando `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool MCP diretamente sem iniciar o servidor stdio JSON-RPC. `gitpr-mcp --list` imprime o registry completo como JSON.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve diretamente no `sys.__stdout__` original, garantindo JSON puro no stdout — razão pela qual o log de uso **nunca** imprime.
* **Offload do Event Loop:** Decorator `_offload` (`anyio.to_thread.run_sync`) aplicado às 12 tools — handlers síncronos não congelam o servidor stdio.
* **Log de Uso 🆕:** `main()` do servidor chama `log_usage()` — o console script `gitpr-mcp` nunca carrega `main.py`, então este é o único ponto que o alcança.
* **Testes E2E:** `tests/test_mcp_server_e2e.py` sobe o servidor real como subprocess e fala JSON-RPC stdio.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório (Repo-Scope):** Rótulo `📁 Repository: owner/repo` e filtragem estrita por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com widget `ProgressBar`.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de cache ao totalizador.
* **Exportação Local:** Salvamento de CSV/JSON em `./.gitpr/metrics/export/` (artefatos de 2026-09-12 e 2026-09-13 versionados nesta janela).

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`.
* **Eventos de Hook, Linter e Blame:** `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()`.
* **Exportação e Limpeza:** `--metrics --export` (CSV/JSON) e `--metrics --purge` com confirmação interativa.

### **19. Sincronização de Idiomas dos Hooks Git — corrigida nesta janela 🆕**

* **Versionamento Independente:** `__scripts_version__` (v0.0.3) controla a versão dos scripts de hook; detecção automática e atualização.
* **Mapeamento de Sufixos (`HOOK_SCRIPT_SUFFIXES`) 🆕:** Códigos de interface (`es_es`, `fr_fr`) passaram a ser traduzidos para os sufixos realmente publicados (`.es`, `.fr`) — antes o idioma escolhido pelo usuário era simplesmente ignorado.
* **Escolha vs. Estado (`SCRIPTS_LANG` / `SCRIPTS_INSTALLED_LANG`) 🆕:** `SCRIPTS_LANG` é a escolha do usuário; `SCRIPTS_INSTALLED_LANG` é o que está em disco. Separados, a auto-sincronização consegue **detectar a troca de idioma** em vez de assumir que já está instalado.
* **`effective_hook_lang()` 🆕:** Resolve o idioma efetivo dos hooks; `--lang` deixou de ser descartado nesse caminho (mudança de comportamento documentada).
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
* **Fail-Fast por Forge:** Azure DevOps exige `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`; Bitbucket exige `GITPR_SCM_USERNAME` (App Password = Basic auth user+token); `create_issue` no Azure levanta `ScmNotSupportedError`.
* **Publicação de Releases:** `provider.create_release()` usado pelo `gitpr release --publish` (GitHub cria a tag no branch default; GitLab exige a tag existente).
* **Artefatos:** Glossário + ADR-001 em `docs/plans/`; família `docs/scm-multiforge.*.md` em 5 idiomas; testes: 9 arquivos, 265 cenários.

### **22. Subcomando `gitpr release` — Changelog / Release Notes**

* **Fluxo:** `git log` entre `--since` (default: última tag alcançável, ou o primeiro commit) e `HEAD` → classificação por Conventional Commits → bump semântico sugerido (`--version <x.y.z>` sobrescreve) → montagem do changelog → resumo executivo de IA opcional → *prepend* no `CHANGELOG.md`. Geração local é o default — nada é publicado nem tocado sem pedido.
* **Classificador (`src/commit_classifier.py`):** Classifica os commits por tipo Conventional Commits (feat/fix/refactor/docs/chore/etc.) com parser tolerante.
* **Builder com Seções Traduzíveis (`src/changelog_builder.py`):** Seções "✨ Features", "🐛 Bug Fixes", "⚠️ Breaking Changes", "Summary", "Contributors" etc. renderizadas via `__()` em runtime (seguem o `--lang`).
* **Bump Semântico (`src/version_bump.py`):** Sugere a próxima versão a partir dos tipos classificados (major para breaking, minor para feat, patch para fix) e valida alvos `x.y.z`.
* **Publicação:** `--publish` cria a release na forge configurada (com confirmação explícita); `--draft` cria como rascunho (GitHub; GitLab não tem conceito de draft); `--format markdown|json` para saída estruturada; `--force` para regravação. **6 opções no subcomando.**
* **Skill Template:** No primeiro uso baixa `templates/gitpr.release.*.md` (5 idiomas) via `ensure_release_skill_template()` — nunca sobrescreve.
* **Dogfooding nesta janela:** `.gitpr/reports/release/` recebeu as release notes geradas pelo próprio comando (`develop_natan_20260910144814`, `...145040`, `...145125`) e `.gitpr/skill/.gitpr.release.md` + `.gitpr.filereview.md` passaram a existir como skills locais do projeto.
* **Artefatos:** Família `docs/release-notes.*.md` (5 idiomas), spec em `docs/plans/`, ADR-002 e ADR-003, glossário de release notes.

### **23. Subcomando `gitpr config` — TUI de Configuração 🆕**

* **Tela Master-Detail (`src/ui/config_app.py`):** Categorias à esquerda, campos da categoria à direita, editados inline. Cabeçalho com busca (`/`) e contador de pendências (`● N não salvas`); rodapé com `F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc`. `Geral` é sempre a primeira entrada do menu.
* **Schema Declarativo (`src/config_schema.py`) — a fonte única de verdade:** 12 categorias (Geral, Provedores de IA, Pull Request, Revisão de Código, Issue, Blame, Linter, Release, SCM / Forge, Filtros de Diff, Skills, Avançado) e **56 `ConfigField`**, dos quais **8 avançados**. Cada campo declara categoria, tipo de widget (`bool`/`int`/`str`/`enum`/`template`/`path`/`secret`/`version`/`words`), `show_if`, validadores, marcadores de versão e ações de download. Rótulos são literais `__()` para o scanner de i18n.
* **Filtragem por Contexto (`show_if`):** `GEMINI_*` / `DEEPSEEK_*` / `OLLAMA_*` aparecem conforme o `DEFAULT_AI_PROVIDER` selecionado (nenhum selecionado → nenhum bloco); `GITHUB_TOKEN_ENCRYPTED` aparece com provider vazio ou `github`; `GITPR_SCM_USERNAME` sob `[Bitbucket]`; `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT` sob `[Azure DevOps]`. Trocar o `Select` re-filtra o painel **na hora, sem F2** (só `on_select_changed` dispara `_render_view()`, e só para chaves em `VISIBILITY_CONTROLLERS`, derivado do schema e não escrito à mão).
* **Busca Global (`/`):** Casa chave ou rótulo em todas as categorias e **ignora o filtro de visibilidade** — procurar `deepseek` com o Gemini selecionado acha os campos, para permitir pré-preenchê-los. Campo sujo é salvo independente de visibilidade (`_build_plan` é cego a visibilidade, por projeto).
* **Validação em Duas Camadas:** **Offline** (tipo, enum, template com placeholder conhecido e `{datetime}` obrigatório) bloqueia o `F2` com erro inline; **online** (só para credenciais alteradas na sessão) roda em worker com timeout de 10s e só bloqueia em `401`/`403` — falha de rede permite gravar.
* **Restaurar (`Ctrl+R`):** Remove a linha do `.env` em vez de reescrever o default; **`Esc`** com alterações pendentes pede confirmação; categoria **Desconhecidas** preserva chaves fora do schema em modo leitura (não oferece remoção, por projeto).
* **Seção Skills — a única project-scoped 🆕:** Painel master-detail inline (lista das skills à esquerda, editor de texto à direita) que edita `.gitpr/skill/*.md` do projeto resolvidos a partir do diretório de chamada, gravando atomicamente e preservando CRLF/LF. `F2` grava o `.env` e os arquivos de skill **na mesma passada**, com um contador de pendências só.
* **Downloads com Força:** Botões que forçam re-download de smart-excludes, traduções, presets de linter e thinking words, via parâmetro `force=` encadeado nos loaders.
* **Módulo de Links Leve (`src/doc_links.py`) 🆕:** `doc_url()` saiu de `core.py` para que a UI obtenha o link da documentação sem importar `core`/SDKs de IA. Cada categoria do schema aponta para o seu doc canônico.
* **Testes:** 5 arquivos novos — `test_config_app.py` (78), `test_config_schema.py` (42), `test_config_validation.py` (40), `test_config_store.py` (22), `test_config_cli.py` (9).
* **Artefatos:** `docs/config-tui.*.md` em 5 idiomas, plano `docs/plans/20260912_config_tui.md`, glossário `glossary-config-tui.md` (8 termos) e survey do grill.
* **Dívida conhecida:** `gitpr -h config` abre a TUI e ignora o `-h` — o gate `if ctx.invoked_subcommand is not None: return` roda antes do bloco de `help_flag`; corrigir mudaria o comportamento de `-h` para **todos** os subcomandos (documentado em `docs/config-tui.md`).

### **24. Log Geral de Uso (`src/usage_log.py`) 🆕**

* **Uma Linha por Comando:** Grava `~/.gitpr/logs/<uuid5>.log`, **um arquivo por dia**, com o comando, argumentos, repositório, usuário e timestamp. Serve para responder "o que eu realmente rodei, e quando?".
* **Nome Derivado da Data:** `uuid5(NAMESPACE_DNS, f"gitpr.usage.{YYYY-MM-DD}")` em vez de aleatório — um nome aleatório exigiria contador ou arquivo de estado para saber qual arquivo é o de hoje, e dois processos concorrentes poderiam discordar. Derivado da data, o mesmo dia sempre resolve para o mesmo nome e comandos concorrentes apenas anexam ao mesmo arquivo.
* **Escrita Síncrona (decisão explícita):** Diferente de `log_local_metric`, que usa thread daemon e por isso perde a gravação se o processo sair antes — inaceitável para um log que promete registrar *todo* comando.
* **Nunca Imprime:** O servidor MCP reserva o stdout para JSON-RPC; um `print` acidental corromperia o protocolo. O módulo também nunca levanta exceção.
* **Um Único Spawn de Git:** `git config --get-regexp '^(remote\.origin\.url|user\.name|user\.email)$'` em vez dos três idiomáticos — ~40 ms em vez de ~150 ms no Windows, em *toda* execução.
* **`_repo_label()` Própria:** Sem reusar `get_repo_name()` de `core.py` (regex fixa em `github.com`, devolveria `unknown/repo` em GitLab/Bitbucket/Azure — defeito novo num projeto que acabou de ganhar multi-forge) e sem `parse_repo_ref`, que é método de provider e exigiria construir um provider (token, `requests`) a cada comando.
* **Controle:** `GITPR_SHOW_LOGS` (default `"true"` — nasce ligado em toda instalação existente, sem migração); desligado em `tests/conftest.py`.
* **Artefatos:** `docs/usage-log.*.md` em 5 idiomas; `tests/test_usage_log.py` (27 cenários).

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_blame_engine_ranges.py` | 7 | Blame por faixa de linhas em arquivo |
| `tests/test_blame_metrics.py` | 7 | Métricas de blame: profundidade, commits, duração |
| `tests/test_changelog_builder.py` | 15 | Builder do changelog: seções, headings traduzíveis, contribuidores |
| `tests/test_chat_backend.py` | 19 | Memória de chat, persistência, comandos slash |
| `tests/test_commit_classifier.py` | 23 | Classificação Conventional Commits (tipos, parser tolerante) |
| `tests/test_config_app.py` | 78 🆕 | TUI de configuração: montagem, troca de categoria, dirty tracking, F2 bloqueado, Ctrl+R, busca, segredos |
| `tests/test_config_cli.py` | 9 🆕 | Registro do subcomando `config`, `-h`, import lazy, stdout limpo |
| `tests/test_config_schema.py` | 42 🆕 | Cobertura de `DEFAULT_CONFIG`, sem duplicatas, categorias/kinds, `advanced` só em Avançado |
| `tests/test_config_store.py` | 22 🆕 | Round-trip no `.env` temporário, comentários e ordem preservados, `remove_config_value()` idempotente |
| `tests/test_config_suggest_reviewers.py` | 8 | Configuração de suggested reviewers (chaves e defaults) |
| `tests/test_config_validation.py` | 40 🆕 | Tipos, enums, templates, `validate_ai_key()` com SDK mockado (401 vs. rede vs. ollama) |
| `tests/test_core.py` | 49 | Fluxos principais, git diff, PR generation, timing, staging, coautoria, idioma dos hooks |
| `tests/test_diff_parser.py` | 15 | Parser de diff por linhas/hunks |
| `tests/test_external_linters.py` | 33 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_i18n.py` | 20 | Paridade entre idiomas (955×6), chaves ausentes/órfãs, identidade |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação |
| `tests/test_issue_engine.py` | 4 | Draft de issue estruturado |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_linter_presets.py` | 5 🆕 | Presets de linter: resolução e re-download forçado |
| `tests/test_main_suggest_reviewers.py` | 6 | Flag `--no-suggest-reviewers` na CLI e no help contextual |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 86 | Ferramentas MCP, recursos, annotations, patching, CLI direto, offload |
| `tests/test_mcp_server_e2e.py` | 6 | Servidor MCP real via subprocess + JSON-RPC stdio |
| `tests/test_metrics.py` | 34 | Coleta, exportação local, escopo de repo, cache token summary |
| `tests/test_net_timeouts.py` | 12 | Timeouts de rede/IA — **2 asserções desatualizadas (600s)** |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_pr_publish_app.py` | 42 | TUI do PR Publisher: telas, fluxos, suggested reviewers |
| `tests/test_pr_publish_linter_modal.py` | 4 | Modal de erro do linter: abort, no-verify |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_release_cli.py` | 4 | CLI do release: options, help com epilog documentado |
| `tests/test_release_engine.py` | 27 | Engine de release: intervalo de commits, CHANGELOG, publicação |
| `tests/test_reviewer_suggestion.py` | 15 | Lógica de sugestão de revisores (ranking, exclusão, top-N) |
| `tests/test_skill_command.py` | 10 | Download e validação de templates de skill |
| `tests/test_skill_context.py` | 14 | `get_skill_context()` com `quiet=True`, fallbacks, registro de skills |
| `tests/test_smart_excludes.py` | 15 | Filtro pathspec inteligente e re-download forçado |
| `tests/test_suggest_reviewers.py` | 14 | Suggested reviewers no fluxo de PR (integração) |
| `tests/test_thinking_words.py` | 5 | Carregamento, parsing com separador `;` e reload forçado |
| `tests/test_updater.py` | 23 🆕 | Gate do PyPI: parsing de versão, cache diário, fetch, decisões do portão, wiring no CLI |
| `tests/test_usage_log.py` | 27 🆕 | Log de uso: nome derivado da data, escrita síncrona, silêncio, `_repo_label()` multi-forge |
| `tests/test_version_bump.py` | 17 | Bump semântico: major/minor/patch, alvos e validação |
| `tests/scm/test_contract.py` | 38 | Contrato `ScmProvider`: assinaturas, dataclasses, erros |
| `tests/scm/test_github_provider.py` | 57 | Provider GitHub: REST, headers, PRs, issues, releases |
| `tests/scm/test_gitlab_provider.py` | 41 | Provider GitLab: API v4, namespace, releases |
| `tests/scm/test_bitbucket_provider.py` | 39 | Provider Bitbucket: Basic auth, workspace |
| `tests/scm/test_azure_devops_provider.py` | 43 | Provider Azure DevOps: org/projeto, PRs, `ScmNotSupportedError` |
| `tests/scm/test_factory.py` | 11 | `resolve_scm_provider()` + `detect_provider_from_remote()` |
| `tests/scm/test_github_api_shim.py` | 18 | Shim deprecado `github_api` → delega ao provider |
| `tests/scm/test_init_wizard.py` | 10 | Wizard `--init`: detecção da forge, validação, persistência |
| `tests/scm/test_release_publish.py` | 8 | Publicação de release por forge (GitHub/GitLab) |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (scaffold; nunca executado) |

**Total:** 1060 cenários coletados em 49 arquivos de teste (40 na raiz + 9 em `tests/scm/`; **+269** desde o relatório anterior, com **8 arquivos novos**). Execução completa nesta máquina com `GITPR_LANG=en_us`: **1055 passed / 3 failed / 2 skipped / 33 subtests** em ~123s.

**Notas de qualidade desta versão:**
- **2 falhas reais (testes desatualizados, herdadas):** `test_net_timeouts.py` ainda assere o default de 600s para `GITPR_AI_TIMEOUT`, mas o código usa **180s** desde o fix `681a7fa`. É o mesmo item que já estava nos Próximos Passos do relatório anterior e **continua aberto**.
- **1 falha de locale (nova, não é regressão):** `test_core.py::TestHooksLanguage::test_the_language_chosen_with_the_lang_flag_is_honoured` assere `i18n.CURRENT_LANG == "pt_br"` — passa com o locale pt-BR da máquina e falha com `GITPR_LANG=en_us`. É a suíte de idioma dos hooks introduzida nesta janela.
- **Sensibilidade de locale reduziu de 4 para 1:** as 4 falhas ambientais da janela anterior (`test_chat_backend::test_api_exception`, `test_main_suggest_reviewers::test_flag_appears_in_contextual_help` e `test_suggest_reviewers` ×2) **passam** agora com `GITPR_LANG=en_us` — deixaram de ser o problema, mas a causa raiz (testes que assumem idioma) persiste, apenas migrou de arquivo.
- `tests/conftest.py` passou a fixar `GITPR_SHOW_LOGS=false` e `GITPR_SKIP_UPDATE_CHECK=true` — a suíte não escreve no log de uso nem é bloqueada pelo portão de atualização.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** **955 chaves** de tradução em cada um dos 6 dicionários (+213 desde o relatório anterior) com **paridade total de key sets**. As ~200 chaves novas cobrem as superfícies da TUI de configuração e do gate do PyPI; 6 chaves obsoletas de update/binário foram removidas, 3 novas adicionadas e 2 de ajuda reescritas. `__lang_version__` subiu v0.0.23 → v0.0.24 → **v0.0.25**, disparando o re-download OTA das traduções.
* **Fontes de tradução em lockstep:** uma chave nova precisa existir no código (fonte), em `langs/pt_br.json` (**lista mestra**), nos dicts FR/ES de `scripts/sync_all_langs.py` (segunda fonte) e nos valores curados de `scripts/fix_mangled_i18n_keys.py` (terceira fonte, lida por `tests/test_i18n.py`); a asserção `len(CLEAN_KEYS)` foi de 50 para **49**.
* **Tópicos novos 🆕 (2, ambos em 5 idiomas):**
  - `docs/config-tui.md` — tela `gitpr config`: layout, leitura de valores, edição/save, validação em duas camadas, busca, fora de escopo e seção para desenvolvedores
  - `docs/usage-log.md` — log de uso: onde os arquivos vivem, o nome derivado da data, o formato da linha e o que ele não faz
* **Tópicos atualizados nesta janela (todos re-sincronizados nos 5 idiomas):** `docs/ARCHITECTURE.md`, `docs/auto-update.md` (reescrito para o modelo PyPI-only), `docs/hooks-versioning.md` (idioma efetivo dos hooks), `docs/mcp-integration.md`, `docs/skill-template.md`, `docs/testar_sem_usar_pypi.md` (sem binário) e `docs/version-markers.md` (novos marcadores).
* **Documentação em 5 idiomas:** **39 tópicos canônicos** em `docs/` — **34 com cobertura completa nos 5 idiomas** (+2 desde o relatório anterior) e 5 tópicos parciais/PT-only (`como_reverter_commit_git_localmente`, `github-issue-prompt-com-gh`, `otimizacao-de-tokens`, `testar_sem_usar_pypi`, `version-markers`).
* **Skills locais do Claude Code:** `.claude/skills/` com **29 skills** (as do projeto — `status-report`, `implement-fixes`, `caveman-commit`, `new-feature`, `code-review`, `wizard`, `grilling` etc. — mais o kit `mattpocock-skills`; o relatório anterior listava apenas 5). A memória ganhou `i18n-sync-canonicos-roundtrip.md` no commit do config TUI.
* **Memory Index:** `.claude/memory/MEMORY.md` com 40 padrões (contagem inalterada nesta janela).
* **Relatórios de tarefas:** `docs/claude-code/reports/develop_natan/` (**90** no total; **+6** na janela — config TUI, 5 correções de UI + usage log, layout/seções/downloads, seção Skills, limpeza `PR_AUTO_PUBLISH` e remoção do binário) e `docs/gemini/reports/develop_natan/` (5 arquivos; sem novas).
* **Relatórios de status:** `docs/reports/` (13 relatórios; este é o 14º).
* **Planos de desenvolvimento:** 89 arquivos em `docs/plans/` (+9 na janela — planos do config TUI, das correções de tela, da seção Skills, da limpeza `PR_AUTO_PUBLISH`, da remoção do binário e o glossário `glossary-config-tui`) + 3 arquivos em `docs/survey/`.

---

## **🔄 Pipeline de Distribuição**

1. **PyPI (canal único):** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **Atualização obrigatória:** a execução verifica o PyPI no startup e **bloqueia com exit code 1** se houver versão mais nova, imprimindo `pip install --upgrade gitpr-cli`; a checagem é cacheada por dia e o `--update` apenas reporta
3. **GitHub Releases:** **removido** — sem PyInstaller, sem asset `.exe`, sem hot-swap; `pyinstaller` saiu do `Pipfile` e o `icon.ico` foi deletado
4. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml` (sempre instalou via pip, então não foi afetado)
5. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`
6. **Templates e idiomas OTA:** `templates/` e `langs/*.json` servidos do GitHub (main) — o bump `v0.0.25` renova as cópias locais de `~/.gitpr/langs/` quando publicado

---

## **📈 Evolução desde o Relatório Anterior (v0.0.13)**

| Área | v0.0.13 (anterior) | v0.0.14 (atual) |
|------|-------------------|-----------------|
| **Versão GitPR** | 1.0.0 | **1.1.0** (CHANGELOG.md com cabeçalho `[1.1.0] - 2026-09-13`) |
| **Versão Idioma** | v0.0.23 | **v0.0.25** (via v0.0.24) |
| **Versão Scripts Hook** | v0.0.3 | **v0.0.3** |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 idiomas, 6 dicionários | 5 idiomas, 6 dicionários |
| **Interface** | CLI + TUIs (Issues, Chat, Dashboard, PR Publisher, LinterApp) + wizard `--init` + `gitpr release` | **+ TUI de configuração `gitpr config` (12 categorias, 56 campos, seção Skills) + log geral de uso** |
| **Ferramentas MCP** | 12 tools / 17 recursos / 7 prompts | 12 tools / 17 recursos / 7 prompts (+ `log_usage()` no entry point) |
| **Flags CLI** | 35 opções na raiz + subcomando `release` (6) | 35 opções na raiz + `release` (6) + **`config` (0 opções)** |
| **Variáveis de Ambiente** | 39 chaves no `DEFAULT_CONFIG` | **39 chaves** (+ `GITPR_SKIP_UPDATE_CHECK`; `GITPR_SHOW_LOGS` saiu da sombra e virou campo na TUI) |
| **Linter** | Regex + bridge Checkstyle (wizard/TUI/relatório) | Inalterado (+ re-download forçado de presets pela TUI) |
| **Hooks Git** | Idioma dos scripts ignorava `--lang` | **Corrigido: `HOOK_SCRIPT_SUFFIXES`, `SCRIPTS_LANG` vs. `SCRIPTS_INSTALLED_LANG`, `effective_hook_lang()`** |
| **Mensagens de Commit** | Com trailer `Co-Authored-By` (opt-out) | Inalterado |
| **i18n (chaves por arquivo)** | 742 × 6 (paridade total) | **955 × 6 (paridade total) — +213 chaves** |
| **Documentação** | 37 tópicos canônicos (32 completos + 5 parciais) | **39 tópicos canônicos (34 completos + 5 parciais) — 2 famílias novas ×5, 7 atualizadas** |
| **Distribuição** | PyPI + GitHub Releases (binário PyInstaller) | **PyPI exclusivo — binário, hot-swap e `pyinstaller` removidos** |
| **Suíte de Testes** | 791 cenários (41 arquivos) | **1060 cenários (49 arquivos: 40 + 9 SCM) — en_us: 1055 passed / 3 failed (2 desatualizados + 1 de locale) / 2 skipped** |
| **Commits desde o relatório** | 10 commits | **2 commits** (`bf9f1b9`, `f108c4c`) |
| **PRs mergeados** | 5 PRs (#146, #151, #153, #155, #159) | **2 PRs (#162, #164)** |
| **Memory Index** | 40 padrões | **40 padrões** (+ `i18n-sync-canonicos-roundtrip.md`) |
| **Relatórios de tarefas** | 84 claude-code, 5 gemini | **90 claude-code (+6 na janela) e 5 gemini** |
| **Planos de desenvolvimento** | 80 | **89 (+9 na janela — config TUI, correções de tela, Skills, limpeza e remoção do binário)** |

---

## **🚧 Próximos Passos**

* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Adicionar histogramas de tempo e gráficos de tendência de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação completa do build e do upload para o PyPI (a geração do changelog agora é local via `gitpr release`, e o canal binário deixou de existir — falta só a automação de CI/CD).
* **Seed de `.gitpr/conf/` local:** O seed de templates de configuração local (smart-excludes, linter) continua pendente como subcomando próprio ou etapa do wizard; a TUI de configuração agora oferece os **downloads** desses arquivos, mas não o seed do projeto.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.
* **Extrator de i18n do `sync_i18n.py`:** O regex trunca literais com concatenação implícita (`__("a " "b")`) — migrar para AST (o guard em `test_i18n.py` já usa AST e não depende do script).
* **Corrigir os testes de timeout desatualizados:** `tests/test_net_timeouts.py` (linhas ~99/117/137/149) assere 600s de default, mas o código usa 180s desde o fix `681a7fa`; alinhar também a docstring stale do `config.py` (ainda menciona "default 600"). **Item herdado, ainda aberto.**
* **Reconciliar a versão do projeto:** `CLAUDE.md` ainda diz "Current version: 0.0.37" enquanto `__version__` está em 1.1.0 e o CHANGELOG registra `[1.1.0] - 2026-09-13`. Definir uma convenção única e atualizar o CLAUDE.md. **Item herdado, ainda aberto.**
* **Dívida do índice do README:** os bullets das famílias `suggested-reviewers`, `scm-multiforge` **e agora `config-tui` e `usage-log`** não estão no índice — a dívida cresceu nesta janela.
* **Robustez de locale nos testes:** 1 teste é sensível ao locale pt_br da máquina (`test_core.py::TestHooksLanguage`) — fixar `GITPR_LANG=en_us` no setup ou mockar `TRANSLATIONS` para a suíte ficar 100% verde em qualquer máquina/CI.
* **`gitpr -h config` ignora o `-h` 🆕:** o subcomando abre a TUI em vez de mostrar a ajuda — o gate `if ctx.invoked_subcommand is not None: return` roda antes do bloco de `help_flag`. Corrigir mudaria o comportamento de `-h` para **todos** os subcomandos, então precisa de decisão.
* **Seção Smart Exclude na TUI 🆕:** dos 12 itens reportados após o uso da tela, o item 10 (seção *Smart Exclude*) é a única entrega ainda não iniciada — o esboço está nos next steps do relatório da tarefa.
* **Dívidas registradas no plano do config TUI 🆕:** `DEFAULT_CONFIG` ficou redundante com o schema; o banner de abertura não lista `--dashboard`, `--init`, `--base` nem `--plugins`; o `LinterApp` não desabilita a command palette.

### ✅ Concluídos nesta janela (2026-09-08 → 2026-09-13)

* ~~**Subcomando `gitpr config` com TUI master-detail**~~ — schema declarativo, camada de escrita do `.env`, validação em duas camadas, busca, docs ×5 (PR #162).
* ~~**Seção Skills na TUI**~~ — edição dos `.gitpr/skill/*.md` do projeto com escrita atômica, registro `SKILL_FILES_BY_TYPE` unificado em `config.py` (PR #162).
* ~~**Log geral de uso (`GITPR_SHOW_LOGS`)**~~ — `src/usage_log.py`, um arquivo por dia, escrita síncrona, silencioso (PR #162).
* ~~**Correção do idioma dos hooks Git**~~ — `--lang` deixou de ser ignorado; `SCRIPTS_LANG` separado de `SCRIPTS_INSTALLED_LANG` (PR #162).
* ~~**Correção do badge de ambiente na TUI**~~ — `AMBIENT_ENV_KEYS` capturado antes do `load_dotenv` de nível de módulo; o badge passou a significar o que promete (PR #162).
* ~~**Limpeza da chave morta `PR_AUTO_PUBLISH`**~~ — removida do `CLAUDE.md` e do `.env` do usuário; §5 da doc da TUI corrigida nas 5 versões.
* ~~**Distribuição exclusiva via PyPI + portão de atualização obrigatória**~~ — `enforce_update_required()`, `GITPR_SKIP_UPDATE_CHECK`, remoção do hot-swap, do binário e do `pyinstaller`; `docs/auto-update.md` reescrito ×5 (PR #164).
* ~~**i18n: +213 chaves e cadeia v0.0.23 → v0.0.25**~~ — paridade total de key sets nos 6 dicionários, com as três fontes de tradução em lockstep.
* ~~**Documentação das 2 famílias novas**~~ — `config-tui` e `usage-log` em 5 idiomas, mais 7 tópicos atualizados.

---

**Relatório gerado em:** 2026-09-13  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
