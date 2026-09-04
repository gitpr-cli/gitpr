# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.31 (2026-08-03)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.6):**
- **Dashboard TUI de Métricas Reformulado:** Escopo isolado por repositório (`repo_filter`), varredura assíncrona ilimitada de arquivos de cache (`~/.gitpr/cache/prompts/`), overlay visual com `ProgressBar`, totalizador unificado de tokens por projeto, controle de arquivos de cache processados (`./.gitpr/metrics/{repo}/processed_cache.json`) e correção do bug de colunas duplicadas no atalho F5 (Refresh).
- **Rastreamento de Duração de Chamadas IA (Wall-Clock Timing):** Injeção de `duration_ms` em milissegundos via `time.perf_counter()` em todas as respostas de LLM, repassada pelo cache e exibida no dashboard de métricas.
- **Exportação Local por Projeto:** `gitpr --metrics --export` agora gera relatórios CSV e JSON na pasta do projeto local (`./.gitpr/metrics/export/`) filtrando pelo repositório ativo.
- **Revalidação Automática de Token do GitHub (Auto-Reauth no 401):** Função de validação de PAT (`GET /user`), pré-validação antes da TUI de issues (`gitpr -is`) e recuperação graciosa de erro HTTP 401 sem perda de rascunhos.
- **Ajustes no Spinner e Thinking Words:** Troca do delimitador de frases de vírgula para ponto e vírgula (`;`), permitindo frases complexas com vírgulas no `templates/gitpr.thinking-words.*.md` sem quebra de parsing.
- **Início Rápido nos READMEs:** Documentação de instalação via `pip install gitpr-cli` e inicialização de repositório via `gitpr --install` nos READMEs de todos os 5 idiomas.
- **Guia do Projeto `GEMINI.md`:** Guia arquitetural completo, convenções de código, pipeline de comandos e padrão de relatórios em `docs/gemini/reports/`.

- **Versão atual:** 0.0.30
- **Publicação:** PyPI (`pip install gitpr-cli`) + GitHub Releases (binário standalone)
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
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
* **Testes:** Pytest + `unittest.mock` (10 arquivos de teste, 114 cenários).
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
* **Smart Excludes:** Filtro de pathspec inteligente (`gitpr.smart-excludes.json`) remoto — baixado do GitHub e atualizado automaticamente com versionamento (`SMART_EXCLUDES_VERSION`), excluindo arquivos irrelevantes (lock files, build artifacts, assets binários) para reduzir tokens.
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

### **4. Segurança e Autenticação (`src/security.py`, `src/config.py`, `src/tui_issue.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Proteção de Tokens:** `encrypt_data` e `decrypt_data` para proteger chaves de API de IA e GitHub PAT.
* **Validação de Token do GitHub 🆕:** Função `validate_github_token()` realiza uma chamada leve (`GET /user`) para validar o PAT.
* **Fluxo de Auto-Reauth 🆕:** Se o token expirar ou for inválido durante o `gitpr -is`, a aplicação captura a resposta 401 HTTP, solicita um novo token ao usuário e relança a interface TUI preservando o rascunho.

### **5. Auto-Updater (`src/updater.py`)**

* **Hot-Swap:** Verifica na API do GitHub Releases a versão mais recente. Se houver divergência, baixa o binário compilado, renomeia o executável atual e substitui sem quebrar a execução em andamento (com capacidade de rollback).
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Verificação de conexão:** Socket `8.8.8.8:53` antes de qualquer operação de rede.
* **Versionamento de assets:** `__lang_version__` (v0.0.8), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION` para controle de atualização de templates e traduções.

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
* **Arquivos Versionados:** `__lang_version__` (v0.0.8) controla atualização dos pacotes de idioma (`langs/*.json`).
* **Cobertura Total:** Mensagens CLI, help do Click, alertas do linter, Git Hooks, spinner, chat TUI, MCP, métricas e TUI Dashboard traduzidos.

### **8. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **Delimitador Atualizado 🆕:** Mudança do separador de frases para ponto e vírgula (`;`), evitando que frases com vírgulas internas sejam divididas incorretamente.
* **Velocidade Adaptativa & Flickering:** Animação de descoberta de caracteres adaptada para frases longas e uso do ANSI `\033[K` para evitar artefatos visuais no terminal.
* **263 entradas por idioma:** Sincronizadas entre os 5 idiomas nos arquivos `templates/gitpr.thinking-words.{lang}.md`.

### **9. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:** Google Gemini (`gemini-2.5-flash`), DeepSeek (`deepseek-chat`), Ollama (local).
* **Medição de Duração 🆕:** Injeção de `duration_ms` (cronometragem de alta precisão via `time.perf_counter()`) no `meta_raw` e `_telemetry_meta`.
* **Modo JSON & Parâmetros Determinísticos:** Outputs estruturados com `temperature=0.0` e `top_p=0.1`.

### **10. Cache Inteligente (`src/cache.py`)**

* **MD5 + Metadata:** Chaveamento por hash MD5 do diff e prompt.
* **Telemetria e Duração 🆕:** Persistência do campo `duration_ms` e `meta_raw` em arquivos de cache em `~/.gitpr/cache/prompts/`.
* **Leitura para Dashboard 🆕:** `scan_cache_files_for_dashboard()` lê todos os arquivos de cache recursivamente para computar métricas históricas completas.

### **11. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:** Diff atual, Histórico da branch (`-ht`), e Arqueologia por Blame (`-b`).
* **TUI Interativa:** Edição de rascunhos, atalho F2 (salvar local), F3 (publicar no GitHub via API REST) e F1 (help).
* **Tratamento de 401 🆕:** Sinalização de reautenticação sem fechamento da aplicação com perda de conteúdo.

### **12. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia a evolução e autoria histórica de trechos de código com classificação de commits (`ORIGIN` vs `REFACTORING`).

### **13. Servidor MCP e Instalador (`src/mcp_server.py`)**

* **10 Ferramentas MCP Anotadas:** Annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) configuradas para IDEs como Cursor, VS Code e Claude Code.
* **15 Recursos + 7 Prompts Templatizados:** 35 arquivos de template em `templates/gitpr.prompt.*.md`.
* **Instalador Automático:** Configuração de editores suportados (VS Code, Cursor, Claude Code, Claude Desktop, Zed) com merge JSON inteligente.

### **14. Dashboard de Métricas TUI Reformulado (`src/ui/metrics_app.py`)** 🆕

* **Escopo por Repositório (Repo-Scope):** Rótulo `📁 Repository: owner/repo` e filtragem estrita de eventos e dados de cache por projeto.
* **Varredura Assíncrona com Overlay:** Worker thread em background que carrega dados de cache enquanto exibe o widget `ProgressBar` da Textual.
* **Consolidação de Dados:** `load_cache_token_summary()` soma tokens de chamadas de cache ao totalizador do dashboard.
* **Controle de Estado de Cache:** Arquivo de registro em `./.gitpr/metrics/{repo}/processed_cache.json`.
* **Fix de Colunas no F5:** Inicialização única de colunas (`_setup_columns()`), prevenindo duplicação visual em atualizações.
* **Exportação Local:** Salvamento de CSV/JSON em `./.gitpr/metrics/export/`.

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

**Total:** 114 cenários de teste automatizados passando com 100% de sucesso.

---

## **🌐 Internacionalização e Documentação**

* **Seção Quick Start nos READMEs 🆕:** Atualização dos arquivos `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md` e `README.fr_fr.md` com instruções de `pip install gitpr-cli` e `gitpr --install`.
* **Novo Guia `GEMINI.md` 🆕:** Guia de desenvolvimento com padrões de código, comandos, estrutura do projeto e relatórios obrigatórios.
* **447 chaves de tradução** por idioma (2.235 traduções no total).
* **Documentação em 5 idiomas:** 23 tópicos em `docs/` traduzidos para EN, PT-BR, PT-PT, ES, FR.
* **Relatórios de tarefas:** `docs/claude-code/reports/` e `docs/gemini/reports/`.

---

## **🔄 Pipeline de Distribuição**

1. **PyPI:** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **GitHub Releases:** PyInstaller → `.exe` standalone → upload automatizado
3. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml`
4. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`

---

## **📈 Evolução desde o Relatório Anterior (v0.0.5)**

| Área | v0.0.5 (anterior) | v0.0.6 (atual) |
|------|-------------------|----------------|
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 (en, pt_br, pt_pt, es_es, fr_fr) | 5 (en, pt_br, pt_pt, es_es, fr_fr) |
| **Dashboard TUI** | Global, limitado a 100 eventos | **Repo-scoped, varredura de cache ilimitada + ProgressBar + F5 fix** |
| **Métricas & Duração** | Tokens e contadores simples | **Wall-clock duration (`duration_ms`) + Export local (`./.gitpr/metrics/export/`)** |
| **GitHub PAT Auth** | Armazenamento seguro sem pré-validação | **Validação prévia via `GET /user` + Auto-Reauth gracioso em erro 401** |
| **Thinking Words** | Separador por vírgula `,` | **Separador `;` (suporta frases complexas) sincronizado em 5 idiomas** |
| **README Documentação** | Foco em download de binários | **Quick Start com `pip install gitpr-cli` e `gitpr --install` nos 5 idiomas** |
| **Manuais de Desenvolvimento**| CLAUDE.md | **CLAUDE.md + GEMINI.md** |
| **Suíte de Testes** | 100+ cenários | **114 cenários de teste (100% passando)** |
| **Versão PyPI** | 0.0.30 | **0.0.30** |

---

## **🚧 Próximos Passos**

* **Testes de integração end-to-end para MCP:** Validação de chamadas de ferramentas e prompts via cliente stdio simulado.
* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-3-5-sonnet`).
* **Gráficos em ASCII/Textual no Dashboard:** Adicionar histogramas de tempo e gráficos de tendência de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação completa do build PyInstaller e envio de assets para o GitHub Releases.

---

**Relatório gerado em:** 2026-08-03  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))  
