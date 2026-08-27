# **🚀 Relatório de Status do Projeto: GitPR CLI — v0.0.12 (2026-08-19)**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek / Ollama). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

**Novidades desta versão (v0.0.12):**
- **Bridge de Linters Externos + Assistente `--linter-setup`:** Integração com linters maduros (ESLint, PHP_CodeSniffer, Stylelint) executados apenas nas linhas alteradas do diff, parser de saída Checkstyle XML, nova TUI de erros (`LinterApp`) e relatório Markdown consolidado em `.gitpr/reports/linter/`. O assistente interativo configura tudo com presets remotos (`templates/gitpr.linter-presets.json`) versionados pelo marcador `LINTER_PRESETS_VERSION`.
- **i18n Reparada e Completa:** O regex legado do sync capturava argumentos de call-site (`fg="cyan"`, `count=len(...)`) e gerava chaves "mangled" que sempre caíam no fallback inglês. Reparadas 51 chaves corrompidas + 36 chaves com `\n` literal em todos os 6 dicionários; auditoria AST de 638 chaves com **0 não traduzidas e 0 mangled**; paridade total de **547 chaves idênticas por arquivo**; `__lang_version__` v0.0.13 → **v0.0.20** com testes de guarda.
- **Trailer de Coautoria:** Todo commit gerado por IA recebe `Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>` — idempotente (não duplica, preserva trailers de terceiros), oculto da TUI (injetado só na execução do commit) e com opt-out `GITPR_COAUTHOR=false`.
- **Fix do Hang do MCP Server:** Todos os 12 tool handlers eram síncronos e rodavam inline no event loop — qualquer chamada bloqueante (subprocess git, download OTA, SDK de IA) travava o servidor stdio inteiro. Novo decorator `_offload` (anyio worker threads), warm-import no startup, `stdin=subprocess.DEVNULL` em todos os subprocessos e timeout duro de 10s no download de smart-excludes. Testes e2e novos com JSON-RPC stdio real.
- **Correções do Modal de Erro do Linter:** Botões "Commit with --no-verify" e "Abort" lado a lado (antes empilhados e sobrepostos); a escolha no-verify agora retoma o fluxo de commit (antes dispensava o modal e voltava ao linter em loop); push do modal adiado via `call_next` para o message pump do app.
- **Dead Code Removido + Ajustes MCP:** Classe morta `FileStageScreen` removida (item pendente do relatório anterior); `claude-code` listado no help do `gitpr-mcp --install`; alias oculto `gitpr --mcp` documentado.
- **Documentação Multilíngue Expandida:** `docs/ARCHITECTURE.md` reescrito em EN canônico + 4 locales criados (18 tópicos de arquitetura, índice de 32 docs); novo tópico `i18n_explanation` em 5 idiomas; READMEs e 4 tópicos atualizados.
- **Formatação Consistente do Codebase:** Refactor Black-style em todo o `src/` (aspas duplas, trailing commas, quebras de linha) — sem mudança funcional.
- **Skills Locais do Claude Code:** `status-report` (geração do relatório de status), `implement-fixes` (workflow de correções) e `caveman-commit` (mensagens de commit compactas — substituiu o doc `docs/caveman-commit.md`).

- **Versão atual:** 0.0.37
- **Versão dos dicionários de idioma:** v0.0.20
- **Versão dos scripts de hook:** v0.0.3
- **Publicação:** PyPI (`pip install gitpr-cli`) + GitHub Releases (binário standalone)
- **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
- **Repositório:** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)
- **Licença:** LGPL-2.1
- **Idiomas suportados:** en_us, pt_br, pt_pt, es_es, fr_fr (5 idiomas, 6 dicionários)

---

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python >= 3.10
* **CLI Framework:** Click (para comandos, flags e formatação de terminal).
* **UI/Terminal:** Textual — TUI (Text User Interface) para chat interativo, edição de issues, help screen, dashboard de métricas, PR Publisher e erros do linter (`LinterApp`).
* **Criptografia:** `cryptography.fernet` para proteção local de chaves de API e tokens GitHub.
* **Configuração:** `python-dotenv`, `pyyaml` (para o linter estático).
* **IA Providers:** Integração via SDK oficial do Google GenAI (`gemini-2.5-flash`), OpenAI SDK (`DeepSeek`), e OpenAI SDK (`Ollama` local).
* **GitHub API:** `requests` (REST API via PAT) — módulo `src/github_api.py` com `create_pull_request()`, `update_pull_request()`, `merge_pull_request()`.
* **MCP:** [mcp](https://pypi.org/project/mcp/) >= 1.0.0 (SDK oficial Anthropic para Model Context Protocol) — 12 ferramentas anotadas, 15 recursos, 7 prompts; handlers offloaded para threads via `anyio`.
* **Testes:** Pytest + `unittest.mock` (17 arquivos de teste, 264 cenários) + testes e2e do servidor MCP via subprocess real (JSON-RPC stdio).
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
* **Detecção de Merge em Progresso:** Helper `is_merge_in_progress()` (verifica `git rev-parse -q --verify MERGE_HEAD`, silencioso e worktree-safe) — usado como defesa em profundidade contra hooks antigos que chamam a CLI durante um merge.
* **Staging com Erro Real:** `stage_files()` retorna a tupla `(success, error_message)` capturando o stderr/stdout do `git add` em falhas — o erro real do git chega ao usuário em vez de ser engolido.
* **Trailer de Coautoria 🆕:** `COAUTHOR_TRAILER` + `append_coauthor_trailer()` — helper idempotente que anexa `Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>` com separação de linhas em branco; não duplica trailer existente e preserva `Co-Authored-By:` de terceiros.
* **Download OTA com Timeout Duro 🆕:** `_download_smart_excludes()` roda a requisição em thread daemon com timeout de 10s — o timeout do urllib não limita a resolução de DNS no Windows; em stall, cai para a cópia offline.
* **Subprocessos Blindados 🆕:** `stdin=subprocess.DEVNULL` em todos os `subprocess.run` — filhos não herdam mais o pipe JSON-RPC do servidor MCP (evita hang interativo).
* **Output de Linter Centralizado 🆕:** `OUTPUT_FILE_NAME_LINTER` mapeado para a pasta `linter` no `_OUTPUT_FOLDER_MAP` — relatórios salvos em `.gitpr/reports/linter/`.

### **2. Sistema de Plugins Global (`src/plugins.py`)**

* **Arquitetura de Plugins:** Sistema de extensibilidade que carrega plugins do diretório `~/.gitpr/plugins/` aplicando-se a **todos os projetos**.
* **Plugins de Linter (`linter/`):** Arquivos `.yml` com regras de regex adicionais mescladas com o `.gitpr.linter.yml` local. 🆕 `load_external_linters()` também lê a seção `external_linters` dos plugins globais.
* **Plugins de Prompt MCP (`prompts/`):** Arquivos `.md` que estendem o contexto do sistema com instruções específicas.
* **Factory Closures:** Funções `get_linter_plugins` e `get_prompt_plugins` com closures para isolar estado entre sessões.
* **Comando `--plugins`:** Lista todos os plugins globais instalados com seus tipos e paths.
* **Documentação Multilíngue:** `docs/plugins-system.md` em 5 idiomas (EN, PT-BR, PT-PT, ES, FR).

### **3. Interface CLI e Setup (`src/main.py` e `src/config.py`)**

* **Setup Inicial:** Detecta primeira execução, cria a pasta `~/.gitpr/`, e solicita interativamente as chaves de API, preferências e idioma.
* **Routing de Comandos:** Gerencia todas as flags (`--commit`, `--review`, `--fullreview`, `--linter`, `--linter-setup`, `--skill`, `--issue`, `--blame`, `--chat`, `--mcp`, `--install`, `--metrics`, `--export`, `--purge`, `--dashboard`, `--no-publish`, `--no-edit`, `--base`, `--lang`, `--provider`, `--pre-save`, `--plugins`, `--status`, `--update`).
* **Comportamento Padrão:** Executar `gitpr` sem flags abre a TUI do PR Publisher.
* **Flags:**
  * `--publish`: substituído pelo fluxo padrão — a TUI do PR Publisher abre por padrão; modificadores `--no-publish` / `--no-edit` / `--base` controlam o fluxo.
  * `--no-publish`: Gera a descrição do PR e salva localmente sem abrir o editor interativo.
  * `--no-edit`: Pula a TUI completamente — auto-commit (com validação do linter), auto-push e publica direto no GitHub.
  * `--base <branch>`: Sobrescreve a branch de destino do Pull Request.
  * `--plugins`: Lista plugins globais instalados.
  * `--linter-setup` 🆕: Abre o assistente interativo de configuração de linters externos (presets remotos + injeção no `.gitpr.linter.yml`).
  * `--version`: Exibe a versão atual do GitPR (via `@click.version_option`).
* **Variáveis de Ambiente:** `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `GITPR_SHOW_LOGS`, `GITPR_AUTO_MERGE`, `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`, `OUTPUT_FILE_NAME_LINTER` 🆕, `GITPR_COAUTHOR` 🆕 (opt-out read-only, fora do `DEFAULT_CONFIG`).
* **Ajuda Contextual:** `-h --flag` exibe documentação específica da funcionalidade com link direto (language-aware) para o GitHub. 🆕 Corrigido para flags com hífen (`--linter-setup`, `--no-publish`, `--no-edit`, `--no-unstaged-check`) — `param_name.replace('-', '_')`.
* **--lang:** Força idioma da interface para a execução atual sem persistir a alteração.
* **--provider:** Força provedor de IA (`gemini`, `deepseek`, `ollama`) para a execução atual.
* **--mcp:** Inicia o servidor MCP no transporte stdio para integração com editores — **12 ferramentas anotadas + 15 recursos + 7 prompts**.
* **--install:** Assistente guiado de 4 etapas que baixa templates de skill, instala Git Hooks, configura MCP nos editores e valida chaves de API. 🆕 Saída 100% traduzida (10 mensagens hardcoded migradas para `__()` + 34 chaves novas).
* **--metrics:** Sistema de telemetria local com escopo por repositório: `--export`, `--purge`, `--dashboard` (TUI interativa com varredura de cache).
* **--status:** Lista arquivos não commitados categorizados (new/modified/deleted) — rápido, sem IA, sem rede.
* **Relatório do Linter Condicional 🆕:** O relatório `.gitpr/reports/linter/` só é gerado quando há warnings ou erros — diffs limpos não criam mais arquivos vazios.

### **4. PR Publisher TUI (`src/ui/pr_publish_app.py` e `src/ui/pr_publish_help.py`)**

* **Interface Interativa Completa:** TUI construída com Textual para revisar, editar e publicar Pull Requests diretamente no terminal.
* **6 Telas Modais:** `StageFilesScreen`, `CommitConfirmScreen`, `CommitProgressScreen`, `CommitMessageScreen`, `LinterErrorScreen`, `ErrorScreen`.
* **Modal de Arquivos Unstaged Aprimorado:** Lista de arquivos com altura fixa (`height: 6`) e scroll interno vertical.
* **Bindings:** F1 (Help), F2 (Salvar .md local), F3 (Publicar via GitHub API), Esc (Sair).
* **Fluxo de Auto-Commit:** Linter → mensagem IA → confirma → commita → push → publica PR.
* **Verificação de Arquivos Unstaged:** Ao iniciar, verifica `git status --porcelain` e oferece modal para selecionar, pular ou cancelar.
* **Tratamento de PR Existente:** Detecta PRs abertos para a branch atual via GitHub API e oferece push ou criar novo.
* **Auto-Upstream:** Detecta falha de `git push` por falta de upstream e automaticamente tenta `--set-upstream origin <branch>`.
* **Detecção de "Nothing to commit":** Trata `git commit` sem mudanças como sucesso.
* **Merge Flow:** Após criação/atualização do PR, oferece opção de merge. Controlado por `GITPR_AUTO_MERGE`.
* **Tratamento de Erro de Merge:** Callbacks `_on_merge_success` / `_on_merge_failure` com modal de erro para HTTP 405 (conflitos) e feedback visual pós-TUI.
* **Seleção Real de Arquivos:** `StageFilesScreen.btn_stage` lê a seleção diretamente de `SelectionList.selected` — toggles individuais de linha (clique/Enter) agora são respeitados; removido o dicionário manual `_selected` que ficava fora de sincronia e o `git add` duplicado dentro da TUI (staging único no `main.py`).
* **Dead Code Removido 🆕:** A classe rascunho `FileStageScreen` (duplicata morta de `StageFilesScreen`) foi removida junto com os imports órfãos `get_unstaged_files`/`stage_files` — item dos "Próximos Passos" do relatório anterior concluído.
* **Trailer de Coautoria Oculto 🆕:** O `Co-Authored-By:` não aparece mais na tela de edição da mensagem (`CommitMessageScreen`) — é injetado apenas na execução do commit, após a confirmação do usuário. `_pending_commit_msg` permanece limpo para o fallback de título do PR.
* **Modal de Erro do Linter Corrigido 🆕:** Botões lado a lado em container `Horizontal` com `height: auto` (antes empilhados/sobrepostos pelo `1fr`); push do `LinterErrorScreen` adiado via `call_next` para o message pump do app (antes o callback era ligado à fila morta do progress screen); `skip_linter` em `_start_progress_and_commit`/`_run_linter_and_commit` garante que o commit no-verify retoma o fluxo sem reexecutar o linter.

### **5. Módulo de API do GitHub (`src/github_api.py`)**

* **Funções Compartilhadas:** `create_pull_request()`, `update_pull_request()`, `merge_pull_request()` — encapsulando chamadas REST à API do GitHub v3.
* **Autenticação via PAT:** Token de acesso pessoal validado com `GET /user` antes das operações.
* **Reaproveitamento:** Funções usadas tanto pela TUI de PR quanto pela TUI de issues.

### **6. Motor de Análise Estática / Linter (`src/linter_engine.py`)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (`+`) no git diff sem gastar cotas de IA.
* **Regras YAML:** Lê o arquivo local `.gitpr.linter.yml` (criado via `--skill`). Suporta regex de validação, ignorar comentários e ignorar diretórios específicos.
* **Plugins de Linter:** Regras adicionais carregadas de `~/.gitpr/plugins/linter/*.yml` e mescladas com as regras locais.
* **Bridge de Linters Externos 🆕:** `_run_external_linter()` executa linters externos via subprocess (`encoding="utf-8"`, `errors="replace"`, `stdin=DEVNULL`, `timeout=120`) e retorna o stdout XML **independentemente do exit code** — linters retornam > 0 quando encontram problemas.
* **Parser Checkstyle XML 🆕:** `_parse_checkstyle_xml()` extrai erros (line/severity/message) com `xml.etree.ElementTree`, tolerando linha não numérica e XML inválido.
* **Cruzamento com o Diff 🆕:** O modo diff rastreia as linhas adicionadas (`+`) e contabiliza apenas erros do XML cuja linha foi alterada no diff atual — problemas pré-existentes são ignorados.
* **Setup Só-Externo 🆕:** Sem regras regex mas com linters externos configurados, a varredura ainda roda (antes era silenciosamente ignorada).
* **Relatório Consolidado 🆕:** `generate_linter_report_content()` consolida erros regex + externos em um único Markdown.
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
* **Versionamento Centralizado:** `__version__` (0.0.37), `__lang_version__` (v0.0.20), `__scripts_version__` (v0.0.3), `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`, `LINTER_PRESETS_VERSION` 🆕 (presets de linter atualizáveis sem release).

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
* **5 Idiomas, 6 Dicionários:** en_us (padrão/fallback), pt_br, pt_pt, es/es_es, fr/fr_fr (es/fr duplicados por família).
* **Arquivos Versionados:** `__lang_version__` (v0.0.20) controla atualização dos pacotes de idioma (`langs/*.json`) — cadeia de bumps v0.0.13 → v0.0.20 nesta janela.
* **Cobertura:** 547 chaves de tradução em cada um dos 6 arquivos — **paridade total de key sets**.
* **Reparo de Chaves Corrompidas 🆕:** 51 chaves "mangled" (o regex legado do sync capturava kwargs de call-site como `fg="cyan"`) + 36 chaves com `\n` literal duplo-escapeado foram reparadas em todos os 6 arquivos — **0 mangled, 0 não traduzidas** após auditoria AST de 638 chaves.
* **i18n Completa do `--install` 🆕:** As 10 mensagens hardcoded do instalador MCP (`_run_install`, `_install_for_editor`) migradas para `__()` com kwargs nomeados; 34 chaves novas traduzidas.
* **Script de Sincronização Corrigido 🆕:** `tests/sync_i18n.py` — novo `PATTERN` para no literal de `__()` (não mais captura o `)` do call-site), `ast.literal_eval` para sequências de escape, índice `_live_key()` para migrar entradas legacy e guard de scan vazio (nunca sobrescreve com zero chaves).
* **Cache com Indexação por Idioma:** Respostas de IA cacheadas incluem o idioma corrente no chaveamento MD5.
* **Chaves Identidade por Design:** 11 chaves mantidas em EN intencionalmente (prompts de IA, marcadores universais `[OK]`/`[FAIL]`, termos técnicos).

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

### **16. Servidor MCP e Invocação CLI Direta (`src/mcp_server.py`)**

* **12 Ferramentas MCP Anotadas:** Ferramentas para `get_git_context`, `analyze_diff`, `list_unstaged_files`, `analyze_unstaged_diff`, `get_full_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`.
* **15 Recursos + 7 Prompts Templatizados:** 35 arquivos de template em `templates/gitpr.prompt.*.md`.
* **Invocação CLI Direta:** Comando `gitpr-mcp --tool <name> [--tool-args '<json>']` invoca qualquer tool MCP diretamente sem iniciar o servidor stdio JSON-RPC.
* **Registry Pattern:** `_TOOL_FUNCS` mapeia nome da tool → callable; `_get_tool_registry()` faz merge com metadados do catálogo.
* **Real Stdout Isolation:** `_write_real_stdout()` escreve diretamente no `sys.__stdout__` original (salvo antes do monkey-patching), garantindo JSON puro no stdout.
* **Listagem de Tools:** `gitpr-mcp --tool` (sem nome) lista todas as 12 tools disponíveis com assinaturas de parâmetros.
* **Carregamento Automático do .env:** API keys disponíveis automaticamente no modo CLI.
* **Offload do Event Loop 🆕:** Decorator `_offload` (`anyio.to_thread.run_sync`) aplicado às 12 tools — handlers síncronos não congelam mais o servidor stdio durante chamadas bloqueantes (causa raiz do hang do `run_linter` no Claude Code). `_TOOL_FUNCS` faz unwrap (`fn.__wrapped__`) mantendo o modo `--tool` CLI síncrono.
* **Warm-Import no Startup 🆕:** Thread de pré-importação do `src.core` — o download OTA de smart-excludes nunca atrasa a primeira chamada (import lock disputado em worker thread, nunca no loop).
* **Help do `--install` Corrigido 🆕:** `claude-code` agora aparece na lista de editores suportados do help (era aceito em `choices` mas omitido no texto).
* **Testes E2E 🆕:** `tests/test_mcp_server_e2e.py` sobe o servidor real como subprocess e fala JSON-RPC stdio (initialize, `run_linter`, `get_git_context` — cada resposta assertada em 60s), hermético via `GITPR_SKIP_SMART_EXCLUDES=1`.
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
* **Exportação Local:** `--metrics --export` gera CSV e JSON em `./.gitpr/metrics/export/` com filtro por repositório. 🆕 Exemplos de exportação (CSV/JSON) versionados no repositório e `.gitignore` ajustado — a pasta `.gitpr/reports/` não é mais ignorada.
* **Limpeza:** `--metrics --purge` remove todos os arquivos de métricas locais com confirmação interativa.

### **19. Sincronização de Hooks Git**

* **Versionamento Independente:** `__scripts_version__` (v0.0.3) controla a versão dos scripts de hook.
* **Detecção Automática:** Compara versão local com a mais recente e atualiza automaticamente.
* **Idioma-Aware:** Baixa templates de hook correspondentes ao idioma configurado.
* **Skip de Merge-Source:** O template `prepare-commit-msg` (5 variantes de idioma) usa um case POSIX que pula as fontes `message|merge|squash|commit` e verifica `.git/MERGE_HEAD` como belt-and-braces — commits gerados pelo git (`git pull`, `git merge`, `--amend`, `-c`/`-C`, `--squash`) preservam a mensagem original do git.

### **20. Bridge de Linters Externos e Assistente Interativo (`src/linter_wizard.py`, `src/ui/linter_app.py`) 🆕**

* **Assistente `--linter-setup` 🆕:** Wizard interativo que lista presets numerados (PHP_CodeSniffer, ESLint, Stylelint), mostra o comando de instalação nativa do linter e injeta o bloco `external_linters` no `.gitpr.linter.yml` (com dedup e criação da pasta `.gitpr/skill/`).
* **Presets Remotos 🆕:** `templates/gitpr.linter-presets.json` servido do GitHub com cadeia de resolução (cópia local atualizada → download → cópia stale → fallback `_LINTER_PRESETS` embutido), versionado pelo marcador `LINTER_PRESETS_VERSION` — novos linters entram sem release.
* **TUI de Erros do Linter 🆕:** `src/ui/linter_app.py` (Textual) exibe erros críticos e warnings quando há erros bloqueantes fora de hooks/quiet; em hook/quiet imprime e faz `sys.exit(1)` (bloqueio de commit preservado).
* **Relatório Markdown 🆕:** `generate_linter_report_content()` consolida erros regex + externos em `.gitpr/reports/linter/` com nome configurável via `OUTPUT_FILE_NAME_LINTER` — gerado apenas quando há violações.
* **Escopo Eficiente 🆕:** Linters externos só executam quando há arquivos modificados com extensão compatível; YAML de configuração lido uma vez por execução.
* **Cobertura de Testes 🆕:** 13 cenários em `tests/test_external_linters.py` (parser XML, subprocess, cruzamento de diff, merge de config, gerador de relatório) + 4 testes de métricas com mock herméticos.

---

## **📊 Testes e Qualidade**

| Arquivo de Teste | Cenários | Foco |
|------------------|----------|------|
| `tests/test_core.py` | 31 | Fluxos principais, git diff, PR generation, timing, merge em progresso, staging, trailer de coautoria |
| `tests/test_chat_backend.py` | 18 | Memória de chat, persistência, comandos slash |
| `tests/test_plugins.py` | 17 | Descoberta de plugins, merge de regras linter, prompts MCP |
| `tests/test_mcp_server.py` | 82 | Ferramentas MCP, recursos, annotations, patching, CLI direto, decorator `_offload` |
| `tests/test_metrics.py` | 34 | Coleta, exportação local, escopo de repo, cache token summary, duration_ms |
| `tests/test_smart_excludes.py` | 13 | Filtro pathspec inteligente |
| `tests/test_mcp_prompts.py` | 11 | Templates de prompt MCP e fallback de idioma |
| `tests/test_blame_metrics.py` | 4 | Métricas de blame: profundidade, commits, duração |
| `tests/test_linter_metrics.py` | 4 | Métricas de linter: erros, warnings, duração |
| `tests/test_thinking_words.py` | 3 | Carregamento e parsing com separador `;` |
| `tests/test_skill_command.py` | 3 | Download e validação de templates de skill |
| `tests/test_install_wizard.py` | 3 | Assistente interativo de instalação |
| `tests/test_pre_save.py` | 3 | Flag --pre-save e payload JSON |
| `tests/test_external_linters.py` | 13 🆕 | Bridge Checkstyle: parser XML, subprocess, cruzamento de diff, relatório |
| `tests/test_i18n.py` | 15 🆕 | Paridade entre idiomas, chaves mangled, truncadas e órfãs, chaves do modal de linter |
| `tests/test_mcp_server_e2e.py` | 6 🆕 | Servidor MCP real via subprocess + JSON-RPC stdio (initialize, run_linter, get_git_context) + modo `--tool` |
| `tests/test_pr_publish_linter_modal.py` | 4 🆕 | Modal de erro do linter: layout lado a lado, abort, no-verify, fluxo TUI completo com commit `no_verify=True` |
| `tests/sync_i18n.py` | — | Script de verificação de cobertura i18n (chaves órfãs, extração por literal) |

**Total:** 264 cenários de teste automatizados passando (17 arquivos de teste). Execução completa verificada nesta versão: **264/264 passed em ~44s** — primeira execução 100% verde na máquina pt-BR (as 2 falhas pré-existentes de locale em `test_external_linters.py` foram corrigidas fixando `TRANSLATIONS` a `{}` via `mock.patch`). Novos testes: `TestExternalLinters` (13), `test_i18n.py` (15), `test_mcp_server_e2e.py` (6), `test_pr_publish_linter_modal.py` (4), `TestOffloadDecorator` (7) e `TestCoauthorTrailer` (5).

---

## **🌐 Internacionalização e Documentação**

* **Cobertura i18n:** 547 chaves de tradução em cada um dos 6 dicionários (+40 desde o relatório anterior) com **paridade total de key sets** — auditoria AST de 638 chaves usadas em código: 0 mangled, 0 não traduzidas.
* **Documentos Atualizados 🆕 (todos em 5 idiomas):**
  - `docs/ARCHITECTURE.md` — reescrito em EN canônico + 4 locales criados (`ARCHITECTURE.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`): 18 tópicos de arquitetura, índice de documentação com 32 links, nota do offload do MCP e do trailer de coautoria
  - `docs/i18n_explanation.md` 🆕 — novo tópico sobre o sistema de internacionalização em 5 idiomas
  - `docs/linter-regras-customizadas.md` — novas seções 5 (Bridge Checkstyle) e 6 (Relatórios Markdown) + bloco `external_linters` na estrutura YAML
  - `docs/commit-message-ia.md` — seção "Co-Author Signature" com exemplo de console atualizado
  - `docs/mcp-integration.md` — seção "Alternative Entry Point (`gitpr --mcp`)" + `claude-code` na lista de editores
  - `docs/pull-request-publication.md` — nota de injeção do trailer por fluxo + tabela de componentes corrigida (`FileStageScreen` → `StageFilesScreen`)
  - `docs/providers-ia.md` — sincronizado
  - `README.md` + 4 locales — subseção "External Linters (Checkstyle Bridge)", linha "Linter Report" na estrutura de saída e bullet da flag `--linter-setup`
  - `docs/caveman-commit.md` — removido: o tópico virou a skill local `caveman-commit` (`.claude/skills/`)
* **Documentação em 5 idiomas:** 33 tópicos canônicos em `docs/` (29 com cobertura completa nos 5 idiomas; 4 tópicos PT-only: `como_reverter_commit_git_localmente`, `github-issue-prompt-com-gh`, `otimizacao-de-tokens`, `testar_sem_usar_pypi`).
* **Skills locais do Claude Code:** `.claude/skills/` com `status-report` 🆕 (geração deste relatório), `implement-fixes` 🆕 (workflow de correções) e `caveman-commit` 🆕 (mensagens de commit compactas) — além das existentes `new-feature` e `reports-to-memory`.
* **Memory Index:** `.claude/memory/MEMORY.md` com 32 padrões em 3 categorias (21 de projeto, 3 de referência, 8 de feedback).
* **Relatórios de tarefas:** `docs/claude-code/reports/` (65 no total; +15 novos: linter externo, chaves i18n corrompidas, staging i18n + dead code + docs MCP, skills, README, co-author, relatório de linter condicional, ARCHITECTURE EN multilíngue, co-author na TUI, hang do MCP, i18n do install wizard, i18n untranslated/mangled, modal de erro do linter) e `docs/gemini/reports/` (8, sem novos nesta janela).
* **Relatórios de status:** `docs/reports/` (12 relatórios de status).
* **Planos de desenvolvimento:** 59 arquivos documentados em `docs/plans/` (+6 novos: linter externo, chaves i18n, ARCHITECTURE multilíngue, hang do MCP ×2, correções do modal de linter).

---

## **🔄 Pipeline de Distribuição**

1. **PyPI:** `python -m build` → `twine upload dist/*` → `pip install gitpr-cli`
2. **GitHub Releases:** PyInstaller → `.exe` standalone → upload automatizado
3. **GitHub Actions:** Workflow `pr-review.yml` + `action.yml`
4. **MCP Server:** Entry point `gitpr-mcp` via `pyproject.toml`

---

## **📈 Evolução desde o Relatório Anterior (v0.0.11)**

| Área | v0.0.11 (anterior) | v0.0.12 (atual) |
|------|-------------------|----------------|
| **Versão GitPR** | 0.0.36 | **0.0.37** |
| **Versão Idioma** | v0.0.13 | **v0.0.20** |
| **Versão Scripts Hook** | v0.0.2 | **v0.0.3** |
| **Provedores IA** | Gemini + DeepSeek + Ollama | Gemini + DeepSeek + Ollama |
| **Idiomas** | 5 (en, pt_br, pt_pt, es_es, fr_fr) | 5 idiomas, 6 dicionários (es/fr duplicados) |
| **Interface** | CLI + TUI Issues + Chat TUI + MCP Server + Dashboard + PR Publisher TUI | **+ TUI de erros do linter (`LinterApp`) + assistente `--linter-setup`** |
| **Ferramentas MCP** | 12 tools (handlers inline no event loop) | **12 tools (handlers offloaded para worker threads via anyio + testes e2e stdio)** |
| **Flags CLI** | 26 flags | **27 flags (+ `--linter-setup`)** |
| **Variáveis de Ambiente** | 16 vars | **23 vars (+ `OUTPUT_FILE_NAME_LINTER` no DEFAULT_CONFIG (22 keys) + `GITPR_COAUTHOR` read-only)** |
| **Linter** | Apenas regras regex (local + plugins) | **Regex + bridge Checkstyle (ESLint/PHPCS/Stylelint) com cruzamento por linhas do diff, wizard, TUI e relatório Markdown** |
| **Mensagens de Commit** | Mensagem pura da IA | **+ trailer `Co-Authored-By: Gitpr-cli` (idempotente, oculto da TUI, opt-out `GITPR_COAUTHOR=false`)** |
| **i18n (chaves por arquivo)** | 507 em pt_BR (paridade incompleta) | **547 × 6 arquivos com paridade total — 0 mangled, 0 não traduzidas** |
| **Documentação** | 34 tópicos | **33 tópicos canônicos (29 com 5 idiomas completos) — 1 novo (i18n_explanation), 1 removido (caveman-commit → skill), 7 tópicos atualizados + ARCHITECTURE com 4 locales novos** |
| **Suíte de Testes** | 214 cenários (13 arquivos) | **264 cenários (17 arquivos, +50) — primeira execução 100% verde na máquina pt-BR** |
| **Commits desde o relatório** | 4 commits | **17 commits** |
| **PRs mergeados** | 2 PRs (#111, #114) | **8 PRs (#119, #122, #124, #127, #129, #131, #133, #135) + 2 PR_DESCs sem referência (i18n mangled, modal de linter)** |
| **Memory Index** | 27 padrões | **32 padrões em 3 categorias (projeto/referência/feedback)** |
| **Relatórios de tarefas** | 50 claude-code (+4 na janela) | **65 claude-code (+15) e 8 gemini (0 novos)** |
| **Planos de desenvolvimento** | 11+ | **59 (+6 na janela)** |

---

## **🚧 Próximos Passos**

* **Provedor Anthropic Claude:** Suporte direto à API do Claude (`claude-sonnet-5`).
* **Gráficos em ASCII/Textual no Dashboard:** Adicionar histogramas de tempo e gráficos de tendência de tokens na TUI de métricas.
* **Pipeline de Release no GitHub Actions:** Automação completa do build PyInstaller e envio de assets para o GitHub Releases.
* **Comando `--init` local:** Seed de `.gitpr/conf/` com templates de configuração local (smart-excludes, linter, etc.).
* **Mais provedores:** OpenAI direto, provedores locais adicionais.
* **Extrator de i18n do `sync_i18n.py`:** O regex trunca literais com concatenação implícita (`__("a " "b")`) — rodar o script como está reescreveria 21 chaves pela metade e perderia suas traduções. Migrar para AST (o guard em `test_i18n.py` já usa AST e não depende do script).

### ✅ Concluídos em 2026-08-27

Ver [relatório da tarefa](../claude-code/reports/develop_natan/2026-08-27_specs_backlog_onda1.md).

* ~~**91 chaves i18n ausentes**~~ — resolvido em `9a9affb`; auditoria via AST confirma 638 chaves em código = 638 nos 6 dicionários, 0 ausentes e 0 órfãs.
* ~~**Guard `missing == 0` no `test_i18n.py`**~~ — `TestNoMissingKeys` (extração via AST) + guard de órfãs.
* ~~**Sanity manual do fluxo TUI real**~~ — [docs/testing/manual_pr_publisher_e2e.md](../testing/manual_pr_publisher_e2e.md), 5 cenários com PASS/FAIL.
* ~~**Testes para PR Publisher**~~ — `test_github_api.py` (9% → 100%) e `test_pr_publish_app.py` (51% → 63%).
* ~~**Hardening de subprocesso e timeouts**~~ — `shell=True` eliminado, `GITPR_AI_TIMEOUT` (600s default), DNS-bounding formalizado em `src/net.py`.
* ~~**Linters externos no modo full-file**~~ — `--input` roda `external_linters`; XML do Checkstyle cruzado por arquivo + linha.
* ~~**Documentar `LINTER_PRESETS_VERSION`**~~ — [docs/version-markers.md](../version-markers.md).
* ~~**Referências quebradas no HELP_MAP**~~ — já corrigidas anteriormente; os 15 destinos foram verificados e todos existem.
* ~~**CLAUDE.md desatualizado**~~ — já em `0.0.37`; `--publish` ausente do CLAUDE.md, dos 5 READMEs, dos docs ativos e da CLI.
* ~~**Scripts legacy de i18n**~~ — os 5 one-offs removidos (preservados no histórico do Git).

---

**Relatório gerado em:** 2026-08-19  
**Branch:** `develop_natan`  
**Autor:** Natan Fiuza ([contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br))
