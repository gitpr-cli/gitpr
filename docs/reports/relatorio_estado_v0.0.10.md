# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.10 (2026-08-11)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.10):**
- **Invocação Direta de MCP Tools via CLI (`gitpr-mcp --tool`):** As 12 tools MCP do GitPR agora podem ser invocadas diretamente da linha de comando com `gitpr-mcp --tool <name> [--tool-args '<json>']`, sem necessidade de iniciar o servidor stdio JSON-RPC. O modo `--tool` (sem nome) lista todas as tools disponíveis com suas assinaturas. Ideal para debug, scripts e uso manual.
- **Tratamento de Erro em Merge de PR:** O PR Publisher (Textual TUI) agora exibe um modal de erro visível quando o merge da PR falha — especialmente HTTP 405 indicando conflitos. Antes, a falha era ignorada silenciosamente e o fluxo prosseguia como se tudo tivesse dado certo.
- **Novos Documentos MCP:** 3 novos tópicos de documentação MCP em 5 idiomas: `mcp-annotations.md` (anotações das tools), `mcp-integration.md` (guia de integração), `mcp-prompts.md` (guia de prompts templatizados).

- **Versão atual:** 0.0.35
- **Versão dos dicionários de idioma:** v0.0.13
- **Versão dos scripts de hook:** v0.0.1
- **Publicação:** PyPI (`pip install gitpr-cli`) + GitHub Releases (binário standalone)
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)
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
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — 12 ferramentas anotadas, 15 recursos, 7 prompts.
* **Testes:** Pytest + `unittest.mock` (13 arquivos de teste, 207 cenários).
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
* **Smart Excludes com Duas Camadas:** Filtro de pathspec inteligente com camada global (`~/.gitpr/conf/`) + local do projeto (`./.gitpr/conf/`). Mesclagem em runtime (união, deduplicada). Auto-seeding do arquivo local na primeira execução. Suporte a 3 variáveis de ambiente (`GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`).
* **Métricas com Rastreamento de Tempo:** Injeção de `log_command_metric()` em todos os fluxos com repasse da duração em milissegundos (`duration_ms`) e lazy imports.
* **Resolução Centralizada de Output:** Função `resolve_output_path()` que centraliza a lógica de diretórios de saída — default em `.gitpr/reports/{type}/` com fallback para caminhos customizados do `.env`.

### **2. Sistema de Plugins Global (`src/plugins.py`)**

* **Arquitetura de Plugins:** Sistema de extensibilidade que carrega plugins do diretório `~/.gitpr/plugins/` aplicando-se a **todos os projetos**.
* **Plugins de Linter (`linter/`):** Arquivos `.yml` com regras de regex adicionais mescladas com o `.gitpr.linter.yml` local.
* **Plugins de Prompt MCP (`prompts/`):** Arquivos `.md` que estendem o contexto do sistema com instruções específicas.
* **Factory Closures:** Funções `get_linter_plugins` e `get_prompt_plugins` com closures para isolar estado entre sessões.
* **Comando `--plugins`:** Lista todos os plugins globais instalados com seus tipos e paths.
* **Documentação Multilíngue:** `docs/plugins-system.md` em 5 idiomas (EN, PT-BR, PT-PT, ES, FR).

### **3. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria a pasta `~/.gitpr/`, e solicita interativamente as chaves de API, preferências e idioma.
* **Routing de Comandos:** Gerencia todas as flags (`--commit`, `--review`, `--fullreview`, `--linter`, `--skill`, `--issue`, `--blame`, `--chat`, `--mcp`, `--install`, `--metrics`, `--export`, `--purge`, `--dashboard`, `--publish`, `--no-publish`, `--no-edit`, `--base`, `--lang`, `--provider`, `--pre-save`, `--plugins`).
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags:**
  * `--publish`: Abre a TUI interativa para revisar, editar e publicar o PR.
  * `--no-publish`: Gera a descrição do PR e salva localmente sem abrir o editor interativo.
  * `--no-edit`: Pula a TUI completamente — auto-commit (com validação do linter), auto-push e publica direto no GitHub.
  * `--base <branch>`: Sobrescreve a branch de destino do Pull Request.
  * `--plugins`: Lista plugins globais instalados.
  * `--version` 🆕: Exibe a versão atual do GitPR (via `@click.version_option`).
* **Variáveis de Ambiente:** `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `GITPR_SHOW_LOGS`, `GITPR_AUTO_MERGE`, `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`.
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub.
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **12 ferramentas anotadas + 15 recursos + 7 prompts**.
* **--install:** Assistente guiado de 4 etapas que baixa templates de skill, instala Git Hooks, configura MCP nos editores e valida chaves de API.
* **--metrics:** Sistema de telemetria local com escopo por repositório: `--export`, `--purge`, `--dashboard` (TUI interativa com varredura de cache).
* **--status:** Lista arquivos não commitados categorizados (new/modified/deleted) — rápido, sem IA, sem rede.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI construída com Textual para revisar, editar e publicar Pull Requests diretamente no terminal.
* **6 Telas Modais:** `CommitConfirmScreen`, `FileStageScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen`.
* **Modal de Arquivos Unstaged Aprimorado:** Lista de arquivos com altura fixa (`height: 6`) e scroll interno vertical.
* **Bindings:** F1 (Help), F2 (Salvar .md local), F3 (Publicar via GitHub API), Esc (Sair).
* **Fluxo de Auto-Commit:** Linter → mensagem IA → confirma → commita → push → publica PR.
* **Verificação de Arquivos Unstaged:** Ao iniciar, verifica `git status --porcelain` e oferece modal para selecionar, pular ou cancelar.
* **Tratamento de PR Existente:** Detecta PRs abertos para a branch atual via GitHub API e oferece push ou criar novo.
* **Auto-Upstream:** Detecta falha de `git push` por falta de upstream e automaticamente tenta `--set-upstream origin <branch>`.
* **Detecção de "Nothing to commit":** Trata `git commit` sem mudanças como sucesso.
* **Merge Flow:** Após criação/atualização do PR, oferece opção de merge. Controlado por `GITPR_AUTO_MERGE`.
* **Tratamento de Erro de Merge 🆕:** Refatoração de `_do_merge` em 3 métodos com separação de responsabilidades: `_do_merge` (dispara em thread), `_on_merge_success` (callback de sucesso), `_on_merge_failure` (callback de falha com modal de erro). HTTP 405 (conflitos) exibe mensagem clara e oferece abrir no browser para resolução manual. Rastreamento de `final_action` ("merged"/"merge_failed") para feedback visual pós-TUI com cores corretas.

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Funções Compartilhadas:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` — encapsulando chamadas REST à API do GitHub v3.
* **Autenticação via PAT:** Token de acesso pessoal validado com `GET /user` antes das operações.
* **Reaproveitamento:** Funções usadas tanto pela TUI de PR quanto pela TUI de issues.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no git diff sem gastar cotas de IA.
* **Regras YAML:** Lê o arquivo local `.gitpr.linter.yml` (criado via `--skill`). Suporta regex de validação, ignorar comentários e ignorar diretórios específicos.
* **Plugins de Linter:** Regras adicionais carregadas de `~/.gitpr/plugins/linter/*.yml` e mescladas com as regras locais.
* **Template multilíngue:** Templates do linter disponíveis em 5 idiomas.
* **Integração no Auto-Commit:** Executado automaticamente antes do commit no fluxo de PR publication.

### **7. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data` e `decrypt_data` para proteger chaves de API de IA e GitHub PAT.
* **Validação de Token do GitHub:** `validate_github_token()` com chamada leve (`GET /user`).
* **Fluxo de Auto-Reauth:** Se o token expirar durante `gitpr -is`, captura 401, solicita novo token e relança TUI preservando o rascunho.

### **8. Auto-Updater (`src/updater.py`)**

* **Hot-Swap:** Verifica na API do GitHub Releases a versão mais recente, baixa o binário compilado e substitui sem quebrar a execução em andamento (com rollback).
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Verificação de conexão:** Socket `8.8.8.8:53` antes de qualquer operação de rede.
* **Versionamento Centralizado:** `__version__` (0.0.35), `__lang_version__` (v0.0.13), `__scripts_version__` (v0.0.1), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`.

### **9. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Construída com Textual — histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico de conversa persistido por branch, permitindo continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear` — atalhos para pair programming.
* **Auto-Patching (F5):** Extrai blocos de código sugeridos pela IA e exporta para arquivo de patch.
* **Atualização de Diff (F2):** Recarrega o `git diff` atual sem reiniciar a sessão.
* **Exportação de Sessão (F6):** Salva o histórico completo do chat para documentação.

### **10. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com suporte a placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas:** en_us (padrão/fallback), pt_br, pt_pt, es_es, fr_fr.
* **Arquivos Versionados:** `__lang_version__` (v0.0.13) controla atualização dos pacotes de idioma (`langs/*.json`).
* **Cobertura:** 503 chaves de tradução em pt_BR.
* **Cache com Indexação por Idioma:** Respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.
* **Script de Sincronização:** `tests/sync_i18n.py` para detecção automática de chaves órfãs.

### **11. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **Delimitador:** Separador de frases por ponto e vírgula (`;`), compatível com frases complexas contendo vírgulas.
* **Velocidade Adaptativa & Flickering:** Animação de descoberta de caracteres adaptada para frases longas e uso do ANSI `\033[K` para evitar artefatos visuais no terminal.
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas.

### **12. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Medição de Duração:** Injeção de `duration_ms` (cronometragem de alta precisão via `time.perf_counter()`) no `meta_raw` e `_telemetry_meta`.
* **Modo JSON & Parâmetros Determinísticos:** Outputs estruturados com `temperature=0.0` e `top_p=0.1`.

### **13. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt.
* **Indexação por Idioma:** O campo `lang` foi adicionado ao chaveamento de cache.
* **Telemetria e Duração:** Persistência do campo `duration_ms` e `meta_raw` em arquivos de cache.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` lê todos os arquivos de cache recursivamente.

### **14. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`), e Arqueologia por Blame (`-b`).
* **Map-Reduce para Issues:** Quando o contexto excede ~90k tokens, divide automaticamente em chunks e unifica os resultados.
* **TUI Interativa:** Edição de rascunhos, atalho F2 (salvar local), F3 (publicar no GitHub) e F1 (help).
* **Tratamento de 401:** Sinalização de reautenticação sem fechamento da aplicação.

### **15. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia a evolução e autoria histórica de trechos de código com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos registrados via `log_blame_metric()` com rastreamento de profundidade e número de commits analisados.

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)** 🆕

* **12 Ferramentas MCP Anotadas:** Ferramentas para `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`.
* **15 Recursos + 7 Prompts Templatizados:** 35 arquivos de template em `templates/gitpr.prompt.*.md`.
* **Invocação CLI Direta 🆕:** Comando `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool MCP diretamente sem iniciar o servidor stdio JSON-RPC.
* **Registry Pattern 🆕:** `_TOOL_FUNCS` mapeia nome da tool → callable; `_get_tool_registry()` faz merge com metadados do catálogo.
* **Real Stdout Isolation 🆕:** `_write_real_stdout()` escreve diretamente no `sys.__stdout__` original (salvo antes do monkey-patching), garantindo JSON puro no stdout.
* **Listagem de Tools 🆕:** `gitpr-mcp --tool` (sem nome) lista todas as 12 tools disponíveis com assinaturas de parâmetros.
* **Carregamento Automático do .env 🆕:** API keys disponíveis automaticamente no modo CLI.
* **Novos Documentos MCP 🆕:** `docs/mcp-annotations.md`, `docs/mcp-integration.md`, `docs/mcp-prompts.md` em 5 idiomas cada (15 novos arquivos).
* **Instalador Automático:** Configuração de editores suportados (VS Code, Cursor, Claude Code, Claude Desktop, Zed) com merge JSON inteligente.

### **17. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório (Repo-Scope):** Rótulo `📁 Repository: owner/repo` e filtragem estrita de eventos e dados de cache por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background com widget `ProgressBar`.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de cache ao totalizador.
* **Controle de Estado de Cache:** Arquivo de registro em `./.gitpr/metrics/{repo}/processed_cache.json`.
* **Exportação Local:** Salvamento de CSV/JSON em `./.gitpr/metrics/export/`.

### **18. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos indexados por `repo_name`.
* **Novos Eventos:** Eventos de listagem de arquivos unstaged e exportação de telemetria.
* **Eventos de Hook:** `log_hook_event()` para hooks Git (pre-commit, prepare-commit-msg, post-checkout, pre-push, post-merge).
* **Eventos de Linter e Blame:** `log_linter_metric()` e `log_blame_metric()`.
* **Exportação Local:** `--metrics --export` gera CSV e JSON em `./.gitpr/metrics/export/` com filtro por repositório.
* **Limpeza:** `--metrics --purge` remove todos os arquivos de métricas locais com confirmação interativa.

### **19. Sincronização de Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (v0.0.1) controla a versão dos scripts de hook.
* **Detecção Automática:** Compara versão local com a mais recente e atualiza automaticamente.
* **Idioma-Aware:** Baixa templates de hook correspondentes ao idioma configurado.

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_core.py` | 25+ | Fluxos principais, git diff, PR generation, timing |
| `tests/test_chat_backend.py` | 30+ | Memória de chat, persistência, comandos slash |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_mcp_server.py` | 75+ 🆕 | Ferramentas MCP, recursos, annotations, patching, CLI direto |
| `tests/test_metrics.py` | 36+ | Coleta, exportação local, escopo de repo, cache token summary, duration_ms |
| `tests/test_smart_excludes.py` | 14+ | Filtro pathspec inteligente |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_blame_metrics.py` | 10+ | Métricas de blame: profundidade, commits, duração |
| `tests/test_linter_metrics.py` | 8+ | Métricas de linter: erros, warnings, duração |
| `tests/test_thinking_words.py` | 9+ | Carregamento e parsing com separador `;` |
| `tests/test_skill_command.py` | 5+ | Download e validação de templates de skill |
| `tests/test_install_wizard.py` | 5+ | Assistente interativo de instalação |
| `tests/test_pre_save.py` | 3+ | Flag --pre-save e payload JSON |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (chaves órfãs) |

**Total:** 207 cenários de teste automatizados passando (13 arquivos de teste). 1 falha conhecida em `test_metrics.py::test_app_skips_export_and_config_files` (pré-existente, não relacionada às mudanças recentes).

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** 503 chaves de tradução em pt_BR.
* **Novos Documentos Técnicos 🆕:** 3 novos tópicos MCP em 5 idiomas cada (15 arquivos):
  - `docs/mcp-annotations.md` — catálogo de anotações das 12 ferramentas MCP
  - `docs/mcp-integration.md` — guia de integração MCP em editores (VS Code, Cursor, Claude Code, Claude Desktop, Zed)
  - `docs/mcp-prompts.md` — referência dos 7 prompts templatizados MCP
* **Documentação Existente:** `docs/plugins-system.md`, `docs/smart-excludes.md`, `docs/untracked-files.md` e mais — todos em 5 idiomas.
* **Documentação em 5 idiomas:** 37 tópicos únicos em `docs/` (+3 novos tópicos MCP).
* **Memory Index:** `.claude/memory/MEMORY.md` com 20 padrões de arquitetura (+2 novos: mcp-tool-cli-invocacao-direta, merge-conflict-error-handling).
* **Relatórios de tarefas:** `docs/claude-code/reports/` e `docs/reports/` (10 relatórios de status).
* **Planos de desenvolvimento:** 10+ planos documentados em `docs/plans/`.

---

## **🔄 Pipeline de Distribuição**

1. **PyPI:** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **GitHub Releases:** PyInstaller → `.exe` standalone → upload automatizado
3. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml`
4. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`

---

## **📈 Evolução desde o Relatório Anterior (v0.0.9)**

| Área | v0.0.9 (anterior) | v0.0.10 (atual) |
|------|-------------------|----------------|
| **Versão GitPR** | 0.0.34 | **0.0.35** |
| **Versão Idioma** | v0.0.12 | **v0.0.13** |
| **Versão Scripts Hook** | v0.0.1 | v0.0.1 |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 (en, pt_br, pt_pt, es_es, fr_fr) | 5 (en, pt_br, pt_pt, es_es, fr_fr) |
| **Interface** | CLI + TUI Issues + Chat TUI + MCP Server + Dashboard + PR Publisher TUI | CLI + TUI Issues + Chat TUI + MCP Server + Dashboard + PR Publisher TUI + **MCP CLI Direto** |
| **Ferramentas MCP** | 10 tools | **12 tools (+ list_unstaged_files, analyze_unstaged_diff)** |
| **MCP CLI Direto** | — | **`gitpr-mcp --tool <name>` — invocação direta sem servidor** |
| **PR Merge Tratamento** | Fluxo ignorava erro de merge | **Modal de erro para HTTP 405 (conflitos) + feedback visual** |
| **Flags CLI** | 25 flags | **26 flags (+ `--version`)** |
| **Variáveis de Ambiente** | 16 vars | 16 vars |
| **Documentação** | 34 tópicos | **37 tópicos (+3: mcp-annotations, mcp-integration, mcp-prompts em 5 idiomas)** |
| **Suíte de Testes** | 171 cenários (13 arquivos) | **207 cenários (13 arquivos, +36 testes MCP)** |
| **Commits desde v0.0.34** | — | **2 commits (mcp-tool-cli + merge-error-handling)** |
| **PRs mergeados** | — | **2 PRs (#107, #110)** |

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

**Relatório gerado em:** 2026-08-11  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
