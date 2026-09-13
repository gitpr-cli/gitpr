## [1.0.0] - 2026-09-10

### Summary
This version brings a wide range of new features focused on internationalization, supporting various version control providers and significant improvements to the user experience. Users can now take advantage of a global plugin system, integration with editors, a metrics and telemetry dashboard with data export, and automated workflows for publishing and merging pull requests. Large difference processing has been optimized with map reduction, and security has been strengthened with shell injection prevention and network time limits. The command-line interface has also been enhanced with interactive configuration wizards, multi-language support, and improvements in issue generation and commit messages.

### Features
- add gitpr release subcommand for changelog (b0e5d92)
- add suggested reviewers to PR flow (c7148ed)
- add multi-forge SCM providers, migrate tests, expand translations (dd2ecef)
- add i18n translations and enhance issue/blame skill loading (9a9affb)
- add metrics export (f78970c)
- add coauthor trailer to commits (4bf8e48)
- add external linter support and setup wizard (97e584a)
- add metrics export (397ba94)
- add status translations for languages (b0ac04d) — i18n
- handle PR merge success and failure states (600a6a1)
- add mcp tool cli flag (1cc4545)
- add CLI version option (8a1adb3)
- add project-local smart excludes (86194ef)
- add unstaged files handling and telemetry exports (d3129e3)
- add global plugin system (6210d97)
- add map-reduce for large diff processing (f91af9e)
- add map-reduce for large diff issue generation (15b01ed)
- add pull request merge flow (d8283dd)
- add option to push to existing PR (744fc15)
- add existing PR handling on publish (47a9004)
- enhance progress screen with initial status (3ff5820)
- add git push before PR publishing (886c835)
- add PR publisher with TUI and auto-commit (02aa34e)
- add docs smart excludes (9a297d3)
- add i18n and automatic hook sync (6743691)
- add metrics for linter, blame, and git hooks (f509662)
- add i18n cache, sync script, and expanded translations (26c2628)
- track AI call duration and enhance metrics dashboard (1e1bfdc)
- add repo-scoped metrics dashboard and token reauth (08ba813)
- add metrics and telemetry system with CSV export and TUI dashboard (7876914)
- add MCP Tool Annotations and template-based prompts (5efd7cb)
- add adaptive speed to spinner and expand thinking words (5e3b3dc)
- add MCP prompts for common GitPR workflows (bb8287d)
- add interactive setup wizard (--install) (d69fa13)
- add MCP config installer and Claude Code support (b42ce80)
- add MCP server integration for editor support (9a25d81)
- add map-reduce, remote smart excludes, and --pre-save flag (67b300d)
- add interactive chat TUI, --lang flag, and Ollama support (d6fca4f)
- internacionaliza skills, spinner e documentação (bf46833)
- adds support for the Ollama provider (1655b95)
- adota inglês como idioma padrão e implementa i18n com  es, fr, pt_pt (f4c718c)
- implementa internacionalização com suporte a pt-BR e en-US (a1d6692)
- adiciona spinner animado com braille e palavras de pensamento (c9cdbf9)
- adiciona suporte a múltiplos repositórios no cache (9dc242c)
- adiciona ajuda contextual e documentação técnica (ad72ca2)
- adiciona motor triplo de contexto para criação de issues (ce86bcb)
- atualiza pyproject.toml (4844eb7)
- adiciona geração de issues padronizadas com TUI e integração GitHub (c76f9ae)
- adiciona geração de issues padronizadas com TUI e integração GitHub (cd458b8)
- adiciona módulo de arqueologia de código com git blame (ad4f3f4)
- adiciona suporte a PyPI e aviso de atualização (4118639)
- prepara projeto para distribuicao no PyPI (38e2e37)
- adiciona alerta de arquivos não monitorados no git diff e documentação (e56ff7a)
- adiciona suporte multi-modelo e auditoria de arquivos completos (dc1fba1)
- adiciona modo de revisão de arquivo completo via --input (4a4f53b)

### Fixes
- silence CLI tool output and bound DNS resolution (681a7fa)
- prevent shell injection in linters and bound network timeouts (7324ff2)
- resume commit flow after linter --no-verify (3d2a63a)
- translate untranslated keys and normalize newlines (e2f0fa0) — i18n
- offload MCP tool handlers from the event loop to fix server hangs (9d4d58c)
- generate linter report only on violations (eebd507)
- make sync script extraction capture only the string literal (4dc5119) — i18n
- repair 51 mangled translation keys, prune dead keys, bump lang version to v0.0.16 (2ea73ce) — i18n
- improve git add error handling and file selection (4302b58)
- skip AI commit message on git-generated sources (merge, squash, amend) (827b77c)
- change thinking words delimiter to semicolon and sync translations (9db4a29)

### Performance
- adiciona filtro smart para reduzir tokens da IA (f7ce5c0)

### Docs
- update technical documentation (61226b3)
- update technical documentation: Suggested Reviewers (a645def)
- update technical documentation (ddc8fff)
- update technical documentation (1b090f2)
- update technical documentation (43ab597)
- change GEMINI.md and CLAUDE.md files (7ae8a5c)
- updates readme (77b63bc)
- updates pr desc reports (dfd7684)
- update technical documentation (a755237)
- add plan and completion report for i18n mangled keys cleanup (46c4f6b)
- update README.md (6ba6ccb)
- atualiza memória do projeto (9b00eda)
- document merge-source skip in git-hooks-locais docs (7e28aeb)
- add Claude memory index and pattern docs (8637209)
- add v0.0.6 status report and bump version to 0.0.31 (cb5bc77)
- enhance MCP prompts docs with template info and resources (e6f0556)
- finaliza traduções multilingues e adiciona plano de chat (f8f54a2)
- reestrutura documentação e destaca ajuda contextual (aaf7330)

### Refactoring
- hide coauthor trailer from TUI (d65c175)
- format codebase for consistency (c67ab6a)
- remove unused FileStageScreen and update translations (4570646)
- centralize output path resolution (cae5be5)
- extract MCP prompts to template files (2c3fb5b)
- remove fallback pipenv e adiciona errors='replace' (aa675a7)

### Chores
- update repo URL and localize issue prompts (fa4bac1)
- bump versions to 0.0.32 and v0.0.10 (4c0d05e)
- derive version from updater and update pt_PT (25e3103)
- update lang version and refine spinner output (5dad289)
- delete exported chat log files (60ea186)
- atualiza versão para 0.0.23 (1e2e752)
- atualiza versão para 0.0.18 e corrige empacotamento (d77132a)

### Other Changes
- guard against mangled keys and enforce language parity (9ca8146) — i18n
- Create other lenguages to plugins-system doc (52229a9)
- Add tokenizer.json (1560d4f)
- Adiciona lista Thinking Words (9485cd4)
- AJustes finais (38e62d4)
- Update to 0.0.14 (60fb15f)
- Retira índice de comantários (306dc11)
- Update linter-regras-customizadas.md (1689e6e)
- Remove arquivos desnecessários (b55df27)

**Contributors:** Nataniel Fiuza
