# Survey — `gitpr check`: Unified CI Command

> Levantamento da sessão de grill que antecedeu a implementação da spec
> [`docs/plans/20261012_skill_gitpr_check_ci_spec.md`](../plans/20261012_skill_gitpr_check_ci_spec.md).
> Decisão arquitetural: [ADR-013](../plans/ADR-013-check-ci-command.md).
> Glossário: [glossary-check-ci.md](../plans/glossary-check-ci.md).
> Plano de execução: [20261012_check_ci_plansfacts.md](../plans/develop_natan/20261012_check_ci_plansfacts.md).

## 1. Contexto da tarefa

Permitir que pipelines de CI (GitHub Actions, GitLab CI, etc.) executem o GitPR através de um único comando unificado (`gitpr check`). O comando orquestra:
1. Resolução de configuração e política ativa (`--policy`);
2. Normalização do diff (`--base` explícito ou auto-detectado via `GITHUB_BASE_REF` / `origin/main` / `HEAD`);
3. Linter regex + bridges externos (Semgrep, Gitleaks, Bandit, etc.) e secret scanning local;
4. Review de IA opcional (`--no-ia`, ou `--ia-only-high-risk`);
5. Risk scoring local agregado e por arquivo;
6. Baseline de achados e supressões auditáveis (classificação em `new`, `existing`, `ignored`, `accepted_debt`, `resolved`);
7. Aplicação do threshold de falha (`--fail-on`);
8. Emissão de artefato mascarado e estruturado em SARIF 2.1.0, JSON ou JUnit XML, com códigos de saída previsíveis (0, 1, 2).

## 2. Decisões do Grill (ADR-013)

| # | Pergunta / Decisão | Resolução |
|---|---|---|
| D1 | Escala de severidade | **3 níveis** (`error|warning|info`) alinhados a `NormalizedFinding`. `minor→warning`, `major|critical|blocker→error` como aliases aceitos por `--fail-on`. |
| D2 | Configuração | **Variáveis `GITPR_CHECK_*` + flags CLI** (`flags > env > defaults`). Sem `config.schema.yml` ou `check.overrides.yml`. |
| D3 | Sem baseline | `baseline_status = null`. Todos os achados contam para `--fail-on`. Baseline com erro de checksum ou incompatível ⇒ falha com exit code 2. |
| D4 | Risk scoring | **Informativo**. Presente em `properties.risk_score` (SARIF) e `risk` (JSON). Não altera exit code por padrão. |
| D5 | Resiliência da IA | Ligada por padrão; se faltar chave, avisa e pula. Falha de rede/provedor no meio da execução aborta com exit code 2. |
| D6 | Timeout global | `GITPR_CHECK_TIMEOUT_SECONDS` (default 300s). Exceder o deadline gera artefato com `incomplete: true` e exit code 2. |
| D7 | Mascaramento de segredos | Gargalo único na camada de saída (`check_output`), mascarando tokens e dados sensíveis antes de serializar SARIF/JSON/JUnit. |
| D8 | Destino do stdout/stderr | Sem `--output`, stdout recebe **apenas o artefato** (JSON, SARIF ou XML puro). Logs, progresso e warnings vão estritamente para stderr. |
| D9 | GitHub Checks API | Fora da v1. Integração no GitHub Actions via `action.yml` chamando `gitpr check` + `actions/upload-artifact` ou `github/codeql-action/upload-sarif`. |
| D10 | Auto-detecção de diff base | Se `--base` não for informado, usa `GITHUB_BASE_REF` (se presente), ou `origin/main` (se existir remote), ou fallback para `HEAD`. |
| D11 | Escopo de docs e i18n | **Entrega completa**: documentação em 5 idiomas (`docs/check-ci.*.md`), `README.*.md`, `langs/*.json` e atualização do `action.yml`. |
| D12 | Metadados SARIF de regras | `tool.driver.rules` montado dinamicamente a partir dos achados reportados, garantindo conformidade com GitHub Code Scanning. |
| D13 | Envelope JSON estruturado | Raiz com `version`, `gitpr_version`, `status`, `exit_code`, `incomplete`, `summary`, `risk` e `findings`. |
| D14 | Validação de Policy | Política informada via `--policy` inexistente ou inválida aborta o run imediatamente com exit code 2. |

## 3. Fatos levantados no código

1. **`NormalizedFinding` já existe e é canônico:** Vive em `src/domain/finding/finding_types.py` com severidades `error`, `warning`, `info`.
2. **`baseline_gate.py` e `create_baseline.py` já colhem linter e IA:** `collect_linter_findings()` executa regex linter + segredos + bridges. `ai_findings_from_record()` extrai achados de IA.
3. **`execute_calculate_risk()` em `calculate_risk.py`:** Já calcula score agregado e scores por arquivo, recebendo `NormalizedFinding` e associando-os aos arquivos do diff.
4. **`action.yml` já existe na raiz:** Atualmente roda `gitpr --linter` e `gitpr --fullreview`. Será atualizado para rodar `gitpr check`.
