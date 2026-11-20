# Plano de Execução — Migração de Badges para BadgeForge

- **Data**: 2026-11-19
- **Branch**: `develop_natan`
- **Task**: `badgeforge_migration`

## Objetivo

Migrar a geração e a documentação dos badges do GitPR de `img.shields.io` para o **BadgeForge** (`https://devtools.natanfiuza.dev.br/api/badges/static/...`), com `?logo=gitpr`, extensão `.svg`, cores CSS (`brightgreen`, `yellow`, `red`, `blue`), estilos `flat`, `flat-square`, `plastic`, `for-the-badge`, e wrapper Markdown/HTML externo para `https://gitpr.natanfiuza.dev.br/`.

## Etapas de Execução

1. **`src/branding/badge_builder.py`**:
   - Substituir `SHIELDS_BASE` por `BADGEFORGE_BASE = "https://devtools.natanfiuza.dev.br/api/badges/static/"`.
   - Atualizar `VALID_STYLES = ("flat", "flat-square", "plastic", "for-the-badge")`.
   - Atualizar `_BADGE_MARKER` para `"devtools.natanfiuza.dev.br/api/badges/static/GitPR/"` e manter reconhecimento de marcador legado (`"img.shields.io/badge/GitPR"`) em `has_badge()` para evitar duplicação em PRs antigos republicados.
   - Atualizar `_escape(text)` para as regras do BadgeForge (`_` -> `__`, espaço -> `_`, `/` -> `%2F` antes de `quote(..., safe="")`, mantendo `-` e `.` literais).
   - Atualizar `_snippet()` para gerar `{BADGEFORGE_BASE}{_escape(BADGE_LABEL)}/{_escape(message)}.svg?color={color}&logo=gitpr` (adicionando `&style={style}` quando `style_in_url=True`).
2. **`src/main.py` e `langs/*.json`**:
   - Atualizar o `help` de `--style` em `gitpr badge` para `"BadgeForge style: flat, flat-square, plastic or for-the-badge."`.
   - Atualizar as chaves correspondentes nos 4 arquivos `langs/*.json` (`pt_br.json`, `pt_pt.json`, `es_es.json`, `fr_fr.json`).
3. **`README.md` e `docs/badge*.md`**:
   - Atualizar as 2 badges e a descrição de `gitpr badge` no `README.md`.
   - Atualizar os 5 arquivos `docs/badge.md`, `docs/badge.pt_br.md`, `docs/badge.pt_pt.md`, `docs/badge.es_es.md` e `docs/badge.fr_fr.md` para referenciar o BadgeForge e os novos snippets/estilos.
4. **Testes (`tests/badge/*` e `tests/demo/test_demo_runner.py`)**:
   - Atualizar assertions de URL, escaping (`quality-checked` sem duplo hífen), estilos válidos e testes offline (`devtools.natanfiuza.dev.br`).
   - Executar `pytest tests/badge/ tests/demo/test_demo_runner.py -v` e depois a suíte completa `pytest -v`.
