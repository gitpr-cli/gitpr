# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.9 (2026-08-10)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.9):**
- **Sistema Global de Plugins (`~/.gitpr/plugins/`):** Arquitetura de plugins que permite extender o GitPR com regras de linter aditivas e templates de prompt MCP dinâmicos. Plugins instalados em `~/.gitpr/plugins/linter/` (YAML) e `~/.gitpr/plugins/prompts/` (Markdown) aplicam-se a **todos os projetos** sem duplicação. Factory closures garantem isolamento entre sessões.
- **Smart Excludes Local por Projeto:** Cada projeto pode definir exclusões específicas em `.gitpr/conf/gitpr.smart-excludes.json`. O arquivo é criado automaticamente na primeira execução (template com lista vazia), mesclado com a lista global em runtime (união, sem duplicatas), e seguro para versionar no repositório — toda a equipe herda as mesmas exclusões.
- **Map-Reduce para Geração de Issues:** O sistema de Map-Reduce (divisão de diffs grandes em chunks) foi estendido para suportar geração de Issues além de PRs e commits. Ativação automática quando o diff excede ~90k tokens estimados.
- **Tokenizador Local (`tokenizer.json`):** Adicionado tokenizador local para estimativa mais precisa de tokens antes do envio para a IA, reduzindo chamadas desnecessárias à API.
- **Melhorias no Tratamento de Arquivos Unstaged:** Detecção e listagem de arquivos não-stageados (`list_unstaged_files`) com categorização (new/modified/deleted) e exportação para telemetria. Modal TUI aprimorado com lista de arquivos com scroll interno e altura reduzida.
- **3 Novas Variáveis de Ambiente:** `GITPR_SKIP_SMART_EXCLUDES` (desabilitar todas as exclusões), `GITPR_SMART_EXCLUDES_GLOBAL` (caminho alternativo para arquivo global), `GITPR_SMART_EXCLUDES_LOCAL` (caminho alternativo para arquivo local).
- **Documentação do Sistema de Plugins:** `docs/plugins-system.md` em 5 idiomas (EN, PT-BR, PT-PT, ES, FR) com guia completo de criação e instalação de plugins.
- **Documentação de Smart Excludes Atualizada:** Todos os 5 idiomas atualizados com configuração local por projeto, cadeia de resolução de 5 etapas, e FAQ revisado.

- **Versão atual:** 0.0.34
- **Versão dos dicionários de idioma:** v0.0.12
- **Versão dos scripts de hook:** v0.0.1
- **Publicação:** PyPI (`pip install gitpr-cli`) + GitHub Releases (binário standalone)
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal).
* **UI/Terminal:** Textual — TUI (Text User Interface) para chat interativo, edição de issues, help screen, dashboard de métricas e PR Publisher.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API e tokens GitHub.
* **Configuração:** `python-dotenv`, `pyyaml` (para o linter estático).
* **IA Providers:** Integração via SDK oficial do Google GenAI (`gemini-2.5-flash`), OpenAI SDK (`DeepSeek`), e OpenAI SDK (`Ollama` local).
* **GitHub API:** `requests` (REST API via PAT) — módulo `src/github_api.py` com `create_pull_request()`, `update_pull_request()`, `merge_pull_request()`.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — Tool Annotations, Prompts com templates e prompt:// resources.
* **Testes:** Pytest + `unittest.mock` (13 arquivos de teste, 171 cenários).
* **Empacotamento:** PyInstaller (binário standalone) + setuptools/build (PyPI).
* **CI/CD:** GitHub Actions (`pr-review.yml`) + `action.yml` para execução em pipelines.

---

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa ~90k tokens, divide automaticamente em lotes por arquivo (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce) mantendo o tom de voz da arquitetura. **Estendido para geração de Issues** 🆕.
* **Tokenizador Local 🆕:** `tokenizer.json` para estimativa precisa de tokens antes do envio para a IA, evitando chamadas que excederiam o limite do modelo.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()` com fallback para tokenizador local.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff` para reduzir contexto inútil.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo (system instruction + prompt) em JSON antes de cada chamada à IA.
* **Smart Excludes Aprimorado 🆕:** Filtro de pathspec inteligente agora com **duas camadas**: global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`). Mesclagem em runtime (união, deduplicada). Auto-seeding do arquivo local na primeira execução. Suporte a 3 novas variáveis de ambiente (`GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`).
* **Métricas com Rastreamento de Tempo:** Injeção de `log_command_metric()` em todos os fluxos com repasse da duração em milissegundos (`duration_ms`) e lazy imports para evitar importação circular.
* **Resolução Centralizada de Output:** Função `resolve_output_path()` que centraliza a lógica de diretórios de saída — default em `.gitpr/reports/{type}/` com fallback para caminhos customizados do `.env`.

### **2. Sistema de Plugins Global (`src/plugins.py`)** 🆕

* **Arquitetura de Plugins:** Sistema de extensibilidade que carrega plugins do diretório `~/.gitpr/plugins/` aplicando-se a **todos os projetos**.
* **Plugins de Linter (`linter/`):** Arquivos `.yml` com regras de regex adicionais mescladas com o `.gitpr.linter.yml` local. Suporte a todas as diretivas do linter: `name`, `regex`, `extensions`, `message`, `ignore_comments`, `ignore_paths`, `require_paths`.
* **Plugins de Prompt MCP (`prompts/`):** Arquivos `.md` que estendem o contexto do sistema com instruções específicas (ex: frameworks, padrões de código, regras de negócio). Injetados dinamicamente como system instructions nas chamadas MCP.
* **Factory Closures:** As funções de carregamento (`get_linter_plugins`, `get_prompt_plugins`) usam closures para isolar estado entre sessões e evitar vazamento de memória.
* **Resolução de Path:** Função `get_plugin_dir()` que resolve diretórios de plugin a partir do `~/.gitpr/plugins/`.
* **Comando `--plugins`:** Lista todos os plugins globais instalados com seus tipos e paths.
* **Documentação Multilíngue 🆕:** `docs/plugins-system.md` em 5 idiomas (EN, PT-BR, PT-PT, ES, FR).

### **3. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria a pasta `~/.gitpr/`, e solicita interativamente as chaves de API, preferências e idioma, salvando num `.env`.
* **Routing de Comandos:** Gerencia todas as flags (`--commit`, `--review`, `--fullreview`, `--linter`, `--skill`, `--issue`, `--blame`, `--chat`, `--mcp`, `--install`, `--metrics`, `--export`, `--purge`, `--dashboard`, `--publish`, `--no-publish`, `--no-edit`, `--base`, `--lang`, `--provider`, `--pre-save`, `--plugins`).
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags Existentes:**
  * `--publish`: Abre a TUI interativa para revisar, editar e publicar o PR (comportamento padrão).
  * `--no-publish`: Gera a descrição do PR e salva localmente sem abrir o editor interativo.
  * `--no-edit`: Pula a TUI completamente — faz auto-commit (com validação do linter), auto-push e publica direto no GitHub. Ideal para CI/CD.
  * `--base <branch>`: Sobrescreve a branch de destino do Pull Request.
  * `--plugins` 🆕: Lista plugins globais instalados (`~/.gitpr/plugins/linter/` e `~/.gitpr/plugins/prompts/`).
* **Novas Variáveis de Ambiente 🆕:** `GITPR_SKIP_SMART_EXCLUDES` (pular todas as exclusões), `GITPR_SMART_EXCLUDES_GLOBAL` (caminho alternativo para arquivo global), `GITPR_SMART_EXCLUDES_LOCAL` (caminho alternativo para arquivo local).
* **Variáveis Existentes:** `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `GITPR_SHOW_LOGS`, `GITPR_AUTO_MERGE`.
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub.
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **10 ferramentas anotadas + 15 recursos + 7 prompts**.
* **--install:** Assistente guiado de 4 etapas que baixa templates de skill, instala Git Hooks, configura MCP nos editores e valida chaves de API.
* **--metrics:** Sistema de telemetria local com escopo por repositório: `--export` (salva em `./.gitpr/metrics/export/`), `--purge` (limpeza), `--dashboard` (TUI interativa com varredura de cache).
* **--status:** Lista arquivos não commitados categorizados (new/modified/deleted) — rápido, sem IA, sem rede 🆕.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI construída com Textual para revisar, editar e publicar Pull Requests diretamente no terminal.
* **6 Telas Modais:** `CommitConfirmScreen`, `FileStageScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen`.
* **Modal de Arquivos Unstaged Aprimorado 🆕:** Lista de arquivos com altura fixa (`height: 6`) e scroll interno vertical. Título e botões sempre visíveis. `StageFilesScreen` e `FileStageScreen` refatoradas com CSS otimizado.
* **Bindings:** F1 (Help — modal com atalhos e instruções), F2 (Salvar .md local), F3 (Publicar via GitHub API), Esc (Sair).
* **Fluxo de Auto-Commit:** Quando há mudanças não commitadas e o usuário usa `--no-edit` ou F3, o GitPR automaticamente executa linter → gera mensagem IA → confirma → commita → push → publica PR.
* **Verificação de Arquivos Unstaged:** Ao iniciar, verifica `git status --porcelain` e oferece modal para selecionar, pular ou cancelar.
* **Tratamento de PR Existente:** Detecta PRs abertos para a branch atual via GitHub API e oferece push para o PR existente ou criar um novo.
* **Auto-Upstream:** Detecta falha de `git push` por falta de upstream e automaticamente tenta `--set-upstream origin <branch>`.
* **Detecção de "Nothing to commit":** Trata `git commit` sem mudanças como sucesso — o fluxo continua sem erro.
* **Merge Flow:** Após criação/atualização do PR, oferece opção de merge. Controlado por `GITPR_AUTO_MERGE`.

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Funções Compartilhadas:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` — encapsulando chamadas REST à API do GitHub v3.
* **Autenticação via PAT:** Token de acesso pessoal validado com `GET /user` antes das operações.
* **Reaproveitamento:** Funções usadas tanto pela TUI de PR quanto pela TUI de issues, eliminando duplicação.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no git diff sem gastar cotas de IA.
* **Regras YAML:** Lê o arquivo local `.gitpr.linter.yml` (criado via `--skill`). Suporta regex de validação, ignorar comentários e ignorar diretórios específicos (usando fnmatch).
* **Plugins de Linter 🆕:** Regras adicionais carregadas de `~/.gitpr/plugins/linter/*.yml` e mescladas com as regras locais.
* **Template multilíngue:** Templates do linter disponíveis em 5 idiomas.
* **Integração no Auto-Commit:** O linter é executado automaticamente antes do commit no fluxo de PR publication.

### **7. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data` e `decrypt_data` para proteger chaves de API de IA e GitHub PAT.
* **Validação de Token do GitHub:** Função `validate_github_token()` realiza uma chamada leve (`GET /user`) para validar o PAT.
* **Fluxo de Auto-Reauth:** Se o token expirar ou for inválido durante o `gitpr -is`, a aplicação captura a resposta 401 HTTP, solicita um novo token ao usuário e relança a interface TUI preservando o rascunho.

### **8. Auto-Updater (`src/updater.py`)**

* **Hot-Swap:** Verifica na API do GitHub Releases a versão mais recente. Se houver divergência, baixa o binário compilado, renomeia o executável atual e substitui sem quebrar a execução em andamento (com capacidade de rollback).
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Verificação de conexão:** Socket `8.8.8.8:53` antes de qualquer operação de rede.
* **Versionamento Centralizado:** `__version__` (0.0.34), `__lang_version__` (v0.0.12), `__scripts_version__` (v0.0.1), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION` — todos derivados exclusivamente do `updater.py`.

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Construída com Textual — histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico de conversa persistido por branch, permitindo continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear` — atalhos para ações comuns de pair programming.
* **Auto-Patching (F5):** Extrai blocos de código sugeridos pela IA e exporta para arquivo de patch para fácil aplicação.
* **Atualização de Diff (F2):** Recarrega o `git diff` atual sem reiniciar a sessão.
* **Exportação de Sessão (F6):** Salva o histórico completo do chat para documentação.

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com suporte a placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas:** en_us (padrão/fallback), pt_br, pt_pt, es_es, fr_fr.
* **Arquivos Versionados:** `__lang_version__` (v0.0.12) controla atualização dos pacotes de idioma (`langs/*.json`).
* **Cobertura:** 503 chaves de tradução em pt_BR. Novas strings para sistema de plugins, Smart Excludes local, e listagem de arquivos unstaged.
* **Cache com Indexação por Idioma:** Respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.
* **Script de Sincronização:** `tests/sync_i18n.py` para detecção automática de chaves órfãs.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **Delimitador:** Separador de frases por ponto e vírgula (`;`), compatível com frases complexas contendo vírgulas.
* **Velocidade Adaptativa & Flickering:** Animação de descoberta de caracteres adaptada para frases longas e uso do ANSI `\033[K` para evitar artefatos visuais no terminal.
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas nos arquivos `templates/gitpr.thinking-words.{lang}.md`.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Medição de Duração:** Injeção de `duration_ms` (cronometragem de alta precisão via `time.perf_counter()`) no `meta_raw` e `_telemetry_meta`.
* **Modo JSON & Parâmetros Determinísticos:** Outputs estruturados com `temperature=0.0` e `top_p=0.1`.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt.
* **Indexação por Idioma:** O campo `lang` foi adicionado ao chaveamento de cache, permitindo respostas distintas para o mesmo diff em idiomas diferentes.
* **Telemetria e Duração:** Persistência do campo `duration_ms` e `meta_raw` em arquivos de cache em `~/.gitpr/cache/prompts/`.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` lê todos os arquivos de cache recursivamente para computar métricas históricas completas.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`), e Arqueologia por Blame (`-b`).
* **Map-Reduce para Issues 🆕:** Quando o contexto (diff/histórico) excede ~90k tokens, o sistema divide automaticamente em chunks e processa via Map-Reduce, unificando os resultados.
* **TUI Interativa:** Edição de rascunhos, atalho F2 (salvar local), F3 (publicar no GitHub via API REST) e F1 (help).
* **Tratamento de 401:** Sinalização de reautenticação sem fechamento da aplicação com perda de conteúdo.

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia a evolução e autoria histórica de trechos de código com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos de arqueologia registrados via `log_blame_metric()` com rastreamento de profundidade e número de commits analisados.

### **16. Servidor MCP e Instalador (`src/mcp_server.py`)**

* **10 Ferramentas MCP Anotadas 🆕:** Novas ferramentas para `analyze_unstaged_diff` e `list_unstaged_files` com annotations completas.
* **15 Recursos + 7 Prompts Templatizados:** 35 arquivos de template em `templates/gitpr.prompt.*.md`.
* **Instalador Automático:** Configuração de editores suportados (VS Code, Cursor, Claude Code, Claude Desktop, Zed) com merge JSON inteligente.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório (Repo-Scope):** Rótulo `📁 Repository: owner/repo` e filtragem estrita de eventos e dados de cache por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background que carrega dados de cache enquanto exibe o widget `ProgressBar` da Textual.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de chamadas de cache ao totalizador do dashboard.
* **Controle de Estado de Cache:** Arquivo de registro em `./.gitpr/metrics/{repo}/processed_cache.json`.
* **Exportação Local:** Salvamento de CSV/JSON em `./.gitpr/metrics/export/`.

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos de métricas são indexados por `repo_name`, permitindo isolamento entre projetos.
* **Novos Eventos 🆕:** Eventos de listagem de arquivos unstaged e exportação de telemetria.
* **Eventos de Hook:** `log_hook_event()` para hooks Git (pre-commit, prepare-commit-msg, post-checkout, pre-push, post-merge).
* **Eventos de Linter e Blame:** `log_linter_metric()` para linter standalone, `log_blame_metric()` para arqueologia de código.
* **Exportação Local:** `--metrics --export` gera CSV e JSON em `./.gitpr/metrics/export/` com filtro por repositório.
* **Limpeza:** `--metrics --purge` remove todos os arquivos de métricas locais com confirmação interativa.

### **19. Sincronização de Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (v0.0.1) no `updater.py` controla a versão dos scripts de hook separadamente dos dicionários de idioma.
* **Detecção Automática:** Ao executar `--installhooks`, o sistema compara a versão local (armazenada no `.env`) com a versão mais recente e atualiza automaticamente se necessário.
* **Idioma-Aware:** Detecta o idioma configurado e baixa os templates de hook correspondentes.

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_core.py` | 25+ | Fluxos principais, git diff, PR generation, timing |
| `tests/test_chat_backend.py` | 30+ | Memória de chat, persistência, comandos slash |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP 🆕 |
| `tests/test_skill_command.py` | 5+ | Download e validação de templates de skill |
| `tests/test_pre_save.py` | 3+ | Flag --pre-save e payload JSON |
| `tests/test_smart_excludes.py` | 14+ | Filtro pathspec inteligente |
| `tests/test_thinking_words.py` | 9+ | Carregamento e parsing com separador `;` |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 33 | Ferramentas MCP, recursos, annotations e patching |
| `tests/test_metrics.py` | 36+ | Coleta, exportação local, escopo de repo, cache token summary, duration_ms |
| `tests/test_install_wizard.py` | 5+ | Assistente interativo de instalação |
| `tests/test_blame_metrics.py` | 10+ | Métricas de blame: profundidade, commits, duração |
| `tests/test_linter_metrics.py` | 8+ | Métricas de linter: erros, warnings, duração |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (chaves órfãs) |

**Total:** 171 cenários de teste automatizados passando (13 arquivos de teste). 1 falha conhecida em `test_metrics.py::test_app_skips_export_and_config_files` (pré-existente, não relacionada às mudanças recentes).

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** 503 chaves de tradução em pt_BR.
* **Nova Documentação Técnica 🆕:** `docs/plugins-system.md` em 5 idiomas (EN, PT-BR, PT-PT, ES, FR) com guia completo do sistema de plugins.
* **Documentação de Smart Excludes Atualizada 🆕:** `docs/smart-excludes.md` em 5 idiomas com configuração local por projeto, cadeia de resolução de 5 etapas, e FAQ revisado.
* **Documentação de Untracked Files Expandida 🆕:** `docs/untracked-files.md` agora disponível em todos os 5 idiomas (eram 2: EN e PT-BR).
* **READMEs Atualizados 🆕:** Todos os 5 READMEs atualizados com exemplo de configuração local do Smart Excludes (JSON).
* **Documentação em 5 idiomas:** 34 tópicos únicos em `docs/` traduzidos para EN, PT-BR, PT-PT, ES, FR (+1 novo tópico: plugins-system).
* **Memory Index:** `.claude/memory/MEMORY.md` com 16 padrões de arquitetura (+2 novos: plugin-system-architecture, nothing-to-commit-detection).
* **Relatórios de tarefas:** `docs/claude-code/reports/` e `docs/reports/` (9 relatórios de status).
* **Planos de desenvolvimento:** 9+ planos documentados em `docs/plans/`.

---

## **🔄 Pipeline de Distribuição**

1. **PyPI:** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **GitHub Releases:** PyInstaller → `.exe` standalone → upload automatizado
3. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml`
4. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`

---

## **📈 Evolução desde o Relatório Anterior (v0.0.8)**

| Área | v0.0.8 (anterior) | v0.0.9 (atual) |
|------|-------------------|----------------|
| **Versão GitPR** | 0.0.33 | **0.0.34** |
| **Versão Idioma** | v0.0.11 | **v0.0.12** |
| **Versão Scripts Hook** | v0.0.1 | v0.0.1 |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 (en, pt_br, pt_pt, es_es, fr_fr) | 5 (en, pt_br, pt_pt, es_es, fr_fr) |
| **Interface** | CLI + TUI Issues + Chat TUI + MCP Server + Dashboard + PR Publisher TUI | CLI + TUI Issues + Chat TUI + MCP Server + Dashboard + PR Publisher TUI |
| **Sistema de Plugins** | — | **Plugins globais (~/.gitpr/plugins/) — linter + prompts MCP** |
| **Smart Excludes** | Global apenas | **Global + Local por projeto (merge em runtime)** |
| **Map-Reduce** | PRs e commits | **+ Issues (3 contextos cobertos)** |
| **Tokenizador Local** | Apenas heurística | **+ tokenizer.json para estimativa precisa** |
| **Novas Flags CLI** | 24 flags | **25 flags (+ `--plugins`, `--status`)** |
| **Variáveis de Ambiente** | 13 vars | **16 vars (+3: SKIP_SMART_EXCLUDES, SMART_EXCLUDES_GLOBAL, SMART_EXCLUDES_LOCAL)** |
| **Documentação** | 24 tópicos | **34 tópicos (+ plugins-system em 5 idiomas, smart-excludes atualizado, untracked-files expandido)** |
| **READMEs** | Básico | **5 READMEs atualizados com exemplo local Smart Excludes** |
| **Suíte de Testes** | 131 cenários (12 arquivos) | **171 cenários (13 arquivos, +40 testes de plugin)** |
| **TUI Modal Unstaged** | Lista expandida com scroll do modal | **Lista com altura fixa e scroll interno** |
| **Commits desde v0.0.33** | — | **7 commits (plugins + smart-excludes + map-reduce + unstaged)** |

---

## **🚧 Próximos Passos**

* **Testes para PR Publisher:** Cobertura de testes unitários e de integração para o fluxo de PR publication (`pr_publish_app.py`, `github_api.py`).
* **Testes de integração end-to-end para MCP:** Validação de chamadas de ferramentas e prompts via cliente stdio simulado.
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Adicionar histogramas de tempo e gráficos de tendência de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação completa do build PyInstaller e envio de assets para o GitHub Releases.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.
* **Comando `--init` local:** Seed de `.gitpr/conf/` com templates de configuração local (smart-excludes, linter, etc.).

---

**Relatório gerado em:** 2026-08-10  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
