# Survey Facts — Migração de Badges para BadgeForge

- **Data**: 2026-11-19
- **Branch**: `develop_natan`
- **Task**: `badgeforge_migration`

## Contexto da Tarefa

Substituir o provedor atual de badges (`img.shields.io`) pelo **BadgeForge** (`devtools.natanfiuza.dev.br/api/badges/static/...`), mantendo geração 100% offline da URL (sem requisições de rede em tempo de execução), suporte ao logo embutido `gitpr` e consistência entre código, documentação, i18n e testes.

## Decisões das Rodadas (Grilling)

### Rodada 1 (Fronteira esgotada)

1. **Q1 — Escopo da substituição**: Migração completa em todo o projeto (`src/branding/badge_builder.py`, `README.md`, `docs/badge*.md`, `langs/*.json`, `src/main.py`, `tests/badge/*` e `tests/demo/*`).
2. **Q2 — Uso do logo `gitpr`**: Incluir `logo=gitpr` em ambos os badges (badge dinâmico de PR e badge estático de adoção/README).
3. **Q3 — Link clicável**: Manter o wrapper Markdown `[![GitPR](url)](https://gitpr.natanfiuza.dev.br/)` (e `<a href><img src></a>` no topo do `README.md`), sem `?link=` na URL da imagem.
4. **Q4 — Estilos suportados em `gitpr badge --style`**: `flat`, `flat-square`, `plastic` e `for-the-badge` (excluindo `social` por ignorar `color`).
5. **Q5 — Cores e extensão**: Manter nomes CSS (`brightgreen`, `yellow`, `red`, `blue`) com extensão `.svg` obrigatória no path.
6. **Q6 — Documentação e i18n**: Atualizar os 5 arquivos `docs/badge*.md`, o help de `--style` em `src/main.py` e as traduções em `langs/*.json` para referenciar o BadgeForge (`devtools.natanfiuza.dev.br`).

## Relatório de Fatos Levantados

- **Módulo de badges**: `src/branding/badge_builder.py` concentra a construção de URLs (`SHIELDS_BASE`, `_escape`, `_snippet`, `build_pr_badge`, `build_readme_badge`, `has_badge`, `append_badge`, `attach_pr_badge`).
- **Dados do linter**: `src/branding/badge_data.py` fornece `BadgeCounts(errors, warnings)` e `collect_linter_counts(diff_text)` — não depende do provedor de imagem.
- **CLI e Demo**: `src/main.py` expõe `gitpr badge` com `--readme` e `--style` (help atual cita `shields.io`); `src/demo/demo_runner.py` usa `append_badge` e `build_pr_badge`.
- **Diferenças de sintaxe BadgeForge vs shields.io** (conforme `badgeforge.md`):
  - Rota: `https://devtools.natanfiuza.dev.br/api/badges/static/{label}/{message}.svg`
  - Escaping: `_` vira espaço; `__` vira `_` literal; `-` e `.` são literais (não dobrar `-` como no shields.io); `/` vira `%252F`.
  - Parâmetros via query string: `?color={color}&logo=gitpr` (e `&style={style}` quando especificado).
- **Documentação e i18n**: `README.md` (linhas 9, 141, 319), `docs/badge.md`, `docs/badge.pt_br.md`, `docs/badge.pt_pt.md`, `docs/badge.es_es.md`, `docs/badge.fr_fr.md` e `langs/*.json` contêm referências a `shields.io`.
- **Testes**: `tests/badge/` (`test_badge_builder.py`, `test_badge_cli.py`, `test_badge_offline.py`, `test_badge_optout.py`, `test_badge_paths.py`, `conftest.py`) e `tests/demo/test_demo_runner.py` validam URLs e comportamento offline.
