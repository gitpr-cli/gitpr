# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.26 (2026-11-15)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.26):**
- **A 1.9.0 foi publicada:** `__version__` = **1.9.0**, `CHANGELOG.md` com `## [1.9.0] - 2026-11-15`, tag `v1.9.0` no merge do PR #336 (`3bb8ec6`, que é também `origin/main`) e o PyPI servindo **1.9.0**. A release entrega o suporte a GitHub Enterprise e o `pt-PT` da extensão.
- **O GitHub Enterprise deixou de ser um beco sem saída:** `GitHubProvider.parse_repo_ref` abandonou o regex ancorado no literal `github.com` e passou a usar um `_REMOTE_RE` genérico (prefixo `user@` opcional, host com porta opcional, separador `:`/`/` e exatamente dois segmentos de caminho). Remotes de instâncias Enterprise (`github.acme.com`, HTTP/SSH/porta/credencial embutida) agora parseiam; o `GITHUB_BASE_URL` continua sendo o que retargeta a API.
- **A cobertura de idiomas da extensão VS Code fechou em cinco:** `package.nls.pt-pt.json` (14 chaves) e `l10n/bundle.l10n.pt-pt.json` (26 chaves) entraram ao lado de `en`, `pt-br`, `es` e `fr`. Os bundles do editor deixaram de ser o único artefato do produto fora do `pt_pt`.
- **A paridade de documentação perdeu as exceções silenciosas:** `_EN_ONLY` foi esvaziado em `tests/unit/test_docs_translation_parity.py` e `docs/github-issue-prompt-com-gh.md` foi movido para `docs/extra/`. O `CONTEXT.md` formalizou a distinção **Canonical doc** × **Extra doc**, e a raiz de `docs/` chegou a **51/51 tópicos nos cinco idiomas**.
- **A ADR-0019 virou contrato executável:** `tests/unit/test_project_config_seed_docs.py` (4 cenários) exige a seção `9.4`, o callout `[!IMPORTANT]` e o `GITPR_SKIP_PROJECT_CONFIG_SEED` nas cinco variantes de `pull-request-publication` **e** de `config-tui`, a âncora cruzada validada por slug estilo GitHub, a ADR-0019 e os dois termos no `CONTEXT.md`. `pull-request-publication` saiu de `_PARITY_EXCEPTIONS`.
- **A migração SCM em ambiente efêmero está documentada e travada:** `persisted=False`, `os.environ` e o tratamento de `PermissionError` estão nas cinco variantes de `docs/scm-multiforge.*` e na [ADR-0020](docs/adr/0020-per-repo-scm-provisioning-migration.md), assegurados por teste.
- **O Map-Reduce virou observável fora do código:** custo e latência das `GITPR_MAP_REDUCE_MAX_TOKENS` / `MAX_PART_TOKENS` (e das variantes por provedor) entraram nos cinco idiomas de `docs/metricas-telemetria.*`, e a [ADR-0022](docs/adr/0022-map-reduce-per-provider-token-partitioning.md) passou a referenciar métricas.
- **O `--install` passou a listar `claude-code`:** a mensagem de editor desconhecido em `src/mcp_server.py` (`_install_for_editor`) lista `vscode, cursor, claude-code, claude, zed, auto`, e as seis traduções de `langs/` foram sincronizadas — a mensagem deixou de negar uma opção que a CLI aceita.
- **O levantamento de pendências virou roteiro executável:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` auditou os **25 relatórios de estado** contra o código e organizou **8 etapas** com critérios de aceite; as Etapas 1–7 estão marcadas como concluídas e a Etapa 8 foi executada no código (a marcação no roteiro ficou pendente).
- **Versão atual:** 1.9.0 (**publicada no PyPI**; tag `v1.9.0` no commit `3bb8ec6`, merge do PR #336)
- **Versão dos dicionários de idioma:** v0.0.44 (🆕 +1 desde v0.0.43; entrega por OTA a mensagem de `--install` corrigida)
- **Versão dos scripts de hook:** v0.0.4 (inalterada)
- **Publicação:** PyPI (`pip install gitpr-cli`) — canal binário removido
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal) — **16 subcomandos** (`badge`, `baseline`, `check`, `config`, `demo`, `explain`, `fix`, `mentor`, `metrics`, `policy`, `release`, `review-pr`, `risk`, `seed`, `split`, `tests`). Quatro deles são **grupos**: `baseline` (6 subcomandos), `metrics` (8), `policy` (7) e `tests` (1). **34 opções Click na raiz** — inalteradas nesta janela (`src/main.py` não foi tocado).
* **UI/Terminal:** Textual — TUI para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher, **CommitApp** (`src/ui/commit_app.py`, 220 linhas), erros do linter (`LinterApp`), configuração (`ConfigApp`), modal `NoticeScreen`, o tour do `gitpr demo` (`src/ui/demo/`), o assistente de migração do ledger (`src/ui/metrics_migration_app.py`) e o `PrBaseApp` (`src/ui/pr_base_app.py`). A `MetricsApp` mantém as abas **Events** e **Charts & Trends** com bindings `1`/`2`. Nenhum widget novo nesta janela.
* **Arquitetura em Camadas:** `src/domain/` (regra pura, sem I/O) + `src/application/use_cases/` (orquestração, **15 casos de uso**) + apresentação (CLI/TUI). **9 pacotes de domínio**: `baseline`, `check`, `finding`, `linter`, `mentor`, `policy`, `pr`, `risk`, `tests_generation`. Fora do domínio: `src/issue_autoclose/`, `src/project_config.py`, `src/scm_settings.py` e `src/ascii_chart.py`.
* **Extensão de Editor:** `extensions/vscode/` — cliente TypeScript fino do MCP para **VS Code e Cursor** (Node.js 20+, `@modelcontextprotocol/sdk`, VSIX). Não contém regra de negócio. 🆕 A localização passou de quatro para **cinco bundles** (`package.nls.*` e `l10n/bundle.l10n.*`): `en`, `pt-br`, `es`, `fr` e **`pt-pt`**. A publicação nos marketplaces continua desacoplada da release do pacote.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API, tokens GitHub e tokens SCM das forges.
* **Configuração:** `python-dotenv`, `pyyaml` (linter estático e configuração do projeto) + schema declarativo próprio (`src/config_schema.py`, **115 `ConfigField`** e **18 categorias**). `DEFAULT_CONFIG` é **derivado** dos campos com `seeded=True` (**55 chaves**) — inalterado nesta janela. `packaging` alimenta a comparação de versões do gate (PEP 440) e a compatibilidade dos policy packs.
* **IA Providers:** Integração via SDK oficial do Google GenAI, OpenAI SDK (DeepSeek) e OpenAI SDK (Ollama local). Defaults configurados: `gemini-pro-latest` / `gemini-flash-lite-latest` e `deepseek-v4-pro` / `deepseek-v4-flash`. Limites de Map-Reduce resolvidos **por provider** em `src/config.py`.
* **Forge APIs:** `requests` (REST) — abstração multi-forge em `src/infrastructure/scm/` (GitHub, GitLab, Bitbucket, Azure DevOps) + `web_links.py`; `src/github_api.py` mantido como shim deprecado. 🆕 O provider GitHub deixou de exigir o host literal `github.com` ao resolver o repositório.
* **Linter / SAST:** regex YAML + bridge Checkstyle + ruleset de segredos embutido (`src/security_ruleset.py`) + 4 bridges em `src/infrastructure/linter/external/` (base + Semgrep, Gitleaks, Bandit), com modelo normalizado em `src/domain/linter/sast_finding_mapper.py` e o achado canônico em `src/domain/finding/`.
* **Infraestrutura de CI:** `src/infrastructure/ci/` — `sarif_builder.py` (SARIF 2.1.0), `junit_builder.py` (JUnit XML) e `masking.py` (mascaramento de credenciais antes de serializar qualquer artefato).
* **Git Internals:** `src/infrastructure/git/` — `patch_applier.py`, `selective_stager.py`, `identity.py`, `risk_history_reader.py` e `test_matcher.py`.
* **Persistência local:** `src/ledger.py` — SQLite (`~/.gitpr/metrics/telemetry.db`) com WAL, `PRAGMA user_version`, chaves UUID e transporte por bundle. A tabela de preços vive em `src/config.py` (`DEFAULT_MODEL_PRICES`) e aceita override por modelo e moeda.
* **Rede:** `src/net.bounded_urlopen` (`UPDATE_FETCH_HARD_TIMEOUT = 3.0`) limita o **wall clock incluindo DNS** no gate de atualização. `get_issue()`/`get_default_branch()` usam timeout de **5 s** (`GITPR_ISSUE_AUTOCLOSE_TIMEOUT`).
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 — **18 ferramentas anotadas**, **19 recursos**, 7 prompts (contagem inalterada; o único arquivo tocado foi `src/mcp_server.py`, na mensagem de `--install`).
* **Testes:** Pytest + `unittest.mock` (**167 módulos de teste** — 65 na raiz, 12 em `tests/application/use_cases/`, 10 em `tests/fix/`, 10 em `tests/scm/`, 10 em `tests/infrastructure/` (baseline 1, ci 3, git 2, linter 4), 21 em `tests/domain/` (baseline 5, check 3, finding 1, linter 2, mentor 1, policy 4, pr 1, risk 2, tests_generation 2), 7 em `tests/badge/`, 6 em `tests/demo/`, 6 em `tests/split/`, 5 em `tests/issue_autoclose/`, 4 em `tests/review/`, 3 em `tests/integration/`, **8 em `tests/unit/`** —, **3471 cenários coletados**) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio) + fixtures de repositório git real (`tests/fix/`, `tests/split/`, `tests/test_full_diff_encoding.py`) + guarda de isolamento de rede (`tests/demo/conftest.py`, `tests/badge/conftest.py`, `tests/integration/conftest.py`, `tests/split/conftest.py`). A extensão tem suíte Mocha própria (7 testes contra o servidor MCP real).
* **Empacotamento:** setuptools/build (PyPI) — `version = {attr = "src.updater.__version__"}`; packs embutidos via `package-data`; `packaging>=23.0`. A extensão é empacotada à parte (`vsce package`, VSIX).
* **CI/CD:** GitHub Actions — `pr-review.yml` + `action.yml` (chama `gitpr check`) + `tests.yml` (matriz Python 3.10/3.13) + `extension.yml` (build, teste e empacotamento do VSIX; release próprio em `ext-v*` e gate granular por marketplace) + `release.yml` (testes, verificação tag/versão via SSOT, build sdist/wheel, `twine check --strict`, Trusted Publishing OIDC no PyPI e criação de GitHub Release em tags `v*`).

---

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa o **gatilho do provider** (~90k tokens por default), divide automaticamente em lotes (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce). Suporta PRs, commits e Issues. O `provider`/`model` são agregados entre os chunks e o `meta`/`modules` são repassados a `log_command_metric`.
* **Limiares por Provider:** `get_map_reduce_thresholds(provider)` (em `src/config.py`) resolve em três níveis — `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` / `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>` → `GITPR_MAP_REDUCE_MAX_TOKENS` / `GITPR_MAP_REDUCE_MAX_PART_TOKENS` → defaults **90.000** (gatilho) e **50.000** (lote). `_positive_int_from_raw` recusa valor inválido ou não positivo, e a invariante `max_part_tokens <= max_tokens` é garantida. `gitpr release` não é afetado; `src/issue_engine.py` e `src/review/remote_pr.py::_chunk_count` resolvem pela mesma função.
* **Cascata de Fatiamento:** `_split_giant_file` parte um arquivo individual acima do lote nos seus hunks (`@@`); `_split_line_chunk` parte um hunk monolítico por linhas/caracteres. Cada sublote reanexa o **cabeçalho original** do arquivo e o marcador `# [file - part N]`, e o particionador cai num fallback por linhas quando o texto não tem `diff --git`.
* **Pré-Reduce Intermediário:** se o conjunto de resumos parciais ainda exceder o gatilho, `generate_pr_content` os loteia até `max_part_tokens` e reconsolida por `call_ai_model` **antes** da síntese final, agregando os metadados de telemetria.
* **Tokenizador Local:** `tokenizer.json` para estimativa precisa de tokens antes do envio para a IA.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()` com fallback para tokenizador local.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff`.
* **`get_git_staged_diff()`:** roda `git diff --cached -U1 -w -M -B -- <SMART_EXCLUDES>` com `encoding="utf-8"`/`errors="replace"` e `stdin=DEVNULL`, devolvendo `None` em falha do git (nunca string vazia disfarçada). É a fonte preferida da mensagem de commit.
* **`get_split_diff()`:** Diff próprio do `split`, com `SPLIT_DIFF_ARGS` (`--binary -M -U3`), **deliberadamente sem** reusar `get_git_diff()`.
* **Guarda de Hunk Binário:** todos os pontos de entrada de diff (`get_git_diff`, `get_git_staged_diff`, `get_unstaged_diff`, `get_git_full_diff`, `current_diff`, `get_check_diff`, `tests_generate`, `risk`) aplicam `collapse_binary_hunks()` — hunks com corridas contíguas de ≥8 `U+FFFD` (ou ≥32 com densidade ≥10%) viram `Binary files … differ`. O caminho rápido O(1) devolve o diff intocado quando não há `U+FFFD`.
* **Colapso Defensivo em `generate_pr_content()`:** a função aplica `collapse_binary_hunks(diff_text)` **antes** do timing e da chamada de IA, cobrindo também chamadores externos.
* **Seed da Configuração Local (`seed_project_configuration()`):** cria `.gitpr/conf/gitpr.config.yml`, `.gitpr/conf/gitpr.smart-excludes.json` e `.gitpr/skill/.gitpr.linter.yml`, devolvendo um resumo estruturado. Nunca sobrescreve sem `force=True`.
* **Seed da Configuração do Projeto:** o callback raiz e o `--install` chamam `ensure_project_config()` em toda invocação dentro de um repositório, exceto nos caminhos de ajuda. `GITPR_SKIP_PROJECT_CONFIG_SEED` desliga o auto-seed. 🆕 O comportamento passou a ser exigido nos cinco idiomas por `tests/unit/test_project_config_seed_docs.py`.
* **`get_base_branch(quiet=)`:** a resolução da base delega a `resolve_pull_request_base()`; `quiet` evita que o aviso de fallback corrompa a TUI ou o stream JSON-RPC.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo em JSON antes de cada chamada à IA.
* **Smart Excludes com Duas Camadas:** Camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`), mescladas em runtime. Os loaders ficaram blindados contra `.env` corrompido e paths ilegíveis.
* **Métricas com Rastreamento de Tempo:** `log_command_metric()` em todos os fluxos, com `meta`, `modules` e `duration_ms`.
* **Resolução Centralizada de Output:** `resolve_output_path()` — default em `.gitpr/reports/{type}/`.
* **Wizard SCM (`run_scm_init_wizard()`)**: `gitpr --init` — detecta a forge pelo remote origin, solicita extras por forge, valida o token e persiste **somente em sucesso**; grava no slot da forge escolhida e só cria override no projeto quando ela difere da detectada.
* **Skill Template de Release (`ensure_release_skill_template()`)**: Baixa `templates/gitpr.release.*.md` no primeiro uso de `gitpr release`.
* **Guarda de Skill Corrompido:** `_CORRUPTED_PR_SKILL_ARTIFACT` documenta o fragmento JSON que vazou para o template `pt_br`, e `get_skill_context()` o remove **em memória** quando `action_type == "pr"`.
* **Registro de Skills Compartilhado:** `SKILL_FILES_BY_TYPE` / `SKILL_TYPES` / `DEFAULT_SKILL_TYPE` em `src/config.py`.
* **Motor de Review com Escopo de Cache (`generate_pr_content`):** `cache_scope` e `store_diff`; o `cache_scope` carrega também o pack de política ativo.
* **Trailer de Coautoria:** `COAUTHOR_TRAILER` + `append_coauthor_trailer()` — idempotente, preserva trailers de terceiros.
* **Captura de Saída do Git Endurecida:** as chamadas de `subprocess.run` em `src/cache.py`, `src/core.py`, `src/issue_engine.py` e `src/main.py` que capturam saída do git usam `encoding="utf-8"` **com** `errors="replace"`.
* **Carregamento de `.env` Resiliente:** `load_dotenv()` em `core.py`, `i18n.py` e `spinner.py` roda dentro de `try/except`.
* **Falha de Git ≠ Diff Vazio:** `diff_text is None` encerra com código 1; diff vazio de verdade sai **0**; no `--hook` o caminho é fail-open.
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
* **Routing de Comandos:** Gerencia todas as flags e os **16 subcomandos** — `release`, `config`, `fix`, `review-pr`, `demo`, `badge`, `split`, `tests`, `explain`, `mentor`, `metrics`, `policy`, `risk`, `baseline`, `check` e `seed`.
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags (34 opções Click na raiz):** `-sd/--seed` semeia a configuração local do projeto e sai; `--close-issue`/`--no-close-issue` seguem mutuamente exclusivas, recusadas com exit code 1 antes de qualquer prompt ou escrita, com a regra de que `-h` vence o conflito. As demais (`--mentor`, `--explain`, `--init`, `--no-suggest-reviewers`, `--no-publish`, `--no-edit`, `--base <branch>`, `--plugins`, `--status`, `--no-unstaged-check`, `--linter-setup`, `--version` etc.) seguem inalteradas.
* **Ramo do `-c`/`--commit`:** `--hook` → comportamento silencioso e merge-aware; sem hook → `CommitApp`. O caminho sem hook exige TTY: o roteamento consulta `_may_ask_the_user()` e, num script/CI/pipe, cai no fluxo de console.
* **Fluxo de Fechamento de Issue:** `_prepare_close_issue(flags, base, may_ask)` roda **antes** do Stage Selector, reusa o contexto SCM resolvido e devolve a decisão mais o registro. `_publish_pr_directly` devolve **bool** para que o registro só seja limpo depois de uma publicação real (ADR-007).
* **Resolução da Base do PR:** o ramo `--base` passa por `_resolve_pr_target()`, que corrige um valor obsoleto do arquivo do projeto quando a execução é interativa e, fora dela, relata a recusa.
* **Gate de Atualização nos Subcomandos:** o gate roda antes do `return`, condicionado a `may_ask and not update and not help_flag and not _subcommand_help_in_argv()`. `_may_ask_the_user()` exige **TTY nos dois lados**.
* **`-h` Antes do Subcomando Corrigido:** `_subcommand_help_in_argv()` varre o `argv` bruto e trata o caso `gitpr -h config`. Coberto por `tests/test_cli_help.py`.
* **Subcomando `check` — 8 opções:** `--base <ref>`, `--format sarif|json|junit`, `-o/--output <path>`, `--fail-on …`, `--no-ia`, `--ia-only-high-risk`, `--baseline <path>` e `--policy <name>@<version>`.
* **Subcomando `seed` — 2 opções:** `--force/-f` e `--all/-a`.
* **Grupo `baseline` — 6 subcomandos:** `create`, `show`, `validate`, `update`, `suppress` e `unsuppress`.
* **Grupo `policy` — 7 subcomandos:** `list`, `show`, `validate`, `use`, `off`, `install` e `init`.
* **Grupo `metrics` — 8 subcomandos:** `export`, `bundle`, `merge`, `dashboard`, `migrate`, `prune`, `purge` e o oculto `hook-event`.
* **Subcomando `risk` — 4 opções:** `--file`, `--format text|json`, `--base`, `--no-history`.
* **Subcomando `mentor` — 2 opções:** `--finding`, `--provider`.
* **`DEFAULT_CONFIG` Derivado:** `src/config.py` importa `DEFAULT_CONFIG` de `src/config_schema.py`, montado como `{field.key: field.default for field in FIELDS if field.seeded}` — **55 chaves**.
* **Limites de Map-Reduce no Schema:** seis campos `GITPR_MAP_REDUCE_MAX_TOKENS_{GEMINI,DEEPSEEK,OLLAMA}` e `GITPR_MAP_REDUCE_MAX_PART_TOKENS_{GEMINI,DEEPSEEK,OLLAMA}` na categoria `ai`, filtrados por `show_if` no provedor ativo. São **env-first**.
* **Preços e Moeda no Schema:** `GITPR_METRICS_CURRENCY` (default `USD`) e os oito campos `GITPR_METRICS_PRICE_<MODEL>_{INPUT,OUTPUT}`, todos com `KIND_FLOAT` e default vazio.
* **Variáveis de Ambiente:** as quatro `GITPR_BASELINE_*`, as duas de mentor, as duas de policy e `GITPR_RISK_INCLUDE_IN_REVIEW`. **Fora do `DEFAULT_CONFIG`:** as seis `GITPR_MAP_REDUCE_*`, `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT`, `GITPR_METRICS_CURRENCY`, as **9 `GITPR_CHECK_*`**, `GITPR_SKIP_UPDATE_CHECK`, `GITPR_ISSUE_AUTOCLOSE`, `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` e `GITPR_SKIP_PROJECT_CONFIG_SEED`.
* **Ajuda Contextual:** `gitpr -h --explain` renderiza; `HELP_MAP["explain"]` e `HELP_PRIORITY["explain"]` apontam para `docs/explain-pr`, e `gitpr tests`/`gitpr tests generate` têm `epilog=` próprio.
* **Camada de escrita do `.env`:** `read_env_file_values()` lê **só o arquivo** via `dotenv_values`; `save_config_values()` com `set_key`; `remove_config_value()` com `unset_key`.
* **Portão de Baseline no Fluxo:** `main.py` resolve o gate de baseline antes de lint, review, full review, auditoria de arquivo, review remoto e risk.
* **Publicação Direta Refatorada:** `_publish_pr_directly` (`--no-edit`) delega ao **`publish_pull_request_use_case`** e devolve se a forge criou o PR.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI para revisar, editar e publicar Pull Requests direto no terminal.
* **7 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen` e `NoticeScreen`.
* **Três Delas Também Servem ao Commit:** `StageFilesScreen`, `CommitMessageScreen` e `CommitProgressScreen` são importadas pela `CommitApp` — nenhum widget foi duplicado, e o helper `_with_suppressed_stdout` também é compartilhado.
* **`body_published` Distingue Criar de Abrir:** a `PrPublishApp` marca quando o corpo foi realmente criado/atualizado na forge, e não apenas quando um PR existente foi aberto.
* **Selo no Corpo do PR:** `attach_pr_badge()` roda em `src/main.py` logo após `pr_data` estar completo — **ponto único de injeção**.
* **`_attach_reviewers` com resolução:** Resolve o que o usuário digitou **antes** de enviar, reporta o descartado e, num `422` de lote, **repete um a um**. Quando um provider de terceiros segue o contrato legado e devolve `None` no read-back, o log diz `(no read-back)`.
* **Suggested Reviewers:** Consulta a forge por revisores sugeridos; `_reviewer_suggestion_view()` monta `resolutions` via `resolve_candidates`.
* **Bindings:** F1 (Help), F2 (Salvar .md local), F3 (Publicar via forge), Esc (Sair).
* **Fluxo de Auto-Commit:** Linter → mensagem IA → confirma → commita → push → publica PR.
* **Modal de Progresso no Merge:** `CommitProgressScreen` com `title` opcional e `mark_finished(show_close=False)`; sucesso exibe `✅ PR #N merged successfully!`, conflito e erro inesperado passam pelo `_on_merge_failure`.
* **Tratamento de PR Existente / Auto-Upstream / Merge Flow** — inalterados (`GITPR_AUTO_MERGE`).

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Shim Deprecado:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` e demais funções delegam a `src/infrastructure/scm/github_provider.py`; emite `DeprecationWarning` e mantém as tuplas legadas `(ok, data, status)` — nenhum código novo pode importá-lo.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no diff sem gastar cotas de IA.
* **Regras YAML:** Lê `.gitpr.linter.yml` (criado via `--skill` ou `gitpr seed`).
* **Plugins de Linter:** Regras adicionais de `~/.gitpr/plugins/linter/*.yml`.
* **Wildcard de Extensão:** `extensions: ["*"]` significa **todo** arquivo, inclusive os sem sufixo e dotfiles.
* **Ruleset de Segredos Embutido:** `load_linter_rules()` mescla `src/security_ruleset.py` **depois** das regras do projeto e dos plugins. Sete regras, todas `extensions: ["*"]`: cinco `error` e duas `warning`. O alerta **nunca ecoa o valor**.
* **Camada de Policy Pack:** `load_linter_rules()` aplica o merge em camadas do pack ativo e **sobrescreve severidades**.
* **Achados Estruturados (`findings_out`):** além das strings de alerta, o motor devolve os achados normalizados do tipo canônico `src/domain/finding/`.
* **Bridges SAST Opt-In:** Semgrep, Gitleaks e Bandit rodam no caminho de arquivo inteiro **e** no de diff, com dedup `[Gitleaks + Regex]`, mascaramento de valor (`AKIA****`) e aviso quando a ferramenta está habilitada mas fora do `PATH`.
* **`skip_external`:** `parse_diff_and_lint(..., skip_external=True)` no fluxo remoto.
* **Relatório Consolidado:** `generate_linter_report_content()` consolida erros regex + externos em `.gitpr/reports/linter/` — gerado apenas quando há violações.
* **Baseline-aware:** os alertas são anotados com o status do baseline antes de virarem relatório.

### **7. Segurança e Autenticação (`src/security.py`, `src/scm_settings.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera a chave mestra `secret.key` em `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data`/`decrypt_data` para chaves de IA e para o token de **cada** forge (um slot por provedor SCM).
* **Credencial por Forge:** um token GitLab nunca responde por um repositório GitHub. O `GITPR_SCM_TOKEN` cru continua sendo o **único** override global de CI/CD e é tentado primeiro em toda forge.
* **Validação Multi-Forge:** `validate_or_request_scm_token(provider, repo_display, allow_prompt=True)` — 401 → loop de reautenticação preservando o rascunho. `allow_prompt=False` (hooks, MCP, CI) nunca pergunta, nunca apaga o token salvo e devolve a instrução "rode `gitpr --init`".
* **Segredos na TUI de Configuração:** Campos `KIND_SECRET` são editados mascarados, **nunca** exibem o valor em claro e são cifrados com Fernet antes de gravar.
* **Varredura de Segredos no Fluxo:** O linter — que roda no pre-commit hook — é um portão de credenciais com regras idênticas em toda máquina.
* **Mascaramento na CI:** `src/infrastructure/ci/masking.py` remove chaves privadas, AWS access key ID/secret, tokens GitHub, Google, OpenAI, Slack, `Bearer`, basic-auth em URL e atribuições genéricas de senha **antes** de o artefato ser serializado. A extensão tem um espelho em TypeScript (`masking.ts`).

### **8. Auto-Updater (`src/updater.py`)**

* **PyPI como Fonte Única:** `get_latest_remote_version()` consulta `https://pypi.org/pypi/gitpr-cli/json` e grava o cache. Aceita `force=True`, usado pelo `--update` para **sempre** ir à rede.
* **Janela Corrida de 1 Hora (`UPDATE_CACHE_TTL_SECONDS = 3600`):** o documento é `{"checked_at": <ISO>, "version": ...}`; `_cache_is_fresh()` aceita idade em `[0, 3600)` segundos.
* **Validação na Leitura:** `dict` de verdade, timestamp parseável, versão string não vazia. Timestamp **no futuro** conta como expirado, e o formato legado com `date` é tratado como expirado e reescrito.
* **Escrita Atômica:** `tempfile.NamedTemporaryFile` no mesmo diretório + `os.replace`, com limpeza do temporário em caso de falha.
* **Fetch Blindado (`bounded_urlopen`):** corpo não-JSON e payload sem versão são **rejeitados antes de entrar no cache**. Teto de 3 s de wall clock, DNS incluído.
* **Comparação PEP 440:** `_coerce_version()` usa `packaging.version.Version`, tolerando o `v` inicial e sufixos PEP 440; `parse_version()` mantém o contrato de tupla para chamadores externos. `_is_newer()` **ignora pré-release remoto** numa instalação estável e trata versão ilegível de qualquer lado como desconhecida.
* **Portão Obrigatório (`enforce_update_required()`):** Devolve `True` (após imprimir as duas versões e o comando pip) quando a versão publicada é mais nova; `False` quando está atualizado, quando a versão remota é **desconhecida (offline)** ou quando a checagem está desligada.
* **Semântica Estrita do Escape:** `GITPR_SKIP_UPDATE_CHECK` é parseado contra `_SKIP_TRUTHY_VALUES` (`1`, `true`, `yes`, `on`, `y`), decisão formalizada na [ADR-0021](docs/adr/0021-strict-boolean-update-check-migration.md), e `tests/unit/test_auto_update_docs_parity.py` trava o aviso nos cinco idiomas.
* **`check_and_update()`:** Só consulta e **informa**, nunca instala.
* **Versionamento Centralizado:** `__version__` (**1.9.0** 🆕), `__lang_version__` (**v0.0.44** 🆕), `__scripts_version__` (**v0.0.4**), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`. O SSOT do pacote é contrato explícito ([ADR-014](docs/adr/0014-canonical-package-version-ssot.md)).
* **✅ Estado do release — 1.9.0 publicada:** o PyPI serve **1.9.0**, o `CHANGELOG.md` tem `## [1.9.0] - 2026-11-15` (`3aee652`), o tag `v1.9.0` no origin aponta para `3bb8ec6` (merge do PR #336, que é também `origin/main`) e `v1.8.0` continua em `6cc0508`. ⚠️ O tag `v1.7.0` continua apontando para `b2688c4` (pré-bump, `__version__` 1.6.0) — pendência herdada, ainda aberta.
* **⚠️ Consistência do SSOT (recorrente):** o bump `3aee652` alterou só `src/updater.py` e o `CHANGELOG.md`; `CLAUDE.md` e `GEMINI.md` foram alinhados a **1.8.0** por `9ad079d` e agora estão uma versão atrás outra vez — `tests/unit/test_version_consistency.py` tem **2 falhas** (`test_claude_md_version_matches_ssot` e `test_gemini_md_version_matches_ssot`).

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Histórico de mensagens, input multi-linha, barra de status com bindings visíveis. `ENABLE_COMMAND_PALETTE = False`.
* **Memória por Branch (`src/chat_memory.py`):** Histórico persistido por branch, com continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear`. O `/tests` (e os aliases localizados) delega ao **mesmo caso de uso** que o CLI usa.
* **Auto-Patching (F5), Atualização de Diff (F2), Exportação de Sessão (F6).**
* **Extrator Compartilhado:** F5 e `ctrl+s` chamam `patch_extractor.extract_code_blocks()` — comportamento visível idêntico, sem lógica duplicada.
* **Ajuda Localizada de Verdade:** `ChatHelpScreen` compõe cada linha via `__()`. Os links da ajuda passam por `doc_url()`, com o contrato `?lang=` do site (`es_es`→`es`, `fr_fr`→`fr`) — formalizado na [ADR-0017](docs/adr/0017-documentation-site-language-fallback.md).

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta o idioma do SO na primeira execução e salva em `GITPR_LANG`; o diretório do perfil é criado **antes** de persistir.
* **5 Idiomas, 6 Dicionários:** en_us (padrão/fallback), pt_br, pt_pt, es/es_es, fr/fr_fr.
* **Arquivos Versionados:** `__lang_version__` (**v0.0.44** 🆕) controla a atualização dos pacotes (`langs/*.json`).
* **✅ Cobertura:** os **seis** arquivos têm **1807 chaves** cada (contagem inalterada). A v0.0.44 não adicionou chave — corrigiu o **valor** da mensagem de editor desconhecido nos seis dicionários. `tests/test_i18n.py` segue **22 verdes**.
* **Snapshot de Ambiente (`AMBIENT_ENV_KEYS`):** `frozenset(os.environ)` capturado **imediatamente antes** do `load_dotenv()` de módulo.
* **Cache com Indexação por Idioma:** As respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.
* **Fonte de Tradução em Lockstep:** uma chave nova precisa existir no código, em `langs/pt_br.json` (lista mestra), nos dicts FR/ES de `scripts/sync_all_langs.py` e nos valores curados de `scripts/fix_mangled_i18n_keys.py`; o extrator usa **AST**.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA com caracteres braille e palavras de "pensamento".
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas. `_load_thinking_words()` / `reload_thinking_words()` aceitam `force=`.
* **O Commit TUI Não Usa o Spinner:** a TUI mostra `CommitProgressScreen` com barra animada própria, e a chamada de IA roda numa `threading.Thread` daemon. Em `--hook` o spinner clássico continua sendo o único feedback.
* **Carregamento de `.env` Blindado:** falha de leitura não impede o spinner de iniciar.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini, DeepSeek e Ollama (local), com primário/secundário por provedor.
* **Modo JSON & Parâmetros Determinísticos:** `temperature=0.0` e `top_p=0.1`; fallback automático entre provedores configurados.
* **Timeout de IA:** default de **180s** (`GITPR_AI_TIMEOUT`).
* **Limites de Contexto por Provider:** o Map-Reduce lê o teto dedicado de cada provedor e cai para o genérico. O gatilho e o lote são resolvidos **antes** da primeira chamada, e o pré-reduce usa exatamente o mesmo lote. 🆕 O custo e a latência desse caminho passaram a estar documentados em `docs/metricas-telemetria.*`.
* **Chamadas com `quiet`:** o release e as features novas encaminham `quiet` até a camada de IA, para que o spinner nunca corrompa uma saída `--format json`.
* **Uma chamada por vez, com cache:** mentor e explain reusam o cache MD5 por prompt.
* **Payload Já Parseado:** `parse_explain_payload()` e `generate_test_file` aceitam o **dict** que o provider entrega, com fallback para string JSON crua.
* **Supressão de Stdout no Commit:** `_generate_commit_msg()` redireciona `sys.stdout` para `os.devnull` durante a chamada, restaurando no `finally`.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt, com indexação por idioma.
* **Seleção do Último Review (`resolve_last_review()`):** Escolhe o registro `review`/`fullreview` **mais novo** para um par repo+branch — é a porta de entrada do `gitpr fix` e do `gitpr mentor`.
* **Diff Revisado (`reviewed_diff`):** Campo no topo do registro que guarda o diff efetivamente revisado.
* **Telemetria e Duração:** Persistência de `duration_ms` e `meta_raw`. O release passa a chave de cache por idioma declarado.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` é **ponte de pré-migração**.
* **Efeito da Sanitização de Skill:** como `get_skill_context()` remove o fragmento corrompido do prompt de PR, a chave MD5 muda e respostas antigas contaminadas não são reutilizadas.
* **`git config` Decodificado com Segurança:** as leituras de `user.name`/`user.email` usam `encoding="utf-8"` + `errors="replace"`.
* **O Commit Reusa o Cache:** a TUI chama `generate_pr_content("commit", "commit", diff_text, provider)`, então a mesma mensagem para o mesmo diff não gera uma segunda chamada de IA.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`) e Arqueologia por Blame (`-b`).
* **Publicação Multi-Forge:** F3 cria a issue na forge **resolvida para o repositório** via `provider.create_issue` — Azure DevOps levanta `ScmNotSupportedError`.
* **Map-Reduce para Issues:** Contexto acima do gatilho do provider é dividido e unificado pela mesma `get_map_reduce_thresholds()` do fluxo de PR.
* **Tratamento de 401:** Sinalização de reautenticação sem fechar a aplicação.
* **`git remote -v` Decodificado com Segurança:** a chamada usa `encoding="utf-8"` + `errors="replace"`.
* **Registro Provider-Agnóstico:** após uma criação bem-sucedida em qualquer forge suportada, `register_created_issue()` grava número **e provider** em `.gitpr/conf/issue.yml`. Falhas de bookkeeping são engolidas, e a primeira escrita adiciona o arquivo ao `.gitignore`.
* **Métrica por Forge:** o evento de criação é derivado dinamicamente (`issue:<provider>_create`).

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia evolução e autoria histórica com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos via `log_blame_metric()` com profundidade e número de commits analisados.
* **Agora também alimenta o risco:** o leitor de histórico do score (`risk_history_reader.py`) usa a mesma janela de 90 dias e classifica bugs/reverts por padrão, sem chamar IA.
* **Alimenta a Sugestão de Revisores:** a análise de blame de um PR classifica os arquivos em `files_with_blame`/`files_without_blame`, consumidos pelo resumo da seção 27.

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)**

* **18 Ferramentas MCP Anotadas:** `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`, `list_fix_candidates`, `review_remote_pr`, `get_baseline_status`, `get_usage_metrics`, `run_check` e `publish_pull_request`.
* **🆕 Mensagem de `--install` Completa:** `_install_for_editor` passou a listar `vscode, cursor, claude-code, claude, zed, auto` no erro de editor desconhecido — antes omitia `claude-code`, uma opção que a própria CLI aceita. As seis traduções de `langs/` foram sincronizadas e `test_install_for_unknown_editor_lists_all_valid_options` trava a lista.
* **Parâmetros Opt-In no Contrato:** `review_code` e `full_review` aceitam `mentor: bool = False`; `generate_pr_description` aceita `explain: bool = False`. São **puramente por parâmetro**.
* **19 Recursos + 7 Prompts Templatizados:** `skill://list` + `skill://{pr,commit,review,filereview,issue,blame,release,fix}` + `linter://config` + `baseline://summary` + `prompt://list` + 7 prompts.
* **Registro de Skills Alinhado:** `mcp_server.SKILL_FILES` tem **11 entradas**; `TestSkillRegistryAgreement` passa.
* **Invocação CLI Direta:** `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool sem iniciar o servidor stdio; `gitpr-mcp --list` imprime o registry completo como JSON.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve no `sys.__stdout__` original, com fallback para `buffer` ou re-encode com `errors='replace'` em code pages legadas do Windows.
* **Offload do Event Loop:** Decorator `_offload` (`anyio.to_thread.run_sync`) em todas as tools — a ordem dos decorators importa (`@mcp.tool` **acima** de `@_offload`).
* **Falhas como Erro Estruturado:** as tools devolvem falha **como dado** em vez de levantar.
* **`get_usage_metrics` com Gráficos:** o payload inclui `token_trend` (janela de até 14 dias) e `latency` (média/mediana/P95) — os mesmos números do CLI e do dashboard.
* **Credencial por Repositório:** toda resolução SCM passa por `src.scm_settings`; sem token, a tool responde com o comando que conserta (`gitpr --init`).
* **Métricas MCP:** `run_check` e `publish_pull_request` gravam linhas locais (`mcp:check`, `mcp:publish_pr`).
* **O servidor MCP nunca é bloqueado pelo gate:** `--mcp`/`gitpr-mcp` está na lista de isenções.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório:** Rótulo `📁 Repository: owner/repo` e filtragem estrita por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com `ProgressBar`; os testes aguardam `workers.wait_for_complete()` antes de asseverar.
* **Duas Abas:** `TabbedContent` com **Events** e **Charts & Trends**, com bindings `1`/`2` e `action_switch_tab`.
* **Motor de Gráficos ASCII (`src/ascii_chart.py`):** funções puras, sem Textual e sem dependências novas — `render_vertical_histogram`, `render_token_timeseries` e `render_empty_card`, além dos formatadores `_fmt_tokens` e `_duration_ms_label`.
* **Uma Única Passada de Leitura:** `_load_sections` devolve `(rendered_sections, chart_data)`, capturando os payloads brutos de `latency` e `token_trend` enquanto renderiza as seções textuais.
* **Estado Vazio Instrucional:** sem ledger, a aba de gráficos mostra um card apontando para `gitpr metrics migrate`.
* **Leitura do Ledger:** o dashboard consulta o `telemetry.db` na thread de trabalho, renderizando as seções a partir dos mesmos renderizadores que o CLI usa.
* **Assistente de Migração (`src/ui/metrics_migration_app.py`):** importar os arquivos legados, importar **e** reconstruir do cache, ou "agora não".
* **Artefatos de Exportação Destrackeados:** o `.gitignore` é a única fonte sobre `.gitpr/metrics/export/`.
* **Documentação Sincronizada:** a aba **Charts & Trends**, o histograma de latência e a série de tokens estão descritos nos **cinco idiomas** de `docs/metricas-telemetria.*`.
* **Testes:** `tests/test_ascii_chart.py` (**9 cenários**).

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`, resolvido por `src/infrastructure/git/identity.py`.
* **Eventos de Hook, Linter e Blame:** `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()`. O `gitpr check` grava `command="check"` com `findings_total`/`findings_errors` e exit code.
* **Evento `issue_autoclose`:** uma linha por decisão de fechamento, com `asked`, `accepted` e `skipped_reason` no `meta`.
* **Token Trend (`TOKEN_TREND_MAX_DAYS = 14`):** série diária contínua (dias sem uso entram como zero) com sparkline e barras horizontais por dia.
* **Latency Histogram:** distribuição por faixas com **média, mediana e P95**; eventos sem duração medida ficam de fora.
* **O `duration_ms` não se perde mais:** o ledger usa `meta["duration_ms"]` como fallback antes de gravar `0`.
* **Custo Configurável por Modelo:** `DEFAULT_MODEL_PRICES` precifica os quatro modelos e os aliases `gemini-pro-latest` (**1.25 / 10.00** por 1M tokens) e `gemini-flash-lite-latest` (**0.10 / 0.40**). Os overrides `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT` vencem a tabela; **as duas taxas são obrigatórias**.
* **Moeda Configurável:** `GITPR_METRICS_CURRENCY` rotula o total e, quando não é USD, descarta a tabela embutida. Um total que deixa modelos de fora continua lendo `Total (partial)`.
* **🆕 Map-Reduce Documentado:** os cinco idiomas de `docs/metricas-telemetria.*` passaram a explicar o impacto de custo e latência de `GITPR_MAP_REDUCE_MAX_TOKENS` / `GITPR_MAP_REDUCE_MAX_PART_TOKENS` (e das variantes por provedor), incluindo as colunas `map_reduce`/`chunks_count`/`duration_ms`; a [ADR-0022](docs/adr/0022-map-reduce-per-provider-token-partitioning.md) referencia métricas.
* **Exportação e Limpeza:** `gitpr metrics export` (CSV/JSON), `prune`, `purge` com confirmação interativa, `bundle`/`merge` para transportar e fundir janelas.
* **O Commit Interativo Também Mede:** o caminho `commit` continua gravando a linha de comando com `meta` e `modules`.

### **19. Sincronização de Idiomas dos Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (**v0.0.4**, inalterada).
* **Templates reescritos na janela v0.0.17:** `post-checkout`, `post-merge` e `pre-push` chamam `gitpr --quiet metrics hook-event <nome>`, guardados por `command -v gitpr` e `|| true`.
* **Mapeamento de Sufixos (`HOOK_SCRIPT_SUFFIXES`):** Códigos de interface (`es_es`, `fr_fr`) traduzidos para os sufixos publicados (`.es`, `.fr`).
* **Escolha vs. Estado (`SCRIPTS_LANG` / `SCRIPTS_INSTALLED_LANG`):** Permite **detectar a troca de idioma**.
* **`effective_hook_lang()`:** Resolve o idioma efetivo; `--lang` deixou de ser descartado nesse caminho.
* **Skip de Merge-Source:** O `prepare-commit-msg` pula as fontes `message|merge|squash|commit`.
* **O `prepare-commit-msg` Continua Não-Interativo:** o hook roda com `--hook`, então **nunca** abre a `CommitApp`.
* **Os hooks rodam com `--quiet` e `--hook`, portanto nunca são bloqueados pelo gate de atualização.**

### **20. Bridge de Linters Externos e Assistente Interativo (`src/linter_wizard.py`, `src/ui/linter_app.py`)**

* **Assistente `--linter-setup`:** Wizard com presets numerados (PHP_CodeSniffer, ESLint, Stylelint) e injeção do bloco `external_linters`.
* **Presets Remotos:** `templates/gitpr.linter-presets.json` com cadeia local → download → stale → fallback embutido.
* **TUI de Erros do Linter:** `src/ui/linter_app.py` (Textual) exibe erros críticos e warnings; em hook/quiet imprime e faz `sys.exit(1)`. `ENABLE_COMMAND_PALETTE = False`.
* **Relatório Markdown:** Consolidado em `.gitpr/reports/linter/` apenas quando há violações.
* **A Camada SAST é irmã, não substituta:** os bridges Semgrep/Gitleaks/Bandit alimentam o **mesmo** pipeline de relatório — e também o `gitpr check`.

### **21. SCM Multi-Forge (`src/infrastructure/scm/`)**

* **Abstração Única (`ScmProvider` ABC):** `base.py` define o contrato (dataclasses `RepoRef`, `PullRequestDraft` etc. e `ScmProviderError(provider, http_status, message)` — `http_status` 0 = falha de rede).
* **`IssueInfo` com `is_open`:** o flag booleano remove as comparações frágeis de string de estado na camada de decisão.
* **As Operações de Issue São de Todas as Forges:** GitLab normaliza `opened` → `open` e emite `Closes #N`; Bitbucket normaliza `new`/`open`/`on hold` → `open` e emite `close #N`; Azure DevOps levanta `ScmNotSupportedError` (Work Items não são issues).
* **`list_pull_requests(repo, state, since, until)` — paginado e canônico:** os quatro provedores traduzem os estados canônicos (`open`/`merged`/`closed`/`all`) para o vocabulário nativo, paginam no cursor de cada API e filtram por janela inclusiva de datas.
* **Por que o filtro é por data do estado:** três das quatro forges devolvem algo mais largo para um PR mergeado, então cada uma filtra a própria resposta contra a data que o estado implica.
* **`supports_merged_dates`:** atributo de classe, `False` no Bitbucket Cloud, que publica **vazio** o `merged_at`.
* **`web_links.py`:** funções puras (`repo_web_base`, `commit_url`, `pull_request_url`, `user_url`) normalizam qualquer formato de remote.
* **`get_pull_request(repo, pr_id)` — método concreto da ABC:** default levanta `ScmNotSupportedError` e cada forge implementa.
* **Detecção de Forge:** `detect_provider_from_remote(remote, default=None)` avalia o casamento de `github` **antes** de retornar o default; um host que não nomeia forge recebe aviso explícito de `resolve_scm_settings`.
* **🆕 `parse_repo_ref` Aceita Domínios Customizados:** o regex ancorado em `github.com` foi substituído por `_REMOTE_RE` — `user@` opcional, host com porta opcional, separador `:` (SSH) ou `/` (HTTPS), scheme removido antes do match e **exatamente dois** segmentos não vazios de caminho (`workspace`/`name`), sob pena de `ValueError`. Remotes de **GitHub Enterprise Server** (`github.acme.com`, HTTP/SSH/porta/credencial embutida) passaram a ser aceitos; caminhos com profundidade diferente de dois (subgrupos aninhados) e URLs malformadas continuam recusados. `raw`, `workspace`, `name` e `provider` do `RepoRef` ficam intactos, e `GITHUB_BASE_URL` continua sendo o que aponta a API Enterprise.
* **Resolução por Repositório:** o registry não lê `GITPR_SCM_PROVIDER`; `resolve_scm_provider(config)` recebe o provider já resolvido por `src/scm_settings.py` (seção 46).
* **GitHub:** `GET /repos/{o}/{r}/issues/{n}` (marcando `pull_request` e caindo para o número pedido quando ausente), `GET /repos/{o}/{r}` para `default_branch` (string vazia quando ausente) e o keyword `close #N`.
* **Cabeçalhos do GitLab Sintetizados:** `changes[].diff` é um hunk solto; `old_path`/`new_path` montam os cabeçalhos `diff --git a/… / --- / +++`, honrando `/dev/null`. E `overflow: true` **levanta** em vez de revisar metade de um diff truncado.
* **`request_pull_request_reviewers` devolve `list[str]`:** Devolve os logins **efetivamente anexados**, lidos do corpo do `201` ([ADR-0009](docs/adr/0009-reviewer-attach-returns-read-back.md)).
* **Helpers Read-Only do GitHub:** `get_commit_author_login` e `get_user_login`.
* **Fail-Fast por Forge:** Azure exige `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`; Bitbucket exige `GITPR_SCM_USERNAME`; `create_issue` no Azure levanta `ScmNotSupportedError`.
* **Publicação de Releases:** `provider.create_release()` usado pelo `gitpr release --publish`.
* **Publicação de PR Compartilhada:** `src/application/use_cases/publish_pull_request.py`, usado pelo `--no-edit` e pelo tool MCP. Valida título/corpo, **exige `provider.token` apenas quando `check_remote_state=True`**, opcionalmente verifica PR existente e branch não empurrada, mascara mensagens de erro e devolve `PublishPrOutcome`.
* **Artefatos:** Glossário + ADR-001/ADR-005/ADR-016/ADR-0020; família `docs/scm-multiforge.*.md` em 5 idiomas; **10 arquivos de teste, 373 cenários** (`test_github_provider.py` 83 com a nova `TestParseRepoRef`, `test_scm_settings.py` 28, `test_init_wizard.py` 21, `test_factory.py` 15).

### **22. Subcomando `gitpr release` — Changelog / Release Notes (`src/release_engine.py`)**

* **Fluxo:** `git log` entre `--since` e `HEAD` → classificação por Conventional Commits → bump semântico sugerido → montagem do changelog → resumo executivo de IA opcional → *prepend* no `CHANGELOG.md`.
* **O Range Deixou de Vir do `git describe`:** a origem do range é a **seção anterior do próprio changelog**, por dois âncoras: o hash mais novo daquela seção e, como fallback, a tag da versão da seção.
* **`_drop_released()` — a segunda linha de defesa:** qualquer commit cujo hash curto apareça em **outra** seção de versão é descartado, com contagem.
* **Todo bullet virou link:** `- {subject} ([{short_hash}]({commit_url})) — {scope} · [#{n}]({pr_url}) · {YYYY-MM-DD}`.
* **A falha de PR mergeado por merge commit:** uma segunda passada (`git log --merges`) monta `hash → PR` pela ancestralidade.
* **Contribuidores resolvidos pela mesma escada dos revisores:** `get_commit_author_login` primeiro, depois `email_to_handle`, com cache em `~/.gitpr/cache/contributors.json`.
* **A Fronteira da Seção Era um Bug Latente:** `upsert_changelog(force=True)` substitui da linha `## [x.y.z]` até o próximo cabeçalho de **nível 2**.
* **Front Matter Declara o Idioma do Skill:** `src/skill_frontmatter.py` (`split_front_matter()`) lê um bloco YAML inicial com `language: <code>` (allowlist `en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`), **remove o bloco** antes de o corpo virar instrução de sistema e troca o idioma do i18n pelo tempo da geração.
* **Classificador (`src/commit_classifier.py`)** e **Builder com Seções Traduzíveis (`src/changelog_builder.py`)**.
* **Bump Semântico (`src/version_bump.py`)** e **Publicação** (`--publish`, `--draft`, `--format markdown|json`, `--force`). **6 opções no subcomando.**
* **🆕 Estado do release:** a seção `## [1.9.0] - 2026-11-15` foi gerada por `gitpr release` (artefato `.gitpr/reports/release/develop_natan_20261115190040_RELEASE.md`) e commitada com o bump `3aee652`; o PyPI serve 1.9.0 e o tag `v1.9.0` está no origin. ⚠️ O **sumário** da seção termina com "The release is version 1.8.0" — o resumo de IA cita a versão anterior (mesma classe de defeito editorial que a 1.8.0 tinha, agora na 1.9.0).
* **O subcomando passa pelo gate de atualização** quando executado num terminal interativo.
* **Artefatos:** `docs/release-notes.*.md` em 5 idiomas, ADR e `tests/test_web_links.py`.

### **23. Subcomando `gitpr config` — TUI de Configuração**

* **Tela Master-Detail (`src/ui/config_app.py`):** Categorias à esquerda, campos à direita, editados inline. Cabeçalho com busca (`/`) e contador de pendências; rodapé `F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc`. `ENABLE_COMMAND_PALETTE = False`.
* **Schema Declarativo (`src/config_schema.py`) — a fonte única de verdade:** **18 categorias** e **115 `ConfigField`**, dos quais **7 avançados** e **55 `seeded`**.
* **`DEFAULT_CONFIG` Derivado:** o dicionário é montado a partir de `seeded=True`, então uma chave nova no schema já nasce semeada ou deliberadamente não-semeada.
* **Categoria `check`:** as nove `GITPR_CHECK_*` (`BASE`, `FORMAT`, `OUTPUT`, `FAIL_ON`, `NO_IA`, `IA_ONLY_HIGH_RISK`, `BASELINE_PATH`, `POLICY`, `TIMEOUT_SECONDS`) aparecem aqui, com os mesmos defaults do pipeline.
* **Categoria `smart_excludes`:** substitui o antigo rótulo `Diff Filters`; `SMART_EXCLUDES_VERSION` mudou de grupo e a categoria tem painel próprio.
* **Painel Smart Excludes:** lista de fontes (projeto, global core, global docs), `TextArea` de edição, botão de criação do arquivo do projeto, status/nota e rastreio de dirty.
* **Categoria `project` e o Atributo `store`:** os campos declaram onde moram (`env` vs `project`). Os três campos do projeto são o path do arquivo (read-only), a branch alvo (editável) e a base efetiva com a origem (read-only). O `KIND_BRANCH` renderiza a escolha de branch.
* **Categoria `scm` por Forge:** linha editável `PROJECT_SCM_PROVIDER`, linha read-only `PROJECT_EFFECTIVE_PROVIDER` e um grupo `gitlab`; tokens e base URLs de **todas** as forges são listados sempre, e o teste de token usa o host do próprio slot.
* **Categoria `issue`:** `GITPR_ISSUE_AUTOCLOSE` e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` aparecem aqui.
* **Tipo `KIND_FLOAT`:** o primeiro campo float do schema é `GITPR_METRICS_CURRENCY`, acompanhado dos oito campos de preço por modelo.
* **Categoria `ai` com Preços:** os campos `*_INPUT`/`*_OUTPUT` ficam visíveis quando o `DEFAULT_AI_PROVIDER` correspondente está selecionado. Os seis campos `GITPR_MAP_REDUCE_*` seguem o mesmo `show_if` por provider.
* **Escrita por Store:** a `ConfigApp` despacha por `store`: valores de projeto **nunca** passam por `save_config_values()`, são gravados primeiro, suportam remoção ao esvaziar, recusam a branch atual e nunca sobrescrevem YAML ilegível.
* **Categorias `policy` e `baseline`:** os campos de pack e os quatro do baseline.
* **Seção Skills Alinhada:** `SKILL_LABELS` tem **11 entradas** (`tests`, `explain`, `mentor`).
* **Filtragem por Contexto (`show_if`):** `GEMINI_*`/`DEEPSEEK_*`/`OLLAMA_*` conforme o `DEFAULT_AI_PROVIDER`; `GITPR_SCM_USERNAME` sob `[Bitbucket]`; `GITPR_SCM_ORGANIZATION`/`PROJECT` sob `[Azure DevOps]`.
* **Busca Global (`/`):** Casa chave ou rótulo em todas as categorias e **ignora o filtro de visibilidade**.
* **Validação em Duas Camadas:** **Offline** bloqueia o `F2` com erro inline; **online** (só credenciais alteradas na sessão) roda em worker com timeout de 10s e só bloqueia em `401`/`403`.
* **Restaurar (`Ctrl+R`):** Remove a linha do `.env` em vez de reescrever o default; `Esc` com pendências pede confirmação.
* **Seções Project-Scoped:** Edita `.gitpr/skill/*.md`, `.gitpr/conf/gitpr.config.yml` e o smart-excludes do projeto, gravando atomicamente e preservando CRLF/LF.
* **Downloads com Força:** Botões que forçam re-download de smart-excludes, traduções, presets e thinking words via `force=`.
* **Módulo de Links Leve (`src/doc_links.py`):** `doc_url()` saiu de `core.py` para a UI obter o link sem importar SDKs de IA. `DOC_LANG_PARAMS` mapeia `es_es`→`es` e `fr_fr`→`fr`.
* **🆕 Documentação Traduzida:** as notas de seed/CI e de opt-out (`GITPR_SKIP_PROJECT_CONFIG_SEED`) chegaram às quatro variantes de `docs/config-tui.*`, com âncora cruzada validada por teste contra `pull-request-publication`.
* **Testes:** `test_config_app.py` (94), `test_config_schema.py` (55), `test_config_validation.py` (40), `test_config_store.py` (22), `test_config_cli.py` (9) e `test_config_issue_autoclose.py` (10).

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
* **`render.py` e o risco:** `compose_review_content` / `render_review_result` **antepõem** a seção `⚡ Risk Assessment` acima dos alertas do linter, quando `GITPR_RISK_INCLUDE_IN_REVIEW` está ligado.
* **A contagem de chunks segue o provider:** `remote_pr.py::_chunk_count` resolve o gatilho por `get_map_reduce_thresholds(provider)` em vez da constante de 90k.
* **Documentação completa nos 5 idiomas:** `docs/review-pr.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md` e `.fr_fr.md`.
* **Hunk Binário no Diff Remoto:** `filter_excluded_sections` sempre aplica `collapse_binary_hunks()`, inclusive nos early exits.
* **Testes:** 4 arquivos em `tests/review/` (**97 cenários**).

### **27. Resolução de Identidade do Revisor (`src/reviewer_resolution.py`)**

* **O Bug (duas falhas silenciosas encadeadas):** (1) **Prefill vazio** — `handles` só com `email_to_handle()`; (2) **Attach não verificado** — valores repassados *verbatim*, o GitHub respondia **201 sem anexar ninguém** e o `_request()` retornava sem levantar.
* **Módulo:** Plano, sem I/O próprio, **que nunca levanta**. `resolve_candidates()` (antes da TUI) e `resolve_typed_reviewers()` (no attach); `match_candidate()` casa exato e normalizado por login, nome ou e-mail.
* **Escada de Resolução:** handle conhecido (sem requisição) → casamento exato com uma pessoa sugerida → lookup por e-mail → validação do login na forge.
* **O que não resolve nunca é enviado:** Sai em `ResolutionOutcome.dropped` como `(valor, motivo_i18n)` e é descartado com aviso visível.
* **A Mesma Escada Serve ao Release:** o `release_engine` reusa `get_commit_author_login` + `email_to_handle`.
* **Companheiro Legado:** se um provider de terceiros devolver `None`, o log diz `(no read-back)` e o fluxo segue — um read-back ausente **nunca** é tratado como falha.
* **Resumo de Blame:** `ReviewerSuggestionResult` tem `files_with_blame`/`files_without_blame`; a CLI imprime **uma** linha consolidada — só quando há arquivos sem blame.
* **Testes:** `tests/test_reviewer_resolution.py` (18) + `test_github_provider.py` (83), `test_pr_publish_app.py` (59), `test_suggest_reviewers.py` (19), `test_reviewer_suggestion.py` (18) e `test_main_suggest_reviewers.py` (8).

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
* **Artefatos:** `docs/badge.*.md` em 5 idiomas e o survey dedicado.

### **30. Subcomando `gitpr split` — Commits Atômicos por Hunk (`src/split/`)**

* **O que é:** Uma árvore de trabalho com vários concerns deixa de virar um commit-blob. O `split` lê o diff não commitado, pede à IA que particione os hunks por **intenção lógica** e propõe um commit atômico por concern. A árvore nunca é reescrita.
* **Pacote de 6 arquivos:** `split_plan.py`, `hunk_parser.py` (puro), `hunk_grouper.py`, `generate_split_plan.py` (read-only), `apply_split_plan.py` (**o único que muta**) e `__init__.py`.
* **A Garantia de Árvore Intacta é Estrutural:** `selective_stager.py` pré-valida **todo** grupo contra um índice temporário em HEAD e usa um `GIT_INDEX_FILE` descartável.
* **Destrutivo para o Índice, Não para a Árvore:** O `--apply` reseta o índice para HEAD antes de stagear.
* **Configuração:** `GITPR_SPLIT_MAX_GROUPS` (5), `GITPR_SPLIT_MAX_HUNKS` (50) e `GITPR_SPLIT_REQUIRE_CONFIRMATION` (`true`). Valores zero ou negativos são **ignorados em favor do default**.
* **Relação com a TUI de Commit:** o `split` e o `-c` atacam o mesmo problema em alturas diferentes — o `split` propõe **vários** commits a partir da árvore; a `CommitApp` organiza **um** commit a partir do índice.
* **Testes:** 6 arquivos em `tests/split/` (**101 cenários**).
* **Artefatos:** `docs/split-command.md` em 5 idiomas, ADR-006, `glossary-gitpr-split.md`, spec/plano e survey.

### **31. Varredura de Segredos Embutida (`src/security_ruleset.py`)**

* **O que é:** Sete regras que rodam em **toda** invocação do linter, mescladas ao fim de `load_linter_rules()` depois das regras do projeto e dos plugins.
* **As Sete Regras:** cinco `error` bloqueantes — AWS access key ID, token GitHub, token Slack, chave de API Google e bloco de chave privada — e duas `warning`: URL de conexão de banco com credenciais e atribuição genérica de credencial, esta atrás de um filtro de placeholder.
* **Cobertura:** atribuição **sem aspas**, prefixos **`ASIA…`**, **`github_pat_…`** e **`xoxc-`/`xoxd-`**, **fronteira à esquerda** no nome da chave e supressão de falsos positivos de runtime (`os.getenv(...)`, `process.env.X`).
* **Por que no Pacote e Não no Template:** Um portão de segredos precisa se comportar **igual** em toda máquina e em todo CI.
* **Configuração:** `GITPR_LINTER_SECURITY` (default `true`; opt-out fail-open) e `GITPR_LINTER_SECURITY_DISABLED_RULES` (`;`-separadas).
* **Testes:** `tests/test_security_ruleset.py` (**77 cenários**) — a invariante "o alerta nunca ecoa o valor" segue valendo.
* **Artefatos:** ADR-007, [ADR-0008](docs/adr/0008-secret-ruleset-coverage-extension.md), `glossary-gitpr-secret-scanning.md`, spec/plano/survey e relatórios de tarefa.

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
* **Documentado em 5 idiomas:** `docs/tests-generate.*.md` (5 arquivos), com link no `gitpr tests generate` (epilog) e no README.
* **Skill:** `.gitpr.tests.md` em `SKILL_LABELS`, `mcp_server.SKILL_FILES` e `SKILL_FILES_BY_TYPE`.

### **34. Subcomando `gitpr explain` e a Flag `--explain` — Guia do Revisor (`src/domain/pr/`)**

* **O que é:** Um guia centrado em quem vai **revisar** — o que muda, por que muda, onde focar e qual o risco de regressão.
* **Domain Layer (`explain_section_builder.py`):** `PrExplanation` / `ReviewerFocusPoint`, o renderizador `build_explain_markdown()` e `parse_explain_payload()`, que tolera saída não-JSON e **detecta placeholders** `[FILL]`/`[TODO]`.
* **`parse_explain_payload()` Aceita `dict | str | None`:** o provider entrega o JSON **já parseado**; a função aceita as três formas e normaliza campos `None`.
* **Branch de Chave Ausente:** `generate_pr_explanation` imprime o erro padrão de chave faltante e sai com **1**.
* **Application Layer (`generate_pr_explanation.py`):** Resolução de provedor, validação da chave, carregamento do skill context (`explain`), prompt, invocação e parsing.
* **Duas Portas de Entrada:** `gitpr explain` (`--provider`, detecção de diff ausente antes de qualquer IA) e a flag `--explain` no CLI raiz. A extensão expõe o mesmo caminho em `GitPR: Generate PR Draft (with Reviewer Guide)`.
* **`-h --explain` Consertado:** a opção usava dest `explain_flag`, mas o `HELP_MAP` procurava `explain`.
* **Documentado em 5 idiomas:** `docs/explain-pr.*.md` (5 arquivos), com link no `HELP_MAP["explain"]`, no epilog do comando e no README.
* **Configuração:** `GITPR_EXPLAIN_BY_DEFAULT` (default `false`).

### **35. Suíte Determinística e o CI (`.github/workflows/tests.yml`, `release.yml`)**

* **O que é:** O workflow que roda a suíte em **Python 3.10** (o piso declarado em `pyproject.toml`) e **3.13**, com `fail-fast: false`.
* **`tests/conftest.py` Hermético:** Pina `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false` e `LANG_VERSION` na versão do código, além de `GITPR_SHOW_LOGS=false`, `GITPR_SKIP_UPDATE_CHECK=true` e `GITPR_SKIP_PROJECT_CONFIG_SEED=true`.
* **Fixtures Autouse Contra Vazamento de Perfil:** `english_interface` e `no_hook_script_sync` impedem que o idioma, as flags de linter e o auto-sync de hooks do perfil do desenvolvedor vazem entre os testes de CLI.
* **Ordem Importa:** `src.updater` é importado **antes** das variáveis de idioma serem definidas.
* **Estabilidade de Testes de Worker:** `test_config_app.py` e `test_metrics.py` aguardam `workers.wait_for_complete()` antes de asseverar.
* **Dependência do Workflow:** O runner limpo não tem `~/.gitpr`, e `test_demo_isolation.py` assevera que o perfil existe — o job cria o diretório e o `.env` vazio explicitamente.
* **🆕 Nesta janela a suíte ganhou 1 módulo e 2 cenários líquidos:** `tests/unit/test_project_config_seed_docs.py` (**4 cenários**) entrou, `test_mcp_server.py` foi de 117 para **118** (`test_install_for_unknown_editor_lists_all_valid_options`), `test_github_provider.py` recontado em **83** com a `TestParseRepoRef`, e os testes de paridade de documentação foram endurecidos sem mudar de contagem (`test_docs_translation_parity.py` 3, `test_scm_multiforge_docs_parity.py` 3). **Total: 3471 cenários em 167 arquivos.**
* **🆕 A família de paridade de documentação ficou sem exceções de idioma:** `_EN_ONLY = {}` — a estrutura continua existindo como escape hatch, mas nenhum documento a usa. `_PARITY_EXCEPTIONS` mantém sete dívidas registradas (`ARCHITECTURE`, `check-ci`, `git-hooks-locais`, `git-status`, `linter-regras-customizadas`, `mentor-mode`, `skill-template`); `pull-request-publication` saiu da lista porque a paridade passou a ser real.
* **🆕 O teste de âncora cruzada é de verdade:** `tests/unit/test_project_config_seed_docs.py` calcula o slug no estilo GitHub (`_github_heading_slug`) para validar o link de `config-tui` para a seção `9.4` de `pull-request-publication` — renomear o heading quebra o teste em vez de produzir um link morto.
* **⚠️ 2 falhas conhecidas:** `tests/unit/test_version_consistency.py::test_claude_md_version_matches_ssot` e `::test_gemini_md_version_matches_ssot` falham porque `CLAUDE.md`/`GEMINI.md` ainda dizem 1.8.0 enquanto `src/updater.__version__` já é 1.9.0.
* **Workflow da extensão:** `.github/workflows/extension.yml` roda `npm install`, compila, testa e empacota o VSIX. O job `github-release` anexa o `.vsix` aos GitHub Releases de tags `ext-v*`; o job `publish-marketplaces` avalia cada PAT de forma independente e é não-bloqueante.
* **Workflow de Release:** `release.yml` roda testes, verifica a consistência tag ↔ `src.updater.__version__`, builda sdist/wheel, valida com `twine check --strict`, publica por Trusted Publishing (OIDC) e cria o GitHub Release.

### **36. Ledger SQLite de Telemetria (`src/ledger.py`, `src/infrastructure/git/identity.py`)**

* **O Problema Não Era o Formato, Era o Join:** os eventos eram gravados como arquivos JSON por comando, a partir de uma **thread daemon**, e depois reconectados ao cache de IA por um casamento heurístico de `(repo, branch, ação, minuto)`.
* **A Escrita é Síncrona, e Isso é a Decisão:** `log_command_metric()` resolve o contexto de git **uma vez por processo** e grava a linha na hora.
* **Schema Versionado:** `SCHEMA_VERSION` + `PRAGMA user_version`, chaves UUID, WAL + `synchronous=FULL`, e `LedgerVersionError` para recusar um bundle mais novo **antes** do `ATTACH`.
* **Invariante "Nunca Nasce Vazio":** `ensure_ledger()` só cria o banco **junto** com a absorção dos JSON legados.
* **Uma Janela, Um Significado:** `--since`/`--until`/`--days` estreitam **toda** superfície de leitura; a seção de ciclo assume os últimos 30 dias e **nomeia a janela**.
* **Cada Métrica é Computada uma Vez e Renderizada uma Vez:** os pares `(style, text)` fazem CLI e dashboard Textual contarem a **mesma** história.
* **Custo com Tabela Embutida e Override:** preços de lista dos quatro modelos, sobrescritos por `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT`. **As duas taxas são obrigatórias**. `GITPR_METRICS_CURRENCY` controla o rótulo.
* **`modules` Normalizado:** caminhos viram dois segmentos (`src/fix`), `(root)` e `(no module)`.
* **Transporte por Bundle:** `bundle` escreve a janela como um `.db` autônomo; `merge` o anexa e insere por UUID.
* **`cache_backfill` Fica de Fora:** linhas reconstruídas do cache são excluídas dos agregados de execução.
* **`issue_autoclose` Entra no Ledger:** uma linha por decisão, com `asked`, `accepted` e `skipped_reason`.
* **`duration_ms` com Fallback de `meta`:** eventos que só carregavam a duração em `meta["duration_ms"]` deixaram de ser gravados como `0`.
* **Identidade de Git sem Forge (`identity.py`):** rótulo de repo, branch e autor numa **única** chamada de subprocesso.
* **A Seção de Ciclo é a Única que o Ledger Não Responde:** lista PRs mergeados via `ScmProvider.list_pull_requests`; toda falha degrada para `Not read: <razão>`.
* **Apresentação Completa:** grupo `gitpr metrics` com 8 subcomandos, dashboard lendo o ledger em thread de trabalho e o assistente de migração de três opções.
* **Testes:** `tests/test_metrics.py` (**175 cenários**).

### **37. Subcomando `gitpr mentor` e a Flag `--mentor` — Modo Mentor (`src/domain/mentor/`)**

* **O que é:** Um review diz *o que* está errado e quase nunca *por que aquilo importa*. O Modo Mentor enriquece achados com **o que está acontecendo**, **por que importa**, uma **analogia** do dia a dia e os **conceitos a estudar**.
* **Domain Layer Puro (`mentor_explanation_builder.py`):** sem I/O, converte o payload da IA em `MentorExplanation` validado e impõe **honestidade epistêmica**: sem evidência suficiente, a explicação **diz isso**; URLs alucinadas são **removidas**; IDs desconhecidos são **rejeitados**.
* **Application Layer (`generate_mentor_explanation.py`):** coleta candidatos, **lotes de no máximo 10 achados**, ordenados por severidade, reusando o cache MD5 por hash de prompt.
* **Duas Portas de Entrada:** `gitpr mentor [--finding <id>] [--provider <nome>]` e a flag `--mentor`, que anexa a seção à revisão normal.
* **Opt-In Estrito:** `GITPR_REVIEW_MENTOR_MODE` (default `false`) e `GITPR_MENTOR_INCLUDE_ANALOGY` (default `true`), editáveis na TUI de configuração.
* **Skill e Registro:** `.gitpr.mentor.md` registrado em `SKILL_FILES_BY_TYPE`, em `mcp_server.SKILL_FILES` e em `SKILL_LABELS`, com templates em **5 idiomas**.
* **Testes:** `tests/domain/mentor/test_mentor_explanation_builder.py` (8), `tests/application/use_cases/test_generate_mentor_explanation.py` (5) e `tests/test_mentor_cli.py` (4).
* **Artefatos:** `docs/mentor-mode.*.md` em **5 idiomas**, ADR-009, `glossary-gitpr-mentor.md`, spec e relatórios de tarefa.

### **38. Subcomando `gitpr risk` — Score de Risco Determinístico (`src/domain/risk/`)**

* **O que é:** Um score **0–100** com nível `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`, calculado **sem IA** a partir de sinais locais.
* **Domain Layer Puro (`risk_types.py`, `risk_rules.py`, `risk_calculator.py`, `risk_explanation.py`):** enums e dataclasses; pesos, limiares, padrões de caminho crítico, casamento por glob e detecção de teste/não-executável carregados de YAML; cálculo por arquivo com **clamp 0–100** e agregação 50/30/20.
* **A Fórmula é Declarada, Não Aprendida:** **50%** o arquivo de maior risco, **30%** a média ponderada por linhas e **20%** evidência crítica.
* **Infrastructure Adapters:** `risk_history_reader.py` lê `git log` e extrai commits, correções de bug e reverts numa janela de **90 dias**; `test_matcher.py` casa arquivo de teste ↔ produção por convenção.
* **Use Case (`calculate_risk.py`):** correlaciona seções do diff, achados, casamento de testes e histórico em `FileRisk`/`PullRequestRisk`, **degradando com aviso** quando um sinal não está disponível.
* **Path Tolerante:** a agregação do `check` aceita `path` **ou** `file_path`.
* **Três Consumos:** o comando `gitpr risk`, a seção `⚡ Risk Assessment` anexada a reviews e ao review de PR remoto, e o **prompt da IA** como contexto **read-only**.
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
* **O Contrato Virou Teste:** `tests/integration/test_baseline_exit_code_contract.py` (8 cenários) trava os dois códigos.
* **Alcance:** CLI (6 subcomandos, todos com `--format json`), MCP (`get_baseline_status` + `baseline://summary`), review de PR remoto e o fluxo de lint.
* **Refatoração que a Feature Exigiu:** `NormalizedFinding` virou tipo canônico em `src/domain/finding/`.
* **Testes:** `tests/domain/baseline/` (5 arquivos, **126**), `tests/application/use_cases/` (5 arquivos, **141**), `tests/infrastructure/baseline/test_local_baseline_repository.py` (24), `tests/domain/finding/test_finding_types.py` (3), `tests/domain/linter/test_structured_findings.py` (44), `tests/test_baseline_cli.py` (54) e `tests/integration/test_baseline_effect_on_review_linter_risk.py` (34) + `tests/integration/test_baseline_exit_code_contract.py` (8).
* **Artefatos:** `docs/baseline-suppressions.*.md` em **5 idiomas**, ADR-012, `glossary-baseline.md`, spec/plano/survey e relatório de tarefa.

### **41. Subcomando `gitpr check` — Portão Unificado de CI (`src/domain/check/`, `src/infrastructure/ci/`)**

* **O que é:** Um **único ponto de entrada** para pipelines de CI que orquestra análise estática, bridges SAST, varredura de segredos, review de IA opcional, score de risco e classificação de baseline, e emite **um artefato padronizado** com código de saída determinístico.
* **A Ordem do Pipeline é Contrato:** (1) resolução de policy — inválida sai com `2`; (2) extração do diff com smart excludes; (3) linter regex + segredos + bridges externos; (4) score de risco preliminar; (5) **review de IA opcional**; (6) classificação de baseline; (7) avaliação do limiar `--fail-on`; (8) geração do artefato com **mascaramento de segredos**.
* **Domain Layer (`src/domain/check/`):** `check_types.py` (severidade normalizada em três níveis com aliases de spec); `check_config.py` (precedência **CLI > env > defaults**); `check_output.py` (dispatch de formato e escrita atômica).
* **Infrastructure Layer (`src/infrastructure/ci/`):** `sarif_builder.py` (SARIF 2.1.0), `junit_builder.py` e `masking.py`.
* **Use Case (`run_check.py`):** `resolve_diff_base()` (explícito → `GITHUB_BASE_REF` → `origin/main` → `HEAD`), execução do linter e dos bridges, score de risco, review opcional, baseline e envelope final. O stdout emite **só o artefato**.
* **Códigos de Saída:** `0` sucesso; `1` achado contável no limiar; `2` erro de execução.
* **CLI:** `gitpr check` com 8 opções e 9 variáveis `GITPR_CHECK_*`, também na TUI de configuração (categoria `check`).
* **GitHub Action Reescrita:** `action.yml` virou um único passo `gitpr check`. **Quebra declarada** para workflows que dependiam de `--linter` + `--fullreview` ([ADR-0011](docs/adr/0011-action-unified-check-migration.md)).
* **A Nota de Migração Virou Teste:** `tests/unit/test_check_ci_docs_parity.py` exige as 5 variantes de idioma de `docs/check-ci.*`, as 7 seções e os termos `action.yml`, `--linter`, `--fullreview`, `gitpr check` e `SARIF`.
* **Testes:** `test_run_check.py` (8), `test_check_types.py` (8), `test_check_config.py` (3), `test_check_output.py` (3), `test_masking.py` (6), `test_sarif_builder.py` (2), `test_junit_builder.py` (2), `test_check_cli.py` (5), `test_baseline_exit_code_contract.py` (8) e `test_check_ci_docs_parity.py` (3).
* **MCP:** o tool `run_check` devolve o envelope JSON do mesmo pipeline, com `no_ia` default `true`.
* **Artefatos:** `docs/check-ci.*.md` em **5 idiomas**, ADR-013 + ADR-0011, `glossary-check-ci.md`, spec, `plansfacts` e survey.

### **42. Extensão de Editor — VS Code e Cursor (`extensions/vscode/`)**

* **O que é:** Uma extensão **thin client** que leva os fluxos do GitPR para dentro do editor sem reimplementar nada: ela inicia o `gitpr-mcp` por stdio e chama as tools existentes. Chaves, tokens, prompts e cache continuam em `~/.gitpr/`, cifrados com Fernet.
* **Arquitetura:** `GitPrMcpClient` sobre `@modelcontextprotocol/sdk` + `SessionManager` com **uma sessão por pasta** (multi-root) + verificação de contrato na conexão: as 7 tools obrigatórias precisam existir; se não, `MissingMcpToolsError` instrui `pip install --upgrade gitpr-cli`.
* **8 Comandos:** `gitpr.commit`, `gitpr.review`, `gitpr.fullReview`, `gitpr.reviewMentor`, `gitpr.generatePr`, `gitpr.generatePrExplain`, `gitpr.publishPr` e `gitpr.check`.
* **Publicação em Duas Etapas:** `generatePr` abre um documento Markdown editável; `publishPr` pede confirmação modal e trata `success`, `needs_push`, `already_exists`, `auth_required` e `error`.
* **Diagnósticos no Painel Problems:** `run_check` é convertido em `DiagnosticCollection("gitpr")`.
* **Mascaramento em Profundidade Dupla:** `masking.ts` espelha `src/infrastructure/ci/masking.py`.
* **🆕 Localização Completa em Cinco Idiomas:** além de `en`, `pt-br`, `es` e `fr`, entraram `extensions/vscode/package.nls.pt-pt.json` (14 chaves: `displayName`, `description`, títulos de comando e descrições de configuração `mcpCommand`, `mcpArgs`, `provider`, `checkUseAI`) e `extensions/vscode/l10n/bundle.l10n.pt-pt.json` (26 chaves de runtime: geração de commit, review, rascunho/publicação de PR, prompts de autenticação e notificações do GitPR Check). A UI do GitPR continua com 5 idiomas e a extensão se iguala a ela.
* **Metadados de Marketplace:** `package.json` tem `icon` (`images/icon.png`), `homepage` e `bugs.url`; o pacote carrega `LICENSE` (LGPL-2.1).
* **Release do VSIX Desacoplado:** o `extension.yml` tem um job dedicado `github-release` que anexa o `.vsix` compilado aos GitHub Releases oficiais de tags `ext-v*`.
* **Gate Granular de Marketplace:** o job `publish-marketplaces` avalia `VSCE_PAT` e `OVSX_PAT` **independentemente**, não bloqueia o restante do workflow e reporta cada resultado no `$GITHUB_STEP_SUMMARY`.
* **Guia de Marketplace em 5 Idiomas:** `docs/marketplace-publishing-guide.*` nos cinco idiomas, com teste de paridade travando tokens, etapas e links.
* **Wizard de Credenciais (`scripts/marketplace-setup-wizard.sh`):** CLI interativo de **5 estágios** — pré-requisitos (`gh`, `npx`) → criação do PAT do Azure DevOps → validação de `VSCE_PAT` por `npx @vscode/vsce verify-pat` → registro do namespace Open VSX → validação de `OVSX_PAT` por `npx ovsx verify-pat`. É **re-executável**, faz upsert idempotente no `.env` e lista no fim o que ainda depende de ação manual.
* **O Que a Extensão Não Faz:** não commita, não faz push e não publica sem confirmação. O comando `gitpr.commit` da extensão chama a tool MCP `generate_commit_message` — ele **não** abre a TUI.
* **Testes:** suíte Mocha própria (7 cenários, incluindo stdio real) + `tests/test_mcp_server.py` (**118 cenários**). 🆕 Não existe hoje um teste que compare o conjunto de chaves dos bundles `pt-pt` com o inglês — a validação da Etapa 8 foi manual.
* **Artefatos:** `docs/editor-extension.*` em **5 idiomas**, `docs/marketplace-publishing-guide.*` em **5 idiomas**, [ADR-014](docs/adr/0014-canonical-package-version-ssot.md), `glossary-editor-extension.md`, specs, `plansfacts` e relatórios.

### **43. TUI de Commit Interativo (`src/ui/commit_app.py`)**

* **O que é:** `gitpr -c`/`--commit` deixou de ser um pipeline silencioso — validava a árvore, pedia a mensagem à IA e commitava de imediato, sem deixar escolher arquivos, revisar o texto ou recusar uma sugestão ruim. Agora é uma `CommitApp(App)` de **4 etapas** que mantém o desenvolvedor no controle até o `git commit`.
* **Pacote:** um módulo só, `src/ui/commit_app.py` (220 linhas). Os três modais são **importados** de `src/ui/pr_publish_app.py` (`StageFilesScreen`, `CommitMessageScreen`, `CommitProgressScreen`) junto com `_with_suppressed_stdout` — **zero widget duplicado**.
* **As 4 Etapas:**
  1. **Stage Selector:** se há arquivos fora do índice, abre `StageFilesScreen` com checkboxes, "Select All", "Deselect All", "Stage Selected", "Skip Staging" e "Cancel". Índice já completo → a etapa é pulada.
  2. **Geração:** lê `get_git_staged_diff()`, cai para `get_git_diff()` quando nada está staged, e chama `generate_pr_content("commit", "commit", diff_text, provider)` numa `threading.Thread` daemon enquanto o `CommitProgressScreen` anima.
  3. **Revisão:** `CommitMessageScreen` mostra a mensagem, que pode ser editada antes de confirmar — a mensagem **editada** é a que vai para o git.
  4. **Execução:** novo `CommitProgressScreen` roda `execute_git_commit(append_coauthor_trailer(msg))` e registra o SHA no log.
* **Toda Falha Vira Estado, Não Exceção:** a IA quebrada cai para `__("Code update")`; o commit que levanta vira `failed` com a saída capturada. Estados terminais: `no_changes`, `cancelled`, `committed`, `failed`.
* **Auto-Exit no Sucesso:** `log.mark_finished(False)` remove o botão, e `_schedule_auto_exit()` registra `set_timer(0.6, self.exit)`. **Em erro o Close é mantido.**
* **`--hook` Intocado:** o caminho de hook continua sem TUI e merge-aware (`is_merge_in_progress()` → `return` silencioso).
* **Guarda de TTY:** sem `--hook`, o roteamento consulta `_may_ask_the_user()`; com TTY, abre a `CommitApp`; sem TTY (CI, pipe, cron), cai no fluxo de console silencioso.
* **Configuração:** `GITPR_SKIP_UNSTAGED_CHECK` e `GITPR_AUTO_STAGE`, ambos no `DEFAULT_CONFIG` e no schema da TUI de configuração.
* **Detalhes de Textual:** `ENABLE_COMMAND_PALETTE = False`; `on_button_pressed` trata o `#btn_close`; `_on_commit_progress_dismissed` lê `_commit_success` em vez de assumir sucesso quando o modal fecha.
* **Estabilidade no Windows:** o teste do fluxo headless completo é pulado em `win32`; o roteamento com/sem TTY mocka a checagem de internet.
* **Testes:** `tests/test_commit_app.py` (**17 cenários**).
* **Artefatos:** `docs/commit-message-ia.*` nos **5 idiomas** e o relatório de tarefa do Gemini.

### **44. Fechamento Automático de Issues (`src/issue_autoclose/`) — Multi-Forge**

* **O que era:** a issue criada com `gitpr -is` era órfã — o número existia só dentro da TUI de issue e se perdia no instante em que ela fechava. Todo PR tinha de ser vinculado à mão, e o merge não fechava nada.
* **Pacote de 5 arquivos:** `issue_registry.py`, `register_created_issue.py`, `resolve_close_issue.py`, `insert_close_line.py` e `__init__.py`.
* **Registro Provider-Neutro (`IssueRegistry`):** o arquivo passou de `.gitpr/conf/github.yml` para **`.gitpr/conf/issue.yml`**, com um campo `provider` (default `github`). O `github.yml` legado é **lido** de forma transparente quando o novo não existe e é apagado na próxima escrita/limpeza.
* **Auto-Ignorando com Precisão:** `record()` roda `git check-ignore` antes da primeira escrita e acrescenta exatamente uma linha ao `.gitignore` quando o arquivo não está coberto.
* **Registro na Criação:** `register_created_issue()` grava número **e provider** de qualquer forge suportada e engole falhas de bookkeeping. O desfecho antigo `not-github` virou `no-provider`.
* **Decisão (`resolve_close_issue`):** barra por flags e configuração, mas **não** mais por forge; cada forge sem suporte degrada para `skipped_reason="not-supported"`. Verifica que a issue ainda está **aberta** e **não é um PR** (preferindo `IssueInfo.is_open`), apaga registros mortos e pergunta **uma vez**.
* **Linha Idempotente (`insert_close_line`):** detecta qualquer keyword existente (`close/closes/closed`, `fix/fixes/fixed`, `resolve/resolves/resolved`, com prefixo `owner/repo#N` opcional, case-insensitive) e nunca duplica a linha.
* **CLI:** `--close-issue` e `--no-close-issue` — mutuamente exclusivas, recusadas antes de qualquer prompt ou escrita; `-h` vence o conflito.
* **Fiação no Fluxo de PR:** `_prepare_close_issue` roda **antes** do Stage Selector e reusa o contexto SCM resolvido; `_publish_pr_directly` devolve se a forge realmente publicou; `PrPublishApp.body_published` distingue criar/atualizar de apenas abrir um PR existente (ADR-007).
* **Contrato SCM:** `IssueInfo` (state no vocabulário da forge, `is_open` e `is_pull_request`), `get_issue()`, `get_default_branch()` e `closing_line()` são defaults concretos da ABC; GitHub, GitLab e Bitbucket implementam, e o Azure DevOps levanta `ScmNotSupportedError`.
* **Configuração:** `GITPR_ISSUE_AUTOCLOSE` (default `true`, opt-out) e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` (default `5`), expostas na categoria `issue` da TUI.
* **Telemetria:** uma linha `issue_autoclose` por decisão (`asked`, `accepted`, `skipped_reason`).
* **Testes:** 5 arquivos em `tests/issue_autoclose/` (**126 cenários**).
* **Artefatos:** [ADR-010](docs/adr/0010-multiforge-issue-autoclose.md), `docs/specs/issue-autoclose/`, `docs/issue-autoclose.*` em **5 idiomas**, `docs/issue-tui-help.*`, `docs/config-tui.*` e `docs/metricas-telemetria.*`, README nos 5 idiomas e relatórios de tarefa.

### **45. Base do PR por Projeto (`src/project_config.py`, `src/ui/pr_base_app.py`)**

* **O que era:** a branch de destino do PR vivia só no `~/.gitpr/.env` da máquina (`PR_DEFAULT_BASE`) ou era adivinhada por `origin/HEAD`. Um repositório que mira `develop` dependia de cada desenvolvedor configurar a mesma variável.
* **O que é:** `.gitpr/conf/gitpr.config.yml` — arquivo **versionado com o projeto** que carrega a base do PR, editado pela TUI de configuração e validado antes de qualquer commit/push.
* **Resolvedor (`src/project_config.py`):** `resolve_pull_request_base()` — `--base` → arquivo do projeto → `PR_DEFAULT_BASE` → detecção `origin/HEAD` → `main`. Leitura/escrita YAML preserva chaves alheias; seeding idempotente; listagem de branches; detecção da branch atual; verificação contra o remoto.
* **Segunda Seção (`scm:`):** o arquivo também carrega `scm.provider` (leitura/escrita), com as duas seções independentes e recusa a sobrescrever um bloco `scm` que não seja mapping.
* **Falha Antes do PR Nascer:** `BaseBranchError`/`CurrentBranchError`; a base precisa existir em `origin/<branch>` e diferir da branch atual.
* **TUI de Configuração:** categoria `project` com atributo `store` (`env` vs `project`), `KIND_BRANCH` e três campos: path do arquivo (read-only), branch alvo (editável) e base efetiva com a origem (read-only).
* **Modal de Reparo (`src/ui/pr_base_app.py`, 98 linhas):** quando o alvo é a própria branch atual e a execução é interativa, um modal focado pede a branch substituta e grava no arquivo do projeto.
* **CLI:** `--base` passa por `_resolve_pr_target()`; o arquivo é semeado em toda invocação dentro de repositório (exceto ajuda); `GITPR_SKIP_PROJECT_CONFIG_SEED` desliga o seed. `gitpr seed` faz o mesmo de forma explícita e idempotente.
* **Fronteira Formalizada:** a [ADR-0019](docs/adr/0019-project-configuration-seed-segregation.md) separa o **auto-seed de runtime** do **provisionamento explícito**. 🆕 Essa fronteira passou a ser exigida por teste nas cinco variantes de idioma (`test_project_config_seed_docs.py`).
* **MCP:** `publish_pull_request` usa o resolvedor compartilhado, devolve envelope de erro para `BaseBranchError` e expõe `warnings` no payload e no catálogo.
* **Efeito Colateral Declarado:** rodar `gitpr` num repositório passa a criar o arquivo na primeira execução. Arquivo existente nunca é sobrescrito; se o `.gitignore` exclui o caminho, um aviso explica que o valor não será versionado.
* **Testes:** `tests/test_project_config.py` (**49**), `tests/test_project_config_cli.py` (7), `tests/test_pr_base_app.py` (12) + ampliações em `test_config_app.py` (94), `test_config_schema.py` (55), `test_config_store.py` (22), `test_mcp_server.py` (118) e `test_core.py` (49).
* **Artefatos:** [ADR-015](docs/plans/ADR-015-project-local-pr-base.md), [ADR-0019](docs/adr/0019-project-configuration-seed-segregation.md), `docs/plans/develop_natan/20261030_project_pr_base_plansfacts.md`, `docs/survey/20261030_project_pr_base_surveyfacts.md` e os tópicos `docs/config-tui.*`/`docs/install-wizard.*`/`docs/pr-descricao-padrao.*`/`docs/pull-request-publication.*` nos 5 idiomas.

### **46. Configuração SCM por Repositório e por Forge (`src/scm_settings.py`)**

* **O que era:** a forge (`GITPR_SCM_PROVIDER`), o token (`GITPR_SCM_TOKEN_ENCRYPTED`) e a base URL eram configurações **globais da máquina** em `~/.gitpr/.env`.
* **O que é:** a forge e a credencial são **propriedade do repositório** ([ADR-016](docs/plans/ADR-016-per-provider-scm-settings.md)). Um único resolvedor responde "qual forge, qual token, qual base URL valem aqui?" para todas as superfícies.
* **Ordem de Resolução (`resolve_provider_choice`):** override do projeto (`scm.provider`) → `detect_provider_from_remote(origin, default=None)` → `github`. Um valor de forge desconhecido no arquivo do projeto é **ignorado com aviso**, nunca fatal.
* **A Regressão Corrigida:** `detect_provider_from_remote` retornava o `default` **antes** de testar `github`, então todo remote `github.com` era "desconhecido" quando o chamador pedia `default=None`. Um teste de regressão cobre HTTPS e SSH.
* **Aviso de Fallback Explícito:** `_default_provider_warning()` é emitido por `resolve_scm_settings` quando existe remote mas a forge veio do default. Sem remote, o aviso **não** aparece, e um override no projeto o silencia.
* **Um Slot por Forge:** `GITHUB_TOKEN_ENCRYPTED`, `GITLAB_TOKEN_ENCRYPTED`, `BITBUCKET_TOKEN_ENCRYPTED`, `AZURE_DEVOPS_TOKEN_ENCRYPTED` (Fernet) e os `*_BASE_URL` correspondentes. O `GITPR_SCM_TOKEN` cru continua sendo o override global de CI/CD e é tentado primeiro em todo provedor.
* **Migração Única e Idempotente (`migrate_legacy_scm_config`, sob lock):** move `GITPR_SCM_PROVIDER` + `GITPR_SCM_TOKEN_ENCRYPTED` + `GITPR_SCM_BASE_URL` para o slot da forge que eles nomeiam, **nunca sobrescreve** um slot já preenchido, remove as linhas legadas e continua funcionando quando o `.env` é somente-leitura (degrada para o ambiente do processo, `persisted=False`).
* **🆕 O Caminho de Fallback Está Documentado:** a [ADR-0020](docs/adr/0020-per-repo-scm-provisioning-migration.md) e as cinco variantes de `docs/scm-multiforge.*` descrevem explicitamente que, quando o arquivo de credenciais não pode ser escrito (`PermissionError`), o valor vive em `os.environ` e a migração reporta `persisted=False` — em vez de fingir que gravou. Um operador de CI/container read-only não é mais surpreendido.
* **Wizard (`gitpr --init`):** persiste **só no sucesso**, grava no slot da forge escolhida, oferece a base URL armazenada como default do prompt (não-GitHub) e só escreve `scm.provider` no arquivo do projeto quando a forge escolhida difere da detectada.
* **TUI de Configuração:** linha editável `PROJECT_SCM_PROVIDER` e linha read-only `PROJECT_EFFECTIVE_PROVIDER`, tokens e base URLs de todas as forges sempre listados, teste de token contra o host do próprio slot e um grupo `gitlab`.
* **Superfícies Convertidas:** `src/main.py`, `src/metrics.py`, `src/release_engine.py` e `src/mcp_server.py` resolvem por `get_scm_settings()` e propagam os avisos do resolvedor.
* **Não-Interativo Nunca Pergunta:** `validate_or_request_scm_token(..., allow_prompt=False)` em hooks, MCP e CI devolve "rode `gitpr --init`", não apaga a credencial salva e ainda usa um token validado que não pôde ser persistido.
* **Testes:** `tests/scm/test_scm_settings.py` (28) + `tests/scm/test_factory.py` (15) + `tests/scm/test_init_wizard.py` (21) + ampliações em `test_azure_devops_provider.py` (51), `test_bitbucket_provider.py` (49), `test_gitlab_provider.py` (56) e `tests/test_tui_issue_token.py` (8).
* **Artefatos:** [ADR-016](docs/plans/ADR-016-per-provider-scm-settings.md), [ADR-0020](docs/adr/0020-per-repo-scm-provisioning-migration.md), `docs/plans/develop_natan/20261107_per_provider_scm_settings_plansfacts.md`, `docs/plans/develop_natan/20261110_scm_per_repo_migration_note_plansfacts.md`, `docs/scm-multiforge.*` (5 idiomas) e o glossário `docs/plans/glossary-scm-multiforge.md`.

### **47. Subcomando `gitpr seed` — Bootstrap da Configuração Local (`src/core.py`, `src/main.py`)**

* **O que era:** a configuração local do projeto (base do PR, smart excludes, regras de linter) nasciam **como efeito colateral** do callback raiz e do download de skills. Não havia como semear de forma explícita, repetível e idempotente.
* **O que é:** `gitpr seed` (e a flag global `-sd/--seed`) promovem o bootstrap a operação de primeira classe. `seed_project_configuration()` cria:
  * `.gitpr/conf/gitpr.config.yml` (base do PR, via `ensure_project_config`);
  * `.gitpr/conf/gitpr.smart-excludes.json` (exclusões do projeto);
  * `.gitpr/skill/.gitpr.linter.yml` (regras do linter local).
* **Nunca Destrói sem Pedido:** arquivo existente **nunca** é sobrescrito; `--force/-f` sobrescreve de propósito, e `--all/-a` inclui também o download de todas as skills de IA. A função devolve um resumo estruturado e o comando grava a métrica `seed`.
* **Fronteira com o Auto-Seed:** a [ADR-0019](docs/adr/0019-project-configuration-seed-segregation.md) formaliza a segregação: o callback raiz/`--install` continua semeando **apenas** o `gitpr.config.yml` no primeiro uso, enquanto o provisionamento completo é sempre explícito por `gitpr seed`. O opt-out `GITPR_SKIP_PROJECT_CONFIG_SEED` cobre CI e monorepos.
* **🆕 Documentado e Traduzido nos 5 Idiomas:** as quatro variantes de `docs/config-tui.*` e de `docs/pull-request-publication.*` passaram a descrever o opt-out e a nota de migração, com paridade estrutural verificada por teste.
* **Wizard de Instalação em 5 Etapas:** **1)** Configuração Local do Projeto, **2)** Skill Templates, **3)** Git Hooks, **4)** Configuração do MCP, **5)** Chave de API. Pular passou a ser explícito.
* **Compatibilidade:** `generate_skill_template()` continua auto-semeando o smart-excludes; `ensure_project_config()` e `download_skill_file()` ganharam o parâmetro `force` mantendo o default no-clobber.
* **Ajuda:** `HELP_MAP["seed"]` aponta para `docs/install-wizard.md` e descreve `--force`/`--all`.
* **Testes:** `tests/test_seed_command.py` (**8 cenários**) + 🆕 `tests/unit/test_project_config_seed_docs.py` (**4 cenários**, paridade do contrato da ADR-0019).
* **Artefatos:** `docs/install-wizard.*` (5 idiomas), [ADR-0019](docs/adr/0019-project-configuration-seed-segregation.md), `docs/plans/develop_natan/20261105_seed_local_conf_plansfacts.md`, survey e walkthrough, e o termo **Project configuration seed** no `CONTEXT.md`.

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_ascii_chart.py` | 9 | Formatação compacta, estados vazios, histograma, série temporal, abas e troca de aba |
| `tests/test_blame_engine_ranges.py` | 7 | Blame por faixa de linhas em arquivo |
| `tests/test_blame_metrics.py` | 7 | Métricas de blame: profundidade, commits, duração |
| `tests/test_baseline_cli.py` | 54 | Grupo `baseline`: create/show/validate/update/suppress/unsuppress |
| `tests/test_changelog_builder.py` | 22 | Builder do changelog: seções, headings traduzíveis, contribuidores, links e datas |
| `tests/test_chat_backend.py` | 19 | Memória de chat, persistência, comandos slash |
| `tests/test_check_cli.py` | 5 | CLI do `check`: opções, formatos, exit codes |
| `tests/test_cli_help.py` | 9 | `-h` antes do subcomando: ajuda renderizada, TUI nunca aberta |
| `tests/test_commit_app.py` | 17 | `CommitApp`: mount, Stage Selector, auto-stage, skip, cancelar, confirmar, sucesso/falha, auto-exit, fluxo headless (pulado no Windows) e roteamento com/sem TTY |
| `tests/test_commit_classifier.py` | 30 | Classificação Conventional Commits + `pr_number_from_merge()` nas 4 forges |
| `tests/test_config_app.py` | 94 | TUI de configuração: montagem, categorias, dirty tracking, F2 bloqueado, Ctrl+R, busca, segredos, stores `project`, painel Smart Excludes |
| `tests/test_config_cli.py` | 9 | Registro do subcomando `config`, `-h`, import lazy, stdout limpo |
| `tests/test_config_issue_autoclose.py` | 10 | Getters de configuração e campos do schema de fechamento de issue |
| `tests/test_config_schema.py` | 55 | Cobertura de `DEFAULT_CONFIG` derivado, sem duplicatas, categorias/kinds (incluindo `KIND_FLOAT`), `seeded`, seção de skills, banner e paleta |
| `tests/test_config_store.py` | 22 | Round-trip no `.env` temporário, comentários e ordem preservados, `remove_config_value()` idempotente |
| `tests/test_config_suggest_reviewers.py` | 8 | Configuração de suggested reviewers (chaves e defaults) |
| `tests/test_config_validation.py` | 40 | Tipos, enums, templates, `validate_ai_key()` com SDK mockado (401 vs. rede vs. ollama) |
| `tests/test_core.py` | 49 | Fluxos principais, git diff, PR generation, timing, staging, coautoria, idioma dos hooks, base do PR |
| `tests/test_diff_failure_cli.py` | 3 | Exit code 1 em falha do git, 0 em diff vazio, fail-open no `--hook` |
| `tests/test_diff_parser.py` | 26 | Parser de diff por linhas/hunks, `summarize_patch()` e `split_patch_sections()` |
| `tests/test_doc_links.py` | 11 | Contrato `?lang=` do site, `doc_url()` dinâmico, links das TUIs e paridade de 5 idiomas |
| `tests/test_explain_command.py` | 4 | CLI do `explain`: sucesso, chave ausente, diff vazio, ajuda contextual |
| `tests/test_external_linters.py` | 33 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_full_diff_encoding.py` | 9 | Repositório real com arquivo Latin-1 + guarda de hunk binário |
| `tests/test_i18n.py` | 22 ✅ | Paridade entre idiomas, chaves ausentes/órfãs, identidade — **todos verdes** |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação (5 etapas) |
| `tests/test_issue_engine.py` | 4 | Draft de issue estruturado |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_linter_presets.py` | 5 | Presets de linter: resolução e re-download forçado |
| `tests/test_main_suggest_reviewers.py` | 8 | Flag `--no-suggest-reviewers` na CLI e no help contextual |
| `tests/test_map_reduce_chunking.py` | 10 | Resolução de limiares por provider, precedência de env, cap, input inválido e os três níveis da cascata |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 118 🆕 | Ferramentas MCP (18), recursos (19), annotations, patching, CLI direto, offload, contrato da extensão, base do PR e a lista completa de editores no erro de `--install` |
| `tests/test_mcp_server_e2e.py` | 6 | Servidor MCP real via subprocess + JSON-RPC stdio |
| `tests/test_mentor_cli.py` | 4 ✅ | CLI do `mentor` e opt-in do `--mentor` — patches em `src.main` |
| `tests/test_metrics.py` | 175 | **Ledger**: escrita síncrona, exportação, bundle/merge, migração, renderizadores, custo, moeda, qualidade, módulos, provedores, ciclo, Token Trend e Latency Histogram |
| `tests/test_net_timeouts.py` | 12 | Timeouts de rede/IA — alinhados ao default real de 180s |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_policy_cli.py` | 26 | Grupo `policy`: list/show/validate/use/off/install/init, confirmação e lockfile |
| `tests/test_pr_base_app.py` | 12 | Modal de troca da base do PR: montagem headless, escolha e cancelamento |
| `tests/test_pr_publish_app.py` | 59 | TUI do PR Publisher: telas, fluxos, suggested reviewers, `NoticeScreen`, modal de merge, `body_published` |
| `tests/test_pr_publish_linter_modal.py` | 4 | Modal de erro do linter: abort, no-verify |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_project_config.py` | 49 | `project_config`: path, YAML, seed, resolvedor de base, seção `scm`, validação contra o remoto |
| `tests/test_project_config_cli.py` | 7 | Fiação da base do projeto na CLI |
| `tests/test_release_cli.py` | 4 | CLI do release: options, help com epilog documentado |
| `tests/test_release_engine.py` | 61 | **Corte ancorado no changelog, `_drop_released()`, links, mapa de PR por merge commit**, front matter de idioma |
| `tests/test_reviewer_resolution.py` | 18 | Escada de resolução, rejeição de nome parcial, dedup, tolerância a falha |
| `tests/test_reviewer_suggestion.py` | 18 | Lógica de sugestão de revisores (ranking, exclusão, top-N, `last_commit_hash`) |
| `tests/test_risk_cli.py` | 4 | CLI do `risk`: `--file`, `--format json`, `--base`, `--no-history` |
| `tests/test_security_ruleset.py` | 77 | Matriz do ruleset embutido: regex, placeholders, nível, wildcard, merge, traduções |
| `tests/test_seed_command.py` | 8 | `gitpr seed`/`--seed`: criação, idempotência, force, `--all`, métricas |
| `tests/test_skill_command.py` | 10 | Download e validação de templates de skill |
| `tests/test_skill_context.py` | 20 | `get_skill_context()` com `quiet=True`, fallbacks, guarda do artefato de PR |
| `tests/test_skill_frontmatter.py` | 11 | `split_front_matter()`: BOM, CRLF, YAML malformado, allowlist de idiomas |
| `tests/test_skill_templates.py` | 99 | Varredura parametrizada de **todo template publicado** contra referências embutidas |
| `tests/test_smart_excludes.py` | 17 | Filtro pathspec inteligente, re-download forçado, famílias binárias |
| `tests/test_suggest_reviewers.py` | 19 | Suggested reviewers no fluxo de PR + resumo de blame |
| `tests/test_tests_command.py` | 4 | CLI do grupo `tests` e do `generate`, `--finding` e epilog com link |
| `tests/test_thinking_words.py` | 5 | Carregamento, parsing com separador `;` e reload forçado |
| `tests/test_tui_issue_token.py` | 8 | `allow_prompt=False`: nunca pergunta, nunca apaga, aponta `gitpr --init` |
| `tests/test_updater.py` | 55 | **Gate do PyPI**: TTL corrido, cache legado/corrompido, escrita atômica, `force`, `bounded_urlopen`, comparador PEP 440, pré-release, skip switch estrito e gate de subcomando |
| `tests/test_usage_log.py` | 27 | Log de uso: nome derivado da data, escrita síncrona, silêncio, `_repo_label()` multi-forge |
| `tests/test_version_bump.py` | 17 | Bump semântico: major/minor/patch, alvos e validação |
| `tests/test_web_links.py` | 26 | Normalização de remote (https/ssh/scp/credenciais/porta) e padrões de URL por forge |
| `tests/application/use_cases/test_activate_policy_pack.py` | 27 | Ativação de pack, lockfile, recusas |
| `tests/application/use_cases/test_baseline_gate.py` | 40 | Gate: carga, classificação, anotação, camadas e aborto |
| `tests/application/use_cases/test_baseline_summary.py` | 12 | Visão read-only do baseline para MCP/IDE |
| `tests/application/use_cases/test_calculate_risk.py` | 5 | Correlação de diff/achados/testes/histórico, degradação |
| `tests/application/use_cases/test_create_baseline.py` | 30 | Criação/atualização com proveniência e preservação de decisões |
| `tests/application/use_cases/test_generate_mentor_explanation.py` | 5 | Lotes, severidade, cache hit, chave ausente |
| `tests/application/use_cases/test_generate_pr_explanation.py` | 3 | Caso de uso do explain: dict do provider e chave ausente |
| `tests/application/use_cases/test_generate_test_file.py` | 5 | Caso de uso da geração de testes: dict do provider e string crua |
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
| `tests/badge/test_badge_paths.py` | 10 ✅ | Ponto único de injeção nos dois publicadores |
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
| `tests/domain/pr/test_explain_section_builder.py` | 6 | Renderização do Markdown, parsing tolerante, `[FILL]`, payload dict e `None` |
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
| `tests/integration/test_baseline_exit_code_contract.py` | 8 | Exit code 1 para baseline inaplicável e 2 no `check` |
| `tests/integration/test_policy_effect_on_review_linter_risk.py` | 31 | Efeito real do pack em review, lint e risk (com guarda de rede autouse) |
| `tests/issue_autoclose/test_close_issue_wiring.py` | 26 | Fiação no fluxo de PR: flags, prompt, publicação real, limpeza do registro |
| `tests/issue_autoclose/test_insert_close_line.py` | 19 | Inserção idempotente e reconhecimento de keywords de fechamento |
| `tests/issue_autoclose/test_issue_registry.py` | 26 | Registro local: round-trip, atomicidade, corrupção, `.gitignore`, repo match, migração do `github.yml` |
| `tests/issue_autoclose/test_register_created_issue.py` | 13 | Registro pós-criação: multi-forge, provider persistido, falhas engolidas |
| `tests/issue_autoclose/test_resolve_close_issue.py` | 42 | Árvore de decisão: gates, `is_open`, PR, registros mortos, `not-supported`, confirmação |
| `tests/review/test_diff_normalizer.py` | 20 | Newlines, validação de diff, smart-excludes em Python |
| `tests/review/test_diff_source.py` | 12 | `DiffOrigin`/`DiffSource`: proveniência, `cache_scope`, `is_remote` |
| `tests/review/test_remote_pr.py` | 40 | Orquestração: portões, PR, diff, linter, comentário opcional |
| `tests/review/test_review_pr_cli.py` | 25 | CLI `review-pr`: opções, rejeições antes da IA, `--post-comment` |
| `tests/scm/test_azure_devops_provider.py` | 51 | Provider Azure DevOps: org/projeto, PRs, `ScmNotSupportedError`, issue read-back |
| `tests/scm/test_bitbucket_provider.py` | 49 | Provider Bitbucket: Basic auth, workspace, PRs, `close #N` |
| `tests/scm/test_contract.py` | 44 | Contrato `ScmProvider`: assinaturas, dataclasses, erros, defaults de issue |
| `tests/scm/test_factory.py` | 15 | `resolve_scm_provider()` + `detect_provider_from_remote()` com `default=None` e GitHub reconhecido |
| `tests/scm/test_github_api_shim.py` | 18 | Shim deprecado `github_api` → delega ao provider |
| `tests/scm/test_github_provider.py` | 83 🆕 | Provider GitHub: REST, headers, PRs, issues, releases, read-back de revisores e **`TestParseRepoRef`** (github.com HTTPS/SSH, Enterprise HTTP/SSH/porta/credencial e recusa de caminhos malformados) |
| `tests/scm/test_gitlab_provider.py` | 56 | Provider GitLab: API v4, namespace, cabeçalhos sintetizados, `overflow`, `Closes #N` |
| `tests/scm/test_init_wizard.py` | 21 | Wizard `--init`: detecção da forge, slot por forge, validação, persistência, GitHub real sem override |
| `tests/scm/test_release_publish.py` | 8 | Publicação de release por forge (GitHub/GitLab) |
| `tests/scm/test_scm_settings.py` | 28 | Resolvedor de forge/credencial: precedência, migração legada, aviso de fallback, read-only |
| `tests/split/test_apply_split_plan.py` | 11 | O único módulo que muta: staging seletivo, um commit por grupo |
| `tests/split/test_generate_split_plan.py` | 12 | Diff → units → groups → pré-validação de conflito → mensagens |
| `tests/split/test_hunk_grouper.py` | 18 | Prompt, orçamento/trimming, chamada de IA, validação da resposta |
| `tests/split/test_hunk_parser.py` | 18 | `parse_units()`/`build_patch()`: texto ↔ modelo, puro |
| `tests/split/test_selective_stager.py` | 11 | Staging de subconjunto, check contra HEAD, índice limpo |
| `tests/split/test_split_cli.py` | 31 | CLI do split: opções, dry run default, `--apply` |
| `tests/unit/test_version_consistency.py` | 5 ⚠️ | SSOT da versão: `pyproject.toml`, `CLAUDE.md` e `GEMINI.md` contra `src.updater.__version__` — **2 falhas** porque os dois docs ainda dizem 1.8.0 |
| `tests/unit/test_check_ci_docs_parity.py` | 3 | Paridade de 5 idiomas e 7 seções do `docs/check-ci.*` + ADR-0011 + referências no `action.yml` |
| `tests/unit/test_auto_update_docs_parity.py` | 4 | Aviso, literais aceitos, `GITPR_SKIP_UPDATE_CHECK` e ADR-0021 nos 5 idiomas |
| `tests/unit/test_docs_translation_parity.py` | 3 🆕 | Guarda genérica de paridade estrutural: `_EN_ONLY` vazio e nenhuma exceção para `pull-request-publication` |
| `tests/unit/test_marketplace_publishing_guide_docs_parity.py` | 4 | Guia de marketplace nos 5 idiomas: tokens, etapas e wizard de credenciais |
| `tests/unit/test_marketplace_wizard_syntax.py` | 3 | Presença/shebang, marcadores e estágios do wizard, `bash -n` estático |
| `tests/unit/test_project_config_seed_docs.py` | 4 🆕 | Seção `9.4`, `[!IMPORTANT]` e `GITPR_SKIP_PROJECT_CONFIG_SEED` nas 5 variantes de `pull-request-publication` e `config-tui`, âncora por slug GitHub, ADR-0019 e termos no `CONTEXT.md` |
| `tests/unit/test_scm_multiforge_docs_parity.py` | 3 🆕 | Nota de provisionamento SCM nos 5 idiomas + `persisted=False`/`os.environ`/`PermissionError` na §3.1 e na ADR-0020 |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (scaffold; nunca executado) |

**Total:** **3471 cenários coletados em 167 módulos de teste** (65 na raiz + 12 em `tests/application/use_cases/` + 10 em `tests/fix/` + 10 em `tests/scm/` + 10 em `tests/infrastructure/` + 21 em `tests/domain/` + 7 em `tests/badge/` + 6 em `tests/demo/` + 6 em `tests/split/` + 5 em `tests/issue_autoclose/` + 4 em `tests/review/` + 3 em `tests/integration/` + **8 em `tests/unit/`**; **+2 cenários, +1 arquivo** desde o relatório anterior).

**Notas de qualidade desta versão:**
- **🆕 A paridade de documentação ficou uniforme:** `_EN_ONLY` está vazio e `pull-request-publication` saiu de `_PARITY_EXCEPTIONS`; qualquer documento novo na raiz de `docs/` precisa das quatro traduções, ou o CI falha de propósito.
- **🆕 O teste de âncora é mais forte que um `grep`:** `test_project_config_seed_docs.py` calcula o slug do heading para validar o link entre `config-tui` e `pull-request-publication`, então renomear a seção quebra o teste em vez de gerar um link morto.
- **🆕 A cobertura do GitHub Enterprise é explícita:** `TestParseRepoRef` cobre HTTPS/SSH de `github.com`, Enterprise com HTTP, SSH, porta e credencial embutida, e recusa de URLs malformadas e de caminhos com profundidade diferente de dois.
- **🆕 O contrato de provisionamento SCM read-only virou teste:** `test_scm_multiforge_docs_parity.py` exige `persisted=False`, `os.environ` e `PermissionError` na documentação e na ADR-0020.
- **⚠️ 2 falhas de consistência de versão (recorrentes):** `CLAUDE.md` e `GEMINI.md` foram alinhados a 1.8.0 por `9ad079d`, mas o bump `3aee652` levou o SSOT a 1.9.0 — `tests/unit/test_version_consistency.py` falha nos dois cenários outra vez. O padrão se repete a cada release: o bump muda só `src/updater.py`.
- **⚠️ Sem teste de paridade dos bundles da extensão:** os arquivos `pt-pt` foram verificados por script manual (chaves e placeholders `{n}`); nada na suíte impede que um novo `package.nls.*` nasça incompleto.
- **`tests/conftest.py` segue hermético:** `GITPR_SHOW_LOGS=false`, `GITPR_SKIP_UPDATE_CHECK=true`, `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false`, `LANG_VERSION` na versão do código e `GITPR_SKIP_PROJECT_CONFIG_SEED=true`.
- **Guarda de rede em vários lugares:** `tests/demo/conftest.py`, `tests/badge/conftest.py`, `tests/integration/conftest.py` e `tests/split/conftest.py`.
- **Fixtures de git real:** `tests/fix/git_fixture.py`, `tests/split/git_fixture.py` e `tests/test_full_diff_encoding.py`.
- **A suíte da extensão é separada:** 7 cenários Mocha em `extensions/vscode/src/test/mcp_client.test.ts`, dos quais 1 integra de verdade com o servidor MCP Python por stdio.
- **CI roda em Python 3.10 e 3.13** com `fail-fast: false`, e o release tem workflow próprio com Trusted Publishing.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** **1807 chaves** em **todos os seis** dicionários (`es.json`, `es_es.json`, `fr.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`). O código usa as mesmas chaves: **0 sem tradução** e **0 órfãs**. A contagem não mudou porque a v0.0.44 corrigiu o **valor** de uma chave existente (a mensagem de editor desconhecido) nos seis arquivos.
* **🆕 `__lang_version__` subiu para v0.0.44:** o OTA entrega a string de `--install` corrigida sem reinstalação, em todos os idiomas.
* **Fontes de tradução em lockstep:** uma chave nova precisa existir no código (fonte), em `langs/pt_br.json` (**lista mestra**), nos dicts FR/ES de `scripts/sync_all_langs.py` e nos valores curados de `scripts/fix_mangled_i18n_keys.py`; o extrator de chaves é **AST** nos dois lados.
* **Tópicos novos:** **nenhum** tópico canônico novo nesta janela — o trabalho foi de sincronização, de dívida de paridade e de consolidação.
* **🆕 A raiz de `docs/` chegou a 100%:** **51 tópicos canônicos** × 5 idiomas = **255 arquivos**, sem tópico parcial. O antigo único tópico EN-only (`github-issue-prompt-com-gh`) deixou a raiz e virou um **Extra doc** em `docs/extra/`, fora do contrato de paridade.
* **🆕 O `CONTEXT.md` formalizou a distinção:** entraram **Canonical doc** (guia da raiz de `docs/`, EN como fonte, espelhado nos quatro sufixos com âncoras estruturais idênticas) e **Extra doc** (how-to avulso em `docs/extra/`, fora do contrato de 5 idiomas). O glossário passou de **53 para 55 termos**.
* **🆕 Tópicos atualizados nesta janela:**
  - `docs/config-tui.*` (**5 arquivos** 🆕) — nota do seed em runtime, o opt-out `GITPR_SKIP_PROJECT_CONFIG_SEED` e a âncora para a §9.4.
  - `docs/pull-request-publication.*` (**5 arquivos** 🆕) — seção `9.4` com `[!IMPORTANT]`, exemplos e a nota de opt-out para CI/monorepo.
  - `docs/scm-multiforge.*` (**5 arquivos**) — caminho read-only/efêmero (`persisted=False`, `os.environ`, `PermissionError`) na §3.1 e o suporte a domínios customizados do GitHub Enterprise na §1.2.
  - `docs/metricas-telemetria.*` (**5 arquivos**) — custo e latência do Map-Reduce, limites por provedor e as colunas `map_reduce`/`chunks_count`/`duration_ms`.
  - `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md` e `README.fr_fr.md` — índice de documentação completado com seis guias (`gitpr-issue-option`, `guia-regex-gitpr`, `marketplace-publishing-guide`, `otimizacao-de-tokens`, `untracked-files`, `version-markers`) e `mentor-mode` nas traduções.
  - `docs/ARCHITECTURE.*` (**5 arquivos**) e `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` — ajustes de conteúdo ligados às edições acima.
  - `docs/adr/0020-per-repo-scm-provisioning-migration.md` — fallback read-only e o tratamento de `PermissionError`.
* **🆕 Um documento de operação novo:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (252 linhas) audita os **25 relatórios de estado** contra o código, separa o que já foi feito do que continua aberto (`P1`–`P8`, `M1`–`M3`) e descreve **8 etapas executáveis** com critérios de aceite e comandos de verificação. As Etapas 1–7 estão marcadas como concluídas; a Etapa 8 foi entregue no código (`5b44c0b`) sem atualizar a marcação.
* **Documentação em 5 idiomas:** **51 tópicos canônicos** (🆕 **51 completos, 0 parciais**) + **6 entradas em `docs/extra/`** (`como_reverter_commit_git_localmente.md`, `deepseek_v3_tokenizer/`, `github-issue-prompt-com-gh.md`, `gitpr_sintese_monetizacao.md`, `progit.pdf`, `testar_sem_usar_pypi.md`), explicitamente fora do contrato.
* **Novos artefatos de especificação:** nenhuma ADR nova nesta janela — `docs/adr/` segue com **11 arquivos**, e a ADR-0020/ADR-0022 foram atualizadas. A numeração de `docs/adr/` não é contínua porque ADR-012/013/015/016 vivem em `docs/plans/`.
* **Skills locais do Claude Code:** `.claude/skills/` com **29 skills** (contagem inalterada).
* **Memory Index:** `.claude/memory/MEMORY.md` com **40 padrões** (inalterado).
* **Relatórios de tarefas:** `docs/claude-code/reports/develop_natan/` (**123**; **+1**) + `docs/claude-code/reports/feat/` (**12 arquivos** em 1 pasta, inalterado) + `docs/claude-code/reports/main/` (**1**) e `docs/gemini/reports/` (**71**; **+9**), mais `docs/gemini/walkthrough/` (**45**; **+7**).
* **Relatórios de status:** `docs/reports/` — este é o **26º relatório** (v0.0.26); o v0.0.25 nunca é sobrescrito.
* **Planos de desenvolvimento:** **191** arquivos em `docs/plans/` (+11) + **51 arquivos em `docs/gemini/plans/`** (+8) + **63 arquivos em `docs/survey/`** (+8).

---

## **🔄 Pipeline de Distribuição**

1. **PyPI (canal único):** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **Atualização obrigatória com janela corrida:** a execução verifica o PyPI no startup e **bloqueia com exit code 1** se houver versão mais nova, imprimindo `pip install --upgrade gitpr-cli`. A resposta fica em cache por **1 hora** e `--update` **sempre** consulta a rede. A comparação é PEP 440: pré-release remoto não bloqueia instalação estável, versão ilegível conta como desconhecida. O gate cobre subcomandos quando há TTY; CI, pipes, hooks, MCP e `-h` seguem isentos.
3. **GitHub Releases:** produção automatizada pelo `release.yml` em tags `v*` — build, validação, Trusted Publishing e criação do release com artefatos.
4. **GitHub Actions:** workflow `pr-review.yml` + `action.yml` (instala via pip) + `tests.yml` (matriz Python 3.10 e 3.13) + `extension.yml` (VSIX; job `github-release` em `ext-v*` e job `publish-marketplaces` com gate granular por PAT) + `release.yml` (PyPI + GitHub Release em `v*`). O `action.yml` chama um único passo `gitpr check` — **quebra declarada** para quem usava `--linter` + `--fullreview`, coberta por teste de paridade de documentação e pelo ADR-0011.
5. **MCP Server:** entry point `gitpr-mcp` via `pyproject.toml`
6. **Extensão de Editor:** pacote VSIX independente (`natanfiuza.gitpr`), com canais VS Code Marketplace e Open VSX; requer Node.js 20+ apenas para build, não para uso. 🆕 O VSIX agora carrega **cinco** locales; o workflow precisa incluir os dois arquivos `pt-pt` no pacote.
7. **Templates e idiomas OTA:** `templates/` e `langs/*.json` servidos do GitHub (main) — `__lang_version__` **v0.0.44** 🆕 renova as cópias locais de `~/.gitpr/langs/`; `__scripts_version__` **v0.0.4** renova os hooks.
8. **Versão derivada do código:** `pyproject.toml` usa `version = {attr = "src.updater.__version__"}` — o `__version__` é a **única** fonte, garantido por [ADR-014](docs/adr/0014-canonical-package-version-ssot.md) e por `tests/unit/test_version_consistency.py`.
9. **`package-data` importa:** os quatro packs embutidos (`src/policy_packs/*`) viajam no wheel.
10. **✅ Estado do release — 1.9.0 publicada:** o PyPI serve **1.9.0**, a seção `## [1.9.0] - 2026-11-15` está no `CHANGELOG.md` (commit `3aee652`), o tag `v1.9.0` aponta para o merge do PR #336 (`3bb8ec6`) e `origin/main` = `3bb8ec6`. O tag `v1.8.0` segue em `6cc0508`.
11. **⚠️ Tag da 1.7.0 continua desalinhado (herdado):** o `v1.7.0` ao vivo aponta para `b2688c4`, um commit **anterior** ao bump, onde `__version__` era 1.6.0. Não bloqueia a 1.9.0, mas o GitHub Release da 1.7.0 segue sem refletir o código publicado.
12. **⚠️ Estado do repositório local:** a branch local `main` está parada em `4723bd5` (relatório v0.0.22) — quem lê a release deve olhar `origin/main`; e `develop_natan` local está alguns commits à frente de `origin/develop_natan` por causa dos merge commits locais, embora esses commits já estejam em `origin/main`.

---

## **📈 Evolução desde o Relatório Anterior (v0.0.25)**

| Área | v0.0.25 (anterior) | v0.0.26 (atual) |
|------|-------------------|-----------------|
| **Versão GitPR** | 1.8.0 — publicada no PyPI; tag `v1.8.0` no merge do PR #325 | **1.9.0** — publicada no PyPI; tag `v1.9.0` no merge do PR #336 |
| **Versão Idioma** | v0.0.43 | **v0.0.44** — mesmo número de chaves, valor corrigido |
| **Versão Scripts Hook** | v0.0.4 | v0.0.4 (inalterada) |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Inalterado |
| **Idiomas** | 5 idiomas, 6 dicionários | Inalterado; 🆕 extensão também com 5 bundles |
| **Subcomandos** | 16 | 16 — inalterado |
| **Flags CLI** | 34 opções na raiz | 34 — inalteradas |
| **Configuração SCM** | Detecção corrigida e aviso de fallback (ADR-0020) | + 🆕 **fallback read-only documentado e travado** (`persisted=False`) |
| **GitHub Enterprise** | `parse_repo_ref` exigia o literal `github.com` | 🆕 **aceita domínios customizados** (HTTP/SSH/porta) |
| **Fechamento de Issue** | Multi-forge | Inalterado |
| **Seed de Configuração** | `gitpr seed`/`--seed` + wizard de 5 etapas | Inalterado no código; 🆕 contrato da ADR-0019 travado nas 5 traduções |
| **Camadas** | 9 pacotes de domínio, 15 casos de uso | Inalterado |
| **Map-Reduce** | Limiar por provider + cascata + pré-reduce | Inalterado no código; 🆕 **custo/latência documentados** nos 5 idiomas |
| **Ferramentas MCP** | 18 tools / 19 recursos / 7 prompts | Inalterado; 🆕 mensagem de `--install` lista `claude-code` |
| **`DEFAULT_CONFIG`** | 55 chaves | 55 — inalterado |
| **Schema de Config** | 115 `ConfigField` / 18 categorias / 55 `seeded` | Inalterado |
| **i18n (chaves por arquivo)** | 1807 × 6 | **1807 × 6** — 0 faltando, 0 órfãs ✅ |
| **Gate de Atualização** | TTL corrido de 1 h, `-u` sempre online, PEP 440 | Inalterado |
| **Linter** | Regex + segredos + SAST + `findings_out` + baseline-aware | Inalterado |
| **Diff / Smart Excludes** | Guarda de hunk binário e 100+ padrões | Inalterado |
| **Hooks Git** | post-checkout/post-merge/pre-push no ledger | Inalterados |
| **Camada SCM** | 4 forges, paginação, `web_links.py` | 🆕 `parse_repo_ref` genérico e Enterprise; 373 cenários |
| **Release engine** | Seção `[1.8.0]`; 1.8.0 publicada e tagueada | Seção `[1.9.0]`; **1.9.0 publicada e tagueada**; ⚠️ sumário cita 1.8.0 |
| **Métricas** | Gráficos ASCII e abas no dashboard; preços por modelo e moeda | + 🆕 documentação de custo/latência do Map-Reduce |
| **Commit TUI** | Teste headless pulado no Windows | Inalterado |
| **Extensão** | Guia traduzido em 5 idiomas e wizard de credenciais | + 🆕 **localização `pt-pt`** (5 bundles) |
| **Documentação** | 52 tópicos (51 completos + 1 parcial) | **51 tópicos (51 completos + 0 parciais)** + `docs/extra/` fora do contrato |
| **Paridade de documentação** | 1 exceção de idioma + 8 dívidas de paridade | 🆕 **0 exceções de idioma** + 7 dívidas de paridade |
| **Agenda do domínio** | `CONTEXT.md` com 53 termos | **55 termos** — Canonical doc, Extra doc |
| **CI** | `tests.yml` + `action.yml` + `extension.yml` + `release.yml` | Inalterado |
| **Suíte de Testes** | 3469 cenários (166 arquivos) | **3471 cenários (167 arquivos) — +2 cenários, +1 arquivo** |
| **Estabilidade da Suíte** | 2 falhas de consistência de versão (docs em 1.7.0) | **2 falhas de consistência de versão** (docs em 1.8.0) — o padrão se repete |
| **Dependências** | Sem novas dependências Python | Nenhuma nova |
| **Commits desde o relatório** | 24 commits, 12 merges | **13 commits, 6 merges** |
| **PRs referenciados** | 11 PRs novos (#311–#325); issues #313–#323 | **6 PRs novos** (#327, #329, #331, #333, #335, #336); issues fechadas #326, #328, #330, #332 e #334 |
| **Roteiro de pendências** | Não existia | 🆕 `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` com 8 etapas |
| **Memory Index** | 40 padrões | 40 padrões (inalterado) |
| **Relatórios de tarefas** | 122 claude-code, 62 gemini, 38 walkthrough | **123 claude-code (+12 feat, +1 main), 71 gemini, 45 walkthrough** |
| **Planos de desenvolvimento** | 180 planos, 43 gemini, 55 surveys | **191 planos, 51 gemini, 63 surveys** |

---

## **🚧 Próximos Passos**

* **🆕 Atualizar `CLAUDE.md` e `GEMINI.md` para 1.9.0:** o bump `3aee652` alterou só `src/updater.py` e o `CHANGELOG.md`; os dois documentos voltaram a ficar uma versão atrás. `tests/unit/test_version_consistency.py` tem **2 falhas** por isso — é a correção mais urgente desta janela, e o padrão se repete a cada release.
* **🆕 Corrigir o sumário da seção `[1.9.0]` do changelog:** o texto termina com "The release is version 1.8.0". A causa é a mesma da 1.8.0 (o resumo de IA cita a versão anterior); vale corrigir o texto **e** verificar o prompt do release engine para que a versão do cabeçalho seja injetada como fato.
* **🆕 Marcar a Etapa 8 como concluída no roteiro:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` ainda exibe `P8` como pendente e o heading da Etapa 8 sem `✅`, embora `5b44c0b` tenha entregado os dois bundles `pt-pt`.
* **🆕 Criar teste de paridade dos bundles da extensão:** a Etapa 8 foi validada por script manual. Um teste que compare o conjunto de chaves e os placeholders `{n}` de `package.nls.pt-pt.json`/`bundle.l10n.pt-pt.json` com os arquivos em inglês impediria que um locale novo nascesse incompleto.
* **🆕 Reduzir as 7 dívidas de `_PARITY_EXCEPTIONS`:** `ARCHITECTURE`, `check-ci`, `git-hooks-locais`, `git-status`, `linter-regras-customizadas`, `mentor-mode` e `skill-template` continuam divergentes em headings, tabelas ou cercas. Cada uma que fechar é uma linha a menos na lista.
* **Alinhar o tag `v1.7.0` (herdado):** o tag no origin aponta para `b2688c4` (pré-bump). Mover/recriar o tag no commit do bump faz o GitHub Release da 1.7.0 coincidir com o PyPI.
* **Publicar a extensão nos marketplaces:** o gate granular já avalia `VSCE_PAT` e `OVSX_PAT`, o VSIX já é anexado ao GitHub Release e o wizard de credenciais já valida os dois tokens — falta rodar o wizard com as credenciais reais e disparar o `ext-v*`. Com o `pt-pt` incluído, vale conferir que os dois arquivos entraram no pacote.
* **Acompanhar o host self-hosted não reconhecido:** o fallback avisa e aponta para `gitpr --init`; hosts com `github` no nome já parseiam. Um domínio arbitrário (`git.acme.com`) ainda depende de `scm.provider` no arquivo do projeto — comportamento documentado, não automático.
* **Mais provedores:** OpenAI direto, provedores locais adicionais. **Item herdado, ainda aberto (M3 do roteiro).**
* **Documentar a operação de release em `docs/`:** o padrão "bump muda só `src/updater.py`, e os docs ficam para trás" já apareceu em duas releases seguidas; um checklist (ou um teste que rode no `release`) evitaria a terceira.
* **Manter `origin/main` e a branch local `main` sincronizadas:** a `main` local está em `4723bd5`, o que confunde qualquer leitura de estado do repositório.

### ✅ Concluídos nesta janela (2026-11-15)

* ~~**`CLAUDE.md` e `GEMINI.md` diziam 1.7.0**~~ 🆕 — `9ad079d` / issue #326: alinhados a 1.8.0 (e novamente defasados após o bump para 1.9.0).
* ~~**O sumário da seção `[1.8.0]` abria com "Version 1.7.0 improves…"**~~ 🆕 — `9ad079d`: reescrito para 1.8.0.
* ~~**As traduções de `config-tui` e `pull-request-publication` estavam defasadas**~~ 🆕 — `47f506d` / issue #326: seção `9.4`, `[!IMPORTANT]` e `GITPR_SKIP_PROJECT_CONFIG_SEED` nos 5 idiomas, mais `tests/unit/test_project_config_seed_docs.py`; `pull-request-publication` saiu de `_PARITY_EXCEPTIONS`.
* ~~**`github-issue-prompt-com-gh` era o único tópico parcial**~~ 🆕 — `5eed732` / issue #328: movido para `docs/extra/`, `_EN_ONLY` esvaziado, READMEs completados e os termos **Canonical doc**/**Extra doc** no `CONTEXT.md`.
* ~~**A migração SCM read-only não estava documentada**~~ 🆕 — `af5fad0` / issue #330: `persisted=False`, `os.environ` e `PermissionError` nos 5 idiomas e na ADR-0020, travados por teste.
* ~~**O custo/latência do Map-Reduce não estava documentado**~~ 🆕 — `5eed732`: `docs/metricas-telemetria.*` nos 5 idiomas + referência na ADR-0022.
* ~~**O GitHub Enterprise era recusado por `parse_repo_ref`**~~ 🆕 — `5bbb499` / issue #332: `_REMOTE_RE` genérico, `TestParseRepoRef` e `docs/scm-multiforge.*` atualizados.
* ~~**A extensão não tinha `pt-pt`**~~ 🆕 — `5b44c0b` / issue #334: `package.nls.pt-pt.json` e `bundle.l10n.pt-pt.json`.
* ~~**A mensagem de `--install` omitia `claude-code`**~~ 🆕 — `5b44c0b` / issue #334: mensagem corrigida, seis dicionários sincronizados e teste dedicado.
* ~~**Não havia um levantamento do que continuava pendente nos relatórios**~~ 🆕 — `9ad079d`: `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` com 25 relatórios auditados e 8 etapas.
* ~~**A versão do pacote estava em 1.8.0 / v0.0.43**~~ 🆕 — `3aee652` / PR #336: bump para **1.9.0** e **v0.0.44**, release `[1.9.0]` no changelog e publicação no PyPI com tag `v1.9.0`.

---

**Relatório gerado em:** 2026-11-15  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
