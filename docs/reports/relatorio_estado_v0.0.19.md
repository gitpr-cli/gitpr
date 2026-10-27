# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.19 (2026-10-27)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.19):**
- **Dois releases fechados — 1.4.1 e 1.4.2:** o v0.0.18 deixou o 1.4.1 "preparado, mas ainda não fechado". Esta janela fechou **os dois**: a tag `v1.4.1` foi criada em 2026-10-18 (PR #218) e a `v1.4.2` em 2026-10-27 (PR #222), com o `CHANGELOG.md` commitado nas duas. O PyPI já serve **1.4.2**; `v1.4.0` deixou de ser a última tag.
- **O diff sumia em repositório com conteúdo legado:** `get_git_full_diff()` decodificava a saída do `git diff` como UTF-8 estrito. Um único byte Latin-1 (`0xFA`) matava a thread de leitura do subprocesso, `stdout` voltava `None` **sem exceção** e o CLI anunciava "No new code found" — como se a branch não tivesse mudanças. Todas as **10** chamadas de `subprocess` que capturam saída do git passaram a decodificar com `errors="replace"`, e o `None` devolvido pelo git agora **encerra com código 1** em PR, review, full review e commit. Diff vazio de verdade continua saindo **0**, e o `--hook` falha **aberto**, porque um `prepare-commit-msg` não-zero abortaria o commit do usuário.
- **`explain` e `tests generate` finalmente documentados — e consertados no caminho:** eram os **dois últimos** recursos sem tópico em `docs/`, herdados como dívida há várias janelas. Ganharam **5 idiomas cada** (`docs/explain-pr.*` e `docs/tests-generate.*`, 10 arquivos). Documentar revelou **quatro defeitos reais**: `parse_explain_payload()` quebrava com o dict já parseado do provider (`json.loads(dict)` → `TypeError`); `generate_test_file` tinha o mesmo descasamento; `gitpr tests generate --finding` lia `cand.finding.suggested_test` e `cand.diff`, atributos que não existem; e `gitpr -h --explain` estava quebrado por um dest mismatch (`explain_flag` × `explain`).
- **READMEs apontam para o site oficial da documentação:** **342** destinos de documentação nos 5 READMEs deixaram `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/*.md` e passaram a `https://gitpr.natanfiuza.dev.br/docs/*`, com o idioma no `?lang=` e o inglês **sem** parâmetro — exatamente o formato que `src/doc_links.py` já canoniza. **217 URLs únicas** verificadas com `curl`: **0 falhas**.
- **A dívida de i18n não foi paga:** os dicionários seguem em **1620 chaves** (×4) e **1618** (`es.json`, `fr.json`), com **8 chaves usadas no código sem tradução** e **2 órfãs** — os mesmos números do relatório anterior. Somadas às **7 falhas de fixture** de `tests/badge/test_badge_paths.py` e às **2 falhas conhecidas** de `tests/test_mentor_cli.py`, a suíte fecha em **2950 aprovados de 2964** (12 falhas, 2 skips).

- **Versão atual:** 1.4.2 (**publicada no PyPI**; tag `v1.4.2` de 2026-10-27 — a `v1.4.1` de 2026-10-18 também foi criada nesta janela)
- **Versão dos dicionários de idioma:** v0.0.35 (inalterada)
- **Versão dos scripts de hook:** v0.0.4 (inalterada)
- **Publicação:** PyPI (`pip install gitpr-cli`) — canal binário removido
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal) — **15 subcomandos** (`badge`, `baseline`, `check`, `config`, `demo`, `explain`, `fix`, `mentor`, `metrics`, `policy`, `release`, `review-pr`, `risk`, `split`, `tests`). Quatro deles são **grupos**: `baseline` (6 subcomandos), `metrics` (8), `policy` (7) e `tests` (1).
* **UI/Terminal:** Textual — TUI para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher (com o modal de progresso reutilizado no merge), erros do linter (`LinterApp`), configuração (`ConfigApp`), modal `NoticeScreen`, o tour do `gitpr demo` (`src/ui/demo/`) e o assistente de migração do ledger (`src/ui/metrics_migration_app.py`).
* **Arquitetura em Camadas:** `src/domain/` (regra pura, sem I/O) + `src/application/use_cases/` (orquestração, **15 casos de uso**) + apresentação (CLI/TUI). **9 pacotes de domínio**: `baseline`, `check`, `finding`, `linter`, `mentor`, `policy`, `pr`, `risk`, `tests_generation`.
* **Extensão de Editor:** `extensions/vscode/` — cliente TypeScript fino do MCP para **VS Code e Cursor** (Node.js 20+, `@modelcontextprotocol/sdk`, VSIX). Não contém regra de negócio.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API, tokens GitHub e tokens SCM das forges.
* **Configuração:** `python-dotenv`, `pyyaml` (linter estático) + schema declarativo próprio (`src/config_schema.py`, **80 `ConfigField`** e **16 categorias**).
* **IA Providers:** Integração via SDK oficial do Google GenAI, OpenAI SDK (DeepSeek) e OpenAI SDK (Ollama local). Defaults configurados: `gemini-pro-latest` / `gemini-flash-lite-latest` e `deepseek-v4-pro` / `deepseek-v4-flash`.
* **Forge APIs:** `requests` (REST) — abstração multi-forge em `src/infrastructure/scm/` (GitHub, GitLab, Bitbucket, Azure DevOps) + `web_links.py`; `src/github_api.py` mantido como shim deprecado.
* **Linter / SAST:** regex YAML + bridge Checkstyle + ruleset de segredos embutido (`src/security_ruleset.py`) + 4 bridges em `src/infrastructure/linter/external/` (base + Semgrep, Gitleaks, Bandit), com modelo normalizado em `src/domain/linter/sast_finding_mapper.py` e o achado canônico em `src/domain/finding/`.
* **Infraestrutura de CI:** `src/infrastructure/ci/` — `sarif_builder.py` (SARIF 2.1.0), `junit_builder.py` (JUnit XML) e `masking.py` (mascaramento de credenciais antes de serializar qualquer artefato).
* **Git Internals:** `src/infrastructure/git/` — `patch_applier.py`, `selective_stager.py`, `identity.py`, `risk_history_reader.py` e `test_matcher.py`.
* **Persistência local:** `src/ledger.py` — SQLite (`~/.gitpr/metrics/telemetry.db`) com WAL, `PRAGMA user_version`, chaves UUID e transporte por bundle.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 — **18 ferramentas anotadas**, **19 recursos**, 7 prompts.
* **Testes:** Pytest + `unittest.mock` (**140 módulos de teste** 🆕 — 53 na raiz, 12 em `tests/application/use_cases/`, 10 em `tests/fix/`, 9 em `tests/scm/`, 7 em `tests/badge/`, 6 em `tests/demo/`, 6 em `tests/split/`, 5 em `tests/domain/baseline/`, 4 em `tests/domain/policy/`, 4 em `tests/review/`, 4 em `tests/infrastructure/linter/external/`, 3 em `tests/domain/check/`, 3 em `tests/infrastructure/ci/`, 2 em `tests/domain/risk/`, 2 em `tests/domain/tests_generation/`, 2 em `tests/integration/`, 2 em `tests/infrastructure/git/`, 2 em `tests/domain/linter/`, 1 em `tests/domain/finding/`, 1 em `tests/domain/mentor/`, 1 em `tests/domain/pr/`, 1 em `tests/infrastructure/baseline/` —, **2964 cenários coletados** 🆕) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio) + fixtures de repositório git real (`tests/fix/`, `tests/split/`, `tests/test_full_diff_encoding.py` 🆕) + guarda de isolamento de rede (`tests/demo/conftest.py`, `tests/integration/conftest.py`). A extensão tem suíte Mocha própria (7 testes contra o servidor MCP real).
* **Empacotamento:** setuptools/build (PyPI) — `version = {attr = "src.updater.__version__"}`; packs embutidos via `package-data`; `packaging>=23.0`. A extensão é empacotada à parte (`vsce package`, VSIX).
* **CI/CD:** GitHub Actions — `pr-review.yml` + `action.yml` (chama `gitpr check`) + `tests.yml` (matriz Python 3.10/3.13) + `extension.yml` (build, teste e empacotamento do VSIX; publicação no Marketplace/Open VSX em tags `ext-v*`).

---

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa ~90k tokens, divide automaticamente em lotes por arquivo (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce). Suporta PRs, commits e Issues. O `provider`/`model` são agregados entre os chunks e o `meta`/`modules` são repassados a `log_command_metric`.
* **Tokenizador Local:** `tokenizer.json` para estimativa precisa de tokens antes do envio para a IA.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()` com fallback para tokenizador local.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff`.
* **`get_split_diff()`:** Diff próprio do `split`, com `SPLIT_DIFF_ARGS` (`--binary -M -U3`), **deliberadamente sem** reusar `get_git_diff()`.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo em JSON antes de cada chamada à IA.
* **Smart Excludes com Duas Camadas:** Camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`), mescladas em runtime. Auto-seeding do arquivo local na primeira execução. `_load_smart_excludes()` aceita `force=`.
* **Métricas com Rastreamento de Tempo:** `log_command_metric()` em todos os fluxos, com `meta`, `modules` e `duration_ms`.
* **Resolução Centralizada de Output:** `resolve_output_path()` — default em `.gitpr/reports/{type}/`.
* **Wizard SCM (`run_scm_init_wizard()`)**: `gitpr --init` — detecta a forge pelo remote origin, solicita extras por forge, valida o token e persiste **somente em sucesso**.
* **Skill Template de Release (`ensure_release_skill_template()`)**: Baixa `templates/gitpr.release.*.md` no primeiro uso de `gitpr release`.
* **Guarda de Skill Corrompido:** `_CORRUPTED_PR_SKILL_ARTIFACT` documenta o fragmento JSON que vazou para o template `pt_br`, e `get_skill_context()` o remove **em memória** quando `action_type == "pr"`.
* **Registro de Skills Compartilhado:** `SKILL_FILES_BY_TYPE` / `SKILL_TYPES` / `DEFAULT_SKILL_TYPE` em `src/config.py`.
* **Motor de Review com Escopo de Cache (`generate_pr_content`):** `cache_scope` e `store_diff`; o `cache_scope` carrega também o pack de política ativo.
* **Trailer de Coautoria:** `COAUTHOR_TRAILER` + `append_coauthor_trailer()` — idempotente, preserva trailers de terceiros.
* **🆕 Captura de Saída do Git Endurecida:** as **10** chamadas de `subprocess.run` em `src/cache.py`, `src/core.py`, `src/issue_engine.py` e `src/main.py` que capturam saída do git (`git config`, `git remote -v`, `git diff`, `git log`, `merge-base`, `symbolic-ref`) passaram a usar `encoding="utf-8"` **com** `errors="replace"`. Antes, um único byte Latin-1 (`0xFA`) matava a thread de leitura no Python 3.13/Windows, `stdout` voltava `None` **sem levantar exceção** e o run anunciava "No new code found". `get_git_full_diff()` ganhou o `text=True` que faltava, e o `git fetch origin` saiu do modo bytes — a mensagem de erro deixou de renderizar como `b'...'`.
* **🆕 Falha de Git ≠ Diff Vazio:** o guarda de diff em `src/main.py` foi dividido em dois caminhos. `diff_text is None` (o git falhou: repositório ausente, remote quebrado, erro de autenticação) agora **encerra com código 1**; um diff vazio ou só com espaços continua saindo **0** com o aviso "No new code found". No modo `--hook`, o caminho é **fail-open** (`return` em vez de `sys.exit(1)`), porque um `prepare-commit-msg` não-zero abortaria o commit do usuário.
* **Subprocessos Blindados:** `stdin=subprocess.DEVNULL` + `encoding='utf-8'`/`errors='replace'` em todos os `subprocess.run`; verificação de conexão via socket antes de operações de rede.

### **2. Sistema de Plugins Global (`src/plugins.py`)**

* **Arquitetura de Plugins:** Carrega plugins de `~/.gitpr/plugins/` aplicando-se a **todos os projetos**.
* **Plugins de Linter (`linter/`):** Arquivos `.yml` mesclados com o `.gitpr.linter.yml` local.
* **Plugins de Prompt MCP (`prompts/`):** Arquivos `.md` que estendem o contexto do sistema.
* **Factory Closures:** `get_linter_plugins` e `get_prompt_plugins` isolam estado entre sessões.
* **Comando `--plugins`:** Lista todos os plugins globais instalados com tipos e paths.
* **Documentação Multilíngue:** `docs/plugins-system.md` em 5 idiomas.
* **Relação com os Policy Packs:** o pack é uma **terceira** camada de regras — plugins são da máquina, o `.gitpr.linter.yml` é do projeto e o pack é versionado e commitado.

### **3. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria `~/.gitpr/` e solicita interativamente chaves, preferências e idioma.
* **Routing de Comandos:** Gerencia todas as flags e os **15 subcomandos** — `release`, `config`, `fix`, `review-pr`, `demo`, `badge`, `split`, `tests`, `explain`, `mentor`, `metrics`, `policy`, `risk`, `baseline` e `check`.
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags (32 opções Click na raiz — inalteradas nesta janela):** `--mentor`, `--explain`, `--init`, `--no-suggest-reviewers`, `--no-publish`, `--no-edit`, `--base <branch>`, `--plugins`, `--status`, `--no-unstaged-check`, `--linter-setup`, `--version` etc.
* **Subcomando `check` — 8 opções:** `--base <ref>`, `--format sarif|json|junit`, `-o/--output <path>`, `--fail-on …`, `--no-ia`, `--ia-only-high-risk`, `--baseline <path>` e `--policy <name>@<version>`.
* **Grupo `baseline` — 6 subcomandos:** `create`, `show`, `validate`, `update`, `suppress` e `unsuppress`.
* **Grupo `policy` — 7 subcomandos:** `list`, `show`, `validate`, `use`, `off`, `install` e `init`.
* **Grupo `metrics` — 8 subcomandos:** `export`, `bundle`, `merge`, `dashboard`, `migrate`, `prune`, `purge` e o oculto `hook-event`.
* **Subcomando `risk` — 4 opções:** `--file`, `--format text|json`, `--base`, `--no-history`.
* **Subcomando `mentor` — 2 opções:** `--finding`, `--provider`.
* **Variáveis de Ambiente (58 chaves no `DEFAULT_CONFIG`):** as quatro `GITPR_BASELINE_*`, as duas de mentor, as duas de policy e `GITPR_RISK_INCLUDE_IN_REVIEW`. **Fora do `DEFAULT_CONFIG`:** `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT`, `GITPR_METRICS_CURRENCY` e as **9 `GITPR_CHECK_*`**.
* **🆕 Ajuda Contextual Consertada:** `gitpr -h --explain` voltou a renderizar — a opção usava dest `explain_flag` enquanto o `HELP_MAP` procurava a chave `explain`. O `HELP_MAP["explain"]` e o `HELP_PRIORITY["explain"]` passaram a apontar para `docs/explain-pr`, e `gitpr tests` e `gitpr tests generate` ganharam `epilog=` próprio com link para `docs/tests-generate` no idioma corrente.
* **Camada de escrita do `.env`:** `read_env_file_values()` lê **só o arquivo** via `dotenv_values`; `save_config_values()` com `set_key`; `remove_config_value()` com `unset_key`.
* **Portão de Baseline no Fluxo:** `main.py` resolve o gate de baseline antes de lint, review, full review, auditoria de arquivo, review remoto e risk.
* **Publicação Direta Refatorada:** `_publish_pr_directly` (`--no-edit`) delega ao **`publish_pull_request_use_case`** — o mesmo caminho do tool MCP `publish_pull_request`.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI para revisar, editar e publicar Pull Requests direto no terminal.
* **7 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen` e `NoticeScreen`.
* **Selo no Corpo do PR:** `attach_pr_badge()` roda em `src/main.py` logo após `pr_data` estar completo — **ponto único de injeção**.
* **`_attach_reviewers` com resolução:** Resolve o que o usuário digitou **antes** de enviar, reporta o descartado e, num `422` de lote, **repete um a um**.
* **Suggested Reviewers:** Consulta a forge por revisores sugeridos; `_reviewer_suggestion_view()` monta `resolutions` via `resolve_candidates`.
* **Bindings:** F1 (Help), F2 (Salvar .md local), F3 (Publicar via forge), Esc (Sair).
* **Fluxo de Auto-Commit:** Linter → mensagem IA → confirma → commita → push → publica PR.
* **Modal de Progresso no Merge:** `CommitProgressScreen` com `title` opcional e `mark_finished(show_close=False)`; sucesso exibe `✅ PR #N merged successfully!`, conflito e erro inesperado passam pelo `_on_merge_failure`.
* **Tratamento de PR Existente / Auto-Upstream / Merge Flow** — inalterados (`GITPR_AUTO_MERGE`).

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Shim Deprecado:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` e demais funções delegam a `src/infrastructure/scm/github_provider.py`; emite `DeprecationWarning` e mantém as tuplas legadas `(ok, data, status)` — nenhum código novo pode importá-lo.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no diff sem gastar cotas de IA.
* **Regras YAML:** Lê `.gitpr.linter.yml` (criado via `--skill`).
* **Plugins de Linter:** Regras adicionais de `~/.gitpr/plugins/linter/*.yml`.
* **Wildcard de Extensão:** `extensions: ["*"]` significa **todo** arquivo, inclusive os sem sufixo e dotfiles.
* **Ruleset de Segredos Embutido:** `load_linter_rules()` mescla `src/security_ruleset.py` **depois** das regras do projeto e dos plugins. Sete regras, todas `extensions: ["*"]`: cinco `error` e duas `warning`. O alerta **nunca ecoa o valor**.
* **Camada de Policy Pack:** `load_linter_rules()` aplica o merge em camadas do pack ativo e **sobrescreve severidades**.
* **Achados Estruturados (`findings_out`):** além das strings de alerta, o motor devolve os achados normalizados do tipo canônico `src/domain/finding/`.
* **Bridges SAST Opt-In:** Semgrep, Gitleaks e Bandit rodam no caminho de arquivo inteiro **e** no de diff, com dedup `[Gitleaks + Regex]`, mascaramento de valor (`AKIA****`) e aviso quando a ferramenta está habilitada mas fora do `PATH`.
* **`skip_external`:** `parse_diff_and_lint(..., skip_external=True)` no fluxo remoto.
* **Relatório Consolidado:** `generate_linter_report_content()` consolida erros regex + externos em `.gitpr/reports/linter/` — gerado apenas quando há violações.
* **Baseline-aware:** os alertas são anotados com o status do baseline antes de virarem relatório.

### **7. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera a chave mestra `secret.key` em `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data`/`decrypt_data` para chaves de IA, GitHub PAT e tokens SCM das forges.
* **Validação Multi-Forge:** `validate_or_request_scm_token(provider, repo_display)` — 401 → loop de reautenticação preservando o rascunho.
* **Segredos na TUI de Configuração:** Campos `KIND_SECRET` são editados mascarados, **nunca** exibem o valor em claro e são cifrados com Fernet antes de gravar.
* **Varredura de Segredos no Fluxo:** O linter — que roda no pre-commit hook — é um portão de credenciais com regras idênticas em toda máquina.
* **Mascaramento na CI:** `src/infrastructure/ci/masking.py` remove chaves privadas, AWS access key ID/secret, tokens GitHub, Google, OpenAI, Slack, `Bearer`, basic-auth em URL e atribuições genéricas de senha **antes** de o artefato ser serializado. A extensão tem um espelho em TypeScript (`masking.ts`).
* ⚠️ **Lacunas de cobertura confirmadas como ainda abertas:** a regra genérica ainda exige aspas após o separador, então `API_KEY=abc123` continua não sendo pego; os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-` continuam fora do ruleset **do linter**; e não há fronteira à esquerda no nome da chave.

### **8. Auto-Updater (`src/updater.py`)**

* **PyPI como Fonte Única:** `get_latest_remote_version()` consulta `https://pypi.org/pypi/gitpr-cli/json` e grava o cache diário.
* **Portão Obrigatório (`enforce_update_required()`):** Devolve `True` (após imprimir as duas versões e o comando pip) quando a versão publicada é mais nova; `False` quando está atualizado, quando a versão remota é **desconhecida (offline)** ou quando a checagem está desligada.
* **`check_and_update()`:** Só consulta e **informa**, nunca instala.
* **Escape Hatch:** `GITPR_SKIP_UPDATE_CHECK` — não é advertised; existe para a suíte e automação offline.
* **Versionamento Centralizado:** `__version__` (**1.4.2** 🆕), `__lang_version__` (**v0.0.35**), `__scripts_version__` (**v0.0.4**), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`.
* **🆕 Estado do release:** os dois releases pendentes foram fechados. A tag **`v1.4.1`** aponta para o merge do PR #218 (2026-10-18) e a **`v1.4.2`** para o merge do PR #222 (2026-10-27); o `CHANGELOG.md` tem as seções `[1.4.1]` e `[1.4.2]` **commitadas**, e o PyPI serve **1.4.2**. `v1.4.0` deixou de ser a última tag.

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Histórico de mensagens, input multi-linha, barra de status com bindings visíveis. `ENABLE_COMMAND_PALETTE = False`.
* **Memória por Branch (`src/chat_memory.py`):** Histórico persistido por branch, com continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear`. O `/tests` (e os aliases localizados) delega ao **mesmo caso de uso** que o CLI usa.
* **Auto-Patching (F5), Atualização de Diff (F2), Exportação de Sessão (F6).**
* **Extrator Compartilhado:** F5 e `ctrl+s` chamam `patch_extractor.extract_code_blocks()` — comportamento visível idêntico, sem lógica duplicada.

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta o idioma do SO na primeira execução e salva em `GITPR_LANG`; o diretório do perfil é criado **antes** de persistir.
* **5 Idiomas, 6 Dicionários:** en_us (padrão/fallback), pt_br, pt_pt, es/es_es, fr/fr_fr.
* **Arquivos Versionados:** `__lang_version__` (**v0.0.35**) controla a atualização dos pacotes (`langs/*.json`).
* **Cobertura — dívida inalterada nesta janela:** **1620 chaves** em `pt_br`, `pt_pt`, `es_es` e `fr_fr`, mas **1618** em `es.json` e `fr.json`. O código usa **1626** chaves: **8 não existem em nenhum dicionário** (mensagens de `publish_pull_request` e descrições das tools MCP `run_check`/`publish_pull_request`) e **2 chaves antigas ficaram órfãs** (as duas mensagens de publicação de PR). ❌
* **Snapshot de Ambiente (`AMBIENT_ENV_KEYS`):** `frozenset(os.environ)` capturado **imediatamente antes** do `load_dotenv()` de módulo.
* **Cache com Indexação por Idioma:** As respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.
* **Fonte de Tradução em Lockstep:** uma chave nova precisa existir no código, em `langs/pt_br.json` (lista mestra), nos dicts FR/ES de `scripts/sync_all_langs.py` e nos valores curados de `scripts/fix_mangled_i18n_keys.py`.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA com caracteres braille e palavras de "pensamento".
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas. `_load_thinking_words()` / `reload_thinking_words()` aceitam `force=`.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini, DeepSeek e Ollama (local), com primário/secundário por provedor.
* **Modo JSON & Parâmetros Determinísticos:** `temperature=0.0` e `top_p=0.1`; fallback automático entre provedores configurados.
* **Timeout de IA:** default de **180s** (`GITPR_AI_TIMEOUT`).
* **Chamadas com `quiet`:** o release e as features novas encaminham `quiet` até a camada de IA, para que o spinner nunca corrompa uma saída `--format json`.
* **Uma chamada por vez, com cache:** mentor e explain reusam o cache MD5 por prompt.
* **🆕 Payload Já Parseado:** `parse_explain_payload()` e `generate_test_file` passaram a aceitar o **dict** que o provider entrega (antes chamavam `json.loads()` num dict, o que levantava `TypeError` e, na sequência, `AttributeError` em `.strip()`); o caminho de string JSON crua continua aceito para respostas antigas do cache.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt, com indexação por idioma.
* **Seleção do Último Review (`resolve_last_review()`):** Escolhe o registro `review`/`fullreview` **mais novo** para um par repo+branch — é a porta de entrada do `gitpr fix` e do `gitpr mentor`.
* **Diff Revisado (`reviewed_diff`):** Campo no topo do registro que guarda o diff efetivamente revisado.
* **Telemetria e Duração:** Persistência de `duration_ms` e `meta_raw`.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` é **ponte de pré-migração**.
* **Efeito da Sanitização de Skill:** como `get_skill_context()` remove o fragmento corrompido do prompt de PR, a chave MD5 muda e respostas antigas contaminadas não são reutilizadas.
* **🆕 `git config` Decodificado com Segurança:** as leituras de `user.name`/`user.email` passaram a usar `encoding="utf-8"` + `errors="replace"`.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`) e Arqueologia por Blame (`-b`).
* **Publicação Multi-Forge:** F3 cria a issue na forge **configurada** (`GITPR_SCM_PROVIDER`) via `provider.create_issue` — Azure DevOps levanta `ScmNotSupportedError`.
* **Map-Reduce para Issues:** Contexto acima de ~90k tokens é dividido e unificado.
* **Tratamento de 401:** Sinalização de reautenticação sem fechar a aplicação.
* **🆕 `git remote -v` Decodificado com Segurança:** a chamada usa `encoding="utf-8"` + `errors="replace"`, fechando o último caminho que podia derrubar a leitura da saída do git.

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia evolução e autoria histórica com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos via `log_blame_metric()` com profundidade e número de commits analisados.
* **Agora também alimenta o risco:** o leitor de histórico do score (`risk_history_reader.py`) usa a mesma janela de 90 dias e classifica bugs/reverts por padrão, sem chamar IA.

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)**

* **18 Ferramentas MCP Anotadas:** `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`, `list_fix_candidates`, `review_remote_pr`, `get_baseline_status`, `get_usage_metrics`, `run_check` e `publish_pull_request`.
* **Parâmetros Opt-In no Contrato:** `review_code` e `full_review` aceitam `mentor: bool = False`; `generate_pr_description` aceita `explain: bool = False`. São **puramente por parâmetro** — nunca fazem OR com os defaults do `.env`.
* **19 Recursos + 7 Prompts Templatizados:** `skill://list` + `skill://{pr,commit,review,filereview,issue,blame,release,fix}` + `linter://config` + `baseline://summary` + `prompt://list` + 7 prompts.
* **Registro de Skills Alinhado:** `mcp_server.SKILL_FILES` tem **11 entradas** (`tests`, `explain` e `mentor` incluídos); `TestSkillRegistryAgreement` passa.
* **Invocação CLI Direta:** `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool sem iniciar o servidor stdio; `gitpr-mcp --list` imprime o registry completo como JSON.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve no `sys.__stdout__` original, com fallback para `buffer` ou re-encode com `errors='replace'` em code pages legadas do Windows.
* **Offload do Event Loop:** Decorator `_offload` (`anyio.to_thread.run_sync`) em todas as tools — a ordem dos decorators importa (`@mcp.tool` **acima** de `@_offload`).
* **Falhas como Erro Estruturado:** as tools novas devolvem falha **como dado** em vez de levantar.
* **Métricas MCP:** `run_check` e `publish_pull_request` gravam linhas locais (`mcp:check`, `mcp:publish_pr`).

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório:** Rótulo `📁 Repository: owner/repo` e filtragem estrita por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com `ProgressBar`; os testes aguardam `workers.wait_for_complete()` antes de asseverar.
* **Leitura do Ledger:** o dashboard consulta o `telemetry.db` na thread de trabalho, renderizando as cinco seções (custo, qualidade, módulos, provedores, ciclo) a partir dos mesmos renderizadores que o CLI usa.
* **Assistente de Migração (`src/ui/metrics_migration_app.py`):** oferece importar os arquivos legados, importar **e** reconstruir a partir do cache de IA, ou "agora não".
* **Exportação Local:** CSV/JSON em `./.gitpr/metrics/export/` — `.gitpr/metrics/` está no `.gitignore`, mas os **34 artefatos já rastreados continuam rastreados** (gitignore não destrackeia).

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Reescrito na janela v0.0.17 — ver §36.** `src/metrics.py` opera sobre **linhas do ledger**.
* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`, resolvido por `src/infrastructure/git/identity.py`.
* **Eventos de Hook, Linter e Blame:** `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()`. O `gitpr check` grava `command="check"` com `findings_total`/`findings_errors` e exit code.
* **Exportação e Limpeza:** `gitpr metrics export` (CSV/JSON), `prune`, `purge` com confirmação interativa, `bundle`/`merge` para transportar e fundir janelas.

### **19. Sincronização de Idiomas dos Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (**v0.0.4**, inalterada).
* **Templates reescritos na janela v0.0.17:** `post-checkout`, `post-merge` e `pre-push` chamam `gitpr --quiet metrics hook-event <nome>`, guardados por `command -v gitpr` e `|| true`.
* **Mapeamento de Sufixos (`HOOK_SCRIPT_SUFFIXES`):** Códigos de interface (`es_es`, `fr_fr`) traduzidos para os sufixos publicados (`.es`, `.fr`).
* **Escolha vs. Estado (`SCRIPTS_LANG` / `SCRIPTS_INSTALLED_LANG`):** Permite **detectar a troca de idioma**.
* **`effective_hook_lang()`:** Resolve o idioma efetivo; `--lang` deixou de ser descartado nesse caminho.
* **Skip de Merge-Source:** O `prepare-commit-msg` pula as fontes `message|merge|squash|commit`.

### **20. Bridge de Linters Externos e Assistente Interativo (`src/linter_wizard.py`, `src/ui/linter_app.py`)**

* **Assistente `--linter-setup`:** Wizard com presets numerados (PHP_CodeSniffer, ESLint, Stylelint) e injeção do bloco `external_linters`.
* **Presets Remotos:** `templates/gitpr.linter-presets.json` com cadeia local → download → stale → fallback embutido.
* **TUI de Erros do Linter:** `src/ui/linter_app.py` (Textual) exibe erros críticos e warnings; em hook/quiet imprime e faz `sys.exit(1)`.
* **Relatório Markdown:** Consolidado em `.gitpr/reports/linter/` apenas quando há violações.
* **A Camada SAST é irmã, não substituta:** os bridges Semgrep/Gitleaks/Bandit alimentam o **mesmo** pipeline de relatório — e agora também o `gitpr check`.

### **21. SCM Multi-Forge (`src/infrastructure/scm/`)**

* **Abstração Única (`ScmProvider` ABC):** `base.py` define o contrato (dataclasses `RepoRef`, `PullRequestDraft` etc. e `ScmProviderError(provider, http_status, message)` — `http_status` 0 = falha de rede).
* **Registry e Factory:** `resolve_scm_provider()` seleciona por `GITPR_SCM_PROVIDER` (default `github`); `detect_provider_from_remote()` identifica a forge pela URL do origin.
* **`list_pull_requests(repo, state, since, until)` — paginado e canônico:** os quatro provedores traduzem os estados canônicos (`open`/`merged`/`closed`/`all`) para o vocabulário nativo, paginam no cursor de cada API e filtram por janela inclusiva de datas.
* **Por que o filtro é por data do estado:** três das quatro forges devolvem algo mais largo para um PR mergeado, então cada uma filtra a própria resposta contra a data que o estado implica.
* **`supports_merged_dates`:** atributo de classe, `False` no Bitbucket Cloud, que publica **vazio** o `merged_at`.
* **`web_links.py`:** funções puras (`repo_web_base`, `commit_url`, `pull_request_url`, `user_url`) normalizam qualquer formato de remote.
* **`get_pull_request(repo, pr_id)` — método concreto da ABC:** default levanta `ScmNotSupportedError` e cada forge implementa.
* **Cabeçalhos do GitLab Sintetizados:** `changes[].diff` é um hunk solto; `old_path`/`new_path` montam os cabeçalhos `diff --git a/… / --- / +++`, honrando `/dev/null`. E `overflow: true` **levanta** em vez de revisar metade de um diff truncado.
* **`request_pull_request_reviewers` devolve `list[str]` (quebra de contrato):** Devolve os logins **efetivamente anexados**, lidos do corpo do `201`. Subclasses de terceiros precisam ser atualizadas — **item herdado, ainda sem documentação.**
* **Helpers Read-Only do GitHub:** `get_commit_author_login` e `get_user_login`.
* **Fail-Fast por Forge:** Azure exige `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`; Bitbucket exige `GITPR_SCM_USERNAME`; `create_issue` no Azure levanta `ScmNotSupportedError`.
* **Publicação de Releases:** `provider.create_release()` usado pelo `gitpr release --publish`.
* **Publicação de PR Compartilhada:** `src/application/use_cases/publish_pull_request.py`, usado pelo `--no-edit` e pelo tool MCP. Valida título/corpo, exige `provider.token`, opcionalmente verifica PR existente e branch não empurrada, mascara mensagens de erro e devolve `PublishPrOutcome`.
* **Artefatos:** Glossário + ADR-001/ADR-005; família `docs/scm-multiforge.*.md` em 5 idiomas; 9 arquivos de teste, **307 cenários**.

### **22. Subcomando `gitpr release` — Changelog / Release Notes (`src/release_engine.py`)**

* **Fluxo:** `git log` entre `--since` e `HEAD` → classificação por Conventional Commits → bump semântico sugerido → montagem do changelog → resumo executivo de IA opcional → *prepend* no `CHANGELOG.md`.
* **O Range Deixou de Vir do `git describe`:** a origem do range é a **seção anterior do próprio changelog**, por dois âncoras: o hash mais novo daquela seção e, como fallback, a tag da versão da seção.
* **`_drop_released()` — a segunda linha de defesa:** qualquer commit cujo hash curto apareça em **outra** seção de versão é descartado, com contagem.
* **Todo bullet virou link:** `- {subject} ([{short_hash}]({commit_url})) — {scope} · [#{n}]({pr_url}) · {YYYY-MM-DD}`.
* **A falha de PR mergeado por merge commit:** uma segunda passada (`git log --merges`) monta `hash → PR` pela ancestralidade.
* **Contribuidores resolvidos pela mesma escada dos revisores:** `get_commit_author_login` primeiro, depois `email_to_handle`, com cache em `~/.gitpr/cache/contributors.json`.
* **A Fronteira da Seção Era um Bug Latente:** `upsert_changelog(force=True)` substitui da linha `## [x.y.z]` até o próximo cabeçalho de **nível 2**.
* **Classificador (`src/commit_classifier.py`)** e **Builder com Seções Traduzíveis (`src/changelog_builder.py`)**.
* **Bump Semântico (`src/version_bump.py`)** e **Publicação** (`--publish`, `--draft`, `--format markdown|json`, `--force`). **6 opções no subcomando.**
* **🆕 Estado do release:** a seção `[1.4.1]` está commitada desde `fafe24b` e a `[1.4.2]` desde `4d980e2`; as tags `v1.4.1` e `v1.4.2` existem e o PyPI serve **1.4.2**. **A dívida do relatório anterior está fechada.**
* **Artefatos:** `docs/release-notes.*.md` em 5 idiomas, ADR e `tests/test_web_links.py`.

### **23. Subcomando `gitpr config` — TUI de Configuração**

* **Tela Master-Detail (`src/ui/config_app.py`):** Categorias à esquerda, campos à direita, editados inline. Cabeçalho com busca (`/`) e contador de pendências; rodapé `F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc`. `ENABLE_COMMAND_PALETTE = False`.
* **Schema Declarativo (`src/config_schema.py`) — a fonte única de verdade:** **16 categorias** e **80 `ConfigField`**, dos quais **8 avançados**. As 9 `GITPR_CHECK_*` ainda **não** estão no schema.
* **Categorias `policy` e `baseline`:** os campos de pack e os quatro do baseline.
* **Seção Skills Alinhada:** `SKILL_LABELS` tem **11 entradas** (`tests`, `explain`, `mentor`).
* **Filtragem por Contexto (`show_if`):** `GEMINI_*`/`DEEPSEEK_*`/`OLLAMA_*` conforme o `DEFAULT_AI_PROVIDER`; `GITPR_SCM_USERNAME` sob `[Bitbucket]`; `GITPR_SCM_ORGANIZATION`/`PROJECT` sob `[Azure DevOps]`.
* **Busca Global (`/`):** Casa chave ou rótulo em todas as categorias e **ignora o filtro de visibilidade**.
* **Validação em Duas Camadas:** **Offline** bloqueia o `F2` com erro inline; **online** (só credenciais alteradas na sessão) roda em worker com timeout de 10s e só bloqueia em `401`/`403`.
* **Restaurar (`Ctrl+R`):** Remove a linha do `.env` em vez de reescrever o default; `Esc` com pendências pede confirmação.
* **Seção Skills — a única project-scoped:** Edita `.gitpr/skill/*.md` do projeto resolvidos a partir do diretório de chamada, gravando atomicamente e preservando CRLF/LF.
* **Downloads com Força:** Botões que forçam re-download de smart-excludes, traduções, presets e thinking words via `force=`.
* **Módulo de Links Leve (`src/doc_links.py`):** `doc_url()` saiu de `core.py` para a UI obter o link sem importar SDKs de IA.
* **Testes:** 5 arquivos — `test_config_app.py` (78), `test_config_schema.py` (42), `test_config_validation.py` (40), `test_config_store.py` (22), `test_config_cli.py` (9).
* **Dívida conhecida:** `gitpr -h config` abre a TUI e ignora o `-h` — o gate `if ctx.invoked_subcommand is not None: return` (main.py:678) roda antes do bloco de `help_flag`.

### **24. Log Geral de Uso (`src/usage_log.py`)**

* **Uma Linha por Comando:** Grava `~/.gitpr/logs/<uuid5>.log`, **um arquivo por dia**, com comando, argumentos, repositório, usuário e timestamp.
* **Nome Derivado da Data:** `uuid5(NAMESPACE_DNS, f"gitpr.usage.{YYYY-MM-DD}")`.
* **Escrita Síncrona (decisão explícita):** Diferente de `log_local_metric`, que usava thread daemon e perdia a gravação se o processo saísse antes.
* **Nunca Imprime:** O servidor MCP reserva o stdout para JSON-RPC; o módulo também nunca levanta exceção.
* **Um Único Spawn de Git:** `git config --get-regexp '^(remote\.origin\.url|user\.name|user\.email)$'` — ~40 ms em vez de ~150 ms no Windows, em *toda* execução.
* **Controle:** `GITPR_SHOW_LOGS` (default `"true"`); desligado em `tests/conftest.py`.
* **Artefatos:** `docs/usage-log.*.md` em 5 idiomas; `tests/test_usage_log.py` (27 cenários).

### **25. Subcomando `gitpr fix` — Achados de Review como Patches Revisáveis (`src/fix/`)**

* **O Pipeline Real:** último review do cache (`resolve_last_review`) → **uma** chamada de IA → extração e validação de diff unificado → `git apply --check` → classificação determinística → dry run ou escrita → histórico.
* **Pacote de 8 arquivos:** `patch_provenance.py`, `patch_extractor.py` (compartilhado com o chat), `patch_safety_classifier.py` (puro, sem I/O), `patch_applier.py` (shim), `fix_history.py`, `apply_fix.py`, `rollback_fix.py`, `__init__.py`.
* **Classificação Determinística:** Recusa patch que atravesse mais de um arquivo ou hunk, toque caminho sensível, estoure o orçamento de linhas, **apague uma linha com cara de chamada**, venha marcado de baixa confiança ou falhe no `git apply --check`. O `--force` **nunca** contorna a aplicabilidade, só a classificação.
* **Escrita Opt-In:** Dry run é o default; qualquer mutação exige `--apply` (ou frase digitada com `--force`).
* **Testes:** 10 arquivos em `tests/fix/` (**204 cenários**) com fixtures de repositório git real.

### **26. Subcomando `gitpr review-pr` — Review de PR Remoto (`src/review/`)**

* **O que é:** Orquestração, **não** um segundo motor de review — o motor existente, o linter e o renderizador alimentados com um diff que veio de outro lugar.
* **Pacote de 5 arquivos:** `diff_source.py`, `diff_normalizer.py`, `render.py`, `remote_pr.py`, `__init__.py`.
* **Read-Only por Default:** `--post-comment` é o **único** caminho que escreve na forge. A tool MCP `review_remote_pr` sequer recebe o argumento.
* **O baseline é resolvido antes da primeira chamada de rede**, e os avisos do gate são mesclados ao relatório/comentário.
* **`render.py` ganhou o parâmetro do risco:** `compose_review_content` / `render_review_result` **antepõem** a seção `⚡ Risk Assessment` acima dos alertas do linter, quando `GITPR_RISK_INCLUDE_IN_REVIEW` está ligado.
* **Artefatos:** `docs/review-pr.md` + `.pt_br.md` (os 3 idiomas restantes **continuam pendentes**), `docs/code-review-ia.*.md` (5), ADR-005 e `glossary-review-pr.md`.
* **Testes:** 4 arquivos em `tests/review/` (**97 cenários**).

### **27. Resolução de Identidade do Revisor (`src/reviewer_resolution.py`)**

* **O Bug (duas falhas silenciosas encadeadas):** (1) **Prefill vazio** — `handles` só com `email_to_handle()`; (2) **Attach não verificado** — valores repassados *verbatim*, o GitHub respondia **201 sem anexar ninguém** e o `_request()` retornava sem levantar.
* **Módulo:** Plano, sem I/O próprio, **que nunca levanta**. `resolve_candidates()` (antes da TUI) e `resolve_typed_reviewers()` (no attach); `match_candidate()` casa exato e normalizado por login, nome ou e-mail.
* **Escada de Resolução:** handle conhecido (sem requisição) → casamento exato com uma pessoa sugerida → lookup por e-mail → validação do login na forge.
* **O que não resolve nunca é enviado:** Sai em `ResolutionOutcome.dropped` como `(valor, motivo_i18n)` e é descartado com aviso visível.
* **A Mesma Escada Serve ao Release:** o `release_engine` reusa `get_commit_author_login` + `email_to_handle`.
* **Testes:** `tests/test_reviewer_resolution.py` (18) + ampliações em `test_github_provider.py` (72), `test_pr_publish_app.py` (55), `test_suggest_reviewers.py` (17), `test_reviewer_suggestion.py` (18) e `test_main_suggest_reviewers.py` (8).

### **28. Subcomando `gitpr demo` — Tour Guiado sobre Exemplos Gravados (`src/demo/`)**

* **O que é:** Um tour interativo que mostra as três saídas principais do GitPR — mensagem de commit, review e descrição de PR — **sem chave de API, sem repositório git e sem rede**.
* **Pipeline Real, Resposta Falsa:** `FakeAIProvider` espelha `src.ai_providers.call_ai_model` **argumento por argumento**; `demo_pipeline()` faz patch de `src.core` e `src.metrics` para que o pipeline de produção rode **intocado**.
* **Isolamento é Requisito, Não Detalhe:** O tour **não pode** tocar o `~/.gitpr` do usuário nem a rede — garantido por `tests/demo/conftest.py`.
* **Pacote:** `demo_runner.py`, `fake_ai_provider.py`, `scenarios/` (dois exemplos localizados nos 5 idiomas). Os cenários são **módulos Python, não JSON**, para viajarem dentro do wheel.
* **TUI:** `src/ui/demo/` com modal de ajuda; o diff é cercado como ```` ```diff ````.
* **CLI:** `gitpr demo` com `--scenario`, `--lang` e `--no-tui`.
* **Testes:** 6 arquivos em `tests/demo/` (**155 cenários**).
* **Artefatos:** `docs/demo.*.md` em 5 idiomas, `README.*` (5) e as métricas de exemplo do tour.

### **29. Selo GitPR e Comando `gitpr badge` (`src/branding/`)**

* **O que é:** Um selo público que atesta que um pull request passou por uma verificação de qualidade local, e um comando que imprime o snippet de adoção para o README do projeto.
* **URL Estática de Propósito:** É um Markdown do shields.io que o GitPR **nunca** busca — publicar um pull request não pode passar a depender de um terceiro estar no ar.
* **Medição Honesta (`badge_data.py`):** `collect_linter_counts()` devolve `None` quando não há regras de linter configuradas, porque lista vazia significa "nada foi verificado", não "nada foi encontrado".
* **O Selo Nunca Bloqueia um Publish:** Todo caminho de falha é capturado e degrada para "sem selo".
* **Ponto Único de Injeção:** `attach_pr_badge()` em `src/main.py`. Append idempotente por marcador.
* **Comando `gitpr badge`:** `--readme` e `--style`. **Só imprime** — o README nunca é modificado.
* **Configuração:** `GITPR_BADGE` (default `true`) — opt-out **read-only**.
* **Testes:** 7 arquivos em `tests/badge/` (**83 cenários**).
* ⚠️ **As 7 falhas de `tests/badge/test_badge_paths.py` continuam abertas:** o provider falso do teste (`SimpleNamespace(name=..., create_pull_request=...)`) não declara `token`, então o `publish_pull_request_use_case` devolve `auth_required` e `create_pull_request` nunca roda — o `captured["request"]` levanta `KeyError`. **Nada foi corrigido nesta janela.** O comportamento do produto está correto (o provider real sempre carrega o token); o fixture é que precisa de `token="ghp_fake"`.
* **Artefatos:** `docs/badge.*.md` em 5 idiomas e o survey dedicado.

### **30. Subcomando `gitpr split` — Commits Atômicos por Hunk (`src/split/`)**

* **O que é:** Uma árvore de trabalho com vários concerns deixa de virar um commit-blob. O `split` lê o diff não commitado, pede à IA que particione os hunks por **intenção lógica** e propõe um commit atômico por concern. A árvore nunca é reescrita.
* **Pacote de 6 arquivos:** `split_plan.py`, `hunk_parser.py` (puro), `hunk_grouper.py`, `generate_split_plan.py` (read-only), `apply_split_plan.py` (**o único que muta**) e `__init__.py`.
* **A Garantia de Árvore Intacta é Estrutural:** `selective_stager.py` pré-valida **todo** grupo contra um índice temporário em HEAD e usa um `GIT_INDEX_FILE` descartável.
* **Destrutivo para o Índice, Não para a Árvore:** O `--apply` reseta o índice para HEAD antes de stagear.
* **Configuração:** `GITPR_SPLIT_MAX_GROUPS` (5), `GITPR_SPLIT_MAX_HUNKS` (50) e `GITPR_SPLIT_REQUIRE_CONFIRMATION` (`true`). Valores zero ou negativos são **ignorados em favor do default**.
* **Testes:** 6 arquivos em `tests/split/` (**101 cenários**).
* **Artefatos:** `docs/split-command.md` em 5 idiomas, ADR-006, `glossary-gitpr-split.md`, spec/plano e survey.

### **31. Varredura de Segredos Embutida (`src/security_ruleset.py`)**

* **O que é:** Sete regras que rodam em **toda** invocação do linter, mescladas ao fim de `load_linter_rules()` depois das regras do projeto e dos plugins.
* **As Sete Regras:** cinco `error` bloqueantes — AWS access key ID, token GitHub, token Slack, chave de API Google e bloco de chave privada — e duas `warning`: URL de conexão de banco com credenciais e atribuição genérica de credencial, esta atrás de um filtro de placeholder (`changeme`, `xxxxxx`, `example`, `dummy`, `sample`, `your_password_here`, `sua_senha`).
* **Por que no Pacote e Não no Template:** Um portão de segredos precisa se comportar **igual** em toda máquina e em todo CI.
* **Lacunas de Cobertura (v1) — confirmadas ainda abertas:** atribuição **sem aspas** não é pega (`API_KEY=abc123`); faltam os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-`; e não há fronteira à esquerda no nome da chave.
* **Configuração:** `GITPR_LINTER_SECURITY` (default `true`; opt-out fail-open) e `GITPR_LINTER_SECURITY_DISABLED_RULES` (`;`-separadas).
* **Testes:** `tests/test_security_ruleset.py` (**61 cenários**).
* **Artefatos:** ADR-007, `glossary-gitpr-secret-scanning.md`, spec/plano/survey e 3 relatórios de tarefa.

### **32. Bridges SAST — Semgrep, Gitleaks e Bandit (`src/infrastructure/linter/external/`)**

* **O que é:** Uma camada **opt-in** que pluga scanners de segurança de terceiros no pipeline de linter existente.
* **Escopo Bounded:** Rodam **só** quando habilitados e **só** sobre os arquivos tocados pelo diff.
* **Contrato Comum:** `ExternalLinterBridge` (ABC) com execução endurecida de `subprocess` (`shell=False`, timeout estrito, `stdin=DEVNULL`, UTF-8 com `errors='replace'`).
* **Deduplicação é o Ponto:** `deduplicate_secret_findings()` funde achados do Gitleaks e do ruleset regex no mesmo arquivo e linha numa **única** entrada confirmada `[Gitleaks + Regex]`.
* **Segredos Mascarados:** `mask_secret_value()` garante que o valor nunca chegue ao achado, ao log ou à telemetria.
* **Resolução em Três Camadas:** `load_sast_config()` lê defaults → `.gitpr.linter.yml` (bloco `sast`, caindo para `linter.external`) → variáveis `GITPR_SAST_*`. **Todas default `false`**.
* **Degradação Graciosa:** Ferramenta habilitada mas ausente do `PATH` emite aviso e a execução continua.
* **Testes:** 4 arquivos em `tests/infrastructure/linter/external/` (**14 cenários**) + `tests/domain/linter/test_sast_finding_mapper.py` (2) + `tests/domain/linter/test_structured_findings.py` (44).

### **33. Subcomando `gitpr tests generate` — Geração de Suíte por IA (`src/domain/tests_generation/`, `src/application/`)**

* **O que é:** Gera arquivos de teste completos e executáveis a partir do diff atual, de um arquivo específico ou de um achado de review, **respeitando a convenção do repositório** (Pest, PHPUnit, Jest, Vitest, Pytest).
* **Domain Layer:** `TestFramework` (enum) e as dataclasses `TestGenerationTarget`, `TestScaffold`, `GeneratedTest`; `detect_test_framework()` detecta pelos arquivos de configuração, manifests e conteúdo do diretório de testes; `build_test_scaffold()` calcula o caminho convencional de destino por framework.
* **Application Layer (`generate_test_file.py`):** Orquestra detecção, resolução de scaffold, prompt, IA, parsing do JSON e escrita opcional. `validate_test_syntax()` roda o toolchain local (`php -l`, `node --check`, `python -m py_compile`) — falha de validação é **aviso**, não erro.
* **Apresentação:** Grupo `tests` com `generate` (`--file`, `--finding`, `--framework`, `--apply`, `--provider`); dry run é o default e sobrescrever teste existente pede confirmação com **No** pré-selecionado.
* **🆕 Documentado em 5 idiomas:** `docs/tests-generate.*.md` (5 arquivos), com link no `gitpr tests generate` (epilog) e no README. **A dívida do relatório anterior está fechada.**
* **🆕 Dois Defeitos Corrigidos:** o caso de uso passou a aceitar o **dict** já parseado do provider (com fallback para string JSON crua, preservando respostas antigas do cache); e o `--finding` deixou de ler `cand.finding.suggested_test`/`cand.diff` — atributos que não existem — passando a usar `cand.suggested_test`/`cand.diff_unified`.
* **Skill:** `.gitpr.tests.md` em `SKILL_LABELS`, `mcp_server.SKILL_FILES` e `SKILL_FILES_BY_TYPE`.

### **34. Subcomando `gitpr explain` e a Flag `--explain` — Guia do Revisor (`src/domain/pr/`)**

* **O que é:** Um guia centrado em quem vai **revisar** — o que muda, por que muda, onde focar e qual o risco de regressão.
* **Domain Layer (`explain_section_builder.py`):** `PrExplanation` / `ReviewerFocusPoint`, o renderizador `build_explain_markdown()` e `parse_explain_payload()`, que tolera saída não-JSON e **detecta placeholders** `[FILL]`/`[TODO]`.
* **🆕 `parse_explain_payload()` Aceita `dict | str | None`:** o provider entrega o JSON **já parseado**; a função chamava `json.loads()` num dict (`TypeError`) e depois `.strip()` (`AttributeError`). Agora aceita as três formas e normaliza campos `None`.
* **🆕 Branch de Chave Ausente:** `generate_pr_explanation` passou a imprimir o erro padrão de chave faltante e sair com **1**, em vez de estourar exceção.
* **Application Layer (`generate_pr_explanation.py`):** Resolução de provedor, validação da chave, carregamento do skill context (`explain`), prompt, invocação e parsing.
* **Duas Portas de Entrada:** `gitpr explain` (`--provider`, detecção de diff ausente antes de qualquer IA) e a flag `--explain` no CLI raiz. A extensão expõe o mesmo caminho em `GitPR: Generate PR Draft (with Reviewer Guide)`.
* **🆕 `-h --explain` Consertado:** a opção usava dest `explain_flag`, mas o `HELP_MAP` procurava `explain` — a ajuda contextual voltou a renderizar.
* **🆕 Documentado em 5 idiomas:** `docs/explain-pr.*.md` (5 arquivos), com link no `HELP_MAP["explain"]`, no epilog do comando e no README. **A dívida do relatório anterior está fechada.**
* **Configuração:** `GITPR_EXPLAIN_BY_DEFAULT` (default `false`).

### **35. Suíte Determinística e o CI (`.github/workflows/tests.yml`)**

* **O que é:** O workflow que roda a suíte em **Python 3.10** (o piso declarado em `pyproject.toml`) e **3.13**, com `fail-fast: false`.
* **`tests/conftest.py` Hermético:** Pina `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false` e `LANG_VERSION` na versão do código, além de `GITPR_SHOW_LOGS=false` e `GITPR_SKIP_UPDATE_CHECK=true`.
* **Ordem Importa:** `src.updater` é importado **antes** das variáveis de idioma serem definidas.
* **Estabilidade de Testes de Worker:** `test_config_app.py` e `test_metrics.py` aguardam `workers.wait_for_complete()` antes de asseverar.
* **Dependência do Workflow:** O runner limpo não tem `~/.gitpr`, e `test_demo_isolation.py` assevera que o perfil existe — o job cria o diretório e o `.env` vazio explicitamente.
* **🆕 Nesta janela a suíte cresceu 12 cenários e as falhas não mudaram:** entraram `tests/test_diff_failure_cli.py` (3) e `tests/test_full_diff_encoding.py` (1), além de 8 regressões distribuídas em cinco arquivos existentes. As **12 falhas** seguem exatamente as mesmas.
* **Workflow da extensão:** `.github/workflows/extension.yml` roda `npm install`, compila, testa e empacota o VSIX; em tags `ext-v*` publica no VS Code Marketplace e no Open VSX, pulando cada passo quando `VSCE_PAT`/`OVSX_PAT` está vazio.

### **36. Ledger SQLite de Telemetria (`src/ledger.py`, `src/infrastructure/git/identity.py`)**

* **O Problema Não Era o Formato, Era o Join:** os eventos eram gravados como arquivos JSON por comando, a partir de uma **thread daemon**, e depois reconectados ao cache de IA por um casamento heurístico de `(repo, branch, ação, minuto)`.
* **A Escrita é Síncrona, e Isso é a Decisão:** `log_command_metric()` resolve o contexto de git **uma vez por processo** e grava a linha na hora.
* **Schema Versionado:** `SCHEMA_VERSION` + `PRAGMA user_version`, chaves UUID, WAL + `synchronous=FULL`, e `LedgerVersionError` para recusar um bundle mais novo **antes** do `ATTACH`.
* **Invariante "Nunca Nasce Vazio":** `ensure_ledger()` só cria o banco **junto** com a absorção dos JSON legados.
* **Uma Janela, Um Significado:** `--since`/`--until`/`--days` estreitam **toda** superfície de leitura; a seção de ciclo assume os últimos 30 dias e **nomeia a janela**.
* **Cada Métrica é Computada uma Vez e Renderizada uma Vez:** os pares `(style, text)` fazem CLI e dashboard Textual contarem a **mesma** história.
* **Custo com Tabela Embutida e Override:** preços de lista dos quatro modelos, sobrescritos por `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT`. **As duas taxas são obrigatórias**.
* **`modules` Normalizado:** caminhos viram dois segmentos (`src/fix`), `(root)` e `(no module)`.
* **Transporte por Bundle:** `bundle` escreve a janela como um `.db` autônomo; `merge` o anexa e insere por UUID.
* **`cache_backfill` Fica de Fora:** linhas reconstruídas do cache são excluídas dos agregados de execução.
* **Identidade de Git sem Forge (`identity.py`):** rótulo de repo, branch e autor numa **única** chamada de subprocesso.
* **A Seção de Ciclo é a Única que o Ledger Não Responde:** lista PRs mergeados via `ScmProvider.list_pull_requests`; toda falha degrada para uma linha — `Not read: <razão>`.
* **Apresentação Completa:** grupo `gitpr metrics` com 8 subcomandos, dashboard lendo o ledger em thread de trabalho e o assistente de migração de três opções.
* **Testes:** `tests/test_metrics.py` (**164 cenários**).

### **37. Subcomando `gitpr mentor` e a Flag `--mentor` — Modo Mentor (`src/domain/mentor/`)**

* **O que é:** Um review diz *o que* está errado e quase nunca *por que aquilo importa*. O Modo Mentor enriquece achados com **o que está acontecendo**, **por que importa**, uma **analogia** do dia a dia e os **conceitos a estudar**.
* **Domain Layer Puro (`mentor_explanation_builder.py`):** sem I/O, converte o payload da IA em `MentorExplanation` validado e impõe **honestidade epistêmica**: sem evidência suficiente, a explicação **diz isso**; URLs alucinadas são **removidas**; IDs desconhecidos são **rejeitados**.
* **Application Layer (`generate_mentor_explanation.py`):** coleta candidatos, **lotes de no máximo 10 achados**, ordenados por severidade, reusando o cache MD5 por hash de prompt.
* **Duas Portas de Entrada:** `gitpr mentor [--finding <id>] [--provider <nome>]` e a flag `--mentor`, que anexa a seção à revisão normal.
* **Opt-In Estrito:** `GITPR_REVIEW_MENTOR_MODE` (default `false`) e `GITPR_MENTOR_INCLUDE_ANALOGY` (default `true`), editáveis na TUI de configuração.
* **Skill e Registro:** `.gitpr.mentor.md` registrado em `SKILL_FILES_BY_TYPE`, em `mcp_server.SKILL_FILES` e em `SKILL_LABELS`, com templates em **5 idiomas**.
* **Testes:** `tests/domain/mentor/test_mentor_explanation_builder.py` (8), `tests/application/use_cases/test_generate_mentor_explanation.py` (5) e `tests/test_mentor_cli.py` (4) — **2 destes falham** pelo bug de isolamento herdado.
* **Artefatos:** `docs/mentor-mode.*.md` em **5 idiomas**, ADR-009, `glossary-gitpr-mentor.md`, spec e relatórios de tarefa.

### **38. Subcomando `gitpr risk` — Score de Risco Determinístico (`src/domain/risk/`)**

* **O que é:** Um score **0–100** com nível `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`, calculado **sem IA** a partir de sinais locais.
* **Domain Layer Puro (`risk_types.py`, `risk_rules.py`, `risk_calculator.py`, `risk_explanation.py`):** enums e dataclasses; pesos, limiares, padrões de caminho crítico, casamento por glob e detecção de teste/não-executável carregados de YAML; cálculo por arquivo com **clamp 0–100** e agregação 50/30/20.
* **A Fórmula é Declarada, Não Aprendida:** **50%** o arquivo de maior risco, **30%** a média ponderada por linhas e **20%** evidência crítica.
* **Infrastructure Adapters:** `risk_history_reader.py` lê `git log` e extrai commits, correções de bug e reverts numa janela de **90 dias**; `test_matcher.py` casa arquivo de teste ↔ produção por convenção.
* **Use Case (`calculate_risk.py`):** correlaciona seções do diff, achados, casamento de testes e histórico em `FileRisk`/`PullRequestRisk`, **degradando com aviso** quando um sinal não está disponível.
* **Três Consumos:** o comando `gitpr risk`, a seção `⚡ Risk Assessment` anexada a reviews e ao review de PR remoto, e o **prompt da IA** como contexto **read-only**. O `gitpr check` usa o mesmo `execute_calculate_risk`.
* **Opt-Out:** `GITPR_RISK_INCLUDE_IN_REVIEW` (default `true`).
* **Configuração por Projeto:** `templates/gitpr.risk.yml` (ou `.gitpr/skill/gitpr.risk.yml`) sobrescreve pesos, limiares e caminhos críticos.
* **Testes:** `tests/domain/risk/` (2 arquivos, 10), `tests/application/use_cases/test_calculate_risk.py` (5), `tests/infrastructure/git/test_risk_history_reader.py` (4), `tests/infrastructure/git/test_test_matcher.py` (5) e `tests/test_risk_cli.py` (4).
* **Artefatos:** `docs/risk-scoring.*.md` em **5 idiomas**, ADR-010, `glossary-gitpr-risk-scoring.md` e relatórios de tarefa.

### **39. Subcomando `gitpr policy` — Policy Packs Versionados (`src/domain/policy/`, `src/infrastructure/policy/`)**

* **O que é:** Um **pack YAML versionado** que carrega, num artefato só, as decisões de qualidade de um repositório: skills, regras de linter, severidades, caminhos críticos, pesos de risco e convenções de PR/commit.
* **Domain Layer (`policy_types.py`, `policy_manifest.py`, `policy_checksum.py`, `policy_compatibility.py`, `policy_resolver.py`):** parsing de manifest com **schema fechado**, verificação de compatibilidade e de credencial, **checksum SHA-256** e um resolvedor de grafo com precedência e composição.
* **Infrastructure Layer:** `local_policy_repository.py` resolve o pack por **três origens** (`.gitpr/policies`, `~/.gitpr/policies` e o pacote embutido) e `policy_pack_loader.py` o carrega.
* **Use Cases:** `activate_policy_pack`, `install_policy_pack`, `resolve_effective_policy` e `validate_policy_pack`.
* **Quatro Packs Embutidos:** `laravel-quality`, `node-quality`, `php-security` e `vue-quality`, cada um com `policy.yml` e `linter.yml`, distribuídos por **`package-data`**.
* **Consumo Integrado em Quatro Pontos:** `calculate_risk`, `config.load_linter_rules`, `core.get_skill_context` e a **chave de cache do PR** (`cache_scope`). O `gitpr check` resolve o pack **antes de tudo** e sai com código 2 se ele for inválido.
* **CLI:** `gitpr policy {list, validate, show, use, off, install, init}`, com confirmação (`--yes`/`--force`), detecção de stack no `init` e gravação da escolha em `.gitpr/policy.lock.yml`.
* **Configuração:** `GITPR_POLICY_ENABLED` e `GITPR_POLICY_CONTEXT_MAX_CHARACTERS`.
* **Retrocompatibilidade:** sem pack ativo, o comportamento é **preservado** — coberto por teste de integração.
* **Dependência:** `packaging>=23.0` (SemVer/PEP 440).
* **Testes:** `tests/domain/policy/` (4 arquivos, 126), `tests/application/use_cases/` (4 arquivos de policy, 89), `tests/test_policy_cli.py` (26) e `tests/integration/test_policy_effect_on_review_linter_risk.py` (31).
* **Artefatos:** `docs/policy-packs.*.md` em **5 idiomas**, ADR-011, `glossary-policy-packs.md`, spec/plano/survey.

### **40. Subcomando `gitpr baseline` — Baseline e Supressões Auditáveis (`src/domain/baseline/`)**

* **O que é:** Linters e reviews re-reportam os mesmos achados pré-existentes a cada execução. O baseline grava a **fotografia dos achados que o repositório já conhece** em `.gitpr/baseline.json`, fingerprinta cada um de forma estável entre execuções e deixa o pipeline classificar o que é novo — **só o `new` bloqueia**.
* **Domain Layer (`baseline_fingerprint.py`, `baseline_types.py`, `baseline_manifest.py`, `baseline_comparator.py`, `suppression_policy.py`):**
  * **Fingerprint estável:** identidade da regra, caminho normalizado, linhas e **sha256 da linha com whitespace colapsado** — a linha crua **nunca** é armazenada.
  * **Manifest canônico:** JSON canônico com checksum, validação que recusa chave desconhecida, versão de schema/fingerprint fora do suportado, invariante de supressão/dívida quebrada, fingerprint duplicado e faixa de linhas inválida.
  * **Comparador:** classificação, contagens por status e resolução de entrada — `resolved` e depois `back` lê como **novo**, a leitura conservadora.
  * **Política de Supressão:** supressões, dívida aceita, overrides e validadores, com casamento em camadas por **especificidade e precedência**, mais rastreio de dívida vencida.
* **Cinco Use Cases:** `baseline_gate`, `baseline_summary`, `compare_against_baseline`, `create_baseline` e `suppress_finding`.
* **Integração com Policy Pack:** o pack pode carregar um bloco `baseline:`, validado pelos **mesmos** validadores.
* **Repository é o Único que Escreve:** `local_baseline_repository.py` é o **único** leitor/escritor de `.gitpr/baseline.json` e `.gitpr/baseline.overrides.yml`.
* **Configuração:** `GITPR_BASELINE_ENABLED`, `GITPR_BASELINE_PATH`, `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` e `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES`.
* **Opt-In e No-Op:** desligado ou sem baseline existente, a feature **não lê arquivo e não imprime nada**.
* **⚠️ A Exceção Deliberada:** um arquivo de baseline que existe mas **não pode ser aplicado** faz o lint, o review, o full review, a auditoria de arquivo, o review remoto e o risk **abortarem com exit code 1**. No `gitpr check`, um baseline corrompido sai com **código 2**.
* **Alcance:** CLI (6 subcomandos, todos com `--format json`), MCP (`get_baseline_status` + `baseline://summary`), review de PR remoto e o fluxo de lint.
* **Refatoração que a Feature Exigiu:** `NormalizedFinding` virou tipo canônico em `src/domain/finding/`.
* **Testes:** `tests/domain/baseline/` (5 arquivos, **126**), `tests/application/use_cases/` (5 arquivos, **141**), `tests/infrastructure/baseline/test_local_baseline_repository.py` (24), `tests/domain/finding/test_finding_types.py` (3), `tests/domain/linter/test_structured_findings.py` (44), `tests/test_baseline_cli.py` (54) e `tests/integration/test_baseline_effect_on_review_linter_risk.py` (34).
* **Artefatos:** `docs/baseline-suppressions.*.md` em **5 idiomas**, ADR-012, `glossary-baseline.md`, spec/plano/survey e relatório de tarefa.

### **41. Subcomando `gitpr check` — Portão Unificado de CI (`src/domain/check/`, `src/infrastructure/ci/`)**

* **O que é:** Um **único ponto de entrada** para pipelines de CI que orquestra análise estática, bridges SAST, varredura de segredos, review de IA opcional, score de risco e classificação de baseline, e emite **um artefato padronizado** com código de saída determinístico.
* **A Ordem do Pipeline é Contrato:** (1) resolução de policy — inválida sai com `2`; (2) extração do diff com smart excludes; (3) linter regex + segredos + bridges externos; (4) score de risco preliminar; (5) **review de IA opcional**; (6) classificação de baseline; (7) avaliação do limiar `--fail-on`; (8) geração do artefato com **mascaramento de segredos**.
* **Domain Layer (`src/domain/check/`):** `check_types.py` (severidade normalizada em três níveis com aliases de spec); `check_config.py` (precedência **CLI > env > defaults**); `check_output.py` (dispatch de formato e escrita atômica).
* **Infrastructure Layer (`src/infrastructure/ci/`):** `sarif_builder.py` (SARIF 2.1.0), `junit_builder.py` (testsuites com `<failure>` e `<system-out>`) e `masking.py`.
* **Use Case (`run_check.py`):** `resolve_diff_base()` (explícito → `GITHUB_BASE_REF` → `origin/main` → `HEAD`), execução do linter e dos bridges, score de risco, review opcional, baseline e envelope final. O stdout emite **só o artefato**.
* **Códigos de Saída:** `0` sucesso; `1` achado contável no limiar; `2` erro de execução.
* **CLI:** `gitpr check` com 8 opções e 9 variáveis `GITPR_CHECK_*`.
* **GitHub Action Reescrita:** `action.yml` virou um único passo `gitpr check`. **Quebra declarada** para workflows que dependiam de `--linter` + `--fullreview`.
* **Testes:** **37 cenários** — `test_run_check.py` (8), `test_check_types.py` (8), `test_check_config.py` (3), `test_check_output.py` (3), `test_masking.py` (6), `test_sarif_builder.py` (2), `test_junit_builder.py` (2) e `test_check_cli.py` (5).
* **MCP:** o tool `run_check` devolve o envelope JSON do mesmo pipeline, com `no_ia` default `true`.
* **Artefatos:** `docs/check-ci.*.md` em **5 idiomas**, ADR-013, `glossary-check-ci.md`, spec, `plansfacts` e survey.

### **42. Extensão de Editor — VS Code e Cursor (`extensions/vscode/`)**

* **O que é:** Uma extensão **thin client** que leva os fluxos do GitPR para dentro do editor sem reimplementar nada: ela inicia o `gitpr-mcp` por stdio e chama as tools existentes. Chaves, tokens, prompts e cache continuam em `~/.gitpr/`, cifrados com Fernet.
* **Arquitetura:** `GitPrMcpClient` sobre `@modelcontextprotocol/sdk` + `SessionManager` com **uma sessão por pasta** (multi-root) + verificação de contrato na conexão: as 7 tools obrigatórias precisam existir; se não, `MissingMcpToolsError` instrui `pip install --upgrade gitpr-cli`.
* **8 Comandos:** `gitpr.commit`, `gitpr.review`, `gitpr.fullReview`, `gitpr.reviewMentor`, `gitpr.generatePr`, `gitpr.generatePrExplain`, `gitpr.publishPr` e `gitpr.check`.
* **Publicação em Duas Etapas:** `generatePr` abre um documento Markdown editável; `publishPr` pede confirmação modal e trata `success`, `needs_push`, `already_exists`, `auth_required` e `error`.
* **Diagnósticos no Painel Problems:** `run_check` é convertido em `DiagnosticCollection("gitpr")`.
* **Mascaramento em Profundidade Dupla:** `masking.ts` espelha `src/infrastructure/ci/masking.py`.
* **Localização da Extensão:** bundles em **en, es, fr e pt-br** (4 idiomas) — a UI do GitPR em si continua com 5.
* **CI/CD da Extensão:** `.github/workflows/extension.yml` instala, compila, testa e empacota o VSIX; em tags `ext-v*` publica no Marketplace e no Open VSX.
* **O Que a Extensão Não Faz:** não commita, não faz push e não publica sem confirmação.
* **Testes:** suíte Mocha própria (7 cenários, incluindo stdio real) + `tests/test_mcp_server.py` (115 cenários).
* **Artefatos:** `docs/editor-extension.*.md` em **5 idiomas**, ADR-014, `glossary-editor-extension.md`, specs, `plansfacts` e relatório do Gemini.

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_blame_engine_ranges.py` | 7 | Blame por faixa de linhas em arquivo |
| `tests/test_blame_metrics.py` | 7 | Métricas de blame: profundidade, commits, duração |
| `tests/test_baseline_cli.py` | 54 | Grupo `baseline`: create/show/validate/update/suppress/unsuppress |
| `tests/test_changelog_builder.py` | 22 | Builder do changelog: seções, headings traduzíveis, contribuidores, links e datas |
| `tests/test_chat_backend.py` | 19 | Memória de chat, persistência, comandos slash |
| `tests/test_check_cli.py` | 5 | CLI do `check`: opções, formatos, exit codes |
| `tests/test_commit_classifier.py` | 30 | Classificação Conventional Commits + `pr_number_from_merge()` nas 4 forges |
| `tests/test_config_app.py` | 78 | TUI de configuração: montagem, troca de categoria, dirty tracking, F2 bloqueado, Ctrl+R, busca, segredos |
| `tests/test_config_cli.py` | 9 | Registro do subcomando `config`, `-h`, import lazy, stdout limpo |
| `tests/test_config_schema.py` | 42 | Cobertura de `DEFAULT_CONFIG`, sem duplicatas, categorias/kinds, `advanced` só em Avançado, seção de skills |
| `tests/test_config_store.py` | 22 | Round-trip no `.env` temporário, comentários e ordem preservados, `remove_config_value()` idempotente |
| `tests/test_config_suggest_reviewers.py` | 8 | Configuração de suggested reviewers (chaves e defaults) |
| `tests/test_config_validation.py` | 40 | Tipos, enums, templates, `validate_ai_key()` com SDK mockado (401 vs. rede vs. ollama) |
| `tests/test_core.py` | 49 | Fluxos principais, git diff, PR generation, timing, staging, coautoria, idioma dos hooks |
| `tests/test_diff_failure_cli.py` | 3 🆕 | Exit code 1 em falha do git, 0 em diff vazio, fail-open no `--hook` |
| `tests/test_diff_parser.py` | 26 | Parser de diff por linhas/hunks + `summarize_patch()` e `split_patch_sections()` |
| `tests/test_explain_command.py` | 4 ⬆️ | CLI do `explain`: sucesso, chave ausente, diff vazio, ajuda contextual |
| `tests/test_external_linters.py` | 33 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_full_diff_encoding.py` | 1 🆕 | Repositório real com arquivo Latin-1: o byte `0xFA` vira `U+FFFD` e o arquivo aparece no diff |
| `tests/test_i18n.py` | 20 | Paridade entre idiomas, chaves ausentes/órfãs, identidade — **3 falhas** ❌ |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação |
| `tests/test_issue_engine.py` | 4 | Draft de issue estruturado |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_linter_presets.py` | 5 | Presets de linter: resolução e re-download forçado |
| `tests/test_main_suggest_reviewers.py` | 8 | Flag `--no-suggest-reviewers` na CLI e no help contextual |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 115 | Ferramentas MCP (18), recursos (19), annotations, patching, CLI direto, offload, contrato da extensão |
| `tests/test_mcp_server_e2e.py` | 6 | Servidor MCP real via subprocess + JSON-RPC stdio |
| `tests/test_mentor_cli.py` | 4 | CLI do `mentor` e opt-in do `--mentor` — **2 falhas conhecidas** ❌ |
| `tests/test_metrics.py` | 164 | **Ledger**: escrita síncrona, exportação idempotente, bundle/merge, versionamento, migração, renderizadores, custo, qualidade, módulos, provedores, ciclo |
| `tests/test_net_timeouts.py` | 12 | Timeouts de rede/IA — alinhados ao default real de 180s |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_policy_cli.py` | 26 | Grupo `policy`: list/show/validate/use/off/install/init, confirmação e lockfile |
| `tests/test_pr_publish_app.py` | 55 | TUI do PR Publisher: telas, fluxos, suggested reviewers, `NoticeScreen`, modal de merge |
| `tests/test_pr_publish_linter_modal.py` | 4 | Modal de erro do linter: abort, no-verify |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_release_cli.py` | 4 | CLI do release: options, help com epilog documentado |
| `tests/test_release_engine.py` | 53 | **Corte ancorado no changelog, `_drop_released()`, links, mapa de PR por merge commit**, publicação |
| `tests/test_reviewer_resolution.py` | 18 | Escada de resolução, rejeição de nome parcial, dedup, tolerância a falha |
| `tests/test_reviewer_suggestion.py` | 18 | Lógica de sugestão de revisores (ranking, exclusão, top-N, `last_commit_hash`) |
| `tests/test_risk_cli.py` | 4 | CLI do `risk`: `--file`, `--format json`, `--base`, `--no-history` |
| `tests/test_security_ruleset.py` | 61 | Matriz do ruleset embutido: regex, placeholders, nível, wildcard, merge, traduções |
| `tests/test_skill_command.py` | 10 | Download e validação de templates de skill |
| `tests/test_skill_context.py` | 20 | `get_skill_context()` com `quiet=True`, fallbacks, guarda do artefato de PR |
| `tests/test_skill_templates.py` | 99 | Varredura parametrizada de **todo template publicado** contra referências embutidas |
| `tests/test_smart_excludes.py` | 15 | Filtro pathspec inteligente e re-download forçado |
| `tests/test_suggest_reviewers.py` | 17 | Suggested reviewers no fluxo de PR (integração, hint `no_login`) |
| `tests/test_tests_command.py` | 4 ⬆️ | CLI do grupo `tests` e do `generate`, `--finding` e epilog com link |
| `tests/test_thinking_words.py` | 5 | Carregamento, parsing com separador `;` e reload forçado |
| `tests/test_updater.py` | 23 | Gate do PyPI: parsing de versão, cache diário, fetch, decisões do portão, wiring no CLI |
| `tests/test_usage_log.py` | 27 | Log de uso: nome derivado da data, escrita síncrona, silêncio, `_repo_label()` multi-forge |
| `tests/test_version_bump.py` | 17 | Bump semântico: major/minor/patch, alvos e validação |
| `tests/test_web_links.py` | 26 | Normalização de remote (https/ssh/scp/credenciais/porta) e padrões de URL por forge |
| `tests/application/use_cases/test_activate_policy_pack.py` | 27 | Ativação de pack, lockfile, recusas |
| `tests/application/use_cases/test_baseline_gate.py` | 40 | Gate: carga, classificação, anotação, camadas e aborto |
| `tests/application/use_cases/test_baseline_summary.py` | 12 | Visão read-only do baseline para MCP/IDE |
| `tests/application/use_cases/test_calculate_risk.py` | 5 | Correlação de diff/achados/testes/histórico, degradação |
| `tests/application/use_cases/test_create_baseline.py` | 30 | Criação/atualização com proveniência e preservação de decisões |
| `tests/application/use_cases/test_generate_mentor_explanation.py` | 5 | Lotes, severidade, cache hit, chave ausente |
| `tests/application/use_cases/test_generate_pr_explanation.py` | 3 ⬆️ | Caso de uso do explain: dict do provider e chave ausente |
| `tests/application/use_cases/test_generate_test_file.py` | 5 ⬆️ | Caso de uso da geração de testes: dict do provider e string crua |
| `tests/application/use_cases/test_install_policy_pack.py` | 10 | Instalação de pack, origens e conflitos |
| `tests/application/use_cases/test_run_check.py` | 8 | Orquestração do check: ordem, degradação, exit codes |
| `tests/application/use_cases/test_suppress_finding.py` | 29 | Supressão/remoção nos quatro escopos |
| `tests/application/use_cases/test_validate_policy_pack.py` | 23 | Validação: schema fechado, checksum, compatibilidade |
| `tests/badge/test_badge_append.py` | 9 | Append idempotente do selo ao corpo do PR |
| `tests/badge/test_badge_builder.py` | 19 | Composição do Markdown do shields.io, escape, regra de cor, estilo |
| `tests/badge/test_badge_cli.py` | 15 | Comando `gitpr badge`: snippet, `--readme`, `--style` |
| `tests/badge/test_badge_data.py` | 7 | Contagem de alertas; `None` sem regras configuradas |
| `tests/badge/test_badge_offline.py` | 6 | Guarda offline (rede proibida, exceto loopback) |
| `tests/badge/test_badge_optout.py` | 17 | `GITPR_BADGE=false` em todos os caminhos de publicação |
| `tests/badge/test_badge_paths.py` | 10 | Ponto único de injeção nos dois publicadores — **7 falhas** ❌ |
| `tests/demo/test_demo_app.py` | 22 | TUI do tour: navegação, telas, modal de ajuda |
| `tests/demo/test_demo_isolation.py` | 14 | O tour não toca `~/.gitpr` nem a rede |
| `tests/demo/test_demo_runner.py` | 33 | Máquina de estados `DemoState`: avançar, voltar, concluído, modo texto |
| `tests/demo/test_demo_scenarios.py` | 47 | Integridade dos cenários gravados (aritmética de hunk) nos 5 idiomas |
| `tests/demo/test_demo_text_mode.py` | 18 | Saída em texto puro (`--no-tui`) para CI e gravações |
| `tests/demo/test_fake_ai_provider.py` | 21 | Contrato do provider falso: espelha `call_ai_model` argumento por argumento |
| `tests/domain/baseline/test_baseline_comparator.py` | 21 | Classificação, contagens de status, `resolved`→`new` |
| `tests/domain/baseline/test_baseline_fingerprint.py` | 12 | Digest dourado, linha crua nunca armazenada, estabilidade |
| `tests/domain/baseline/test_baseline_manifest.py` | 26 | JSON canônico, checksum, chaves desconhecidas, invariantes |
| `tests/domain/baseline/test_baseline_types.py` | 15 | Status persistidos, escopos e precedência |
| `tests/domain/baseline/test_suppression_policy.py` | 52 | Camadas, especificidade, overrides, dívida vencida |
| `tests/domain/check/test_check_config.py` | 3 | Precedência CLI > env > defaults |
| `tests/domain/check/test_check_output.py` | 3 | Dispatch de formato e escrita atômica |
| `tests/domain/check/test_check_types.py` | 8 | Severidade em 3 níveis, aliases de spec, resumo |
| `tests/domain/finding/test_finding_types.py` | 3 | Tipo canônico do achado: `snippet_hash`, `rule_version` |
| `tests/domain/linter/test_sast_finding_mapper.py` | 2 | Formatação uniforme e deduplicação `[Gitleaks + Regex]` |
| `tests/domain/linter/test_structured_findings.py` | 44 | `findings_out`: achados estruturados e o contador de linha do lado novo |
| `tests/domain/mentor/test_mentor_explanation_builder.py` | 8 | Builder puro: honestidade epistêmica, URLs removidas, ordem preservada |
| `tests/domain/policy/test_policy_checksum.py` | 15 | SHA-256 do pack e detecção de edição manual |
| `tests/domain/policy/test_policy_compatibility.py` | 22 | Compatibilidade de versão e credencial |
| `tests/domain/policy/test_policy_manifest.py` | 42 | Schema fechado, bloco `baseline:`, erros de manifesto |
| `tests/domain/policy/test_policy_resolver.py` | 47 | Precedência, composição em camadas, pack ativo × base |
| `tests/domain/pr/test_explain_section_builder.py` | 6 ⬆️ | Renderização do Markdown, parsing tolerante, `[FILL]`, payload dict e `None` |
| `tests/domain/risk/test_risk_calculator.py` | 5 | Fórmula 50/30/20, clamp 0–100, elevação obrigatória |
| `tests/domain/risk/test_risk_rules.py` | 5 | Pesos, limiares, glob de caminho crítico, YAML de override |
| `tests/domain/tests_generation/test_framework_detector.py` | 11 | Detecção por config, manifest e diretório; override; falha avisada |
| `tests/domain/tests_generation/test_scaffold_builder.py` | 7 | Caminho convencional por framework (Laravel, Pytest, JS/TS) |
| `tests/fix/test_apply_fix.py` | 53 | Caso de uso completo: review → IA → validar → classificar → dry-run/apply |
| `tests/fix/test_chat_shared_extractor.py` | 8 | Extrator compartilhado entre chat e `fix` |
| `tests/fix/test_fix_cli.py` | 31 | Roteamento do subcomando, opções, dry-run default, `--force` |
| `tests/fix/test_fix_history.py` | 21 | Ledger `.gitpr/fix_history.json`: escrita atômica, leitura |
| `tests/fix/test_fix_settings.py` | 10 | As cinco `GITPR_FIX_*` e os fallbacks de valor inválido |
| `tests/fix/test_patch_applier.py` | 19 | Invólucro de `git apply`: check/apply/reverse, branch, status |
| `tests/fix/test_patch_extractor.py` | 13 | Blocos cercados → diff unificado validado |
| `tests/fix/test_patch_safety_classifier.py` | 22 | Matriz safe/review_required/experimental e códigos de motivo |
| `tests/fix/test_resolve_last_review.py` | 13 | Seleção do último review, exclusão de reviews por arquivo |
| `tests/fix/test_rollback_fix.py` | 14 | `--rollback`: reverse e as três recusas |
| `tests/infrastructure/baseline/test_local_baseline_repository.py` | 24 | Único leitor/escritor: escrita atômica, checksum, reparo |
| `tests/infrastructure/ci/test_junit_builder.py` | 2 | JUnit XML: failure/system-out |
| `tests/infrastructure/ci/test_masking.py` | 6 | Mascaramento de credenciais antes de serializar |
| `tests/infrastructure/ci/test_sarif_builder.py` | 2 | SARIF 2.1.0 e `tool.driver.rules` |
| `tests/infrastructure/git/test_risk_history_reader.py` | 4 | `git log` seguro: commits, bugs e reverts em 90 dias |
| `tests/infrastructure/git/test_test_matcher.py` | 5 | Casamento teste ↔ produção por convenção |
| `tests/infrastructure/linter/external/test_bandit_bridge.py` | 3 | Bridge Bandit: disponibilidade, parsing, mapeamento |
| `tests/infrastructure/linter/external/test_base_bridge.py` | 4 | ABC: subprocess endurecido, timeout, binário ausente |
| `tests/infrastructure/linter/external/test_gitleaks_bridge.py` | 4 | Bridge Gitleaks: mascaramento de segredo, escopo por arquivo |
| `tests/infrastructure/linter/external/test_semgrep_bridge.py` | 3 | Bridge Semgrep: parsing JSON, severidade, pulo de não-Python |
| `tests/integration/test_baseline_effect_on_review_linter_risk.py` | 34 | Efeito real do baseline em review, lint e risk num repositório de verdade |
| `tests/integration/test_policy_effect_on_review_linter_risk.py` | 31 | Efeito real do pack em review, lint e risk (com guarda de rede autouse) |
| `tests/review/test_diff_normalizer.py` | 20 | Newlines, validação de diff, smart-excludes em Python |
| `tests/review/test_diff_source.py` | 12 | `DiffOrigin`/`DiffSource`: proveniência, `cache_scope`, `is_remote` |
| `tests/review/test_remote_pr.py` | 40 | Orquestração: portões, PR, diff, linter, comentário opcional |
| `tests/review/test_review_pr_cli.py` | 25 | CLI `review-pr`: opções, rejeições antes da IA, `--post-comment` |
| `tests/scm/test_azure_devops_provider.py` | 48 | Provider Azure DevOps: org/projeto, PRs, `ScmNotSupportedError` |
| `tests/scm/test_bitbucket_provider.py` | 44 | Provider Bitbucket: Basic auth, workspace, PRs |
| `tests/scm/test_contract.py` | 42 | Contrato `ScmProvider`: assinaturas, dataclasses, erros |
| `tests/scm/test_factory.py` | 11 | `resolve_scm_provider()` + `detect_provider_from_remote()` |
| `tests/scm/test_github_api_shim.py` | 18 | Shim deprecado `github_api` → delega ao provider |
| `tests/scm/test_github_provider.py` | 72 | Provider GitHub: REST, headers, PRs, issues, releases, read-back de revisores |
| `tests/scm/test_gitlab_provider.py` | 52 | Provider GitLab: API v4, namespace, cabeçalhos sintetizados e `overflow` |
| `tests/scm/test_init_wizard.py` | 12 | Wizard `--init`: detecção da forge, validação, persistência |
| `tests/scm/test_release_publish.py` | 8 | Publicação de release por forge (GitHub/GitLab) |
| `tests/split/test_apply_split_plan.py` | 11 | O único módulo que muta: staging seletivo, um commit por grupo |
| `tests/split/test_generate_split_plan.py` | 12 | Diff → units → groups → pré-validação de conflito → mensagens |
| `tests/split/test_hunk_grouper.py` | 18 | Prompt, orçamento/trimming, chamada de IA, validação da resposta |
| `tests/split/test_hunk_parser.py` | 18 | `parse_units()`/`build_patch()`: texto ↔ modelo, puro |
| `tests/split/test_selective_stager.py` | 11 | Staging de subconjunto, check contra HEAD, índice limpo |
| `tests/split/test_split_cli.py` | 31 | CLI do split: opções, dry run default, `--apply` |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (scaffold; nunca executado) |

**Total:** **2964 cenários coletados em 140 módulos de teste** (53 na raiz + 12 em `tests/application/use_cases/` + 10 em `tests/fix/` + 9 em `tests/scm/` + 7 em `tests/badge/` + 6 em `tests/demo/` + 6 em `tests/split/` + 5 em `tests/domain/baseline/` + 4 em `tests/domain/policy/` + 4 em `tests/review/` + 4 em `tests/infrastructure/linter/external/` + 3 em `tests/domain/check/` + 3 em `tests/infrastructure/ci/` + 2 em `tests/domain/risk/` + 2 em `tests/domain/tests_generation/` + 2 em `tests/integration/` + 2 em `tests/infrastructure/git/` + 2 em `tests/domain/linter/` + 1 em `tests/domain/finding/` + 1 em `tests/domain/mentor/` + 1 em `tests/domain/pr/` + 1 em `tests/infrastructure/baseline/`; **+12 cenários e +2 arquivos** desde o relatório anterior).

**Notas de qualidade desta versão:**
- **Execução completa nesta máquina: `12 failed, 2950 passed, 2 skipped, 138 subtests passed in 401,46s (6min41s)`.** O número de cenários cresceu **12** (+0,4%) e o de falhas **não mudou**: são exatamente as mesmas 12 do relatório anterior. A suíte também ficou **mais rápida** (401s contra 723s), provavelmente porque o `git fetch` deixou o modo bytes e as chamadas de git param de estourar em fixtures com conteúdo legado.
- **As 7 falhas de `tests/badge/test_badge_paths.py` continuam sem correção.** O provider falso do teste (`SimpleNamespace(name=..., create_pull_request=...)`) não tem `.token`; o `publish_pull_request_use_case` devolve `auth_required` (401) e `create_pull_request` nunca roda — o `captured["request"]` levanta `KeyError`. **O produto está correto** (o provider real carrega o token); **o fixture precisa declarar `token="ghp_fake"`**.
- **As 3 falhas de i18n são dívida de tradução real e não foram tocadas nesta janela:** `test_key_parity_and_count` (es/fr com 1618), `test_no_missing_keys` (8 chaves usadas no código sem dicionário) e `test_no_orphan_keys` (2 chaves antigas). Os dicionários seguem com os mesmos 1620/1618 do relatório anterior.
- **As 2 falhas de `tests/test_mentor_cli.py` seguem sendo o mesmo bug de isolamento:** `@patch("src.core.get_git_diff")` não alcança o binding importado por valor em `src/main.py`. Numa árvore cuja única alteração é um `.md` (filtrado por `:(exclude)*.md` nos smart excludes) o diff real volta vazio, o fluxo retorna antes do renderizador e a asserção falha. **Com o patch em `src.main.get_git_diff`, os dois cenários passam.** É uma correção de duas linhas, ainda pendente.
- **Do lado positivo, os 12 cenários novos cobrem exatamente o que mudou:** 3 em `test_diff_failure_cli.py` (contrato de exit code), 1 em `test_full_diff_encoding.py` (repositório real com Latin-1), 2 em `test_explain_command.py`, 2 em `test_tests_command.py`, 2 em `test_explain_section_builder.py`, 1 em `test_generate_pr_explanation.py` e 1 em `test_generate_test_file.py`. O CI roda em Python 3.10 e 3.13 com `fail-fast: false`.
- **`tests/conftest.py` segue hermético:** `GITPR_SHOW_LOGS=false`, `GITPR_SKIP_UPDATE_CHECK=true`, `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false` e `LANG_VERSION` na versão do código.
- **Guarda de rede em dois lugares:** `tests/demo/conftest.py` e `tests/integration/conftest.py`.
- **Fixtures de git real:** `tests/fix/git_fixture.py`, `tests/split/git_fixture.py` e, agora, `tests/test_full_diff_encoding.py` — que cria um origin bare temporário e comita um arquivo Latin-1 de verdade.
- **A suíte da extensão é separada:** 7 cenários Mocha em `extensions/vscode/src/test/mcp_client.test.ts`, dos quais 1 integra de verdade com o servidor MCP Python por stdio; ela não entra na contagem do pytest.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n — dívida inalterada:** **1620 chaves** em `pt_br.json`, `pt_pt.json`, `es_es.json` e `fr_fr.json`, mas **1618** em `es.json` e `fr.json`. O código usa **1626** chaves: **8 sem tradução** (as mensagens de `publish_pull_request` e as descrições das tools MCP `run_check`/`publish_pull_request`) e **2 órfãs** (`Cannot publish a Pull Request from a detached HEAD or empty branch.` e `Current branch has not been pushed to the remote…`). Nenhuma chave nova foi adicionada nesta janela — e nenhuma dívida foi paga. ❌
* **`__lang_version__` segue em v0.0.35** (sem bump nesta janela).
* **Fontes de tradução em lockstep:** uma chave nova precisa existir no código (fonte), em `langs/pt_br.json` (**lista mestra**), nos dicts FR/ES de `scripts/sync_all_langs.py` e nos valores curados de `scripts/fix_mangled_i18n_keys.py`; a asserção `len(CLEAN_KEYS)` segue em 49.
* **🆕 Tópicos novos (2, ambos em 5 idiomas):**
  - `docs/explain-pr.md` — o Guia do Revisor: o que muda, por que muda, onde focar e o risco de regressão, com a seção `⚡ Risk Assessment` e a detecção de placeholders.
  - `docs/tests-generate.md` — a geração de suíte por IA: detecção de framework (Pest, PHPUnit, Jest, Vitest, Pytest), o scaffold convencional, a validação de sintaxe e o dry run.
* **Tópicos atualizados nesta janela:** `README.*` (5) — os links de documentação saíram do GitHub e passaram a apontar para `gitpr.natanfiuza.dev.br/docs/*`, com `?lang=` por idioma (**342 destinos**; **217 URLs únicas** verificadas, **0 falhas**).
* **Documentação em 5 idiomas:** **50 tópicos canônicos** em `docs/` (+2) — **47 com cobertura completa nos 5 idiomas** e apenas **3 tópicos parciais** (`github-issue-prompt-com-gh`, `version-markers`, `review-pr`), os mesmos 3 de antes.
* **🆕 A lacuna de documentação foi fechada:** `explain` e `tests` eram as **últimas** features sem tópico em `docs/`. Agora **nenhuma feature está sem documentação**.
* **Skills locais do Claude Code:** `.claude/skills/` com **29 skills** (contagem inalterada).
* **Memory Index:** `.claude/memory/MEMORY.md` com **40 padrões** (contagem inalterada).
* **Relatórios de tarefas:** `docs/claude-code/reports/develop_natan/` (**112** no total; **+4** — `2026-10-18_docs_explain_tests.md`, `2026-10-18_status_report_v0_0_18.md`, `2026-10-27_git_diff_non_utf8.md`, `2026-10-27_readme_docs_site_links.md`) e `docs/gemini/reports/develop_natan/` (**16**; inalterado).
* **Relatórios de status:** `docs/reports/` — este é o **19º relatório** (v0.0.19); o v0.0.18 nunca é sobrescrito.
* **Planos de desenvolvimento:** 146 arquivos em `docs/plans/` (**+3** — `20261018_docs_explain_tests_plansfacts.md`, `20261027_git_diff_non_utf8_plansfacts.md`, `20261027_readme_docs_site_links_plansfacts.md`) + **20 arquivos em `docs/survey/`** (+3).

---

## **🔄 Pipeline de Distribuição**

1. **PyPI (canal único):** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **Atualização obrigatória:** a execução verifica o PyPI no startup e **bloqueia com exit code 1** se houver versão mais nova, imprimindo `pip install --upgrade gitpr-cli`; a checagem é cacheada por dia e o `--update` apenas reporta
3. **GitHub Releases:** removido — sem PyInstaller, sem asset `.exe`, sem hot-swap
4. **GitHub Actions:** workflow `pr-review.yml` + `action.yml` (instala via pip) + `tests.yml` (matriz Python 3.10 e 3.13) + `extension.yml` (VSIX; publicação no Marketplace/Open VSX em `ext-v*`). O `action.yml` chama um único passo `gitpr check` — **quebra declarada** para quem usava `--linter` + `--fullreview`.
5. **MCP Server:** entry point `gitpr-mcp` via `pyproject.toml`
6. **Extensão de Editor:** pacote VSIX independente (`natanfiuza.gitpr`), com canais VS Code Marketplace e Open VSX; requer Node.js 20+ apenas para build, não para uso
7. **Templates e idiomas OTA:** `templates/` e `langs/*.json` servidos do GitHub (main) — `__lang_version__` **v0.0.35** renova as cópias locais de `~/.gitpr/langs/`; `__scripts_version__` **v0.0.4** renova os hooks
8. **Versão derivada do código:** `pyproject.toml` usa `version = {attr = "src.updater.__version__"}` — o `__version__` é a **única** fonte
9. **`package-data` importa:** os quatro packs embutidos (`src/policy_packs/*`) viajam no wheel
10. **🆕 Estado do release:** os **dois** releases pendentes foram fechados e publicados. **`v1.4.1`** (tag em 2026-10-18, merge do PR #218) e **`v1.4.2`** (tag em 2026-10-27, merge do PR #222) existem; o PyPI serve **1.4.2**. O `develop_natan` está um commit à frente da tag com a migração dos links do README (mergeada em `main` pelo PR #223), que entra no **próximo** release. O pipeline de release continua manual.

---

## **📈 Evolução desde o Relatório Anterior (v0.0.18)**

| Área | v0.0.18 (anterior) | v0.0.19 (atual) |
|------|-------------------|-----------------|
| **Versão GitPR** | 1.4.1 (bump commitado; **tag ainda não criada**) | **1.4.2** — tag `v1.4.2` criada e **publicada no PyPI**; a `v1.4.1` também foi tagueada nesta janela |
| **Versão Idioma** | v0.0.35 | v0.0.35 (inalterada) |
| **Versão Scripts Hook** | v0.0.4 | v0.0.4 (inalterada) |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama (inalterado) |
| **Idiomas** | 5 idiomas, 6 dicionários | 5 idiomas, 6 dicionários |
| **Subcomandos** | 15 | 15 (inalterado) — 4 grupos (baseline 6, metrics 8, policy 7, tests 1) |
| **Interface** | CLI + TUIs + wizards + 15 subcomandos | Inalterada; **READMEs migrados para o site de docs** |
| **Camadas** | 9 pacotes de domínio, 15 casos de uso | 9 e 15 (inalterado) |
| **Infraestrutura CI** | `src/infrastructure/ci/` — SARIF, JUnit, mascaramento | Inalterada |
| **Ferramentas MCP** | 18 tools / 19 recursos / 7 prompts | 18 / 19 / 7 (inalterado) |
| **Flags CLI** | 32 na raiz + 15 subcomandos | 32 + 15 (inalterado) |
| **Variáveis de Ambiente** | 58 no `DEFAULT_CONFIG` + preços/câmbio + 9 `GITPR_CHECK_*` | Inalterado |
| **Schema de Config** | 80 `ConfigField` / 16 categorias | 80 / 16 (inalterado) |
| **Robustez de Git 🆕** | Decodificação UTF-8 estrita em 10 chamadas; falha do git virava "diff vazio" | **`errors="replace"` em todas as 10 chamadas** e **exit code 1** quando o git falha (0 só para diff realmente vazio; `--hook` fail-open) |
| **Linter** | Regex + segredos + SAST + `findings_out` + baseline-aware | Inalterado |
| **Hooks Git** | post-checkout/post-merge/pre-push no ledger | Inalterados |
| **Camada SCM** | 4 forges, paginação, `web_links.py` | Inalterada |
| **Release engine** | Seção 1.4.1 gerada (uncommitted, sem tag) | **1.4.1 e 1.4.2 commitados, tagueados e publicados** |
| **i18n (chaves por arquivo)** | 1620 × 4 e 1618 × 2 — 8 sem tradução e 2 órfãs | **Inalterado** ❌ |
| **Documentação** | 48 tópicos (45 completos + 3 parciais) | **50 tópicos (47 completos + 3 parciais)** — `explain-pr` e `tests-generate` em 5 idiomas |
| **Links dos READMEs 🆕** | `github.com/.../blob/main/docs/*.md` | **`gitpr.natanfiuza.dev.br/docs/*` com `?lang=`** — 342 destinos, 217 URLs verificadas |
| **CI** | `tests.yml` (3.10 + 3.13) + `action.yml` + `extension.yml` | Inalterado |
| **Suíte de Testes** | 2952 cenários (138 arquivos) | **2964 cenários (140 arquivos) — +12 cenários, +2 arquivos** |
| **Falhas conhecidas** | 12 | **12 — exatamente as mesmas** (7 badge + 3 i18n + 2 mentor) |
| **Dependências** | Sem novas dependências Python | Inalterado |
| **Commits desde o relatório** | 6 commits | **4 commits** (`fafe24b`, `f52cdad`, `4d980e2`, `5ee6025`) |
| **PRs mergeados** | 6 PRs (#208, #210, #212, #214, #216, #217) | **4 PRs (#218, #220, #222, #223)**; 1 issue fechada (#221) |
| **Memory Index** | 40 padrões | 40 padrões (inalterado) |
| **Relatórios de tarefas** | 108 claude-code, 16 gemini | **112 claude-code (+4) e 16 gemini** |
| **Planos de desenvolvimento** | 144 planos, 17 surveys | **146 planos (+3), 20 surveys (+3)** |

---

## **🚧 Próximos Passos**

* **Corrigir as 7 falhas de `tests/badge/test_badge_paths.py`:** o provider falso do teste não tem `.token`, e o caso de uso compartilhado exige o atributo. Adicionar `token="ghp_fake"` ao `SimpleNamespace` (ou permitir pular a checagem quando `check_remote_state=False`) devolve os 7 cenários. **Item herdado, ainda aberto — terceira janela consecutiva.**
* **Pagar a dívida de i18n:** 8 chaves usadas sem tradução (mensagens de `publish_pull_request` e descrições MCP) + 2 órfãs + as 2 chaves faltantes em `es.json`/`fr.json`. Fechar isso desbloqueia `test_key_parity_and_count`, `test_no_missing_keys` e `test_no_orphan_keys` de uma vez. **Item herdado, ainda aberto.**
* **Corrigir o isolamento de `tests/test_mentor_cli.py`:** são as **duas falhas mais antigas** da suíte. O patch aponta para `src.core.get_git_diff`, mas `src/main.py` importa o nome **por valor**. Trocar o alvo para `src.main.get_git_diff` fecha a suíte sem tocar no produto. **Item herdado, ainda aberto.**
* **Automatizar o release no GitHub Actions:** o CI de testes tem quatro workflows, mas build + upload para o PyPI continuam manuais — e o `extension.yml` já mostra o padrão (gatilho em tag) que um `release.yml` pode seguir. **Item herdado, ainda aberto.**
* **Estender a cobertura do ruleset de segredos:** as três lacunas continuam abertas — atribuição sem aspas (`API_KEY=abc123`), os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-`, e a ausência de fronteira à esquerda no nome da chave. **Item herdado, ainda aberto.**
* **Traduzir `docs/review-pr.*.md`:** é a **última** família de feature com cobertura parcial (2 de 5 idiomas). **Item herdado, ainda aberto.**
* **Destrackear os artefatos de `.gitpr/metrics/export/`:** restam **34 arquivos rastreados**, porque `gitignore` não destrackeia. Falta um `git rm --cached` único. **Item herdado, ainda aberto.**
* **Documentar a quebra de contrato do `request_pull_request_reviewers`:** passou de `None` para `list[str]`; subclasses de terceiros de `ScmProvider` precisam ser atualizadas. **Item herdado, ainda aberto.**
* **Mapear o blast radius do baseline no exit code:** um baseline que não pode ser aplicado aborta seis fluxos com exit code 1, e o `check` usa **2**. Vale explicitar o contrato completo em `docs/baseline-suppressions`/`docs/check-ci`. **Item herdado, parcialmente coberto pelo check.**
* **Reconciliar a versão do projeto:** `CLAUDE.md` ainda diz `Current version: 0.0.37` enquanto o `__version__` está em **1.4.2**. Definir uma convenção única. **Item herdado, ainda aberto.**
* **`gitpr -h config` ignora o `-h`:** o subcomando abre a TUI em vez de mostrar a ajuda — o gate `if ctx.invoked_subcommand is not None: return` roda antes do bloco de `help_flag`. **Item herdado, ainda aberto.**
* **Migrar o extrator do `sync_i18n.py` para AST:** o regex trunca literais com concatenação implícita (`__("a " "b")`). `tests/test_i18n.py` já usa AST; o script de sincronização continua no regex. **Item herdado, ainda aberto.**
* **Seção Smart Exclude na TUI:** o item 10 do survey da TUI de configuração continua não iniciado, e os campos `GITPR_SMART_EXCLUDES_*` seguem sob `diff`, sem categoria própria. **Item herdado, ainda aberto.**
* **Dívidas registradas no plano do config TUI:** `DEFAULT_CONFIG` ficou redundante com o schema; o banner de abertura não lista `--init`, `--base` nem `--plugins`; o `LinterApp` é o **único** app Textual que ainda não desabilita a command palette; e as **9 `GITPR_CHECK_*`** ainda **não** têm categoria no schema. **Item herdado, ainda aberto.**
* **Criar uma nota de migração para o `action.yml`:** a troca de `--linter` + `--fullreview` por `gitpr check` é uma quebra de contrato para workflows existentes; o `docs/check-ci` documenta o comando novo, mas não um "antes e depois". **Item herdado, ainda aberto.**
* **Publicar a extensão nos marketplaces:** o workflow está pronto, mas depende de `VSCE_PAT`/`OVSX_PAT`; até lá, a instalação é por VSIX local. **Item herdado, ainda aberto.**
* **🆕 Revisar o `git diff` em repositórios com arquivos binários grandes:** a decodificação com `errors="replace"` resolve o conteúdo legado, mas bytes binários no diff agora chegam ao modelo como uma sequência de `U+FFFD`. Vale confirmar que os smart excludes cobrem os casos reais.
* **🆕 Publicar um release com a migração dos READMEs:** o commit `5ee6025` já está em `main` (PR #223), mas não há tag. O próximo release deve incluí-lo.
* **🆕 Acompanhar o fallback ES/FR no site:** os links dos READMEs já levam `?lang=es_es` e `?lang=fr_fr`, mas o site ainda serve inglês para esses dois idiomas. Publicar as traduções torna os links corretos sem tocar nos READMEs.
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Histogramas de tempo e tendências de tokens na TUI de métricas.
* **Seed de `.gitpr/conf/` local:** O seed de templates de configuração local (smart-excludes, linter) continua pendente como subcomando próprio ou etapa do wizard.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.

### ✅ Concluídos nesta janela (2026-10-18 → 2026-10-27)

* ~~**Fechar o release 1.4.1**~~ — tag `v1.4.1` criada em 2026-10-18 (PR #218), `CHANGELOG.md` commitado em `fafe24b` e pacote publicado. **Item da janela anterior fechado.**
* ~~**Documentar `explain` e `tests`**~~ — `docs/explain-pr.*` e `docs/tests-generate.*` em 5 idiomas, com links no README, nos epilogs e no `HELP_MAP`. **Item da janela anterior fechado** — e a documentação revelou quatro defeitos que também foram corrigidos.
* ~~**Fechar um novo release com a correção de codificação**~~ 🆕 — `4d980e2` (PR #222): decodificação tolerante, exit code 1 em falha do git, `--hook` fail-open, `__version__` 1.4.2, seção `[1.4.2]` no changelog e tag `v1.4.2`.
* ~~**Migrar os links de documentação dos READMEs para o site**~~ 🆕 — 342 destinos em 5 arquivos, `?lang=` por idioma, 217 URLs verificadas com 0 falhas (PR #223).
* ~~**Fechar o bug do `gitpr -h --explain`**~~ 🆕 — dest `explain_flag` → `explain`, com regressão em `test_explain_command.py`.

---

**Relatório gerado em:** 2026-10-27  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
