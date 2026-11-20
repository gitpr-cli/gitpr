# Walkthrough — Migração de Badges para BadgeForge (`devtools.natanfiuza.dev.br`)

## Mudanças realizadas
- **`src/branding/badge_builder.py`**: Substituído `SHIELDS_BASE` por `BADGEFORGE_BASE = "https://devtools.natanfiuza.dev.br/api/badges/static/"`, atualizado `_escape()` para manter `-` e `.` literais (e `_` -> `__`, espaço -> `_`, `/` -> `%252F`), incluído `logo=gitpr` e `.svg` em `_snippet()`, expandido `VALID_STYLES` para `("flat", "flat-square", "plastic", "for-the-badge")`, e mantido `_LEGACY_BADGE_MARKER` em `has_badge()`.
- **`src/main.py` e `langs/*.json`**: Atualizado o texto de ajuda de `--style` em `gitpr badge` e suas traduções nos 6 arquivos de idioma (`es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt`).
- **`README.md` e `docs/badge*.md`**: Atualizados os badges no topo/rodapé do `README.md`, a lista de estilos e os 5 guias `docs/badge*.md`.
- **`tests/badge/*` e `tests/demo/test_demo_runner.py`**: Atualizadas as asserções de URL, escaping, estilos e rede offline.

## O que foi testado e resultados
- `python -m pytest tests/badge/test_badge_builder.py tests/badge/test_badge_append.py tests/badge/test_badge_cli.py tests/badge/test_badge_offline.py tests/badge/test_badge_optout.py tests/badge/test_badge_data.py tests/demo/test_demo_runner.py -v`: **108 passed** in 30.52s.
- `python -m pytest tests/badge/test_badge_paths.py -k "not test_the_badge_is_inside_the_editable_text_area" -v`: **9 passed, 1 deselected** in 8.49s (o teste assíncrono `test_the_badge_is_inside_the_editable_text_area` do Textual travou no ambiente sandbox e foi deselecionado).
- `python run.py badge --readme`: imprimiu `[![GitPR](https://devtools.natanfiuza.dev.br/api/badges/static/GitPR/quality-checked.svg?color=blue&logo=gitpr&style=flat)](https://gitpr.natanfiuza.dev.br/)`.
