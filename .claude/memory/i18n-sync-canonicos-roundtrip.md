---
name: i18n-sync-canonicos-roundtrip
description: Adicionar key i18n nova com script cirúrgico — arquivos canônicos aceitam json round-trip byte-safe; nunca rodar tests/sync_i18n.py wholesale
metadata:
  type: feedback
  source: docs/claude-code/reports/develop_natan/2026-09-05_scm_multiforge_providers.md
  date: 2026-09-05
  branch: develop_natan
---

Adicionar chaves i18n novas (Etapas 3–8 do Multi-Forge, 14–15 keys por vez nos
6 `langs/*.json`) sem nunca rodar `tests/sync_i18n.py` wholesale: ele é
regex-based, reconstrói os arquivos e **mangla** (ver [[i18n-sync-regex-chaves-mangled]]).

Padrão que funcionou (scripts `tests/_stage*_i18n_insert.py`, cirúrgicos,
deletados após uso):

1. **Diagnóstico de canonicalidade por arquivo**: `bytes == json.dumps(
   json.loads(bytes), indent=2, ensure_ascii=False, sort_keys=True) + "\n"`
   com CRLF. Canônico → caminho seguro de **round-trip completo** (load → merge
   das keys → dumps → CRLF): preserva TODOS os valores existentes exatamente.
2. Não-canônico → **line_insert byte-exact**: inserir cada linha nova logo após
   a linha-âncora do predecessor na ordem de sort (processar em ordem crescente;
   se o predecessor for a última key do arquivo, ele ganha vírgula).
3. Verificações obrigatórias por arquivo: contagem 661→675 (ou +N), round-trip
   parse, **idempotência** (re-aplicar devolve os mesmos bytes) e ausência
   prévia da key. Âncoras de voz: ler valores existentes antes de traduzir
   (ex.: pt_pt usa "ficheiro .env"; fr usa " :" tipográfico antes de dois-pontos;
   es/es_es formais "Ejecute").

**Fatos que parecem bugs e não são:**
- **Canonicalidade é por arquivo vs. o próprio dump** — NÃO é byte-parity entre
  es.json/es_es.json e fr.json/fr_fr.json: drift histórico LEGÍTIMO em valores
  legados (ex.: "Timeout de API de GitHub" vs "Timeout de la API de GitHub").
  O gate `test_i18n` exige igualdade do **SET de keys** por arquivo e tradução
  ≠ key com `{braces}` — nunca espelhar os pares byte a byte.
- Não confundir o count 661 pré-Etapa-8 com valor mágico: o gate usa contagem
  >500 e paridade entre os 6, não um número fixo.

**Why:** uma tentativa de "auditoria de espelho" over-strict (es == es_es)
faliu à toa, e rodar o sync wholesale reconstruiria os 6 JSONs perdendo o
drift legado ou manglando chaves — quebra o gate em runtime silenciosamente.

**How to apply:** ao tocar strings de usuário, rodar `python -m pytest
tests/test_i18n.py -q` (gate de 20 testes) depois de qualquer sync manual.

Ver também: [[i18n-auditoria-ast-categorias]], [[testes-i18n-pin-translations]],
[[langs-ota-stale-race]].
