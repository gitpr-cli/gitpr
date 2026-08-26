---
name: i18n-sync-regex-chaves-mangled
description: Regex antiga do sync_i18n capturava kwargs do call-site dentro da chave, gerando chaves que nunca casam em runtime
metadata:
  type: feedback
  source: docs/claude-code/reports/develop_natan/2026-08-15_i18n_mangled_keys_cleanup.md
  date: 2026-08-15
  branch: develop_natan
---

O `tests/sync_i18n.py` gerou por muito tempo chaves "mangled" nos 6 `langs/*.json` —
chaves cujo texto engolia fragmentos do call-site, como
`'📋 Auto-staging {count} file(s)...", count=len(unstaged)), fg="cyan'`.
Essas chaves **nunca casam** no `__()` em runtime, então a mensagem sempre caía no
fallback inglês mesmo com o idioma instalado. Foram 51 chaves por arquivo na primeira
limpeza (2026-08-15) e mais 36 por arquivo na segunda (2026-08-19).

**Why:** Duas causas distintas, ambas na extração:

1. **Regex exigia `)` de fechamento** depois da aspa do literal. Como muitos `__()`
   recebem kwargs (`__("...", count=len(x)), fg="cyan")`), o match corria além do
   literal e capturava tudo até o último parêntese.
2. **Escapes não resolvidos.** Chaves gravadas com `\n` literal (barra + n) e `\'`
   literal não correspondem à string de runtime, que tem newline real e apóstrofo real.

Houve ainda um incidente operacional: numa primeira execução o scan retornou zero
chaves e o script **sobrescreveu os 6 JSONs** com dicionários vazios.

**How to apply:**
- O `PATTERN` corrigido para na própria aspa do literal e passa o capturado por
  `ast.literal_eval` — os escapes viram a string exata de runtime.
- Chamadas `__()` com literais adjacentes (concatenação implícita em várias linhas)
  não são extraíveis: refatore para um único literal, como foi feito no
  `src/mcp_server.py`. Descrições multi-linha de prompts MCP são limitação conhecida
  do PATTERN — chaves truncadas delas nascem mortas.
- O sync tem `_live_key()` (índice que desescapa) para migrar entradas legacy em vez
  de descartá-las, e um **guard que recusa escrever quando o scan extrai 0 chaves**.
  Nunca remova esse guard.
- `tests/test_i18n.py` guarda o padrão de chave mangled, a paridade entre os 6 arquivos
  e a contagem — rode-o depois de qualquer mexida em `langs/`.
- Ver [[i18n-auditoria-ast-categorias]], [[langs-ota-stale-race]] e [[testes-i18n-pin-translations]].
