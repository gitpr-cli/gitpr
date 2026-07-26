# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.29 (2026-07-25)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão:** MCP Prompts com sistema de templates multilíngue (35 arquivos em 5 idiomas), MCP Tool Annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) para melhor integração com IDEs, Thinking Words expandidas para 201 entradas com frases completas, e Spinner com velocidade adaptativa para frases longas.

- **Versão atual:** 0.0.29
- **Publicação:** PyPI (`pip install gitpr-cli`) + GitHub Releases (binário standalone)
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas)

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal).
* **UI/Terminal:** Textual — TUI (Text User Interface) para chat interativo, edição de issues e help screen.
* **Criptografia:** cryptography.fernet para proteção local de chaves de API.
* **Configuração:** dotenv, pyyaml (para o linter estático).
* **IA Providers:** Integração via SDK oficial do Google GenAI (gemini-2.5-flash), OpenAI SDK (DeepSeek), e OpenAI SDK (Ollama local).
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — **Tool Annotations e Prompts refatorados em v0.0.29**.
* **Testes:** Pytest + unittest.mock (8 arquivos de teste, 165+ cenários).
* **Empacotamento:** PyInstaller (binário standalone) + setuptools/build (PyPI).
* **CI/CD:** GitHub Actions (`pr-review.yml`) + `action.yml` para execução em pipelines.

## **🧩 Módulos Implementados e Arquitetura de Arquivos**

### **1. Núcleo e Operações Git (`src/core.py`)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON.
* **Map-Reduce (Diffs Gigantes):** Quando o diff ultrapassa ~90k tokens, divide automaticamente em lotes por arquivo (`split_diff_into_chunks`), processa cada parte (Map) e unifica os resumos (Reduce) mantendo o tom de voz da arquitetura.
* **Estimativa de Tokens:** Heurística leve `len() // 4` via `estimate_token_count()`.
* **Otimização Nativa do Git:** Flags `-U1`, `-w`, `-M`, `-B` nos comandos `get_git_diff` e `get_git_full_diff` para reduzir contexto inútil.
* **Pre-Save (`--pre-save`):** Flag oculta de debug que salva o payload completo (system instruction + prompt) em JSON antes de cada chamada à IA.
* **Smart Excludes:** Filtro de pathspec inteligente (`gitpr.smart-excludes.json`) remoto — baixado do GitHub e atualizado automaticamente com versionamento (`SMART_EXCLUDES_VERSION`), excluindo arquivos irrelevantes (lock files, build artifacts, assets binários) para reduzir tokens.

### **2. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria a pasta `~/.gitpr/`, e solicita interativamente as chaves de API, preferências e idioma, salvando num `.env`.
* **Routing de Comandos:** Gerencia todas as flags (`--commit`, `--review`, `--fullreview`, `--linter`, `--skill`, `--issue`, `--blame`, `--chat`, `--mcp`, `--lang`, `--provider`, `--pre-save`).
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub.
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **10 ferramentas anotadas + 15 recursos + 7 prompts** 🆕.

### **3. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no git diff sem gastar cotas de IA.
* **Regras YAML:** Lê o arquivo local `.gitpr.linter.yml` (criado via `--skill`). Suporta regex de validação, ignorar comentários e ignorar diretórios específicos (usando fnmatch).
* **Template multilíngue:** Templates do linter disponíveis em 5 idiomas.

### **4. Segurança e Cofre (`src/security.py`)**

* **Criptografia:** Gera uma chave mestra `secret.key` na pasta `~/.gitpr/`.
* **Funções:** `encrypt_data` e `decrypt_data` para garantir que tokens e chaves não fiquem em texto claro.
* **GitHub PAT:** Token de acesso pessoal do GitHub armazenado de forma encriptada para criação de issues via API REST.

### **5. Auto-Updater (`src/updater.py`)**

* **Hot-Swap:** Verifica na API do GitHub Releases a versão mais recente. Se houver divergência, baixa o binário compilado, renomeia o executável atual e substitui sem quebrar a execução em andamento (com capacidade de rollback).
* **Cache diário:** Evita verificações repetidas no mesmo dia.
* **Verificação de conexão:** Socket `8.8.8.8:53` antes de qualquer operação de rede.
* **Versionamento de assets:** `__lang_version__`, `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION` para controle de atualização de templates e traduções.

### **6. Interface de Chat Interativo (`src/ui/chat_app.py`)**

* **TUI Completa:** Construída com Textual — histórico de mensagens, input multi-linha, barra de status com bindings visíveis.
* **Memória por Branch (`src/chat_memory.py`):** Histórico de conversa persistido por branch, permitindo continuidade entre sessões.
* **Comandos Slash:** `/explain`, `/tests`, `/optimize`, `/clear` — atalhos para ações comuns de pair programming.
* **Auto-Patching (F5):** Extrai blocos de código sugeridos pela IA e exporta para arquivo de patch para fácil aplicação.
* **Atualização de Diff (F2):** Recarrega o `git diff` atual sem reiniciar a sessão.
* **Exportação de Sessão (F6):** Salva o histórico completo do chat para documentação.
* **Comandos multilíngues:** Arquivos `chat_commands.{lang}.json` com traduções dos comandos slash.

### **7. Internacionalização — i18n (`src/i18n.py`)**

* **Sistema Inspirado no Laravel:** Função `__()` com suporte a placeholders nomeados (`{count}`, `{file}`, etc.).
* **Detecção Automática:** Detecta idioma do SO na primeira execução e salva em `GITPR_LANG`.
* **5 Idiomas:** en_us (padrão/fallback), pt_br, pt_pt, es_es, fr_fr.
* **Fallback em Inglês:** Se uma tradução estiver faltando, exibe o texto em inglês diretamente.
* **Arquivos Versionados:** `__lang_version__` controla atualização dos pacotes de idioma (`langs/*.json`).
* **Cobertura:** Todas as mensagens de interface, help do Click, alertas do linter, mensagens do sistema, Git Hooks, spinner, chat, MCP tools, MCP resources, MCP prompts e MCP annotations traduzidos.
* **364 chaves por idioma** (+42 chaves MCP na v0.0.29).

### **8. Spinner Animado (`src/spinner.py`)**

* **Braille + Thinking Words:** Thread em background durante chamadas de IA exibindo caracteres braille com palavras de "pensamento".
* **Descoberta Progressiva:** Palavras reveladas letra por letra com caracteres aleatórios, seguidas de ciclo de pontos (`. .. ...`).
* **Cores Aleatórias:** Paleta de 10 cores para cada palavra.
* **Velocidade Adaptativa 🆕:** Frases longas (36+ caracteres) reveladas mais rápido (1 frame/letra, 0.04s) para exibir o texto completo antes de trocar de palavra. Palavras curtas mantêm velocidade original.
* **Multilíngue:** Thinking Words carregadas de templates específicos por idioma (`gitpr.thinking-words.{lang}.md`), com versionamento (`THINKING_WORDS_VERSION`).
* **201 entradas por idioma 🆕:** Lista expandida com frases criativas mescladas de `words_happy.md` (84 palavras originais + 117 frases).

### **9. Provedores de IA (`src/ai_providers.py`)**

* **3 Provedores Suportados:**
  * **Google Gemini:** `gemini-2.5-flash` (primário) / `gemini-2.5-flash-lite` (secundário)
  * **DeepSeek:** `deepseek-chat` (primário e secundário)
  * **Ollama:** Qualquer modelo local compatível com OpenAI API
* **Arquitetura Multi-Modelo:** Fallback automático entre provedores em caso de falha.
* **Modo JSON:** Todos os provedores configurados para output estruturado (`response_mime_type` / `response_format`).
* **Parâmetros determinísticos:** Temperature 0.0, top_p 0.1.

### **10. Cache Inteligente (`src/cache.py`)**

* **MD5:** Hash exato do código (diff) + instruções para identificar chamadas idênticas.
* **Cache por Repositório:** JSON inclui campo `repo` para filtro multi-projeto.
* **Economia de Cota:** Retorna resultados em milissegundos do cache local (`~/.gitpr/cache/prompts/`).

### **11. Motor de Issues e TUI (`src/issue_engine.py`, `src/tui_issue.py`, `src/ui/issue_app.py`)**

* **3 Motores de Contexto:**
  * **Issue de Código Novo (`gitpr -is`):** Lê o `git diff` atual.
  * **Issue de Épico/Release (`gitpr -is -ht`):** Lê histórico completo da branch (Git Log + Cache de PR).
  * **Issue de Dívida Técnica (`gitpr -is -b arquivo:linhas`):** Linha do tempo via `git blame`.
* **TUI Interativa:** Editor de issues com syntax highlight, bindings para salvar local (F2) ou enviar via API do GitHub (F3).
* **Help Screen (F1):** Modal com atalhos e instruções.

### **12. Arqueólogo de Código (`src/blame_engine.py`)**

* **Git Blame + IA:** Rastreia origem de regras de negócio com profundidade máxima de 4 commits pais.
* **Classificação:** Modelo secundário classifica commits como `ORIGIN` ou `REFACTORING`.
* **Sumário Executivo:** Modelo avançado gera análise final consolidada.
* **Output:** Terminal color-coded (verde=origin, amarelo=refactoring) + relatório Markdown.

### **13. Sistema de Skills e Templates**

* **Templates Locais:** `.gitpr.commit.md`, `.gitpr.pr.md`, `.gitpr.review.md`, `.gitpr.filereview.md`, `.gitpr.issue.md`, `.gitpr.blame.md` como *System Instructions* personalizáveis.
* **Templates Remotos:** Baixados do GitHub via `--skill` (nunca sobrescreve arquivos locais existentes).
* **Multilíngue:** Templates disponíveis em 5 idiomas com fallback inteligente (`get_skill_context()`).
* **Pasta `.gitpr/skill/`:** Organização limpa dos arquivos de skill no projeto.

### **14. Otimização Map-Reduce para Diffs Gigantes**

* **Ativação Automática:** Quando o diff excede ~90k tokens estimados.
* **Split Seguro:** Quebra no delimitador regex `(^diff --git a/)` para não corromper sintaxe.
* **Rate Limiting:** `time.sleep(1)` entre lotes Map.
* **Documentação:** Página dedicada em 5 idiomas (`docs/map-reduce-diff.{lang}.md`) linkada no console durante o processamento.
* **Progresso no Console:** Exibe contagem de lotes e link para documentação.

### **15. Integração CI/CD**

* **GitHub Actions:** Workflow `pr-review.yml` para revisão automática de PRs.
* **Action Definition:** `action.yml` para uso como GitHub Action em pipelines externos.
* **Git Hooks Locais:** `pre-commit` (linter) e `prepare-commit-msg` (geração de mensagem por IA) instaláveis via `--installhooks`.

### **16. Servidor MCP — Integração com Editores e IDEs (`src/mcp_server.py`)** 

* **10 Ferramentas MCP com Annotations 🆕:** `get_git_context`, `analyze_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue` — todas com `ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`).
  * **3 ferramentas read-only** (`readOnlyHint=True`, `idempotentHint=True`): `get_git_context`, `analyze_diff`, `run_linter`.
  * **7 ferramentas com efeitos colaterais** (`readOnlyHint=False`, `destructiveHint=False`): chamadas de rede (AI APIs, git fetch).
* **15 Recursos MCP 🆕:** 7 templates de skill (`skill://pr`, `skill://commit`, etc.) + config do linter (`linter://config`) + 7 templates de prompt (`prompt://review`, `prompt://commit`, etc.) + `prompt://list`.
* **7 Prompts MCP com Templates 🆕:** Conteúdo externalizado em 35 arquivos de template (7 prompts × 5 idiomas) no diretório `templates/gitpr.prompt.*.md` com fallback de idioma automático.
* **Transporte stdio:** Comunicação via JSON-RPC 2.0 — padrão para ferramentas CLI locais.
* **Isolamento de Output:** Sistema de monkey-patching que redireciona todo o output do terminal (banners, spinners, cores) para stderr, garantindo que o canal stdout fique limpo para o protocolo MCP.
* **Comando `gitpr-mcp`:** Entry point dedicado registrado no `pyproject.toml`.
* **Flag `--mcp`:** Alias via CLI principal (`gitpr --mcp`).

### **17. Instalador MCP (`gitpr-mcp --install`)**

* **6 Editores Suportados:** VS Code (`.vscode/mcp.json`), Cursor (`.cursor/mcp.json`), Claude Code (`.mcp.json`), Claude Desktop (global), Zed (global).
* **Modo Auto:** Detecta automaticamente quais editores estão configurados e instala para todos.
* **Merge Inteligente:** Adiciona o servidor GitPR sem remover servidores existentes — idempotente e seguro.
* **Criação de Diretórios:** Cria automaticamente `.vscode/`, `.cursor/` ou o diretório global se não existirem.

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_core.py` | 25+ | Fluxos principais, git diff, PR generation |
| `tests/test_chat_backend.py` | 30+ | Memória de chat, persistência, comandos |
| `tests/test_skill_command.py` | 10+ | Download e validação de templates |
| `tests/test_pre_save.py` | 10+ | Flag --pre-save e payload JSON |
| `tests/test_smart_excludes.py` | 14+ | Filtro pathspec inteligente |
| `tests/test_thinking_words.py` | 10+ | Carregamento e parsing de thinking words |
| `tests/test_mcp_prompts.py` 🆕 | 11 | Funções de prompt, PROMPT_FILES, _read_prompt_file(), language fallback |
| `tests/test_mcp_server.py` | 33 | Ferramentas MCP, recursos, patching de output, safe-call wrapper |

## **🌐 Internacionalização e Documentação**

* **364 chaves de tradução** por idioma (5 idiomas = 1.820 traduções).
* **Documentação completa em 5 idiomas:** 22 tópicos × 5 idiomas = 110+ páginas de documentação.
* **Nova documentação 🆕:** `docs/mcp-prompts.md` (sistema de templates), `docs/mcp-annotations.md` (tool annotations) — cada uma com 4 traduções.
* **Templates MCP 🆕:** 35 arquivos de prompt (`gitpr.prompt.*.md`) em 5 idiomas no diretório `templates/`.
* **Thinking Words 🆕:** 201 entradas por idioma (84 palavras + 117 frases) em `templates/gitpr.thinking-words.{lang}.md`.
* **Planos de desenvolvimento:** 8 planos documentados em `docs/plans/`.
* **Relatórios Claude Code:** 12+ reports de tarefas em `docs/claude-code/reports/develop_natan/`.
* **Site oficial:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
* **READMEs sincronizados:** Links relativos convertidos para absolutos (compatível com PyPI). Atualizados com MCP Prompts e MCP Tool Annotations em todos os 5 idiomas 🆕.

## **🔄 Pipeline de Distribuição**

1. **PyPI:** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **GitHub Releases:** PyInstaller → `.exe` standalone → upload via workflow
3. **GitHub Actions:** PR Review automatizado com `action.yml`
4. **MCP:** `gitpr-mcp` registrado como entry point no `pyproject.toml` → instalado automaticamente com `pip install`

## **📈 Evolução desde o Relatório Anterior (v0.0.3)**

| Área | v0.0.3 (anterior) | v0.0.4 (atual) |
|------|-------------------|-----------------|
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 (en, pt_br, pt_pt, es_es, fr_fr) | 5 (en, pt_br, pt_pt, es_es, fr_fr) |
| **Interface** | CLI + TUI Issues + Chat TUI + MCP Server | CLI + TUI Issues + Chat TUI + MCP Server |
| **MCP Tools** | 10 tools (sem annotations) | **10 tools com ToolAnnotations** |
| **MCP Resources** | 7 (skills + linter) | **15 (skills + linter + prompts)** |
| **MCP Prompts** | 7 prompts (hardcoded) | **7 prompts com templates (35 arquivos em 5 idiomas)** |
| **MCP Prompt Resources** | — | **8 recursos `prompt://`** |
| **MCP Docs** | `mcp-integration.md` | **+ `mcp-prompts.md` + `mcp-annotations.md` (5 idiomas cada)** |
| **Thinking Words** | ~15 palavras (fallback) | **201 entradas/idioma (palavras + frases)** |
| **Spinner** | Velocidade fixa | **Velocidade adaptativa (frases longas ~2.2s)** |
| **Testes** | 8 arquivos (160+ cenários) | **8 arquivos (165+ cenários)** |
| **Documentação** | 100+ páginas | **110+ páginas** |
| **READMEs** | Links MCP Integration + Prompts | **+ MCP Tool Annotations (todos 5 idiomas)** |
| **Versão** | 0.0.28 | 0.0.29 |

## **🚧 Próximos Passos**

* **Testes de integração MCP:** Cobertura end-to-end do servidor MCP com cliente de teste.
* **Mais provedores:** Claude API, OpenAI direto, provedores locais adicionais.
* **Métricas e analytics:** Dashboard de uso para times.
* **Plugin system:** Extensibilidade para regras de linter e prompts customizados.
* **Migração MCP SDK v2:** Monitorar estabilização do SDK v2.x (modo stateless, tasks).
* **GitHub Release automatizado:** Pipeline de CI/CD completo para build + release.

---

**Relatório gerado em:** 2026-07-25
**Branch:** `develop_natan`
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
