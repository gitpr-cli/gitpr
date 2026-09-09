# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.13 (2026-09-08)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.13):**
- **SCM Multi-Forge (`gitpr --init` + camada `ScmProvider`):** Abstração única sobre GitHub, GitLab, Bitbucket e Azure DevOps em `src/infrastructure/scm/` — registry com `resolve_scm_provider()` (default `github`, fallback do token legado intacto), `parse_repo_ref()` para endereçar repositórios, providers que levantam `ScmProviderError` e wizard `--init` que detecta a forge pelo remote, valida o token (`test_connection`, 3 tentativas, re-prompt em 401) e persiste **apenas em sucesso** com criptografia Fernet. `src/github_api.py` virou um shim deprecado que delega ao provider.
- **Suggested Reviewers no fluxo de PR:** Sugestão de revisores da própria forge na publicação de PRs, com opt-out por flag (`--no-suggest-reviewers`) e configuração por ambiente (`GITPR_SUGGEST_REVIEWERS`, `GITPR_REVIEWER_SUGGESTION_TOP_N`, `GITPR_REVIEWER_SUGGESTION_EXCLUDED`).
- **Subcomando `gitpr release` (Changelog / Release Notes):** Gera o changelog da branch entre `--since` (default: última tag) e `HEAD`, classifica os commits por Conventional Commits (`src/commit_classifier.py`), sugere bump semântico (`src/version_bump.py`), monta as seções traduzíveis (`src/changelog_builder.py`), adiciona resumo executivo de IA e faz *prepend* no `CHANGELOG.md`. Com `--publish`/`--draft` publica a release na forge (GitHub cria a tag; GitLab exige tag existente); `--format markdown|json` para saída estruturada. Template de skill `gitpr.release.*.md` baixado automaticamente no primeiro uso, em 5 idiomas.
- **MCP Server silencioso + DNS limitado:** Correção do vazamento de saída das tools no fluxo stdio/CLI e resolução DNS com limite de tempo (bug da janela anterior). Default de `GITPR_AI_TIMEOUT` reduzido de 600s para **180s**.
- **URLs e prompts localizados:** URLs do repositório padronizadas nos templates e na documentação; prompts de criação de issue ganham o idioma ativo.
- **i18n expandida para 742 chaves:** Headings do changelog agora são traduzíveis (helper de runtime, não constantes opacas), 48 chaves novas traduzidas nos 6 dicionários, `__lang_version__` v0.0.23 e bullet da família `release-notes` no índice do README (5 cópias).
- **Documentação Multilíngue Expandida:** 3 famílias novas completas em 5 idiomas — `release-notes`, `scm-multiforge` e `suggested-reviewers` (+ ADRs de arquitetura para SCM e release) — e 8 tópicos atualizados.
- **Salto de versão:** `__version__` foi de 0.0.37 para **1.0.0** (via 0.0.38 nesta janela); o CHANGELOG.md registra o cabeçalho `[v0.1.0] - 2026-09-07` gerado pela própria feature de release durante o desenvolvimento.

- **Versão atual:** 1.0.0
- **Versão dos dicionários de idioma:** v0.0.23
- **Versão dos scripts de hook:** v0.0.3
- **Publicação:** PyPI (`pip install gitpr-cli`) + GitHub Releases (binário standalone)
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal).
* **UI/Terminal:** Textual — TUI (Text User Interface) para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher e erros do linter (`LinterApp`).
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API, tokens GitHub e tokens SCM das forges.
* **Configuração:** `python-dotenv`, `pyyaml` (para o linter estático).
* **IA Providers:** Integração via SDK oficial do Google GenAI (`gemini-2.5-flash`), OpenAI SDK (`DeepSeek`), e OpenAI SDK (`Ollama` local).
* **Forge APIs:** `requests` (REST) — camada de abstração multi-forge em `src/infrastructure/scm/` (GitHub, GitLab, Bitbucket, Azure DevOps); módulo legado `src/github_api.py` mantido como shim deprecado.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — 12 ferramentas anotadas, 17 recursos, 7 prompts; handlers offloaded para threads via `anyio`.
* **Testes:** Pytest + `unittest.mock` (41 arquivos de teste — 32 na raiz + 9 em `tests/scm/` —, 791 cenários coletados) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio).
* **Empacotamento:** PyInstaller (binário standalone) + setuptools/build (PyPI).
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
* **Smart Excludes com Duas Camadas:** Filtro de pathspec inteligente com camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`). Mesclagem em runtime (união, deduplicada). Auto-seeding do arquivo local na primeira execução.
* **Métricas com Rastreamento de Tempo:** Injeção de `log_command_metric()` em todos os fluxos com repasse da duração em milissegundos (`duration_ms`) e lazy imports.
* **Resolução Centralizada de Output:** Função `resolve_output_path()` que centraliza a lógica de diretórios de saída — default em `.gitpr/reports/{type}/`.
* **Wizard SCM (`run_scm_init_wizard()`) 🆕:** `gitpr --init` — detecta a forge pelo remote origin, solicita extras por forge (org/projeto Azure, usuário Bitbucket), valida o token com `test_connection` (3 tentativas, 401 re-prompt) e persiste `GITPR_SCM_PROVIDER` + `GITPR_SCM_TOKEN_ENCRYPTED` (Fernet) **somente em sucesso**.
* **Skill Template de Release (`ensure_release_skill_template()`) 🆕:** Baixa `templates/gitpr.release.*.md` no primeiro uso de `gitpr release` (CLI layer, idioma-aware, nunca sobrescreve; pulado em `--format json`).
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
* **Routing de Comandos:** Gerencia todas as flags e o subcomando `release` (ver módulo 22).
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags (35 opções Click na raiz):**
  * `--init` 🆕: Abre o wizard de configuração SCM multi-forge (detecção da forge + validação do token).
  * `--no-suggest-reviewers` 🆕: Desliga a sugestão de revisores no fluxo de publicação de PR.
  * `--no-publish`: Gera a descrição do PR e salva localmente sem abrir o editor interativo.
  * `--no-edit`: Pula a TUI completamente — auto-commit, auto-push e publica direto no GitHub.
  * `--base <branch>`: Sobrescreve a branch de destino do Pull Request.
  * `--plugins`: Lista plugins globais instalados.
  * `--linter-setup`: Abre o assistente interativo de configuração de linters externos.
  * `--version`: Exibe a versão atual do GitPR (via `@click.version_option`).
* **Variáveis de Ambiente (39 chaves no `DEFAULT_CONFIG`):** família SCM 🆕 (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME`), família de revisores 🆕 (`GITPR_SUGGEST_REVIEWERS`, `GITPR_REVIEWER_SUGGESTION_TOP_N`, `GITPR_REVIEWER_SUGGESTION_EXCLUDED`), além de `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `GITPR_SHOW_LOGS`, `GITPR_AUTO_MERGE`, `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`, `GITPR_AI_TIMEOUT` (default 180s nesta janela), `OUTPUT_FILE_NAME_*`, `GITPR_COAUTHOR` (read-only) e demais.
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub. 🆕 Subcomandos ganham `epilog=` próprio: `gitpr release -h` termina com "Full documentation:" + `get_doc_url("release-notes.md")` (parágrafo `\b` do Click para a URL não ser reembrulhada sob nenhum locale).
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **12 ferramentas anotadas + 17 recursos + 7 prompts**.
* **--install:** Assistente guiado de 4 etapas que baixa templates de skill, instala Git Hooks, configura MCP nos editores e valida chaves de API.
* **--metrics:** Sistema de telemetria local com escopo por repositório: `--export`, `--purge`, `--dashboard`.
* **--status:** Lista arquivos não commitados categorizados (new/modified/deleted) — rápido, sem IA, sem rede.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI construída com Textual para revisar, editar e publicar Pull Requests diretamente no terminal.
* **6 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen`.
* **Suggested Reviewers 🆕:** O fluxo de publicação consulta a forge por revisores sugeridos e os oferece na TUI; seleção controlada por `--no-suggest-reviewers`, `GITPR_SUGGEST_REVIEWERS`, `GITPR_REVIEWER_SUGGESTION_TOP_N` e `GITPR_REVIEWER_SUGGESTION_EXCLUDED`.
* **Bindings:** F1 (Help), F2 (Salvar .md local), F3 (Publicar via GitHub API), Esc (Sair).
* **Fluxo de Auto-Commit:** Linter → mensagem IA → confirma → commita → push → publica PR.
* **Verificação de Arquivos Unstaged:** Ao iniciar, verifica `git status --porcelain` e oferece modal para selecionar, pular ou cancelar.
* **Tratamento de PR Existente:** Detecta PRs abertos para a branch atual via API e oferece push ou criar novo.
* **Auto-Upstream:** Detecta falha de `git push` por falta de upstream e automaticamente tenta `--set-upstream origin <branch>`.
* **Merge Flow:** Após criação/atualização do PR, oferece opção de merge. Controlado por `GITPR_AUTO_MERGE`.

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Shim Deprecado 🆕:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` e demais funções agora delegam a `src/infrastructure/scm/github_provider.py`; o módulo emite `DeprecationWarning` e mantém as tuplas legadas `(ok, data, status)` — nenhum código novo pode importá-lo.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no git diff sem gastar cotas de IA.
* **Regras YAML:** Lê o arquivo local `.gitpr.linter.yml` (criado via `--skill`).
* **Plugins de Linter:** Regras adicionais carregadas de `~/.gitpr/plugins/linter/*.yml`.
* **Bridge de Linters Externos:** Executa ESLint/PHPCS/Stylelint nas linhas alteradas do diff, parser Checkstyle XML e cruzamento por linha.
* **Relatório Consolidado:** `generate_linter_report_content()` consolida erros regex + externos em `.gitpr/reports/linter/` — gerado apenas quando há violações.

### **7. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data` e `decrypt_data` para proteger chaves de API de IA, GitHub PAT e tokens SCM das forges (`GITPR_SCM_TOKEN_ENCRYPTED`).
* **Validação Multi-Forge 🆕:** `validate_or_request_scm_token(provider, repo_display)` — valida o token na forge configurada com 401 → loop de reautenticação preservando o rascunho; o token GitHub legado (`GITHUB_TOKEN_ENCRYPTED`) permanece funcional até o `--init` rodar.

### **8. Auto-Updater (`src/updater.py`)**

* **Hot-Swap:** Verifica na API do GitHub Releases a versão mais recente, baixa o binário compilado e substitui sem quebrar a execução em andamento (com rollback).
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Versionamento Centralizado:** `__version__` (**1.0.0**), `__lang_version__` (**v0.0.23**), `__scripts_version__` (**v0.0.3**), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`.

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Construída com Textual — histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico de conversa persistido por branch, permitindo continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear` — atalhos para pair programming.
* **Auto-Patching (F5), Atualização de Diff (F2), Exportação de Sessão (F6).**

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com suporte a placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas, 6 Dicionários:** en_us (padrão/fallback), pt_br, pt_pt, es/es_es, fr/fr_fr.
* **Arquivos Versionados:** `__lang_version__` (**v0.0.23**) controla atualização dos pacotes de idioma (`langs/*.json`) — cadeia de bumps v0.0.20 → v0.0.23 nesta janela.
* **Cobertura:** **742 chaves** de tradução em cada um dos 6 arquivos — **paridade total de key sets** (auditoria AST de 742 chaves em código: 0 não traduzidas, 0 órfãs).
* **Headings do Changelog Traduzíveis 🆕:** Os 8 headings de seção do changelog (Features, Bug Fixes, Breaking Changes etc.) deixaram de ser constantes opacas e agora são literais `__()` resolvidos em runtime via helper `_category_heading()` — seguem `--lang`/`set_lang` e são visíveis ao extrator AST.
* **Traduções Genuínas 🆕:** +195 chaves desde o relatório anterior (48 delas da tarefa de next steps de 08-09-2026, em tradução real nos 6 dicionários, CRLF preservado).
* **Cache com Indexação por Idioma:** Respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Modo JSON & Parâmetros Determinísticos:** Outputs estruturados com `temperature=0.0` e `top_p=0.1`; fallback automático entre provedores configurados.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt, com indexação por idioma.
* **Telemetria e Duração:** Persistência dos campos `duration_ms` e `meta_raw` em arquivos de cache.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` lê todos os arquivos de cache recursivamente.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`), e Arqueologia por Blame (`-b`).
* **Publicação Multi-Forge 🆕:** F3 cria a issue na forge **configurada** (`GITPR_SCM_PROVIDER`) via `provider.create_issue` — não apenas GitHub; Azure DevOps levanta `ScmNotSupportedError` (Work Items dependem do process template).
* **Map-Reduce para Issues:** Quando o contexto excede ~90k tokens, divide automaticamente em chunks e unifica os resultados.
* **Tratamento de 401:** Sinalização de reautenticação sem fechamento da aplicação.

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia a evolução e autoria histórica de trechos de código com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos registrados via `log_blame_metric()` com rastreamento de profundidade e número de commits analisados.

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)**

* **12 Ferramentas MCP Anotadas:** Ferramentas para `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`.
* **17 Recursos + 7 Prompts Templatizados:** `skill://list` + `skill://{pr,commit,review,filereview,issue,blame,release}` + `linter://config` + `prompt://list` + 7 prompts — 🆕 recursos de skill de release (e família correspondente nos templates).
* **Invocação CLI Direta:** Comando `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool MCP diretamente sem iniciar o servidor stdio JSON-RPC.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve diretamente no `sys.__stdout__` original, garantindo JSON puro no stdout.
* **Silêncio Garantido 🆕:** Saída das tools silenciada no fluxo servidor/CLI (vazamentos de print que corrompiam a stream JSON-RPC foram eliminados — fix `681a7fa`, PR #146).
* **DNS com Limite de Tempo 🆕:** Resolução de DNS das operações de rede limitada no tempo — nenhuma chamada bloqueante fica presa na resolução (junto ao timeout duro de download OTA).
* **Offload do Event Loop:** Decorator `_offload` (`anyio.to_thread.run_sync`) aplicado às 12 tools — handlers síncronos não congelam o servidor stdio.
* **Testes E2E:** `tests/test_mcp_server_e2e.py` sobe o servidor real como subprocess e fala JSON-RPC stdio.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório (Repo-Scope):** Rótulo `📁 Repository: owner/repo` e filtragem estrita por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com widget `ProgressBar`.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de cache ao totalizador.
* **Exportação Local:** Salvamento de CSV/JSON em `./.gitpr/metrics/export/`.

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`.
* **Eventos de Hook, Linter e Blame:** `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()`.
* **Exportação e Limpeza:** `--metrics --export` (CSV/JSON) e `--metrics --purge` com confirmação interativa.

### **19. Sincronização de Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (v0.0.3) controla a versão dos scripts de hook; detecção automática e atualização.
* **Idioma-Aware:** Baixa templates de hook correspondentes ao idioma configurado.
* **Skip de Merge-Source:** O template `prepare-commit-msg` pula as fontes `message|merge|squash|commit` — commits gerados pelo git preservam a mensagem original.

### **20. Bridge de Linters Externos e Assistente Interativo (`src/linter_wizard.py`, `src/ui/linter_app.py`)**

* **Assistente `--linter-setup`:** Wizard interativo com presets numerados (PHP_CodeSniffer, ESLint, Stylelint) e injeção do bloco `external_linters` no `.gitpr.linter.yml`.
* **Presets Remotos:** `templates/gitpr.linter-presets.json` servido do GitHub com cadeia de resolução local → download → stale → fallback embutido.
* **TUI de Erros do Linter:** `src/ui/linter_app.py` (Textual) exibe erros críticos e warnings; em hook/quiet imprime e faz `sys.exit(1)`.
* **Relatório Markdown:** Consolidado em `.gitpr/reports/linter/` — apenas quando há violações.

### **21. SCM Multi-Forge (`src/infrastructure/scm/`) 🆕**

* **Abstração Única (`ScmProvider` ABC):** `base.py` define o contrato (dataclasses `RepoRef`, `PullRequestDraft` etc. e `ScmProviderError(provider, http_status, message)` — `http_status` 0 = falha de rede); um provider concreto por forge em `github_provider.py`, `gitlab_provider.py`, `bitbucket_provider.py`, `azure_devops_provider.py`.
* **Registry e Factory:** `resolve_scm_provider()` seleciona por `GITPR_SCM_PROVIDER` (default `github` — migração zero, fallback do token GitHub legado intacto); `detect_provider_from_remote()` identifica a forge pela URL do origin.
* **Endereçamento de Repositório:** `parse_repo_ref(remote_url) -> RepoRef(raw, workspace, name, provider)` — workspace = owner GitHub / namespace GitLab (subgrupos) / workspace Bitbucket / display `{org}/{project}` do Azure.
* **Fail-Fast por Forge:** Azure DevOps exige `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`; Bitbucket exige `GITPR_SCM_USERNAME` (App Password = Basic auth user+token); `create_issue` no Azure levanta `ScmNotSupportedError`.
* **Publicação de Releases 🆕:** `provider.create_release()` usado pelo `gitpr release --publish` (GitHub cria a tag no branch default; GitLab exige a tag existente) — `tests/scm/test_release_publish.py`.
* **Artefatos:** Glossário + ADR-001 em `docs/plans/`; família `docs/scm-multiforge.*.md` em 5 idiomas; testes: 9 arquivos, 265 cenários.

### **22. Subcomando `gitpr release` — Changelog / Release Notes 🆕**

* **Fluxo:** `git log` entre `--since` (default: última tag alcançável, ou o primeiro commit) e `HEAD` → classificação por Conventional Commits → bump semântico sugerido (`--version <x.y.z>` sobrescreve) → montagem do changelog → resumo executivo de IA opcional → *prepend* no `CHANGELOG.md`. Geração local é o default — nada é publicado nem tocado sem pedido.
* **Classificador (`src/commit_classifier.py`):** Classifica os commits por tipo Conventional Commits (feat/fix/refactor/docs/chore/etc.) com parser tolerante — base do agrupamento das seções.
* **Builder com Seções Traduzíveis (`src/changelog_builder.py`):** Seções "✨ Features", "🐛 Bug Fixes", "⚠️ Breaking Changes", "Summary", "Contributors" etc. renderizadas via `__()` em runtime (seguem o `--lang`); aritmética de auditoria AST fechada (742 = 742).
* **Bump Semântico (`src/version_bump.py`):** Sugere a próxima versão a partir dos tipos classificados (major para breaking, minor para feat, patch para fix) e valida alvos `x.y.z`.
* **Publicação:** `--publish` cria a release na forge configurada (com confirmação explícita); `--draft` cria como rascunho (GitHub; GitLab não tem conceito de draft); `--format markdown|json` para saída estruturada; `--force` para regravação.
* **Skill Template:** No primeiro uso baixa `templates/gitpr.release.*.md` (5 idiomas: en/pt_br/pt_pt/es_es/fr_fr) via `ensure_release_skill_template()` — nunca sobrescreve; editável localmente como system instruction do resumo executivo.
* **Ajuda Contextual:** `gitpr release -h` termina com "Full documentation:" + link language-aware para `docs/release-notes.md` (epilog `\b`, sem rewrap da URL).
* **Testes:** 94 cenários novos — `test_release_cli.py` (4), `test_release_engine.py` (27), `test_changelog_builder.py` (15), `test_commit_classifier.py` (23), `test_version_bump.py` (17) + `tests/scm/test_release_publish.py` (8).
* **Artefatos:** Família `docs/release-notes.*.md` (5 idiomas), spec em `docs/plans/`, ADR-002 (subcomando) e ADR-003 (módulos flat), glossário de release notes.

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_blame_engine_ranges.py` | 7 🆕 | Blame por faixa de linhas em arquivo |
| `tests/test_blame_metrics.py` | 7 | Métricas de blame: profundidade, commits, duração |
| `tests/test_changelog_builder.py` | 15 🆕 | Builder do changelog: seções, headings traduzíveis, contribuidores |
| `tests/test_chat_backend.py` | 19 | Memória de chat, persistência, comandos slash |
| `tests/test_commit_classifier.py` | 23 🆕 | Classificação Conventional Commits (tipos, parser tolerante) |
| `tests/test_config_suggest_reviewers.py` | 8 🆕 | Configuração de suggested reviewers (chaves e defaults) |
| `tests/test_core.py` | 39 | Fluxos principais, git diff, PR generation, timing, staging, coautoria |
| `tests/test_diff_parser.py` | 15 🆕 | Parser de diff por linhas/hunks |
| `tests/test_external_linters.py` | 33 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_i18n.py` | 20 | Paridade entre idiomas (742×6), chaves ausentes/órfãs, identidade |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação |
| `tests/test_issue_engine.py` | 4 | Draft de issue estruturado |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_main_suggest_reviewers.py` | 6 🆕 | Flag `--no-suggest-reviewers` na CLI e no help contextual |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 85 | Ferramentas MCP, recursos, annotations, patching, CLI direto, offload |
| `tests/test_mcp_server_e2e.py` | 6 | Servidor MCP real via subprocess + JSON-RPC stdio |
| `tests/test_metrics.py` | 34 | Coleta, exportação local, escopo de repo, cache token summary |
| `tests/test_net_timeouts.py` | 12 | Timeouts de rede/IA — **2 asserções desatualizadas (600s)** |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_pr_publish_app.py` | 42 | TUI do PR Publisher: telas, fluxos, suggested reviewers |
| `tests/test_pr_publish_linter_modal.py` | 4 | Modal de erro do linter: abort, no-verify |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_release_cli.py` | 4 🆕 | CLI do release: options, help com epilog documentado |
| `tests/test_release_engine.py` | 27 🆕 | Engine de release: intervalo de commits, CHANGELOG, publicação |
| `tests/test_reviewer_suggestion.py` | 15 🆕 | Lógica de sugestão de revisores (ranking, exclusão, top-N) |
| `tests/test_skill_command.py` | 10 | Download e validação de templates de skill |
| `tests/test_skill_context.py` | 6 🆕 | `get_skill_context()` com `quiet=True` (fallbacks, release) |
| `tests/test_smart_excludes.py` | 13 | Filtro pathspec inteligente |
| `tests/test_suggest_reviewers.py` | 14 🆕 | Suggested reviewers no fluxo de PR (integração) |
| `tests/test_thinking_words.py` | 3 | Carregamento e parsing com separador `;` |
| `tests/test_version_bump.py` | 17 🆕 | Bump semântico: major/minor/patch, alvos e validação |
| `tests/scm/test_contract.py` | 38 🆕 | Contrato `ScmProvider`: assinaturas, dataclasses, erros |
| `tests/scm/test_github_provider.py` | 57 🆕 | Provider GitHub: REST, headers, PRs, issues, releases |
| `tests/scm/test_gitlab_provider.py` | 41 🆕 | Provider GitLab: API v4, namespace, releases |
| `tests/scm/test_bitbucket_provider.py` | 39 🆕 | Provider Bitbucket: Basic auth, workspace |
| `tests/scm/test_azure_devops_provider.py` | 43 🆕 | Provider Azure DevOps: org/projeto, PRs, `ScmNotSupportedError` |
| `tests/scm/test_factory.py` | 11 🆕 | `resolve_scm_provider()` + `detect_provider_from_remote()` |
| `tests/scm/test_github_api_shim.py` | 18 🆕 | Shim deprecado `github_api` → delega ao provider (substitui `test_github_api.py`) |
| `tests/scm/test_init_wizard.py` | 10 🆕 | Wizard `--init`: detecção da forge, validação, persistência |
| `tests/scm/test_release_publish.py` | 8 🆕 | Publicação de release por forge (GitHub/GitLab) |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (scaffold; nunca executado) |

**Total:** 791 cenários coletados em 41 arquivos de teste (32 na raiz + 9 em `tests/scm/`; +527 desde o relatório anterior — inclui os 265 cenários de SCM, que antes não existiam como suíte). Execução completa nesta máquina com `GITPR_LANG=en_us`: **787 passed / 2 failed / 2 skipped / 15 subtests** em ~63s.

**Notas de qualidade desta versão:**
- **2 falhas reais (testes desatualizados):** `test_net_timeouts.py` ainda assere o default de 600s para `GITPR_AI_TIMEOUT`, mas o código passou a usar **180s** nesta janela (fix `681a7fa`) — ver Próximos Passos.
- **4 falhas ambientais de locale (máquina pt-BR):** `test_chat_backend::test_api_exception`, `test_main_suggest_reviewers::test_flag_appears_in_contextual_help` e `test_suggest_reviewers` ×2 renderizam texto pt_br da cópia OTA de `~/.gitpr/langs/` — passam integralmente com `GITPR_LANG=en_us`. A suíte 100% verde do relatório anterior não se repete nesta versão (2 regressões de teste + sensibilidade de locale).
- `test_github_api.py` foi **removido** (código legado virou shim) e sucedido por `tests/scm/test_github_api_shim.py` (18 cenários).

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** **742 chaves** de tradução em cada um dos 6 dicionários (+195 desde o relatório anterior) com **paridade total de key sets** — auditoria AST de 742 chaves usadas em código: 0 não traduzidas, 0 órfãs. As 48 últimas chaves (next steps da família release-notes: headings do changelog, help strings, prompts de IA com `\n` real preservado) foram traduzidas com CRLF byte-exato preservado.
* **Tópicos novos 🆕 (os 3 em 5 idiomas):**
  - `docs/release-notes.md` — família do subcomando `gitpr release` (fluxo, versões, publicações, resumo de IA, skill template)
  - `docs/scm-multiforge.md` — camada `ScmProvider` e wizard `--init` (4 forges, tokens, limitações por forge)
  - `docs/suggested-reviewers.md` — suggested reviewers no fluxo de PR (configuração e flags)
* **Tópicos atualizados nesta janela (todos re-sincronizados nos 5 idiomas):** `docs/auto-update.md`, `docs/github-ci-linter.md`, `docs/linter-regras-customizadas.md`, `docs/map-reduce-diff.md`, `docs/mcp-integration.md`, `docs/providers-ia.md`, `docs/skill-template.md`, `docs/smart-excludes.md` + `docs/ARCHITECTURE.md` (EN; registro das novas famílias).
* **Documentação em 5 idiomas:** **37 tópicos canônicos** em `docs/` — **32 com cobertura completa nos 5 idiomas** (+3 desde o relatório anterior) e 5 tópicos parciais/PT-only (`como_reverter_commit_git_localmente`, `github-issue-prompt-com-gh`, `otimizacao-de-tokens`, `testar_sem_usar_pypi`, `version-markers` — este último agora contado explicitamente).
* **Skills locais do Claude Code:** `.claude/skills/` com `status-report`, `implement-fixes`, `caveman-commit`, `new-feature` e `reports-to-memory` (sem novas nesta janela).
* **Memory Index:** `.claude/memory/MEMORY.md` com 40 padrões (25 de projeto, 9 de feedback, 3 de referência + 3 avulsos).
* **Relatórios de tarefas:** `docs/claude-code/reports/develop_natan/` (**84** no total; **+15** na janela — SCM multi-forge, suggested reviewers, docs das 3 famílias, release notes/spec, skill de release template, next steps de i18n etc.) e `docs/gemini/reports/` (5 arquivos hoje; +2 na janela: `2026-08-28_add_mcp_tools_to_gemini_md.md` e `2026-09-03_update_repo_urls.md` — a contagem do relatório anterior (8) incluía arquivos removidos na restauração do diretório em 26-08).
* **Relatórios de status:** `docs/reports/` (12 relatórios; este é o 13º).
* **Planos de desenvolvimento:** 80 arquivos em `docs/plans/` (+21 na janela — specs e ADRs de SCM multi-forge, release notes, suggested reviewers, surveys e skill de release).

---

## **🔄 Pipeline de Distribuição**

1. **PyPI:** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **GitHub Releases:** PyInstaller → `.exe` standalone → upload automatizado
3. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml`
4. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`
5. **Templates e idiomas OTA:** `templates/` e `langs/*.json` servidos do GitHub (main) — o bump `v0.0.23` renova as cópias locais de `~/.gitpr/langs/` quando publicado

---

## **📈 Evolução desde o Relatório Anterior (v0.0.12)**

| Área | v0.0.12 (anterior) | v0.0.13 (atual) |
|------|-------------------|----------------|
| **Versão GitPR** | 0.0.37 | **1.0.0** (via 0.0.38 na janela; CHANGELOG.md com cabeçalho `[v0.1.0]`) |
| **Versão Idioma** | v0.0.20 | **v0.0.23** |
| **Versão Scripts Hook** | v0.0.3 | **v0.0.3** |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 idiomas, 6 dicionários | 5 idiomas, 6 dicionários |
| **Interface** | CLI + TUI Issues + Chat TUI + MCP Server + Dashboard + PR Publisher TUI + LinterApp + `--linter-setup` | **+ wizard SCM `--init` + subcomando `gitpr release` (CLI) + suggested reviewers no PR Publisher** |
| **Ferramentas MCP** | 12 tools (offload) | **12 tools (offload; saída silenciada + DNS limitado) — 17 recursos (era 15)** |
| **Flags CLI** | 27 flags | **35 opções na raiz (+ `--init`, `--no-suggest-reviewers`; contagem Click completa) + subcomando `release` com 6 opções** |
| **Variáveis de Ambiente** | 23 vars | **39 chaves no `DEFAULT_CONFIG` (+ 7 SCM + 3 de revisores)** |
| **Linter** | Regex + bridge Checkstyle (wizard/TUI/relatório) | Inalterado |
| **Mensagens de Commit** | Com trailer `Co-Authored-By` (opt-out) | Inalterado |
| **i18n (chaves por arquivo)** | 547 × 6 (paridade total) | **742 × 6 (paridade total) — headings do changelog traduzíveis** |
| **Documentação** | 33 tópicos canônicos (29 completos + 4 parciais) | **37 tópicos canônicos (32 completos + 5 parciais) — 3 famílias novas ×5, 8 atualizadas** |
| **Suíte de Testes** | 264 cenários (17 arquivos) | **791 cenários coletados (41 arquivos: 32 + 9 SCM) — en_us: 787 passed / 2 failed (desatualizados) / 2 skipped** |
| **Commits desde o relatório** | 17 commits | **10 commits** |
| **PRs mergeados** | 8 PRs (#119–#135) + 2 PR_DESCs sem referência | **5 PRs (#146, #151, #153, #155, #159)** |
| **Memory Index** | 32 padrões | **40 padrões (25 projeto / 9 feedback / 3 referência)** |
| **Relatórios de tarefas** | 65 claude-code, 8 gemini | **84 claude-code (+15 na janela) e 5 gemini (+2; contagem anterior incluía arquivos da pré-restauração de 26-08)** |
| **Planos de desenvolvimento** | 59 | **80 (+21 na janela — specs, ADRs e surveys)** |

---

## **🚧 Próximos Passos**

* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Adicionar histogramas de tempo e gráficos de tendência de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação completa do build PyInstaller e envio de assets para o GitHub Releases (a geração do changelog agora é local via `gitpr release` — falta a automação de CI/CD).
* **Seed de `.gitpr/conf/` local:** `--init` virou o wizard SCM nesta janela; o seed de templates de configuração local (smart-excludes, linter) continua pendente como subcomando próprio ou etapa do wizard.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.
* **Extrator de i18n do `sync_i18n.py`:** O regex trunca literais com concatenação implícita (`__("a " "b")`) — migrar para AST (o guard em `test_i18n.py` já usa AST e não depende do script).
* **Corrigir os testes de timeout desatualizados 🆕:** `tests/test_net_timeouts.py` (linhas ~99/117/137/149) assere 600s de default, mas o código usa 180s desde `681a7fa`; alinhar também a docstring stale do `config.py` (ainda menciona "default 600").
* **Reconciliar a versão do projeto 🆕:** `CLAUDE.md` ainda diz "Current version: 0.0.37"; `__version__` está em 1.0.0; o CHANGELOG.md registra `[v0.1.0] - 2026-09-07` (gerado pela própria feature). Definir uma convenção única e atualizar o CLAUDE.md.
* **Dívida do índice do README 🆕:** os bullets das famílias `suggested-reviewers` e `scm-multiforge` ainda não estão no índice (decisão: só `release-notes` nesta rodada).
* **Robustez de locale nos testes 🆕:** 4 testes são sensíveis ao locale pt_br da máquina (cópias OTA de `~/.gitpr/langs/`) — fixar `GITPR_LANG=en_us` no setup ou mockar `TRANSLATIONS` para a suíte ficar 100% verde em qualquer máquina/CI.

### ✅ Concluídos nesta janela (2026-08-28 → 2026-09-08)

* ~~**Silêncio das tools MCP + DNS limitado**~~ — fix `681a7fa` (PR #146); default de `GITPR_AI_TIMEOUT` 600s → 180s.
* ~~**URLs do repositório padronizadas + prompts de issue localizados**~~ — `fa4bac1` (PR #151).
* ~~**SCM multi-forge completo**~~ — providers, factory, wizard `--init`, shim deprecado, docs ×5 e suíte `tests/scm/` (PR #153).
* ~~**Suggested reviewers no fluxo de PR**~~ — flag, config, testes e docs ×5 (PR #155).
* ~~**Subcomando `gitpr release`**~~ — módulos, testes, templates de skill ×5, docs ×5, ADRs e spec (PR #159, commit `b0e5d92`).
* ~~**Next steps da família release-notes**~~ — ajuda contextual `gitpr release -h` → docs; 48 chaves i18n traduzidas (742 × 6); headings do changelog traduzíveis; bullet da família no índice do README ×5 — ver [relatório da tarefa](../claude-code/reports/develop_natan/2026-09-08_release_notes_next_steps.md).

---

**Relatório gerado em:** 2026-09-08  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
