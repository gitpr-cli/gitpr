---
name: i18n-auditoria-ast-categorias
description: Auditoria autoritativa de i18n é via AST de todos os __() em src/; três categorias de falha (mangled, untranslated, missing)
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-19_i18n_untranslated_keys_mangled_fix.md
  date: 2026-08-19
  branch: develop_natan
---

A verificação confiável de cobertura de i18n do GitPR é uma **auditoria AST** que extrai
todas as chamadas `__()` de todos os módulos em `src/` (incluindo `src/ui/`) e cruza com
os 6 `langs/*.json`. Auditorias por fluxo isolado enganam: a auditoria só do fluxo
`--install` achou 19 chaves não traduzidas; a auditoria completa achou 28 em pt_br e até
110 em es/fr.

O resultado se divide em **três categorias distintas** — confundir uma com a outra leva a
"correções" que não corrigem nada:

| Categoria | Significado | Efeito |
|---|---|---|
| `mangled` | Chave existe no JSON mas nunca casa (escapes/call-site) | Fallback inglês silencioso |
| `untranslated` | Chave existe e casa, mas `value == key` | Fallback inglês silencioso |
| `missing` | Chave usada no código e ausente do JSON | Fallback inglês silencioso |

Os três sintomas são idênticos para o usuário (texto em inglês), mas o conserto de cada
um é diferente: reparar a chave, traduzir o valor, ou adicionar a entrada.

**Why:** Em 2026-08-19 os dicionários chegaram a `mangled=0` e `untranslated=0` nos 6
idiomas (547 chaves), mas ainda com `missing=91` — descrições de tools MCP, strings de
TUI (`❌ Merge Conflict`), mensagens de updater/ai_providers/github_api e linhas do
relatório de blame.

**How to apply:**
- Ao investigar "mensagem saiu em inglês", classifique primeiro em qual das 3 categorias
  ela cai — não presuma que é falta de tradução.
- **11 chaves são inglês por decisão de projeto** e não devem ser traduzidas: conteúdo de
  prompt de IA (`=== AI PR HISTORY ===`, `=== REGISTERED COMMITS ===`, instrução do resumo
  de blame, prompt do arquiteto), marcadores universais `[OK]`/`[FAIL]`, e termos técnicos
  universais (`Tokens`, `Auto-Patch`). O `ORIGIN`/`REFACTORING` do blame_engine também é
  valor de protocolo, não texto de UI. Existe allowlist em `tests/test_i18n.py`.
- `es`/`es_es` e `fr`/`fr_fr` são dicionários duplicados da mesma família — valores podem
  ser cross-preenchidos entre o par, mas os dois arquivos precisam existir e ficar em paridade.
- Chaves novas são **anexadas ao fim** de cada JSON (os arquivos não são ordenados alfabeticamente).
- Ver [[i18n-sync-regex-chaves-mangled]] e [[langs-ota-stale-race]].
