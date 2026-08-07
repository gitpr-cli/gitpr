# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.32 (2026-08-06)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.7):**
- **Expansão da Cobertura i18n (491 chaves):** Sincronização completa das chamadas `__()` em `core.py`, `main.py` e `linter_engine.py` com o arquivo de tradução `pt_br.json`. Script de verificação `tests/sync_i18n.py` para detectar chaves órfãs em qualquer arquivo fonte. Adição de 5 novas traduções para strings do Smart Excludes, banner CLI com `--install` e telemetria local.
- **Smart Excludes para Documentação:** Filtro pathspec inteligente que detecta e exclui arquivos de documentação (`.md`, `.rst`, `.txt`) do diff, com notificação visual da quantidade de arquivos excluídos (`📄 {count} documentation file(s) excluded`) e link para documentação.
- **Sincronização Automática de Hooks Git:** Sistema de versionamento independente para scripts de hook (`__scripts_version__` v0.0.1) com verificação e atualização automática ao executar `--installhooks`. Detecta idioma do ambiente e baixa a versão correta dos templates.
- **Métricas para Linter, Blame e Git Hooks:** Telemetria expandida com `log_hook_event()` para eventos de hook, `log_linter_metric()` para execuções do linter standalone e `log_blame_metric()` para arqueologia de código.
- **Cache i18n com Indexação por Idioma:** Sistema de cache de respostas IA agora inclui o idioma corrente no chaveamento, evitando colisões entre respostas geradas em idiomas diferentes.
- **Versionamento Centralizado no Updater:** Versão do GitPR (`__version__`) e versão dos dicionários de idioma (`__lang_version__`) derivadas exclusivamente do `src/updater.py`, eliminando duplicação com `pyproject.toml`.
- **Documentação de Padrões de Arquitetura:** Memory index com 14 padrões documentados extraídos de 36 relatórios de tarefas, cobrindo cache, spinner, MCP, métricas, UI, versionamento e outros subsistemas.

- **Versão atual:** 0.0.32
- **Versão dos dicionários de idioma:** v0.0.10
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
* **UI/Terminal:** Textual — TUI (Text User Interface) para chat interativo, edição de issues, help screen e dashboard de métricas.
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API e tokens GitHub.
* **Configuração:** `python-dotenv`, `pyyaml` (para o linter estático).
* **IA Providers:** Integração via SDK oficial do Google GenAI (`gemini-2.5-flash`), OpenAI SDK (`DeepSeek`), e OpenAI SDK (`Ollama` local).
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — **Tool Annotations, Prompts com templates e prompt:// resources**.
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
* **Smart Excludes 🆕:** Filtro de pathspec inteligente (`gitpr.smart-excludes.json`) remoto — baixado do GitHub e atualizado automaticamente com versionamento (`SMART_EXCLUDES_VERSION`). **Nova funcionalidade:** exclusão de arquivos de documentação com notificação visual (`📄 {count} documentation file(s) excluded`) e link `Learn more` para documentação.
* **Métricas com Rastreamento de Tempo:** Injeção de `log_command_metric()` em todos os fluxos com repasse da duração em milissegundos (`duration_ms`) e lazy imports para evitar importação circular.

### **2. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria a pasta `~/.gitpr/`, e solicita interativamente as chaves de API, preferências e idioma, salvando num `.env`.
* **Routing de Comandos:** Gerencia todas as flags (`--commit`, `--review`, `--fullreview`, `--linter`, `--skill`, `--issue`, `--blame`, `--chat`, `--mcp`, `--install`, `--metrics`, `--export`, `--purge`, `--dashboard`, `--lang`, `--provider`, `--pre-save`).
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub.
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **10 ferramentas anotadas + 15 recursos + 7 prompts**.
* **--install:** Assistente guiado de 4 etapas que baixa templates de skill, instala Git Hooks, configura MCP nos editores e valida chaves de API.
* **--metrics:** Sistema de telemetria local com escopo por repositório: `--export` (salva em `./.gitpr/metrics/export/`), `--purge` (limpeza), `--dashboard` (TUI interativa com varredura de cache).

### **3. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no git diff sem gastar cotas de IA.
* **Regras YAML:** Lê o arquivo local `.gitpr.linter.yml` (criado via `--skill`). Suporta regex de validação, ignorar comentários e ignorar diretórios específicos (usando fnmatch).
* **Template multilíngue:** Templates do linter disponíveis em 5 idiomas.
* **Métricas de Linter 🆕:** Eventos de execução do linter registrados via `log_linter_metric()` com contagem de erros e warnings.

### **4. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data` e `decrypt_data` para proteger chaves de API de IA e GitHub PAT.
* **Validação de Token do GitHub:** Função `validate_github_token()` realiza uma chamada leve (`GET /user`) para validar o PAT.
* **Fluxo de Auto-Reauth:** Se o token expirar ou for inválido durante o `gitpr -is`, a aplicação captura a resposta 401 HTTP, solicita um novo token ao usuário e relança a interface TUI preservando o rascunho.

### **5. Auto-Updater (`src/updater.py`)**

* **Hot-Swap:** Verifica na API do GitHub Releases a versão mais recente. Se houver divergência, baixa o binário compilado, renomeia o executável atual e substitui sem quebrar a execução em andamento (com capacidade de rollback).
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Verificação de conexão:** Socket `8.8.8.8:53` antes de qualquer operação de rede.
* **Versionamento Centralizado 🆕:** `__version__` (0.0.32), `__lang_version__` (v0.0.10), `__scripts_version__` (v0.0.1), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION` — todos derivados exclusivamente do `updater.py`, fonte única da verdade para versionamento.

### **6. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Construída com Textual — histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico de conversa persistido por branch, permitindo continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear` — atalhos para ações comuns de pair programming.
* **Auto-Patching (F5):** Extrai blocos de código sugeridos pela IA e exporta para arquivo de patch para fácil aplicação.
* **Atualização de Diff (F2):** Recarrega o `git diff` atual sem reiniciar a sessão.
* **Exportação de Sessão (F6):** Salva o histórico completo do chat para documentação.

### **7. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com suporte a placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas:** en_us (padrão/fallback), pt_br, pt_pt, es_es, fr_fr.
* **Arquivos Versionados:** `__lang_version__` (v0.0.10) controla atualização dos pacotes de idioma (`langs/*.json`).
* **Cobertura Expandida 🆕:** 491 chaves de tradução em pt_BR (+44 desde v0.0.6). Sincronização completa entre chamadas `__()` no código-fonte e dicionários de tradução. Script `tests/sync_i18n.py` para detecção automática de chaves órfãs.
* **Cache com Indexação por Idioma 🆕:** Respostas de IA cacheadas agora incluem o idioma corrente no chaveamento MD5, evitando colisões entre idiomas diferentes.

### **8. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **Delimitador Atualizado:** Mudança do separador de frases para ponto e vírgula (`;`), evitando que frases com vírgulas internas sejam divididas incorretamente.
* **Velocidade Adaptativa & Flickering:** Animação de descoberta de caracteres adaptada para frases longas e uso do ANSI `\033[K` para evitar artefatos visuais no terminal.
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas nos arquivos `templates/gitpr.thinking-words.{lang}.md`.

### **9. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Medição de Duração:** Injeção de `duration_ms` (cronometragem de alta precisão via `time.perf_counter()`) no `meta_raw` e `_telemetry_meta`.
* **Modo JSON & Parâmetros Determinísticos:** Outputs estruturados com `temperature=0.0` e `top_p=0.1`.

### **10. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt.
* **Indexação por Idioma 🆕:** O campo `lang` foi adicionado ao chaveamento de cache, permitindo respostas distintas para o mesmo diff em idiomas diferentes.
* **Telemetria e Duração:** Persistência do campo `duration_ms` e `meta_raw` em arquivos de cache em `~/.gitpr/cache/prompts/`.
* **Leitura para Dashboard:** `scan_cache_files_for_dashboard()` lê todos os arquivos de cache recursivamente para computar métricas históricas completas.

### **11. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`), e Arqueologia por Blame (`-b`).
* **TUI Interativa:** Edição de rascunhos, atalho F2 (salvar local), F3 (publicar no GitHub via API REST) e F1 (help).
* **Tratamento de 401:** Sinalização de reautenticação sem fechamento da aplicação com perda de conteúdo.

### **12. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia a evolução e autoria histórica de trechos de código com classificação de commits (`ORIGIN` vs `REFACTORING`).
* **Métricas de Blame 🆕:** Eventos de arqueologia registrados via `log_blame_metric()` com rastreamento de profundidade e número de commits analisados.

### **13. Servidor MCP e Instalador (`src/mcp_server.py`)**

* **10 Ferramentas MCP Anotadas:** Annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) configuradas para IDEs como Cursor, VS Code e Claude Code.
* **15 Recursos + 7 Prompts Templatizados:** 35 arquivos de template em `templates/gitpr.prompt.*.md`.
* **Instalador Automático:** Configuração de editores suportados (VS Code, Cursor, Claude Code, Claude Desktop, Zed) com merge JSON inteligente.

### **14. Dashboard de Métricas TUI (`src/ui/metrics_app.py`)**

* **Escopo por Repositório (Repo-Scope):** Rótulo `📁 Repository: owner/repo` e filtragem estrita de eventos e dados de cache por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background que carrega dados de cache enquanto exibe o widget `ProgressBar` da Textual.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de chamadas de cache ao totalizador do dashboard.
* **Controle de Estado de Cache:** Arquivo de registro em `./.gitpr/metrics/{repo}/processed_cache.json`.
* **Fix de Colunas no F5:** Inicialização única de colunas (`_setup_columns()`), prevenindo duplicação visual em atualizações.
* **Exportação Local:** Salvamento de CSV/JSON em `./.gitpr/metrics/export/`.

### **15. Sistema de Métricas e Telemetria (`src/metrics.py`)**

* **Escopo por Repositório:** Todos os eventos de métricas são indexados por `repo_name`, permitindo isolamento entre projetos.
* **Novos Eventos 🆕:** `log_hook_event()` para hooks Git (pre-commit, prepare-commit-msg), `log_linter_metric()` para linter standalone, `log_blame_metric()` para arqueologia de código.
* **Exportação Local:** `--metrics --export` gera CSV e JSON em `./.gitpr/metrics/export/` com filtro por repositório.
* **Limpeza:** `--metrics --purge` remove todos os arquivos de métricas locais com confirmação interativa.

### **16. Sincronização de Hooks Git 🆕**

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
| `tests/test_blame_metrics.py` 🆕 | 10+ | Métricas de blame: profundidade, commits, duração |
| `tests/test_linter_metrics.py` 🆕 | 8+ | Métricas de linter: erros, warnings, duração |
| `tests/sync_i18n.py` 🆕 | — | Script de verificação de cobertura i18n (chaves órfãs) |

**Total:** 131 cenários de teste automatizados passando com 100% de sucesso.

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n Expandida 🆕:** 491 chaves de tradução em pt_BR (eram 447 no v0.0.6, +44 novas). Sincronização completa validada para `core.py`, `main.py` e `linter_engine.py`.
* **Script de Sincronização 🆕:** `tests/sync_i18n.py` — script reutilizável para detectar chaves `__()` em qualquer arquivo fonte que não possuem tradução no dicionário de idioma.
* **Novos Testes de Métricas 🆕:** `test_blame_metrics.py` (140 linhas) e `test_linter_metrics.py` (116 linhas) cobrindo telemetria dos novos módulos.
* **Documentação em 5 idiomas:** 23 tópicos em `docs/` traduzidos para EN, PT-BR, PT-PT, ES, FR.
* **Memory Index:** `.claude/memory/MEMORY.md` com 14 padrões de arquitetura extraídos de 36 relatórios.
* **Relatórios de tarefas:** `docs/claude-code/reports/` e `docs/reports/`.

---

## **🔄 Pipeline de Distribuição**

1. **PyPI:** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **GitHub Releases:** PyInstaller → `.exe` standalone → upload automatizado
3. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml`
4. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`

---

## **📈 Evolução desde o Relatório Anterior (v0.0.6)**

| Área | v0.0.6 (anterior) | v0.0.7 (atual) |
|------|-------------------|----------------|
| **Versão GitPR** | 0.0.30 | **0.0.32** |
| **Versão Idioma** | v0.0.8 | **v0.0.10** |
| **Versão Scripts Hook** | — | **v0.0.1** |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 (en, pt_br, pt_pt, es_es, fr_fr) | 5 (en, pt_br, pt_pt, es_es, fr_fr) |
| **Traduções pt_BR** | 447 chaves | **491 chaves (+44)** |
| **Dashboard TUI** | Repo-scoped, cache ilimitado + ProgressBar + F5 fix | Repo-scoped, cache ilimitado + ProgressBar + F5 fix |
| **Smart Excludes** | Filtro de pathspec remoto | **+ Exclusão de documentação com notificação visual** |
| **Métricas & Telemetria** | Wall-clock duration + Export local | **+ Métricas de Linter, Blame e Git Hooks** |
| **Hooks Git** | Instalação manual (`--installhooks`) | **+ Sincronização automática com versionamento** |
| **Cache i18n** | Chaveamento por MD5 do diff | **+ Indexação por idioma** |
| **Versionamento** | `__version__` duplicado (updater + pyproject) | **Fonte única no updater.py** |
| **Suíte de Testes** | 114 cenários (10 arquivos) | **131 cenários (12 arquivos + sync_i18n)** |
| **Documentação de Padrões** | CLAUDE.md + GEMINI.md | **+ Memory Index com 14 padrões** |

---

## **🚧 Próximos Passos**

* **Sincronização i18n nos demais idiomas:** Expansão das traduções para es_es, fr_fr e pt_pt com a mesma cobertura do pt_br (491 chaves).
* **Testes de integração end-to-end para MCP:** Validação de chamadas de ferramentas e prompts via cliente stdio simulado.
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Adicionar histogramas de tempo e gráficos de tendência de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação completa do build PyInstaller e envio de assets para o GitHub Releases.

---

**Relatório gerado em:** 2026-08-06  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
