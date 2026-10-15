# Plano — `gitpr check`: Unified CI Command (`develop_natan`, 2026-10-14)

> Spec: [`docs/plans/20261012_skill_gitpr_check_ci_spec.md`](../20261012_skill_gitpr_check_ci_spec.md)
> Survey: [`docs/survey/20261012_check_ci_surveyfacts.md`](../../survey/20261012_check_ci_surveyfacts.md)
> ADR: [`docs/plans/ADR-013-check-ci-command.md`](../ADR-013-check-ci-command.md)
> Glossário: [`docs/plans/glossary-check-ci.md`](../glossary-check-ci.md)

## 1. Decisões fechadas (Grill, 14)

Ver survey §2 e ADR-013. Resumo:
- Severidade de 3 níveis (`error|warning|info`) com folding dos aliases (`minor` -> `warning`, `major|critical|blocker` -> `error`).
- Configuração via variáveis de ambiente `GITPR_CHECK_*` + flags CLI (`flags > env > defaults`).
- Sem baseline: `baseline_status = null`, todos os achados contam para `--fail-on`. Baseline corrompido/divergente ⇒ erro fatal exit code 2.
- Risk scoring é puramente informativo (SARIF `properties.risk_score` e JSON `risk`).
- IA ligada por padrão, degrada graciosamente se sem chave; falha de chamada no meio ⇒ exit code 2.
- Deadline global (`GITPR_CHECK_TIMEOUT_SECONDS`, default 300s); estouro gera artefato com `incomplete: true` e exit code 2.
- Mascaramento de segredos em gargalo único em `check_output.py` antes de qualquer serialização.
- Saída padrão (stdout) recebe apenas o artefato estruturado (quando `--output` for omitido); logs e avisos vão para stderr.
- Auto-detecção de diff base no CI (`GITHUB_BASE_REF` -> `origin/main` -> `HEAD`).
- Entrega completa com documentação em 5 idiomas, `README.*.md`, `langs/*.json` e atualização do `action.yml`.
- `tool.driver.rules` dinâmico em SARIF para compatibilidade total com GitHub Code Scanning.
- Envelope JSON estruturado com resumo, score de risco e findings.
- `--policy` estrito: política inválida ou inexistente aborta imediatamente com exit code 2.

## 2. Contratos e Arquitetura

### 2.1 Domain (`src/domain/check/`)

- `check_types.py`:
  - `CheckSeverity` (enum: `INFO = "info"`, `WARNING = "warning"`, `ERROR = "error"`) + helper `parse_severity(str) -> CheckSeverity` que trata aliases (`minor`, `major`, `critical`, `blocker`).
  - `CheckOutputFormat` (enum: `SARIF = "sarif"`, `JSON = "json"`, `JUNIT = "junit"`).
  - `CheckFinding`:
    - `fingerprint: str`
    - `rule_id: str`
    - `category: str`
    - `file_path: str`
    - `line_start: int`
    - `line_end: int`
    - `severity: CheckSeverity`
    - `source: str`
    - `message: str`
    - `suggestion: str | None`
    - `baseline_status: str | None`
    - `risk_score: float | None`
    - `provenance: dict`
  - `CheckSummary`: contagem por severidade e status de baseline.
  - `CheckResult`:
    - `findings: list[CheckFinding]`
    - `exit_code: int` (0, 1, 2)
    - `fail_on: CheckSeverity`
    - `output_format: CheckOutputFormat`
    - `output_path: str | None`
    - `analysis_version: str`
    - `warnings: list[str]`
    - `incomplete: bool`
    - `risk_summary: dict | None`

- `check_config.py`:
  - `CheckConfig` dataclass:
    - `base_ref: str | None`
    - `output_format: CheckOutputFormat`
    - `output_path: str | None`
    - `fail_on: CheckSeverity`
    - `no_ia: bool`
    - `ia_only_high_risk: bool`
    - `baseline_path: str | None`
    - `policy_name: str | None`
    - `policy_version: str | None`
    - `timeout_seconds: int`
  - `load_check_config(cli_args) -> CheckConfig` resolvendo `CLI flags > env vars > defaults`.

### 2.2 Infrastructure / Builders (`src/infrastructure/ci/`)

- `sarif_builder.py`:
  - `build_sarif(result: CheckResult, repo_path: str | None = None) -> dict`
  - Segue schema SARIF 2.1.0 oficial.
  - Constrói `tool.driver.rules` com rule metadata.
  - Mapeia severidades: `info -> note`, `warning -> warning`, `error -> error`.
  - Inclui `fingerprint`, `baseline_status`, `risk_score` em `properties`.
- `junit_builder.py`:
  - `build_junit_xml(result: CheckResult) -> str`
  - Gera XML compatível com JUnit: cada finding é um `<testcase>`.
  - `error` gera `<failure message="...">`.
  - `warning` e `info` geram `<testcase>` limpos ou informativos.
- `masking.py`:
  - Mascaramento de dados sensíveis e credenciais em mensagens e sugestões antes de serializar.

### 2.3 Output layer (`src/domain/check/check_output.py`)

- `format_check_output(result: CheckResult, output_format: CheckOutputFormat) -> str`:
  - Aplica o mascaramento canônico.
  - Despacha para SARIF (JSON indentado), JSON (envelope) ou JUnit (XML).

### 2.4 Application Use Case (`src/application/use_cases/run_check.py`)

- `execute_check(config: CheckConfig, repo_path: str | None = None) -> CheckResult`:
  - 1. Inicia cronômetro e deadline (`timeout_seconds`).
  - 2. Resolve Policy Pack ativo (`--policy`). Se inválido, aborta com exit code 2.
  - 3. Determina diff base (auto-detecção ou explícito) e obtém `diff_text`.
  - 4. Executa linter regex + secret scanner + external bridges.
  - 5. Executa risk scoring local preliminar (para saber quais arquivos são high-risk se `--ia-only-high-risk`).
  - 6. Executa review de IA (se não `--no-ia`), filtrando se necessário por high-risk files.
  - 7. Executa baseline gate (se baseline configurado ou default presente). Classifica achados.
  - 8. Recalcula risk scoring com todos os achados coletados.
  - 9. Avalia threshold `--fail-on` sobre os findings contáveis. Determina `exit_code` (0 ou 1). Se timeout estourou durante a execução, marca `incomplete: True` e `exit_code = 2`.
  - 10. Retorna `CheckResult`.

### 2.5 CLI (`src/main.py`)

- Registra `@cli.command("check")` com todas as flags:
  - `--base`
  - `--format` (`sarif`, `json`, `junit`)
  - `--output`, `-o`
  - `--fail-on`
  - `--no-ia`
  - `--ia-only-high-risk`
  - `--baseline`
  - `--policy`
- Imprime artefato em `stdout` (ou escreve em `--output`).
- Redireciona logs e feedback visual/spinner para `sys.stderr`.
- Executa `sys.exit(result.exit_code)`.

### 2.6 Docs & i18n

- `docs/check-ci.md` + 4 traduções (`docs/check-ci.{pt_br,pt_pt,es_es,fr_fr}.md`).
- Atualização dos `README.*.md` com a seção `gitpr check`.
- Atualização de `action.yml` com pipeline `gitpr check`.
- Chaves em `langs/*.json`.

## 3. Fases de Execução

1. **Fase 1: Contratos e Tipos de Domínio (`src/domain/check/`)**
   - Implementar `check_types.py` e `check_config.py`.
   - Testes unitários em `tests/domain/check/test_check_types.py` e `test_check_config.py`.

2. **Fase 2: Mascaramento e Builders de Formato (`src/infrastructure/ci/` e `src/domain/check/`)**
   - Implementar `masking.py`, `sarif_builder.py`, `junit_builder.py` e `check_output.py`.
   - Testes unitários com validação de schemas em `tests/infrastructure/ci/test_sarif_builder.py`, `test_junit_builder.py` e `tests/domain/check/test_check_output.py`.

3. **Fase 3: Caso de Uso Orquestrador (`src/application/use_cases/run_check.py`)**
   - Orquestrar diff, bridges, IA, risk, baseline, timeout e thresholds.
   - Testes de use case cobrindo todas as matrizes de saída (0, 1, 2, timeout, sem IA, com baseline, sem baseline) em `tests/application/use_cases/test_run_check.py`.

4. **Fase 4: Integração CLI (`src/main.py`)**
   - Subcomando `gitpr check` com tratamento rigoroso de stderr vs stdout.
   - Testes de integração de CLI em `tests/test_check_cli.py`.

5. **Fase 5: Documentação, Action e i18n**
   - Atualizar `action.yml`.
   - Criar `docs/check-ci.*.md` em 5 idiomas.
   - Atualizar `README.*.md` e `langs/*.json`.
   - Gerar relatório de conclusão em `docs/gemini/reports/develop_natan/YYYY-MM-DD_gitpr_check_ci.md`.
