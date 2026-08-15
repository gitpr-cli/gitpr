## Completion Report — Bridge para Linters Externos (Checkstyle) + Assistente Interativo

Execução do plano `docs/plans/20260815_implementar_plugin_linter_externo.md` (Fases 1–8).

### What was done
- **Fase 1 — Configuração:** Adicionada `OUTPUT_FILE_NAME_LINTER` (`{branch}_{datetime}_LINTER.md`) ao `DEFAULT_CONFIG` em `src/config.py` e mapeada para a pasta `linter` no `_OUTPUT_FOLDER_MAP` de `src/core.py` — `resolve_output_path()` agora salva relatórios em `.gitpr/reports/linter/` automaticamente.
- **Fase 2 — Execução segura:** Nova função `_run_external_linter()` em `src/linter_engine.py` executa o comando do linter externo via `subprocess` (shell, `encoding="utf-8"`, `errors="replace"`), retornando o `stdout` (XML Checkstyle) **independentemente do exit code** — linters retornam > 0 quando encontram problemas.
- **Fase 3 — Parser e cruzamento de diff:** `_parse_checkstyle_xml()` extrai erros (line/severity/message) com `xml.etree.ElementTree`, tolerando linha não numérica e XML inválido. O modo diff agora rastreia as linhas adicionadas (`+`) em `modified_files` e contabiliza apenas erros do XML cuja linha foi alterada no diff atual. `load_external_linters()` em `src/config.py` carrega `external_linters` do `.gitpr.linter.yml` local **e** dos plugins globais. Guard do early-return ajustado: sem regras regex mas com linters externos, a varredura ainda roda (setup só-externo não é mais silenciosamente ignorado).
- **Fase 4 — Relatório e TUI:** `generate_linter_report_content()` consolida erros regex + externos em Markdown salvo em `.gitpr/reports/linter/`. Nova TUI `src/ui/linter_app.py` (Textual) exibe erros/warnings apenas quando há *errors* bloqueantes **fora** de hooks/quiet; em hook/quiet imprime e faz `sys.exit(1)`. Bloco `if linter:` de `src/main.py` substituído pelo novo fluxo (relatório → métrica → TUI/print → warnings).
- **Fase 5 — Assistente interativo:** Novo `src/linter_wizard.py` com `--linter-setup`: lista presets numerados, mostra o comando de instalação nativa e injeta o bloco no `.gitpr.linter.yml` (com dedup e criação da pasta `.gitpr/skill/`). Presets servidos remotamente por `templates/gitpr.linter-presets.json` com cadeia de resolução (cópia local atualizada → download → cópia stale → fallback `_LINTER_PRESETS` embutido), versionados pelo marcador `LINTER_PRESETS_VERSION` vs `__lang_version__` — novos linters podem ser adicionados sem release. Ao final, exibe o link da documentação via `get_doc_url()`.
- **Fase 6 — Documentação:** Seções 5 (Bridge Checkstyle) e 6 (Relatórios Markdown) adicionadas a `docs/linter-regras-customizadas.md` + bloco `external_linters` na estrutura YAML da Seção 2 — sincronizado nos 5 idiomas (EN, PT-BR, PT-PT, ES, FR). Bullet `--linter-setup` adicionado aos 5 READMEs.
- **Fase 7 — i18n:** 25 novas chaves traduzidas nos 6 pacotes (`pt_br`, `pt_pt`, `es`, `es_es`, `fr`, `fr_fr`) — com escape `\n` correto no JSON (chaves com quebra de linha real casam em runtime). `__lang_version__` v0.0.13 → **v0.0.14** para forçar re-download dos pacotes.
- **Correção auxiliar:** O help contextual (`-h --flag`) usava `locals().get(param_name)` e nunca encontrava flags com hífen (`--linter-setup`, `--no-publish`, `--no-edit`, `--no-unstaged-check`) — adicionado `param_name.replace('-', '_')` (1 linha), corrigindo também as flags pré-existentes.
- **Fase 8 — Relatório:** este documento.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/config.py | feat | `OUTPUT_FILE_NAME_LINTER` no DEFAULT_CONFIG + `load_external_linters()` (local + plugins) |
| src/core.py | feat | `OUTPUT_FILE_NAME_LINTER` → pasta `linter` no `_OUTPUT_FOLDER_MAP` |
| src/linter_engine.py | feat | `_run_external_linter()`, `_parse_checkstyle_xml()`, cruzamento por linhas adicionadas, `generate_linter_report_content()` |
| src/main.py | feat | Novo fluxo `if linter:` (relatório + TUI + hook safety), flag `--linter-setup` (option + dispatch + HELP_MAP + HELP_PRIORITY), fix do help contextual com hífen |
| src/linter_wizard.py | feat | Novo módulo: presets remotos/fallback + assistente interativo |
| src/ui/linter_app.py | feat | Nova TUI Textual de erros do linter |
| src/updater.py | feat | `__lang_version__` v0.0.13 → v0.0.14 |
| templates/gitpr.linter-presets.json | feat | Presets remotos (PHPCS, ESLint, Stylelint) servidos do GitHub |
| tests/test_external_linters.py | test | 13 novos cenários: parser XML, subprocess, cruzamento de diff, merge de config, gerador de relatório |
| tests/test_linter_metrics.py | test | 4 testes com mock de `load_external_linters` para hermetismo |
| docs/linter-regras-customizadas.md (+4 locales) | docs | Seções 5/6 + bloco `external_linters` na Seção 2, em 5 idiomas |
| README.md (+4 locales) | docs | Bullet da flag `--linter-setup` em 5 idiomas |
| langs/*.json (6 arquivos) | feat | +25 chaves traduzidas por idioma |

### Impact
- **Functionality:** `gitpr --linter` agora consolida regras regex locais/plugins + linters externos (ESLint, PHPCS, Stylelint…) em relatório Markdown único salvo em `.gitpr/reports/linter/`, filtrando apenas linhas alteradas no diff. Com erros bloqueantes fora de hooks, abre TUI; em hooks, imprime e sai com exit 1 (comportamento de bloqueio de commit preservado). `gitpr --linter-setup` configura linters externos interativamente.
- **Performance:** Linters externos só executam quando há arquivos modificados com extensão compatível; YAML de linters externos é lido uma vez por execução do motor (sem custo no modo full-file para regras regex).
- **Compatibility:** Sem breaking changes — flags e variáveis existentes intactos; `OUTPUT_FILE_NAME_LINTER` é aditiva. Usuários com setup só de linters externos (sem regras regex) passam a ser validados (antes eram silenciosamente ignorados). `__lang_version__` bump força re-download dos pacotes de idioma.

### Next steps (if applicable)
- Publicar `templates/gitpr.linter-presets.json` no `main` antes do release para o wizard baixar os presets (fallback embutido cobre o período offline).
- Propagar as 25 novas chaves para o re-download via bump `__lang_version__` (v0.0.14) — já aplicado; subir os `langs/*.json` junto.
- Considerar suporte a `external_linters` no modo full-file (`--input`) e filtro por `file` do XML (hoje o cruzamento usa apenas linha).
- Documentar o marcador `LINTER_PRESETS_VERSION` no `.env` na documentação de config (padrão Version Marker já documentado no projeto).
- `scripts/` temporário de migração i18n foi removido após uso.
