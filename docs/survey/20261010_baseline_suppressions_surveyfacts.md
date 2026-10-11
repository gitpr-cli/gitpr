# Survey — Baseline & Supressões Auditáveis

> Levantamento da sessão de grill que antecedeu a implementação do spec
> [`docs/plans/20261010_skill_gitpr_baseline_spec.md`](../plans/20261010_skill_gitpr_baseline_spec.md).
> Plano de execução: [20261010_baseline_suppressions_plansfacts.md](../plans/develop_natan/20261010_baseline_suppressions_plansfacts.md).
> Decisão arquitetural: [ADR-012](../plans/ADR-012-baseline-suppressions.md).

## 1. Contexto da tarefa

Permitir adoção progressiva do GitPR em repositórios legados: classificar achados como
`new | existing | resolved | ignored | accepted_debt`, com supressões auditáveis, dívida
técnica com dono/prazo e um baseline versionável em Git cujo checksum detecta edição manual
não rastreada. Só achados `new` bloqueiam; sem baseline, o comportamento atual permanece
byte a byte.

O spec (§0) exigia confirmar 7 fatos antes de codificar. Todos foram levantados com leitura
direta do código (três explorações paralelas + verificação pontual), e o resultado mudou o
escopo em pontos importantes (§3 abaixo).

## 2. Decisões das rodadas

### Rodada 1

| # | Pergunta | Decisão |
|---|---|---|
| Q1 | Ponto de parada da sessão | **Entrega completa** (§12 inteiro) + docs de usuário e README nos **5 idiomas** |
| Q2 | Achados da IA entram no baseline? | **Sim, via array opcional `findings` no envelope do review** (mesma chamada de IA; ausente ⇒ comportamento de hoje). `baseline create` lê o último review em cache; `--refresh` força nova chamada. Map-reduce continua prosa-only |
| Q3 | Campos do fingerprint | **Regra + categoria + path + linhas + hash do conteúdo da linha**; sem matching de realocação na v1 (linha desloca ⇒ `new`) |
| Q4 | Onde ficam as configurações | **Convenção do projeto**: `GITPR_BASELINE_*` em `~/.gitpr/.env` + categoria `baseline` em `src/config_schema.py` + `.gitpr/baseline.json` + `.gitpr/baseline.overrides.yml` |

### Rodada 2

| # | Pergunta | Decisão |
|---|---|---|
| Q5 | Origens de diff do `create` | **LOCAL (`git diff HEAD`) + `--base <branch>`**; achados da IA do cache; `--pr <n>` adiado |
| Q6 | Checksum divergente | **Baseline ignorado + aviso destacado + exit != 0** nos fluxos que bloqueiam, mandando rodar `validate`/`update --recompute` |
| Q7 | Risk scoring | **Só `new` pontua**; `existing`/`ignored`/`accepted_debt` viram evidência informativa de 0 pontos com o status em `details` |
| Q8 | Casa do modelo de finding | **Mover para `src/domain/finding/`** com `base_bridge.py` re-exportando (shim) |

### Rodada 3

| # | Pergunta | Decisão |
|---|---|---|
| Q9 | Escopos de supressão | **As quatro, com semântica precisa**: `finding` (fingerprint), `line` (regra+arquivo+intervalo que contém, ignora hash de conteúdo), `file` (regra+path glob), `rule` (regra no repo) |
| Q10 | Policy Pack fornece baseline | **Sim, já na v1**: bloco `baseline:` no manifest do pack, validado pelos mesmos validadores |
| Q11 | Id do achado na CLI | **Prefixo único do fingerprint** (`sha256:ab12cd34ef56`), curto ou completo |
| Q12 | MCP | **Tool read-only `get_baseline_status` + resource `baseline://summary`** |

### Rodada 4

| # | Pergunta | Decisão |
|---|---|---|
| Q13 | Chaves §9 vs §6 | **Invariantes no código**: `suppress_blocker_requires_reason` e `accepted_debt_requires_owner` são regras incondicionais (o §6 as exige); `default_status_for_new` não existe. Só 4 chaves viram config |
| Q14 | Supressão vinda de pack | **Camada em memória**, nunca gravada em `.gitpr/baseline.json`; exibida no `show` como `policy:<nome>`; `unsuppress` não a remove |

## 3. Relatório de fatos levantados

| # | Fato | Evidência |
|---|---|---|
| 1 | **Não existe modelo de finding para a IA.** O review devolve prosa: `{"review": "..."}` | `src/core.py:957-972`; síntese map-reduce idem em `:1201-1208` |
| 2 | Existe `NormalizedFinding` (linter/SAST) e `FindingRef` (só no `gitpr fix`) — sem campo de sugestão, sem id estável, sem `source=ai` | `src/infrastructure/linter/external/base_bridge.py:10-21`; `src/fix/patch_provenance.py:26-41` |
| 3 | **O linter devolve strings formatadas** e o nome da regra **não aparece** na mensagem (só `rule["message"]` interpolado) — impossível fingerprintar por regra hoje | `src/linter_engine.py:65-77`; `format_finding_message` em `src/domain/linter/sast_finding_mapper.py:7-14` |
| 4 | O `gitpr risk` re-parseia as strings com regex e **inventa** `category`/`source` | `src/main.py:4095-4126` |
| 5 | **Não existe fingerprint.** O MD5 do cache é chave de prompt, não id de achado; o `patch_id` do fix é escopo-de-patch | `src/cache.py:15`; `src/fix/patch_provenance.py:72-80` |
| 6 | **Não existe `.gitpr/config.yml` nem `config.schema.yml`.** Config = `~/.gitpr/.env` + `src/config_schema.py` (15 categorias na TUI) | `src/config.py:16-96,560-586`; `src/config_schema.py:134-229,262-1128` |
| 7 | **`gitpr check` e SARIF não existem** — zero ocorrências de `sarif` em `src/` | `src/main.py` (grupos: metrics, policy, tests) |
| 8 | **Só um mecanismo bloqueia**: erro do linter → `sys.exit(1)`; o hook de pre-commit roda `gitpr --linter --quiet` | `src/main.py:854`; `scripts/pre-commit-template.sh:16-33` |
| 9 | **Subcomandos não executam o callback raiz** — `review-pr` e `risk` precisam resolver baseline/policy por conta própria | `src/main.py:622-623` |
| 10 | `NormalizedFinding` já é importado por `src/domain/linter/` — a inversão de camada existe hoje | `src/domain/linter/sast_finding_mapper.py:4` |
| 11 | Precedentes reaproveitáveis: checksum sha256 de política, escrita atômica do fix_history, leitura do último review em cache, YAML de overrides de policy, recusa de escrita sem terminal | `src/domain/policy/policy_checksum.py:20-66`; `src/fix/fix_history.py:73-96`; `src/cache.py:107-144`; `src/infrastructure/policy/local_policy_repository.py:104-142`; `src/main.py:3221-3246` |
| 12 | i18n: a chave é o literal em inglês e o teste exige **paridade e ausência de órfãos** nos 6 `langs/*.json` | `src/i18n.py:116-129`; `tests/test_i18n.py:120-245` |
| 13 | Convenções de doc: ADR em `docs/plans/ADR-NNN-*.md` (próximo livre: 012), glossário em `docs/plans/glossary-*.md`, **não** existe `CONTEXT.md`; docs de usuário com 4 irmãos de idioma | `docs/plans/`; `docs/` (43 docs com o conjunto completo) |
| 14 | Testes: `unittest` majoritário, fixture de git real (`GitRepoTestCase`), rede banida por fixture autouse na integração, IA stubada por patch do nome local | `tests/fix/git_fixture.py:23-112`; `tests/integration/conftest.py:63-85` |

### Consequências dos fatos no escopo

1. **Fase extra obrigatória**: emitir findings estruturados no linter (fato 3). Sem o `rule_id`
   nos achados, o fingerprint do linter é impossível — o spec não previa essa fase.
2. **A mudança de prompt do review (Q2) invalida o cache de review uma vez** (fato 1: o envelope
   muda, o MD5 do prompt muda). Custo aceito e documentado.
3. **O §8.5 do spec (limite de contexto do baseline em prompt) fica satisfeito por abstenção**:
   o baseline nunca é injetado em prompt — a classificação é pós-hoc.
4. **O §8.2/§11.9 (check/SARIF) ficam adiados por inexistência** (fato 7).
5. **A integração vive em `main.py` + uma linha de prompt em `core.py`**, e os subcomandos
   resolvem o baseline sozinhos (fato 9).
