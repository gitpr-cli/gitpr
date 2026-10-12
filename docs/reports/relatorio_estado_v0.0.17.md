# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.17 (2026-10-12)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.17):**
- **O release 1.3.0 foi fechado e o 1.4.0 já está tagueado:** a tag `v1.3.0` (merge do PR #193, 2026-09-24) encerrou o item que bloqueava duas janelas, e o `CHANGELOG.md` foi completado com as seis features que faltavam. Dez dias depois a tag `v1.4.0` (merge do PR #207, 2026-10-12) fechou esta janela inteira — as cinco features abaixo **mais** a nota de release do 1.3.0 caberam num único ciclo.
- **`gitpr release` deixou de repetir o histórico:** as notas de release listavam, a cada versão, todos os commits de todas as versões anteriores (a seção 1.3.0 saiu com 124 bullets, 115 deles repetição da 1.2.0). A causa não era a IA — era o range do `git log`, ancorado em `git describe`, que neste repositório resolvia para `v0.0.8`. O corte passou a ser a **seção anterior do próprio changelog**, cada bullet ganhou **link real e clicável** de commit, PR e contribuidor, e um commit que já está em outra seção é descartado antes de virar bullet — quando nada sobra, o release **aborta** em vez de publicar uma seção vazia.
- **A telemetria saiu do arquivo JSON e virou um ledger SQLite:** eventos eram gravados em arquivos por comando, a partir de uma thread daemon, e depois "enriquecidos" de volta pelo cache de IA através de um casamento heurístico por (repo, branch, ação, minuto) que dependia de três mapas de pastas divergentes. O resultado era previsível: `tokens_actual` **sempre zero** e perda de dados entre repositórios na exportação. O `~/.gitpr/metrics/telemetry.db` grava a linha **de forma síncrona**, com os tokens copiados dos metadados do provedor no momento da escrita, e um processo curto (um hook, por exemplo) deixou de perder a própria linha ao sair.
- **Mentor Mode — o review que ensina, não só aponta:** um review diz *o que* está errado e quase nunca *por que aquilo importa*. O `gitpr mentor` (e a flag `--mentor` em `-r`/`-f`) enriquece os achados do último review com o que está acontecendo, por que importa, uma analogia do dia a dia e os conceitos a estudar. É **opt-in** e nunca inventa: sem evidência suficiente, a explicação diz isso em vez de preencher o vazio.
- **Score de risco determinístico — sem IA, sem cota:** `gitpr risk` produz um score 0–100 com nível `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` a partir de sinais locais (caminhos críticos, testes ausentes, migrations, histórico de bugs e reverts, achados estáticos). A fórmula é declarada (**50/30/20**), as regras de elevação obrigatória também, e o score entra no prompt do review como contexto **read-only** e no relatório. Um número explicável vale mais que um palpite caro.
- **Policy Packs — a política do repositório virou artefato versionado:** skills, regras de linter, severidades, caminhos críticos, pesos de risco e convenções de PR/commit andavam espalhados e cada repositório os configurava à mão. O `gitpr policy` adota um pack YAML versionado com **checksum**, resolve a precedência entre camadas e grava a escolha no lockfile que o time commita. Quatro packs embutidos entram no wheel; sem pack ativo, **nada muda**.
- **Baseline e supressões auditáveis — o ruído conhecido para de bloquear:** linters e reviews re-reportavam os mesmos achados pré-existentes a cada execução, e cabia ao revisor diferenciar a saída na cabeça. O `.gitpr/baseline.json` grava a fotografia dos achados aceitos, cada achado novo é classificado como `new`/`existing`/`resolved`/`ignored`/`accepted_debt`, e **só o `new` bloqueia**. Toda supressão carrega motivo; dívida aceita carrega dono e, se houver, prazo.
- **O modelo de achado virou tipo canônico:** `NormalizedFinding` saiu de `infrastructure/linter/external/base_bridge.py` para `src/domain/finding/`. Sem isso, cada bridge — Semgrep, Gitleaks, Bandit, o ruleset regex — fingerprintaria uma forma diferente do mesmo achado e o baseline não teria como reconhecê-lo.
- **A dívida da janela anterior foi fechada:** `SKILL_LABELS` e `mcp_server.SKILL_FILES` receberam `tests`, `explain` e agora `mentor`; as **40 chaves `__()`** que não existiam em nenhum dicionário foram traduzidas; e as **4 falhas** da janela anterior não existem mais. As três asserções que acusaram a dívida continuam rodando — elas só pararam de acusar. A suíte, medida de ponta a ponta nesta janela, fecha em **2795 aprovados de 2799** — as duas falhas restantes são um bug de isolamento em `tests/test_mentor_cli.py`, não regressão do produto (ver §Testes).
- **Cobertura de i18n fechou o ciclo:** **1603 chaves** em cada um dos 6 dicionários (+445 nesta janela) e **zero chaves usadas no código sem tradução** — o código usa 1603, os dicionários têm 1603.
- **As traduções pendentes foram pagas:** `split-command` e `otimizacao-de-tokens` completaram os 5 idiomas; `review-pr` segue com 2. Duas famílias PT-only (`como_reverter_commit_git_localmente`, `testar_sem_usar_pypi`) saíram do topo de `docs/` para `docs/extra/`.

- **Versão atual:** 1.4.0 (**tagueada** — `v1.4.0`, merge do PR #207, 2026-10-12; `v1.3.0` em 2026-09-24)
- **Versão dos dicionários de idioma:** v0.0.34 (cadeia v0.0.32 → v0.0.33 → v0.0.34 nesta janela)
- **Versão dos scripts de hook:** v0.0.4 (v0.0.3 → v0.0.4 nesta janela)
- **Publicação:** PyPI (`pip install gitpr-cli`) — canal binário removido
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal) — **14 subcomandos** 🆕 (`badge`, **`baseline`** 🆕, `config`, `demo`, `explain`, `fix`, **`mentor`** 🆕, **`metrics`** 🆕, **`policy`** 🆕, `release`, `review-pr`, **`risk`** 🆕, `split`, `tests`). Quatro deles são **grupos**: `baseline` (6 subcomandos), `metrics` (8), `policy` (7) e `tests` (1).
* **UI/Terminal:** Textual — TUI para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher, erros do linter (`LinterApp`), configuração (`ConfigApp`), modal `NoticeScreen`, o **tour do `gitpr demo`** (`src/ui/demo/`) e o **assistente de migração do ledger** (`src/ui/metrics_migration_app.py`) 🆕.
* **Arquitetura em Camadas:** `src/domain/` (regra pura, sem I/O) + `src/application/use_cases/` (orquestração, **14 casos de uso** 🆕) + apresentação (CLI/TUI). **8 pacotes de domínio** 🆕: `baseline`, `finding`, `linter`, `mentor`, `policy`, `pr`, `risk`, `tests_generation`.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API, tokens GitHub e tokens SCM das forges.
* **Configuração:** `python-dotenv`, `pyyaml` (linter estático) + schema declarativo próprio (`src/config_schema.py`, **80 `ConfigField`** e **16 categorias** 🆕).
* **IA Providers:** Integração via SDK oficial do Google GenAI, OpenAI SDK (DeepSeek) e OpenAI SDK (Ollama local). Defaults configurados: `gemini-pro-latest` / `gemini-flash-lite-latest` e `deepseek-v4-pro` / `deepseek-v4-flash`.
* **Forge APIs:** `requests` (REST) — abstração multi-forge em `src/infrastructure/scm/` (GitHub, GitLab, Bitbucket, Azure DevOps) + **`web_links.py`** 🆕 (URLs de commit, PR e perfil por forge, funções puras); `src/github_api.py` mantido como shim deprecado.
* **Linter / SAST:** regex YAML + bridge Checkstyle + ruleset de segredos embutido (`src/security_ruleset.py`) + 4 bridges em `src/infrastructure/linter/external/` (base + Semgrep, Gitleaks, Bandit), com modelo normalizado em `src/domain/linter/sast_finding_mapper.py`. 🆕 O achado normalizado passou a viver em **`src/domain/finding/`** e há um **side channel `findings_out`** que expõe os achados estruturados ao lado das strings de alerta.
* **Git Internals:** `src/infrastructure/git/` — `patch_applier.py`, `selective_stager.py`, **`identity.py`** 🆕 (rótulo de repo, branch e autor numa única chamada de git), **`risk_history_reader.py`** 🆕 e **`test_matcher.py`** 🆕.
* **Persistência local 🆕:** `src/ledger.py` — SQLite (`~/.gitpr/metrics/telemetry.db`) com WAL, `PRAGMA user_version`, chaves UUID e transporte por bundle.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 — **16 ferramentas anotadas** 🆕, **19 recursos** 🆕, 7 prompts.
* **Testes:** Pytest + `unittest.mock` (**129 módulos de teste** 🆕 — 49 na raiz, 11 em `tests/application/use_cases/`, 10 em `tests/fix/`, 9 em `tests/scm/`, 7 em `tests/badge/`, 6 em `tests/demo/`, 6 em `tests/split/`, 5 em `tests/domain/baseline/`, 4 em `tests/domain/policy/`, 4 em `tests/review/`, 4 em `tests/infrastructure/linter/external/`, 2 em `tests/domain/risk/`, 2 em `tests/domain/tests_generation/`, 2 em `tests/integration/`, 2 em `tests/infrastructure/git/`, 1 em `tests/domain/finding/`, 1 em `tests/domain/mentor/`, 1 em `tests/domain/pr/`, 2 em `tests/domain/linter/`, 1 em `tests/infrastructure/baseline/` —, **2799 cenários coletados**) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio) + fixtures de repositório git real (`tests/fix/`, `tests/split/`) + **guarda de isolamento de rede** (`tests/demo/conftest.py`, `tests/integration/conftest.py`).
* **Empacotamento:** setuptools/build (PyPI) — `version = {attr = "src.updater.__version__"}`; **packs embutidos via `package-data`** 🆕 e nova dependência **`packaging>=23.0`** 🆕.
* **CI/CD:** GitHub Actions — `pr-review.yml` + `action.yml` + `tests.yml` (matriz Python 3.10/3.13).

---

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa ~90k tokens, divide automaticamente em lotes por arquivo (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce). Suporta PRs, commits e Issues. 🆕 O `provider`/`model` passaram a ser **agregados entre os chunks** e o `meta`/`modules` são repassados a `log_command_metric`, que passou a copiar tokens reais dos metadados do provedor no momento da escrita.
* **Tokenizador Local:** `tokenizer.json` para estimativa precisa de tokens antes do envio para a IA.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()` com fallback para tokenizador local.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff` para reduzir contexto inútil.
* **`get_split_diff()`:** Diff próprio do `split`, com `SPLIT_DIFF_ARGS` (`--binary -M -U3`), **deliberadamente sem** reusar `get_git_diff()` — o `-w` (ignora whitespace) e os smart-excludes quebrariam a garantia de árvore byte-idêntica.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo (system instruction + prompt) em JSON antes de cada chamada à IA.
* **Smart Excludes com Duas Camadas:** Camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`), mescladas em runtime. Auto-seeding do arquivo local na primeira execução. `_load_smart_excludes()` aceita `force=`.
* **Métricas com Rastreamento de Tempo:** `log_command_metric()` em todos os fluxos, agora com `meta`, `modules` e `duration_ms`. 🆕 Duas cópias divergentes do mapa comando→pasta de cache foram **removidas** daqui — eram a causa de `tokens_actual` ser sempre `0`.
* **Resolução Centralizada de Output:** `resolve_output_path()` — default em `.gitpr/reports/{type}/`.
* **Wizard SCM (`run_scm_init_wizard()`)**: `gitpr --init` — detecta a forge pelo remote origin, solicita extras por forge, valida o token e persiste **somente em sucesso**; anuncia o selo automático no caminho de PR.
* **Skill Template de Release (`ensure_release_skill_template()`)**: Baixa `templates/gitpr.release.*.md` no primeiro uso de `gitpr release`.
* **Registro de Skills Compartilhado:** `SKILL_FILES_BY_TYPE` / `SKILL_TYPES` / `DEFAULT_SKILL_TYPE` em `src/config.py`. 🆕 Ganhou a entrada de **`mentor`** (`.gitpr.mentor.md`) — `tests` e `explain` já estavam lá em `tests/test_skill_context.py`.
* **Motor de Review com Escopo de Cache (`generate_pr_content`):** `cache_scope` (anexado **só à chave de cache**) e `store_diff` (grava o diff revisado). 🆕 O `cache_scope` passou a carregar também o **pack de política ativo**, para que dois repositórios sob políticas diferentes não compartilhem uma resposta.
* **Trailer de Coautoria:** `COAUTHOR_TRAILER` + `append_coauthor_trailer()` — idempotente, preserva trailers de terceiros.
* **Subprocessos Blindados:** `stdin=subprocess.DEVNULL` + `encoding='utf-8'`/`errors='replace'` em todos os `subprocess.run`; verificação de conexão via socket `8.8.8.8:53` antes de operações de rede.

### **2. Sistema de Plugins Global (`src/plugins.py`)**

* **Arquitetura de Plugins:** Carrega plugins de `~/.gitpr/plugins/` aplicando-se a **todos os projetos**.
* **Plugins de Linter (`linter/`):** Arquivos `.yml` mesclados com o `.gitpr.linter.yml` local.
* **Plugins de Prompt MCP (`prompts/`):** Arquivos `.md` que estendem o contexto do sistema.
* **Factory Closures:** `get_linter_plugins` e `get_prompt_plugins` isolam estado entre sessões.
* **Comando `--plugins`:** Lista todos os plugins globais instalados com tipos e paths.
* **Documentação Multilíngue:** `docs/plugins-system.md` em 5 idiomas.
* 🆕 **Relação com os Policy Packs:** o pack é uma **terceira** camada de regras — plugins são da máquina, o `.gitpr.linter.yml` é do projeto e o pack é versionado e commitado. `load_linter_rules()` mescla as três em ordem declarada, com as severidades do pack por cima.

### **3. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria `~/.gitpr/` e solicita interativamente chaves, preferências e idioma. A dica de primeira execução aponta para `gitpr demo`.
* **Routing de Comandos:** Gerencia todas as flags e os **14 subcomandos** — `release`, `config`, `fix`, `review-pr`, `demo`, `badge`, `split`, `tests`, `explain`, **`mentor`** 🆕, **`metrics`** 🆕, **`policy`** 🆕, **`risk`** 🆕 e **`baseline`** 🆕.
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags (agora 32 opções Click na raiz — 5 saíram, 1 entrou nesta janela):**
  * **Saíram 🆕:** `--metrics`, `--export`, `--purge`, `--hook-event` e `--dashboard` — viraram o grupo `gitpr metrics` (ver §36). **Quebra de CLI declarada.**
  * **`--mentor` 🆕:** Anexa a seção didática de Mentor à revisão de código (`-r` / `-f`).
  * `--explain`, `--init`, `--no-suggest-reviewers`, `--no-publish`, `--no-edit`, `--base <branch>`, `--plugins`, `--status`, `--no-unstaged-check`, `--linter-setup`, `--version` — inalteradas.
* **Grupo `baseline` 🆕 — 6 subcomandos:** `create` (`--refresh`, `--base`, `--yes`, `--format`), `show` (`--status`, `--rule`, `--file`, `--format`), `validate` (`--format`), `update` (`--recompute`, `--base`, `--yes`), `suppress` (`--reason`, `--scope`, `--debt`, `--owner`, `--due-date`, `--yes`) e `unsuppress` (`--yes`).
* **Grupo `policy` 🆕 — 7 subcomandos:** `list`, `show`, `validate`, `use`, `off`, `install` (`--force`, `--yes`) e `init` (`--stack`, `--yes`).
* **Grupo `metrics` 🆕 — 8 subcomandos:** `export`, `bundle`, `merge`, `dashboard`, `migrate`, `prune`, `purge` e o oculto `hook-event`; os de leitura compartilham `--days`/`--since`/`--until`.
* **Subcomando `risk` 🆕 — 4 opções:** `--file`, `--format text|json`, `--base`, `--no-history`.
* **Subcomando `mentor` 🆕 — 2 opções:** `--finding`, `--provider`.
* **Variáveis de Ambiente (58 chaves no `DEFAULT_CONFIG`, +9 nesta janela):** as quatro `GITPR_BASELINE_*` (`ENABLED`, `PATH`, `REQUIRE_LOCKFILE_CHECKSUM_MATCH`, `ALLOW_LOCAL_OVERRIDES`), as duas de mentor (`GITPR_REVIEW_MENTOR_MODE`, `GITPR_MENTOR_INCLUDE_ANALOGY`), as duas de policy (`GITPR_POLICY_ENABLED`, `GITPR_POLICY_CONTEXT_MAX_CHARACTERS`) e `GITPR_RISK_INCLUDE_IN_REVIEW`. **Fora do `DEFAULT_CONFIG`:** `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT` e `GITPR_METRICS_CURRENCY`, lidas por `get_model_price()`.
* **Ajuda Contextual:** `-h --flag` exibe documentação específica com link language-aware; subcomandos têm `epilog=` próprio (parágrafo `\b` do Click). 🆕 `risk`, `policy`, `baseline` e `mentor` entraram em `HELP_MAP`/`HELP_PRIORITY`.
* **Camada de escrita do `.env`:** `read_env_file_values()` lê **só o arquivo** via `dotenv_values`; `save_config_values()` com `set_key`; `remove_config_value()` com `unset_key`. `validate_ai_key()` distingue credencial recusada (`401`/`403`) de rede inalcançável.
* **Portão de Baseline no Fluxo 🆕:** `main.py` resolve o gate de baseline antes de lint, review, full review, auditoria de arquivo, review remoto e risk, e o **exit code do lint passou a seguir o bloqueio baseline-aware** — achado novo falha, achado conhecido não.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI para revisar, editar e publicar Pull Requests direto no terminal.
* **7 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen` e `NoticeScreen`.
* **Selo no Corpo do PR:** `attach_pr_badge()` roda em `src/main.py` logo após `pr_data` estar completo — **ponto único de injeção**. Append idempotente por marcador e divulgação explícita no `--no-edit`.
* **`_attach_reviewers` com resolução:** Resolve o que o usuário digitou **antes** de enviar, reporta o descartado e, num `422` de lote, **repete um a um**.
* **Suggested Reviewers:** Consulta a forge por revisores sugeridos; `_reviewer_suggestion_view()` monta `resolutions` via `resolve_candidates` e pré-preenche `handles`.
* **Bindings:** F1 (Help), F2 (Salvar .md local), F3 (Publicar via forge), Esc (Sair).
* **Fluxo de Auto-Commit:** Linter → mensagem IA → confirma → commita → push → publica PR. 🆕 O resultado do linter agora carrega os **achados estruturados** (`findings_out`), que é o que o baseline classifica antes de o relatório ser composto.
* **Tratamento de PR Existente / Auto-Upstream / Merge Flow** — inalterados (`GITPR_AUTO_MERGE`).

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Shim Deprecado:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` e demais funções delegam a `src/infrastructure/scm/github_provider.py`; emite `DeprecationWarning` e mantém as tuplas legadas `(ok, data, status)` — nenhum código novo pode importá-lo.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no diff sem gastar cotas de IA.
* **Regras YAML:** Lê `.gitpr.linter.yml` (criado via `--skill`).
* **Plugins de Linter:** Regras adicionais de `~/.gitpr/plugins/linter/*.yml`.
* **Wildcard de Extensão:** `extensions: ["*"]` significa **todo** arquivo, inclusive os sem sufixo e dotfiles.
* **Ruleset de Segredos Embutido:** `load_linter_rules()` mescla `src/security_ruleset.py` **depois** das regras do projeto e dos plugins. Sete regras, todas `extensions: ["*"]`: cinco `error` e duas `warning`. O alerta **nunca ecoa o valor** — a mensagem carrega só `{file_name}` e `{line_number}`.
* 🆕 **Camada de Policy Pack:** `load_linter_rules()` passou a aplicar o merge em camadas do pack ativo e a **sobrescrever severidades**, sem tocar no `.gitpr.linter.yml` nem nos plugins.
* 🆕 **Achados Estruturados (`findings_out`):** além das strings de alerta, o motor devolve os achados normalizados do tipo canônico `src/domain/finding/` — é essa lista que o baseline fingerprinta. Inclui a correção do contador de linhas do lado novo, para que linhas de contexto avancem corretamente.
* **Bridges SAST Opt-In:** Semgrep, Gitleaks e Bandit rodam no caminho de arquivo inteiro **e** no de diff, com dedup `[Gitleaks + Regex]`, mascaramento de valor (`AKIA****`) e aviso quando a ferramenta está habilitada mas fora do `PATH`.
* **`skip_external`:** `parse_diff_and_lint(..., skip_external=True)` no fluxo remoto, porque o bridge roda binários contra arquivos em disco — a árvore local, não o PR.
* **Relatório Consolidado:** `generate_linter_report_content()` consolida erros regex + externos em `.gitpr/reports/linter/` — gerado apenas quando há violações.
* 🆕 **Baseline-aware:** os alertas são anotados com o status do baseline antes de virarem relatório, e o exit code do fluxo de lint segue o bloqueio baseline-aware.

### **7. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera a chave mestra `secret.key` em `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data`/`decrypt_data` para chaves de IA, GitHub PAT e tokens SCM das forges.
* **Validação Multi-Forge:** `validate_or_request_scm_token(provider, repo_display)` — 401 → loop de reautenticação preservando o rascunho.
* **Segredos na TUI de Configuração:** Campos `KIND_SECRET` são editados mascarados, **nunca** exibem o valor em claro e são cifrados com Fernet antes de gravar.
* **Varredura de Segredos no Fluxo:** O linter — que roda no pre-commit hook — é um portão de credenciais com regras idênticas em toda máquina.
* ⚠️ **Lacunas de cobertura confirmadas como ainda abertas nesta janela:** a regra genérica ainda exige aspas após o separador (`\s*[:=]\s*['\"]`), então o formato `.env` **sem aspas** (`API_KEY=abc123`) continua não sendo pego; os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-` continuam fora (o padrão é `gh[pousr]_` e `xox[baprs]-`); e não há fronteira à esquerda no nome da chave, então `mytoken` casa igual a `token`.

### **8. Auto-Updater (`src/updater.py`)**

* **PyPI como Fonte Única:** `get_latest_remote_version()` consulta `https://pypi.org/pypi/gitpr-cli/json` e grava o cache diário **sem** o campo `download_url`.
* **Portão Obrigatório (`enforce_update_required()`):** Devolve `True` (após imprimir as duas versões e o comando pip) quando a versão publicada é mais nova; `False` quando está atualizado, quando a versão remota é **desconhecida (offline)** ou quando a checagem está desligada.
* **`check_and_update()`:** Só consulta e **informa**, nunca instala.
* **Escape Hatch:** `GITPR_SKIP_UPDATE_CHECK` — não é advertised; existe para a suíte e automação offline.
* **Versionamento Centralizado:** `__version__` (**1.4.0** 🆕), `__lang_version__` (**v0.0.34** 🆕 — cadeia v0.0.31 → **v0.0.32** (release notes) → **v0.0.33** (mentor) → **v0.0.34** (bump de release)), `__scripts_version__` (**v0.0.4** 🆕), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`.
* 🆕 **Nesta janela os três bumpes saíram do working tree e viraram commit:** o `af35270` subiu GitPR, idiomas e scripts juntos, e o `CHANGELOG.md` deixou de anunciar uma versão que o pacote não construía.
* ⚠️ **Correção pendente no working tree:** os cabeçalhos de seção do `[1.4.0]` saíram localizados (`Funcionalidades`, `Documentação`, `Tarefas`, `Contribuidores`) e foram corrigidos para o inglês **sem commit** — é a única alteração em aberto no repositório hoje.

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
* **Arquivos Versionados:** `__lang_version__` (**v0.0.34**) controla a atualização dos pacotes (`langs/*.json`).
* **Cobertura:** **1603 chaves** em cada um dos 6 arquivos — paridade total de key sets **e cobertura total do código**: o código usa **1603** chaves e **nenhuma** fica sem tradução (+445 nesta janela; a dívida de 40 chaves da janela anterior foi fechada). ✅
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
* 🆕 **Chamadas com `quiet`:** o release e as features novas encaminham `quiet` até a camada de IA, para que o spinner nunca corrompa uma saída `--format json`.
* 🆕 **Uma chamada por vez, com cache:** mentor e explain reusam o cache MD5 por prompt — rodar de novo sobre um review inalterado não custa nada.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt, com indexação por idioma.
* **Seleção do Último Review (`resolve_last_review()`):** Escolhe o registro `review`/`fullreview` **mais novo** para um par repo+branch — é a porta de entrada do `gitpr fix` e, agora, também do `gitpr mentor`.
* **Diff Revisado (`reviewed_diff`):** Campo no topo do registro que guarda o diff efetivamente revisado, preferido por `fix/apply_fix.reviewed_diff()`.
* **Telemetria e Duração:** Persistência de `duration_ms` e `meta_raw`.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` foi **rebaixada a ponte de pré-migração** — o dashboard lê o ledger, e o scan só existe para reconstruir a série a partir do cache quando o usuário escolhe isso no assistente de migração.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`) e Arqueologia por Blame (`-b`).
* **Publicação Multi-Forge:** F3 cria a issue na forge **configurada** (`GITPR_SCM_PROVIDER`) via `provider.create_issue` — Azure DevOps levanta `ScmNotSupportedError`.
* **Map-Reduce para Issues:** Contexto acima de ~90k tokens é dividido e unificado.
* **Tratamento de 401:** Sinalização de reautenticação sem fechar a aplicação.

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia evolução e autoria histórica com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos via `log_blame_metric()` com profundidade e número de commits analisados.
* 🆕 **Agora também alimenta o risco:** o leitor de histórico do score (`risk_history_reader.py`) usa a mesma janela de 90 dias e classifica bugs/reverts por padrão, sem chamar IA.

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)**

* **16 Ferramentas MCP Anotadas 🆕:** as 14 anteriores + **`get_baseline_status`** 🆕 (o digest do baseline: contagens por status, top regras, supressões e dívida aceita com dono e prazo, dívida vencida, estado do checksum — **nunca roda o linter, nunca chama a IA, nunca escreve) e **`get_usage_metrics`** 🆕 (o ledger de uso numa janela: execuções, custo por modelo, módulos tocados, provedores e taxas de qualidade; sem atalho de dia — quem chama nomeia as próprias datas).
* **19 Recursos + 7 Prompts Templatizados 🆕:** `skill://list` + `skill://{pr,commit,review,filereview,issue,blame,release,fix}` + `linter://config` + **`baseline://summary`** 🆕 + `prompt://list` + 7 prompts.
* **Registro de Skills Alinhado 🆕:** `mcp_server.SKILL_FILES` passou a ter **11 entradas** — recebeu `tests`, `explain` e `mentor`. A asserção `TestSkillRegistryAgreement`, que acusava a divergência, agora **passa**. ✅
* **Invocação CLI Direta:** `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool sem iniciar o servidor stdio; `gitpr-mcp --list` imprime o registry completo como JSON.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve no `sys.__stdout__` original, com fallback para `buffer` ou re-encode com `errors='replace'` em code pages legadas do Windows.
* **Offload do Event Loop:** Decorator `_offload` (`anyio.to_thread.run_sync`) em todas as tools — a ordem dos decorators importa (`@mcp.tool` **acima** de `@_offload`).
* **Falhas como Erro Estruturado 🆕:** as tools novas devolvem falha **como dado** em vez de levantar — um agente que pergunta o estado do baseline recebe a razão da falha, não uma exceção.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório:** Rótulo `📁 Repository: owner/repo` e filtragem estrita por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com `ProgressBar`; os testes aguardam `workers.wait_for_complete()` antes de asseverar.
* 🆕 **Leitura do Ledger:** o dashboard deixou de varrer arquivos JSON e passou a consultar o `telemetry.db` na thread de trabalho, renderizando as **cinco seções novas** (custo, qualidade, módulos, provedores, ciclo) a partir dos mesmos renderizadores que o CLI usa.
* 🆕 **Assistente de Migração (`src/ui/metrics_migration_app.py`):** oferece importar os arquivos legados, importar **e** reconstruir a partir do cache de IA, ou "agora não" — com semântica de aborto que **nunca cria um ledger vazio** sobre arquivos ainda não importados.
* **Exportação Local:** CSV/JSON em `./.gitpr/metrics/export/` — 🆕 `.gitpr/metrics/` entrou no `.gitignore` com um comentário explicando por que `.gitpr/skill/` **não** entra (é conteúdo do projeto). Os 35 artefatos já rastreados continuam rastreados, porque `gitignore` não destrackeia.

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* 🆕 **Reescrito nesta janela — ver §36.** `src/metrics.py` deixou de escrever arquivos e passou a operar sobre **linhas do ledger**; `enrich_metrics_from_cache()` e `load_cache_token_summary()` foram **removidos** (eram o casamento heurístico que zerava `tokens_actual`).
* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`, agora resolvido por `src/infrastructure/git/identity.py` — que funciona em **qualquer** forge, não só no GitHub.
* **Eventos de Hook, Linter e Blame:** `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()`.
* **Exportação e Limpeza:** `gitpr metrics export` (CSV/JSON), `prune`, `purge` com confirmação interativa, `bundle`/`merge` para transportar e fundir janelas.

### **19. Sincronização de Idiomas dos Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (**v0.0.4** 🆕).
* 🆕 **Templates reescritos:** `post-checkout`, `post-merge` e `pre-push` passaram a chamar `gitpr --quiet metrics hook-event <nome>`, guardados por `command -v gitpr` e `|| true` — a resolução de repositório em bash, que era **só do GitHub** e gravava eventos sob nomes de pasta inutilizáveis, foi removida. **Ação necessária: reinstalar os hooks com `gitpr --installhooks`.**
* **Mapeamento de Sufixos (`HOOK_SCRIPT_SUFFIXES`):** Códigos de interface (`es_es`, `fr_fr`) traduzidos para os sufixos publicados (`.es`, `.fr`).
* **Escolha vs. Estado (`SCRIPTS_LANG` / `SCRIPTS_INSTALLED_LANG`):** Permite **detectar a troca de idioma**.
* **`effective_hook_lang()`:** Resolve o idioma efetivo; `--lang` deixou de ser descartado nesse caminho.
* **Skip de Merge-Source:** O `prepare-commit-msg` pula as fontes `message|merge|squash|commit`.

### **20. Bridge de Linters Externos e Assistente Interativo (`src/linter_wizard.py`, `src/ui/linter_app.py`)**

* **Assistente `--linter-setup`:** Wizard com presets numerados (PHP_CodeSniffer, ESLint, Stylelint) e injeção do bloco `external_linters`.
* **Presets Remotos:** `templates/gitpr.linter-presets.json` com cadeia local → download → stale → fallback embutido.
* **TUI de Erros do Linter:** `src/ui/linter_app.py` (Textual) exibe erros críticos e warnings; em hook/quiet imprime e faz `sys.exit(1)`.
* **Relatório Markdown:** Consolidado em `.gitpr/reports/linter/` apenas quando há violações.
* **A Camada SAST é irmã, não substituta:** os bridges Semgrep/Gitleaks/Bandit alimentam o **mesmo** pipeline de relatório.

### **21. SCM Multi-Forge (`src/infrastructure/scm/`)**

* **Abstração Única (`ScmProvider` ABC):** `base.py` define o contrato (dataclasses `RepoRef`, `PullRequestDraft` etc. e `ScmProviderError(provider, http_status, message)` — `http_status` 0 = falha de rede).
* **Registry e Factory:** `resolve_scm_provider()` seleciona por `GITPR_SCM_PROVIDER` (default `github`); `detect_provider_from_remote()` identifica a forge pela URL do origin.
* 🆕 **`list_pull_requests(repo, state, since, until)` — paginado e canônico:** os quatro provedores traduzem os estados canônicos (`open`/`merged`/`closed`/`all`) para o vocabulário nativo, paginam no cursor de cada API (Link, `X-Next-Page`, continuation token, next-URL), filtram por janela inclusiva de datas e param cedo quando podem. **`list_open_pull_requests(repo)` virou um wrapper fino** na classe base — nenhum call-site mudou, mas o limite de uma página acabou.
* 🆕 **Por que o filtro é por data do estado:** três das quatro forges devolvem algo mais largo para um PR mergeado (o GitHub não tem estado `merged`, o Azure chama de `completed`, o Bitbucket diz `DECLINED`), então cada uma filtra a própria resposta contra a data que o estado implica — `merged_at` para merged, `closed_at` para closed, `created_at` nos demais.
* 🆕 **`supports_merged_dates`:** atributo de classe, `False` no Bitbucket Cloud, que publica **vazio** o `merged_at` em vez de uma data vizinha — declarado **antes** da chamada, como `supports_reviewable_diff`.
* 🆕 **`web_links.py` — o GitPR passou a construir links HTML:** até esta janela todo link vinha pronto no `html_url` do payload. As funções puras (`repo_web_base`, `commit_url`, `pull_request_url`, `user_url`) normalizam qualquer formato de remote — `https`, `ssh://`, `git://`, scp-like, com credenciais, porta customizada e **subgrupos aninhados do GitLab** — para uma base https e aplicam o padrão de página de cada forge. O Azure DevOps não tem URL de perfil simples, então seus contribuidores mantêm o nome de exibição.
* **`get_pull_request(repo, pr_id)` — método concreto da ABC:** default levanta `ScmNotSupportedError` e cada forge implementa — `list_open_pull_requests` pagina uma página só e não distingue fechado de inexistente.
* **Cabeçalhos do GitLab Sintetizados:** `changes[].diff` é um **hunk solto**; `old_path`/`new_path` montam os cabeçalhos `diff --git a/… / --- / +++`, honrando `/dev/null`. E `overflow: true` **levanta** em vez de revisar metade de um diff truncado.
* **`request_pull_request_reviewers` devolve `list[str]` (quebra de contrato):** Devolve os logins **efetivamente anexados**, lidos do corpo do `201`. Subclasses de terceiros precisam ser atualizadas — **item herdado, ainda sem documentação.**
* **Helpers Read-Only do GitHub:** `get_commit_author_login` (SHA → conta ligada ao e-mail do autor) e `get_user_login` (valida/canonicaliza um handle sem gastar requisição quando não pode ser login).
* **Fail-Fast por Forge:** Azure exige `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`; Bitbucket exige `GITPR_SCM_USERNAME`; `create_issue` no Azure levanta `ScmNotSupportedError`.
* **Publicação de Releases:** `provider.create_release()` usado pelo `gitpr release --publish`.
* **Artefatos:** Glossário + ADR-001/ADR-005; família `docs/scm-multiforge.*.md` em 5 idiomas; 9 arquivos de teste, **305 cenários** 🆕.

### **22. Subcomando `gitpr release` — Changelog / Release Notes (`src/release_engine.py`)**

* **Fluxo:** `git log` entre `--since` e `HEAD` → classificação por Conventional Commits → bump semântico sugerido (`--version <x.y.z>` sobrescreve) → montagem do changelog → resumo executivo de IA opcional → *prepend* no `CHANGELOG.md`.
* 🆕 **O Range Deixou de Vir do `git describe`:** o `describe --tags --abbrev=0` só enxerga tags alcançáveis a partir do HEAD — neste repositório resolvia para `v0.0.8`, então **cada release listava todas as versões anteriores**. A seção `[1.3.0]` saiu com **124 bullets, 115 deles repetição da 1.2.0**, e o bump sugerido podia ser **menor** que a versão já publicada. A origem do range passou a ser a **seção anterior do próprio changelog**, por dois âncoras: o hash mais novo daquela seção (resolvido num único `git log --no-walk`, ordenado por epoch para sobreviver a fusos mistos) e, como fallback, a tag da versão da seção; sem nenhum dos dois, degrada para a última tag **com aviso visível**.
* 🆕 **`_drop_released()` — a segunda linha de defesa:** qualquer commit cujo hash curto apareça em **outra** seção de versão é descartado, com contagem. Quando nada sobrevive, o run **aborta** com `❌ Nothing new to release` em vez de escrever uma seção vazia.
* 🆕 **Todo bullet virou link:** `- {subject} ([{short_hash}]({commit_url})) — {scope} · [#{n}]({pr_url}) · {YYYY-MM-DD}`. O número do PR sai do final `(#123)` do squash-merge, que permanece no subject; sem forge ou sem token, degrada para texto puro.
* 🆕 **A falha de PR mergeado por merge commit — corrigida por construção:** `git log --no-merges` significa que um commit de merge **nunca** chega ao classificador, então o `pr_number` era `None` **por construção** e nenhum changelog jamais teve segmento `[#n]`. Uma **segunda passada sobre o mesmo range** (`git log --merges`) monta `hash → PR` pela ancestralidade (`rev-list <merge>^1..<merge>^2`): os bullets continuam um por commit, agora com o link. Um merge que não é pull request (`Merge branch 'main' into …`) não empresta número, um commit alcançável por dois merges fica com o mais próximo, e a correção **não é retroativa** — só uma seção recém-cortada ganha links.
* 🆕 **Contribuidores resolvidos pela mesma escada dos revisores:** `get_commit_author_login` primeiro (vê endereços privados que a busca por usuário não vê), depois `email_to_handle`, com cache em `~/.gitpr/cache/contributors.json` — **só sucessos são cacheados**, então um run limitado por rate limit tenta de novo depois.
* 🆕 **A Fronteira da Seção Era um Bug Latente:** `upsert_changelog(force=True)` substitui da linha `## [x.y.z]` até o próximo cabeçalho de **nível 2**. Um `###` como fronteira deixava o corpo antigo vivo **acima** do novo; o `### Summary` e o rodapé de contribuidores ficavam para trás.
* **Classificador (`src/commit_classifier.py`)** e **Builder com Seções Traduzíveis (`src/changelog_builder.py`)** — 🆕 o builder ganhou a dataclass `LinkContext` e o classificador ganhou `pr_number_from_merge()`, que entende merge de GitHub, GitLab, Bitbucket e Azure DevOps.
* **Bump Semântico (`src/version_bump.py`)** e **Publicação** (`--publish`, `--draft`, `--format markdown|json`, `--force`). **6 opções no subcomando.**
* **Quebras declaradas:** `ReleaseNotesResult` ganhou o campo obrigatório `previous_version`; `build_release_section` ganhou o parâmetro opcional `links` (retrocompatível).
* **Artefatos:** `docs/release-notes.*.md` — a família já existia em 5 idiomas e foi **reescrita nesta janela** para o motor corrigido 🆕 —, ADR e `tests/test_web_links.py`.
* **Estado do release 1.4.0:** o `CHANGELOG.md` tem a seção `[1.4.0] - 2026-10-12` completa — as cinco features desta janela **mais** a nota do 1.3.0, com links. É a primeira seção gerada pelo motor corrigido.

### **23. Subcomando `gitpr config` — TUI de Configuração**

* **Tela Master-Detail (`src/ui/config_app.py`):** Categorias à esquerda, campos à direita, editados inline. Cabeçalho com busca (`/`) e contador de pendências; rodapé `F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc`. `ENABLE_COMMAND_PALETTE = False`.
* **Schema Declarativo (`src/config_schema.py`) — a fonte única de verdade:** **16 categorias** 🆕 (+2: **Policy** e **Baseline**) e **80 `ConfigField`** 🆕 (+9), dos quais **8 avançados**. Cada campo declara categoria, tipo de widget, `show_if`, validadores, marcadores de versão e ações de download.
* **Categorias `policy` e `baseline` 🆕:** os campos de pack (habilitação e teto de caracteres do contexto injetado) e os quatro do baseline, incluindo o caminho do arquivo e o interruptor que exige o checksum do lockfile.
* **Seção Skills Alinhada 🆕:** `SKILL_LABELS` passou de 8 para **11 entradas** — recebeu `tests`, `explain` e `mentor`. Os dois tipos que renderizavam **em branco** na barra lateral agora têm rótulo, e as duas asserções de `test_config_schema.py::TestSkillsSection` **passam**. ✅
* **Filtragem por Contexto (`show_if`):** `GEMINI_*`/`DEEPSEEK_*`/`OLLAMA_*` conforme o `DEFAULT_AI_PROVIDER`; `GITPR_SCM_USERNAME` sob `[Bitbucket]`; `GITPR_SCM_ORGANIZATION`/`PROJECT` sob `[Azure DevOps]`.
* **Busca Global (`/`):** Casa chave ou rótulo em todas as categorias e **ignora o filtro de visibilidade**.
* **Validação em Duas Camadas:** **Offline** bloqueia o `F2` com erro inline; **online** (só credenciais alteradas na sessão) roda em worker com timeout de 10s e só bloqueia em `401`/`403`.
* **Restaurar (`Ctrl+R`):** Remove a linha do `.env` em vez de reescrever o default; `Esc` com pendências pede confirmação.
* **Seção Skills — a única project-scoped:** Edita `.gitpr/skill/*.md` do projeto resolvidos a partir do diretório de chamada, gravando atomicamente e preservando CRLF/LF.
* **Downloads com Força:** Botões que forçam re-download de smart-excludes, traduções, presets e thinking words via `force=`.
* **Módulo de Links Leve (`src/doc_links.py`):** `doc_url()` saiu de `core.py` para a UI obter o link sem importar SDKs de IA.
* **Testes:** 5 arquivos — `test_config_app.py` (78), `test_config_schema.py` (42), `test_config_validation.py` (40), `test_config_store.py` (22), `test_config_cli.py` (9). 🆕 A suíte passou a **estabilizar o ambiente** antes de montar a TUI — sem isso, um `GITPR_BASELINE_*` vazado do shell mudava a árvore de categorias.
* **Dívida conhecida:** `gitpr -h config` abre a TUI e ignora o `-h` — o gate `if ctx.invoked_subcommand is not None: return` (main.py:678) roda antes do bloco de `help_flag`.

### **24. Log Geral de Uso (`src/usage_log.py`)**

* **Uma Linha por Comando:** Grava `~/.gitpr/logs/<uuid5>.log`, **um arquivo por dia**, com comando, argumentos, repositório, usuário e timestamp.
* **Nome Derivado da Data:** `uuid5(NAMESPACE_DNS, f"gitpr.usage.{YYYY-MM-DD}")` — dois processos concorrentes não podem discordar sobre qual arquivo é o de hoje.
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
* 🆕 **O baseline é resolvido antes da primeira chamada de rede**, e os avisos do gate são mesclados ao relatório/comentário — um PR remoto é julgado pela mesma política do repositório local.
* 🆕 **`render.py` ganhou o parâmetro do risco:** `compose_review_content` / `render_review_result` **antepõem** a seção `⚡ Risk Assessment` acima dos alertas do linter, quando `GITPR_RISK_INCLUDE_IN_REVIEW` está ligado.
* **Artefatos:** `docs/review-pr.md` + `.pt_br.md` (os 3 idiomas restantes **continuam pendentes**), `docs/code-review-ia.*.md` (5), ADR-005 e `glossary-review-pr.md`.
* **Testes:** 4 arquivos em `tests/review/` (**97 cenários**).

### **27. Resolução de Identidade do Revisor (`src/reviewer_resolution.py`)**

* **O Bug (duas falhas silenciosas encadeadas):** (1) **Prefill vazio** — `handles` só com `email_to_handle()`; (2) **Attach não verificado** — valores repassados *verbatim*, o GitHub respondia **201 sem anexar ninguém** e o `_request()` retornava sem levantar.
* **Módulo:** Plano, sem I/O próprio, **que nunca levanta**. `resolve_candidates()` (antes da TUI) e `resolve_typed_reviewers()` (no attach); `match_candidate()` casa exato e normalizado por login, nome ou e-mail.
* **Escada de Resolução:** handle conhecido (sem requisição) → casamento exato com uma pessoa sugerida → lookup por e-mail → validação do login na forge.
* **O que não resolve nunca é enviado:** Sai em `ResolutionOutcome.dropped` como `(valor, motivo_i18n)` e é descartado com aviso visível.
* **A Mesma Escada Serve ao Release 🆕:** o `release_engine` reusa `get_commit_author_login` + `email_to_handle` para transformar e-mails de commit em logins clicáveis.
* **Testes:** `tests/test_reviewer_resolution.py` (18) + ampliações em `test_github_provider.py` (72), `test_pr_publish_app.py` (45), `test_suggest_reviewers.py` (17), `test_reviewer_suggestion.py` (18) e `test_main_suggest_reviewers.py` (8).

### **28. Subcomando `gitpr demo` — Tour Guiado sobre Exemplos Gravados (`src/demo/`)**

* **O que é:** Um tour interativo que mostra as três saídas principais do GitPR — mensagem de commit, review e descrição de PR — **sem chave de API, sem repositório git e sem rede**.
* **Pipeline Real, Resposta Falsa:** `FakeAIProvider` espelha `src.ai_providers.call_ai_model` **argumento por argumento**; `demo_pipeline()` faz patch de `src.core` e `src.metrics` para que o pipeline de produção rode **intocado** e só a origem da resposta seja trocada.
* **Isolamento é Requisito, Não Detalhe:** O tour **não pode** tocar o `~/.gitpr` do usuário nem a rede — garantido por `tests/demo/conftest.py` (proibição de rede autouse, com exceção de loopback para o event loop proactor do Windows).
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

* **O que é:** Uma árvore de trabalho com vários concerns deixa de virar um commit-blob. O `split` lê o diff não commitado, pede à IA que particione os hunks por **intenção lógica** e propõe um commit atômico por concern. A árvore nunca é reescrita: os arquivos terminam byte a byte iguais ao início.
* **Pacote de 6 arquivos:** `split_plan.py`, `hunk_parser.py` (puro), `hunk_grouper.py`, `generate_split_plan.py` (read-only), `apply_split_plan.py` (**o único que muta**) e `__init__.py`.
* **A Garantia de Árvore Intacta é Estrutural:** `selective_stager.py` pré-valida **todo** grupo contra um índice temporário em HEAD e usa um `GIT_INDEX_FILE` descartável.
* **Destrutivo para o Índice, Não para a Árvore:** O `--apply` reseta o índice para HEAD antes de stagear, então o que o usuário já tinha staged é desestagiado — documentado explicitamente.
* **Configuração:** `GITPR_SPLIT_MAX_GROUPS` (5), `GITPR_SPLIT_MAX_HUNKS` (50) e `GITPR_SPLIT_REQUIRE_CONFIRMATION` (`true`). Valores zero ou negativos são **ignorados em favor do default**.
* **Testes:** 6 arquivos em `tests/split/` (**101 cenários**).
* **Artefatos:** `docs/split-command.md` — 🆕 **agora em 5 idiomas** (os 3 que faltavam entraram em 2026-09-24), ADR-006, `glossary-gitpr-split.md`, spec/plano e survey.

### **31. Varredura de Segredos Embutida (`src/security_ruleset.py`)**

* **O que é:** Sete regras que rodam em **toda** invocação do linter, mescladas ao fim de `load_linter_rules()` depois das regras do projeto e dos plugins.
* **As Sete Regras:** cinco `error` bloqueantes — AWS access key ID, token GitHub, token Slack, chave de API Google e bloco de chave privada — e duas `warning`: URL de conexão de banco com credenciais e atribuição genérica de credencial (`password = "…"`), esta atrás de um filtro de placeholder (`changeme`, `xxxxxx`, `example`, `dummy`, `sample`, `your_password_here`, `sua_senha`).
* **Por que no Pacote e Não no Template:** Um portão de segredos precisa se comportar **igual** em toda máquina e em todo CI, então as regras vivem no pacote e não podem ser substituídas por `--skill` nem reescritas pelo wizard.
* **Lacunas de Cobertura (v1) — confirmadas ainda abertas 🆕:** atribuição **sem aspas** não é pega (`API_KEY=abc123`, o formato `.env`); faltam os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-`; e não há fronteira à esquerda no nome da chave.
* **Configuração:** `GITPR_LINTER_SECURITY` (default `true`; opt-out fail-open) e `GITPR_LINTER_SECURITY_DISABLED_RULES` (`;`-separadas).
* **Testes:** `tests/test_security_ruleset.py` (**61 cenários**).
* **Artefatos:** ADR-007, `glossary-gitpr-secret-scanning.md`, spec/plano/survey e 3 relatórios de tarefa.

### **32. Bridges SAST — Semgrep, Gitleaks e Bandit (`src/infrastructure/linter/external/`)**

* **O que é:** Uma camada **opt-in** que pluga scanners de segurança de terceiros no pipeline de linter existente.
* **Escopo Bounded:** Rodam **só** quando habilitados e **só** sobre os arquivos tocados pelo diff.
* **Contrato Comum:** `ExternalLinterBridge` (ABC) com execução endurecida de `subprocess` (`shell=False`, timeout estrito, `stdin=DEVNULL`, UTF-8 com `errors='replace'`). 🆕 O modelo `NormalizedFinding` **saiu daqui** para `src/domain/finding/`, e o `base_bridge` passou a **re-exportá-lo** para não quebrar import existente.
* **Deduplicação é o Ponto:** `deduplicate_secret_findings()` funde achados do Gitleaks e do ruleset regex no mesmo arquivo e linha numa **única** entrada confirmada `[Gitleaks + Regex]`.
* **Segredos Mascarados:** `mask_secret_value()` garante que o valor nunca chegue ao achado, ao log ou à telemetria.
* **Resolução em Três Camadas:** `load_sast_config()` lê defaults → `.gitpr.linter.yml` (bloco `sast`, caindo para `linter.external`) → variáveis `GITPR_SAST_*`. **Todas default `false`**.
* **Degradação Graciosa:** Ferramenta habilitada mas ausente do `PATH` emite aviso e a execução continua.
* **Testes:** 4 arquivos em `tests/infrastructure/linter/external/` (**14 cenários**) + `tests/domain/linter/test_sast_finding_mapper.py` (2) + **`tests/domain/linter/test_structured_findings.py` (44)** 🆕, que cobre a passagem dos achados normalizados pelo motor de lint.

### **33. Subcomando `gitpr tests generate` — Geração de Suíte por IA (`src/domain/tests_generation/`, `src/application/`)**

* **O que é:** Gera arquivos de teste completos e executáveis a partir do diff atual, de um arquivo específico ou de um achado de review, **respeitando a convenção do repositório** (Pest, PHPUnit, Jest, Vitest, Pytest).
* **Domain Layer:** `TestFramework` (enum) e as dataclasses `TestGenerationTarget`, `TestScaffold`, `GeneratedTest`; `detect_test_framework()` detecta pelos arquivos de configuração, manifests e conteúdo do diretório de testes; `build_test_scaffold()` calcula o caminho convencional de destino por framework.
* **Application Layer (`generate_test_file.py`):** Orquestra detecção, resolução de scaffold, prompt, IA, parsing do JSON e escrita opcional. `validate_test_syntax()` roda o toolchain local (`php -l`, `node --check`, `python -m py_compile`) — falha de validação é **aviso**, não erro.
* **Apresentação:** Grupo `tests` com `generate` (`--file`, `--finding`, `--framework`, `--apply`, `--provider`); dry run é o default e sobrescrever teste existente pede confirmação com **No** pré-selecionado. O chat delega `/tests` ao **mesmo** caso de uso.
* **Dívida fechada 🆕:** o tipo `tests` está em `SKILL_LABELS` e em `mcp_server.SKILL_FILES`, e as 17 chaves `__()` que não existiam foram traduzidas. **Continua sem tópico em `docs/`** — só template de skill e spec.

### **34. Subcomando `gitpr explain` e a Flag `--explain` — Guia do Revisor (`src/domain/pr/`)**

* **O que é:** Um guia centrado em quem vai **revisar** — o que muda, por que muda, onde focar e qual o risco de regressão.
* **Domain Layer (`explain_section_builder.py`):** `PrExplanation` / `ReviewerFocusPoint`, o renderizador `build_explain_markdown()` e `parse_explain_payload()`, que tolera saída não-JSON e **detecta placeholders** `[FILL]`/`[TODO]` para sinalizar evidência insuficiente em vez de apresentar um guia oco como completo.
* **Application Layer (`generate_pr_explanation.py`):** Resolução de provedor, validação da chave, carregamento do skill context (`explain`), prompt, invocação e parsing.
* **Duas Portas de Entrada:** `gitpr explain` (`--provider`, detecção de diff ausente antes de qualquer IA) e a flag `--explain` no CLI raiz, que anexa o guia ao corpo da descrição de PR **e** ao payload JSON.
* **Configuração:** `GITPR_EXPLAIN_BY_DEFAULT` (default `false`).
* **Dívida fechada 🆕:** `explain` está em `SKILL_LABELS` e em `mcp_server.SKILL_FILES`, e as chaves foram traduzidas. **Continua sem tópico em `docs/`.**

### **35. Suíte Determinística e o CI (`.github/workflows/tests.yml`)**

* **O que é:** O workflow que roda a suíte em **Python 3.10** (o piso declarado em `pyproject.toml`) e **3.13**, com `fail-fast: false`.
* **`tests/conftest.py` Hermético:** Pina `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false` e `LANG_VERSION` na versão do código, além de `GITPR_SHOW_LOGS=false` e `GITPR_SKIP_UPDATE_CHECK=true`.
* **Ordem Importa:** `src.updater` é importado **antes** das variáveis de idioma serem definidas, porque o `i18n` fotografa `os.environ` em `AMBIENT_ENV_KEYS` no import.
* **Estabilidade de Testes de Worker:** `test_config_app.py` e `test_metrics.py` aguardam `workers.wait_for_complete()` antes de asseverar.
* **Dependência do Workflow:** O runner limpo não tem `~/.gitpr`, e `test_demo_isolation.py` assevera que o perfil existe — o job cria o diretório e o `.env` vazio explicitamente.
* 🆕 **Nesta janela a suíte cresceu 48% e o cenário de falha mudou de lado:** as três asserções que existiam para acusar dívida de registro (`TestSkillsSection`, `TestNoMissingKeys`, `TestSkillRegistryAgreement`) **passam** — o mecanismo de detecção funcionou e foi pago no mesmo ciclo em que foi criado.

### **36. Ledger SQLite de Telemetria (`src/ledger.py`, `src/infrastructure/git/identity.py`) 🆕**

* **O Problema Não Era o Formato, Era o Join:** os eventos eram gravados como arquivos JSON por comando, a partir de uma **thread daemon** (que um processo curto — um hook — pode não sobreviver), e depois reconectados ao cache de IA por um casamento heurístico de `(repo, branch, ação, minuto)` que dependia de **três mapas comando→pasta divergentes**. O sintoma era `tokens_actual` **sempre `0`** para `fullreview`/`filereview` e perda de dados entre repositórios na exportação.
* **A Escrita é Síncrona, e Isso é a Decisão:** `log_command_metric()` resolve o contexto de git **uma vez por processo** e grava a linha na hora, em vez de entregá-la a uma thread que um hook pode não sobreviver. Tokens, modelo e provedor são **copiados dos metadados do provedor no momento da escrita** — não há mais enriquecimento a posteriori.
* **Schema Versionado:** `SCHEMA_VERSION` + `PRAGMA user_version`, chaves UUID (não inteiros sequenciais, para que `merge` de dois ledgers não colida), WAL + `synchronous=FULL`, e `LedgerVersionError` para recusar um bundle mais novo **antes** do `ATTACH` — o ledger local nunca fica meio-importado.
* **Invariante "Nunca Nasce Vazio":** `ensure_ledger()` só cria o banco **junto** com a absorção dos JSON legados (originais movidos para `~/.gitpr/metrics_legacy/`, marcador de recusa, caminho silencioso em modo não interativo).
* **Uma Janela, Um Significado:** `--since`/`--until`/`--days` (inclusivos nas duas pontas) estreitam **toda** superfície de leitura. A seção de ciclo é a exceção — ela pergunta à rede, então assume os últimos 30 dias e **nomeia a janela no próprio cabeçalho** em vez de estreitar em silêncio.
* **Cada Métrica é Computada uma Vez e Renderizada uma Vez:** os pares `(style, text)` (`TITLE`/`PLAIN`/`WARN`) fazem CLI e dashboard Textual contarem a **mesma** história; uma seção sem nada a dizer é omitida, nunca impressa vazia.
* **Custo com Tabela Embutida e Override:** preços de lista dos quatro modelos que o GitPR distribui (`deepseek-v4-pro`, `deepseek-v4-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`), sobrescritos por `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT`. **As duas taxas são obrigatórias** — precificar metade de um modelo a um zero não configurado **subestima** a conta, então o modelo é reportado só em tokens. `ollama`/`local` custam zero; `GITPR_METRICS_CURRENCY` rotula o total e, quando não é USD, **descarta** a tabela embutida em vez de rotular um preço em dólar com outro nome. Um total que deixa modelos de fora lê `Total (partial)`.
* **`modules` Normalizado:** os caminhos do diff viram dois segmentos (`src/fix`), `(root)` para um arquivo na raiz e `(no module)` para os comandos que nunca tiveram diff (linter, blame, hooks).
* **Transporte por Bundle:** `bundle` escreve a janela como um `.db` autônomo (schema e `user_version` viajam com ele) e `merge` o anexa e insere por UUID, migrando um bundle antigo para cima e recusando um mais novo.
* **`cache_backfill` Fica de Fora:** linhas reconstruídas a partir do cache de IA são marcadas e **excluídas dos agregados de execução** — a chave do cache é o prompt, então elas contam prompts distintos, não execuções.
* **Identidade de Git sem Forge (`identity.py`):** rótulo de repo, branch e autor numa **única** chamada de subprocesso, válido em qualquer forge — e deliberadamente **sem** construir um `ScmProvider`, que custaria caro em todo comando de telemetria.
* **A Seção de Ciclo é a Única que o Ledger Não Responde:** ela lista PRs mergeados via `ScmProvider.list_pull_requests` e mede `created_at → merged_at`, com códigos de status explícitos (ok/empty/unavailable/unsupported). Toda falha degrada para **uma linha** — `Not read: <razão>`, sem data de merge no Bitbucket, nada mergeado na janela — nunca um stack trace e nunca um número chutado.
* **Apresentação Completa:** grupo `gitpr metrics` com 8 subcomandos, dashboard lendo o ledger em thread de trabalho e o assistente de migração de três opções.
* **Configuração:** `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT`, `GITPR_METRICS_CURRENCY` e `.gitpr/metrics/` no `.gitignore`.
* **Testes:** `tests/test_metrics.py` saltou de 34 para **164 cenários**; `tests/scm/*` ganhou a paginação de `list_pull_requests` e `within_window` em todas as forges; `test_commit_classifier.py` (30) cobre `pr_number_from_merge`.
* **Artefatos:** ADR-008, `glossary-metrics-telemetry.md`, `docs/plans/develop_natan/20260927_metrics_audit_plansfacts.md`, survey e **`docs/metricas-telemetria.*.md` reescrito nos 5 idiomas**. Vocabulário canônico em `docs/plans/glossary-metrics-telemetry.md` (conforme CLAUDE.md).

### **37. Subcomando `gitpr mentor` e a Flag `--mentor` — Modo Mentor (`src/domain/mentor/`) 🆕**

* **O que é:** Um review diz *o que* está errado e quase nunca *por que aquilo importa*. O Modo Mentor enriquece achados com **o que está acontecendo**, **por que importa**, uma **analogia** do dia a dia e os **conceitos a estudar** — para quem está começando, o valor de um review está no que ele ensina depois de apontar.
* **Domain Layer Puro (`mentor_explanation_builder.py`):** sem I/O, converte o payload da IA em `MentorExplanation` validado e impõe **honestidade epistêmica** em três frentes: sem evidência suficiente, a explicação **diz isso** em vez de preencher o vazio; URLs alucinadas são **removidas** dos ponteiros "learn more"; e IDs de achado desconhecidos são **rejeitados**, preservando a ordem estrita dos achados originais.
* **Application Layer (`generate_mentor_explanation.py`):** coleta candidatos (`collect_candidates`), **lotes de no máximo 10 achados** por execução, ordenados por severidade, reusando o cache MD5 por hash de prompt — repetir o mentor sobre um review inalterado **não custa nada**.
* **Duas Portas de Entrada:** `gitpr mentor [--finding <id>] [--provider <nome>]` roda sobre o **último review persistido** (portanto precisa vir depois de um `-r`/`-f`), e a flag `--mentor` anexa a seção à revisão normal, com aviso quando usada numa ação que não a suporta.
* **Opt-In Estrito:** `GITPR_REVIEW_MENTOR_MODE` (default `false`) e `GITPR_MENTOR_INCLUDE_ANALOGY` (default `true`), editáveis na TUI de configuração. Ligar custa chamadas de IA adicionais — é por isso que o default é desligado.
* **Skill e Registro:** `.gitpr.mentor.md` registrado em `SKILL_FILES_BY_TYPE`, em `mcp_server.SKILL_FILES` e em `SKILL_LABELS`, com templates em **5 idiomas**.
* **Testes:** `tests/domain/mentor/test_mentor_explanation_builder.py` (8), `tests/application/use_cases/test_generate_mentor_explanation.py` (5) e `tests/test_mentor_cli.py` (4).
* **Artefatos:** `docs/mentor-mode.*.md` em **5 idiomas**, ADR-009, `glossary-gitpr-mentor.md`, spec e relatórios de tarefa.

### **38. Subcomando `gitpr risk` — Score de Risco Determinístico (`src/domain/risk/`) 🆕**

* **O que é:** Um score **0–100** com nível `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`, calculado **sem IA** a partir de sinais locais, para que o revisor saiba onde olhar primeiro — e para que o mesmo diff receba o mesmo número duas vezes.
* **Domain Layer Puro (`risk_types.py`, `risk_rules.py`, `risk_calculator.py`, `risk_explanation.py`):** enums e dataclasses (`RiskLevel`, `RiskSignal`, `RiskEvidence`, `FileRisk`, `PullRequestRisk`); pesos, limiares, padrões de caminho crítico, casamento por glob e detecção de teste/não-executável carregados de YAML; cálculo por arquivo com **clamp 0–100** e agregação 50/30/20.
* **A Fórmula é Declarada, Não Aprendida:** a agregação combina **50%** o arquivo de maior risco, **30%** a média ponderada por linhas e **20%** evidência crítica. Acima disso há **regras de elevação obrigatória**: score ≥ 80 sobe para pelo menos `HIGH`; um bloqueador ou score ≥ 90 força `CRITICAL`. Um score sem regra de elevação é um número que o time aprende a ignorar.
* **Infrastructure Adapters:** `risk_history_reader.py` lê `git log` com segurança e extrai commits, correções de bug e reverts numa janela de **90 dias**; `test_matcher.py` casa arquivo de teste ↔ arquivo de produção por convenção, em vários layouts de linguagem.
* **Use Case (`calculate_risk.py`):** correlaciona seções do diff parseado, achados, casamento de testes e histórico em `FileRisk`/`PullRequestRisk`, **degradando com aviso** quando um sinal não está disponível. Aplica o pack de política por cima da configuração base, quando há um ativo.
* **Três Consumos:** o comando `gitpr risk` (`--file`, `--format text|json`, `--base`, `--no-history`), a seção `⚡ Risk Assessment` anexada a reviews e ao review de PR remoto, e o **prompt da IA** — onde o score entra como contexto **read-only**, com formato compacto.
* **Opt-Out:** `GITPR_RISK_INCLUDE_IN_REVIEW` (default `true`) — como o default liga, a seção passa a aparecer nos reviews de quem atualizar; desligar é uma variável. **Mudança de comportamento declarada.**
* **Configuração por Projeto:** `templates/gitpr.risk.yml` (ou `.gitpr/skill/gitpr.risk.yml`) sobrescreve pesos, limiares e caminhos críticos. Pesos negativos só são aceitos para sinais **mitigadores** como `test_present`.
* **Testes:** `tests/domain/risk/` (2 arquivos, 10 cenários), `tests/application/use_cases/test_calculate_risk.py` (5), `tests/infrastructure/git/test_risk_history_reader.py` (4), `tests/infrastructure/git/test_test_matcher.py` (5) e `tests/test_risk_cli.py` (4).
* **Artefatos:** `docs/risk-scoring.*.md` em **5 idiomas**, ADR-010, `glossary-gitpr-risk-scoring.md` e relatórios de tarefa (incluindo um do Gemini).

### **39. Subcomando `gitpr policy` — Policy Packs Versionados (`src/domain/policy/`, `src/infrastructure/policy/`) 🆕**

* **O que é:** Um **pack YAML versionado** que carrega, num artefato só, as decisões de qualidade de um repositório: skills, regras de linter, severidades, caminhos críticos, pesos de risco e convenções de PR/commit. Hoje cada repositório configura isso à mão — o que torna o comportamento difícil de reproduzir, compartilhar e **travar**. O pack torna a configuração declarativa, versionada, componível e reproduzível.
* **Domain Layer (`policy_types.py`, `policy_manifest.py`, `policy_checksum.py`, `policy_compatibility.py`, `policy_resolver.py`):** parsing de manifest com **schema fechado** (chave desconhecida é erro, não aviso), verificação de compatibilidade e de credencial, **checksum SHA-256** e um resolvedor de grafo com precedência e composição.
* **Infrastructure Layer:** `local_policy_repository.py` resolve o pack por **três origens** (`.gitpr/policies`, `~/.gitpr/policies` e o pacote embutido) e `policy_pack_loader.py` o carrega.
* **Use Cases:** `activate_policy_pack`, `install_policy_pack`, `resolve_effective_policy` e `validate_policy_pack`.
* **Quatro Packs Embutidos:** `laravel-quality`, `node-quality`, `php-security` e `vue-quality`, cada um com `policy.yml` e `linter.yml`, distribuídos por **`package-data`** — um pack que não viaja no wheel é um pack que só existe na máquina de quem o escreveu.
* **Consumo Integrado em Quatro Pontos:** `calculate_risk` (política sobre configuração base), `config.load_linter_rules` (merge em camadas + override de severidade), `core.get_skill_context` (injeta o contexto do pack) e a **chave de cache do PR** (`cache_scope`) — dois repositórios sob políticas diferentes não podem compartilhar uma resposta de IA.
* **CLI:** `gitpr policy {list, validate, show, use, off, install, init}`, com confirmação (`--yes`/`--force`), detecção de stack no `init` e gravação da escolha em `.gitpr/policy.lock.yml`.
* **Configuração:** `GITPR_POLICY_ENABLED` e `GITPR_POLICY_CONTEXT_MAX_CHARACTERS` (o teto do contexto injetado no prompt), ambos na nova categoria `policy` do schema.
* **Retrocompatibilidade:** sem pack ativo, o comportamento é **preservado** — coberto por teste de integração, não por inspeção.
* **Dependência Nova:** `packaging>=23.0` (SemVer/PEP 440), declarada em `Pipfile` e `pyproject.toml`.
* **Testes:** `tests/domain/policy/` (4 arquivos, 126 cenários), `tests/application/use_cases/` (4 arquivos de policy, 89), `tests/test_policy_cli.py` (26) e `tests/integration/test_policy_effect_on_review_linter_risk.py` (31 — efeitos reais num repositório de verdade, com guarda autouse de rede).
* **Artefatos:** `docs/policy-packs.*.md` em **5 idiomas**, ADR-011, `glossary-policy-packs.md`, spec/plano/survey.

### **40. Subcomando `gitpr baseline` — Baseline e Supressões Auditáveis (`src/domain/baseline/`) 🆕**

* **O que é:** Linters e reviews re-reportam os mesmos achados pré-existentes a cada execução, e o trabalho de diferenciar a saída na cabeça sobra para o revisor. O baseline grava a **fotografia dos achados que o repositório já conhece** em `.gitpr/baseline.json`, fingerprinta cada um de forma estável entre execuções e deixa o pipeline classificar o que é novo — **só o `new` bloqueia**.
* **Domain Layer (`baseline_fingerprint.py`, `baseline_types.py`, `baseline_manifest.py`, `baseline_comparator.py`, `suppression_policy.py`):**
  * **Fingerprint estável:** identidade da regra, caminho normalizado, linhas e **sha256 da linha com whitespace colapsado** — a linha crua **nunca** é armazenada, então o baseline não é um arquivo onde segredos vazam por acidente.
  * **Manifest canônico:** JSON canônico com checksum, validação que recusa chave desconhecida, versão de schema/fingerprint fora do suportado, invariante de supressão/dívida quebrada, fingerprint duplicado e faixa de linhas inválida.
  * **Comparador:** classificação, contagens por status e resolução de entrada — `resolved` e depois `back` lê como **novo**, que é a leitura conservadora.
  * **Política de Supressão:** supressões, dívida aceita, overrides e validadores, com casamento em camadas (entrada × overrides × policy pack) por **especificidade e precedência**, mais rastreio de dívida vencida.
* **Cinco Use Cases:** `baseline_gate` (o ponto de entrada único do pipeline — carrega, classifica, anota e compõe as camadas de entrada, local e override de pack), `baseline_summary` (visão JSON **read-only** para IDE e agentes MCP), `compare_against_baseline`, `create_baseline` (criação/atualização com proveniência, checksums e **preservação das decisões humanas**) e `suppress_finding` (suprime/remove nos escopos de achado, linha, arquivo e regra).
* **Integração com Policy Pack:** o pack pode carregar um bloco `baseline:`, validado pelos **mesmos** validadores, composto pelo resolvedor como uma camada etiquetada e reportado pelo `policy validate`.
* **Repository é o Único que Escreve:** `local_baseline_repository.py` é o **único** leitor/escritor de `.gitpr/baseline.json` e `.gitpr/baseline.overrides.yml`, com escrita atômica, portão de checksum/versão e caminho de reparo.
* **Configuração:** `GITPR_BASELINE_ENABLED`, `GITPR_BASELINE_PATH`, `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` e `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES`, na nova categoria `baseline`.
* **Opt-In e No-Op:** desligado ou sem baseline existente, a feature **não lê arquivo e não imprime nada** — quem não usa não vê mudança.
* **⚠️ A Exceção Deliberada:** um arquivo de baseline que existe mas **não pode ser aplicado** faz o lint, o review, o full review, a auditoria de arquivo, o review remoto e o risk **abortarem com exit code 1**. Um baseline que falha em silêncio é um baseline que "some" com achados sem ninguém saber — o aborto é a escolha segura.
* **Alcance:** CLI (6 subcomandos, todos com `--format json`), MCP (tool `get_baseline_status` + recurso `baseline://summary`), review de PR remoto (resolvido **antes da primeira chamada de rede**) e o fluxo de lint, cujo exit code passou a seguir o bloqueio baseline-aware.
* **Refatoração que a Feature Exigiu:** `NormalizedFinding` virou tipo canônico em `src/domain/finding/` (com `snippet_hash` e `rule_version`), importado por todos os bridges — sem isso, o mesmo achado teria uma forma por ferramenta e o fingerprint não o reconheceria.
* **Testes:** `tests/domain/baseline/` (5 arquivos, **126 cenários**), `tests/application/use_cases/` (5 arquivos, **141**), `tests/infrastructure/baseline/test_local_baseline_repository.py` (24), `tests/domain/finding/test_finding_types.py` (3), `tests/domain/linter/test_structured_findings.py` (44), `tests/test_baseline_cli.py` (54) e `tests/integration/test_baseline_effect_on_review_linter_risk.py` (34).
* **Artefatos:** `docs/baseline-suppressions.*.md` em **5 idiomas**, ADR-012, `glossary-baseline.md`, spec/plano/survey e relatório de tarefa.

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_blame_engine_ranges.py` | 7 | Blame por faixa de linhas em arquivo |
| `tests/test_blame_metrics.py` | 7 | Métricas de blame: profundidade, commits, duração |
| `tests/test_baseline_cli.py` | 54 🆕 | Grupo `baseline`: create/show/validate/update/suppress/unsuppress |
| `tests/test_changelog_builder.py` | 22 | Builder do changelog: seções, headings traduzíveis, contribuidores, **links e datas** |
| `tests/test_chat_backend.py` | 19 | Memória de chat, persistência, comandos slash |
| `tests/test_commit_classifier.py` | 30 | Classificação Conventional Commits + **`pr_number_from_merge()` nas 4 forges** |
| `tests/test_config_app.py` | 78 | TUI de configuração: montagem, troca de categoria, dirty tracking, F2 bloqueado, Ctrl+R, busca, segredos |
| `tests/test_config_cli.py` | 9 | Registro do subcomando `config`, `-h`, import lazy, stdout limpo |
| `tests/test_config_schema.py` | 42 | Cobertura de `DEFAULT_CONFIG`, sem duplicatas, categorias/kinds, `advanced` só em Avançado, **seção de skills** ✅ |
| `tests/test_config_store.py` | 22 | Round-trip no `.env` temporário, comentários e ordem preservados, `remove_config_value()` idempotente |
| `tests/test_config_suggest_reviewers.py` | 8 | Configuração de suggested reviewers (chaves e defaults) |
| `tests/test_config_validation.py` | 40 | Tipos, enums, templates, `validate_ai_key()` com SDK mockado (401 vs. rede vs. ollama) |
| `tests/test_core.py` | 49 | Fluxos principais, git diff, PR generation, timing, staging, coautoria, idioma dos hooks |
| `tests/test_diff_parser.py` | 26 | Parser de diff por linhas/hunks + `summarize_patch()` e `split_patch_sections()` |
| `tests/test_explain_command.py` | 2 | CLI do `explain`: sucesso, chave ausente, diff vazio |
| `tests/test_external_linters.py` | 33 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_i18n.py` | 20 | Paridade entre idiomas, chaves ausentes/órfãs, identidade — **zero chaves faltantes** ✅ |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação |
| `tests/test_issue_engine.py` | 4 | Draft de issue estruturado |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_linter_presets.py` | 5 | Presets de linter: resolução e re-download forçado |
| `tests/test_main_suggest_reviewers.py` | 8 | Flag `--no-suggest-reviewers` na CLI e no help contextual |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 110 | Ferramentas MCP (16), recursos (19), annotations, patching, CLI direto, offload — **acordo de registries de skill** ✅ |
| `tests/test_mcp_server_e2e.py` | 6 | Servidor MCP real via subprocess + JSON-RPC stdio |
| `tests/test_mentor_cli.py` | 4 🆕 | CLI do `mentor` e opt-in do `--mentor` |
| `tests/test_metrics.py` | 164 | **Ledger**: escrita síncrona, exportação idempotente, bundle/merge, versionamento, migração, renderizadores, custo, qualidade, módulos, provedores, ciclo |
| `tests/test_net_timeouts.py` | 12 | Timeouts de rede/IA — alinhados ao default real de 180s |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_policy_cli.py` | 26 🆕 | Grupo `policy`: list/show/validate/use/off/install/init, confirmação e lockfile |
| `tests/test_pr_publish_app.py` | 45 | TUI do PR Publisher: telas, fluxos, suggested reviewers, `NoticeScreen` |
| `tests/test_pr_publish_linter_modal.py` | 4 | Modal de erro do linter: abort, no-verify |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_release_cli.py` | 4 | CLI do release: options, help com epilog documentado |
| `tests/test_release_engine.py` | 53 | **Corte ancorado no changelog, `_drop_released()`, links, mapa de PR por merge commit**, publicação |
| `tests/test_reviewer_resolution.py` | 18 | Escada de resolução, rejeição de nome parcial, dedup, tolerância a falha |
| `tests/test_reviewer_suggestion.py` | 18 | Lógica de sugestão de revisores (ranking, exclusão, top-N, `last_commit_hash`) |
| `tests/test_risk_cli.py` | 4 🆕 | CLI do `risk`: `--file`, `--format json`, `--base`, `--no-history` |
| `tests/test_security_ruleset.py` | 61 | Matriz do ruleset embutido: regex, placeholders, nível, wildcard, merge, traduções |
| `tests/test_skill_command.py` | 10 | Download e validação de templates de skill |
| `tests/test_skill_context.py` | 18 | `get_skill_context()` com `quiet=True`, fallbacks, registro de skills |
| `tests/test_smart_excludes.py` | 15 | Filtro pathspec inteligente e re-download forçado |
| `tests/test_suggest_reviewers.py` | 17 | Suggested reviewers no fluxo de PR (integração, hint `no_login`) |
| `tests/test_tests_command.py` | 2 | CLI do grupo `tests` e do `generate` |
| `tests/test_thinking_words.py` | 5 | Carregamento, parsing com separador `;` e reload forçado |
| `tests/test_updater.py` | 23 | Gate do PyPI: parsing de versão, cache diário, fetch, decisões do portão, wiring no CLI |
| `tests/test_usage_log.py` | 27 | Log de uso: nome derivado da data, escrita síncrona, silêncio, `_repo_label()` multi-forge |
| `tests/test_version_bump.py` | 17 | Bump semântico: major/minor/patch, alvos e validação |
| `tests/test_web_links.py` | 26 🆕 | Normalização de remote (https/ssh/scp/credenciais/porta) e padrões de URL por forge |
| `tests/application/use_cases/test_activate_policy_pack.py` | 27 🆕 | Ativação de pack, lockfile, recusas |
| `tests/application/use_cases/test_baseline_gate.py` | 40 🆕 | Gate: carga, classificação, anotação, camadas e aborto |
| `tests/application/use_cases/test_baseline_summary.py` | 12 🆕 | Visão read-only do baseline para MCP/IDE |
| `tests/application/use_cases/test_calculate_risk.py` | 5 🆕 | Correlação de diff/achados/testes/histórico, degradação |
| `tests/application/use_cases/test_create_baseline.py` | 30 🆕 | Criação/atualização com proveniência e preservação de decisões |
| `tests/application/use_cases/test_generate_mentor_explanation.py` | 5 🆕 | Lotes, severidade, cache hit, chave ausente |
| `tests/application/use_cases/test_generate_pr_explanation.py` | 2 | Caso de uso do explain |
| `tests/application/use_cases/test_generate_test_file.py` | 4 | Caso de uso da geração de testes |
| `tests/application/use_cases/test_install_policy_pack.py` | 10 🆕 | Instalação de pack, origens e conflitos |
| `tests/application/use_cases/test_suppress_finding.py` | 29 🆕 | Supressão/remoção nos quatro escopos |
| `tests/application/use_cases/test_validate_policy_pack.py` | 23 🆕 | Validação: schema fechado, checksum, compatibilidade |
| `tests/badge/test_badge_append.py` | 9 | Append idempotente do selo ao corpo do PR |
| `tests/badge/test_badge_builder.py` | 19 | Composição do Markdown do shields.io, escape, regra de cor, estilo |
| `tests/badge/test_badge_cli.py` | 15 | Comando `gitpr badge`: snippet, `--readme`, `--style` |
| `tests/badge/test_badge_data.py` | 7 | Contagem de alertas; `None` sem regras configuradas |
| `tests/badge/test_badge_offline.py` | 6 | Guarda offline (rede proibida, exceto loopback) |
| `tests/badge/test_badge_optout.py` | 17 | `GITPR_BADGE=false` em todos os caminhos de publicação |
| `tests/badge/test_badge_paths.py` | 10 | Ponto único de injeção nos dois publicadores (TUI e `--no-edit`) |
| `tests/demo/test_demo_app.py` | 22 | TUI do tour: navegação, telas, modal de ajuda |
| `tests/demo/test_demo_isolation.py` | 14 | O tour não toca `~/.gitpr` nem a rede |
| `tests/demo/test_demo_runner.py` | 33 | Máquina de estados `DemoState`: avançar, voltar, concluído, modo texto |
| `tests/demo/test_demo_scenarios.py` | 47 | Integridade dos cenários gravados (aritmética de hunk) nos 5 idiomas |
| `tests/demo/test_demo_text_mode.py` | 18 | Saída em texto puro (`--no-tui`) para CI e gravações |
| `tests/demo/test_fake_ai_provider.py` | 21 | Contrato do provider falso: espelha `call_ai_model` argumento por argumento |
| `tests/domain/baseline/test_baseline_comparator.py` | 21 🆕 | Classificação, contagens de status, `resolved`→`new` |
| `tests/domain/baseline/test_baseline_fingerprint.py` | 12 🆕 | Digest dourado, linha crua nunca armazenada, estabilidade |
| `tests/domain/baseline/test_baseline_manifest.py` | 26 🆕 | JSON canônico, checksum, chaves desconhecidas, invariantes |
| `tests/domain/baseline/test_baseline_types.py` | 15 🆕 | Status persistidos, escopos e precedência |
| `tests/domain/baseline/test_suppression_policy.py` | 52 🆕 | Camadas, especificidade, overrides, dívida vencida |
| `tests/domain/finding/test_finding_types.py` | 3 🆕 | Tipo canônico do achado: `snippet_hash`, `rule_version` |
| `tests/domain/linter/test_sast_finding_mapper.py` | 2 | Formatação uniforme e deduplicação `[Gitleaks + Regex]` |
| `tests/domain/linter/test_structured_findings.py` | 44 🆕 | `findings_out`: achados estruturados e o contador de linha do lado novo |
| `tests/domain/mentor/test_mentor_explanation_builder.py` | 8 🆕 | Builder puro: honestidade epistêmica, URLs removidas, ordem preservada |
| `tests/domain/policy/test_policy_checksum.py` | 15 🆕 | SHA-256 do pack e detecção de edição manual |
| `tests/domain/policy/test_policy_compatibility.py` | 22 🆕 | Compatibilidade de versão e credencial |
| `tests/domain/policy/test_policy_manifest.py` | 42 🆕 | Schema fechado, bloco `baseline:`, erros de manifesto |
| `tests/domain/policy/test_policy_resolver.py` | 47 🆕 | Precedência, composição em camadas, pack ativo × base |
| `tests/domain/pr/test_explain_section_builder.py` | 4 | Renderização do Markdown, parsing tolerante, detecção de `[FILL]` |
| `tests/domain/risk/test_risk_calculator.py` | 5 🆕 | Fórmula 50/30/20, clamp 0–100, elevação obrigatória |
| `tests/domain/risk/test_risk_rules.py` | 5 🆕 | Pesos, limiares, glob de caminho crítico, YAML de override |
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
| `tests/infrastructure/baseline/test_local_baseline_repository.py` | 24 🆕 | Único leitor/escritor: escrita atômica, checksum, reparo |
| `tests/infrastructure/git/test_risk_history_reader.py` | 4 🆕 | `git log` seguro: commits, bugs e reverts em 90 dias |
| `tests/infrastructure/git/test_test_matcher.py` | 5 🆕 | Casamento teste ↔ produção por convenção |
| `tests/infrastructure/linter/external/test_bandit_bridge.py` | 3 | Bridge Bandit: disponibilidade, parsing, mapeamento |
| `tests/infrastructure/linter/external/test_base_bridge.py` | 4 | ABC: subprocess endurecido, timeout, binário ausente |
| `tests/infrastructure/linter/external/test_gitleaks_bridge.py` | 4 | Bridge Gitleaks: mascaramento de segredo, escopo por arquivo |
| `tests/infrastructure/linter/external/test_semgrep_bridge.py` | 3 | Bridge Semgrep: parsing JSON, severidade, pulo de não-Python |
| `tests/integration/test_baseline_effect_on_review_linter_risk.py` | 34 🆕 | Efeito real do baseline em review, lint e risk num repositório de verdade |
| `tests/integration/test_policy_effect_on_review_linter_risk.py` | 31 🆕 | Efeito real do pack em review, lint e risk (com guarda de rede autouse) |
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
| `tests/test_web_links.py` | 26 🆕 | (ver acima) |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (scaffold; nunca executado) |

**Total:** **2799 cenários coletados em 129 módulos de teste** (49 na raiz + 11 em `tests/application/use_cases/` + 10 em `tests/fix/` + 9 em `tests/scm/` + 7 em `tests/badge/` + 6 em `tests/demo/` + 6 em `tests/split/` + **5 em `tests/domain/baseline/`** 🆕 + **4 em `tests/domain/policy/`** 🆕 + 4 em `tests/review/` + 4 em `tests/infrastructure/linter/external/` + **2 em `tests/domain/risk/`** 🆕 + 2 em `tests/domain/tests_generation/` + **2 em `tests/integration/`** 🆕 + **2 em `tests/infrastructure/git/`** 🆕 + 2 em `tests/domain/linter/` + **1 em `tests/domain/finding/`** 🆕 + **1 em `tests/domain/mentor/`** 🆕 + 1 em `tests/domain/pr/` + **1 em `tests/infrastructure/baseline/`** 🆕; **+910 cenários e +33 arquivos** desde o relatório anterior).

**Notas de qualidade desta versão:**
- **✅ As 4 falhas da janela anterior foram fechadas, com as asserções intactas.** `SKILL_LABELS` passou de 8 para **11** entradas e `mcp_server.SKILL_FILES` de 8 para **11**; as **40 chaves `__()`** sem tradução foram resolvidas — o código usa 1603 e os dicionários têm 1603, **zero faltantes**. As três asserções que acusavam a dívida (`TestSkillsSection` ×2, `TestNoMissingKeys`, `TestSkillRegistryAgreement`) **continuam rodando e agora passam** — verificado nesta janela com `pytest tests/test_config_schema.py::TestSkillsSection tests/test_mcp_server.py::TestSkillRegistryAgreement tests/test_i18n.py::TestNoMissingKeys` → **11 passed**.
- **Crescimento de 910 cenários (+48%) em um único ciclo**, o maior salto já registrado neste projeto. `tests/test_metrics.py` sozinho passou de 34 para **164** cenários, e as três features novas com maior densidade de teste são o baseline (≈380 cenários somados), o policy (≈246) e o ledger.
- **O CI roda a suíte em Python 3.10 e 3.13** desde a janela passada, e `fail-fast: false` garante que uma falha de versão não esconda a outra.
- **Testes de integração entraram no repertório:** `tests/integration/` é novo e prova **efeito real** — um pack ativo e um baseline ativo mudam o review, o lint e o risk num repositório de verdade, com guarda autouse que bloqueia rede fora do loopback.
- **`tests/conftest.py` segue hermético:** `GITPR_SHOW_LOGS=false`, `GITPR_SKIP_UPDATE_CHECK=true`, `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false` e `LANG_VERSION` na versão do código.
- **Execução completa nesta máquina: `2 failed, 2795 passed, 2 skipped, 138 subtests passed in 520,46s (8min40s)`.** A suíte foi finalmente rodada de ponta a ponta nesta janela e o resultado é honesto: **2795 dos 2799 cenários coletados passam**. As **duas falhas não são regressão do produto** — são um bug de isolamento em `tests/test_mentor_cli.py`, e a causa raiz foi identificada e confirmada por experimento:
  - `TestMentorCli` faz `@patch("src.core.get_git_diff")`, mas `src/main.py` importa o nome **por valor** (`from src.core import … get_git_diff`), então o patch nunca alcança o binding que o fluxo realmente usa: a função **real** roda. O `get_git_diff()` real executa `git diff -U1 -w -M -B HEAD -- <59 smart excludes>`, e como a única alteração rastreada na árvore de trabalho durante a execução era o `CHANGELOG.md` — filtrado por `:(exclude)*.md` —, o diff volta com **0 bytes**, o fluxo cai no retorno antecipado de `main.py:1444` (`⚠️ Nenhum código novo encontrado`) com **exit code 0**, e a asserção `render_review_result.assert_called_once()` falha porque o renderizador nunca foi chamado.
  - **A prova:** repetindo os dois cenários com o patch apontado para `src.main.get_git_diff` (o binding correto), ambos se comportam exatamente como as asserções esperam — `--mentor` chama `_append_mentor_section` **e** o renderizador; sem `--mentor` o append **não** é chamado e o renderizador é. Ou seja: **os dois testes são dependentes do ambiente**, passando enquanto a árvore de trabalho tiver qualquer alteração que não seja `.md` (o que foi verdade durante todo o desenvolvimento das features) e falhando numa árvore só de documentação.
  - O código de produção está correto — o caminho `-r` chega a `render_review_result` (`main.py:1593`) como sempre chegou. **Correção recomendada:** trocar o alvo do patch para `src.main.get_git_diff` nos dois cenários (ou patchar `src.core` e o binding de `main` juntos).
- **Nenhuma das 4 falhas da janela anterior permanece:** elas eram de outra natureza (registro de skills e chaves `__()` sem tradução) e as asserções que as caracterizavam seguem rodando e passando.
- **Guarda de rede em dois lugares:** `tests/demo/conftest.py` (o tour não pode envenenar um cache real) e `tests/integration/conftest.py` (novo).
- **Fixtures de git real:** `tests/fix/git_fixture.py` e `tests/split/git_fixture.py` continuam sendo o padrão para o que só é honesto com o `git apply` de verdade.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** **1603 chaves** de tradução nos 6 dicionários, com **paridade total de key sets** — e, pela primeira vez em várias janelas, **paridade com o código também**: o código usa 1603 chaves e não há nenhuma sem tradução. ✅ (+445 nesta janela.) A cadeia medida por commit foi 1158 → 1161 (release notes, +3) → 1258 (ledger, +97) → 1288 (mentor, +30) → 1308 (docs do risk, +20) → 1437 (policy, +129) → **1603** (baseline, +166).
* **`__lang_version__` subiu v0.0.31 → v0.0.32 → v0.0.33 → v0.0.34**, disparando o re-download OTA das traduções — e desta vez o bump está **commitado** (`af35270`), não no working tree.
* **Fontes de tradução em lockstep:** uma chave nova precisa existir no código (fonte), em `langs/pt_br.json` (**lista mestra**), nos dicts FR/ES de `scripts/sync_all_langs.py` e nos valores curados de `scripts/fix_mangled_i18n_keys.py`; a asserção `len(CLEAN_KEYS)` segue em 49.
* **Tópicos novos 🆕 (4, todos em 5 idiomas):**
  - `docs/mentor-mode.md` — o Modo Mentor: o que ele ensina, as três garantias de honestidade epistêmica, os lotes de 10 e o opt-in.
  - `docs/risk-scoring.md` — o score determinístico: os sinais locais, a fórmula 50/30/20, as regras de elevação e o `gitpr.risk.yml`.
  - `docs/policy-packs.md` — os packs versionados: a escada de precedência, o lockfile que o time commita e as três falhas que abortam em vez de degradar em silêncio.
  - `docs/baseline-suppressions.md` — o baseline: os cinco status, por que só o `new` bloqueia, o que o fingerprint hasheia e o que ele deliberadamente deixa de fora, os quatro escopos de supressão e o bloco `baseline:` de um pack.
* **Tópicos traduzidos nesta janela (dívida paga) 🆕:** `docs/split-command.*.md` completou os 5 idiomas (+3: pt_pt, es_es, fr_fr) e `docs/otimizacao-de-tokens.*.md` também. **`review-pr` continua com 2 idiomas** — é a última família de feature parcialmente traduzida.
* **Tópicos atualizados nesta janela:** `docs/release-notes.*` (5 — reescrito para o corte ancorado no changelog e os links por forge), `docs/metricas-telemetria.*` (5 — reescrito para o ledger SQLite, com o vocabulário canônico de `glossary-metrics-telemetry.md`), `docs/mcp-integration.*` (5 — as tools e recursos novos), `docs/mcp-annotations.*` (5), `docs/ARCHITECTURE.*` (5) e `README.*` (5 — o índice ganhou as famílias `mentor-mode`, `risk-scoring`, `policy-packs` e `baseline-suppressions`).
* **Subdiretório `docs/extra/` 🆕:** duas famílias PT-only (`como_reverter_commit_git_localmente`, `testar_sem_usar_pypi`) foram **movidas** do topo de `docs/` para `docs/extra/` (`R100`, sem mudança de conteúdo) — material de apoio deixa de disputar a contagem de tópicos canônicos.
* **Documentação em 5 idiomas:** **46 tópicos canônicos** em `docs/` (+4 novos − 2 movidos) — **43 com cobertura completa nos 5 idiomas** 🆕 e apenas **3 tópicos parciais** (`github-issue-prompt-com-gh`, `version-markers`, `review-pr`), contra 7 na janela anterior. ✅
* **Lacuna de documentação que persiste 🆕:** `explain` e `tests` continuam sendo as **únicas** features sem tópico em `docs/` — ganharam o registro de skill e as chaves, mas não a página. As quatro features desta janela (mentor, risk, policy, baseline) já nasceram com doc em 5 idiomas, o que torna as duas exceções ainda mais visíveis.
* **Skills locais do Claude Code:** `.claude/skills/` com **29 skills** (contagem inalterada nesta janela).
* **Memory Index:** `.claude/memory/MEMORY.md` com **40 padrões** (contagem inalterada nesta janela).
* **Relatórios de tarefas:** `docs/claude-code/reports/develop_natan/` (**105** no total; **+4** — `2026-09-23_release_dedup_links.md`, `2026-09-29_metrics_telemetry_v2.md`, `2026-10-09_policy_packs.md`, `2026-10-10_baseline.md`) e `docs/gemini/reports/develop_natan/` (**14**; **+7**).
* **Relatórios de status:** `docs/reports/` (16 relatórios; este é o **17º**).
* **Planos de desenvolvimento:** 135 arquivos em `docs/plans/` (+20 na janela — specs/planos de release, métricas, risk, policy e baseline; **ADR-008 a ADR-012**; os glossários `metrics-telemetry`, `gitpr-mentor`, `gitpr-risk-scoring`, `policy-packs` e `baseline`; e o subdiretório novo `docs/plans/develop_natan/`) + **14 arquivos em `docs/survey/`** (+4).

---

## **🔄 Pipeline de Distribuição**

1. **PyPI (canal único):** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **Atualização obrigatória:** a execução verifica o PyPI no startup e **bloqueia com exit code 1** se houver versão mais nova, imprimindo `pip install --upgrade gitpr-cli`; a checagem é cacheada por dia e o `--update` apenas reporta
3. **GitHub Releases:** removido — sem PyInstaller, sem asset `.exe`, sem hot-swap
4. **GitHub Actions:** workflow `pr-review.yml` + `action.yml` (instala via pip) + `tests.yml` (matriz Python 3.10 e 3.13). **Continua faltando o workflow de release** — o build e o upload para o PyPI ainda são manuais.
5. **MCP Server:** entry point `gitpr-mcp` via `pyproject.toml`
6. **Templates e idiomas OTA:** `templates/` e `langs/*.json` servidos do GitHub (main) — o bump `v0.0.34` renova as cópias locais de `~/.gitpr/langs/` quando publicado; `__scripts_version__` **v0.0.4** renova os hooks (reinstalar com `gitpr --installhooks`)
7. **Versão derivada do código:** `pyproject.toml` usa `version = {attr = "src.updater.__version__"}` — o `__version__` é a **única** fonte
8. **`package-data` agora importa 🆕:** os quatro packs embutidos (`src/policy_packs/*`) viajam no wheel; um passo de build que os exclua produz um `gitpr policy list` que não enxerga os packs de fábrica
9. **Estado do release 🆕:** **`v1.3.0` tagueada** (2026-09-24, merge do PR #193) e **`v1.4.0` tagueada** (2026-10-12, merge do PR #207). O `CHANGELOG.md` tem as duas seções completas e linkadas — a `[1.4.0]` é a primeira gerada pelo motor corrigido. A única alteração em aberto no working tree é a correção dos cabeçalhos localizados da seção `[1.4.0]`, que saíram em pt-BR (`Funcionalidades`, `Documentação`, `Tarefas`, `Contribuidores`) e foram normalizados para o inglês.

---

## **📈 Evolução desde o Relatório Anterior (v0.0.16)**

| Área | v0.0.16 (anterior) | v0.0.17 (atual) |
|------|-------------------|-----------------|
| **Versão GitPR** | 1.3.0 (bump **não commitado**; HEAD em 1.2.0) — tag `v1.2.0` | **1.4.0** — **tags `v1.3.0` (24/09) e `v1.4.0` (12/10) criadas** ✅ |
| **Versão Idioma** | v0.0.32 (bump **não commitado**) | **v0.0.34** (v0.0.32 → v0.0.33 → v0.0.34, **commitado**) |
| **Versão Scripts Hook** | v0.0.3 | **v0.0.4** (templates de hook reescritos para o ledger) |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama (inalterado) |
| **Idiomas** | 5 idiomas, 6 dicionários | 5 idiomas, 6 dicionários |
| **Subcomandos** | 9 | **14** (+ `mentor`, `metrics`, `policy`, `risk`, `baseline`) — **4 deles são grupos** (baseline 6, metrics 8, policy 7, tests 1) |
| **Interface** | CLI + TUIs + wizards + 9 subcomandos | **+ `gitpr mentor`/`--mentor` + grupo `metrics` (com assistente de migração) + `gitpr policy` + `gitpr risk` + `gitpr baseline`** |
| **Camadas** | `src/domain/` e `src/application/use_cases/` | **8 pacotes de domínio** (+ `baseline`, `finding`, `mentor`, `policy`, `risk`) e **14 casos de uso** |
| **Persistência local 🆕** | — | **`src/ledger.py`** — SQLite em `~/.gitpr/metrics/telemetry.db` (WAL, `user_version`, UUID, bundle/merge) |
| **Ferramentas MCP** | 14 tools / 18 recursos / 7 prompts (`skill://explain` e `skill://tests` **faltando** ⚠️) | **16 tools / 19 recursos / 7 prompts** ✅ (+`get_usage_metrics`, +`get_baseline_status`, +`baseline://summary`; registries de skill alinhados) |
| **Flags CLI** | 36 na raiz + 9 subcomandos | **32 na raiz** (−5 métricas, +`--mentor`) + **14 subcomandos** com 22 subcomandos de grupo |
| **Variáveis de Ambiente** | 49 chaves no `DEFAULT_CONFIG` | **58 chaves** (+9: 4 baseline, 2 mentor, 2 policy, 1 risk) + `GITPR_METRICS_PRICE_*`/`CURRENCY` |
| **Schema de Config** | 71 `ConfigField` / 14 categorias | **80 `ConfigField` (+9) / 16 categorias** (+ Policy, + Baseline) |
| **Linter** | Regex + segredos embutidos + wildcard + 3 bridges SAST | **+ achados estruturados (`findings_out`) + tipo canônico `src/domain/finding/` + severidade pelo Policy Pack + exit code baseline-aware** |
| **Hooks Git** | pre-commit bloqueia segredos | **+ post-checkout/post-merge/pre-push chamam `gitpr --quiet metrics hook-event`** (resolução de repo em bash, só-GitHub, removida) |
| **Camada SCM** | 4 forges, `get_pull_request`, `supports_reviewable_diff` | **+ `list_pull_requests` paginado e canônico, `supports_merged_dates`, `within_window()`, `web_links.py` (links por forge)** — 305 cenários |
| **Release engine** | Range por `git describe`, sem links | **Range ancorado na seção anterior do changelog, `_drop_released()`, links de commit/PR/contribuidor, mapa de PR por merge commit** |
| **i18n (chaves por arquivo)** | 1158 × 6 — código usa 1198 → **40 sem tradução** ⚠️ | **1603 × 6 — código usa 1603 → zero sem tradução** ✅ (+445) |
| **Documentação** | 44 tópicos (37 completos + 7 parciais) | **46 tópicos (43 completos + 3 parciais)** — 4 famílias novas em 5 idiomas + 2 dívidas de tradução pagas + `docs/extra/` |
| **CI** | `.github/workflows/tests.yml` (3.10 + 3.13) | Inalterado (o workflow de **release** continua pendente) |
| **Suíte de Testes** | 1889 cenários (96 arquivos) | **2799 cenários (129 arquivos) — +910 cenários, +33 arquivos** (maior salto já registrado) |
| **Falhas conhecidas** | 4 (registro de skills pela metade, uma causa raiz) | **2** — as 4 da dívida **fechadas** ✅; restam 2 em `tests/test_mentor_cli.py`, de **isolamento de teste** (patch em `src.core` que não alcança o binding de `src.main`), sem regressão de produto |
| **Dependências** | — | **+ `packaging>=23.0`** (SemVer/PEP 440 do Policy Pack) |
| **Commits desde o relatório** | 8 commits | **11 commits** (`c561664`, `64a406f`, `4380ce8`, `811651f`, `57c5140`, `c46440f`, `e1cfb11`, `4d42d56`, `8450186`, `af35270`, `1abb1b5`) |
| **PRs mergeados** | 7 PRs (#177–#189) | **10 PRs (#192, #193, #194, #196, #198, #200, #201, #203, #205, #207)**; 6 issues fechadas (#191, #197, #199, #202, #204, #206) |
| **Memory Index** | 41 padrões | **40 padrões** (inalterado nesta janela) |
| **Relatórios de tarefas** | 101 claude-code, 7 gemini | **105 claude-code (+4) e 14 gemini (+7)** |
| **Planos de desenvolvimento** | 115 planos, 10 surveys | **135 planos (+20), 14 surveys (+4)** — inclui ADR-008 a ADR-012 |

---

## **🚧 Próximos Passos**

* **Corrigir o isolamento de `tests/test_mentor_cli.py` 🆕:** são as **duas únicas falhas** da suíte hoje. O patch aponta para `src.core.get_git_diff`, mas `src/main.py` importa o nome **por valor** — a função real roda, e numa árvore cuja única alteração é um `.md` (filtrado por `:(exclude)*.md` nos smart excludes) o diff volta vazio e o fluxo retorna antes do renderizador. Repetido com o patch em `src.main.get_git_diff`, os dois cenários passam. É uma correção de duas linhas que fecha a suíte em **2797/2799**.
* **Commitar a correção do `CHANGELOG.md` 🆕:** os cabeçalhos de seção da `[1.4.0]` saíram localizados (pt-BR) e foram normalizados para o inglês **no working tree**. É a única alteração em aberto no repositório — e o pacote publicado já carrega a versão em português no arquivo versionado.
* **Documentar `explain` e `tests`:** são, agora, as **duas únicas** features sem tópico em `docs/` — todas as quatro que chegaram nesta janela nasceram documentadas em 5 idiomas. **Item herdado da janela anterior e ainda aberto.**
* **Automatizar o release no GitHub Actions 🆕:** o CI de testes existe há duas janelas, mas o build e o upload para o PyPI continuam manuais — e nesta janela o passo manual foi feito **duas vezes** (v1.3.0 e v1.4.0). Um workflow de release com gatilho em tag fecha o último trecho manual do pipeline.
* **Estender a cobertura do ruleset de segredos:** as três lacunas continuam abertas e foram **reconfirmadas no código nesta janela** — atribuição sem aspas (`API_KEY=abc123`, o formato `.env`, que é justamente onde segredos vazam), os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-`, e a ausência de fronteira à esquerda no nome da chave (hoje `mytoken` casa igual a `token`).
* **Traduzir `docs/review-pr.*.md` 🆕:** é a **última** família com cobertura parcial (2 de 5 idiomas). `split-command` e `otimizacao-de-tokens` foram pagas nesta janela.
* **Destrackear os artefatos de `.gitpr/metrics/export/` 🆕:** o `.gitpr/metrics/` entrou no `.gitignore` nesta janela — mas os **35 arquivos já rastreados continuam rastreados**, porque `gitignore` não destrackeia. Falta um `git rm --cached` único. **A dívida parou de crescer, mas não foi quitada.**
* **Documentar a quebra de contrato do `request_pull_request_reviewers`:** passou de `None` para `list[str]`; subclasses de terceiros de `ScmProvider` precisam ser atualizadas. `docs/scm-multiforge.*.md` é o lugar, nas 5 versões. **Item herdado, ainda aberto.**
* **Mapear o blast radius do baseline no exit code 🆕:** um baseline que não pode ser aplicado agora **aborta** lint, review, full review, auditoria de arquivo, review remoto e risk com exit code 1. É a escolha segura, mas é uma mudança de comportamento em **seis** fluxos — vale um `docs/baseline-suppressions` explicitando o contrato de saída para pipelines de CI.
* **Reconciliar a versão do projeto:** `CLAUDE.md` ainda diz `Current version: 0.0.37` enquanto o `__version__` está em **1.4.0**. Definir uma convenção única. **Item herdado, ainda aberto.**
* **`gitpr -h config` ignora o `-h`:** o subcomando abre a TUI em vez de mostrar a ajuda — o gate `if ctx.invoked_subcommand is not None: return` roda antes do bloco de `help_flag`. Corrigir mudaria o comportamento de `-h` para **todos** os subcomandos, então precisa de decisão. **Item herdado, ainda aberto.**
* **Migrar o extrator do `sync_i18n.py` para AST:** o regex trunca literais com concatenação implícita (`__("a " "b")`). **Progresso parcial 🆕:** `tests/test_i18n.py` já usa um extrator baseado em AST (`_extract_keys_ast`) e é ele que hoje verifica a cobertura; o script de sincronização continua no regex.
* **Seção Smart Exclude na TUI:** dos 12 itens reportados após o uso da tela, o item 10 (*Smart Exclude*) é a única entrega ainda não iniciada — e os campos `GITPR_SMART_EXCLUDES_*` seguem sob `diff`, sem categoria própria.
* **Dívidas registradas no plano do config TUI:** `DEFAULT_CONFIG` ficou redundante com o schema; o banner de abertura não lista `--init`, `--base` nem `--plugins` (o `--dashboard` saiu do CLI, então essa parte do item ficou obsoleta 🆕); o `LinterApp` é o **único** app Textual que ainda não desabilita a command palette.
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Histogramas de tempo e tendências de tokens na TUI de métricas — o dashboard já lê o ledger, que é o pré-requisito que faltava.
* **Seed de `.gitpr/conf/` local:** O seed de templates de configuração local (smart-excludes, linter) continua pendente como subcomando próprio ou etapa do wizard.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.

### ✅ Concluídos nesta janela (2026-09-23 → 2026-10-12)

* ~~**Fechar a dívida das duas features novas**~~ — `SKILL_LABELS` (8 → **11**) e `mcp_server.SKILL_FILES` (8 → **11**) receberam `tests`, `explain` e `mentor`; as **40 chaves `__()`** sem tradução foram resolvidas e a cobertura chegou a 1603/1603. **As 4 falhas viraram 0, com as asserções intactas.**
* ~~**Fechar o release 1.3.0**~~ — tag **`v1.3.0`** criada (merge do PR #193, 2026-09-24) e o `CHANGELOG.md` completado com as seis features que faltavam. **Era o item que bloqueava duas janelas.**
* ~~**Fechar o release 1.4.0**~~ 🆕 — tag **`v1.4.0`** criada (merge do PR #207, 2026-10-12), com os três bumps (GitPR, idiomas, scripts) **commitados** e não mais no working tree.
* ~~**`gitpr release` repete o histórico e não tem links**~~ 🆕 — corte ancorado na seção anterior do changelog, `_drop_released()`, links de commit/PR/contribuidor, mapa de PR por merge commit e `web_links.py` (PR #192).
* ~~**Telemetria em JSON com `tokens_actual` sempre zero**~~ 🆕 — ledger SQLite com escrita síncrona, tokens copiados na escrita, grupo `gitpr metrics`, assistente de migração e custo por modelo (PRs #194/#196).
* ~~**Modo Mentor**~~ 🆕 — `src/domain/mentor/`, caso de uso, `gitpr mentor` + `--mentor`, skill em 5 idiomas (PR #198).
* ~~**Score de risco determinístico**~~ 🆕 — `src/domain/risk/`, `calculate_risk`, leitores de histórico e de testes, `gitpr risk` e seção anexada ao review (PR #200).
* ~~**Policy Packs**~~ 🆕 — `src/domain/policy/`, `src/infrastructure/policy/`, 4 packs embutidos, grupo `gitpr policy` e dependência `packaging` (PR #203).
* ~~**Baseline e supressões auditáveis**~~ 🆕 — `src/domain/baseline/`, `src/domain/finding/` canônico, gate nos seis fluxos, tool e recurso MCP (PR #205).
* ~~**Traduzir os tópicos parciais**~~ — `docs/split-command.*.md` e `docs/otimizacao-de-tokens.*.md` completaram os 5 idiomas.
* ~~**`.gitpr/metrics/` fora do controle de versão**~~ — entrou no `.gitignore` com comentário explicando o que **não** é ignorado (`.gitpr/skill/`) e por quê.
* ~~**Higiene do `docs/`**~~ — duas famílias de material de apoio (`como_reverter_commit_git_localmente`, `testar_sem_usar_pypi`) foram movidas para `docs/extra/`, tirando-as da contagem de tópicos canônicos.
* ~~**Hooks que só funcionavam no GitHub**~~ — `post-checkout`, `post-merge` e `pre-push` passaram a delegar ao próprio GitPR, com `__scripts_version__` em v0.0.4.

---

**Relatório gerado em:** 2026-10-12  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
