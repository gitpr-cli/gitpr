## Completion Report — Migração de Badges para BadgeForge (`devtools.natanfiuza.dev.br`)

### What was done
- Migrado o construtor de badges em `src/branding/badge_builder.py` de `img.shields.io` para o **BadgeForge** (`https://devtools.natanfiuza.dev.br/api/badges/static/`), incluindo `?logo=gitpr`, extensão `.svg` obrigatória no path, cores CSS (`brightgreen`, `yellow`, `red`, `blue`) e suporte aos estilos `flat`, `flat-square`, `plastic` e `for-the-badge`.
- Ajustado `_escape()` em `src/branding/badge_builder.py` para as regras do BadgeForge (`_` -> `__`, espaço -> `_`, `/` -> `%252F`, mantendo `-` e `.` literais).
- Mantido o reconhecimento do marcador legado (`img.shields.io/badge/GitPR`) em `has_badge()` ao lado do novo marcador (`devtools.natanfiuza.dev.br/api/badges/static/GitPR/`) para evitar duplicação ao republicar PRs antigos.
- Atualizado o help de `--style` do subcomando `gitpr badge` em `src/main.py` e as traduções correspondentes em `langs/es.json`, `langs/es_es.json`, `langs/fr.json`, `langs/fr_fr.json`, `langs/pt_br.json` e `langs/pt_pt.json`.
- Atualizados os badges e referências no `README.md` e nos 5 arquivos de documentação (`docs/badge.md`, `docs/badge.pt_br.md`, `docs/badge.pt_pt.md`, `docs/badge.es_es.md`, `docs/badge.fr_fr.md`).
- Atualizados os testes em `tests/badge/*` e `tests/demo/test_demo_runner.py`, além de adicionado teste para reconhecimento de badge legado em `tests/badge/test_badge_append.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/branding/badge_builder.py` | feat | Migração de URL, escaping, estilos e marcador para BadgeForge |
| `src/main.py` | docs | Atualização do help de `--style` em `gitpr badge` |
| `langs/es.json`, `langs/es_es.json`, `langs/fr.json`, `langs/fr_fr.json`, `langs/pt_br.json`, `langs/pt_pt.json` | docs | Tradução da nova string de ajuda `--style` |
| `README.md` | docs | Substituição dos 2 badges e descrição de `gitpr badge` |
| `docs/badge.md`, `docs/badge.pt_br.md`, `docs/badge.pt_pt.md`, `docs/badge.es_es.md`, `docs/badge.fr_fr.md` | docs | Substituição de referências e snippets para BadgeForge |
| `tests/badge/test_badge_builder.py`, `tests/badge/test_badge_append.py`, `tests/badge/test_badge_cli.py`, `tests/badge/test_badge_offline.py`, `tests/badge/test_badge_optout.py`, `tests/badge/test_badge_paths.py`, `tests/demo/test_demo_runner.py` | test | Atualização de asserções para BadgeForge e teste de compatibilidade com badge legado |
| `docs/survey/20261119_badgeforge_migration_surveyfacts.md` | docs | Registro da sessão de `/grill-with-docs` |
| `docs/plans/develop_natan/20261119_badgeforge_migration_plansfacts.md` | docs | Plano de execução gerado pelo `/grill-with-docs` |

### Impact
- **Functionality:** Todos os badges de PR e de README passam a apontar para `https://devtools.natanfiuza.dev.br/api/badges/static/GitPR/...svg` com `logo=gitpr`, mantendo geração 100% offline.
- **Performance:** Sem impacto (montagem puramente textual da URL).
- **Compatibility:** `has_badge()` reconhece tanto o formato novo quanto o legado (`img.shields.io/badge/GitPR`).

### Next steps (if applicable)
- Executar `pipenv run pytest tests/badge/test_badge_paths.py -v` fora do sandbox (onde o Textual TUI `app.run_test()` não trava) e revisar/commitar as alterações no working tree.
