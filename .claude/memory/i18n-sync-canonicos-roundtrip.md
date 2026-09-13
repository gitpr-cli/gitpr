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

**RECORRÊNCIA (2026-09-13, tela de config):** rodado de novo wholesale e o
estrago se repetiu — 23 chaves completas viraram fragmentos, todas com valor
EN. Assinatura do dano, para reconhecer em 5 segundos: `test_no_orphan_keys`
acusa ~24 órfãos que são **prefixos truncados** de chaves reais, e um `'...'`
fantasma que veio do regex casando `__("...")` **dentro de um docstring**
(o extrator AST ignora; o regex não). `test_no_missing_keys` acusa as mesmas
23 na forma completa. `test_identity_keys_with_braces_allowlist` passou a
falhar porque a chave `{pr_url}` do conflito de merge perdeu a tradução.

**Reparo, se acontecer:** o conjunto-alvo exato é
`tests/test_i18n.py::_keys_used_in_code()` (AST, dobra concatenação
implícita). Das 23, **21 já estavam traduzidas no HEAD** — `git show
HEAD:langs/<lang>.json` devolve os valores. As 2 nascidas na working tree
(não commitadas) não têm fonte e precisam ser traduzidas à mão. Script
cirúrgico: dropa `key not in code_keys`, repõe as ausentes do HEAD, regrava
`json.dump(sorted(...), indent=2, ensure_ascii=False)` — resultado 931 chaves
por arquivo (932 menos o `'...'` fantasma), `test_i18n.py` verde.

**Nota:** a mensagem de falha de `test_no_missing_keys` manda rodar o sync
("run `python tests/sync_i18n.py`") — é uma armadilha. O script nunca foi
migrado para o extrator AST que o próprio `test_i18n.py` já usa.

Ver também: [[i18n-auditoria-ast-categorias]], [[testes-i18n-pin-translations]],
[[langs-ota-stale-race]].
