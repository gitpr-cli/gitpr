# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.33 (2026-08-09)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.8):**
- **PR Publisher TUI (`gitpr` padrão):** Interface interativa no terminal para revisar, editar e publicar Pull Requests diretamente no GitHub via REST API. Inclui edição de título, corpo e branch base com bindings F1 (Help), F2 (Salvar local), F3 (Publicar) e Esc (Sair). Fluxo completo com 6 telas modais para commit, staging e progresso.
- **Fluxo de Auto-Commit Inteligente:** Ao usar `--no-edit` ou publicar com F3 com mudanças não commitadas, o GitPR executa o linter estático, gera uma mensagem de commit por IA (Conventional Commits), confirma com o usuário e executa `git commit` antes de publicar o PR.
- **Gestão de Arquivos Não-Stageados:** No início, o GitPR verifica arquivos não-stageados e oferece um modal TUI (`StageFilesApp`) para selecionar, pular ou cancelar antes da geração do PR.
- **Tratamento de PR Existente:** Quando um PR já existe para a branch atual, a TUI oferece push para o PR existente (atualizando o corpo via PATCH) ou criar um novo.
- **Fluxo de Merge:** Após criação ou atualização do PR, o GitPR pode opcionalmente fazer o merge. Controlado pela variável de ambiente `GITPR_AUTO_MERGE`.
- **Auto-Upstream no Push:** Quando `git push` falha por falta de upstream, o GitPR automaticamente tenta novamente com `--set-upstream origin <branch>`.
- **Detecção de "Nothing to commit":** Falhas de commit por ausência de mudanças staged são tratadas como sucesso — o fluxo continua para a publicação do PR.
- **Centralização de Output:** Todos os arquivos gerados agora usam `.gitpr/reports/` organizados por tipo (`pr_desc/`, `review/`, `full_review/`, `file_review/`, `blame/`, `issue/`). Caminhos customizados no `.env` são respeitados para compatibilidade.
- **6 Novas Variáveis de Ambiente:** `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `GITPR_SHOW_LOGS`, `GITPR_AUTO_MERGE` — controle granular do fluxo de publicação.
- **Módulo de API do GitHub (`src/github_api.py`):** Funções compartilhadas para `create_pull_request()`, `update_pull_request()` e `merge_pull_request()` via REST API.
- **Documentação Técnica Multilíngue:** `docs/pull-request-publication.md` em 5 idiomas (EN, PT-BR, PT-PT, ES, FR) com cobertura completa do fluxo de PR.
- **CHANGELOG.md:** Histórico completo de versões de v0.0.1 até v0.0.33 no formato Keep a Changelog, populado a partir dos relatórios de status em `docs/reports/`.

- **Versão atual:** 0.0.33
- **Versão dos dicionários de idioma:** v0.0.11
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
* **UI/Terminal:** Textual — TUI (Text User Interface) para chat interativo, edição de issues, help screen, dashboard de métricas e **PR Publisher** 🆕.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API e tokens GitHub.
* **Configuração:** `python-dotenv`, `pyyaml` (para o linter estático).
* **IA Providers:** Integração via SDK oficial do Google GenAI (`gemini-2.5-flash`), OpenAI SDK (`DeepSeek`), e OpenAI SDK (`Ollama` local).
* **GitHub API:** `requests` (REST API via PAT) — **uso expandido com novo módulo `github_api.py`** 🆕.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — Tool Annotations, Prompts com templates e prompt:// resources.
* **Testes:** Pytest + `unittest.mock` (12 arquivos de teste, 131 cenários).
* **Empacotamento:** PyInstaller (binário standalone) + setuptools/build (PyPI).
* **CI/CD:** GitHub Actions (`pr-review.yml`) + `action.yml` para execução em pipelines.

---

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa ~90k tokens, divide automaticamente em lotes por arquivo (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce) mantendo o tom de voz da arquitetura.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()`.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff` para reduzir contexto inútil.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo (system instruction + prompt) em JSON antes de cada chamada à IA.
* **Smart Excludes:** Filtro de pathspec inteligente (`gitpr.smart-excludes.json`) remoto — baixado do GitHub e atualizado automaticamente com versionamento (`SMART_EXCLUDES_VERSION`), excluindo arquivos irrelevantes (lock files, build artifacts, assets binários e documentação) para reduzir tokens.
* **Métricas com Rastreamento de Tempo:** Injeção de `log_command_metric()` em todos os fluxos com repasse da duração em milissegundos (`duration_ms`) e lazy imports para evitar importação circular.
* **Resolução Centralizada de Output 🆕:** Nova função `resolve_output_path()` que centraliza a lógica de diretórios de saída — default em `.gitpr/reports/{type}/` com fallback para caminhos customizados do `.env`.

### **2. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria a pasta `~/.gitpr/`, e solicita interativamente as chaves de API, preferências e idioma, salvando num `.env`.
* **Routing de Comandos:** Gerencia todas as flags (`--commit`, `--review`, `--fullreview`, `--linter`, `--skill`, `--issue`, `--blame`, `--chat`, `--mcp`, `--install`, `--metrics`, `--export`, `--purge`, `--dashboard`, `--publish`, `--no-publish`, `--no-edit`, `--base`, `--lang`, `--provider`, `--pre-save`).
* **Comportamento Padrão Alterado 🆕:** Executar `gitpr` sem flags agora abre a TUI do PR Publisher (antes: gerava arquivo e saía).
* **Novas Flags 🆕:**
  * `--publish`: Abre a TUI interativa para revisar, editar e publicar o PR (comportamento padrão).
  * `--no-publish`: Gera a descrição do PR e salva localmente sem abrir o editor interativo.
  * `--no-edit`: Pula a TUI completamente — faz auto-commit (com validação do linter), auto-push e publica direto no GitHub. Ideal para CI/CD.
  * `--base <branch>`: Sobrescreve a branch de destino do Pull Request.
* **Novas Variáveis de Ambiente 🆕:** `GITPR_AUTO_COMMIT` (pular confirmação de commit), `GITPR_SKIP_LINT` (pular validação do linter), `GITPR_AUTO_STAGE` (stage automático de arquivos), `GITPR_SKIP_UNSTAGED_CHECK` (pular verificação de unstaged), `GITPR_SHOW_LOGS` (controlar logs de progresso), `GITPR_AUTO_MERGE` (auto-merge após publicação).
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub.
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **10 ferramentas anotadas + 15 recursos + 7 prompts**.
* **--install:** Assistente guiado de 4 etapas que baixa templates de skill, instala Git Hooks, configura MCP nos editores e valida chaves de API.
* **--metrics:** Sistema de telemetria local com escopo por repositório: `--export` (salva em `./.gitpr/metrics/export/`), `--purge` (limpeza), `--dashboard` (TUI interativa com varredura de cache).

### **3. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)** 🆕

* **Interface Interativa Completa:** TUI construída com Textual para revisar, editar e publicar Pull Requests diretamente no terminal.
* **6 Telas Modais:**
  * `CommitConfirmScreen`: Confirmação antes do commit automático.
  * `FileStageScreen`: Seleção interativa de arquivos para staging.
  * `CommitProgressScreen`: Barra de progresso durante commit e push com logs em tempo real.
  * `CommitMessageScreen`: Exibição e confirmação da mensagem gerada por IA.
  * `LinterErrorScreen`: Exibição de erros do linter com opção de abortar ou continuar.
  * `ErrorScreen`: Exibição de erros gerais com scroll, capped em `max-height: 80%`.
* **Bindings:** F1 (Help — modal com atalhos e instruções), F2 (Salvar .md local), F3 (Publicar via GitHub API), Esc (Sair).
* **Fluxo de Auto-Commit:** Quando há mudanças não commitadas e o usuário usa `--no-edit` ou F3, o GitPR automaticamente:
  1. Executa o linter estático (a menos que `GITPR_SKIP_LINT=true`)
  2. Gera mensagem de commit via IA (Conventional Commits)
  3. Confirma com o usuário (a menos que `GITPR_AUTO_COMMIT=true`)
  4. Executa `git commit`
  5. Continua para push e publicação do PR
* **Verificação de Arquivos Unstaged:** Ao iniciar, verifica `git status --porcelain` e oferece modal `StageFilesApp` para selecionar, pular ou cancelar.
* **Tratamento de PR Existente:** Detecta PRs abertos para a branch atual via GitHub API e oferece push para o PR existente (atualizando via PATCH) ou criar um novo.
* **Auto-Upstream:** Detecta falha de `git push` por falta de upstream e automaticamente tenta `--set-upstream origin <branch>`.
* **Detecção de "Nothing to commit":** Trata `git commit` sem mudanças como sucesso — o fluxo continua sem erro.
* **Merge Flow:** Após criação/atualização do PR, oferece opção de merge. Controlado por `GITPR_AUTO_MERGE`.
* **Correção de Stdout:** Wrapper `_with_real_stdout()` para evitar `OSError: [Errno 9] Bad file descriptor` quando a TUI do Textual chama `click.secho()`.

### **4. Módulo de API do GitHub (`src/github_api.py`)** 🆕

* **Funções Compartilhadas:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` — encapsulando chamadas REST à API do GitHub v3.
* **Autenticação via PAT:** Token de acesso pessoal validado com `GET /user` antes das operações.
* **Reaproveitamento:** Funções usadas tanto pela TUI de PR quanto pela TUI de issues, eliminando duplicação.

### **5. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no git diff sem gastar cotas de IA.
* **Regras YAML:** Lê o arquivo local `.gitpr.linter.yml` (criado via `--skill`). Suporta regex de validação, ignorar comentários e ignorar diretórios específicos (usando fnmatch).
* **Template multilíngue:** Templates do linter disponíveis em 5 idiomas.
* **Integração no Auto-Commit 🆕:** O linter é executado automaticamente antes do commit no fluxo de PR publication.

### **6. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data` e `decrypt_data` para proteger chaves de API de IA e GitHub PAT.
* **Validação de Token do GitHub:** Função `validate_github_token()` realiza uma chamada leve (`GET /user`) para validar o PAT.
* **Fluxo de Auto-Reauth:** Se o token expirar ou for inválido durante o `gitpr -is`, a aplicação captura a resposta 401 HTTP, solicita um novo token ao usuário e relança a interface TUI preservando o rascunho.

### **7. Auto-Updater (`src/updater.py`)**

* **Hot-Swap:** Verifica na API do GitHub Releases a versão mais recente. Se houver divergência, baixa o binário compilado, renomeia o executável atual e substitui sem quebrar a execução em andamento (com capacidade de rollback).
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Verificação de conexão:** Socket `8.8.8.8:53` antes de qualquer operação de rede.
* **Versionamento Centralizado:** `__version__` (0.0.33), `__lang_version__` (v0.0.11), `__scripts_version__` (v0.0.1), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION` — todos derivados exclusivamente do `updater.py`.

### **8. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Construída com Textual — histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico de conversa persistido por branch, permitindo continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear` — atalhos para ações comuns de pair programming.
* **Auto-Patching (F5):** Extrai blocos de código sugeridos pela IA e exporta para arquivo de patch para fácil aplicação.
* **Atualização de Diff (F2):** Recarrega o `git diff` atual sem reiniciar a sessão.
* **Exportação de Sessão (F6):** Salva o histórico completo do chat para documentação.

### **9. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com suporte a placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas:** en_us (padrão/fallback), pt_br, pt_pt, es_es, fr_fr.
* **Arquivos Versionados:** `__lang_version__` (v0.0.11) controla atualização dos pacotes de idioma (`langs/*.json`).
* **Cobertura Expandida 🆕:** ~623 chaves de tradução em pt_BR (+132 desde v0.0.32). Novas strings para PR Publisher TUI, telas modais, fluxo de commit, e documentação de PR publication.
* **Cache com Indexação por Idioma:** Respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.
* **Script de Sincronização:** `tests/sync_i18n.py` para detecção automática de chaves órfãs.

### **10. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **Delimitador:** Separador de frases por ponto e vírgula (`;`), compatível com frases complexas contendo vírgulas.
* **Velocidade Adaptativa & Flickering:** Animação de descoberta de caracteres adaptada para frases longas e uso do ANSI `\033[K` para evitar artefatos visuais no terminal.
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas nos arquivos `templates/gitpr.thinking-words.{lang}.md`.

### **11. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Medição de Duração:** Injeção de `duration_ms` (cronometragem de alta precisão via `time.perf_counter()`) no `meta_raw` e `_telemetry_meta`.
* **Modo JSON & Parâmetros Determinísticos:** Outputs estruturados com `temperature=0.0` e `top_p=0.1`.

### **12. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt.
* **Indexação por Idioma:** O campo `lang` foi adicionado ao chaveamento de cache, permitindo respostas distintas para o mesmo diff em idiomas diferentes.
* **Telemetria e Duração:** Persistência do campo `duration_ms` e `meta_raw` em arquivos de cache em `~/.gitpr/cache/prompts/`.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` lê todos os arquivos de cache recursivamente para computar métricas históricas completas.

### **13. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`), e Arqueologia por Blame (`-b`).
* **TUI Interativa:** Edição de rascunhos, atalho F2 (salvar local), F3 (publicar no GitHub via API REST) e F1 (help).
* **Tratamento de 401:** Sinalização de reautenticação sem fechamento da aplicação com perda de conteúdo.

### **14. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia a evolução e autoria histórica de trechos de código com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame:** Eventos de arqueologia registrados via `log_blame_metric()` com rastreamento de profundidade e número de commits analisados.

### **15. Servidor MCP e Instalador (`src/mcp_server.py`)**

* **10 Ferramentas MCP Anotadas:** Annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) configuradas para IDEs como Cursor, VS Code e Claude Code.
* **15 Recursos + 7 Prompts Templatizados:** 35 arquivos de template em `templates/gitpr.prompt.*.md`.
* **Instalador Automático:** Configuração de editores suportados (VS Code, Cursor, Claude Code, Claude Desktop, Zed) com merge JSON inteligente.

### **16. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório (Repo-Scope):** Rótulo `📁 Repository: owner/repo` e filtragem estrita de eventos e dados de cache por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background que carrega dados de cache enquanto exibe o widget `ProgressBar` da Textual.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de chamadas de cache ao totalizador do dashboard.
* **Controle de Estado de Cache:** Arquivo de registro em `./.gitpr/metrics/{repo}/processed_cache.json`.
* **Fix de Colunas no F5:** Inicialização única de colunas (`_setup_columns()`), prevenindo duplicação visual em atualizações.
* **Exportação Local:** Salvamento de CSV/JSON em `./.gitpr/metrics/export/`.

### **17. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos de métricas são indexados por `repo_name`, permitindo isolamento entre projetos.
* **Eventos de Hook:** `log_hook_event()` para hooks Git (pre-commit, prepare-commit-msg, post-checkout, pre-push, post-merge).
* **Eventos de Linter e Blame:** `log_linter_metric()` para linter standalone, `log_blame_metric()` para arqueologia de código.
* **Exportação Local:** `--metrics --export` gera CSV e JSON em `./.gitpr/metrics/export/` com filtro por repositório.
* **Limpeza:** `--metrics --purge` remove todos os arquivos de métricas locais com confirmação interativa.

### **18. Sincronização de Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (v0.0.1) no `updater.py` controla a versão dos scripts de hook separadamente dos dicionários de idioma.
* **Detecção Automática:** Ao executar `--installhooks`, o sistema compara a versão local (armazenada no `.env`) com a versão mais recente e atualiza automaticamente se necessário.
* **Idioma-Aware:** Detecta o idioma configurado e baixa os templates de hook correspondentes.

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_core.py` | 25+ | Fluxos principais, git diff, PR generation, timing |
| `tests/test_chat_backend.py` | 30+ | Memória de chat, persistência, comandos slash |
| `tests/test_skill_command.py` | 10+ | Download e validação de templates de skill |
| `tests/test_pre_save.py` | 10+ | Flag --pre-save e payload JSON |
| `tests/test_smart_excludes.py` | 14+ | Filtro pathspec inteligente |
| `tests/test_thinking_words.py` | 10+ | Carregamento e parsing com separador `;` |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_mcp_server.py` | 33 | Ferramentas MCP, recursos, annotations e patching |
| `tests/test_metrics.py` | 36+ | Coleta, exportação local, escopo de repo, cache token summary, duration_ms |
| `tests/test_install_wizard.py` | 5+ | Assistente interativo de instalação |
| `tests/test_blame_metrics.py` | 10+ | Métricas de blame: profundidade, commits, duração |
| `tests/test_linter_metrics.py` | 8+ | Métricas de linter: erros, warnings, duração |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (chaves órfãs) |

**Total:** 131 cenários de teste automatizados passando com 100% de sucesso.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n Expandida 🆕:** ~623 chaves de tradução em pt_BR (eram 491 no v0.0.32, +132 novas). Novas strings cobrindo PR Publisher TUI, telas modais de commit, fluxo de staging, e documentação.
* **Nova Documentação Técnica 🆕:** `docs/pull-request-publication.md` em 5 idiomas (EN, PT-BR, PT-PT, ES, FR) com cobertura completa do fluxo de PR publication, variáveis de ambiente, e troubleshooting.
* **CHANGELOG.md 🆕:** Histórico completo de todas as versões (v0.0.1 → v0.0.33) no formato Keep a Changelog com seções Added, Changed e Fixed.
* **READMEs Atualizados 🆕:** Todos os 5 READMEs atualizados com PR Publisher features, estrutura de diretórios `.gitpr/reports/` e links para documentação.
* **Documentação em 5 idiomas:** 24 tópicos em `docs/` traduzidos para EN, PT-BR, PT-PT, ES, FR (+1 novo tópico: pull-request-publication).
* **Memory Index:** `.claude/memory/MEMORY.md` com 14 padrões de arquitetura extraídos de 36 relatórios.
* **Relatórios de tarefas:** `docs/claude-code/reports/` e `docs/reports/` (8 relatórios de status).
* **Planos de desenvolvimento:** 8+ planos documentados em `docs/plans/`.

---

## **🔄 Pipeline de Distribuição**

1. **PyPI:** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **GitHub Releases:** PyInstaller → `.exe` standalone → upload automatizado
3. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml`
4. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`

---

## **📈 Evolução desde o Relatório Anterior (v0.0.7)**

| Área | v0.0.7 (anterior) | v0.0.8 (atual) |
|------|-------------------|----------------|
| **Versão GitPR** | 0.0.32 | **0.0.33** |
| **Versão Idioma** | v0.0.10 | **v0.0.11** |
| **Versão Scripts Hook** | v0.0.1 | v0.0.1 |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 (en, pt_br, pt_pt, es_es, fr_fr) | 5 (en, pt_br, pt_pt, es_es, fr_fr) |
| **Interface** | CLI + TUI Issues + Chat TUI + MCP Server + Dashboard | CLI + TUI Issues + Chat TUI + MCP Server + Dashboard + **PR Publisher TUI** |
| **PR Publication** | Apenas geração local de .md | **TUI interativa completa + auto-commit + push + publicação via API** |
| **Comportamento Padrão** | `gitpr` gera arquivo local | **`gitpr` abre TUI do PR Publisher** |
| **Telas TUI (total)** | 3 (issues, chat, metrics) | **5 apps TUI + 6 telas modais de commit** |
| **GitHub API** | Issues via REST | **+ PRs (create, update, merge) via módulo dedicado** |
| **Novas Flags CLI** | 21 flags | **24 flags (+ `--publish`, `--no-publish`, `--no-edit`, `--base`)** |
| **Variáveis de Ambiente** | 7 vars | **13 vars (+6: AUTO_COMMIT, SKIP_LINT, AUTO_STAGE, SKIP_UNSTAGED, SHOW_LOGS, AUTO_MERGE)** |
| **Traduções pt_BR** | 491 chaves | **~623 chaves (+132 PR Publisher e commit flow)** |
| **Módulos Python** | 21 arquivos em src/ | **25 arquivos (+ github_api.py, pr_publish_app.py, pr_publish_help.py)** |
| **Documentação** | 23 tópicos | **24 tópicos (+ pull-request-publication.md em 5 idiomas)** |
| **CHANGELOG** | — (apenas GitHub Releases) | **Histórico completo das 8 versões (v0.0.1 → v0.0.33)** |
| **Suíte de Testes** | 131 cenários (12 arquivos) | 131 cenários (12 arquivos) |
| **Commits desde v0.0.32** | — | **7 commits (PR Publisher + merge flow)** |

---

## **🚧 Próximos Passos**

* **Testes para PR Publisher:** Cobertura de testes unitários e de integração para o fluxo de PR publication (`pr_publish_app.py`, `github_api.py`).
* **Testes de integração end-to-end para MCP:** Validação de chamadas de ferramentas e prompts via cliente stdio simulado.
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Adicionar histogramas de tempo e gráficos de tendência de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação completa do build PyInstaller e envio de assets para o GitHub Releases.
* **Mais provedores:** OpenAI direto, provedores locais adicionais.
* **Plugin system:** Extensibilidade para regras de linter e prompts customizados.

---

**Relatório gerado em:** 2026-08-09  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
