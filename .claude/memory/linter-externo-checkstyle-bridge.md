---
name: linter-externo-checkstyle-bridge
description: Bridge de linters externos usa stdout do subprocess ignorando o exit code e cruza o XML Checkstyle só com as linhas adicionadas do diff
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-15_plugin_linter_externo.md
  date: 2026-08-15
  branch: develop_natan
---

O `--linter` consolida regras regex locais/plugins **e** linters externos (ESLint, PHPCS,
Stylelint…) que emitam formato `checkstyle`. Três decisões não óbvias em
`src/linter_engine.py`:

1. **O exit code do linter externo é ignorado.** `_run_external_linter()` retorna o stdout
   independentemente do código de saída — linters retornam > 0 justamente quando *acham*
   problemas, então tratar exit != 0 como falha descartaria exatamente o caso útil.
2. **Cruzamento por linha adicionada.** `_parse_checkstyle_xml()` extrai line/severity/message
   e o modo diff só contabiliza erros cuja linha aparece entre as linhas `+` de
   `modified_files`. O cruzamento usa **apenas a linha**, não o atributo `file` do XML —
   limitação conhecida.
3. **Guard do early-return.** Setup com `external_linters` mas sem regras regex antes era
   silenciosamente ignorado; hoje a varredura roda mesmo sem regras regex.

Config vem de `load_external_linters()` (`src/config.py`), que mescla o `external_linters`
do `.gitpr.linter.yml` local **com** os plugins globais.

O assistente `gitpr --linter-setup` (`src/linter_wizard.py`) injeta blocos prontos no YAML
a partir de presets servidos remotamente em `templates/gitpr.linter-presets.json`, com a
cadeia de resolução usual (cópia local → download → cópia stale → `_LINTER_PRESETS`
embutido) e marcador `LINTER_PRESETS_VERSION`. Presets novos entram sem release.

**Why:** O objetivo é que o linter só reclame do que o autor mexeu neste diff, sem exigir
que o time reconfigure o linter nativo do projeto.

**How to apply:**
- Relatório Markdown vai para `.gitpr/reports/linter/` (`OUTPUT_FILE_NAME_LINTER`) e
  **só é escrito quando há warnings ou errors** — execução limpa não cria arquivo.
- Com erros bloqueantes fora de hook/quiet abre a TUI (`src/ui/linter_app.py`); em
  hook/quiet imprime e faz `sys.exit(1)`, preservando o bloqueio de commit.
- Pendências conhecidas: `external_linters` não funciona no modo full-file (`--input`);
  `_run_external_linter` ainda monta comando com f-string + `shell=True` (candidato a
  shlex/argv).
- Ver [[plugin-system-architecture]], [[version-marker-pattern]] e [[output-reports-centralized-paths]].
