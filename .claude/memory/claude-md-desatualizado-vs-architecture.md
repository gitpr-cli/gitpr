---
name: claude-md-desatualizado-vs-architecture
description: CLAUDE.md e GEMINI.md derivam silenciosamente do código porque são auto-carregados e ninguém os relê; conferir versão e flags contra src/ antes de citar
metadata:
  type: feedback
  source: docs/claude-code/reports/develop_natan/2026-08-18_architecture_multilang.md
  date: 2026-08-18
  branch: develop_natan
---

`CLAUDE.md` e `GEMINI.md` são carregados automaticamente em toda sessão, o que os torna
perigosos quando envelhecem: são lidos como verdade sem verificação, e ninguém os reabre
para conferir. Em 2026-08-26 a defasagem acumulada era:

| Arquivo | Estava | Realidade no código |
|---|---|---|
| CLAUDE.md | "Current version: 0.0.30" | `src/updater.py`: 0.0.37 |
| CLAUDE.md | Tabela listava a flag `--publish` | Não existe em `src/main.py` — o publisher **é** o fluxo padrão; os modificadores são `--no-publish`, `--no-edit`, `--base` |
| CLAUDE.md | Tabela sem `--chat`, `--install`, `--metrics`, `--status`, `--plugins`, `--mcp`, `--lang`, `--linter-setup` | Todas existem |
| GEMINI.md | "Current version: 0.0.35" | 0.0.37 |
| `HELP_MAP` (`src/main.py`) | `chat-interativo.md` e `metricas_analytics_dashboard.md` | Arquivos inexistentes → `get_doc_url()` gerava 2 links quebrados |

**Corrigido em 2026-08-26:** versões atualizadas nos dois arquivos, tabela de comandos do
CLAUDE.md reescrita a partir da lista real de `@click.option` e do dispatch em
`src/main.py:1435`, linha do fluxo padrão corrigida nos dois, e os 2 refs quebrados do
`HELP_MAP` apontados para `understanding_chat_functionality.md` e `metricas-telemetria.md`
(as 15 refs do HELP_MAP foram verificadas contra `docs/`).

**Why:** A tabela de flags do CLAUDE.md ficou ~dezenas de commits atrás do código. Seguir
a versão antiga produzia comandos inexistentes (`gitpr --publish`) e escondia features
inteiras. O mesmo vetor de erro atinge qualquer arquivo auto-carregado.

**How to apply:**
- Antes de citar versão, flag ou lista de features a partir de CLAUDE.md/GEMINI.md,
  **confira no código**: `src/main.py` para flags, `src/updater.py` para versões.
- Ao adicionar flag nova ao GitPR, atualize as tabelas de comando dos **dois** arquivos
  junto — é o passo que sempre foi esquecido.
- Verificação rápida de links de doc do HELP_MAP:
  `grep -oE 'get_doc_url\("[^"]+"\)' src/main.py` e testar cada um contra `docs/`.
- `docs/ARCHITECTURE.md` (EN canônico + 4 locales, reescrito em 2026-08-18 a partir do
  código com refs `file:line`) segue sendo a visão de arquitetura mais fiel.
- Ver [[docs-multilingue-convencao]] e [[help-contextual-pattern]].
