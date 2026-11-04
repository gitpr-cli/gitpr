# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.22 (2026-11-04)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.22):**
- **O ciclo issue → PR → merge passou a fechar sozinho:** toda issue criada com `gitpr -is` agora é registrada em `.gitpr/conf/github.yml` (um registro local que se auto-ignora no `.gitignore`), e o próximo `gitpr` verifica que ela continua aberta antes de oferecer a linha `close #N` no corpo do Pull Request. `--close-issue` aceita sem perguntar, `--no-close-issue` pula a checagem, e `GITPR_ISSUE_AUTOCLOSE=false` desliga a feature. O pacote novo `src/issue_autoclose/` tem **5 arquivos** e uma fileira de decisões registradas nas ADRs 001–007 em `docs/specs/issue-autoclose/`.
- **A base do PR deixou de morar só na máquina de quem executa:** `.gitpr/conf/gitpr.config.yml` é versionado com o projeto e carrega a branch de destino; `src/project_config.py` resolve `--base` → arquivo do projeto → `PR_DEFAULT_BASE` → `origin/HEAD` → `main`, e o alvo precisa existir em `origin` e diferir da branch atual. Um alvo igual à branch atual é recusado e, na execução interativa, reparado por um modal dedicado (`src/ui/pr_base_app.py`) que escreve o novo valor no arquivo do projeto ([ADR-015](docs/plans/ADR-015-project-local-pr-base.md)).
- **A dívida de i18n foi paga:** os seis dicionários têm agora **1698 chaves** cada um, `__lang_version__` subiu para **v0.0.38**, e `tests/test_i18n.py` fecha **22 verdes** — sem chaves faltando, sem órfãs, sem identidade acima da allowlist. O extrator de `sync_i18n.py` trocou o regex por **AST**, o que eliminou os 21 falsos negativos de concatenação implícita.
- **O ruleset de segredos cobriu as três lacunas que estavam abertas:** chaves STS `ASIA…`, PATs `github_pat_…`, cookies `xoxc-`/`xoxd-`, atribuições **sem aspas** (`API_KEY=abc123`), fronteira à esquerda no nome da chave e menos falsos positivos (`bypassword`, `os.getenv(...)`). São **7 regras** com regexes mais largas, cobertas por **77 cenários**.
- **Contratos que estavam só na cabeça viraram teste:** a versão do pacote tem **SSOT único** em `src/updater.py` (ADR-014) e um teste que falha se `pyproject.toml`, `CLAUDE.md` ou `GEMINI.md` divergirem; o contrato de exit code do baseline ganhou 8 cenários de integração; o read-back de revisores legado (`None`) deixou de imprimir `attached None`; e o `-h` antes do subcomando voltou a renderizar ajuda em vez de abrir a TUI.
- **A 1.5.0 está tagueada, mas ainda não publicada:** a tag `v1.5.0` aponta para o merge do PR #260 (2026-11-04), porém o PyPI ainda serve **1.4.4** — o release workflow existe (`.github/workflows/release.yml`), mas a publicação precisa ser confirmada.

- **Versão atual:** 1.5.0 (**tagueada como `v1.5.0`; o PyPI ainda serve 1.4.4**)
- **Versão dos dicionários de idioma:** v0.0.38 (🆕 +2 desde v0.0.36, agora com os dicionários realmente alterados)
- **Versão dos scripts de hook:** v0.0.4 (inalterada)
- **Publicação:** PyPI (`pip install gitpr-cli`) — canal binário removido
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal) — **15 subcomandos** (`badge`, `baseline`, `check`, `config`, `demo`, `explain`, `fix`, `mentor`, `metrics`, `policy`, `release`, `review-pr`, `risk`, `split`, `tests`). Quatro deles são **grupos**: `baseline` (6 subcomandos), `metrics` (8), `policy` (7) e `tests` (1). **33 opções Click na raiz** — 🆕 `--close-issue` e `--no-close-issue`.
* **UI/Terminal:** Textual — TUI para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher, **CommitApp** (`src/ui/commit_app.py`, 220 linhas), erros do linter (`LinterApp`), configuração (`ConfigApp`), modal `NoticeScreen`, o tour do `gitpr demo` (`src/ui/demo/`), o assistente de migração do ledger (`src/ui/metrics_migration_app.py`) e 🆕 **`PrBaseApp`** (`src/ui/pr_base_app.py`, 98 linhas), o modal que troca a base do PR igual à branch atual.
* **Arquitetura em Camadas:** `src/domain/` (regra pura, sem I/O) + `src/application/use_cases/` (orquestração, **15 casos de uso**) + apresentação (CLI/TUI). **9 pacotes de domínio**: `baseline`, `check`, `finding`, `linter`, `mentor`, `policy`, `pr`, `risk`, `tests_generation`. 🆕 **Fora do domínio:** `src/issue_autoclose/` (fluxo de fechamento de issue sobre `ScmProvider` e o registro local) e `src/project_config.py` (resolução de path/YAML e validação contra o remoto) — ambos são orquestração e borda, não regra pura.
* **Extensão de Editor:** `extensions/vscode/` — cliente TypeScript fino do MCP para **VS Code e Cursor** (Node.js 20+, `@modelcontextprotocol/sdk`, VSIX). Não contém regra de negócio.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API, tokens GitHub e tokens SCM das forges.
* **Configuração:** `python-dotenv`, `pyyaml` (linter estático e configuração do projeto) + schema declarativo próprio (`src/config_schema.py`, **85 `ConfigField`** e **17 categorias** — 🆕 a categoria `project`). `packaging` alimenta a comparação de versões do gate (PEP 440) e a compatibilidade dos policy packs.
* **IA Providers:** Integração via SDK oficial do Google GenAI, OpenAI SDK (DeepSeek) e OpenAI SDK (Ollama local). Defaults configurados: `gemini-pro-latest` / `gemini-flash-lite-latest` e `deepseek-v4-pro` / `deepseek-v4-flash`.
* **Forge APIs:** `requests` (REST) — abstração multi-forge em `src/infrastructure/scm/` (GitHub, GitLab, Bitbucket, Azure DevOps) + `web_links.py`; `src/github_api.py` mantido como shim deprecado. 🆕 `IssueInfo` e as três operações de issue (`get_issue`, `get_default_branch`, `closing_line`) entraram no contrato do `ScmProvider`.
* **Linter / SAST:** regex YAML + bridge Checkstyle + ruleset de segredos embutido (`src/security_ruleset.py`) + 4 bridges em `src/infrastructure/linter/external/` (base + Semgrep, Gitleaks, Bandit), com modelo normalizado em `src/domain/linter/sast_finding_mapper.py` e o achado canônico em `src/domain/finding/`. 🆕 O ruleset manteve as 7 regras e **ampliou a cobertura** de cada regex.
* **Infraestrutura de CI:** `src/infrastructure/ci/` — `sarif_builder.py` (SARIF 2.1.0), `junit_builder.py` (JUnit XML) e `masking.py` (mascaramento de credenciais antes de serializar qualquer artefato).
* **Git Internals:** `src/infrastructure/git/` — `patch_applier.py`, `selective_stager.py`, `identity.py`, `risk_history_reader.py` e `test_matcher.py`.
* **Persistência local:** `src/ledger.py` — SQLite (`~/.gitpr/metrics/telemetry.db`) com WAL, `PRAGMA user_version`, chaves UUID e transporte por bundle. 🆕 O evento `issue_autoclose` entra no mesmo ledger, com `asked`/`accepted`/`skipped_reason` no `meta`.
* **Rede:** `src/net.bounded_urlopen` (`UPDATE_FETCH_HARD_TIMEOUT = 3.0`) limita o **wall clock incluindo DNS** no gate de atualização. 🆕 `get_issue()`/`get_default_branch()` usam timeout de **5 s** (`GITPR_ISSUE_AUTOCLOSE_TIMEOUT`), porque o fluxo de PR só precisa de um sim/não.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 — **18 ferramentas anotadas**, **19 recursos**, 7 prompts. 🆕 O fechamento de issue **não** expôs tool nova: é comportamento do fluxo de PR; o `publish_pull_request` passou a compartilhar o resolvedor de base e a devolver `warnings`.
* **Testes:** Pytest + `unittest.mock` (**153 módulos de teste** — 59 na raiz, 12 em `tests/application/use_cases/`, 10 em `tests/fix/`, 9 em `tests/scm/`, 7 em `tests/badge/`, 6 em `tests/split/`, 6 em `tests/demo/`, 5 em `tests/domain/baseline/`, 5 em `tests/issue_autoclose/`, 4 em `tests/domain/policy/`, 4 em `tests/review/`, 4 em `tests/infrastructure/linter/external/`, 3 em `tests/domain/check/`, 3 em `tests/infrastructure/ci/`, 3 em `tests/integration/`, 2 em `tests/domain/risk/`, 2 em `tests/domain/tests_generation/`, 2 em `tests/infrastructure/git/`, 2 em `tests/domain/linter/`, 1 em `tests/domain/finding/`, 1 em `tests/domain/mentor/`, 1 em `tests/domain/pr/`, 1 em `tests/infrastructure/baseline/`, 1 em `tests/unit/` —, **3276 cenários coletados**) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio) + fixtures de repositório git real (`tests/fix/`, `tests/split/`, `tests/test_full_diff_encoding.py`) + guarda de isolamento de rede (`tests/demo/conftest.py`, `tests/integration/conftest.py`). A extensão tem suíte Mocha própria (7 testes contra o servidor MCP real).
* **Empacotamento:** setuptools/build (PyPI) — `version = {attr = "src.updater.__version__"}`; packs embutidos via `package-data`; `packaging>=23.0`. A extensão é empacotada à parte (`vsce package`, VSIX).
* **CI/CD:** GitHub Actions — `pr-review.yml` + `action.yml` (chama `gitpr check`) + `tests.yml` (matriz Python 3.10/3.13) + `extension.yml` (build, teste e empacotamento do VSIX; publicação no Marketplace/Open VSX em tags `ext-v*`) + 🆕 `release.yml` (testes, verificação tag/versão via SSOT, build sdist/wheel, `twine check --strict`, Trusted Publishing OIDC no PyPI e criação de GitHub Release em tags `v*`).

---

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa ~90k tokens, divide automaticamente em lotes por arquivo (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce). Suporta PRs, commits e Issues. O `provider`/`model` são agregados entre os chunks e o `meta`/`modules` são repassados a `log_command_metric`.
* **Tokenizador Local:** `tokenizer.json` para estimativa precisa de tokens antes do envio para a IA.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()` com fallback para tokenizador local.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff`.
* **`get_git_staged_diff()`:** roda `git diff --cached -U1 -w -M -B -- <SMART_EXCLUDES>` com `encoding="utf-8"`/`errors="replace"` e `stdin=DEVNULL`, devolvendo `None` em falha do git (nunca string vazia disfarçada). É a fonte preferida da mensagem de commit: o que não está staged não entra no prompt.
* **`get_split_diff()`:** Diff próprio do `split`, com `SPLIT_DIFF_ARGS` (`--binary -M -U3`), **deliberadamente sem** reusar `get_git_diff()`.
* **🆕 Seed da Configuração do Projeto:** o callback raiz e o `--install` chamam `ensure_project_config()` (`src/project_config.py`) em toda invocação dentro de um repositório, exceto nos caminhos de ajuda. Arquivo existente **nunca** é sobrescrito; a criação é anunciada só no caminho interativo da raiz e pode ser desligada por `GITPR_SKIP_PROJECT_CONFIG_SEED` (escape hatch do suite de testes).
* **🆕 `get_base_branch(quiet=)`: ** a resolução da base saiu do improviso e passou a delegar a `resolve_pull_request_base()`; `quiet` evita que o aviso de fallback corrompa a TUI ou o stream JSON-RPC.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo em JSON antes de cada chamada à IA.
* **Smart Excludes com Duas Camadas:** Camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`), mescladas em runtime. Auto-seeding do arquivo local na primeira execução. `_load_smart_excludes()` aceita `force=`.
* **Métricas com Rastreamento de Tempo:** `log_command_metric()` em todos os fluxos, com `meta`, `modules` e `duration_ms`.
* **Resolução Centralizada de Output:** `resolve_output_path()` — default em `.gitpr/reports/{type}/`.
* **Wizard SCM (`run_scm_init_wizard()`)**: `gitpr --init` — detecta a forge pelo remote origin, solicita extras por forge, valida o token e persiste **somente em sucesso**.
* **Skill Template de Release (`ensure_release_skill_template()`)**: Baixa `templates/gitpr.release.*.md` no primeiro uso de `gitpr release`.
* **Guarda de Skill Corrompido:** `_CORRUPTED_PR_SKILL_ARTIFACT` documenta o fragmento JSON que vazou para o template `pt_br`, e `get_skill_context()` o remove **em memória** quando `action_type == "pr"`.
* **Registro de Skills Compartilhado:** `SKILL_FILES_BY_TYPE` / `SKILL_TYPES` / `DEFAULT_SKILL_TYPE` em `src/config.py`.
* **Motor de Review com Escopo de Cache (`generate_pr_content`):** `cache_scope` e `store_diff`; o `cache_scope` carrega também o pack de política ativo.
* **Trailer de Coautoria:** `COAUTHOR_TRAILER` + `append_coauthor_trailer()` — idempotente, preserva trailers de terceiros. É esse trailer que a TUI de commit aplica à mensagem editada antes de `execute_git_commit()`.
* **Captura de Saída do Git Endurecida:** as chamadas de `subprocess.run` em `src/cache.py`, `src/core.py`, `src/issue_engine.py` e `src/main.py` que capturam saída do git usam `encoding="utf-8"` **com** `errors="replace"` — incluindo `get_git_staged_diff()`.
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
* **Routing de Comandos:** Gerencia todas as flags e os **15 subcomandos** — `release`, `config`, `fix`, `review-pr`, `demo`, `badge`, `split`, `tests`, `explain`, `mentor`, `metrics`, `policy`, `risk`, `baseline` e `check`.
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags (33 opções Click na raiz):** 🆕 `--close-issue` e `--no-close-issue` — mutuamente exclusivas, recusadas com exit code 1 antes de qualquer prompt ou escrita, e com a regra de que `-h` vence o conflito. As demais (`--mentor`, `--explain`, `--init`, `--no-suggest-reviewers`, `--no-publish`, `--no-edit`, `--base <branch>`, `--plugins`, `--status`, `--no-unstaged-check`, `--linter-setup`, `--version` etc.) seguem inalteradas.
* **Ramo do `-c`/`--commit`:** `--hook` → comportamento silencioso e merge-aware; sem hook → `CommitApp`. **O caminho sem hook continua sem guarda de TTY** — abrir `gitpr -c` num script ainda entra na TUI.
* **🆕 Fluxo de Fechamento de Issue:** `_prepare_close_issue(flags, base, may_ask)` roda **antes** do Stage Selector, reusa o contexto SCM resolvido e devolve a decisão (linha de fechamento + issue) mais o registro. A linha entra em `insert_close_line(pr_desc_body, decision)` no ponto único de montagem do corpo. `_publish_pr_directly` agora devolve **bool** para que o registro só seja limpo depois de uma publicação real (ADR-007).
* **🆕 Resolução da Base do PR:** o ramo `--base` passa por `_resolve_pr_target()`, que corrige um valor obsoleto do arquivo do projeto quando a execução é interativa e, fora dela, relata a recusa. O arquivo `.gitpr/conf/gitpr.config.yml` é semeado em toda invocação dentro de um repositório, exceto nos caminhos de ajuda.
* **Gate de Atualização nos Subcomandos:** o callback do grupo rodava antes do gate raiz, então `gitpr release`, `fix`, `review-pr` e os demais **nunca** eram bloqueados por um release novo. O gate roda antes do `return`, condicionado a `may_ask and not update and not help_flag and not _subcommand_help_in_argv()`. `_may_ask_the_user()` exige **TTY nos dois lados** — CI, pipes, cron, hooks e o servidor MCP continuam livres.
* **🆕 `-h` Antes do Subcomando Corrigido:** `_subcommand_help_in_argv()` existe porque o Click **limpa os argumentos do contexto** antes de o callback do grupo rodar. A varredura do `argv` bruto passou a tratar o caso `gitpr -h config`, que antes abria a TUI de configuração em vez da ajuda. Coberto por `tests/test_cli_help.py`.
* **Subcomando `check` — 8 opções:** `--base <ref>`, `--format sarif|json|junit`, `-o/--output <path>`, `--fail-on …`, `--no-ia`, `--ia-only-high-risk`, `--baseline <path>` e `--policy <name>@<version>`.
* **Grupo `baseline` — 6 subcomandos:** `create`, `show`, `validate`, `update`, `suppress` e `unsuppress`.
* **Grupo `policy` — 7 subcomandos:** `list`, `show`, `validate`, `use`, `off`, `install` e `init`.
* **Grupo `metrics` — 8 subcomandos:** `export`, `bundle`, `merge`, `dashboard`, `migrate`, `prune`, `purge` e o oculto `hook-event`.
* **Subcomando `risk` — 4 opções:** `--file`, `--format text|json`, `--base`, `--no-history`.
* **Subcomando `mentor` — 2 opções:** `--finding`, `--provider`.
* **Variáveis de Ambiente (58 chaves no `DEFAULT_CONFIG`):** as quatro `GITPR_BASELINE_*`, as duas de mentor, as duas de policy e `GITPR_RISK_INCLUDE_IN_REVIEW`. **Fora do `DEFAULT_CONFIG`:** `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT`, `GITPR_METRICS_CURRENCY`, as **9 `GITPR_CHECK_*`**, `GITPR_SKIP_UPDATE_CHECK` (booleano estrito) e 🆕 `GITPR_ISSUE_AUTOCLOSE`, `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` e `GITPR_SKIP_PROJECT_CONFIG_SEED`. As duas primeiras aparecem no schema da TUI (categoria `issue`); as demais são defaults read-only deliberadamente **não** semeados no `~/.gitpr/.env`.
* **Ajuda Contextual:** `gitpr -h --explain` renderiza; `HELP_MAP["explain"]` e `HELP_PRIORITY["explain"]` apontam para `docs/explain-pr`, e `gitpr tests`/`gitpr tests generate` têm `epilog=` próprio. 🆕 `HELP_MAP` ganhou `close_issue` e `no_close_issue`.
* **Camada de escrita do `.env`:** `read_env_file_values()` lê **só o arquivo** via `dotenv_values`; `save_config_values()` com `set_key`; `remove_config_value()` com `unset_key`.
* **Portão de Baseline no Fluxo:** `main.py` resolve o gate de baseline antes de lint, review, full review, auditoria de arquivo, review remoto e risk.
* **Publicação Direta Refatorada:** `_publish_pr_directly` (`--no-edit`) delega ao **`publish_pull_request_use_case`** — o mesmo caminho do tool MCP `publish_pull_request` — e devolve se a forge criou o PR.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI para revisar, editar e publicar Pull Requests direto no terminal.
* **7 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen` e `NoticeScreen`.
* **Três Delas Também Servem ao Commit:** `StageFilesScreen`, `CommitMessageScreen` e `CommitProgressScreen` são importadas pela `CommitApp` — nenhum widget foi duplicado, e o helper `_with_suppressed_stdout` também é compartilhado.
* **🆕 `body_published` Distingue Criar de Abrir:** a `PrPublishApp` passou a marcar quando o corpo foi realmente criado/atualizado na forge, e não apenas quando um PR existente foi aberto. É esse sinal que permite limpar o registro da issue só depois de uma publicação de verdade.
* **Selo no Corpo do PR:** `attach_pr_badge()` roda em `src/main.py` logo após `pr_data` estar completo — **ponto único de injeção**.
* **`_attach_reviewers` com resolução:** Resolve o que o usuário digitou **antes** de enviar, reporta o descartado e, num `422` de lote, **repete um a um**. 🆕 Quando um provider de terceiros segue o contrato legado e devolve `None` no read-back, o log diz `(no read-back)` em vez de `attached None`.
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
* **✅ Lacunas de cobertura do ruleset fechadas nesta janela:** a regra genérica passou a pegar atribuição **sem aspas**, os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-` entraram no catálogo, e a fronteira à esquerda do nome da chave impede falsos positivos como `bypassword`. O estado da arte está detalhado na seção 31.

### **8. Auto-Updater (`src/updater.py`)**

* **PyPI como Fonte Única:** `get_latest_remote_version()` consulta `https://pypi.org/pypi/gitpr-cli/json` e grava o cache. Aceita `force=True`, usado pelo `--update` para **sempre** ir à rede.
* **Janela Corrida de 1 Hora (`UPDATE_CACHE_TTL_SECONDS = 3600`):** o cache deixou de ser "válido enquanto a data local for hoje". O documento é `{"checked_at": <ISO>, "version": ...}`; `_cache_is_fresh()` aceita idade em `[0, 3600)` segundos.
* **Validação na Leitura:** `dict` de verdade, timestamp parseável, versão string não vazia. Timestamp **no futuro** conta como expirado, e o formato legado com `date` é tratado como expirado e reescrito.
* **Escrita Atômica:** `tempfile.NamedTemporaryFile` no mesmo diretório + `os.replace`, com limpeza do temporário em caso de falha.
* **Fetch Blindado (`bounded_urlopen`):** corpo não-JSON e payload sem versão são **rejeitados antes de entrar no cache**. Teto de 3 s de wall clock, DNS incluído.
* **Comparação PEP 440:** `_coerce_version()` usa `packaging.version.Version`, tolerando o `v` inicial e sufixos PEP 440; `parse_version()` mantém o contrato de tupla para chamadores externos. `_is_newer()` **ignora pré-release remoto** numa instalação estável e trata versão ilegível de qualquer lado como desconhecida.
* **Portão Obrigatório (`enforce_update_required()`):** Devolve `True` (após imprimir as duas versões e o comando pip) quando a versão publicada é mais nova; `False` quando está atualizado, quando a versão remota é **desconhecida (offline)** ou quando a checagem está desligada.
* **Semântica Estrita do Escape:** `GITPR_SKIP_UPDATE_CHECK` é parseado contra `_SKIP_TRUTHY_VALUES` (`1`, `true`, `yes`, `on`, `y`).
* **`check_and_update()`:** Só consulta e **informa**, nunca instala.
* **Versionamento Centralizado:** `__version__` (**1.5.0** 🆕), `__lang_version__` (**v0.0.38** 🆕), `__scripts_version__` (**v0.0.4**), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`. 🆕 O SSOT do pacote virou contrato explícito ([ADR-014](docs/adr/0014-canonical-package-version-ssot.md)) e está coberto por `tests/unit/test_version_consistency.py`.
* **⚠️ Estado do release — tagueado, não publicado:** a tag `v1.5.0` aponta para o merge do PR #260 (`4c2bede`, 2026-11-04) e a seção `[1.5.0] - 2026-11-03` está commitada no `CHANGELOG.md`. O PyPI, porém, ainda serve **1.4.4** — a publicação pelo `release.yml` precisa ser executada/confirmada. Enquanto isso, o gate não bloqueia ninguém (a versão remota é mais antiga que a local).
* **Gate Revalidado:** com a 1.4.4 publicada na janela anterior, o cenário 1.4.2 → 1.4.4 foi coberto pelo TTL de 1 hora; a revalidação real em cliente antigo continua sendo um acompanhamento de campo.

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Histórico de mensagens, input multi-linha, barra de status com bindings visíveis. `ENABLE_COMMAND_PALETTE = False`.
* **Memória por Branch (`src/chat_memory.py`):** Histórico persistido por branch, com continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear`. O `/tests` (e os aliases localizados) delega ao **mesmo caso de uso** que o CLI usa.
* **Auto-Patching (F5), Atualização de Diff (F2), Exportação de Sessão (F6).**
* **Extrator Compartilhado:** F5 e `ctrl+s` chamam `patch_extractor.extract_code_blocks()` — comportamento visível idêntico, sem lógica duplicada.
* **🆕 Ajuda Localizada de Verdade:** `ChatHelpScreen` deixou de ter literais estáticos e compõe cada linha via `__()`, com os rótulos corrigidos (`Ctrl+Shift+S`, `Ctrl+Shift+E`).

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta o idioma do SO na primeira execução e salva em `GITPR_LANG`; o diretório do perfil é criado **antes** de persistir.
* **5 Idiomas, 6 Dicionários:** en_us (padrão/fallback), pt_br, pt_pt, es/es_es, fr/fr_fr.
* **Arquivos Versionados:** `__lang_version__` (**v0.0.38** 🆕) controla a atualização dos pacotes (`langs/*.json`).
* **✅ Cobertura — a dívida foi paga:** os **seis** arquivos têm **1698 chaves** cada. O código usa as mesmas chaves; não há chave sem dicionário nem órfã. `tests/test_i18n.py` fecha **22 verdes**, incluindo a paridade de contagem, a ausência de chaves faltantes/órfãs e o guarda de identidade.
* **🆕 O Bump de Idioma Agora Tem Conteúdo:** `__lang_version__` passou de v0.0.36 para **v0.0.38** e, desta vez, os dicionários mudaram: espanhol e francês foram sincronizados com policy packs, baseline, mentor, risk, MCP, base do PR, configuração de projeto e atalhos do chat; a renovação OTA entrega tradução nova.
* **🆕 Guarda Contra Regressão:** `test_all_identity_keys_are_allowlisted` falha quando uma chave cujo valor é igual ao inglês não está na allowlist de termos técnicos/acrônimos/cognatos legítimos.
* **Snapshot de Ambiente (`AMBIENT_ENV_KEYS`):** `frozenset(os.environ)` capturado **imediatamente antes** do `load_dotenv()` de módulo.
* **Cache com Indexação por Idioma:** As respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.
* **Fonte de Tradução em Lockstep:** uma chave nova precisa existir no código, em `langs/pt_br.json` (lista mestra), nos dicts FR/ES de `scripts/sync_all_langs.py` e nos valores curados de `scripts/fix_mangled_i18n_keys.py`. 🆕 O extrator do `sync_i18n.py` usa **AST**, não regex.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA com caracteres braille e palavras de "pensamento".
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas. `_load_thinking_words()` / `reload_thinking_words()` aceitam `force=`.
* **O Commit TUI Não Usa o Spinner:** a TUI mostra `CommitProgressScreen` com barra animada própria, e a chamada de IA roda numa `threading.Thread` daemon. Em `--hook` o spinner clássico continua sendo o único feedback.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini, DeepSeek e Ollama (local), com primário/secundário por provedor.
* **Modo JSON & Parâmetros Determinísticos:** `temperature=0.0` e `top_p=0.1`; fallback automático entre provedores configurados.
* **Timeout de IA:** default de **180s** (`GITPR_AI_TIMEOUT`).
* **Chamadas com `quiet`:** o release e as features novas encaminham `quiet` até a camada de IA, para que o spinner nunca corrompa uma saída `--format json`.
* **Uma chamada por vez, com cache:** mentor e explain reusam o cache MD5 por prompt.
* **Payload Já Parseado:** `parse_explain_payload()` e `generate_test_file` aceitam o **dict** que o provider entrega, com fallback para string JSON crua (respostas antigas do cache).
* **Supressão de Stdout no Commit:** `_generate_commit_msg()` redireciona `sys.stdout` para `os.devnull` durante a chamada (o mesmo padrão de `_with_suppressed_stdout`), restaurando no `finally` — um print do provider não corrompe a tela Textual.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt, com indexação por idioma.
* **Seleção do Último Review (`resolve_last_review()`):** Escolhe o registro `review`/`fullreview` **mais novo** para um par repo+branch — é a porta de entrada do `gitpr fix` e do `gitpr mentor`.
* **Diff Revisado (`reviewed_diff`):** Campo no topo do registro que guarda o diff efetivamente revisado.
* **Telemetria e Duração:** Persistência de `duration_ms` e `meta_raw`.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` é **ponte de pré-migração**.
* **Efeito da Sanitização de Skill:** como `get_skill_context()` remove o fragmento corrompido do prompt de PR, a chave MD5 muda e respostas antigas contaminadas não são reutilizadas.
* **`git config` Decodificado com Segurança:** as leituras de `user.name`/`user.email` usam `encoding="utf-8"` + `errors="replace"`.
* **O Commit Reusa o Cache:** a TUI chama `generate_pr_content("commit", "commit", diff_text, provider)`, então a mesma mensagem para o mesmo diff não gera uma segunda chamada de IA.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`) e Arqueologia por Blame (`-b`).
* **Publicação Multi-Forge:** F3 cria a issue na forge **configurada** (`GITPR_SCM_PROVIDER`) via `provider.create_issue` — Azure DevOps levanta `ScmNotSupportedError`.
* **Map-Reduce para Issues:** Contexto acima de ~90k tokens é dividido e unificado.
* **Tratamento de 401:** Sinalização de reautenticação sem fechar a aplicação.
* **`git remote -v` Decodificado com Segurança:** a chamada usa `encoding="utf-8"` + `errors="replace"`.
* **🆕 O Número Deixou de se Perder:** após uma criação bem-sucedida no GitHub, `register_created_issue()` grava o número em `.gitpr/conf/github.yml`. Falhas de bookkeeping são engolidas — um problema local nunca transforma uma criação bem-sucedida em erro — e a primeira escrita adiciona o arquivo ao `.gitignore`.

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia evolução e autoria histórica com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos via `log_blame_metric()` com profundidade e número de commits analisados.
* **Agora também alimenta o risco:** o leitor de histórico do score (`risk_history_reader.py`) usa a mesma janela de 90 dias e classifica bugs/reverts por padrão, sem chamar IA.

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)**

* **18 Ferramentas MCP Anotadas:** `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`, `list_fix_candidates`, `review_remote_pr`, `get_baseline_status`, `get_usage_metrics`, `run_check` e `publish_pull_request`. 🆕 O fechamento de issue **não** virou tool: é comportamento do fluxo de PR.
* **Parâmetros Opt-In no Contrato:** `review_code` e `full_review` aceitam `mentor: bool = False`; `generate_pr_description` aceita `explain: bool = False`. São **puramente por parâmetro** — nunca fazem OR com os defaults do `.env`.
* **19 Recursos + 7 Prompts Templatizados:** `skill://list` + `skill://{pr,commit,review,filereview,issue,blame,release,fix}` + `linter://config` + `baseline://summary` + `prompt://list` + 7 prompts.
* **Registro de Skills Alinhado:** `mcp_server.SKILL_FILES` tem **11 entradas** (`tests`, `explain` e `mentor` incluídos); `TestSkillRegistryAgreement` passa.
* **Invocação CLI Direta:** `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool sem iniciar o servidor stdio; `gitpr-mcp --list` imprime o registry completo como JSON.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve no `sys.__stdout__` original, com fallback para `buffer` ou re-encode com `errors='replace'` em code pages legadas do Windows.
* **Offload do Event Loop:** Decorator `_offload` (`anyio.to_thread.run_sync`) em todas as tools — a ordem dos decorators importa (`@mcp.tool` **acima** de `@_offload`).
* **Falhas como Erro Estruturado:** as tools novas devolvem falha **como dado** em vez de levantar.
* **🆕 `publish_pull_request` com o Resolvedor Compartilhado:** usa `resolve_pull_request_base()`, devolve envelope `{"status": "error"}` para `BaseBranchError` e expõe os `warnings` do resolvedor no payload e no catálogo da tool.
* **Métricas MCP:** `run_check` e `publish_pull_request` gravam linhas locais (`mcp:check`, `mcp:publish_pr`).
* **O servidor MCP nunca é bloqueado pelo gate:** `--mcp`/`gitpr-mcp` está na lista de isenções desde a primeira versão do gate.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório:** Rótulo `📁 Repository: owner/repo` e filtragem estrita por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com `ProgressBar`; os testes aguardam `workers.wait_for_complete()` antes de asseverar.
* **Leitura do Ledger:** o dashboard consulta o `telemetry.db` na thread de trabalho, renderizando as cinco seções (custo, qualidade, módulos, provedores, ciclo) a partir dos mesmos renderizadores que o CLI usa.
* **Assistente de Migração (`src/ui/metrics_migration_app.py`):** oferece importar os arquivos legados, importar **e** reconstruir a partir do cache de IA, ou "agora não".
* **🆕 Artefatos de Exportação Destrackeados:** os **34 arquivos** de `.gitpr/metrics/export/` que continuavam rastreados foram removidos do índice (`git rm --cached`); o `.gitignore` agora é a única fonte sobre eles.

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`, resolvido por `src/infrastructure/git/identity.py`.
* **Eventos de Hook, Linter e Blame:** `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()`. O `gitpr check` grava `command="check"` com `findings_total`/`findings_errors` e exit code.
* **🆕 Evento `issue_autoclose`:** uma linha por decisão de fechamento, com `asked`, `accepted` e `skipped_reason` no `meta` — permite medir quantas ofertas foram aceitas, recusadas e por qual motivo.
* **Exportação e Limpeza:** `gitpr metrics export` (CSV/JSON), `prune`, `purge` com confirmação interativa, `bundle`/`merge` para transportar e fundir janelas.
* **O Commit Interativo Também Mede:** o caminho `commit` continua gravando a linha de comando com `meta` e `modules`; a TUI não criou um tipo de métrica novo.

### **19. Sincronização de Idiomas dos Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (**v0.0.4**, inalterada).
* **Templates reescritos na janela v0.0.17:** `post-checkout`, `post-merge` e `pre-push` chamam `gitpr --quiet metrics hook-event <nome>`, guardados por `command -v gitpr` e `|| true`.
* **Mapeamento de Sufixos (`HOOK_SCRIPT_SUFFIXES`):** Códigos de interface (`es_es`, `fr_fr`) traduzidos para os sufixos publicados (`.es`, `.fr`).
* **Escolha vs. Estado (`SCRIPTS_LANG` / `SCRIPTS_INSTALLED_LANG`):** Permite **detectar a troca de idioma**.
* **`effective_hook_lang()`:** Resolve o idioma efetivo; `--lang` deixou de ser descartado nesse caminho.
* **Skip de Merge-Source:** O `prepare-commit-msg` pula as fontes `message|merge|squash|commit`.
* **O `prepare-commit-msg` Continua Não-Interativo:** o hook roda com `--hook`, então **nunca** abre a `CommitApp` — a TUI só existe no uso humano de `gitpr -c`.
* **Os hooks rodam com `--quiet` e `--hook`, portanto nunca são bloqueados pelo gate de atualização.**

### **20. Bridge de Linters Externos e Assistente Interativo (`src/linter_wizard.py`, `src/ui/linter_app.py`)**

* **Assistente `--linter-setup`:** Wizard com presets numerados (PHP_CodeSniffer, ESLint, Stylelint) e injeção do bloco `external_linters`.
* **Presets Remotos:** `templates/gitpr.linter-presets.json` com cadeia local → download → stale → fallback embutido.
* **TUI de Erros do Linter:** `src/ui/linter_app.py` (Textual) exibe erros críticos e warnings; em hook/quiet imprime e faz `sys.exit(1)`.
* **Relatório Markdown:** Consolidado em `.gitpr/reports/linter/` apenas quando há violações.
* **A Camada SAST é irmã, não substituta:** os bridges Semgrep/Gitleaks/Bandit alimentam o **mesmo** pipeline de relatório — e também o `gitpr check`.

### **21. SCM Multi-Forge (`src/infrastructure/scm/`)**

* **Abstração Única (`ScmProvider` ABC):** `base.py` define o contrato (dataclasses `RepoRef`, `PullRequestDraft` etc. e `ScmProviderError(provider, http_status, message)` — `http_status` 0 = falha de rede).
* **Registry e Factory:** `resolve_scm_provider()` seleciona por `GITPR_SCM_PROVIDER` (default `github`); `detect_provider_from_remote()` identifica a forge pela URL do origin.
* **`list_pull_requests(repo, state, since, until)` — paginado e canônico:** os quatro provedores traduzem os estados canônicos (`open`/`merged`/`closed`/`all`) para o vocabulário nativo, paginam no cursor de cada API e filtram por janela inclusiva de datas.
* **Por que o filtro é por data do estado:** três das quatro forges devolvem algo mais largo para um PR mergeado, então cada uma filtra a própria resposta contra a data que o estado implica.
* **`supports_merged_dates`:** atributo de classe, `False` no Bitbucket Cloud, que publica **vazio** o `merged_at`.
* **`web_links.py`:** funções puras (`repo_web_base`, `commit_url`, `pull_request_url`, `user_url`) normalizam qualquer formato de remote.
* **`get_pull_request(repo, pr_id)` — método concreto da ABC:** default levanta `ScmNotSupportedError` e cada forge implementa.
* **🆕 `IssueInfo` e as Operações de Issue:** `get_issue()` devolve `IssueInfo` com `state` no vocabulário da forge e `is_pull_request`; `get_default_branch()` lê a branch padrão; `closing_line()` devolve a sintaxe de fechamento (`close #N` no GitHub). As três são **defaults concretos** da ABC que levantam `ScmNotSupportedError`, então as outras três forges degradam para "feature inativa" em vez de quebrar.
* **GitHub:** `GET /repos/{o}/{r}/issues/{n}` (marcando `pull_request` e caindo para o número pedido quando ausente), `GET /repos/{o}/{r}` para `default_branch` (string vazia quando ausente) e o keyword `close #N`.
* **Cabeçalhos do GitLab Sintetizados:** `changes[].diff` é um hunk solto; `old_path`/`new_path` montam os cabeçalhos `diff --git a/… / --- / +++`, honrando `/dev/null`. E `overflow: true` **levanta** em vez de revisar metade de um diff truncado.
* **`request_pull_request_reviewers` devolve `list[str]`:** Devolve os logins **efetivamente anexados**, lidos do corpo do `201`. 🆕 A quebra de contrato está documentada em [ADR-0009](docs/adr/0009-reviewer-attach-returns-read-back.md) e em `docs/suggested-reviewers.*`/`docs/scm-multiforge.*`.
* **Helpers Read-Only do GitHub:** `get_commit_author_login` e `get_user_login`.
* **Fail-Fast por Forge:** Azure exige `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`; Bitbucket exige `GITPR_SCM_USERNAME`; `create_issue` no Azure levanta `ScmNotSupportedError`.
* **Publicação de Releases:** `provider.create_release()` usado pelo `gitpr release --publish`.
* **Publicação de PR Compartilhada:** `src/application/use_cases/publish_pull_request.py`, usado pelo `--no-edit` e pelo tool MCP. Valida título/corpo, **exige `provider.token` apenas quando `check_remote_state=True`**, opcionalmente verifica PR existente e branch não empurrada, mascara mensagens de erro e devolve `PublishPrOutcome`. Os campos `url`/`number` do resultado são lidos com `getattr` defensivo.
* **Artefatos:** Glossário + ADR-001/ADR-005; família `docs/scm-multiforge.*.md` em 5 idiomas; 9 arquivos de teste, **317 cenários**.

### **22. Subcomando `gitpr release` — Changelog / Release Notes (`src/release_engine.py`)**

* **Fluxo:** `git log` entre `--since` e `HEAD` → classificação por Conventional Commits → bump semântico sugerido → montagem do changelog → resumo executivo de IA opcional → *prepend* no `CHANGELOG.md`.
* **O Range Deixou de Vir do `git describe`:** a origem do range é a **seção anterior do próprio changelog**, por dois âncoras: o hash mais novo daquela seção e, como fallback, a tag da versão da seção.
* **`_drop_released()` — a segunda linha de defesa:** qualquer commit cujo hash curto apareça em **outra** seção de versão é descartado, com contagem.
* **Todo bullet virou link:** `- {subject} ([{short_hash}]({commit_url})) — {scope} · [#{n}]({pr_url}) · {YYYY-MM-DD}`.
* **A falha de PR mergeado por merge commit:** uma segunda passada (`git log --merges`) monta `hash → PR` pela ancestralidade. 🆕 A seção `[1.5.0]` cobre 7 PRs mergeados e lista os 15 merges da janela sem perder nenhum.
* **Contribuidores resolvidos pela mesma escada dos revisores:** `get_commit_author_login` primeiro, depois `email_to_handle`, com cache em `~/.gitpr/cache/contributors.json`.
* **A Fronteira da Seção Era um Bug Latente:** `upsert_changelog(force=True)` substitui da linha `## [x.y.z]` até o próximo cabeçalho de **nível 2**.
* **Classificador (`src/commit_classifier.py`)** e **Builder com Seções Traduzíveis (`src/changelog_builder.py`)**.
* **Bump Semântico (`src/version_bump.py`)** e **Publicação** (`--publish`, `--draft`, `--format markdown|json`, `--force`). **6 opções no subcomando.**
* **🆕 Estado do release:** a seção `## [1.5.0] - 2026-11-03` está commitada e traduzida; a tag `v1.5.0` existe. **A publicação no PyPI ainda não aconteceu** — o pacote servido continua sendo 1.4.4.
* **O subcomando passa pelo gate de atualização** quando executado num terminal interativo.
* **Artefatos:** `docs/release-notes.*.md` em 5 idiomas, ADR e `tests/test_web_links.py`.

### **23. Subcomando `gitpr config` — TUI de Configuração**

* **Tela Master-Detail (`src/ui/config_app.py`):** Categorias à esquerda, campos à direita, editados inline. Cabeçalho com busca (`/`) e contador de pendências; rodapé `F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc`. `ENABLE_COMMAND_PALETTE = False`.
* **Schema Declarativo (`src/config_schema.py`) — a fonte única de verdade:** **17 categorias** e **85 `ConfigField`**, dos quais **8 avançados**. As 9 `GITPR_CHECK_*` ainda **não** estão no schema.
* **🆕 Categoria `project` e o Atributo `store`:** os campos declaram onde moram (`env` vs `project`). Os três campos do projeto são o path do arquivo (read-only), a branch alvo (editável) e a base efetiva com a origem (read-only). O novo `KIND_BRANCH` renderiza a escolha de branch.
* **🆕 Categoria `issue`:** `GITPR_ISSUE_AUTOCLOSE` e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` aparecem aqui.
* **🆕 Escrita por Store:** a `ConfigApp` despacha por `store`: valores de projeto **nunca** passam por `save_config_values()`, são gravados primeiro, suportam remoção ao esvaziar, recusam a branch atual e nunca sobrescrevem YAML ilegível. A linha da base efetiva é atualizada in-place depois de salvar.
* **Categorias `policy` e `baseline`:** os campos de pack e os quatro do baseline.
* **Seção Skills Alinhada:** `SKILL_LABELS` tem **11 entradas** (`tests`, `explain`, `mentor`).
* **Filtragem por Contexto (`show_if`):** `GEMINI_*`/`DEEPSEEK_*`/`OLLAMA_*` conforme o `DEFAULT_AI_PROVIDER`; `GITPR_SCM_USERNAME` sob `[Bitbucket]`; `GITPR_SCM_ORGANIZATION`/`PROJECT` sob `[Azure DevOps]`.
* **Busca Global (`/`):** Casa chave ou rótulo em todas as categorias e **ignora o filtro de visibilidade**.
* **Validação em Duas Camadas:** **Offline** bloqueia o `F2` com erro inline; **online** (só credenciais alteradas na sessão) roda em worker com timeout de 10s e só bloqueia em `401`/`403`.
* **Restaurar (`Ctrl+R`):** Remove a linha do `.env` em vez de reescrever o default; `Esc` com pendências pede confirmação.
* **Seção Skills — a única project-scoped até agora:** Edita `.gitpr/skill/*.md` do projeto resolvidos a partir do diretório de chamada, gravando atomicamente e preservando CRLF/LF. 🆕 A categoria `project` introduz uma **segunda** superfície versionada, com o mesmo cuidado de escrita atômica.
* **Downloads com Força:** Botões que forçam re-download de smart-excludes, traduções, presets e thinking words via `force=`.
* **Módulo de Links Leve (`src/doc_links.py`):** `doc_url()` saiu de `core.py` para a UI obter o link sem importar SDKs de IA.
* **Testes:** 5 arquivos — `test_config_app.py` (88), `test_config_schema.py` (46), `test_config_validation.py` (40), `test_config_store.py` (22), `test_config_cli.py` (9), mais 🆕 `test_config_issue_autoclose.py` (10).
* **✅ Dívida fechada:** `gitpr -h config` deixou de abrir a TUI e passou a renderizar a ajuda (`tests/test_cli_help.py`).

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
* **✅ Documentação agora completa nos 5 idiomas:** `docs/review-pr.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md` e `.fr_fr.md` — o tópico deixou de ser parcial.
* **Testes:** 4 arquivos em `tests/review/` (**97 cenários**).

### **27. Resolução de Identidade do Revisor (`src/reviewer_resolution.py`)**

* **O Bug (duas falhas silenciosas encadeadas):** (1) **Prefill vazio** — `handles` só com `email_to_handle()`; (2) **Attach não verificado** — valores repassados *verbatim*, o GitHub respondia **201 sem anexar ninguém** e o `_request()` retornava sem levantar.
* **Módulo:** Plano, sem I/O próprio, **que nunca levanta**. `resolve_candidates()` (antes da TUI) e `resolve_typed_reviewers()` (no attach); `match_candidate()` casa exato e normalizado por login, nome ou e-mail.
* **Escada de Resolução:** handle conhecido (sem requisição) → casamento exato com uma pessoa sugerida → lookup por e-mail → validação do login na forge.
* **O que não resolve nunca é enviado:** Sai em `ResolutionOutcome.dropped` como `(valor, motivo_i18n)` e é descartado com aviso visível.
* **A Mesma Escada Serve ao Release:** o `release_engine` reusa `get_commit_author_login` + `email_to_handle`.
* **🆕 Companheiro Legado:** se um provider de terceiros devolver `None` (contrato antigo), o log diz `(no read-back)` e o fluxo segue — um read-back ausente **nunca** é tratado como falha.
* **Testes:** `tests/test_reviewer_resolution.py` (18) + ampliações em `test_github_provider.py` (86), `test_pr_publish_app.py` (59), `test_suggest_reviewers.py` (17), `test_reviewer_suggestion.py` (18) e `test_main_suggest_reviewers.py` (8).

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
* **Testes:** 7 arquivos em `tests/badge/` (**83 cenários**), todos verdes desde a janela v0.0.20.
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

### **31. Varredura de Segredos Embutida (`src/security_ruleset.py`) 🆕 Cobertura Ampliada**

* **O que é:** Sete regras que rodam em **toda** invocação do linter, mescladas ao fim de `load_linter_rules()` depois das regras do projeto e dos plugins.
* **As Sete Regras:** cinco `error` bloqueantes — AWS access key ID, token GitHub, token Slack, chave de API Google e bloco de chave privada — e duas `warning`: URL de conexão de banco com credenciais e atribuição genérica de credencial, esta atrás de um filtro de placeholder (`changeme`, `xxxxxx`, `example`, `dummy`, `sample`, `your_password_here`, `sua_senha`).
* **✅ As Três Lacunas Fechadas:** a regra genérica agora pega **atribuição sem aspas** (`.env`/YAML `API_KEY=abc123`), os prefixos **`ASIA…`**, **`github_pat_…`** e **`xoxc-`/`xoxd-`** entraram no catálogo, e há **fronteira à esquerda** no nome da chave — `bypassword` não casa mais. Expressões de runtime (`os.getenv(...)`, `process.env.X`) também deixaram de gerar falso positivo.
* **Por que no Pacote e Não no Template:** Um portão de segredos precisa se comportar **igual** em toda máquina e em todo CI.
* **Configuração:** `GITPR_LINTER_SECURITY` (default `true`; opt-out fail-open) e `GITPR_LINTER_SECURITY_DISABLED_RULES` (`;`-separadas).
* **Testes:** `tests/test_security_ruleset.py` (**77 cenários**, eram 61) — matriz de regex, placeholders, nível, wildcard, merge e traduções; a invariante "o alerta nunca ecoa o valor" segue valendo.
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
* **`-h --explain` Consertado:** a opção usava dest `explain_flag`, mas o `HELP_MAP` procurava `explain` — a ajuda contextual voltou a renderizar.
* **Documentado em 5 idiomas:** `docs/explain-pr.*.md` (5 arquivos), com link no `HELP_MAP["explain"]`, no epilog do comando e no README.
* **Configuração:** `GITPR_EXPLAIN_BY_DEFAULT` (default `false`).

### **35. Suíte Determinística e o CI (`.github/workflows/tests.yml`, `release.yml`)**

* **O que é:** O workflow que roda a suíte em **Python 3.10** (o piso declarado em `pyproject.toml`) e **3.13**, com `fail-fast: false`.
* **`tests/conftest.py` Hermético:** Pina `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false` e `LANG_VERSION` na versão do código, além de `GITPR_SHOW_LOGS=false`, `GITPR_SKIP_UPDATE_CHECK=true` e 🆕 `GITPR_SKIP_PROJECT_CONFIG_SEED=true` (o suite nunca escreve em um checkout de desenvolvedor).
* **Ordem Importa:** `src.updater` é importado **antes** das variáveis de idioma serem definidas.
* **Estabilidade de Testes de Worker:** `test_config_app.py` e `test_metrics.py` aguardam `workers.wait_for_complete()` antes de asseverar.
* **Dependência do Workflow:** O runner limpo não tem `~/.gitpr`, e `test_demo_isolation.py` assevera que o perfil existe — o job cria o diretório e o `.env` vazio explicitamente.
* **🆕 Nesta janela a suíte ganhou 266 cenários e 12 módulos:** `tests/issue_autoclose/` (5 arquivos, **120 cenários**), `test_project_config.py` (41), `test_pr_base_app.py` (12), `test_config_issue_autoclose.py` (10), `test_cli_help.py` (9), `test_project_config_cli.py` (7), `tests/unit/test_version_consistency.py` (5), `tests/integration/test_baseline_exit_code_contract.py` (8), além do crescimento de `test_mcp_server.py` (117), `test_security_ruleset.py` (77), `test_github_provider.py` (86), `test_config_app.py` (88), `test_pr_publish_app.py` (59), `test_config_schema.py` (46) e `test_i18n.py` (22). **Total: 3276 cenários em 153 arquivos.**
* **Workflow da extensão:** `.github/workflows/extension.yml` roda `npm install`, compila, testa e empacota o VSIX; em tags `ext-v*` publica no VS Code Marketplace e no Open VSX, pulando cada passo quando `VSCE_PAT`/`OVSX_PAT` está vazio.
* **🆕 Workflow de Release:** `release.yml` roda testes, verifica a consistência tag ↔ `src.updater.__version__`, builda sdist/wheel, valida com `twine check --strict`, publica por Trusted Publishing (OIDC) e cria o GitHub Release. O SSOT de versão também tem teste próprio (`tests/unit/test_version_consistency.py`).

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
* **🆕 `issue_autoclose` Entra no Ledger:** uma linha por decisão, com `asked`, `accepted` e `skipped_reason`; a doc de métricas lista o comando ao lado dos demais.
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
* **✅ Isolamento de Teste Corrigido:** `@patch("src.core.get_git_diff")` passou a `@patch("src.main.get_git_diff")` — o nome é importado por valor em `src/main.py`, então o patch antigo não alcançava o código sob teste. As **duas falhas herdadas mais antigas da suíte** fecharam.
* **Testes:** `tests/domain/mentor/test_mentor_explanation_builder.py` (8), `tests/application/use_cases/test_generate_mentor_explanation.py` (5) e `tests/test_mentor_cli.py` (4) — **todos verdes**.
* **Artefatos:** `docs/mentor-mode.*.md` em **5 idiomas**, ADR-009, `glossary-gitpr-mentor.md`, spec e relatórios de tarefa.

### **38. Subcomando `gitpr risk` — Score de Risco Determinístico (`src/domain/risk/`)**

* **O que é:** Um score **0–100** com nível `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`, calculado **sem IA** a partir de sinais locais.
* **Domain Layer Puro (`risk_types.py`, `risk_rules.py`, `risk_calculator.py`, `risk_explanation.py`):** enums e dataclasses; pesos, limiares, padrões de caminho crítico, casamento por glob e detecção de teste/não-executável carregados de YAML; cálculo por arquivo com **clamp 0–100** e agregação 50/30/20.
* **A Fórmula é Declarada, Não Aprendida:** **50%** o arquivo de maior risco, **30%** a média ponderada por linhas e **20%** evidência crítica.
* **Infrastructure Adapters:** `risk_history_reader.py` lê `git log` e extrai commits, correções de bug e reverts numa janela de **90 dias**; `test_matcher.py` casa arquivo de teste ↔ produção por convenção.
* **Use Case (`calculate_risk.py`):** correlaciona seções do diff, achados, casamento de testes e histórico em `FileRisk`/`PullRequestRisk`, **degradando com aviso** quando um sinal não está disponível.
* **🆕 Path Tolerante:** a agregação do `check` aceitava só `path` e silenciava entradas com `file_path`, produzindo `high_risk_files` e `file_risk_map` com chaves vazias. Agora qualquer um dos dois atributos serve — o report de risco não degrada em silêncio.
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
* **🆕 O Contrato Virou Teste:** `tests/integration/test_baseline_exit_code_contract.py` (8 cenários) trava os dois códigos — o fluxo que não consegue aplicar o baseline nunca se disfarça de execução limpa.
* **Alcance:** CLI (6 subcomandos, todos com `--format json`), MCP (`get_baseline_status` + `baseline://summary`), review de PR remoto e o fluxo de lint.
* **Refatoração que a Feature Exigiu:** `NormalizedFinding` virou tipo canônico em `src/domain/finding/`.
* **Testes:** `tests/domain/baseline/` (5 arquivos, **126**), `tests/application/use_cases/` (5 arquivos, **141**), `tests/infrastructure/baseline/test_local_baseline_repository.py` (24), `tests/domain/finding/test_finding_types.py` (3), `tests/domain/linter/test_structured_findings.py` (44), `tests/test_baseline_cli.py` (54) e `tests/integration/test_baseline_effect_on_review_linter_risk.py` (34) + 🆕 `tests/integration/test_baseline_exit_code_contract.py` (8).
* **Artefatos:** `docs/baseline-suppressions.*.md` em **5 idiomas**, ADR-012, `glossary-baseline.md`, spec/plano/survey e relatório de tarefa.

### **41. Subcomando `gitpr check` — Portão Unificado de CI (`src/domain/check/`, `src/infrastructure/ci/`)**

* **O que é:** Um **único ponto de entrada** para pipelines de CI que orquestra análise estática, bridges SAST, varredura de segredos, review de IA opcional, score de risco e classificação de baseline, e emite **um artefato padronizado** com código de saída determinístico.
* **A Ordem do Pipeline é Contrato:** (1) resolução de policy — inválida sai com `2`; (2) extração do diff com smart excludes; (3) linter regex + segredos + bridges externos; (4) score de risco preliminar; (5) **review de IA opcional**; (6) classificação de baseline; (7) avaliação do limiar `--fail-on`; (8) geração do artefato com **mascaramento de segredos**.
* **Domain Layer (`src/domain/check/`):** `check_types.py` (severidade normalizada em três níveis com aliases de spec); `check_config.py` (precedência **CLI > env > defaults**); `check_output.py` (dispatch de formato e escrita atômica).
* **Infrastructure Layer (`src/infrastructure/ci/`):** `sarif_builder.py` (SARIF 2.1.0), `junit_builder.py` (testsuites com `<failure>` e `<system-out>`) e `masking.py`.
* **Use Case (`run_check.py`):** `resolve_diff_base()` (explícito → `GITHUB_BASE_REF` → `origin/main` → `HEAD`), execução do linter e dos bridges, score de risco, review opcional, baseline e envelope final. O stdout emite **só o artefato**. 🆕 A agregação de risco aceita `path` **ou** `file_path`.
* **Códigos de Saída:** `0` sucesso; `1` achado contável no limiar; `2` erro de execução — agora com o contrato do baseline coberto por teste.
* **CLI:** `gitpr check` com 8 opções e 9 variáveis `GITPR_CHECK_*`.
* **GitHub Action Reescrita:** `action.yml` virou um único passo `gitpr check`. **Quebra declarada** para workflows que dependiam de `--linter` + `--fullreview`.
* **Testes:** 45 cenários — `test_run_check.py` (8), `test_check_types.py` (8), `test_check_config.py` (3), `test_check_output.py` (3), `test_masking.py` (6), `test_sarif_builder.py` (2), `test_junit_builder.py` (2), `test_check_cli.py` (5) e 🆕 `test_baseline_exit_code_contract.py` (8).
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
* **O Que a Extensão Não Faz:** não commita, não faz push e não publica sem confirmação. O comando `gitpr.commit` da extensão chama a tool MCP `generate_commit_message` — ele **não** abre a TUI, que é exclusiva do terminal. 🆕 O fechamento automático de issue também é **exclusivo do CLI**: a extensão não tem caminho para registrar a issue criada.
* **Testes:** suíte Mocha própria (7 cenários, incluindo stdio real) + `tests/test_mcp_server.py` (117 cenários).
* **Artefatos:** `docs/editor-extension.*.md` em **5 idiomas**, ADR-014, `glossary-editor-extension.md`, specs, `plansfacts` e relatório do Gemini.

### **43. TUI de Commit Interativo (`src/ui/commit_app.py`)**

* **O que é:** `gitpr -c`/`--commit` deixou de ser um pipeline silencioso — validava a árvore, pedia a mensagem à IA e commitava de imediato, sem deixar escolher arquivos, revisar o texto ou recusar uma sugestão ruim. Agora é uma `CommitApp(App)` de **4 etapas** que mantém o desenvolvedor no controle até o `git commit`.
* **Pacote:** um módulo só, `src/ui/commit_app.py` (220 linhas). Os três modais são **importados** de `src/ui/pr_publish_app.py` (`StageFilesScreen`, `CommitMessageScreen`, `CommitProgressScreen`) junto com `_with_suppressed_stdout` — **zero widget duplicado**.
* **As 4 Etapas:**
  1. **Stage Selector:** se há arquivos fora do índice, abre `StageFilesScreen` com checkboxes, "Select All", "Deselect All", "Stage Selected", "Skip Staging" e "Cancel". Índice já completo → a etapa é pulada.
  2. **Geração:** lê `get_git_staged_diff()`, cai para `get_git_diff()` quando nada está staged, e chama `generate_pr_content("commit", "commit", diff_text, provider)` numa `threading.Thread` daemon enquanto o `CommitProgressScreen` anima.
  3. **Revisão:** `CommitMessageScreen` mostra a mensagem, que pode ser editada antes de confirmar — a mensagem **editada** é a que vai para o git.
  4. **Execução:** novo `CommitProgressScreen` roda `execute_git_commit(append_coauthor_trailer(msg))` e registra o SHA no log.
* **Toda Falha Vira Estado, Não Exceção:** a IA quebrada cai para `__("Code update")`; o commit que levanta vira `failed` com a saída capturada. Estados terminais: `no_changes`, `cancelled`, `committed`, `failed`.
* **Auto-Exit no Sucesso:** `log.mark_finished(False)` remove o botão, e `_schedule_auto_exit()` registra `set_timer(0.6, self.exit)` — o usuário volta ao prompt sem clicar em nada. **Em erro o Close é mantido**, porque é ali que o log da falha fica legível.
* **`--hook` Intocado:** o caminho de hook continua sem TUI e merge-aware (`is_merge_in_progress()` → `return` silencioso). O `prepare-commit-msg` nunca abre a aplicação.
* **Configuração:** `GITPR_SKIP_UNSTAGED_CHECK` (pula o Stage Selector) e `GITPR_AUTO_STAGE` (stageia tudo e segue), ambos já existentes no `DEFAULT_CONFIG` e no schema da TUI de configuração.
* **Detalhes de Textual:** `ENABLE_COMMAND_PALETTE = False`; `on_button_pressed` trata o `#btn_close`; `_on_commit_progress_dismissed` lê `_commit_success` em vez de assumir sucesso quando o modal fecha.
* **⚠️ Quebra de Comportamento (ainda aberta):** sem `--hook`, `gitpr -c` **sempre** abre a TUI — não há guarda de TTY no roteamento. Um script ou job de CI que contava com o commit silencioso precisa passar a usar `--hook`; `GITPR_SKIP_UNSTAGED_CHECK`/`--no-unstaged-check` só pulam a etapa 1.
* **Testes:** `tests/test_commit_app.py` (**14 cenários**) — cada transição de estado e callback, mais um fluxo headless completo com o pilot do `run_test()`.
* **Domínio:** `CONTEXT.md` mantém os termos **Stage selector** e **Commit flow**.
* **Artefatos:** `docs/commit-message-ia.*.md` nos **5 idiomas** e o relatório de tarefa do Gemini.

### **44. Fechamento Automático de Issues (`src/issue_autoclose/`) 🆕**

* **O que era:** a issue criada com `gitpr -is` era órfã — o número existia só dentro da TUI de issue e se perdia no instante em que ela fechava. Todo PR tinha de ser vinculado à mão, e o merge não fechava nada.
* **Pacote de 5 arquivos:** `issue_registry.py` (235 linhas), `register_created_issue.py` (80), `resolve_close_issue.py` (226), `insert_close_line.py` (46) e `__init__.py`. Cada um é uma responsabilidade: persistir, registrar na criação, decidir na próxima execução e inserir no corpo.
* **Registro Local (`IssueRegistry`):** `.gitpr/conf/github.yml` com `schema_version: 1` e um único `last_issue` (last write wins, coerente com um fluxo de um PR por vez). Escrita **atômica** via arquivo irmão + `os.replace`; `load()` devolve `error` em vez de levantar (arquivo corrompido não trava a criação), e `matches_repo()` compara owner/repo sem caixa para nunca fechar a issue do repositório errado.
* **Auto-Ignorando com Precisão:** `record()` roda `git check-ignore` antes da primeira escrita e acrescenta exatamente uma linha `.gitpr/conf/github.yml` ao `.gitignore` quando o arquivo não está coberto — `.gitpr/conf/` **não** é ignorado inteiro, porque `gitpr.config.yml` é versionado de propósito ([ADR-015](docs/plans/ADR-015-project-local-pr-base.md)).
* **Registro na Criação:** `register_created_issue()` só grava no **GitHub** e engole falhas de bookkeeping — um problema de escrita local nunca transforma uma criação bem-sucedida em erro.
* **Decisão (`resolve_close_issue`):** barra cedo por flags, configuração e forge não-GitHub; só depois toca disco/rede. Verifica que a issue ainda está **aberta** e **não é um PR**, apaga registros mortos (404, fechada, número de PR) e pergunta **uma vez**, avisando quando o PR mira uma branch diferente da padrão.
* **Linha Idempotente (`insert_close_line`):** detecta qualquer keyword existente (`close/closes/closed`, `fix/fixes/fixed`, `resolve/resolves/resolved`, com prefixo `owner/repo#N` opcional, case-insensitive) e nunca duplica a linha.
* **CLI:** `--close-issue` e `--no-close-issue` — mutuamente exclusivas, recusadas antes de qualquer prompt ou escrita; `-h` vence o conflito. Entradas em `HELP_MAP`.
* **Fiação no Fluxo de PR:** `_prepare_close_issue` roda **antes** do Stage Selector e reusa o contexto SCM resolvido; `_publish_pr_directly` devolve se a forge realmente publicou; `PrPublishApp.body_published` distingue criar/atualizar de apenas abrir um PR existente. O registro só é limpo depois de uma publicação real (ADR-007).
* **Contrato SCM:** `IssueInfo` (state no vocabulário da forge + `is_pull_request`), `get_issue()`, `get_default_branch()` e `closing_line()` são **defaults concretos** da ABC que levantam `ScmNotSupportedError`; só o GitHub implementa. As outras forges degradam para "feature inativa".
* **Configuração:** `GITPR_ISSUE_AUTOCLOSE` (default `true`, opt-out) e `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` (default `5`, int positivo), expostas na categoria `issue` da TUI; lidas como defaults read-only e **não** semeadas no `~/.gitpr/.env`.
* **Telemetria:** uma linha `issue_autoclose` por decisão (`asked`, `accepted`, `skipped_reason`).
* **Testes:** 5 arquivos em `tests/issue_autoclose/` (**120 cenários**) — round-trip do registro, schema, corrupção, falha de escrita atômica, `.gitignore`, decisão, idempotência da linha, flags, fiação e semântica de `body_published`.
* **Artefatos:** `docs/specs/issue-autoclose/` (**12 arquivos**: spec, entrevista, glossário, prompt e ADRs 001–007), `docs/issue-tui-help.*`, `docs/config-tui.*` e `docs/metricas-telemetria.*` nos **5 idiomas**, README nos 5 idiomas e 12 relatórios de tarefa em `docs/claude-code/reports/feat/issue-autoclose/`.

### **45. Base do PR por Projeto (`src/project_config.py`, `src/ui/pr_base_app.py`) 🆕**

* **O que era:** a branch de destino do PR vivia só no `~/.gitpr/.env` da máquina (`PR_DEFAULT_BASE`) ou era adivinhada por `origin/HEAD`. Um repositório que mira `develop` dependia de cada desenvolvedor configurar a mesma variável, e o erro (PR aberto contra a branch errada) só aparecia na forge.
* **O que é:** `.gitpr/conf/gitpr.config.yml` — arquivo **versionado com o projeto** que carrega a base do PR, editado pela TUI de configuração e validado antes de qualquer commit/push. Um resolvedor único serve CLI e MCP, então todos os pontos de entrada concordam na precedência e nas regras de falha.
* **Resolvedor (`src/project_config.py`, 426 linhas):** `resolve_pull_request_base()` — `--base` → arquivo do projeto → `PR_DEFAULT_BASE` → detecção `origin/HEAD` → `main`. Leitura/escrita YAML preserva chaves alheias; seeding idempotente; listagem de branches; detecção da branch atual; verificação contra o remoto.
* **Falha Antes do PR Nascer:** `BaseBranchError`/`CurrentBranchError`; a base precisa existir em `origin/<branch>` e diferir da branch atual — sem `origin` ou com ref ausente, o fluxo para com dica acionável em vez de abrir um PR fadado.
* **TUI de Configuração:** nova categoria `project` com atributo `store` (`env` vs `project`), `KIND_BRANCH` e três campos: path do arquivo (read-only), branch alvo (editável) e base efetiva com a origem (read-only). A `ConfigApp` grava primeiro os valores de projeto, suporta remoção ao esvaziar, recusa a branch atual e nunca sobrescreve YAML ilegível; a linha da base efetiva é atualizada in-place.
* **Modal de Reparo (`src/ui/pr_base_app.py`, 98 linhas):** quando o alvo é a própria branch atual e a execução é interativa, um modal focado pede a branch substituta e grava no arquivo do projeto. Testado em modo headless (`tests/test_pr_base_app.py`, 12 cenários).
* **CLI:** `--base` passa por `_resolve_pr_target()`; o arquivo é semeado em toda invocação dentro de repositório (exceto ajuda), anunciado só no caminho interativo da raiz; `GITPR_SKIP_PROJECT_CONFIG_SEED` desliga o seed (suite de testes).
* **MCP:** `publish_pull_request` usa o resolvedor compartilhado, devolve envelope de erro para `BaseBranchError` e expõe `warnings` no payload e no catálogo.
* **Efeito Colateral Declarado:** rodar `gitpr` num repositório passa a criar o arquivo na primeira execução. Arquivo existente nunca é sobrescrito; se o `.gitignore` exclui o caminho, um aviso explica que o valor não será versionado.
* **Testes:** `tests/test_project_config.py` (41), `tests/test_project_config_cli.py` (7), `tests/test_pr_base_app.py` (12) + ampliações em `test_config_app.py` (88), `test_config_schema.py` (46), `test_config_store.py` (22), `test_mcp_server.py` (117) e `test_core.py` (49).
* **Artefatos:** [ADR-015](docs/plans/ADR-015-project-local-pr-base.md), `docs/plans/develop_natan/20261030_project_pr_base_plansfacts.md`, `docs/survey/20261030_project_pr_base_surveyfacts.md`, e `docs/config-tui.*`/`docs/install-wizard.*`/`docs/pr-descricao-padrao.*`/`docs/pull-request-publication.*` nos 5 idiomas.

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
| `tests/test_cli_help.py` | 9 🆕 | `-h` antes do subcomando: ajuda renderizada, TUI nunca aberta |
| `tests/test_commit_app.py` | 14 | `CommitApp`: mount, Stage Selector, auto-stage, skip, cancelar, confirmar, sucesso/falha do commit, auto-exit e fluxo headless |
| `tests/test_commit_classifier.py` | 30 | Classificação Conventional Commits + `pr_number_from_merge()` nas 4 forges |
| `tests/test_config_app.py` | 88 | TUI de configuração: montagem, troca de categoria, dirty tracking, F2 bloqueado, Ctrl+R, busca, segredos, store `project` |
| `tests/test_config_cli.py` | 9 | Registro do subcomando `config`, `-h`, import lazy, stdout limpo |
| `tests/test_config_issue_autoclose.py` | 10 🆕 | Getters de configuração e campos do schema de fechamento de issue |
| `tests/test_config_schema.py` | 46 | Cobertura de `DEFAULT_CONFIG`, sem duplicatas, categorias/kinds, `advanced` só em Avançado, seção de skills |
| `tests/test_config_store.py` | 22 | Round-trip no `.env` temporário, comentários e ordem preservados, `remove_config_value()` idempotente |
| `tests/test_config_suggest_reviewers.py` | 8 | Configuração de suggested reviewers (chaves e defaults) |
| `tests/test_config_validation.py` | 40 | Tipos, enums, templates, `validate_ai_key()` com SDK mockado (401 vs. rede vs. ollama) |
| `tests/test_core.py` | 49 | Fluxos principais, git diff, PR generation, timing, staging, coautoria, idioma dos hooks, base do PR |
| `tests/test_diff_failure_cli.py` | 3 | Exit code 1 em falha do git, 0 em diff vazio, fail-open no `--hook` |
| `tests/test_diff_parser.py` | 26 | Parser de diff por linhas/hunks + `summarize_patch()` e `split_patch_sections()` |
| `tests/test_explain_command.py` | 4 | CLI do `explain`: sucesso, chave ausente, diff vazio, ajuda contextual |
| `tests/test_external_linters.py` | 33 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_full_diff_encoding.py` | 1 | Repositório real com arquivo Latin-1: o byte `0xFA` vira `U+FFFD` e o arquivo aparece no diff |
| `tests/test_i18n.py` | 22 ✅ | Paridade entre idiomas, chaves ausentes/órfãs, identidade — **todos verdes** |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação |
| `tests/test_issue_engine.py` | 4 | Draft de issue estruturado |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_linter_presets.py` | 5 | Presets de linter: resolução e re-download forçado |
| `tests/test_main_suggest_reviewers.py` | 8 | Flag `--no-suggest-reviewers` na CLI e no help contextual |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 117 | Ferramentas MCP (18), recursos (19), annotations, patching, CLI direto, offload, contrato da extensão, base do PR |
| `tests/test_mcp_server_e2e.py` | 6 | Servidor MCP real via subprocess + JSON-RPC stdio |
| `tests/test_mentor_cli.py` | 4 ✅ | CLI do `mentor` e opt-in do `--mentor` — **patches em `src.main`, todos verdes** |
| `tests/test_metrics.py` | 164 | **Ledger**: escrita síncrona, exportação idempotente, bundle/merge, versionamento, migração, renderizadores, custo, qualidade, módulos, provedores, ciclo |
| `tests/test_net_timeouts.py` | 12 | Timeouts de rede/IA — alinhados ao default real de 180s |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_policy_cli.py` | 26 | Grupo `policy`: list/show/validate/use/off/install/init, confirmação e lockfile |
| `tests/test_pr_base_app.py` | 12 🆕 | Modal de troca da base do PR: montagem headless, escolha e cancelamento |
| `tests/test_pr_publish_app.py` | 59 | TUI do PR Publisher: telas, fluxos, suggested reviewers, `NoticeScreen`, modal de merge, `body_published` |
| `tests/test_pr_publish_linter_modal.py` | 4 | Modal de erro do linter: abort, no-verify |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_project_config.py` | 41 🆕 | `project_config`: path, YAML, seed, resolvedor de base, validação contra o remoto |
| `tests/test_project_config_cli.py` | 7 🆕 | Fiação da base do projeto na CLI |
| `tests/test_release_cli.py` | 4 | CLI do release: options, help com epilog documentado |
| `tests/test_release_engine.py` | 53 | **Corte ancorado no changelog, `_drop_released()`, links, mapa de PR por merge commit**, publicação |
| `tests/test_reviewer_resolution.py` | 18 | Escada de resolução, rejeição de nome parcial, dedup, tolerância a falha |
| `tests/test_reviewer_suggestion.py` | 18 | Lógica de sugestão de revisores (ranking, exclusão, top-N, `last_commit_hash`) |
| `tests/test_risk_cli.py` | 4 | CLI do `risk`: `--file`, `--format json`, `--base`, `--no-history` |
| `tests/test_security_ruleset.py` | 77 | Matriz do ruleset embutido: regex, placeholders, nível, wildcard, merge, traduções |
| `tests/test_skill_command.py` | 10 | Download e validação de templates de skill |
| `tests/test_skill_context.py` | 20 | `get_skill_context()` com `quiet=True`, fallbacks, guarda do artefato de PR |
| `tests/test_skill_templates.py` | 99 | Varredura parametrizada de **todo template publicado** contra referências embutidas |
| `tests/test_smart_excludes.py` | 15 | Filtro pathspec inteligente e re-download forçado |
| `tests/test_suggest_reviewers.py` | 17 | Suggested reviewers no fluxo de PR (integração, hint `no_login`) |
| `tests/test_tests_command.py` | 4 | CLI do grupo `tests` e do `generate`, `--finding` e epilog com link |
| `tests/test_thinking_words.py` | 5 | Carregamento, parsing com separador `;` e reload forçado |
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
| `tests/badge/test_badge_paths.py` | 10 ✅ | Ponto único de injeção nos dois publicadores — segue verde |
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
| `tests/integration/test_baseline_exit_code_contract.py` | 8 🆕 | Exit code 1 para baseline inaplicável e 2 no `check` |
| `tests/integration/test_policy_effect_on_review_linter_risk.py` | 31 | Efeito real do pack em review, lint e risk (com guarda de rede autouse) |
| `tests/issue_autoclose/test_close_issue_wiring.py` | 26 🆕 | Fiação no fluxo de PR: flags, prompt, publicação real, limpeza do registro |
| `tests/issue_autoclose/test_insert_close_line.py` | 19 🆕 | Inserção idempotente e reconhecimento de keywords de fechamento |
| `tests/issue_autoclose/test_issue_registry.py` | 23 🆕 | Registro local: round-trip, atomicidade, corrupção, `.gitignore`, repo match |
| `tests/issue_autoclose/test_register_created_issue.py` | 12 🆕 | Registro pós-criação: GitHub-only, falhas engolidas, primeira escrita |
| `tests/issue_autoclose/test_resolve_close_issue.py` | 40 🆕 | Árvore de decisão: gates, issue aberta, PR, registros mortos, confirmação |
| `tests/review/test_diff_normalizer.py` | 20 | Newlines, validação de diff, smart-excludes em Python |
| `tests/review/test_diff_source.py` | 12 | `DiffOrigin`/`DiffSource`: proveniência, `cache_scope`, `is_remote` |
| `tests/review/test_remote_pr.py` | 40 | Orquestração: portões, PR, diff, linter, comentário opcional |
| `tests/review/test_review_pr_cli.py` | 25 | CLI `review-pr`: opções, rejeições antes da IA, `--post-comment` |
| `tests/scm/test_azure_devops_provider.py` | 48 | Provider Azure DevOps: org/projeto, PRs, `ScmNotSupportedError` |
| `tests/scm/test_bitbucket_provider.py` | 44 | Provider Bitbucket: Basic auth, workspace, PRs |
| `tests/scm/test_contract.py` | 44 | Contrato `ScmProvider`: assinaturas, dataclasses, erros, defaults de issue |
| `tests/scm/test_factory.py` | 11 | `resolve_scm_provider()` + `detect_provider_from_remote()` |
| `tests/scm/test_github_api_shim.py` | 18 | Shim deprecado `github_api` → delega ao provider |
| `tests/scm/test_github_provider.py` | 86 | Provider GitHub: REST, headers, PRs, issues, releases, read-back de revisores, `get_issue`/`get_default_branch` |
| `tests/scm/test_gitlab_provider.py` | 52 | Provider GitLab: API v4, namespace, cabeçalhos sintetizados e `overflow` |
| `tests/scm/test_init_wizard.py` | 12 | Wizard `--init`: detecção da forge, validação, persistência |
| `tests/scm/test_release_publish.py` | 8 | Publicação de release por forge (GitHub/GitLab) |
| `tests/split/test_apply_split_plan.py` | 11 | O único módulo que muta: staging seletivo, um commit por grupo |
| `tests/split/test_generate_split_plan.py` | 12 | Diff → units → groups → pré-validação de conflito → mensagens |
| `tests/split/test_hunk_grouper.py` | 18 | Prompt, orçamento/trimming, chamada de IA, validação da resposta |
| `tests/split/test_hunk_parser.py` | 18 | `parse_units()`/`build_patch()`: texto ↔ modelo, puro |
| `tests/split/test_selective_stager.py` | 11 | Staging de subconjunto, check contra HEAD, índice limpo |
| `tests/split/test_split_cli.py` | 31 | CLI do split: opções, dry run default, `--apply` |
| `tests/unit/test_version_consistency.py` | 5 🆕 | SSOT da versão: `pyproject.toml`, `CLAUDE.md` e `GEMINI.md` contra `src.updater.__version__` |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (scaffold; nunca executado) |

**Total:** **3276 cenários coletados em 153 módulos de teste** (59 na raiz + 12 em `tests/application/use_cases/` + 10 em `tests/fix/` + 9 em `tests/scm/` + 7 em `tests/badge/` + 6 em `tests/split/` + 6 em `tests/demo/` + 5 em `tests/domain/baseline/` + 5 em `tests/issue_autoclose/` + 4 em `tests/domain/policy/` + 4 em `tests/review/` + 4 em `tests/infrastructure/linter/external/` + 3 em `tests/domain/check/` + 3 em `tests/infrastructure/ci/` + 3 em `tests/integration/` + 2 em `tests/domain/risk/` + 2 em `tests/domain/tests_generation/` + 2 em `tests/infrastructure/git/` + 2 em `tests/domain/linter/` + 1 em `tests/domain/finding/` + 1 em `tests/domain/mentor/` + 1 em `tests/domain/pr/` + 1 em `tests/infrastructure/baseline/` + 1 em `tests/unit/`; **+266 cenários, +12 arquivos** desde o relatório anterior).

**Notas de qualidade desta versão:**
- **⚠️ Execução completa nesta máquina — o cenário que trava:** sem exclusão, o run fica preso em **~33%** (≈1085 cenários) e não termina nem após 16 minutos. A causa é `tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched`: ele chama `gitpr -c --no-unstaged-check` pelo `CliRunner`, e o ramo `commit` de [main.py:1625-1638](src/main.py#L1625-L1638) **abre a `CommitApp` sem checar TTY**, então `app.run()` espera um terminal que não existe. Isolado, o arquivo roda **24 dos 34 cenários** e para no 25º; o cenário sozinho não retorna (processo morto após 45 s). **É a primeira evidência concreta da dívida de guarda de TTY** — não é falha de asserção, é a TUI bloqueando um processo não interativo.
- **Execução completa com esse cenário deselecionado:** **3272 passed, 1 failed, 2 skipped, 1 deselected e 227 subtests passed em 695,38 s (11min35s)**. A conta fecha com os 3276 coletados (3272 + 1 + 2 + 1). A única falha é a já conhecida `test_headless_full_flow` (timeout de 5 s aguardando o Confirm na `CommitMessageScreen`) — o intermitente descrito abaixo.
- **Os módulos verificados isoladamente fecham verdes:** `tests/test_i18n.py` (**22 passed em 1,49 s**), os quatro `tests/infrastructure/linter/external/` (**14 passed em 0,09 s**) e a contagem por arquivo dos testes novos conferida por `--collect-only` (120 em `tests/issue_autoclose/`, 41 em `test_project_config.py`, 12 em `test_pr_base_app.py`, 9 em `test_cli_help.py`, 10 em `test_config_issue_autoclose.py`, 5 em `test_version_consistency.py`, 8 em `test_baseline_exit_code_contract.py`).
- **✅ As 5 falhas herdadas fecharam:** as 3 de i18n (contagem/paridade, chaves faltantes, órfãs) e as 2 de `tests/test_mentor_cli.py` (patch no módulo errado) não existem mais. `tests/test_i18n.py` roda **22 passed em 1,49 s** isoladamente, e o patch do mentor aponta para `src.main.get_git_diff`.
- **✅ A dívida de tradução foi paga, não contornada:** os seis dicionários têm **1698 chaves**; não houve mudança de expectativa de teste, houve tradução de verdade — incluindo as 3 strings do commit TUI que estavam pendentes, o `argparse` do MCP e a `ChatHelpScreen`.
- **⚠️ O teste intermitente do commit continua intermitente:** `test_headless_full_flow` voltou a falhar neste run — `AssertionError: timed out waiting for condition. Current screen: CommitMessageScreen()` após 5 s esperando o botão Confirm. Nenhum commit desta janela endereçou o problema; ele é hoje a **única falha** da suíte.
- **Os cenários novos cobrem exatamente o que mudou:** o pacote `issue_autoclose` tem uma suíte por arquivo; a `project_config` cobre path/YAML/seed/resolvedor; o contrato de exit code do baseline ganhou teste de integração; e o SSOT de versão tem um guarda próprio em `tests/unit/`.
- **`tests/conftest.py` segue hermético:** `GITPR_SHOW_LOGS=false`, `GITPR_SKIP_UPDATE_CHECK=true`, `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false`, `LANG_VERSION` na versão do código e 🆕 `GITPR_SKIP_PROJECT_CONFIG_SEED=true`.
- **Guarda de rede em dois lugares:** `tests/demo/conftest.py` e `tests/integration/conftest.py`.
- **Fixtures de git real:** `tests/fix/git_fixture.py`, `tests/split/git_fixture.py` e `tests/test_full_diff_encoding.py`.
- **A suíte da extensão é separada:** 7 cenários Mocha em `extensions/vscode/src/test/mcp_client.test.ts`, dos quais 1 integra de verdade com o servidor MCP Python por stdio; ela não entra na contagem do pytest.
- **CI roda em Python 3.10 e 3.13** com `fail-fast: false`, e o release tem workflow próprio com Trusted Publishing.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n — dívida paga:** **1698 chaves** em **todos os seis** dicionários (`es.json`, `es_es.json`, `fr.json`, `fr_fr.json`, `pt_br.json`, `pt_pt.json`). O código usa as mesmas chaves: **0 sem tradução** e **0 órfãs**. Era 1620 (×4)/1618 (×2), 11 faltando e 2 órfãs no relatório anterior. ✅
* **🆕 `__lang_version__` subiu para v0.0.38 com conteúdo:** espanhol e francês foram sincronizados com policy packs, baseline, mentor, risk, MCP, base do PR, configuração de projeto e atalhos do chat; o `argparse` do MCP e a `ChatHelpScreen` passaram por `__()`; a renovação OTA agora entrega tradução nova de verdade.
* **Fontes de tradução em lockstep:** uma chave nova precisa existir no código (fonte), em `langs/pt_br.json` (**lista mestra**), nos dicts FR/ES de `scripts/sync_all_langs.py` e nos valores curados de `scripts/fix_mangled_i18n_keys.py`; a asserção `len(CLEAN_KEYS)` segue em 49. 🆕 O extrator de chaves virou **AST** nos dois lados (script e teste), eliminando a divergência de concatenação implícita.
* **Tópicos novos:** **nenhum** nesta janela — os 50 tópicos canônicos se mantêm.
* **🆕 Tópicos atualizados nesta janela:**
  - `docs/issue-tui-help.*` (**5 arquivos**) — documenta o registro da issue criada, o aviso de fechamento e as flags `--close-issue`/`--no-close-issue`.
  - `docs/config-tui.*` (**5 arquivos**) — a categoria `project` (arquivo versionado, base alvo, base efetiva) e a categoria `issue` (`GITPR_ISSUE_AUTOCLOSE*`).
  - `docs/metricas-telemetria.*` (**5 arquivos**) — o comando `issue_autoclose` e o `meta` com `asked`/`accepted`/`skipped_reason`.
  - `docs/review-pr.*` (**5 arquivos agora completos**) — PT-PT, ES e FR foram traduzidos; o tópico deixou de ser parcial.
  - `docs/install-wizard.*`, `docs/pr-descricao-padrao.*` e `docs/pull-request-publication.*` (**5 arquivos cada**) — seed e precedência da base do PR, e o comportamento do MCP.
  - `docs/baseline-suppressions.*` e `docs/check-ci.*` (**5 arquivos cada**) — contrato de exit code do baseline e agregação de risco por `path`/`file_path`.
  - `docs/suggested-reviewers.*` e `docs/scm-multiforge.*` (**5 arquivos cada**) — read-back legado (`None`) e o contrato `list[str]`.
  - `docs/commit-message-ia.*` (**5 arquivos**) — sem mudança de fluxo, apenas sincronização de tradução.
* **`CONTEXT.md` (atualizado):** o glossário do domínio passou de **7 para 22 termos**. Novos: **PR target base**, **Project configuration file**, **Self-target**, **Release workflow**, **Trusted publishing**, **Diff base**, **Embedded security ruleset**, **Read-back**, **Unusable baseline**, **Package version**, **Language asset version**, **Hook script version**, **Issue registry**, **Closing line** e **Close issue decision**.
* **Documentação em 5 idiomas:** **50 tópicos canônicos** em `docs/` (inalterado) — **48 com cobertura completa nos 5 idiomas** e **2 tópicos parciais** (`github-issue-prompt-com-gh`, `version-markers`). O `review-pr` deixou de ser parcial.
* **Novos artefatos de especificação:** `docs/specs/issue-autoclose/` (**12 arquivos** — spec, entrevista, glossário, prompt e ADRs 001–007) e 3 novas ADRs em `docs/adr/` (`0008` secret ruleset, `0009` reviewer read-back, `0014` package version SSOT).
* **Skills locais do Claude Code:** `.claude/skills/` com **29 skills** (contagem inalterada).
* **Memory Index:** `.claude/memory/MEMORY.md` com **40 padrões** (contagem inalterada).
* **Relatórios de tarefas:** `docs/claude-code/reports/develop_natan/` (**116**; **+2** desde o relatório anterior) + 🆕 `docs/claude-code/reports/feat/issue-autoclose/` (**12**) e `docs/gemini/reports/develop_natan/` (**31**; **+12**).
* **Relatórios de status:** `docs/reports/` — este é o **22º relatório** (v0.0.22); o v0.0.21 nunca é sobrescrito.
* **Planos de desenvolvimento:** **152** arquivos em `docs/plans/` (+4) + **12 arquivos em `docs/gemini/plans/`** (+10) + **24 arquivos em `docs/survey/`** (+3).

---

## **🔄 Pipeline de Distribuição**

1. **PyPI (canal único):** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **Atualização obrigatória com janela corrida:** a execução verifica o PyPI no startup e **bloqueia com exit code 1** se houver versão mais nova, imprimindo `pip install --upgrade gitpr-cli`. A resposta fica em cache por **1 hora** e `--update` **sempre** consulta a rede. A comparação é PEP 440: pré-release remoto não bloqueia instalação estável, versão ilegível conta como desconhecida. O gate cobre subcomandos quando há TTY; CI, pipes, hooks, MCP e `-h` seguem isentos.
3. **GitHub Releases:** produção automatizada pelo `release.yml` em tags `v*` — build, validação, Trusted Publishing e criação do release com artefatos.
4. **GitHub Actions:** workflow `pr-review.yml` + `action.yml` (instala via pip) + `tests.yml` (matriz Python 3.10 e 3.13) + `extension.yml` (VSIX; publicação no Marketplace/Open VSX em `ext-v*`) + 🆕 `release.yml` (PyPI + GitHub Release em `v*`). O `action.yml` chama um único passo `gitpr check` — **quebra declarada** para quem usava `--linter` + `--fullreview`.
5. **MCP Server:** entry point `gitpr-mcp` via `pyproject.toml`
6. **Extensão de Editor:** pacote VSIX independente (`natanfiuza.gitpr`), com canais VS Code Marketplace e Open VSX; requer Node.js 20+ apenas para build, não para uso
7. **Templates e idiomas OTA:** `templates/` e `langs/*.json` servidos do GitHub (main) — `__lang_version__` **v0.0.38** 🆕 renova as cópias locais de `~/.gitpr/langs/`; `__scripts_version__` **v0.0.4** renova os hooks
8. **Versão derivada do código:** `pyproject.toml` usa `version = {attr = "src.updater.__version__"}` — o `__version__` é a **única** fonte, agora garantido por [ADR-014](docs/adr/0014-canonical-package-version-ssot.md) e por `tests/unit/test_version_consistency.py`
9. **`package-data` importa:** os quatro packs embutidos (`src/policy_packs/*`) viajam no wheel
10. **⚠️ Estado do release — tagueado, pendente de publicação:** `__version__` é **1.5.0**, a tag `v1.5.0` existe e a seção `[1.5.0]` está no `CHANGELOG.md`, mas **o PyPI ainda serve 1.4.4**. O próximo passo é executar/confirmar o `release.yml` para a tag — até lá, `pip install --upgrade gitpr-cli` não entrega a 1.5.0.

---

## **📈 Evolução desde o Relatório Anterior (v0.0.21)**

| Área | v0.0.21 (anterior) | v0.0.22 (atual) |
|------|-------------------|-----------------|
| **Versão GitPR** | 1.4.4 — tagueada (`v1.4.4`) e **publicada no PyPI** | **1.5.0** — tagueada (`v1.5.0`), seção no changelog, **PyPI ainda em 1.4.4** |
| **Versão Idioma** | v0.0.36 — bump sem alteração de dicionário | **v0.0.38** — dicionários realmente alterados |
| **Versão Scripts Hook** | v0.0.4 | v0.0.4 (inalterada) |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Inalterado |
| **Idiomas** | 5 idiomas, 6 dicionários | Inalterado |
| **Subcomandos** | 15 | 15 (inalterado) — 4 grupos (baseline 6, metrics 8, policy 7, tests 1) |
| **Flags CLI** | 32 opções na raiz | **33** — 🆕 `--close-issue` e `--no-close-issue` |
| **Fechamento de Issue 🆕** | — | Pacote `src/issue_autoclose/` (5 arquivos): registro local, decisão, linha idempotente e fiação no PR |
| **Base do PR 🆕** | `PR_DEFAULT_BASE` da máquina ou `origin/HEAD` | **`.gitpr/conf/gitpr.config.yml` versionado** + `src/project_config.py` + modal de reparo |
| **Camadas** | 9 pacotes de domínio, 15 casos de uso | Inalterado — as duas features novas são orquestração/borda |
| **Ferramentas MCP** | 18 tools / 19 recursos / 7 prompts | Inalterado — `publish_pull_request` ganhou base compartilhada e `warnings` |
| **Variáveis de Ambiente** | 58 no `DEFAULT_CONFIG` + preços/câmbio + 9 `GITPR_CHECK_*` | 58 + preços/câmbio + 9 `GITPR_CHECK_*` + 🆕 3 read-only (`GITPR_ISSUE_AUTOCLOSE`, `GITPR_ISSUE_AUTOCLOSE_TIMEOUT`, `GITPR_SKIP_PROJECT_CONFIG_SEED`) |
| **Schema de Config** | 80 `ConfigField` / 16 categorias | **85 / 17** — categorias `project` e campos de issue, atributo `store` |
| **i18n (chaves por arquivo)** | 1620 × 4 e 1618 × 2 — 1629 no código, 11 sem tradução, 2 órfãs | **1698 × 6 — 0 faltando, 0 órfãs** ✅ |
| **Gate de Atualização** | TTL corrido de 1 h, `-u` sempre online, PEP 440, `bounded_urlopen`, semântica estrita, gate de subcomando em TTY | Inalterado no código |
| **Linter** | Regex + segredos + SAST + `findings_out` + baseline-aware | Inalterado — o **ruleset** de segredos ampliou a cobertura (7 regras, 77 cenários) |
| **Hooks Git** | post-checkout/post-merge/pre-push no ledger | Inalterados — `prepare-commit-msg` segue não-interativo |
| **Camada SCM** | 4 forges, paginação, `web_links.py` | + `IssueInfo`, `get_issue()`, `get_default_branch()`, `closing_line()`; read-back legado documentado |
| **Release engine** | Seções `[1.4.3]`/`[1.4.4]` commitadas; PyPI em 1.4.4 | Seção `[1.5.0]` commitada e traduzida; tag `v1.5.0`; publicação pendente |
| **Documentação** | 50 tópicos (47 completos + 3 parciais) | 50 tópicos (48 completos + 2 parciais) — `review-pr` traduzido nos 5 idiomas |
| **Agenda do domínio** | `CONTEXT.md` com 7 termos | **22 termos** — PR target base, project config file, self-target, issue registry, closing line etc. |
| **CI** | `tests.yml` (3.10 + 3.13) + `action.yml` + `extension.yml` | + 🆕 `release.yml` (Trusted Publishing) |
| **Suíte de Testes** | 3010 cenários (141 arquivos) | **3276 cenários (153 arquivos) — +266 cenários, +12 arquivos** |
| **Falhas conhecidas** | 5 (3 i18n + 2 mentor) + 1 intermitente | **0 das herdadas** (i18n e mentor fechadas); o intermitente do commit segue aberto e **a suíte completa agora trava em `test_a_flow_that_never_enforced_it_is_untouched`** (`-c` sem guarda de TTY) |
| **Dependências** | Sem novas dependências Python | Nenhuma nova — `PyYAML` e `requests` já estavam presentes |
| **Commits desde o relatório** | 3 commits de código + 1 de documentação + 2 merges | **37 commits e 15 merges** (2026-10-30 → 2026-11-04) |
| **PRs mergeados** | 2 PRs (#230, #231) | **15 PRs (#235, #237, #239, #241, #243, #244, #245, #247, #249, #251, #253, #255, #256, #258, #260)** |
| **Memory Index** | 40 padrões | 40 padrões (inalterado) |
| **Relatórios de tarefas** | 114 claude-code, 19 gemini | **116 claude-code (+12 em `feat/issue-autoclose/`), 31 gemini** |
| **Planos de desenvolvimento** | 148 planos, 2 gemini, 21 surveys | **152 planos, 12 gemini, 24 surveys** |

---

## **🚧 Próximos Passos**

* **🆕 Publicar a 1.5.0 no PyPI:** a tag `v1.5.0` existe e o `release.yml` está pronto, mas o pacote servido é 1.4.4. Executar/confirmar o workflow da tag e validar `pip install --upgrade gitpr-cli`; depois conferir que um cliente 1.4.4 passa a bloquear. **É a dívida de release reaberta.**
* **🆕 Estabilizar `test_headless_full_flow`:** o clique em `#btn_confirm` chega antes de o layout do `CommitMessageScreen` estabilizar e o teste morre no timeout de 5 s. Esperar o botão ficar **clicável** (ou trocar o clique por `screen.dismiss("confirm")`) remove a única falha intermitente da suíte. **Item herdado, sem mudança nesta janela.**
* **🆕 Proteger o `-c` de execução não interativa — agora com evidência:** o roteamento continua sem guarda de TTY — sem `--hook`, `gitpr -c` **sempre** abre a `CommitApp` ([main.py:1625-1638](src/main.py#L1625-L1638)), inclusive em scripts e CI. Nesta janela o custo deixou de ser hipotético: `test_a_flow_that_never_enforced_it_is_untouched` chama `gitpr -c` pelo `CliRunner` e **`app.run()` nunca retorna**, travando a execução completa da suíte em ~33%. Reaproveitar `_may_ask_the_user()` (ou exigir `--hook`) conserta o comportamento e destrava o teste de uma vez. **Item herdado, ainda aberto — e é a prioridade de estabilidade da suíte.**
* **🆕 Cobrir o fechamento de issue nas outras forges:** a feature é GitHub-only por design (`get_issue`/`get_default_branch`/`closing_line` levantam `ScmNotSupportedError`). GitLab (`Closes #N`), Bitbucket e Azure precisam de implementação própria antes de a feature ser multi-forge.
* **🆕 Documentar o novo arquivo versionado como mudança de fluxo:** `.gitpr/conf/gitpr.config.yml` nasce na primeira execução dentro de um repositório. Quem roda GitPR em CI ou em monorepos precisa saber que o arquivo será criado e que `GITPR_SKIP_PROJECT_CONFIG_SEED` o desliga — a documentação de config cobre a feature, mas não a nota de migração.
* **Corrigir o isolamento de `tests/test_mentor_cli.py`:** ✅ **concluído** — o patch passou a apontar para `src.main.get_git_diff`.
* **Fechar o débito de i18n:** ✅ **concluído** — 1698 chaves nos seis dicionários, `tests/test_i18n.py` 22/22.
* **Estender a cobertura do ruleset de segredos:** ✅ **concluído** — `ASIA…`, `github_pat_…`, `xoxc/xoxd`, atribuição sem aspas e fronteira à esquerda.
* **Traduzir `docs/review-pr.*.md`:** ✅ **concluído** — 5 idiomas completos.
* **Destrackear os artefatos de `.gitpr/metrics/export/`:** ✅ **concluído** — 0 arquivos rastreados.
* **Documentar a quebra de contrato do `request_pull_request_reviewers`:** ✅ **concluído** — ADR-0009 + docs de revisores/SCM.
* **Mapear o blast radius do baseline no exit code:** ✅ **coberto** — `tests/integration/test_baseline_exit_code_contract.py` (8 cenários) e docs atualizadas.
* **Reconciliar a versão do projeto:** ✅ **concluído** — `CLAUDE.md`/`GEMINI.md` em 1.5.0, ADR-014 e teste de consistência.
* **`gitpr -h config` ignora o `-h`:** ✅ **concluído** — `-h` antes do subcomando renderiza a ajuda e não abre a TUI.
* **Migrar o extrator do `sync_i18n.py` para AST:** ✅ **concluído** — regex substituído, 21 falsos negativos eliminados.
* **Documentar a mudança de semântica do `GITPR_SKIP_UPDATE_CHECK` como nota de migração:** o `docs/tutorial/install-from-source` já descreve o parser estrito, mas automações que setavam `=false` esperando silenciar a checagem passam a vê-la rodar. **Item herdado, ainda aberto.**
* **Documentar a quebra de comportamento do `-c` interativo como nota de migração:** o `commit-message-ia` descreve o fluxo novo, mas não diz explicitamente "antes era silencioso; em CI use `--hook`". **Item herdado, ainda aberto.**
* **Seção Smart Exclude na TUI:** os campos `GITPR_SMART_EXCLUDES_*` seguem sob `diff`, sem categoria própria. **Item herdado, ainda aberto.**
* **Dívidas registradas no plano do config TUI:** `DEFAULT_CONFIG` ficou redundante com o schema; o banner de abertura não lista `--init`, `--base` nem `--plugins`; o `LinterApp` é o **único** app Textual que ainda não desabilita a command palette; e as **9 `GITPR_CHECK_*`** ainda **não** têm categoria no schema. **Item herdado, ainda aberto.**
* **Criar uma nota de migração para o `action.yml`:** a troca de `--linter` + `--fullreview` por `gitpr check` é quebra de contrato para workflows existentes. **Item herdado, ainda aberto.**
* **Publicar a extensão nos marketplaces:** o workflow está pronto, mas depende de `VSCE_PAT`/`OVSX_PAT`; até lá, a instalação é por VSIX local. **Item herdado, ainda aberto.**
* **Revisar o `git diff` em repositórios com arquivos binários grandes:** bytes binários chegam ao modelo como sequência de `U+FFFD`; vale confirmar que os smart excludes cobrem os casos reais. **Item herdado, ainda aberto.**
* **Acompanhar o fallback ES/FR no site:** os links dos READMEs já usam `?lang=es` e `?lang=fr`, mas o site ainda pode servir inglês. **Item herdado, ainda aberto.**
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Histogramas de tempo e tendências de tokens na TUI de métricas.
* **Seed de `.gitpr/conf/` local:** o seed do smart-excludes e do linter continua pendente como subcomando próprio ou etapa do wizard — o `gitpr.config.yml` agora cobre só a base do PR.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.

### ✅ Concluídos nesta janela (2026-10-30 → 2026-11-04)

* ~~**Toda issue criada com `gitpr -is` virava órfã**~~ 🆕 — PR #260 (`4c2bede`): registro local, `get_issue`/`get_default_branch`/`closing_line`, linha `close #N` idempotente, flags `--close-issue`/`--no-close-issue` e métrica `issue_autoclose`. **120 cenários novos.**
* ~~**A base do PR só existia no `.env` da máquina**~~ 🆕 — PR #235 (`2eff88b`): `.gitpr/conf/gitpr.config.yml` versionado, resolvedor único, validação contra `origin` e modal `PrBaseApp` ([ADR-015](docs/plans/ADR-015-project-local-pr-base.md)).
* ~~**A dívida de i18n (11 chaves faltando, 2 órfãs, 3 testes vermelhos)**~~ — PR #237 (`96526b9`): espanhol e francês sincronizados, MCP e chat localizados, guarda de identidade, `__lang_version__` v0.0.37; fechada de vez em 1698 chaves. **`test_i18n.py` 22/22.**
* ~~**As 2 falhas antigas de `test_mentor_cli.py`**~~ — PR #239 (`90fd76c`): patch movido para `src.main.get_git_diff`.
* ~~**O release era manual**~~ — PR #241 (`d401931`): `release.yml` com testes, verificação tag/versão, build, `twine check`, Trusted Publishing e GitHub Release.
* ~~**Lacunas do ruleset de segredos**~~ — PR #243 (`9dd149a`): `ASIA…`, `github_pat_…`, `xoxc/xoxd`, atribuição sem aspas, fronteira à esquerda e filtros de runtime.
* ~~**`gitpr -h config` abria a TUI**~~ — PR #253 (`ce52558`): `-h` antes do subcomando renderiza a ajuda.
* ~~**Risk report degradava em silêncio com `file_path`**~~ — PR #249 (`3e6f97a`): agregação tolerante e contrato de exit code do baseline coberto.
* ~~**A versão podia divergir entre `pyproject.toml`, `CLAUDE.md` e `GEMINI.md`**~~ — PR #251 (`ed7e888`): SSOT em `src/updater.__version__` ([ADR-014](docs/adr/0014-canonical-package-version-ssot.md)) e teste de consistência.
* ~~**O extrator de i18n truncava concatenação implícita**~~ — PR #255 (`694a640`): AST no script e no teste.
* ~~**O contrato do read-back de revisores não estava documentado**~~ — PR #247 (`149fb49`): `(no read-back)` + [ADR-0009](docs/adr/0009-reviewer-attach-returns-read-back.md).
* ~~**`review-pr` só tinha 2 dos 5 idiomas**~~ — PR #244 (`8cdd1fc`): PT-PT, ES e FR traduzidos.
* ~~**34 artefatos de métricas continuavam rastreados**~~ — PR #245 (`e4f455b`): `git rm --cached` aplicado.
* ~~**A 1.4.4 estava publicada mas o release ainda era manual**~~ — a 1.4.4 continua no PyPI e o pipeline de release agora é automatizado; a 1.5.0 é o primeiro candidato a passar por ele.

---

**Relatório gerado em:** 2026-11-04  
**Branch:** `main`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
