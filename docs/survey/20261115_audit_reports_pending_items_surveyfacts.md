# Survey — Auditoria de Pendências (`🚧 Próximos Passos` e `🌐 Internacionalização e Documentação`)

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `audit_reports_pending_items`

## Contexto da tarefa

Os 25 relatórios de estado em `docs/reports/` (`relatorio_estado_ GitPR-CLI.md` até `relatorio_estado_v0.0.25.md`) registram evoluções sucessivas de código, testes, internacionalização e documentação, mantendo seções `🚧 Próximos Passos` e `🌐 Internacionalização e Documentação`. A tarefa consistiu em confrontar essas seções com o estado atual da branch `develop_natan`, separar o que já foi implementado do que permanece pendente e estruturar um roteiro em etapas executáveis em `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md`.

## Fatos levantados

1. **Itens já resolvidos no código apesar de listados em relatórios anteriores:**
   - `CHANGELOG.md` (linha 6) já contém o resumo da versão `[1.8.0]`.
   - `FileStageScreen` já foi removido de `src/ui/pr_publish_app.py` (commit `4570646` citado no `CHANGELOG.md`).
   - `gitpr --mcp` já está documentado em `docs/mcp-integration.md`.
   - O bug de detecção self-hosted e aviso de fallback já foi tratado em `src/infrastructure/scm/factory.py`, `src/scm_settings.py` e `docs/scm-multiforge.*` (§1.2).
2. **Versão SSOT desincronizada (`P1`):** `src/updater.py` define `__version__ = "1.8.0"`, mas `CLAUDE.md` (linha 8) e `GEMINI.md` (linha 8) ainda exibem `1.7.0`. `tests/unit/test_version_consistency.py` valida esses arquivos contra `src/updater.py`.
3. **Drift de documentação ADR-0019 (`P2`):** `docs/config-tui.md` (linha 159) e `docs/pull-request-publication.md` (§4, §9.1, §9.4, §14, §15 Ex. 9–10) não foram espelhados nas traduções `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`. `"pull-request-publication"` está em `_PARITY_EXCEPTIONS` (`tests/unit/test_docs_translation_parity.py:27`), e `tests/unit/test_project_config_seed_docs.py` ainda não existe.
4. **Cobertura `docs/` e links dos `README*.md` (`P3`):** `docs/` possui 52 tópicos de topo: 51 com todos os 5 idiomas e 1 exceção (`docs/github-issue-prompt-com-gh.md`), listada em `_EN_ONLY` (`tests/unit/test_docs_translation_parity.py:14-16`). Adicionalmente, `README.md` omite 6 guias canônicos (`gitpr-issue-option`, `guia-regex-gitpr`, `marketplace-publishing-guide`, `otimizacao-de-tokens`, `untracked-files`, `version-markers`), e os 4 READMEs traduzidos omitem esses 6 além de `mentor-mode`.
5. **Variáveis reais de Map-Reduce e métricas (`P4`):** Em `src/config.py` (linhas 252–353) e `docs/map-reduce-diff.md`, os parâmetros são `GITPR_MAP_REDUCE_MAX_TOKENS` (`90000`) e `GITPR_MAP_REDUCE_MAX_PART_TOKENS` (`50000`) mais variantes `<PROVIDER>`, e `src/metrics.py` expõe `map_reduce`, `chunks_count` e `duration_ms`. `docs/metricas-telemetria.*` e a ADR-0022 ainda não cobrem custo/latência de Map-Reduce.
6. **Fallback read-only na migração SCM (`P5`):** `src/scm_settings.py` (`migrate_legacy_scm_config`, linhas 217–342) trata `(OSError, PermissionError)` retornando `persisted=False` e aplicando os valores em `os.environ`, comportamento ainda não documentado em `docs/scm-multiforge.*` e ADR-0020.
7. **GitHub Enterprise em `GitHubProvider.parse_repo_ref` (`P6`):** `src/infrastructure/scm/github_provider.py` (linhas 81–94) aceita apenas o literal `github.com`, e `docs/scm-multiforge.md` (§1.2 linha 61, §3 linha 104) ainda documenta essa limitação.
8. **Erro CLI/i18n em `src/mcp_server.py` (`P7`):** `_install_for_editor` (`src/mcp_server.py:2901`) omite `claude-code` da lista de editores válidos exibida no erro, embora `--install` (`choices` na linha 3058) aceite `claude-code`. `tests/test_i18n.py` exige paridade exata AST <-> 6 JSONs de `langs/`.
9. **Extensão VS Code sem `pt-pt` (`P8`):** `extensions/vscode/` contém `package.nls.{json,pt-br.json,es.json,fr.json}` (14 chaves) e `l10n/bundle.l10n.{json,pt-br.json,es.json,fr.json}` (26 chaves), faltando `package.nls.pt-pt.json` e `l10n/bundle.l10n.pt-pt.json`.

## Decisões das rodadas

### Rodada 1
- **Escopo executável (`Q1`):** Separar as 8 tarefas determinísticas de repositório (`Etapa 1` a `Etapa 8`) de ações operacionais do mantenedor (`M1` tag/PyPI, `M2` marketplace wizard/PATs) e roadmap aberto (`M3` OpenAI/novos provedores locais).
- **`docs/github-issue-prompt-com-gh.md` (`Q2`):** Mover para `docs/extra/github-issue-prompt-com-gh.md` e remover de `_EN_ONLY` para atingir 100% (51/51) na raiz de `docs/`.
- **Estrutura do arquivo em `docs/prompts/` (`Q3`):** Salvar em `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` com Matriz Consolidada, 8 Etapas executáveis com comandos `pytest` e Seção 3 dedicada a Mantenedor & Backlog.
