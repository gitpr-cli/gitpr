# Memory Index

> Gerado automaticamente por `/reports-to-memory` em 2026-08-26
> Baseado em 75 relatórios (67 Claude Code + 8 Gemini) de 1 branch

## Project
- [Help Contextual Pattern](help-contextual-pattern.md) — Padrão de help contextual com Click usando flag regular em vez de help_option (develop_natan, 2026-07-01)
- [Cache Filter Repo+Branch](cache-filter-repo-branch.md) — Cache JSON inclui campo repo; filtro por repo_name + branch_name evita colisões (develop_natan, 2026-07-02)
- [UI Subpackage Packaging](ui-subpackage-packaging.md) — src/ui/ requer __init__.py vazio e find-packages no pyproject.toml (develop_natan, 2026-07-02)
- [Spinner Config Pattern](spinner-config-pattern.md) — Cadeia de resolução env → download GitHub → fallback para recursos configuráveis (develop_natan, 2026-07-02)
- [Skill Folder Auto-Migration](skill-folder-auto-migration.md) — resolve_skill_path() migra arquivos legacy da raiz para .gitpr/skill/ (develop_natan, 2026-07-13)
- [Smart Excludes Remote Control](smart-excludes-remote-control.md) — Lista de exclusão do git diff controlada remotamente via template JSON (develop_natan, 2026-07-18)
- [Version Marker Pattern](version-marker-pattern.md) — Marcadores de versão no .env controlam re-download de recursos remotos em bloco (develop_natan, 2026-07-18)
- [MCP Server Isolation](mcp-server-isolation.md) — Servidor MCP usa monkey-patching de stdout para isolar JSON-RPC (develop_natan, 2026-07-23)
- [Spinner Adaptive Speed](spinner-adaptive-speed.md) — Velocidade adaptativa do spinner baseada no comprimento da frase (develop_natan, 2026-07-25)
- [Metrics Telemetry Architecture](metrics-telemetry-architecture.md) — Arquitetura de telemetria offline com fire-and-forget threads e dashboard TUI (develop_natan, 2026-07-26)
- [GitHub Token Reauth Flow](github-token-reauth-flow.md) — Validação de PAT via GET /user antes da TUI com loop de re-autenticação (develop_natan, 2026-07-28)
- [Metrics Cache Enrichment](metrics-cache-enrichment.md) — Enriquecimento de métricas com tokens reais via scan do cache de prompts (develop_natan, 2026-08-02)
- [Dashboard Repo-Scope](dashboard-repo-scope.md) — Dashboard de métricas com escopo por repositório, merge cache+eventos (develop_natan, 2026-08-02)
- [AI Call Duration Tracking](ai-call-duration-tracking.md) — Rastreamento de duração real (wall-clock) das chamadas de IA via perf_counter (develop_natan, 2026-08-02)
- [Gemini Reports Convention](gemini-reports-convention.md) — GEMINI.md estabelece relatórios em docs/gemini/reports/ paralelos aos do Claude (develop_natan, 2026-08-03)
- [Output Reports Centralized Paths](output-reports-centralized-paths.md) — Centralização de outputs em .gitpr/reports/ com resolve_output_path() e _OUTPUT_FOLDER_MAP (develop_natan, 2026-08-06)
- [Unstaged Check Before AI Commands](unstaged-check-before-ai-commands.md) — Verificação centralizada de arquivos unstaged antes de todos os comandos de IA (develop_natan, 2026-08-09)
- [Plugin System Architecture](plugin-system-architecture.md) — Sistema de plugins globais: linter aditivo + prompts MCP dinâmicos com factory closures (develop_natan, 2026-08-09)
- [Smart Excludes Local por Projeto](smart-excludes-local-projeto.md) — Arquivo local .gitpr/conf/gitpr.smart-excludes.json mergeado com lista global no runtime (develop_natan, 2026-08-10)
- [MCP Tool CLI Invocação Direta](mcp-tool-cli-invocacao-direta.md) — gitpr-mcp --tool <name> invoca tools MCP diretamente sem servidor stdio (develop_natan, 2026-08-11)
- [Hook Templates Release Ordering](hook-templates-release-ordering.md) — Templates de hook devem chegar ao main antes do bump de __scripts_version__ (develop_natan, 2026-08-12)
- [Linter Externo Checkstyle Bridge](linter-externo-checkstyle-bridge.md) — Bridge ignora exit code do linter e cruza XML só com linhas adicionadas do diff (develop_natan, 2026-08-15)
- [Co-Author Trailer Injeção Pós-Cache](coauthor-trailer-injecao-pos-cache.md) — Trailer anexado no consumo, nunca no prompt/cache; na TUI só no momento do commit (develop_natan, 2026-08-16)
- [i18n Auditoria AST e Categorias](i18n-auditoria-ast-categorias.md) — Auditoria via AST dos __() em src/; 3 categorias de falha (mangled/untranslated/missing) (develop_natan, 2026-08-19)
- [Smart Excludes no sys_inst (Map-Reduce)](smart-excludes-sys-inst-mapreduce.md) — Lista de docs excluídos vai no sys_inst para sobreviver ao fatiamento do Map-Reduce (develop_natan, 2026-08-19)

## Reference
- [Pre-Save Debug Flag](pre-save-debug-flag.md) — Flag oculta --pre-save que dumps payload completo da IA em JSON (develop_natan, 2026-07-18)
- [Docs Multilíngue Convenção](docs-multilingue-convencao.md) — Convenção docs/<nome>.<lang>.md com inglês canônico e localizações por sufixo (develop_natan, 2026-08-03)
- [GitHub API Shared Module](github-api-shared-module.md) — src/github_api.py como módulo centralizado de chamadas à API REST do GitHub (develop_natan, 2026-08-06)

## Feedback
- [Windows UTF-8 Encoding Fix](windows-utf8-encoding-fix.md) — Consoles Windows com cp1252 crasham em emojis; fix com sys.stdout.reconfigure (develop_natan, 2026-08-03)
- [TUI Stdout Conflict Fix](tui-stdout-conflict-fix.md) — Textual substitui sys.stdout e quebra click.secho() no Windows; wrapper _with_real_stdout() resolve (develop_natan, 2026-08-07)
- [Nothing to Commit Detection](nothing-to-commit-detection.md) — Detecção multilingue de "nothing to commit" no git commit — trata como sucesso, não erro (develop_natan, 2026-08-09)
- [Merge Conflict Error Handling](merge-conflict-error-handling.md) — Falha de merge no PR publisher exibe modal de erro em vez de prosseguir silenciosamente (develop_natan, 2026-08-11)
- [Staging Seleção Widget Erro Real](staging-selecao-widget-erro-real.md) — Modal de staging: seleção via dicionário paralelo dessincronizava e erros de git add eram engolidos (develop_natan, 2026-08-13)
- [i18n Sync Regex e Chaves Mangled](i18n-sync-regex-chaves-mangled.md) — Regex antiga capturava kwargs do call-site dentro da chave; nunca casavam em runtime (develop_natan, 2026-08-15)
- [CLAUDE.md/GEMINI.md Derivam do Código](claude-md-desatualizado-vs-architecture.md) — Arquivos auto-carregados envelhecem sem ninguém notar; conferir versão e flags contra src/ (corrigido em 2026-08-26) (develop_natan, 2026-08-18)
- [MCP run_linter Trava](mcp-run-linter-hangs.md) — Hang das tools MCP resolvido com _offload (anyio); se travar, taskkill gitpr-mcp.exe + reiniciar editor (develop_natan, 2026-08-18)
- [Textual Modal Callback Dead Pump](textual-modal-callback-dead-pump.md) — Push de modal em timer de tela removida liga callback do dismiss à fila morta; usar call_next no app (develop_natan, 2026-08-19)
- [Langs OTA Stale Race](langs-ota-stale-race.md) — Mudanças em langs/*.json exigem bump de __lang_version__ pós-merge; senão clientes fixam arquivo velho sob marcador novo (develop_natan, 2026-08-19)
- [Testes i18n Pin Translations](testes-i18n-pin-translations.md) — Testes que afirmam texto de usuário quebram em máquina pt-BR; fixar TRANSLATIONS={} via mock.patch (develop_natan, 2026-08-19)
