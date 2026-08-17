# **🚀 GitPR - Automação Inteligente de Code Review e Pull Requests**

O **GitPR** é uma ferramenta de Interface de Linha de Comando (CLI) desenvolvida em Python que atua como um assistente de engenharia de software diretamente no terminal. Ele combina a velocidade de validações estáticas locais com o poder analítico de Inteligências Artificiais (**Google Gemini**, **DeepSeek** e **Ollama** — local) para automatizar e elevar a qualidade de Commits, Code Reviews, Issues e Pull Requests.

Além da CLI, o GitPR também opera como **servidor MCP (Model Context Protocol)** — expondo todas as suas capacidades de IA para editores como VS Code, Cursor, Claude Desktop, Zed e Claude Code — e oferece interfaces TUI (Textual) para publicação de PRs, criação de Issues, chat de programação em par e dashboard de métricas.

## **🎯 Para que serve?**

O objetivo principal do GitPR é eliminar o trabalho repetitivo e garantir um alto padrão de qualidade (*Quality Gate*) no ciclo de vida do desenvolvimento de software. Ele resolve três problemas principais:

1. **Histórico de Git Poluído:** Força o uso de *Conventional Commits* e gera mensagens semânticas automaticamente — inclusive via git hooks instalados no repositório.  
2. **Pull Requests Vazios ou Pobres:** Escreve descrições detalhadas baseadas no diff, separando mudanças técnicas de impacto no negócio, e publica o PR diretamente no GitHub via TUI.  
3. **Dívida Técnica e Bugs:** Realiza Code Reviews semânticos e validações de regras (Regex) antes mesmo de o código sair da máquina do desenvolvedor (abordagem *Shift-Left*), além de arqueologia de código com `git blame` para rastrear a origem de regras de negócio.

---

## **✨ Funcionalidades Principais**

* **📝 Auto-Commit (`-c` / `--commit`):** Lê as alterações em *staged* (git diff) e gera uma mensagem de commit concisa no formato imperativo (Conventional Commits). No modo hook (`--hook`), injeta a mensagem diretamente no arquivo temporário do Git; ignora merges, squashes e amends.  
* **📖 Geração de Pull Request → Publicador de PR (Padrão):** Analisa o diff entre a branch atual e a principal, gerando um .md com resumo, impacto e detalhes técnicos. Em seguida abre um TUI (Textual) para revisar, editar e publicar o PR diretamente no GitHub — com auto-commit validado por linter, push automático, atualização de PR existente e merge opcional. Modificadores: `--no-publish` (só salva localmente), `--no-edit` (publica direto, sem TUI) e `--base <branch>` (branch alvo).  
* **🕵️ Code Review Inteligente (`-r` / `--review`):** Inspeciona o código alterado em busca de más práticas de arquitetura, violações de SOLID e vulnerabilidades de segurança.  
* **🔬 Auditoria de Ficheiro Completo (`-i` / `--input`):** Permite apontar o GitPR para um ficheiro específico (ex: um código legado) para que a IA faça uma análise arquitetural de cima a baixo, sugerindo refatorações para o ficheiro inteiro.  
* **⚡ Linter Estático Local (`-l` / `--linter`):** Um motor de Expressões Regulares (Regex) ultrarrápido que roda localmente para detetar erros óbvios (ex: console.log, chaves hardcoded) sem gastar tokens de IA. Suporta também **linters externos** (ESLint, PHPCS, Stylelint) como bridge Checkstyle — configurados via wizard interativo (`--linter-setup`).  
* **🪝 Integração com Git Hooks (`-ih` / `--installhooks`):** Injeta o GitPR no ciclo natural do Git, rodando o Linter num pre-commit ou sugerindo mensagens num prepare-commit-msg. Instala **5 hooks** (pre-commit, prepare-commit-msg, pre-push, post-checkout, post-merge) com **auto-sync versionado e localizado** (EN, PT-BR, PT-PT, ES, FR).  
* **🗿 Arqueologia de Código (`-b` / `--blame`):** Rastreia a origem de uma regra de negócio com `git blame` + IA (profundidade máxima de 4 commits-pai), classificando cada commit como **ORIGIN** ou **REFACTORING** e gerando uma timeline com resumo executivo.  
* **📋 Issues Padronizadas (`-is` / `--issue`):** Gera um rascunho de Issue no formato **What / Why / Where / How** e abre uma TUI para edição ou publicação via API REST do GitHub. Possui **3 motores de contexto**: diff (padrão), histórico da branch (`-ht`) e blame (`-b file:lines`).  
* **💬 Chat de Programação em Par (`-ch` / `--chat`):** TUI interativo onde a IA vê o diff atual e mantém conversa contextual, com memória por branch, slash commands (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patch e exportação de sessão.  
* **🔌 Servidor MCP (`--mcp` / `gitpr-mcp`):** Expõe todas as capacidades de IA como **12 tools**, **resources** e **7 prompts** para editores compatíveis com MCP (VS Code, Cursor, Claude Desktop, Zed, Claude Code). Instalação automática via `gitpr-mcp --install <editor|auto>`. Invocação direta sem servidor persistente: `gitpr-mcp --tool <name> --tool-args '{...}'` — JSON no stdout, diagnóstico no stderr (seguro para pipes, scripts e CI).  
* **📊 Métricas e Telemetria Local (`--metrics` / `--dashboard`):** Coleta offline de eventos (comando, status, provider, tokens, duração) com export CSV/JSON e dashboard TUI com escopo por repositório, enriquecido com tokens reais lidos do cache de prompts.  
* **🧙 Setup Wizard (`--install`):** Configuração guiada em 4 passos — templates de skills, git hooks, configuração MCP nos editores detetados e verificação da API key do provedor de IA.  
* **🔎 Status de Arquivos (`--status`):** Lista arquivos não commitados categorizados (new / modified / deleted) — rápido, sem IA e sem rede.  
* **🧩 Sistema de Plugins (`--plugins`):** Packs globais de regras de linter (`~/.gitpr/plugins/linter/*.yml`) e prompts MCP (`~/.gitpr/plugins/prompts/*.md`) aplicados aditivamente em todos os projetos.  
* **🔄 Multi-Model (Agnóstico de IA):** Permite escolher entre o **Google Gemini**, o **DeepSeek** ou o **Ollama** (local, sem rede) como motor de raciocínio, alternando dinamicamente via .env ou pela flag `--provider`, com fallback automático entre provedores.  
* **🌐 Internacionalização (`--lang`):** Interface em 5 idiomas com deteção automática do sistema operativo, fallback para inglês e override temporário por flag.  
* **🗜️ Otimização de Tokens (Map-Reduce + Smart Excludes):** Diffs acima de ~90k tokens são divididos em chunks por ficheiro e resumidos (Map) antes da consolidação final (Reduce). Lockfiles, ficheiros minificados e documentação são excluídos do diff automaticamente (listas remotas + configuração local por projeto).  
* **🔄 Auto-Update (`-u` / `--update`):** Consulta os Releases do GitHub (binário) ou PyPI (pip) e substitui o próprio executável (*hot-swap*) com rollback em caso de falha.  

---

## **🛠️ Detalhes do Desenvolvimento e Arquitetura**

O GitPR foi arquitetado focando em **Performance**, **Segurança** e **Extensibilidade**.

### **1. Facade/Mediator (core.py)**

O módulo `core.py` orquestra tudo: operações git, montagem de prompts, cache, skills, hooks, smart excludes e saída de arquivos. A CLI (`main.py`) faz apenas roteamento de flags; os módulos especializados (IA, linter, blame, issues, MCP, métricas, TUI) são coordenados pelo core. Os componentes visuais ficam isolados no sub-package `src/ui/`.

### **2. Sistema de "Skills" (Prompt Engineering Desacoplado)**

Em vez de ter os *prompts* da IA fixos no código Python, o GitPR utiliza um sistema de arquivos .md locais (Skills) que atuam como *System Instructions*.

* .gitpr.commit.md  
* .gitpr.pr.md  
* .gitpr.review.md  
* .gitpr.filereview.md  
* .gitpr.issue.md  
* .gitpr.blame.md  

Isso permite que cada equipa adapte a "personalidade" e as regras de negócio da IA sem precisar alterar uma única linha de código fonte da ferramenta. Os arquivos vivem em `.gitpr/skill/` (com migração automática de caminhos legacy da raiz do projeto).

### **3. Strategy Pattern para Provedores de IA**

O módulo `ai_providers.py` isola a comunicação com as APIs externas. O motor (Core) apenas pede um JSON, e este módulo decide como formatar a requisição usando o SDK da Google (Gemini) ou o SDK da OpenAI (DeepSeek e Ollama — 100% compatível com a API OpenAI). Características:

* **Retry Automático** (3 tentativas, intervalo de 2s) para instabilidades de rede.  
* **Fallback automático** para o outro provedor em caso de falha do configurado.  
* **JSON estruturado obrigatório** e temperature 0.0 para saída determinística.  
* **Tiering de modelos por complexidade:** tarefas simples (commit) usam o modelo secundário/barato; tarefas avançadas (review, PR, issue) usam o modelo primário.

### **4. Segurança de Chaves (Cryptography)**

As chaves de API (API_KEYS) nunca são salvas em texto limpo. O módulo `security.py` utiliza a biblioteca cryptography (Fernet) para gerar uma chave mestra local e guardar as credenciais de forma cifrada no arquivo `~/.gitpr/.env`. O **GitHub PAT** segue o mesmo padrão e é validado contra `api.github.com/user` antes de qualquer uso, com loop de re-autenticação (máx. 3 tentativas) quando expira.

### **5. Sistema de Cache MD5**

Para economizar consumo de Tokens de IA (dinheiro) e tempo (latência), o GitPR cria um hash MD5 do *prompt* gerado a partir do *diff*. Se o desenvolvedor pedir um Code Review do mesmo código duas vezes, o sistema recupera a resposta do diretório `~/.gitpr/cache/prompts/` instantaneamente. Cada entrada guarda **repo + branch** — o filtro duplo evita colisões entre projetos com o mesmo nome de branch, e o histórico de PRs cacheados alimenta o contexto de issues de histórico (`-ht`).

### **6. Triplo "Quality Gate" (Performance)**

A ferramenta foi desenhada para equilibrar o consumo de recursos:

* **Camada 1 (Linter Local):** Rápida (<100ms), offline, focada em sintaxe (via linter_engine.py e .gitpr.linter.yml).  
* **Camada 2 (Linters Externos):** Bridge Checkstyle — roda ESLint/PHPCS/Stylelint e filtra erros apenas para as linhas alteradas no diff.  
* **Camada 3 (IA Cloud):** Profunda (2s-8s), online, focada em semântica e intenção.

### **7. Map-Reduce para Diffs Gigantes**

Quando o diff ultrapassa ~90k tokens estimados, o GitPR divide-o em chunks por ficheiro (preservando os cabeçalhos `diff --git`), pede à IA um resumo técnico de cada parte (Map) e unifica tudo na mensagem final de commit, review, PR ou issue (Reduce). Ativação automática, sem flags — com progresso no console e métrica própria.

### **8. Smart Excludes (Otimização de Tokens)**

Ficheiros não-código são removidos do diff antes de ir para a IA, com duas camadas controladas remotamente: lockfiles/gerados (`.lock`, `*.min.js`, `*.map`, `*.svg`…) e prosa de documentação (`*.md`, `*.txt`, `*.rst`…). A documentação alterada ainda é comunicada à IA como **metadados** (apenas os caminhos, sem conteúdo). Cada projeto pode adicionar exclusões locais em `.gitpr/conf/gitpr.smart-excludes.json`, fundidas com a lista global em runtime. Overrides via env: `GITPR_SKIP_SMART_EXCLUDES`.

### **9. Verificação de Arquivos Unstaged**

Antes de qualquer comando de IA, o GitPR lista os arquivos não commitados (new/modified/deleted) e oferece uma TUI de seleção de staging — ou auto-stage quando `GITPR_AUTO_STAGE=true`. O comportamento é adaptado por comando (PR/issue exigem staging, review apenas informa) e pode ser desativado com `--no-unstaged-check`.

### **10. Saída Centralizada (.gitpr/reports/)**

Todos os artefatos gerados (PR, review, full review, file review, blame, issue, linter) são salvos em `.gitpr/reports/<tipo>/` via `resolve_output_path()`. Caminhos personalizados no `.env` (com separador de diretórios) são respeitados — apenas nomes de arquivo "nus" são redirecionados (retrocompatível).

### **11. Telemetria Offline (Fire-and-Forget)**

O módulo `metrics.py` regista eventos em threads daemon — a telemetria nunca pode quebrar a CLI. Cada evento guarda comando, status, provider, tokens, duração (via `time.perf_counter()`), repo e branch. O dashboard enriquece os eventos com **tokens reais** lidos do cache de prompts e faz merge incremental com o cache.

### **12. Sistema de Plugins Globais**

`~/.gitpr/plugins/` contém packs de regras de linter (`linter/*.yml`) e templates de prompts MCP (`prompts/*.md`). As regras são fundidas **aditivamente** com o `.gitpr.linter.yml` do projeto; os prompts tornam-se resources e prompts MCP dinâmicos via factory closures (evitando late-binding em loops). Plugins malformados geram warning, nunca quebram a execução.

### **13. Servidor MCP (Isolamento de stdout)**

O `mcp_server.py` roda sobre stdio e expõe 12 tools anotadas (`get_git_context`, `analyze_diff`, `analyze_unstaged_diff`, `get_full_diff`, `list_unstaged_files`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`), resources (skills, linter, prompts) e 7 prompts pré-construídos. A arquitetura isola o JSON-RPC via **monkey-patching de stdout** (todo print é redirecionado para stderr, expondo apenas o buffer real para o transporte MCP) — aplicado antes de qualquer import interno. O modo `--tool` permite invocar qualquer ferramenta diretamente da linha de comando sem servidor persistente.

### **14. Ecossistema TUI (Textual)**

As interfaces visuais vivem em `src/ui/` e seguem padrões comuns: retorno de estado via `final_action`/`final_message` (permitindo loops de re-autenticação no main), chamadas de IA em threads de fundo, modais de ajuda (F1) com URLs localizadas, e o wrapper `_with_real_stdout()` que contorna o conflito Textual×click no Windows. Aplicações: `PrPublishApp` (publicação de PR com telas de staging, commit, linter e erro), `IssueApp`, `ChatApp`, `MetricsApp` e `LinterApp`.

### **15. Motor de Internacionalização (__())**

`src/i18n.py` implementa um motor inspirado no helper `__()` do Laravel: chaves em inglês no código, traduções em JSON (`~/.gitpr/langs/{lang}.json`) baixadas OTA quando o idioma muda, fallback para o próprio texto em inglês e suporte a placeholders nomeados. Idiomas: EN, PT-BR, PT-PT, ES, FR.

### **16. Version Markers (Recursos OTA)**

Recursos remotos (traduções, thinking words, smart excludes, presets de linter, scripts de hooks) são re-baixados em bloco quando os marcadores de versão (`__lang_version__`, `__scripts_version__` no `updater.py`) mudam. Os hooks instalados são comparados com `SCRIPTS_VERSION` + `SCRIPTS_LANG` no `.env` e **auto-sincronizados silenciosamente** a cada execução (respeitando o idioma do utilizador).

### **17. Sistema de Auto-Update**

Construído com empacotamento PyInstaller, o módulo `updater.py` consulta os *Releases* do repositório no GitHub. Se houver uma nova versão, o executável faz o download do novo binário, substitui-se a si mesmo (*hot-swap*) e relança o comando perfeitamente — com rollback automático em caso de falha. Verificação diária em cache (`~/.gitpr/update_cache.json`) e guarda de conexão (socket `8.8.8.8:53`) antes de qualquer operação de rede.

### **18. Spinner Adaptativo**

Durante as chamadas de IA, o `spinner.py` roda em thread de fundo com caracteres braille, "palavras de pensamento" descobertas letra a letra (lista controlada remotamente, com cache por versão) e velocidade adaptativa ao tamanho da frase.

---

## **💻 Stack Tecnológica**

| Componente | Tecnologia |
| --- | --- |
| CLI framework | click >= 8.0.0 |
| TUI (issues, PRs, chat, dashboard) | Textual (ModalScreen, App, bindings) |
| IA (Gemini) | `google-genai` SDK |
| IA (DeepSeek / Ollama) | `openai` SDK (API compatível) |
| MCP Server | `mcp` (Python SDK oficial) |
| GitHub API | `requests` (REST, PAT via header) |
| i18n | Motor próprio `__()` inspirado no Laravel |
| Config/Build | `pyproject.toml` + setuptools >= 61 |
| Encriptação | `cryptography.fernet` (simétrica) |
| Linter | `pyyaml` (regras) + regex |
| Testes | pytest + unittest.mock |
| Empacotamento | PyInstaller (executável standalone) |

---

## **🗂️ Estrutura do Projeto**

```text
src/
├── main.py           # CLI (Click) — roteamento de comandos e flags
├── core.py           # Orquestração — git ops, prompts de IA, cache, skills, hooks
├── config.py         # Configuração, .env, API keys, modelos, plugins
├── security.py       # Encriptação Fernet (API keys em repouso)
├── cache.py          # Cache local de respostas da IA (MD5, repo+branch)
├── ai_providers.py   # Camada unificada de chamadas de IA (Gemini + DeepSeek + Ollama)
├── spinner.py        # Spinner braille animado com palavras de pensamento
├── i18n.py           # Motor de internacionalização (__())
├── linter_engine.py  # Análise estática com regex (regras YAML) + linters externos
├── linter_wizard.py  # Wizard de configuração de linters externos (bridge Checkstyle)
├── blame_engine.py   # Arqueologia de código com git blame + IA
├── issue_engine.py   # Geração de issues com IA (3 motores de contexto)
├── chat_memory.py    # Persistência de sessões do chat (repo+branch, histórico de diffs)
├── tui_issue.py      # Validação de token GitHub e entrada da TUI
├── metrics.py        # Telemetria offline (fire-and-forget, enriquecimento via cache)
├── github_api.py     # Chamadas centralizadas à API REST do GitHub (PRs)
├── mcp_server.py     # Servidor MCP (stdio) + tools/resources/prompts + modo --tool
├── updater.py        # Verificação de versão (PyPI + GitHub), hot-swap e version markers
└── ui/               # Sub-package: componentes TUI (Textual)
    ├── __init__.py       # Marcador de package (descoberta do setuptools)
    ├── issue_app.py      # TUI de edição e publicação de Issues
    ├── pr_publish_app.py # TUI do publicador de PRs + seleção de staging + telas de commit
    ├── chat_app.py       # TUI do chat de programação em par
    ├── metrics_app.py    # Dashboard TUI de métricas
    ├── linter_app.py     # Exibição de violações do linter
    ├── help_screen.py    # Modal de ajuda (F1) — atalhos e instruções
    └── pr_publish_help.py # Modal de ajuda do publicador de PR

scripts/            # Templates de git hooks localizados (5 idiomas)
templates/          # Templates remotos servidos do GitHub (--skill)
langs/              # Arquivos de tradução (pt_br, pt_pt, es, fr)
tests/              # Testes unitários (unittest + mock)
docs/               # Documentação técnica (EN canônico + sufixos de idioma)
```

---

## **📚 Documentação Detalhada**

Cada funcionalidade tem um guia dedicado em `docs/` (inglês canônico + `.pt_br` / `.pt_pt` / `.es_es` / `.fr_fr`):

* [pull-request-publication.md](pull-request-publication.md) — Publicador de PR (TUI, auto-commit, merge)  
* [understanding_chat_functionality.md](understanding_chat_functionality.md) — Chat de programação em par  
* [mcp-integration.md](mcp-integration.md) — Integração MCP com editores  
* [metricas-telemetria.md](metricas-telemetria.md) — Métricas e telemetria local  
* [plugins-system.md](plugins-system.md) — Sistema de plugins globais  
* [map-reduce-diff.md](map-reduce-diff.md) — Map-reduce para diffs gigantes  
* [smart-excludes.md](smart-excludes.md) — Otimização de tokens  
* [hooks-versioning.md](hooks-versioning.md) — Versionamento e auto-sync dos hooks  
* [linter-regras-customizadas.md](linter-regras-customizadas.md) — Regras de linter e linters externos  
* [blame-arqueologo.md](blame-arqueologo.md) — Arqueologia de código (git blame)  
* [issue-tui-help.md](issue-tui-help.md) — Issues padronizadas e TUI  
* [install-wizard.md](install-wizard.md) — Setup wizard  
* [i18n_explanation.md](i18n_explanation.md) — Motor de i18n  
* [github-pat-integration.md](github-pat-integration.md) — Segurança do GitHub PAT  

---
