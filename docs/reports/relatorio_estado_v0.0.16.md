# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.16 (2026-09-23)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.16):**
- **`gitpr demo` — a primeira execução deixou de ser um ato de fé:** Um tour guiado que mostra mensagem de commit, review e descrição de PR **sem chave de API, sem repositório git e sem rede**. A pergunta que ele responde ("o que essa ferramenta faz?") só tem uma janela para ser feita — o primeiro uso, antes de o usuário ter configurado um provedor. O tour roda pelo **pipeline real de geração** com a fonte da resposta trocada, então o que aparece é o que a ferramenta de fato produz, enquanto todo efeito externo (cache, métricas, disco, rede, leitura de chave) é neutralizado.
- **Selo GitPR no corpo do PR + comando `gitpr badge`:** Um PR escrito por IA era indistinguível de um escrito à mão, e o resultado do linter morria num terminal que rolou para fora da tela. O selo transforma esse sinal privado numa afirmação visível no próprio PR publicado — e é deliberadamente uma URL estática do shields.io, que o GitPR **nunca** busca, para que publicar um PR não passe a depender de um terceiro estar no ar. Medição honesta: sem regras de linter configuradas o selo **não** é emitido, porque lista vazia significa "nada foi verificado", não "nada foi encontrado".
- **`gitpr split` — uma árvore de trabalho com várias intenções deixa de virar um commit-blob:** Lê o diff não commitado, pede à IA que particione os hunks por intenção lógica e propõe **um commit atômico por concern**, cada um com mensagem gerada a partir do patch daquele grupo isolado. A árvore nunca é reescrita: os arquivos terminam byte a byte iguais ao início — só o histórico muda. *(O índice, sim: o `--apply` reseta para HEAD antes de stagear.)*
- **Varredura de segredos embutida — a regra que não pode ser sobrescrita:** Sete regras (`src/security_ruleset.py`) que rodam em **toda** invocação do linter: cinco `error` bloqueantes (AWS key ID, token GitHub/Slack, chave Google, bloco de chave privada) e dois `warning`. O catálogo local era inteiramente gerenciado pelo usuário — podia ser sobrescrito pelo download, reescrito pelo wizard (perdendo comentários) ou estendido só por plugins da máquina. Um portão de segredos precisa se comportar igual em toda máquina, então as regras passaram a viver **dentro do pacote**. **Mudança de comportamento: um commit que passava pode agora ser bloqueado.**
- **Suporte a `extensions: ["*"]`:** Agora significa *todo* arquivo, incluindo os sem sufixo — que é exatamente de onde segredos vazam (`id_rsa`, `.env`, `credentials`, `Dockerfile`). Uma regra com `extensions: ["py"]` mantém o filtro exatamente como antes.
- **Bridges SAST opt-in — Semgrep, Gitleaks e Bandit:** Uma camada que pluga scanners de segurança de terceiros no linter existente. Rodam **só** quando habilitados, **só** sobre os arquivos tocados pelo diff, e os achados são deduplicados contra o ruleset interno: um segredo visto pelos dois aparece **uma vez** com marcador de confirmação multi-fonte (`[Gitleaks + Regex]`). O Gitleaks tem os valores mascarados (`AKIA****`) antes de virar achado.
- **`gitpr tests generate` — a suíte que respeita a convenção do repositório:** Gera arquivos de teste completos a partir do diff, de um arquivo específico ou de um achado de review. Detecta o framework em uso (Pest, PHPUnit, Jest, Vitest, Pytest) em vez de impor um estilo, calcula o caminho convencional de destino (o split `Feature`/`Unit` do Laravel, o `tests/**/test_*.py` do Pytest) e valida a sintaxe com o toolchain local (`php -l`, `node --check`, `python -m py_compile`) — falha de validação vira aviso, não erro. Dry run é o default.
- **`gitpr explain` + flag `--explain` — o guia de quem vai revisar:** Um guia centrado no revisor (o que muda, por que muda, onde focar, qual o risco de regressão) para que ninguém tenha que reconstruir a intenção a partir de um diff cru. Disponível como subcomando próprio e como flag que anexa a seção à descrição do PR gerada.
- **Arquitetura em camadas — `src/domain/` e `src/application/`:** As duas últimas features (`tests` e `explain`) nasceram com separação explícita entre regra de domínio pura e orquestração de caso de uso, e o CLI e a TUI de chat passaram a compartilhar **o mesmo** caso de uso em vez de duplicá-lo.
- **Suíte determinística e o primeiro CI:** `tests/conftest.py` ficou hermético (pina `GITPR_LANG=en_us` e desliga o ruleset de segredos) e o `.github/workflows/tests.yml` roda a suíte em **Python 3.10** (o piso declarado, nunca exercitado) e 3.13. Foi o CI que tornou visível o drift de locale — **22 testes** falhavam numa máquina pt-BR por asserir o literal em inglês.
- **As 3 falhas herdadas de três relatórios seguidos foram fechadas:** os dois testes de timeout desatualizados (`600s` vs. o default real de `180s`) e o teste sensível ao locale. A linha de base da suíte deixou de ser "3 falhas conhecidas" e passou a ser **verde por construção**.
- **Dívida nova e concentrada:** as duas features mais recentes (`tests` e `explain`) entraram com o registro de skills **pela metade** — **40 chaves `__()`** usadas no código não existem em nenhum dos 6 dicionários, e os registries de rótulos do config e do MCP não receberam os tipos novos. São **4 falhas** na suíte completa, todas com a mesma causa raiz.
- **Estado do release 1.3.0:** o `__version__` e o `__lang_version__` estão no **working tree e não commitados** (HEAD segue em 1.2.0 / v0.0.31), o `CHANGELOG.md` **tem** a entrada `[1.3.0] - 2026-09-21` — mas ela cobre **apenas** a varredura de segredos, e não `demo`, `badge`, `split`, SAST, `tests` nem `explain`. A tag `v1.2.0` **foi criada** (merge do PR #174), fechando o item que bloqueava a janela anterior.

- **Versão atual:** 1.3.0 (bump no working tree — HEAD em 1.2.0; última tag `v1.2.0`)
- **Versão dos dicionários de idioma:** v0.0.32 (bump no working tree — HEAD em v0.0.31)
- **Versão dos scripts de hook:** v0.0.3
- **Publicação:** PyPI (`pip install gitpr-cli`) — canal binário removido
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal) — **9 subcomandos** 🆕 (`badge`, `config`, `demo`, `explain`, `fix`, `release`, `review-pr`, `split`, `tests`).
* **UI/Terminal:** Textual — TUI para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher, erros do linter (`LinterApp`), configuração (`ConfigApp`), modal `NoticeScreen` e o **tour do `gitpr demo`** (`src/ui/demo/`) 🆕.
* **Arquitetura em Camadas 🆕:** `src/domain/` (regra pura, sem I/O) + `src/application/use_cases/` (orquestração) + apresentação (CLI/TUI). Introduzida com `tests` e `explain`; o CLI e o chat `/tests` chamam **o mesmo** caso de uso.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API, tokens GitHub e tokens SCM das forges.
* **Configuração:** `python-dotenv`, `pyyaml` (linter estático) + schema declarativo próprio (`src/config_schema.py`, **71 `ConfigField`** 🆕).
* **IA Providers:** Integração via SDK oficial do Google GenAI (`gemini-2.5-flash`), OpenAI SDK (`DeepSeek`) e OpenAI SDK (`Ollama` local).
* **Forge APIs:** `requests` (REST) — abstração multi-forge em `src/infrastructure/scm/` (GitHub, GitLab, Bitbucket, Azure DevOps); `src/github_api.py` mantido como shim deprecado.
* **Linter / SAST 🆕:** regex YAML + bridge Checkstyle + **ruleset de segredos embutido** (`src/security_ruleset.py`) + **4 bridges em `src/infrastructure/linter/external/`** (base + Semgrep, Gitleaks, Bandit), com modelo normalizado em `src/domain/linter/sast_finding_mapper.py`.
* **Git Internals 🆕:** `src/infrastructure/git/` — `patch_applier.py` (movido de `src/fix/`) e `selective_stager.py` (staging de subconjunto arbitrário de hunks).
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 — **14 ferramentas anotadas, 18 recursos, 7 prompts** (contagem inalterada nesta janela).
* **Testes:** Pytest + `unittest.mock` (**96 módulos de teste — 44 na raiz, 9 em `tests/scm/`, 10 em `tests/fix/`, 6 em `tests/split/`, 6 em `tests/demo/`, 7 em `tests/badge/`, 4 em `tests/review/`, 4 em `tests/infrastructure/linter/external/`, 2 em `tests/domain/tests_generation/`, 2 em `tests/application/use_cases/`, 1 em `tests/domain/pr/`, 1 em `tests/domain/linter/`** 🆕 —, **1889 cenários coletados**) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio) + fixtures de repositório git real (`tests/fix/git_fixture.py`, `tests/split/git_fixture.py`) + **guarda de isolamento de rede** (`tests/demo/conftest.py`).
* **Empacotamento:** setuptools/build (PyPI) — `version = {attr = "src.updater.__version__"}`.
* **CI/CD:** GitHub Actions — `pr-review.yml` + `action.yml` + **`tests.yml`** 🆕 (matriz Python 3.10/3.13).

---

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa ~90k tokens, divide automaticamente em lotes por arquivo (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce). Suporta PRs, commits e Issues.
* **Tokenizador Local:** `tokenizer.json` para estimativa precisa de tokens antes do envio para a IA.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()` com fallback para tokenizador local.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff` para reduzir contexto inútil.
* **`get_split_diff()` 🆕:** Diff próprio do `split`, com `SPLIT_DIFF_ARGS` (`--binary -M -U3`), **deliberadamente sem** reusar `get_git_diff()` — o `-w` (ignora whitespace) e os smart-excludes quebrariam a garantia de árvore byte-idêntica, porque o patch reconstruído tem que bater com o arquivo em disco.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo (system instruction + prompt) em JSON antes de cada chamada à IA.
* **Smart Excludes com Duas Camadas:** Camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`), mescladas em runtime. Auto-seeding do arquivo local na primeira execução. `_load_smart_excludes()` aceita `force=`.
* **Métricas com Rastreamento de Tempo:** `log_command_metric()` em todos os fluxos com `duration_ms` e lazy imports.
* **Resolução Centralizada de Output:** `resolve_output_path()` — default em `.gitpr/reports/{type}/`.
* **Wizard SCM (`run_scm_init_wizard()`)**: `gitpr --init` — detecta a forge pelo remote origin, solicita extras por forge, valida o token e persiste **somente em sucesso**. 🆕 Anuncia o selo automático no caminho de PR e informa o switch exato que o desliga.
* **Skill Template de Release (`ensure_release_skill_template()`)**: Baixa `templates/gitpr.release.*.md` no primeiro uso de `gitpr release`.
* **Registro de Skills Compartilhado:** `SKILL_FILES_BY_TYPE` / `SKILL_TYPES` / `DEFAULT_SKILL_TYPE` em `src/config.py`. 🆕 Ganhou entradas para `tests` (`.gitpr.tests.md`) e `explain` (`.gitpr.explain.md`).
* **Motor de Review com Escopo de Cache (`generate_pr_content`):** `cache_scope` (anexado **só à chave de cache**) e `store_diff` (grava o diff revisado). Defaults mantêm o caminho local byte-idêntico.
* **Trailer de Coautoria:** `COAUTHOR_TRAILER` + `append_coauthor_trailer()` — idempotente, preserva trailers de terceiros.
* **Subprocessos Blindados:** `stdin=subprocess.DEVNULL` + `encoding='utf-8'`/`errors='replace'` em todos os `subprocess.run`; verificação de conexão via socket `8.8.8.8:53` antes de operações de rede.

### **2. Sistema de Plugins Global (`src/plugins.py`)**

* **Arquitetura de Plugins:** Carrega plugins de `~/.gitpr/plugins/` aplicando-se a **todos os projetos**.
* **Plugins de Linter (`linter/`):** Arquivos `.yml` mesclados com o `.gitpr.linter.yml` local.
* **Plugins de Prompt MCP (`prompts/`):** Arquivos `.md` que estendem o contexto do sistema.
* **Factory Closures:** `get_linter_plugins` e `get_prompt_plugins` isolam estado entre sessões.
* **Comando `--plugins`:** Lista todos os plugins globais instalados com tipos e paths.
* **Documentação Multilíngue:** `docs/plugins-system.md` em 5 idiomas.

### **3. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria `~/.gitpr/` e solicita interativamente chaves, preferências e idioma. 🆕 A dica de primeira execução aponta para `gitpr demo`.
* **Routing de Comandos:** Gerencia todas as flags e os **9 subcomandos** — `release`, `config`, `fix`, `review-pr`, **`demo`** 🆕, **`badge`** 🆕, **`split`** 🆕, **`tests`** 🆕 (grupo, com `generate`) e **`explain`** 🆕.
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags (agora 36 opções Click na raiz, +1 nesta janela):**
  * **`--explain` 🆕:** Inclui a seção *Reviewer Guide* na descrição do PR (e no payload JSON emitido).
  * `--init`, `--no-suggest-reviewers`, `--no-publish`, `--no-edit`, `--base <branch>`, `--plugins`, `--linter-setup`, `--version` — inalteradas.
* **Subcomando `demo` 🆕 — 3 opções:** `--scenario`, `--lang` e `--no-tui` (front-end em texto puro para CI e gravações). O `--lang` é aplicado **dentro** do subcomando, porque o callback raiz retorna antes do handler.
* **Subcomando `badge` 🆕 — 2 opções:** `--readme` (forma nua do snippet, amigável a pipe) e `--style` (`flat`/`flat-square`/`for-the-badge`). **Só imprime** — o README nunca é modificado.
* **Subcomando `split` 🆕 — 5 opções:** `--dry-run`, `--apply`, `--yes`, `--max-groups` e `--provider`. A invocação nua imprime o plano e pergunta antes de commitar qualquer coisa.
* **Grupo `tests` 🆕 → subcomando `generate` — 5 opções:** `--file`, `--finding`, `--framework`, `--apply` e `--provider`. Dry run é o default e sobrescrever um teste existente pede confirmação com **No** pré-selecionado.
* **Subcomando `explain` 🆕 — 1 opção:** `--provider`. Detecta ausência de diff com erro claro antes de qualquer chamada de IA.
* **Variáveis de Ambiente (49 chaves no `DEFAULT_CONFIG`, +5 nesta janela):** `GITPR_LINTER_SECURITY`, `GITPR_LINTER_SECURITY_DISABLED_RULES` e as três `GITPR_SPLIT_*` (`MAX_GROUPS`, `MAX_HUNKS`, `REQUIRE_CONFIRMATION`). **Outras 5 são read-only / não semeadas:** `GITPR_BADGE` (default `true`), `GITPR_EXPLAIN_BY_DEFAULT` (default `false`) e as três `GITPR_SAST_*_ENABLED` — o GitPR **nunca** as escreve sozinho no `~/.gitpr/.env`.
* **Ajuda Contextual:** `-h --flag` exibe documentação específica com link language-aware. Subcomandos têm `epilog=` próprio (parágrafo `\b` do Click para a URL não ser reembrulhada sob nenhum locale). 🆕 `explain` entrou em `HELP_MAP`/`HELP_PRIORITY`.
* **--lang / --provider / --mcp / --install / --metrics / --status** — inalteradas.
* **Camada de escrita do `.env`:** `read_env_file_values()` lê **só o arquivo** via `dotenv_values`; `save_config_values()` com `set_key`; `remove_config_value()` com `unset_key`. `validate_ai_key()` distingue credencial recusada (`401`/`403`) de rede inalcançável.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI para revisar, editar e publicar Pull Requests direto no terminal.
* **7 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen` e `NoticeScreen`.
* **Selo no Corpo do PR 🆕:** `attach_pr_badge()` roda em `src/main.py` logo após `pr_data` estar completo — **ponto único de injeção**, então os dois publicadores (a área de texto da TUI e o `--no-edit`) leem o selo do mesmo lugar. O usuário **vê** o selo e pode apagá-lo antes de enviar; o `--no-edit` imprime uma linha dizendo o que foi para o corpo que ele não viu. Append idempotente por marcador — republicar ou mover o selo não empilha selos.
* **`_attach_reviewers` com resolução:** Resolve o que o usuário digitou **antes** de enviar, reporta o descartado e, num `422` de lote, **repete um a um** — o GitHub rejeita o lote inteiro quando um único login é inelegível.
* **Suggested Reviewers:** Consulta a forge por revisores sugeridos; `_reviewer_suggestion_view()` monta `resolutions` via `resolve_candidates` e pré-preenche `handles`.
* **Bindings:** F1 (Help), F2 (Salvar .md local), F3 (Publicar via forge), Esc (Sair).
* **Fluxo de Auto-Commit:** Linter → mensagem IA → confirma → commita → push → publica PR.
* **Verificação de Arquivos Unstaged:** `git status --porcelain` na entrada, com modal para selecionar, pular ou cancelar.
* **Tratamento de PR Existente / Auto-Upstream / Merge Flow** — inalterados (`GITPR_AUTO_MERGE`).

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Shim Deprecado:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` e demais funções delegam a `src/infrastructure/scm/github_provider.py`; emite `DeprecationWarning` e mantém as tuplas legadas `(ok, data, status)` — nenhum código novo pode importá-lo.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no diff sem gastar cotas de IA.
* **Regras YAML:** Lê `.gitpr.linter.yml` (criado via `--skill`).
* **Plugins de Linter:** Regras adicionais de `~/.gitpr/plugins/linter/*.yml`.
* **Wildcard de Extensão 🆕:** `extensions: ["*"]` passa a significar **todo** arquivo, inclusive os sem sufixo e dotfiles. É o que dá cobertura a `id_rsa`, `.env`, `credentials` e `Dockerfile`; uma regra com `extensions: ["py"]` mantém o filtro como sempre foi.
* **Ruleset de Segredos Embutido 🆕:** `load_linter_rules()` mescla `src/security_ruleset.py` **depois** das regras do projeto e dos plugins, que ficam intocados — só a ordem muda, jogando os alertas de segurança para o fim do relatório. Sete regras, todas `extensions: ["*"]`: cinco `error` (AWS key ID, token GitHub/Slack, chave Google, bloco de chave privada) e duas `warning` (URL de banco com credenciais e atribuição genérica de credencial, atrás de um filtro de placeholder).
* **O Alerta Nunca Ecoa o Valor:** A mensagem carrega só `{file_name}` e `{line_number}` — ela viaja para o console, para o relatório Markdown e, no fluxo de PR, para o corpo de um pull request público; imprimir o segredo o copiaria nos três.
* **`--input` Ampliado 🆕:** A auditoria de arquivo inteiro passou a varrer `.md`, `.txt` e lockfiles, já que o ruleset casa toda extensão. Ali **reporta sem bloquear** — o `sys.exit(1)` existe só no caminho `--linter`.
* **Bridges SAST Opt-In 🆕:** Semgrep, Gitleaks e Bandit rodam no caminho de arquivo inteiro **e** no de diff, filtrando achados por linhas adicionadas e avisando quando a ferramenta está habilitada mas fora do `PATH`. `load_sast_config()` resolve em três camadas: defaults → `.gitpr.linter.yml` (bloco `sast`, caindo para `linter.external`) → variáveis `GITPR_SAST_*`. **Tudo default `false`** (opt-in estrito).
* **`skip_external`:** `parse_diff_and_lint(..., skip_external=False)` desliga os **dois** call-sites do bridge externo; o fluxo remoto passa `True`, porque o bridge roda binários contra arquivos em disco — a árvore local, não o PR.
* **Relatório Consolidado:** `generate_linter_report_content()` consolida erros regex + externos em `.gitpr/reports/linter/` — gerado apenas quando há violações.
* `load_linter_presets()` aceita `force=` para re-download a partir da TUI.

### **7. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera a chave mestra `secret.key` em `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data`/`decrypt_data` para chaves de IA, GitHub PAT e tokens SCM das forges.
* **Validação Multi-Forge:** `validate_or_request_scm_token(provider, repo_display)` — 401 → loop de reautenticação preservando o rascunho; o token GitHub legado permanece funcional até o `--init` rodar.
* **Segredos na TUI de Configuração:** Campos `KIND_SECRET` são editados mascarados, **nunca** exibem o valor em claro e são cifrados com Fernet antes de gravar. `GITPR_SCM_TOKEN` é `read_only`.
* **Varredura de Segredos no Próprio Fluxo 🆕:** O linter — que roda no pre-commit hook — passou a ser um portão de credenciais com regras idênticas em toda máquina, porque vivem no pacote e não num template baixado que o `--skill` ou o wizard podem substituir.

### **8. Auto-Updater (`src/updater.py`)**

* **PyPI como Fonte Única:** `get_latest_remote_version()` consulta `https://pypi.org/pypi/gitpr-cli/json` e grava o cache diário **sem** o campo `download_url`.
* **Portão Obrigatório (`enforce_update_required()`):** Devolve `True` (após imprimir as duas versões e o comando pip) quando a versão publicada é mais nova; `False` quando está atualizado, quando a versão remota é **desconhecida (offline)** ou quando a checagem está desligada. Devolver `bool` em vez de chamar `sys.exit` internamente mantém a função testável.
* **`check_and_update()`:** Só consulta e **informa**, nunca instala.
* **Escape Hatch:** `GITPR_SKIP_UPDATE_CHECK` — não é advertised; existe para a suíte e automação offline.
* **Versionamento Centralizado:** `__version__` (**1.3.0** — bump no working tree), `__lang_version__` (**v0.0.32** — cadeia v0.0.28 → v0.0.29 → v0.0.30 → v0.0.31 → v0.0.32 nesta janela 🆕), `__scripts_version__` (**v0.0.3**), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION`.

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico persistido por branch, com continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear`. 🆕 O `/tests` (e os aliases localizados `/testes`, `/pruebas`) **deixou de ser encaminhado ao modelo genérico** e passou a delegar ao **mesmo caso de uso** que o CLI usa (`TestGenerationTarget`), em vez de duplicar a lógica.
* **Auto-Patching (F5), Atualização de Diff (F2), Exportação de Sessão (F6).**
* **Extrator Compartilhado:** F5 e `ctrl+s` chamam `patch_extractor.extract_code_blocks()` — comportamento visível idêntico, sem lógica duplicada.

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta o idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas, 6 Dicionários:** en_us (padrão/fallback), pt_br, pt_pt, es/es_es, fr/fr_fr.
* **Arquivos Versionados:** `__lang_version__` (**v0.0.32**) controla a atualização dos pacotes (`langs/*.json`) — cadeia de bumps v0.0.28 → v0.0.29 → v0.0.30 → v0.0.31 → v0.0.32 nesta janela.
* **Cobertura:** **1158 chaves** em cada um dos 6 arquivos — paridade total de key sets (+110 desde o relatório anterior). **Ressalva importante 🆕:** o código usa **1198** chaves, então **40 chaves `__()` não existem em nenhum dicionário** (ver §33 e §34) — a paridade entre os 6 arquivos é total, mas a cobertura em relação ao código não é.
* **Fix de Primeira Execução 🆕:** `i18n.py` passou a **criar o diretório do perfil antes** de persistir o idioma detectado, evitando um crash na primeira execução numa máquina limpa.
* **Snapshot de Ambiente (`AMBIENT_ENV_KEYS`):** `frozenset(os.environ)` capturado **imediatamente antes** do `load_dotenv()` de módulo — corrige o badge "⚠ no ambiente" que confirmava tautologicamente que a chave está no arquivo.
* **Cache com Indexação por Idioma:** As respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA com caracteres braille e palavras de "pensamento".
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas. `_load_thinking_words()` / `reload_thinking_words()` aceitam `force=`.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Modo JSON & Parâmetros Determinísticos:** `temperature=0.0` e `top_p=0.1`; fallback automático entre provedores configurados.
* **Timeout de IA:** default de **180s** (`GITPR_AI_TIMEOUT`) — o valor de 600s foi baixado deliberadamente no fix `681a7fa` e o teste desatualizado foi finalmente alinhado nesta janela (ver §37).

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt, com indexação por idioma.
* **Seleção do Último Review (`resolve_last_review()`):** Escolhe o registro `review`/`fullreview` **mais novo** para um par repo+branch, excluindo reviews de escopo de arquivo — é a porta de entrada do `gitpr fix`.
* **Diff Revisado (`reviewed_diff`):** Campo no topo do registro que guarda o diff efetivamente revisado, preferido por `fix/apply_fix.reviewed_diff()`.
* **Telemetria e Duração:** Persistência de `duration_ms` e `meta_raw`.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` lê todos os arquivos de cache recursivamente.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`) e Arqueologia por Blame (`-b`).
* **Publicação Multi-Forge:** F3 cria a issue na forge **configurada** (`GITPR_SCM_PROVIDER`) via `provider.create_issue` — Azure DevOps levanta `ScmNotSupportedError`.
* **Map-Reduce para Issues:** Contexto acima de ~90k tokens é dividido e unificado.
* **Tratamento de 401:** Sinalização de reautenticação sem fechar a aplicação.

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia evolução e autoria histórica com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos via `log_blame_metric()` com profundidade e número de commits analisados.

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)**

* **14 Ferramentas MCP Anotadas:** `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`, `list_fix_candidates` e `review_remote_pr` — **contagem inalterada nesta janela**.
* **18 Recursos + 7 Prompts Templatizados:** `skill://list` + `skill://{pr,commit,review,filereview,issue,blame,release,fix}` + `linter://config` + `prompt://list` + 7 prompts. **Ressalva 🆕:** `skill://explain` e `skill://tests` **não** existem — o teste `TestSkillRegistryAgreement` falha justamente porque `mcp_server.SKILL_FILES` não recebeu os dois tipos novos que `config.SKILL_FILES_BY_TYPE` já tem.
* **Invocação CLI Direta:** `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool sem iniciar o servidor stdio; `gitpr-mcp --list` imprime o registry completo como JSON.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve no `sys.__stdout__` original, garantindo JSON puro. 🆕 Endurecido contra `UnicodeEncodeError` em code pages legadas do Windows (fallback para `buffer` ou re-encode com `errors='replace'`).
* **Offload do Event Loop:** Decorator `_offload` (`anyio.to_thread.run_sync`) nas 14 tools — a ordem dos decorators importa (`@mcp.tool` **acima** de `@_offload`).
* **Log de Uso:** `main()` do servidor chama `log_usage()` — o console script `gitpr-mcp` nunca carrega `main.py`.
* **Testes E2E:** `tests/test_mcp_server_e2e.py` sobe o servidor real como subprocess e fala JSON-RPC stdio.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório:** Rótulo `📁 Repository: owner/repo` e filtragem estrita por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com `ProgressBar`. 🆕 Os testes passaram a aguardar `workers.wait_for_complete()` antes de asseverar — sem isso, a suíte era instável por corrida.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de cache ao totalizador.
* **Exportação Local:** CSV/JSON em `./.gitpr/metrics/export/` — 🆕 mais artefatos gerados entraram **rastreados** (`gitpr_metrics_2026-09-18/19/21/22.*`); a dívida de `.gitignore` segue aberta.

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`.
* **Eventos de Hook, Linter e Blame:** `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()`.
* **Exportação e Limpeza:** `--metrics --export` (CSV/JSON) e `--metrics --purge` com confirmação interativa.

### **19. Sincronização de Idiomas dos Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (v0.0.3).
* **Mapeamento de Sufixos (`HOOK_SCRIPT_SUFFIXES`):** Códigos de interface (`es_es`, `fr_fr`) traduzidos para os sufixos publicados (`.es`, `.fr`).
* **Escolha vs. Estado (`SCRIPTS_LANG` / `SCRIPTS_INSTALLED_LANG`):** Permite **detectar a troca de idioma**.
* **`effective_hook_lang()`:** Resolve o idioma efetivo; `--lang` deixou de ser descartado nesse caminho.
* **Skip de Merge-Source:** O `prepare-commit-msg` pula as fontes `message|merge|squash|commit`.

### **20. Bridge de Linters Externos e Assistente Interativo (`src/linter_wizard.py`, `src/ui/linter_app.py`)**

* **Assistente `--linter-setup`:** Wizard com presets numerados (PHP_CodeSniffer, ESLint, Stylelint) e injeção do bloco `external_linters`.
* **Presets Remotos:** `templates/gitpr.linter-presets.json` com cadeia local → download → stale → fallback embutido.
* **TUI de Erros do Linter:** `src/ui/linter_app.py` (Textual) exibe erros críticos e warnings; em hook/quiet imprime e faz `sys.exit(1)`.
* **Relatório Markdown:** Consolidado em `.gitpr/reports/linter/` apenas quando há violações.
* 🆕 **A Camada SAST é irmã, não substituta:** os bridges Semgrep/Gitleaks/Bandit vivem em `src/infrastructure/linter/external/` (ver §31) e alimentam o **mesmo** pipeline de relatório.

### **21. SCM Multi-Forge (`src/infrastructure/scm/`)**

* **Abstração Única (`ScmProvider` ABC):** `base.py` define o contrato (dataclasses `RepoRef`, `PullRequestDraft` etc. e `ScmProviderError(provider, http_status, message)` — `http_status` 0 = falha de rede); um provider concreto por forge.
* **Registry e Factory:** `resolve_scm_provider()` seleciona por `GITPR_SCM_PROVIDER` (default `github`); `detect_provider_from_remote()` identifica a forge pela URL do origin.
* **Endereçamento de Repositório:** `parse_repo_ref(remote_url) -> RepoRef(raw, workspace, name, provider)`.
* **`get_pull_request(repo, pr_id)` — método concreto da ABC:** default levanta `ScmNotSupportedError` e cada forge implementa — `list_open_pull_requests` pagina **uma página só** e não distingue fechado de inexistente.
* **`supports_reviewable_diff`:** Atributo de classe, `False` no Azure DevOps, checado **antes de qualquer chamada de rede**.
* **Cabeçalhos do GitLab Sintetizados:** `changes[].diff` é um **hunk solto**; `old_path`/`new_path` passaram a montar os cabeçalhos `diff --git a/… / --- / +++`, honrando `/dev/null`.
* **`overflow` do GitLab Levanta:** Um MR com diff truncado era revisado pela metade; agora levanta `ScmProviderError`.
* **`request_pull_request_reviewers` devolve `list[str]` (quebra de contrato):** Devolve os logins **efetivamente anexados**, lidos do corpo do `201`. Subclasses de terceiros precisam ser atualizadas.
* **Dois Helpers Read-Only do GitHub:** `get_commit_author_login` (mapeia SHA → conta ligada ao e-mail do autor) e `get_user_login` (valida/canonicaliza um handle, rejeita o que não pode ser login sem gastar requisição).
* **Fail-Fast por Forge:** Azure exige `GITPR_SCM_ORGANIZATION`/`GITPR_SCM_PROJECT`; Bitbucket exige `GITPR_SCM_USERNAME`; `create_issue` no Azure levanta `ScmNotSupportedError`.
* **Publicação de Releases:** `provider.create_release()` usado pelo `gitpr release --publish`.
* **Artefatos:** Glossário + ADR-001/ADR-005; família `docs/scm-multiforge.*.md` em 5 idiomas; 9 arquivos de teste, **284 cenários**.

### **22. Subcomando `gitpr release` — Changelog / Release Notes**

* **Fluxo:** `git log` entre `--since` e `HEAD` → classificação por Conventional Commits → bump semântico sugerido (`--version <x.y.z>` sobrescreve) → montagem do changelog → resumo executivo de IA opcional → *prepend* no `CHANGELOG.md`.
* **Classificador (`src/commit_classifier.py`)** e **Builder com Seções Traduzíveis (`src/changelog_builder.py`)** — seções renderizadas via `__()` em runtime.
* **Bump Semântico (`src/version_bump.py`)** e **Publicação** (`--publish`, `--draft`, `--format markdown|json`, `--force`). **6 opções no subcomando.**
* **Pendência de release 🆕:** a entrada `[1.3.0] - 2026-09-21` **existe** no `CHANGELOG.md`, mas foi escrita pelo commit da varredura de segredos e cobre **somente** ela — `demo`, `badge`, `split`, SAST, `tests` e `explain` **não estão** no changelog, e a entrada está datada de 21/09 enquanto o `explain` é de 23/09. Rodar `gitpr release` é o passo que falta.

### **23. Subcomando `gitpr config` — TUI de Configuração**

* **Tela Master-Detail (`src/ui/config_app.py`):** Categorias à esquerda, campos à direita, editados inline. Cabeçalho com busca (`/`) e contador de pendências; rodapé `F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc`.
* **Schema Declarativo (`src/config_schema.py`) — a fonte única de verdade:** 🆕 **14 categorias** (+1: **Split**) e **71 `ConfigField`** (+10), dos quais **9 avançados**. Cada campo declara categoria, tipo de widget, `show_if`, validadores, marcadores de versão e ações de download.
* **Categoria `split` 🆕:** `GITPR_SPLIT_MAX_GROUPS`, `GITPR_SPLIT_MAX_HUNKS` e `GITPR_SPLIT_REQUIRE_CONFIRMATION` com um parser de inteiro positivo que cai no default em valor não-parseável — **zero ou negativo não desliga o teto em silêncio**.
* **Campos Read-Only 🆕:** `GITPR_BADGE`, `GITPR_EXPLAIN_BY_DEFAULT` e as três `GITPR_SAST_*_ENABLED` aparecem no schema (e portanto na tela) mas **não** são semeadas no `.env`.
* **Filtragem por Contexto (`show_if`):** `GEMINI_*`/`DEEPSEEK_*`/`OLLAMA_*` conforme o `DEFAULT_AI_PROVIDER`; `GITPR_SCM_USERNAME` sob `[Bitbucket]`; `GITPR_SCM_ORGANIZATION`/`PROJECT` sob `[Azure DevOps]`. Trocar o `Select` re-filtra o painel na hora.
* **Busca Global (`/`):** Casa chave ou rótulo em todas as categorias e **ignora o filtro de visibilidade**.
* **Validação em Duas Camadas:** **Offline** bloqueia o `F2` com erro inline; **online** (só credenciais alteradas na sessão) roda em worker com timeout de 10s e só bloqueia em `401`/`403`.
* **Restaurar (`Ctrl+R`):** Remove a linha do `.env` em vez de reescrever o default; `Esc` com pendências pede confirmação.
* **Seção Skills — a única project-scoped:** Edita `.gitpr/skill/*.md` do projeto resolvidos a partir do diretório de chamada, gravando atomicamente e preservando CRLF/LF. **Dívida conhecida 🆕:** `SKILL_LABELS` não recebeu `tests` nem `explain` — sem rótulo, os dois tipos renderizam **em branco** na barra lateral (ver §33/§34).
* **Downloads com Força:** Botões que forçam re-download de smart-excludes, traduções, presets e thinking words via `force=`.
* **Módulo de Links Leve (`src/doc_links.py`):** `doc_url()` saiu de `core.py` para a UI obter o link sem importar SDKs de IA.
* **Testes:** 5 arquivos — `test_config_app.py` (78), `test_config_schema.py` (42), `test_config_validation.py` (40), `test_config_store.py` (22), `test_config_cli.py` (9).
* **Dívida conhecida:** `gitpr -h config` abre a TUI e ignora o `-h` — o gate `if ctx.invoked_subcommand is not None: return` roda antes do bloco de `help_flag`.

### **24. Log Geral de Uso (`src/usage_log.py`)**

* **Uma Linha por Comando:** Grava `~/.gitpr/logs/<uuid5>.log`, **um arquivo por dia**, com comando, argumentos, repositório, usuário e timestamp.
* **Nome Derivado da Data:** `uuid5(NAMESPACE_DNS, f"gitpr.usage.{YYYY-MM-DD}")` em vez de aleatório — dois processos concorrentes não podem discordar sobre qual arquivo é o de hoje.
* **Escrita Síncrona (decisão explícita):** Diferente de `log_local_metric`, que usa thread daemon e perde a gravação se o processo sair antes.
* **Nunca Imprime:** O servidor MCP reserva o stdout para JSON-RPC; o módulo também nunca levanta exceção.
* **Um Único Spawn de Git:** `git config --get-regexp '^(remote\.origin\.url|user\.name|user\.email)$'` — ~40 ms em vez de ~150 ms no Windows, em *toda* execução.
* **Controle:** `GITPR_SHOW_LOGS` (default `"true"`); desligado em `tests/conftest.py`.
* **Artefatos:** `docs/usage-log.*.md` em 5 idiomas; `tests/test_usage_log.py` (27 cenários).

### **25. Subcomando `gitpr fix` — Achados de Review como Patches Revisáveis (`src/fix/`)**

* **O Pipeline Real:** último review do cache (`resolve_last_review`) → **uma** chamada de IA → extração e validação de diff unificado → `git apply --check` → classificação determinística → dry run ou escrita → histórico.
* **Pacote de 8 arquivos:** `patch_provenance.py`, `patch_extractor.py` (compartilhado com o chat), `patch_safety_classifier.py` (puro, sem I/O), `patch_applier.py`, `fix_history.py`, `apply_fix.py`, `rollback_fix.py`, `__init__.py` (só docstring).
* **Classificação Determinística:** Recusa patch que atravesse mais de um arquivo ou hunk, toque caminho sensível, estoure o orçamento de linhas, **apague uma linha com cara de chamada**, venha marcado de baixa confiança ou falhe no `git apply --check`. O `--force` **nunca** contorna a aplicabilidade, só a classificação.
* **Escrita Opt-In:** Dry run é o default; qualquer mutação exige `--apply` (ou frase digitada com `--force`).
* **`patch_applier.py` Mudou de Casa 🆕:** O invólucro do `git apply` foi promovido a `src/infrastructure/git/patch_applier.py` (compartilhado com o `split`) e `src/fix/patch_applier.py` virou um **shim de re-export** — nenhum import existente quebrou.
* **Testes:** 10 arquivos em `tests/fix/` (**204 cenários**) com fixtures de repositório git real.

### **26. Subcomando `gitpr review-pr` — Review de PR Remoto (`src/review/`)**

* **O que é:** Orquestração, **não** um segundo motor de review — o motor existente, o linter e o renderizador alimentados com um diff que veio de outro lugar. Um `.txt` de review remoto e um de review local do mesmo diff diferem **só no nome do arquivo**.
* **Pacote de 5 arquivos:** `diff_source.py` (proveniência pura), `diff_normalizer.py` (normalização, validação e smart-excludes **em Python**), `render.py` (extraído de `main.py`, agora compartilhado), `remote_pr.py` (o caso de uso), `__init__.py`.
* **Read-Only por Default:** `--post-comment` é o **único** caminho que escreve na forge. A tool MCP `review_remote_pr` sequer recebe o argumento.
* **Interação com o `fix`:** Como o review remoto não corresponde a nenhuma árvore local, o diff revisado é guardado no cache (`reviewed_diff`) e o `fix` o prefere.
* **Artefatos:** `docs/review-pr.md` + `.pt_br.md`, `docs/code-review-ia.*.md` (5), ADR-005 e `glossary-review-pr.md`.
* **Testes:** 4 arquivos em `tests/review/` (**97 cenários**).

### **27. Resolução de Identidade do Revisor (`src/reviewer_resolution.py`)**

* **O Bug (duas falhas silenciosas encadeadas):** (1) **Prefill vazio** — `handles` só com `email_to_handle()`, que enxerga apenas e-mails `users.noreply.github.com` ou com e-mail público; (2) **Attach não verificado** — valores repassados *verbatim*, o GitHub responde **201 sem anexar ninguém** e o `_request()` retorna sem levantar: sucesso aparente, revisor ausente, aviso nenhum.
* **Módulo Novo:** Plano, sem I/O próprio, **que nunca levanta**. `resolve_candidates()` (antes da TUI) e `resolve_typed_reviewers()` (no attach); `match_candidate()` casa exato e normalizado por login, nome ou e-mail.
* **Escada de Resolução:** handle conhecido (sem requisição) → casamento exato com uma pessoa sugerida → lookup por e-mail → validação do login na forge.
* **O que não resolve nunca é enviado:** Sai em `ResolutionOutcome.dropped` como `(valor, motivo_i18n)` e é descartado com aviso visível.
* **Provider Duck-Typed:** Acesso por `getattr`, então fakes e forges sem os métodos novos continuam funcionando.
* **Testes:** `tests/test_reviewer_resolution.py` (18) + ampliações em `test_github_provider.py` (68), `test_pr_publish_app.py` (45), `test_suggest_reviewers.py` (17), `test_reviewer_suggestion.py` (18) e `test_main_suggest_reviewers.py` (8).

### **28. Subcomando `gitpr demo` — Tour Guiado sobre Exemplos Gravados (`src/demo/`) 🆕**

* **O que é:** Um tour interativo que mostra as três saídas principais do GitPR — mensagem de commit, review e descrição de PR — **sem chave de API, sem repositório git e sem rede**. A pergunta "o que essa ferramenta faz?" só tem uma janela para ser feita: o primeiro uso, antes de o usuário ter configurado um provedor.
* **Pipeline Real, Resposta Falsa:** `FakeAIProvider` espelha `src.ai_providers.call_ai_model` **argumento por argumento**; `demo_pipeline()` faz patch de `src.core` e `src.metrics` para que o pipeline de produção (montagem do prompt, chunking do diff, parsing da resposta) rode **intocado** e só a origem da resposta seja trocada. É o que garante que o tour mostra o que a ferramenta de fato produz, e não uma maquete.
* **Isolamento é Requisito, Não Detalhe:** O tour **não pode** tocar o `~/.gitpr` do usuário (cache, métricas, logs) nem a rede — garantido por `tests/demo/conftest.py` (proibição de rede autouse, com exceção de loopback para o event loop proactor do Windows). Uma regressão aqui envenenaria um cache real com conteúdo de demonstração em silêncio.
* **Pacote:** `demo_runner.py` (máquina de estados `DemoState` sem UI + front-end em texto puro), `fake_ai_provider.py`, `scenarios/` (dois exemplos: um bug de atualização de perfil em Laravel e um IDOR cross-tenant em Express, cada um localizado nos 5 idiomas com fallback para inglês). Os cenários são **módulos Python, não JSON**, para viajarem dentro do wheel.
* **TUI:** `src/ui/demo/` (tela única, no padrão dos apps existentes) com modal de ajuda; o diff é cercado como ```` ```diff ```` e a mensagem de commit renderizada como texto puro.
* **CLI:** `gitpr demo` com `--scenario`, `--lang` e `--no-tui`.
* **i18n:** +32 chaves e bump para **v0.0.29**.
* **Testes:** 6 arquivos em `tests/demo/` (**155 cenários**) — máquina de estados, integridade dos cenários (aritmética de hunk), navegação na TUI, modo texto, contrato do provider falso e as guardas de isolamento.
* **Artefatos:** `docs/demo.*.md` em 5 idiomas, `README.*` (5) e as métricas de exemplo do tour.

### **29. Selo GitPR e Comando `gitpr badge` (`src/branding/`) 🆕**

* **O que é:** Um selo público que atesta que um pull request passou por uma verificação de qualidade local, e um comando que imprime o snippet de adoção para o README do projeto.
* **A Motivação é Confiança no Ponto de Publicação:** Um corpo de PR escrito por IA é indistinguível de um escrito à mão, e o resultado do linter morria num terminal que rolou para fora da tela. O selo transforma esse sinal privado numa afirmação visível e verificável no próprio PR publicado.
* **URL Estática de Propósito:** É um Markdown do shields.io que o GitPR **nunca** busca — publicar um pull request não pode passar a depender de um terceiro estar no ar.
* **Medição Honesta (`badge_data.py`):** `collect_linter_counts()` devolve `None` quando não há regras de linter configuradas (rodar `gitpr --skill`), porque lista vazia significa "nada foi verificado", não "nada foi encontrado" — um selo verde sobre um diff não checado seria uma afirmação que o GitPR não pode sustentar. O bridge externo é pulado: ele inspeciona a árvore de trabalho, não a revisão sob review.
* **O Selo Nunca Bloqueia um Publish:** Todo caminho de falha na coleta é capturado e degrada para "sem selo".
* **Ponto Único de Injeção:** `attach_pr_badge()` em `src/main.py`, logo após `pr_data` estar completo — os dois publicadores leem do mesmo lugar. Append idempotente por marcador.
* **Comando `gitpr badge`:** `--readme` (forma nua, amigável a pipe) e `--style`. **Só imprime** — o README nunca é modificado.
* **Divulgação:** O wizard de init anuncia o selo automático no caminho de PR e o `--no-edit` imprime uma linha nomeando o que entrou no corpo que o usuário não viu — um recurso que só aparece depois de configurar uma variável é um recurso que ninguém descobre.
* **Configuração:** `GITPR_BADGE` (default `true`) — opt-out **read-only**, nunca escrito automaticamente.
* **i18n:** +10 chaves e bump para **v0.0.30**.
* **Testes:** 7 arquivos em `tests/badge/` (**83 cenários**) — builder, coleta de dados, CLI, opt-out, caminhos de publicação e uma guarda offline (proibição de rede autouse, exceto loopback); as suítes do demo e do wizard foram estendidas.
* **Demo:** O passo de PR do tour agora mostra o selo que um publish real anexaria, contado do bloco de linter **gravado no próprio cenário** — nenhuma regra é lida e nenhum diff é lintado.
* **Artefatos:** `docs/badge.*.md` em 5 idiomas e `docs/survey/20260919_gitpr_badge_surveyfacts.md`.

### **30. Subcomando `gitpr split` — Commits Atômicos por Hunk (`src/split/`) 🆕**

* **O que é:** Uma árvore de trabalho com vários concerns não precisa mais virar um commit-blob. O `split` lê o diff não commitado, pede à IA que particione os hunks por **intenção lógica** e propõe um commit atômico por concern — cada um com mensagem gerada a partir do patch reconstruído **daquele grupo isolado**. A árvore nunca é reescrita: os arquivos terminam byte a byte iguais ao início; só o histórico muda.
* **Pacote de 6 arquivos, em camadas de baixo para cima:**
  * `split_plan.py` — contrato de dados: `SplitError`, `Hunk`, `OpaqueSection`, `ChangeUnit`, `HunkGroup`, `SplitPlan`.
  * `hunk_parser.py` — `parse_units()` / `build_patch()`: texto ↔ modelo, **puro**, nunca roda git.
  * `hunk_grouper.py` — renderização do prompt, orçamento e trimming, **uma** chamada de IA, validação da resposta.
  * `generate_split_plan.py` — diff → units → groups → pré-validação de conflito → mensagens. **Somente leitura.**
  * `apply_split_plan.py` — **o único módulo do split que muta**: staging seletivo e um commit por grupo.
  * `__init__.py` — marcador de pacote.
* **A Garantia de Árvore Intacta é Estrutural:** `selective_stager.py` pré-valida **todo** grupo contra um índice temporário em HEAD e usa um `GIT_INDEX_FILE` descartável — um plano nunca é aplicado sem checagem, e o índice do usuário nunca é lido nem movido durante o planejamento.
* **Destrutivo para o Índice, Não para a Árvore:** O `--apply` reseta o índice para HEAD antes de stagear, então o que o usuário já tinha staged é desestagiado. O conteúdo dos arquivos é preservado, mas o staging precisa ser refeito — documentado explicitamente.
* **Configuração:** `GITPR_SPLIT_MAX_GROUPS` (default 5), `GITPR_SPLIT_MAX_HUNKS` (default 50) e `GITPR_SPLIT_REQUIRE_CONFIRMATION` (default `true`). Valores zero ou negativos são **ignorados em favor do default**, em vez de desligarem um teto em silêncio.
* **i18n:** +50 chaves e bump para **v0.0.31**.
* **Testes:** 6 arquivos em `tests/split/` (**101 cenários**) rodando contra repositórios descartáveis reais, com a rede bloqueada.
* **Artefatos:** `docs/split-command.md` + `.pt_br.md` (os 3 idiomas restantes ficaram pendentes), ADR-006 (`split-apply-safety`), `glossary-gitpr-split.md`, spec/plano em `docs/plans/` e survey.

### **31. Varredura de Segredos Embutida (`src/security_ruleset.py`) 🆕**

* **O que é:** Sete regras que rodam em **toda** invocação do linter, mescladas ao fim de `load_linter_rules()` depois das regras do projeto e dos plugins, que ficam intocados.
* **As Sete Regras:** cinco `error` bloqueantes — AWS access key ID, token GitHub, token Slack, chave de API Google e bloco de chave privada (`-----BEGIN … PRIVATE KEY-----`) — e duas `warning` que reportam sem bloquear: URL de conexão de banco com credenciais e atribuição genérica de credencial (`password = "…"`), esta atrás de um filtro de placeholder (`changeme`, `xxxxxx`, `example`, `dummy`, `sample`, `your_password_here`, `sua_senha`).
* **Por que no Pacote e Não no Template:** O catálogo local era inteiramente gerenciado pelo usuário — podia ser sobrescrito pelo download, reescrito pelo wizard (perdendo comentários) ou estendido só por plugins da máquina. Um portão de segredos precisa se comportar **igual** em toda máquina e em todo CI, então as regras vivem no pacote e não podem ser substituídas por `--skill` nem reescritas pelo wizard.
* **Lacunas de Cobertura Conhecidas (v1), declaradas:** atribuição **sem aspas** não é pega (`API_KEY=abc123` — o formato `.env`, que é exatamente onde segredos vazam); faltam os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-`; e a regra genérica não tem fronteira à esquerda no nome da chave, então `mytoken` casa igual a `token`.
* **Configuração:** `GITPR_LINTER_SECURITY` (default `true`; opt-out fail-open — só `false`/`0`/`no`/`off`/`n` desliga) e `GITPR_LINTER_SECURITY_DISABLED_RULES` (`;`-separadas).
* **Testes:** `tests/test_security_ruleset.py` (**61 cenários**) — compilação de regex, detecção positiva/negativa, filtro de placeholder, roteamento de nível, aplicação do wildcard, merge e completude de tradução.
* **Artefatos:** ADR-007 (`secret-ruleset-location-and-severity`), `glossary-gitpr-secret-scanning.md`, spec/plano/survey e 3 relatórios de tarefa.

### **32. Bridges SAST — Semgrep, Gitleaks e Bandit (`src/infrastructure/linter/external/`) 🆕**

* **O que é:** Uma camada **opt-in** que pluga scanners de segurança de terceiros no pipeline de linter existente, elevando o piso de todo review sem custo para quem não precisa.
* **Escopo Bounded:** Rodam **só** quando habilitados e **só** sobre os arquivos tocados pelo diff.
* **Contrato Comum:** `ExternalLinterBridge` (ABC) com execução endurecida de `subprocess` (`shell=False`, timeout estrito, `stdin=DEVNULL`, UTF-8 com `errors='replace'`) e bridges concretos para Semgrep, Gitleaks e Bandit. O modelo `NormalizedFinding` / `ExternalLinterResult` faz todo tool produzir achados na mesma severidade (`error`/`warning`/`info`) e na mesma forma.
* **Deduplicação é o Ponto:** `deduplicate_secret_findings()` funde achados do Gitleaks e do ruleset regex no mesmo arquivo e linha numa **única** entrada confirmada `[Gitleaks + Regex]` — um segredo visto pelos dois aparece uma vez, com confirmação multi-fonte, em vez de duas.
* **Segredos Mascarados:** `mask_secret_value()` (`AKIA****`) garante que o valor nunca chegue ao achado, ao log ou à telemetria.
* **Resolução em Três Camadas:** `load_sast_config()` lê defaults → `.gitpr.linter.yml` (bloco `sast`, caindo para `linter.external`) → variáveis `GITPR_SAST_*`. **Todas default `false`** — opt-in estrito, então ninguém vê mudança até pedir.
* **Degradação Graciosa:** Ferramenta habilitada mas ausente do `PATH` emite `⚠️ SAST tool '{tool}' is enabled in config but was not found in PATH.` e a execução continua.
* **Normalização de Caminho:** Todos os bridges normalizam para barras invertidas→normais e forma relativa ao repositório, para casar as chaves de arquivo modificado do diff no Windows **e** no Unix.
* **Configuração:** `GITPR_SAST_SEMGREP_ENABLED`, `GITPR_SAST_GITLEAKS_ENABLED`, `GITPR_SAST_BANDIT_ENABLED` + `GITPR_SAST_<TOOL>_TIMEOUT` (60s / 30s / 45s).
* **Dependências:** `semgrep`, `gitleaks` e `bandit` **não** são pacotes Python do projeto — são binários externos que precisam estar no `PATH`.
* **i18n:** +7 chaves (a última adição de chaves desta janela).
* **Testes:** 4 arquivos em `tests/infrastructure/linter/external/` (**14 cenários**) + `tests/domain/linter/test_sast_finding_mapper.py` (2) — disponibilidade, timeout de subprocess, binário ausente, parsing de JSON, mapeamento de severidade, mascaramento de segredo e pulo de não-Python.

### **33. Subcomando `gitpr tests generate` — Geração de Suíte por IA (`src/domain/tests_generation/`, `src/application/`) 🆕**

* **O que é:** Gera arquivos de teste completos e executáveis a partir do diff atual, de um arquivo específico ou de um achado de review, **respeitando a convenção do repositório** (Pest, PHPUnit, Jest, Vitest, Pytest) em vez de impor um estilo.
* **Domain Layer:** `TestFramework` (enum) e as dataclasses `TestGenerationTarget`, `TestScaffold`, `GeneratedTest` como contrato compartilhado; `detect_test_framework()` detecta pelos arquivos de configuração, manifests de dependência e conteúdo do diretório de testes, com override explícito e aviso quando a detecção falha; `build_test_scaffold()` calcula o caminho convencional de destino por framework (o split `Feature`/`Unit` do Laravel, o `tests/**/test_*.py` do Pytest, as convenções `.test`/`.spec` de JS/TS).
* **Application Layer (`generate_test_file.py`):** Orquestra detecção de framework, resolução de scaffold, construção do prompt, invocação da IA, parsing do JSON e escrita opcional. `validate_test_syntax()` roda o toolchain local (`php -l`, `node --check`, `python -m py_compile`) quando disponível — falha de validação é **aviso**, não erro.
* **Degradação Graciosa:** Sem chave de API, ou com resposta não-JSON do modelo, o resultado é marcado como de baixa confiança em vez de levantar (tira as cercas de markdown e segue).
* **Apresentação:** Grupo `tests` com o subcomando `generate` (`--file`, `--finding`, `--framework`, `--apply`, `--provider`); dry run é o default e sobrescrever teste existente pede confirmação com **No** pré-selecionado. O chat delega `/tests` ao **mesmo** caso de uso.
* **Testes:** `tests/domain/tests_generation/` (18), `tests/application/use_cases/test_generate_test_file.py` (4) e `tests/test_tests_command.py` (2).
* **Dívida 🆕:** Nenhuma chave i18n nova foi adicionada — a feature usa **17 chaves `__()`** que não existem em nenhum dos 6 dicionários (parte das 40 faltantes), e `SKILL_LABELS`/`mcp_server.SKILL_FILES` não receberam o tipo `tests`. Não há `docs/tests*.md`.

### **34. Subcomando `gitpr explain` e a Flag `--explain` — Guia do Revisor (`src/domain/pr/`) 🆕**

* **O que é:** Um guia centrado em quem vai **revisar** — o que muda, por que muda, onde focar e qual o risco de regressão — para que ninguém tenha que reconstruir a intenção a partir de um diff cru.
* **Domain Layer (`explain_section_builder.py`):** `PrExplanation` / `ReviewerFocusPoint`, o renderizador `build_explain_markdown()` e `parse_explain_payload()`, que tolera saída não-JSON ou malformada e **detecta placeholders** `[FILL]`/`[TODO]` para sinalizar evidência insuficiente em vez de apresentar um guia oco como completo.
* **Application Layer (`generate_pr_explanation.py`):** Resolução de provedor, validação da chave, carregamento do skill context (`explain`), construção do prompt, invocação e parsing para o modelo de domínio.
* **Duas Portas de Entrada:** `gitpr explain` (subcomando, com `--provider`, detecção de diff ausente antes de qualquer IA e saída colorizada) e a flag `--explain` no CLI raiz, que anexa o guia ao corpo da descrição de PR **e** ao payload JSON emitido, num único `pr_desc_body` reusado.
* **Configuração:** `GITPR_EXPLAIN_BY_DEFAULT` (default `false`) — quando `true`, a seção é anexada a **toda** descrição gerada, o que adiciona uma chamada de IA e aumenta custo/tokens por PR.
* **Skill:** `.gitpr.explain.md` registrado em `SKILL_FILES_BY_TYPE`, com templates em 5 idiomas.
* **Testes:** `tests/domain/pr/test_explain_section_builder.py` (4), `tests/application/use_cases/test_generate_pr_explanation.py` (2) e `tests/test_explain_command.py` (2).
* **Dívida 🆕:** Mesmo padrão do `tests` — chaves `__()` sem tradução (parte das 40), ausente de `SKILL_LABELS` e de `mcp_server.SKILL_FILES`, e sem tópico em `docs/`.

### **35. Suíte Determinística e o Primeiro CI (`.github/workflows/tests.yml`) 🆕**

* **O que é:** O primeiro workflow que roda a suíte, em **Python 3.10** (o piso declarado em `pyproject.toml`, nunca exercitado) e **3.13** (a versão de desenvolvimento no `Pipfile`), com `fail-fast: false`.
* **O que o CI Tornou Visível:** **22 testes** falhavam numa máquina pt-BR porque asseveram o literal em inglês enquanto `__()` renderiza português — a suíte só ficava verde com `GITPR_LANG=en_us` na linha de comando. Foi a motivação direta do endurecimento do `conftest.py`.
* **`tests/conftest.py` Hermético 🆕:** Pina `GITPR_LANG=en_us` (impede a suíte de escrever no perfil real e de renderizar traduções), `GITPR_LINTER_SECURITY=false` (três suítes asseveram a lista de regras que o `load_linter_rules()` real devolve) e `LANG_VERSION` na versão do código (impede o re-download de `~/.gitpr/langs/*.json` a cada bump).
* **Ordem Importa:** `src.updater` é importado **antes** das variáveis de idioma serem definidas, porque o `i18n` fotografa `os.environ` em `AMBIENT_ENV_KEYS` no import — uma sessão real recebe `LANG_VERSION` do arquivo, não do shell.
* **Estabilidade de Testes de Worker:** `test_config_app.py` e `test_metrics.py` passaram a aguardar `workers.wait_for_complete()` antes de asseverar.
* **Dependência do Workflow:** O runner limpo não tem `~/.gitpr`, e `tests/demo/test_demo_isolation.py` assevera que o perfil existe (ele o fotografa para provar que o tour não escreve nele) — o job cria o diretório e o `.env` vazio explicitamente.

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
| `tests/test_config_schema.py` | 42 | Cobertura de `DEFAULT_CONFIG`, sem duplicatas, categorias/kinds, `advanced` só em Avançado, **seção de skills** ⚠️ |
| `tests/test_config_store.py` | 22 | Round-trip no `.env` temporário, comentários e ordem preservados, `remove_config_value()` idempotente |
| `tests/test_config_suggest_reviewers.py` | 8 | Configuração de suggested reviewers (chaves e defaults) |
| `tests/test_config_validation.py` | 40 | Tipos, enums, templates, `validate_ai_key()` com SDK mockado (401 vs. rede vs. ollama) |
| `tests/test_core.py` | 49 | Fluxos principais, git diff, PR generation, timing, staging, coautoria, idioma dos hooks |
| `tests/test_diff_parser.py` | 26 | Parser de diff por linhas/hunks + `summarize_patch()` e `split_patch_sections()` |
| `tests/test_explain_command.py` | 2 🆕 | CLI do `explain`: sucesso, chave ausente, diff vazio |
| `tests/test_external_linters.py` | 33 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_i18n.py` | 20 | Paridade entre idiomas, chaves ausentes/órfãs, identidade — **asserção de 40 chaves faltantes** ⚠️ |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação |
| `tests/test_issue_engine.py` | 4 | Draft de issue estruturado |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_linter_presets.py` | 5 | Presets de linter: resolução e re-download forçado |
| `tests/test_main_suggest_reviewers.py` | 8 | Flag `--no-suggest-reviewers` na CLI e no help contextual |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 104 | Ferramentas MCP (14), recursos (18), annotations, patching, CLI direto, offload — **acordo de registries de skill** ⚠️ |
| `tests/test_mcp_server_e2e.py` | 6 | Servidor MCP real via subprocess + JSON-RPC stdio |
| `tests/test_metrics.py` | 34 | Coleta, exportação local, escopo de repo, cache token summary |
| `tests/test_net_timeouts.py` | 12 | Timeouts de rede/IA — **alinhados ao default real de 180s** ✅ |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_pr_publish_app.py` | 45 | TUI do PR Publisher: telas, fluxos, suggested reviewers, `NoticeScreen` |
| `tests/test_pr_publish_linter_modal.py` | 4 | Modal de erro do linter: abort, no-verify |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_release_cli.py` | 4 | CLI do release: options, help com epilog documentado |
| `tests/test_release_engine.py` | 27 | Engine de release: intervalo de commits, CHANGELOG, publicação |
| `tests/test_reviewer_resolution.py` | 18 | Escada de resolução, rejeição de nome parcial, dedup, tolerância a falha |
| `tests/test_reviewer_suggestion.py` | 18 | Lógica de sugestão de revisores (ranking, exclusão, top-N, `last_commit_hash`) |
| `tests/test_security_ruleset.py` | 61 🆕 | Matriz do ruleset embutido: regex, placeholders, nível, wildcard, merge, traduções |
| `tests/test_skill_command.py` | 10 | Download e validação de templates de skill |
| `tests/test_skill_context.py` | 14 | `get_skill_context()` com `quiet=True`, fallbacks, registro de skills |
| `tests/test_smart_excludes.py` | 15 | Filtro pathspec inteligente e re-download forçado |
| `tests/test_suggest_reviewers.py` | 17 | Suggested reviewers no fluxo de PR (integração, hint `no_login`) |
| `tests/test_tests_command.py` | 2 🆕 | CLI do grupo `tests` e do `generate` |
| `tests/test_thinking_words.py` | 5 | Carregamento, parsing com separador `;` e reload forçado |
| `tests/test_updater.py` | 23 | Gate do PyPI: parsing de versão, cache diário, fetch, decisões do portão, wiring no CLI |
| `tests/test_usage_log.py` | 27 | Log de uso: nome derivado da data, escrita síncrona, silêncio, `_repo_label()` multi-forge |
| `tests/test_version_bump.py` | 17 | Bump semântico: major/minor/patch, alvos e validação |
| `tests/application/use_cases/test_generate_pr_explanation.py` | 2 🆕 | Caso de uso do explain: provedor, chave, parsing |
| `tests/application/use_cases/test_generate_test_file.py` | 4 🆕 | Caso de uso da geração de testes: dry-run/apply, validação de sintaxe |
| `tests/badge/test_badge_append.py` | 9 🆕 | Append idempotente do selo ao corpo do PR |
| `tests/badge/test_badge_builder.py` | 19 🆕 | Composição do Markdown do shields.io, escape, regra de cor, estilo |
| `tests/badge/test_badge_cli.py` | 15 🆕 | Comando `gitpr badge`: snippet, `--readme`, `--style` |
| `tests/badge/test_badge_data.py` | 7 🆕 | Contagem de alertas; `None` sem regras configuradas |
| `tests/badge/test_badge_offline.py` | 6 🆕 | Guarda offline (rede proibida, exceto loopback) |
| `tests/badge/test_badge_optout.py` | 17 🆕 | `GITPR_BADGE=false` em todos os caminhos de publicação |
| `tests/badge/test_badge_paths.py` | 10 🆕 | Ponto único de injeção nos dois publicadores (TUI e `--no-edit`) |
| `tests/demo/test_demo_app.py` | 22 🆕 | TUI do tour: navegação, telas, modal de ajuda |
| `tests/demo/test_demo_isolation.py` | 14 🆕 | O tour não toca `~/.gitpr` nem a rede |
| `tests/demo/test_demo_runner.py` | 33 🆕 | Máquina de estados `DemoState`: avançar, voltar, concluído, modo texto |
| `tests/demo/test_demo_scenarios.py` | 47 🆕 | Integridade dos cenários gravados (aritmética de hunk) nos 5 idiomas |
| `tests/demo/test_demo_text_mode.py` | 18 🆕 | Saída em texto puro (`--no-tui`) para CI e gravações |
| `tests/demo/test_fake_ai_provider.py` | 21 🆕 | Contrato do provider falso: espelha `call_ai_model` argumento por argumento |
| `tests/domain/linter/test_sast_finding_mapper.py` | 2 🆕 | Formatação uniforme e deduplicação `[Gitleaks + Regex]` |
| `tests/domain/pr/test_explain_section_builder.py` | 4 🆕 | Renderização do Markdown, parsing tolerante, detecção de `[FILL]` |
| `tests/domain/tests_generation/test_framework_detector.py` | 11 🆕 | Detecção por config, manifest e diretório; override; falha avisada |
| `tests/domain/tests_generation/test_scaffold_builder.py` | 7 🆕 | Caminho convencional por framework (Laravel, Pytest, JS/TS) |
| `tests/fix/test_apply_fix.py` | 53 | Caso de uso completo: review → IA → validar → classificar → dry-run/apply |
| `tests/fix/test_chat_shared_extractor.py` | 8 | Extrator compartilhado entre chat e `fix` (comportamento idêntico) |
| `tests/fix/test_fix_cli.py` | 31 | Roteamento do subcomando, opções, dry-run default, `--force` |
| `tests/fix/test_fix_history.py` | 21 | Ledger `.gitpr/fix_history.json`: escrita atômica, leitura |
| `tests/fix/test_fix_settings.py` | 10 | As cinco `GITPR_FIX_*` e os fallbacks de valor inválido |
| `tests/fix/test_patch_applier.py` | 19 | Invólucro de `git apply`: check/apply/reverse, branch, status |
| `tests/fix/test_patch_extractor.py` | 13 | Blocos cercados → diff unificado validado |
| `tests/fix/test_patch_safety_classifier.py` | 22 | Matriz safe/review_required/experimental e códigos de motivo |
| `tests/fix/test_resolve_last_review.py` | 13 | Seleção do último review, exclusão de reviews por arquivo |
| `tests/fix/test_rollback_fix.py` | 14 | `--rollback`: reverse e as três recusas |
| `tests/infrastructure/linter/external/test_bandit_bridge.py` | 3 🆕 | Bridge Bandit: disponibilidade, parsing, mapeamento |
| `tests/infrastructure/linter/external/test_base_bridge.py` | 4 🆕 | ABC: subprocess endurecido, timeout, binário ausente |
| `tests/infrastructure/linter/external/test_gitleaks_bridge.py` | 4 🆕 | Bridge Gitleaks: mascaramento de segredo, escopo por arquivo |
| `tests/infrastructure/linter/external/test_semgrep_bridge.py` | 3 🆕 | Bridge Semgrep: parsing JSON, severidade, pulo de não-Python |
| `tests/review/test_diff_normalizer.py` | 20 | Newlines, validação de diff, smart-excludes em Python |
| `tests/review/test_diff_source.py` | 12 | `DiffOrigin`/`DiffSource`: proveniência, `cache_scope`, `is_remote` |
| `tests/review/test_remote_pr.py` | 40 | Orquestração: portões, PR, diff, linter, comentário opcional |
| `tests/review/test_review_pr_cli.py` | 25 | CLI `review-pr`: opções, rejeições antes da IA, `--post-comment` |
| `tests/scm/test_azure_devops_provider.py` | 43 | Provider Azure DevOps: org/projeto, PRs, `ScmNotSupportedError` |
| `tests/scm/test_bitbucket_provider.py` | 39 | Provider Bitbucket: Basic auth, workspace |
| `tests/scm/test_contract.py` | 38 | Contrato `ScmProvider`: assinaturas, dataclasses, erros |
| `tests/scm/test_factory.py` | 11 | `resolve_scm_provider()` + `detect_provider_from_remote()` |
| `tests/scm/test_github_api_shim.py` | 18 | Shim deprecado `github_api` → delega ao provider |
| `tests/scm/test_github_provider.py` | 68 | Provider GitHub: REST, headers, PRs, issues, releases, read-back de revisores |
| `tests/scm/test_gitlab_provider.py` | 47 | Provider GitLab: API v4, namespace, cabeçalhos sintetizados e `overflow` |
| `tests/scm/test_init_wizard.py` | 10 | Wizard `--init`: detecção da forge, validação, persistência |
| `tests/scm/test_release_publish.py` | 8 | Publicação de release por forge (GitHub/GitLab) |
| `tests/split/test_apply_split_plan.py` | 11 🆕 | O único módulo que muta: staging seletivo, um commit por grupo |
| `tests/split/test_generate_split_plan.py` | 12 🆕 | Diff → units → groups → pré-validação de conflito → mensagens |
| `tests/split/test_hunk_grouper.py` | 18 🆕 | Prompt, orçamento/trimming, chamada de IA, validação da resposta |
| `tests/split/test_hunk_parser.py` | 18 🆕 | `parse_units()`/`build_patch()`: texto ↔ modelo, puro |
| `tests/split/test_selective_stager.py` | 11 🆕 | Staging de subconjunto, check contra HEAD, índice limpo |
| `tests/split/test_split_cli.py` | 31 🆕 | CLI do split: opções, dry run default, `--apply` |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (scaffold; nunca executado) |

**Total:** **1889 cenários coletados em 96 módulos de teste** (44 na raiz + 9 em `tests/scm/` + 10 em `tests/fix/` + **6 em `tests/split/`** 🆕 + **6 em `tests/demo/`** 🆕 + **7 em `tests/badge/`** 🆕 + 4 em `tests/review/` + **4 em `tests/infrastructure/linter/external/`** 🆕 + **2 em `tests/domain/tests_generation/`** 🆕 + **2 em `tests/application/use_cases/`** 🆕 + **1 em `tests/domain/pr/`** 🆕 + **1 em `tests/domain/linter/`** 🆕; **+452** desde o relatório anterior, com **32 arquivos novos**). Execução completa nesta máquina com `GITPR_LANG=en_us`: **1883 passed / 4 failed / 2 skipped / 81 subtests** em ~373s.

**Notas de qualidade desta versão:**
- **✅ As 3 falhas herdadas foram fechadas.** Os dois testes desatualizados de `test_net_timeouts.py` (que asseriam 600s num código que entrega 180s desde o fix `681a7fa`) foram alinhados — o item estava aberto há **três relatórios seguidos**. E a falha sensível ao locale foi resolvida pinando `GITPR_LANG=en_us` no `conftest.py`, o que também eliminou as **22 falhas de locale** que o CI revelou numa máquina pt-BR.
- **⚠️ 4 falhas novas, uma única causa raiz:** as duas features mais recentes (`tests` e `explain`) entraram com o **registro de skills pela metade**. São elas:
  1. `test_config_schema.py::TestSkillsSection::test_the_labels_cover_the_registry_exactly` — `SKILL_LABELS` não tem `tests` nem `explain`; sem rótulo, os dois renderizam **em branco** na barra lateral da TUI de configuração.
  2. `test_config_schema.py::TestSkillsSection::test_the_labels_follow_the_registry_order` — a mesma lacuna vista pela ordem: `SKILL_TYPES` tem 10 entradas, `SKILL_LABELS` tem 8.
  3. `test_i18n.py::TestNoMissingKeys::test_no_missing_keys` — **40 chaves `__()`** usadas no código não existem em **nenhum** dos 6 dicionários (todas dos comandos `tests` e `explain`). Como o inglês é o fallback, elas renderizam como a própria chave em qualquer idioma.
  4. `test_mcp_server.py::TestSkillRegistryAgreement::test_the_two_skill_registries_agree` — `mcp_server.SKILL_FILES` e `config.SKILL_FILES_BY_TYPE` deixaram de concordar; `skill://explain` e `skill://tests` não são expostos pelo MCP.
- **A causa é uma só e é barata de fechar:** registrar os dois tipos em `SKILL_LABELS`, em `mcp_server.SKILL_FILES` e rodar `python tests/sync_i18n.py` para as 40 chaves. O ponto relevante é que a suíte **detectou** — as três asserções existem exatamente para isso, e o CI as roda em duas versões de Python.
- **Crescimento de 452 cenários** com a linha de base de falhas herdadas zerada — o sinal desta janela: a suíte deixou de carregar falhas conhecidas e passou a acusar dívida nova no mesmo commit em que ela nasce.
- `tests/conftest.py` ficou **hermético**: `GITPR_SHOW_LOGS=false`, `GITPR_SKIP_UPDATE_CHECK=true`, `GITPR_LANG=en_us`, `GITPR_LINTER_SECURITY=false` e `LANG_VERSION` na versão do código — a suíte não escreve no log de uso, no `.env` real nem em `~/.gitpr/langs/`.
- **Fixtures de git real:** `tests/fix/git_fixture.py` e `tests/split/git_fixture.py` montam repositórios de verdade — o `patch_applier` e o `selective_stager` só são honestos se o `git apply` for o de verdade.
- **Guarda de rede:** `tests/demo/conftest.py` proíbe a rede por autouse — uma regressão ali envenenaria um cache real com conteúdo de demonstração.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** **1158 chaves** de tradução nos 6 dicionários, com **paridade total de key sets** entre eles (+110 desde o relatório anterior). A cadeia medida por commit foi 1048 → 1080 (`demo`, +32) → 1090 (`badge`, +10) → 1140 (`split`, +50) → 1151 (segredos, +11) → **1158** (SAST, +7). Os dois últimos commits (`tests`, `explain`) **não** adicionaram chaves — usam 40 que não existem. ⚠️ O código usa **1198** chaves.
* **`__lang_version__` subiu v0.0.28 → v0.0.29 → v0.0.30 → v0.0.31 → v0.0.32**, disparando o re-download OTA das traduções. A varredura de segredos e o SAST adicionaram chaves **sem** bumpar o marcador; o bump para v0.0.32 cobre os dois e está **no working tree, não commitado**.
* **Fontes de tradução em lockstep:** uma chave nova precisa existir no código (fonte), em `langs/pt_br.json` (**lista mestra**), nos dicts FR/ES de `scripts/sync_all_langs.py` (segunda fonte) e nos valores curados de `scripts/fix_mangled_i18n_keys.py` (terceira fonte, lida por `tests/test_i18n.py`); a asserção `len(CLEAN_KEYS)` segue em 49.
* **Tópicos novos 🆕 (3):**
  - `docs/demo.md` — o tour guiado: o que ele mostra, o pipeline real com resposta falsa, os cenários e a garantia de isolamento — **em 5 idiomas**
  - `docs/badge.md` — o selo do PR: o que ele afirma, onde é anexado, quando é omitido e como imprimir o estático para o README — **em 5 idiomas**
  - `docs/split-command.md` — commits atômicos por hunk: o pipeline, a pré-validação, o que o `--apply` faz com o índice — **em EN + PT-BR** (os 3 idiomas restantes ficaram pendentes)
* **Subdiretório novo 🆕:** `docs/tutorial/` com a família `install-from-source.*` **em 5 idiomas** (instalação a partir do código-fonte).
* **Tópicos atualizados nesta janela:** `docs/linter-regras-customizadas.*` (5 — o campo `level`, o ruleset embutido e as duas escotilhas de escape), `docs/git-hooks-locais.*` (5 — o que o pre-commit hook passou a bloquear e como contornar), `docs/auto-update.*` (5), `docs/ARCHITECTURE.md`, além de `README.md` e as 4 traduções (índice com as famílias `demo`, `badge`, `split-command`, `fix-command` e `review-pr`).
* **Documentação em 5 idiomas:** **44 tópicos canônicos** em `docs/` (+3) — **37 com cobertura completa nos 5 idiomas** (+2) e **7 tópicos parciais/PT-only** (`como_reverter_commit_git_localmente`, `github-issue-prompt-com-gh`, `otimizacao-de-tokens`, `testar_sem_usar_pypi`, `version-markers`, `review-pr` com 2 idiomas e, agora, `split-command` com 2).
* **Lacuna de documentação 🆕:** `explain` e `tests` são as duas primeiras features em várias janelas a chegarem **sem tópico em `docs/`** — só têm os templates de skill.
* **Skills locais do Claude Code:** `.claude/skills/` com **29 skills** (contagem inalterada nesta janela).
* **Memory Index:** `.claude/memory/MEMORY.md` com **41 padrões** (+1 nesta janela).
* **Relatórios de tarefas:** `docs/claude-code/reports/develop_natan/` (**101** no total; **+8** na janela) e `docs/gemini/reports/develop_natan/` (**7**; **+2** — `2026-09-21_skill_gitpr_sast_bridge.md` e `2026-09-22_skill_gitpr_tests_generate.md`).
* **Relatórios de status:** `docs/reports/` (15 relatórios; este é o 16º).
* **Planos de desenvolvimento:** 115 arquivos em `docs/plans/` (+16 na janela — specs/planos de `demo`, `badge`, `split`, segredos, SAST, `tests` e `explain`, ADR-006 e ADR-007, os glossários `glossary-gitpr-split` e `glossary-gitpr-secret-scanning`) + **10 arquivos em `docs/survey/`** (+4).

---

## **🔄 Pipeline de Distribuição**

1. **PyPI (canal único):** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **Atualização obrigatória:** a execução verifica o PyPI no startup e **bloqueia com exit code 1** se houver versão mais nova, imprimindo `pip install --upgrade gitpr-cli`; a checagem é cacheada por dia e o `--update` apenas reporta
3. **GitHub Releases:** removido — sem PyInstaller, sem asset `.exe`, sem hot-swap
4. **GitHub Actions:** workflow `pr-review.yml` + `action.yml` (instala via pip) + **`tests.yml`** 🆕 (matriz Python 3.10 e 3.13, com criação explícita do perfil `~/.gitpr` que `test_demo_isolation.py` assevera existir)
5. **MCP Server:** entry point `gitpr-mcp` via `pyproject.toml`
6. **Templates e idiomas OTA:** `templates/` e `langs/*.json` servidos do GitHub (main) — o bump `v0.0.32` renova as cópias locais de `~/.gitpr/langs/` quando publicado
7. **Versão derivada do código 🆕:** `pyproject.toml` usa `version = {attr = "src.updater.__version__"}` — o `__version__` é a **única** fonte, e é por isso que um bump não commitado deixa o pacote construído em 1.2.0 enquanto o `CHANGELOG.md` já anuncia 1.3.0
8. **Estado do release 1.3.0 🆕:** a tag **`v1.2.0` foi criada** (merge do PR #174, 2026-09-17), fechando o bloqueio da janela anterior. O `__version__` (1.3.0) e o `__lang_version__` (v0.0.32) estão **no working tree e não commitados** (HEAD em 1.2.0 / v0.0.31); o `CHANGELOG.md` tem a entrada `[1.3.0]` commitada, mas **incompleta** — cobre só a varredura de segredos. O caminho é estender o changelog com as 6 features restantes, rodar `gitpr release`, commitar o bump e taguear.

---

## **📈 Evolução desde o Relatório Anterior (v0.0.15)**

| Área | v0.0.15 (anterior) | v0.0.16 (atual) |
|------|-------------------|-----------------|
| **Versão GitPR** | 1.2.0 (bump **não commitado**; HEAD em 1.1.0) | **1.3.0** (bump **não commitado**; HEAD em 1.2.0) — **tag `v1.2.0` criada** ✅ |
| **Versão Idioma** | v0.0.28 | **v0.0.32** (via v0.0.29, v0.0.30 e v0.0.31; bump **não commitado** — HEAD em v0.0.31) |
| **Versão Scripts Hook** | v0.0.3 | **v0.0.3** |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 idiomas, 6 dicionários | 5 idiomas, 6 dicionários |
| **Subcomandos** | 4 (`release`, `config`, `fix`, `review-pr`) | **9** (+ `demo`, `badge`, `split`, `tests`, `explain`) |
| **Interface** | CLI + TUIs + wizards `--init`/`--install` + 4 subcomandos | **+ `gitpr demo` (TUI + modo texto) + `gitpr badge` + `gitpr split` + `gitpr tests generate` + `gitpr explain` + flag `--explain`** |
| **Camadas** | `src/infrastructure/` (SCM) | **+ `src/domain/` e `src/application/use_cases/` (arquitetura em camadas)** 🆕 |
| **Ferramentas MCP** | 14 tools / 18 recursos / 7 prompts | **14 tools / 18 recursos / 7 prompts** (inalterado — `skill://explain` e `skill://tests` **faltando** ⚠️) |
| **Flags CLI** | 35 na raiz + `release` (6) + `config` (0) + `fix` (8) + `review-pr` (2) | **36 na raiz** (+`--explain`) + `release` (6) + `config` (0) + `fix` (8) + `review-pr` (2) + **`demo` (3) + `badge` (2) + `split` (5) + `tests generate` (5) + `explain` (1)** |
| **Variáveis de Ambiente** | 44 chaves no `DEFAULT_CONFIG` | **49 chaves** (+5: 2 de segurança + 3 do split) — **+5 read-only fora do `DEFAULT_CONFIG`** (`GITPR_BADGE`, `GITPR_EXPLAIN_BY_DEFAULT`, 3× `GITPR_SAST_*_ENABLED`) |
| **Schema de Config** | 61 `ConfigField` / 13 categorias | **71 `ConfigField` (+10) / 14 categorias** (+ Split) |
| **Linter** | Regex + bridge Checkstyle | **+ ruleset de segredos embutido (7 regras) + wildcard `extensions: ["*"]` + 3 bridges SAST opt-in (Semgrep, Gitleaks, Bandit) com dedup multi-fonte** |
| **Hooks Git** | `HOOK_SCRIPT_SUFFIXES`, `SCRIPTS_LANG`, `effective_hook_lang()` | Inalterado (mas o pre-commit agora **bloqueia segredos** por padrão) |
| **Camada SCM** | 4 forges, `get_pull_request`, `supports_reviewable_diff` | Inalterada nesta janela |
| **i18n (chaves por arquivo)** | 1048 × 6 (paridade total) | **1158 × 6 (paridade total) — +110**, mas o código usa **1198** → **40 chaves sem tradução** ⚠️ |
| **Documentação** | 41 tópicos canônicos (35 completos + 6 parciais) | **44 tópicos canônicos (37 completos + 7 parciais) — 3 famílias novas + `docs/tutorial/`** |
| **CI** | Nenhum workflow de testes | **`.github/workflows/tests.yml`** (Python 3.10 + 3.13) 🆕 |
| **Suíte de Testes** | 1437 cenários (64 arquivos) | **1889 cenários (96 arquivos) — +452 cenários, +32 arquivos; en_us: 1883 passed / 4 failed / 2 skipped** |
| **Falhas herdadas** | 3 (2 de timeout + 1 de locale) | **0 — todas fechadas** ✅ (4 novas, uma causa raiz) |
| **Commits desde o relatório** | 5 commits | **8 commits** (`8920d13`, `da162d0`, `69f41ec`, `c38aed2`, `47784a7`, `a799664`, `7d84daf`, `6138cf1`) |
| **PRs mergeados** | 3 PRs (#167, #171, #173) | **7 PRs (#177, #179, #181, #183, #185, #187, #189)** |
| **Memory Index** | 40 padrões | **41 padrões** |
| **Relatórios de tarefas** | 93 claude-code, 5 gemini | **101 claude-code (+8) e 7 gemini (+2)** |
| **Planos de desenvolvimento** | 99 planos, 6 surveys | **115 planos (+16), 10 surveys (+4)** |

---

## **🚧 Próximos Passos**

* **Fechar a dívida das duas features novas 🆕:** registrar `tests` e `explain` em `SKILL_LABELS` (`src/config_schema.py`) e em `mcp_server.SKILL_FILES`, e rodar `python tests/sync_i18n.py` para as **40 chaves** faltantes. São **4 testes vermelhos** com uma causa raiz única — é o item mais barato desta lista e o único que hoje deixa a suíte não-verde.
* **Fechar o release 1.3.0 🆕:** o `__version__` (1.3.0) e o `__lang_version__` (v0.0.32) estão no working tree sem commit. Além disso, a entrada `[1.3.0]` do `CHANGELOG.md` **cobre apenas a varredura de segredos** — `demo`, `badge`, `split`, SAST, `tests` e `explain` precisam entrar nela antes de taguear.
* **Documentar `explain` e `tests` 🆕:** são as duas primeiras features em várias janelas a chegar sem tópico em `docs/` — só existem os templates de skill e as specs em `docs/plans/`.
* **Traduzir o que ficou parcial:** `docs/split-command.*.md` existe só em EN e PT-BR (faltam pt_pt, es_es, fr_fr), assim como `docs/review-pr.*.md`.
* **Estender a cobertura do ruleset de segredos 🆕:** as lacunas estão declaradas no próprio changelog — atribuição **sem aspas** (`API_KEY=abc123`, o formato `.env`, que é justamente onde segredos vazam), os prefixos `ASIA…`, `github_pat_…` e `xoxc-`/`xoxd-`, e a ausência de fronteira à esquerda no nome da chave (hoje `mytoken` casa igual a `token`).
* **Documentar a quebra de contrato do `request_pull_request_reviewers`:** passou de `None` para `list[str]`; subclasses de terceiros de `ScmProvider` precisam ser atualizadas. `docs/scm-multiforge.*.md` é o lugar, nas 5 versões. **Item herdado, ainda aberto.**
* **`.gitpr/metrics/export/` no `.gitignore`:** mais quatro pares CSV/JSON entraram rastreados nesta janela (`2026-09-18`, `19`, `21` e `22`). São artefatos gerados localmente. **A dívida cresceu.**
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Histogramas de tempo e tendências de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação do build e do upload para o PyPI (o CI de testes agora existe; falta o de release).
* **Seed de `.gitpr/conf/` local:** O seed de templates de configuração local (smart-excludes, linter) continua pendente como subcomando próprio ou etapa do wizard.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.
* **Extrator de i18n do `sync_i18n.py`:** O regex trunca literais com concatenação implícita (`__("a " "b")`) — migrar para AST.
* **Reconciliar a versão do projeto:** `CLAUDE.md` ainda diz `Current version: 0.0.37` enquanto o `__version__` está em 1.3.0. Definir uma convenção única. **Item herdado, ainda aberto.**
* **Dívida do índice do README:** as famílias `suggested-reviewers`, `scm-multiforge`, `config-tui` e `usage-log` continuam fora do índice (as desta janela — `demo`, `badge`, `split-command` — entraram).
* **`gitpr -h config` ignora o `-h`:** o subcomando abre a TUI em vez de mostrar a ajuda — o gate `if ctx.invoked_subcommand is not None: return` roda antes do bloco de `help_flag`. Corrigir mudaria o comportamento de `-h` para **todos** os subcomandos, então precisa de decisão.
* **Seção Smart Exclude na TUI:** dos 12 itens reportados após o uso da tela, o item 10 (*Smart Exclude*) é a única entrega ainda não iniciada.
* **Dívidas registradas no plano do config TUI:** `DEFAULT_CONFIG` ficou redundante com o schema; o banner de abertura não lista `--dashboard`, `--init`, `--base` nem `--plugins`; o `LinterApp` não desabilita a command palette.

### ✅ Concluídos nesta janela (2026-09-17 → 2026-09-23)

* ~~**Alinhar os testes de timeout desatualizados**~~ — `tests/test_net_timeouts.py` passou a asserir os 180s reais (`test_ai_timeout_defaults_to_180`) e o docstring de `get_ai_timeout()` foi corrigido. **Item que estava aberto há três relatórios.**
* ~~**Robustez de locale nos testes**~~ — `tests/conftest.py` pina `GITPR_LANG=en_us`; as **22 falhas de locale** que o CI revelou numa máquina pt-BR também desapareceram.
* ~~**Fechar o release 1.2.0**~~ — tag `v1.2.0` criada (merge do PR #174) e a entrada `[1.2.0] - 2026-09-17` está no `CHANGELOG.md`. **Era o item que bloqueava a publicação.**
* ~~**Subcomando `gitpr demo`**~~ — pacote `src/demo/` + TUI `src/ui/demo/`, pipeline real com provider falso, 2 cenários em 5 idiomas e guarda de isolamento (PR #177).
* ~~**Selo GitPR e comando `gitpr badge`**~~ — `src/branding/`, medição honesta, ponto único de injeção, opt-out `GITPR_BADGE` e 7 arquivos de teste (PR #179).
* ~~**Subcomando `gitpr split`**~~ — pacote `src/split/` (6 arquivos), `src/infrastructure/git/` com `selective_stager`, pré-validação contra índice temporário (PR #181).
* ~~**Varredura de segredos embutida**~~ — `src/security_ruleset.py` (7 regras), wildcard `extensions: ["*"]`, duas variáveis de opt-out e o alerta que nunca ecoa o valor (PR #183).
* ~~**Bridges SAST Semgrep/Gitleaks/Bandit**~~ — `src/infrastructure/linter/external/`, dedup `[Gitleaks + Regex]`, mascaramento de segredo e opt-in estrito (PR #185).
* ~~**Subcomando `gitpr tests generate`**~~ — `src/domain/tests_generation/` + `src/application/use_cases/`, detecção de framework, validação de sintaxe e chat delegando ao mesmo caso de uso (PR #187).
* ~~**Subcomando `gitpr explain` e flag `--explain`**~~ — `src/domain/pr/explain_section_builder.py` + `generate_pr_explanation.py`, parsing tolerante com detecção de `[FILL]` (PR #189).
* ~~**Primeiro CI da suíte**~~ — `.github/workflows/tests.yml` em Python 3.10 e 3.13, mais o `conftest.py` hermético e a estabilização dos testes de worker.
* ~~**Higiene de i18n na primeira execução**~~ — `i18n.py` cria o diretório do perfil antes de persistir o idioma detectado.
* ~~**`patch_applier` compartilhado**~~ — promovido a `src/infrastructure/git/`, com `src/fix/patch_applier.py` mantido como shim de re-export (nada quebrou).

---

**Relatório gerado em:** 2026-09-23  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
