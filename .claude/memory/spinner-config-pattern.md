---
name: spinner-config-pattern
description: Cadeia de resolução env → download GitHub → fallback para recursos configuráveis
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-02_spinner_env_config.md
  date: 2026-07-02
  branch: develop_natan
---

O projeto usa um padrão consistente de 3 níveis para carregar recursos configuráveis:

1. **`.env` local** (`~/.gitpr/.env`): se a variável existe e o version marker bate, usa direto
2. **Download do GitHub**: se `.env` está vazio ou version marker desatualizado, baixa de
   `https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/`
3. **Fallback interno**: constante hardcoded no código como último recurso (offline)

Cada nível de fallback é silencioso — nunca quebra o pipeline principal.

Este padrão é usado em:
- `_load_thinking_words()` no `src/spinner.py`
- `_load_smart_excludes()` no `src/core.py`
- `get_translations()` no `src/i18n.py`

O parser de `.env` é multi-formato: aceita palavras separadas por pipe (`|`),
ponto-e-vírgula (`;`), ou uma por linha. O separador primário é `|`.

**Why:** Centralizar a configuração no `.env` do usuário permite customização,
enquanto o download automático do GitHub garante que atualizações de templates
cheguem a todos os clientes sem novo release. O fallback interno garante
funcionamento offline.

**How to apply:** Ao adicionar novo recurso configurável remotamente:
1. Criar o template no GitHub (`templates/gitpr.<nome>.*.md`)
2. Adicionar constante `_FALLBACK_<NOME>` no módulo
3. Criar função `_load_<nome>()` com a cadeia de 3 níveis
4. Usar version marker (`__lang_version__`) como gatilho de re-download
5. NUNCA emitir output no caminho de falha (degradação silenciosa)

Relacionado: [[version-marker-pattern]], [[smart-excludes-remote-control]]
