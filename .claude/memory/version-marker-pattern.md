---
name: version-marker-pattern
description: Marcadores de versão no .env controlam re-download de recursos remotos em bloco
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-18_thinking_words_dedup_version.md
  date: 2026-07-18
  branch: develop_natan
---

O GitPR usa version markers no `~/.gitpr/.env` para controlar quando recursos
remotos devem ser re-baixados. O gatilho universal é o bump de `__lang_version__`
em `src/updater.py`.

Marcadores existentes:
- `LANG_VERSION`: controla re-download dos arquivos de tradução (`langs/*.json`)
- `SMART_EXCLUDES_VERSION`: controla re-download da lista de exclusão
- `THINKING_WORDS_VERSION`: controla re-download da lista de palavras do spinner

**Um bump em `__lang_version__` refresca TODOS os recursos juntos**: traduções,
smart-excludes e thinking words. Isso é intentional — simplifica o deploy de
atualizações.

O padrão para cada recurso é:
1. Comparar marker do `.env` com `__lang_version__`
2. Se diferente (ou ausente): baixar do GitHub e stampart marker
3. Se igual: usar cópia local
4. Se download falhar: usar cópia local stale (melhor que fallback interno)

**Why:** Antes dos version markers, recursos baixados uma vez nunca mais
atualizavam (ex: thinking words ficavam congeladas na primeira instalação).
Agora, qualquer bump de `__lang_version__` propaga atualizações para toda
a base instalada.

**How to apply:**
1. Ao adicionar novo recurso remoto, criar seu próprio marker (ex: `MY_FEATURE_VERSION`)
2. Comparar com `__lang_version__` no loader
3. Bumpar `__lang_version__` quando o recurso mudar no GitHub
4. User customizations no `.env` são sobrescritas no bump (comportamento esperado)

Relacionado: [[spinner-config-pattern]], [[smart-excludes-remote-control]]
