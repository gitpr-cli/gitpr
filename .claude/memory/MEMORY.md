# Memory Index

> Gerado automaticamente por `/reports-to-memory` em 2026-08-05
> Baseado em 36 relatórios de 1 branch

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

## Reference
- [Pre-Save Debug Flag](pre-save-debug-flag.md) — Flag oculta --pre-save que dumps payload completo da IA em JSON (develop_natan, 2026-07-18)

## Feedback
- [Windows UTF-8 Encoding Fix](windows-utf8-encoding-fix.md) — Consoles Windows com cp1252 crasham em emojis; fix com sys.stdout.reconfigure (develop_natan, 2026-08-03)
