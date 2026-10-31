# Contrato de exit code do baseline inutilizável

## Goal Description
Quando o baseline não pode ser aplicado (ausente quando exigido, adulterado, checksum divergente, ilegível), seis fluxos abortam com **exit 1** e o `check` aborta com **exit 2**. Nada disso estava documentado em um só lugar, e `baseline-suppressions.md:68` afirmava o contrário do código para `-r`/`-f`/`-i`. Este plano documentou e travou por testes de integração o contrato atual (decisões Q1–Q6). Nenhuma mudança de comportamento de exit code.

## Contrato atual (verificado no código)

| Fluxo | Onde | Baseline inutilizável |
|---|---|---|
| `-l` / `--linter` | `main.py:950` → `_resolve_baseline_or_die` (L357-387) | exit **1** |
| `-r` / `--review` | idem | exit **1** |
| `-f` / `--fullreview` | idem | exit **1** |
| `-i` / `--input` | idem | exit **1** |
| `gitpr risk` | `main.py:5292` | exit **1** |
| `gitpr review-pr` | `remote_pr.py:148` → capturado em `main.py:2817` | exit **1** |
| `gitpr check` | `run_check.py:273-289` e `327-330` | exit **2** |
| `-c`, PR, blame, issue, chat, release, split, fix | não lê o baseline | sem efeito |

Lógica da divergência: nos fluxos locais, 1 é "falhou" genérico; no `check` (CI), 1 = "reprovou" e 2 = "não consegui avaliar" (ADR-013).

## User Review Required
> [!NOTE]
> Alinhar os seis fluxos para exit 2 (breaking change) fica **explicitamente adiado**; foi registrado na seção "Decisão adiada" da doc, sem ADR (nenhuma decisão muda).

## Proposed Changes

### Docs (5 idiomas: en, pt_br, pt_pt, es_es, fr_fr)

#### [MODIFY] docs/baseline-suppressions.md (+ 4 traduções)
- Nova subseção em §3: **"Unusable baseline: exit codes per flow"** com a tabela acima (fonte canônica), a definição de *unusable baseline* e a nota "Decisão adiada".
- Corrigir L68: `-r`, `-f`, `-i` → "o baseline não muda o exit code por achado, mas **exit 1** se o arquivo não puder ser aplicado".
- Adicionar a menção de exit 1 em `risk` e `review-pr` (L69-70).
- L85 (`REQUIRE_LOCKFILE_CHECKSUM_MATCH`): trocar "exits non-zero in the flows that block" por remissão à tabela.

#### [MODIFY] docs/check-ci.md (+ 4 traduções)
- §3 linha do exit 2: manter o texto e acrescentar remissão: "Other flows exit 1 on an unusable baseline — see baseline-suppressions §3".

### Glossário

#### [MODIFY] CONTEXT.md
- Termo **Unusable baseline**: arquivo ausente (quando exigido), adulterado, com checksum divergente (guarda ligada) ou ilegível, em um fluxo que exige o baseline. Sem detalhes de implementação.

### Testes

#### [NEW] tests/integration/test_baseline_exit_code_contract.py
Conjunto completo de testes de integração verificando que um baseline inutilizável dispara:
- `-l`, `-r`, `-f`, `-i`, `risk`, `review-pr` (SCM mockado) → `exit_code == 1`, mensagem em stderr.
- `check` → `exit_code == 2`.
- `-c` → não lê o baseline (exit 0, sem mensagem de baseline).

### Correção de Suporte
#### [MODIFY] src/application/use_cases/run_check.py
- Correção de acesso de atributo em `FileRisk` (`f.file_path` em vez de `f.path`).

### Relatório (GEMINI.md)
#### [NEW] docs/gemini/reports/develop_natan/2026-10-31_baseline_exit_code_contract.md
Relatório de conclusão no formato exigido. Nenhum `git add/commit`.
