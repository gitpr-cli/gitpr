## Completion Report — Atualização dos READMEs para Linters Externos (Checkstyle Bridge)

Complemento documental do commit `97e584a` (feat: add external linter support and setup wizard), que já havia adicionado o bullet da flag `--linter-setup` e as seções 5/6 de `docs/linter-regras-customizadas.md` nos 5 idiomas. Este relatório cobre os pontos dos READMEs que ainda não refletiam a implementação.

### What was done
- Nova subseção **"External Linters (Checkstyle Bridge)"** na seção "Local Linter (Static Analysis)" de cada README: bridge para linters externos (ESLint, PHP_CodeSniffer, Stylelint) via formato `checkstyle`, assistente `gitpr --linter-setup`, presets remotos (`templates/gitpr.linter-presets.json`) e consolidação em relatório Markdown.
- Linha **"Linter Report"** adicionada à tabela "Output Directory Structure" (`.gitpr/reports/linter/`).
- Descrição do link "Customizable Static Linter" na seção "Technical Documentation" atualizada para cobrir bridge de linters externos e relatórios Markdown.
- Tudo sincronizado nos 5 idiomas: EN, PT-BR, PT-PT, ES, FR.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| README.md | docs | Subseção External Linters + linha Linter Report + link de doc atualizado |
| README.pt_br.md | docs | Idem em PT-BR ("Linters Externos (Bridge via Checkstyle)") |
| README.pt_pt.md | docs | Idem em PT-PT (terminologia PT-PT: "guardado", "ficheiro") |
| README.es_es.md | docs | Idem em ES ("Linters Externos (Bridge vía Checkstyle)") |
| README.fr_fr.md | docs | Idem em FR ("Linters Externes (Bridge via Checkstyle)") |

### Impact
- **Functionality:** Nenhuma — somente documentação. Os READMEs agora descrevem corretamente o `--linter-setup`, o bridge Checkstyle e o destino `.gitpr/reports/linter/` dos relatórios.
- **Performance:** N/A.
- **Compatibility:** Nenhum breaking change. Conteúdo factual verificado contra `templates/gitpr.linter-presets.json` (presets PHPCS, ESLint, Stylelint) e `OUTPUT_FILE_NAME_LINTER` (DEFAULT_CONFIG).

### Next steps (if applicable)
- Commit e push das alterações (aguardando instrução do usuário).
- Publicar `templates/gitpr.linter-presets.json` no `main` antes do release (pendência já registrada no relatório da feature).
