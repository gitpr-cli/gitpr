# Release 1.6.0: seção em inglês controlada pela skill

## Context

A seção `## [1.6.0] - 2026-11-07` do `CHANGELOG.md` foi gerada em português. Duas causas independentes:

1. **Títulos de seção** (`Summary`, `✨ Features`, `🐛 Fixes`…) são renderizados por `__()` em render time (`src/changelog_builder.py:189-205, 244, 261`), ou seja, seguem `CURRENT_LANG`, que vem do locale do SO (`pt_br`) salvo em `~/.gitpr/.env`.
2. **Resumo da IA**: `_language_for_prompt()` (`src/release_engine.py:515-524`) deriva de `CURRENT_LANG`, e a skill local não conseguia sobrescrever isso — a regra 1 da skill ("use the language in the user message") delegava justamente para esse prompt.

Objetivo: (a) traduzir a seção 1.6.0 existente para inglês e remover dela um commit que pertence à 1.5.0; (b) fazer com que os próximos `gitpr release` produzam a seção inteira em inglês a partir de um `language:` declarado no front matter da skill local — **sem** depender de `GITPR_LANG` global.

## Decisões fechadas com o usuário

- Front matter `language: en_us` como mecanismo (não um mapa explícito de títulos).
- Remover o bullet `bump version to 1.5.0 and lang to v0.0.38 (#260)` da seção 1.6.0.
- Nenhuma flag `--lang` nova no subcomando `release`.
- `templates/gitpr.release*.md` **não** recebem front matter (template distribuído a todos os usuários; a declaração é local).

## Mudanças

### 1. Novo módulo `src/skill_frontmatter.py`

`split_front_matter(text) -> (metadata, body)` reconhece front matter apenas quando a primeira linha — após BOM opcional — é `---` e existe fechamento antes do fim do texto. Sem front matter, `---` sem fechamento, YAML malformado ou não-mapping: `({}, text)` intacto. Bloco vazio: `({}, body)`. CRLF e BOM aceitos. Nunca levanta.

### 2. `src/release_engine.py`

- `CURRENT_LANG` deixa de ser importado no topo (era snapshot); `_language_for_prompt()` importa tardiamente para enxergar `set_lang()`.
- `_SKILL_LANGUAGES`, `_normalized_skill_language()`, `_load_release_skill()` (uma única leitura da skill), `_declared_language()` (context manager que aplica `set_lang` e restaura os globais diretamente no `finally`).
- `_generate_summary()` passa a receber o `system_instruction` já extraído; `generate_release_notes()` lê a skill uma vez e envolve IA + montagem da seção no context manager.
- Cache: o idioma entra no texto do prompt, então muda o MD5 — sem código extra.

### 3. `.gitpr/skill/.gitpr.release.md`

Front matter `language: en_us`; regra 1 passa a ser autoritativa ("Always write in English, regardless of the language requested in the user message").

### 4. `CHANGELOG.md` — seção 1.6.0

Títulos traduzidos (`Summary`, `✨ Features`, `🐛 Fixes`, `📚 Docs`, `🔧 Chores`, `📦 Other Changes`, `Contributors:`), parágrafo do resumo traduzido, bullet da 1.5.0 removido.

### 5. Testes

- `tests/test_skill_frontmatter.py` (novo): parsing, strip, casos de borda.
- `tests/test_release_engine.py::TestSkillLanguageDeclaration`: idioma dirige prompt e títulos, strip do system instruction, funcionamento com `ai_summary=False`, fallback, restauração de `CURRENT_LANG`/`TRANSLATIONS`, cache por idioma.
- `EngineTestCase.setUp` ganhou patch padrão de `get_skill_context` para manter a suíte hermética.

### 6. Documentação

`docs/release-notes.md` §4.1 + 4 traduções; `CLAUDE.md` (versão 1.6.0 + bullet em Skills System); `GEMINI.md` (versão 1.6.0).

## Verificação

```powershell
python -m pytest tests/test_skill_frontmatter.py tests/test_release_engine.py -q
python -m pytest tests/ -q
```

Prova manual: com `GITPR_LANG=pt_br` e `--format json`, os títulos saem em inglês graças ao front matter da skill.
