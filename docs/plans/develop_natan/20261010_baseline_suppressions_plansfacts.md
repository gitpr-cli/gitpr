# Plano — Baseline & Supressões Auditáveis (`develop_natan`, 2026-10-10)

> Spec: [`docs/plans/20261010_skill_gitpr_baseline_spec.md`](../20261010_skill_gitpr_baseline_spec.md)
> Survey: [`docs/survey/20261010_baseline_suppressions_surveyfacts.md`](../../survey/20261010_baseline_suppressions_surveyfacts.md)
> ADR: [`docs/plans/ADR-012-baseline-suppressions.md`](../ADR-012-baseline-suppressions.md)
> Glossário: [`docs/plans/glossary-baseline.md`](../glossary-baseline.md)

## Decisões fechadas (grill, 14)

Ver survey §2. Resumo: entrega completa + docs em 5 idiomas; achados da IA no baseline via
array `findings` opcional no envelope do review; fingerprint com hash de conteúdo; config na
convenção do projeto; `create` cobre `HEAD` + `--base`; checksum divergente ⇒ baseline
ignorado + exit != 0; só `new` pontua no risk; `NormalizedFinding` em `src/domain/finding/`;
quatro escopos de supressão; Policy Pack fornece camada de supressões; id = prefixo do
fingerprint; MCP read-only; §9 reduzido a 4 chaves (as outras são invariantes); supressão de
pack nunca é gravada.

## Contratos

### Fingerprint (`src/domain/baseline/baseline_fingerprint.py`)

Payload = linhas unidas por `"\n"`, UTF-8, sem newline final; digest = `"sha256:" + sha256(payload)`.

```
1  FINGERPRINT_VERSION ("1")   # primeiro: um bump muda todo fingerprint (spec §4.4)
2  rule_identity               # rule_id, ou "category:<categoria>"
3  category (lowercase)
4  normalize_path(file_path)   # relativo ao repo, "/", lowercase
5  source                      # linter | ai | external | semgrep | ...
6  line_start
7  line_end
8  snippet_hash                # sha256 do texto da linha com espaços colapsados, ou ""
```

Nunca no payload: mensagem, timestamp, provider/modelo, branch, caminho absoluto, código ou
segredo. Só o **digest** da linha é persistido — nenhum conteúdo de código ou segredo chega ao
arquivo (spec §4.2, §7.4). Sem `rule_id` ⇒ `low_confidence = True` (achados da IA).

### `.gitpr/baseline.json`

Campos do manifest: `schema_version`, `fingerprint_version`, `policy_name`, `policy_version`,
`gitpr_version`, `created_at`, `updated_at`, `checksum`, `entries[]`. Cada entrada: fingerprint,
rule_id, category, file_path, line_start/end, severity, source, status, low_confidence,
first_seen_commit/date, last_seen_commit/date, resolved_at, suppressed, suppression_reason,
suppression_scope, suppressed_by/at, accepted_debt_owner/due_date/reason, provenance.

- Status persistidos: `existing | ignored | accepted_debt | resolved`. `new` é resultado de
  comparação, nunca gravado. O enum mantém `NEW` para o comparator.
- Checksum que não cobre a si mesmo: sha256 do JSON canônico (`sort_keys`, separadores
  `(",", ":")`, `ensure_ascii=False`) de tudo menos a chave `checksum`; entradas ordenadas por
  fingerprint antes de escrever. Reusa `checksum_bytes` (`src/domain/policy/policy_checksum.py:20`).
- Escrita atômica no idioma de `src/fix/fix_history.py:73-96`; diretório via `gitpr_dir()`.
- Nenhuma entrada guarda `message`.

### `.gitpr/baseline.overrides.yml`

`overrides.suppressions[]` (`scope` finding|rule|file|line + `reason` obrigatório + campos do
escopo) e `overrides.accepted_debt[]` (`owner` + `reason` obrigatórios, `due_date` opcional).
Schema fechado, forma de `src/domain/policy/policy_manifest.py:440-455`.

### Configuração — 4 chaves

`GITPR_BASELINE_ENABLED` (true), `GITPR_BASELINE_PATH` (.gitpr/baseline.json),
`GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` (true),
`GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` (true). `get_baseline_settings()` em `src/config.py`
(perto de `get_fix_settings()`) + 4 `ConfigField` e `Category("baseline", …)` na TUI.

### Status, escopos e bloqueio

- Hit exato ⇒ status gravado; ausência ⇒ `new`; entrada de arquivo **presente no diff** e não
  vista ⇒ `resolved`; entrada de arquivo fora do diff ⇒ permanece `existing`.
- Escopos, do mais específico ao mais amplo: `finding` > `line` (regra+arquivo+intervalo que
  contém, ignora hash de conteúdo) > `file` (regra+path glob) > `rule` (regra no repo). O mais
  específico vence e fornece o motivo exibido.
- Camadas: entradas → overrides locais → supressões do Policy Pack (memória; `policy:<nome>`).
- Bloqueio: só `new` com `level: error` mantém o `sys.exit(1)` de `src/main.py:854`.
- O baseline nunca entra em prompt.

## Fases

Cada fase é um commit isolado; o agente não commita (regra do `CLAUDE.md`).

| Fase | Entrega | Verificação |
|---|---|---|
| 0 | `src/domain/finding/finding_types.py` (dataclass canônico + `snippet_hash`/`rule_version` opcionais) e shim em `base_bridge.py` | `pytest tests/domain/finding -q` + suíte inteira |
| 1 | `baseline_fingerprint.py` puro | `pytest tests/domain/baseline/test_baseline_fingerprint.py -q` (payload/digest dourados) |
| 2 | `baseline_types.py`, `baseline_manifest.py`, `baseline_comparator.py`, `suppression_policy.py`, `__init__.py` | `pytest tests/domain/baseline -q` |
| 3 | `src/infrastructure/baseline/local_baseline_repository.py` | `pytest tests/infrastructure/baseline -q` |
| 4 | `src/linter_engine.py` → findings estruturados + `lint_findings()` | suíte de linter + `pytest tests/domain/linter -q` (retorno byte-idêntico) |
| 5 | `create_baseline.py`, `compare_against_baseline.py`, `baseline_gate.py`, `RiskSignal.BASELINE_FINDING` | `pytest tests/application/use_cases -q` |
| 6 | Integração I1–I9 (`core.py` + `main.py`) | `pytest tests/integration -q` (não-regressão byte a byte) |
| 7 | Grupo `gitpr baseline` (create/show/validate/update/suppress/unsuppress) | `pytest tests/test_baseline_cli.py -q` |
| 8 | Bloco `baseline:` no manifest de Policy Pack | `pytest tests/domain/policy tests/application/use_cases/test_validate_policy_pack.py -q` |
| 9 | Config (4 chaves + TUI) e smart-excludes | `pytest tests/test_config_schema.py tests/test_config_validation.py -q` |
| 10 | MCP `get_baseline_status` + `baseline://summary` | `pytest tests/test_mcp_server.py -q` |
| 11 | i18n (6 langs), docs (5 idiomas), README (5), policy-packs (5), mcp-integration (5), ADR-012, glossário | `pytest tests/test_i18n.py -q` |
| 12 | Gate final | `python -m pytest tests/ -v` + verificação manual |

## Integração (Fase 6)

| # | Local | Mudança |
|---|---|---|
| I1 | `src/core.py:957-972` | Envelope do review ganha `findings` opcional (formato do `gitpr.fix`); map-reduce fica prosa-only |
| I3 | `src/main.py:773` | `_resolve_baseline(required=bool(linter or review or fullreview))` após `_resolve_policy_or_die` |
| I4 | `src/main.py:794-854` | Anotação por status no relatório/terminal/TUI; `exit 1` só com erro `new` |
| I5 | `src/main.py:1437-1461` | Mesma anotação antes de `render_review_result`; sem mudança de exit code |
| I6 | `src/main.py:1444-1459` | Risk recebe só os `new`; evidência informativa de 0 pontos; `status_line` no topo |
| I7 | `src/main.py:2489-2546` | `review-pr` resolve policy + baseline por conta própria |
| I8 | `src/main.py:4095-4126` | `risk` usa `lint_findings` quando há baseline; sem baseline, bloco intocado |
| I9 | Demais fluxos | `required=False`; baseline não consultado |

## Adaptações ao spec e riscos

1. `gitpr check`/SARIF não existem ⇒ §8.2/§11.9 adiados por inexistência.
2. A Fase 4 é pré-requisito não listado no spec (sem o nome da regra nos achados, não há
   fingerprint do linter).
3. `resolved` só em arquivo tocado pelo diff — evita falso `resolved` quando o diff encolhe.
4. Cache de review invalidado uma vez pela mudança de prompt (I1) — custo aceito.
5. Review em cache obsoleto: `create` recusa registro cujo `diff` gravado diverge do atual.
6. `create --base` e `risk --base` devem andar em par — dica de uma linha quando divergirem.
7. Fingerprint sensível a deslocamento de linha: falso `new` é visível e remediável; falso
   `existing` esconderia segredo real — o viés é deliberado.
8. Bloco `baseline:` do pack é opcional (sem bump de `schema_version`); packs que o usarem
   devem declarar `min_gitpr_version` compatível.

## Fora de escopo

Dashboard web, sincronização cloud, aprovação administrativa, assinatura criptográfica,
varredura retroativa do histórico, integração Jira/Linear, marketplace de supressões,
enforcement em CI (`gitpr check`), `baseline create --pr <n>`, `gitpr --status` com baseline.
