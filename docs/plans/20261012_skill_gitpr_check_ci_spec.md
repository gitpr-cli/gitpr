# SPEC — GitPR `check` Unificado para CI (SARIF/JSON/JUnit)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: criar `gitpr check` como comando unificado de CI que executa linter, bridges externos, secret scanning, review de IA (opcional), risk scoring e baseline, produzindo saída estruturada em SARIF/JSON/JUnit e códigos de saída previsíveis para pipelines.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler `core.py` e o pipeline atual de review/linter/risk/baseline para confirmar o modelo real de finding, severidade, fingerprint, baseline e risk score já implementados ou especificados.
2. Confirmar se baseline e supressões auditáveis já foram implementados (spec anterior). Se sim, `gitpr check` deve consumi-los. Se não, esta feature deve implementar baseline mínimo ou documentar dependência explícita antes de prosseguir.
3. Confirmar se risk scoring e Policy Packs já foram implementados ou especificados. Se sim, `gitpr check` deve integrar risk score e política ativa. Se não, documentar dependência explícita.
4. Verificar se o projeto já tem alguma estrutura de `gitpr check`, action.yml, SARIF ou CI output. Reaproveitar o que existir; não duplicar.
5. Confirmar o formato real de findings internos (severidade, categoria, arquivo, linha, fonte, mensagem, sugestão) para mapear corretamente para SARIF/JSON/JUnit.
6. Confirmar o mecanismo de cache e telemetria local. O check deve ser reproduzível, não enviar código/histórico para serviços externos e não incluir conteúdo sensível em logs.
7. Confirmar a interface real do provider de IA. O review de IA no `gitpr check` deve ser opcional e configurável, respeitando custo/latência de CI.

Não prosseguir sem completar os passos 1–4. Se baseline/risk scoring não estiverem implementados, esta spec deve documentar dependência explícita ou implementar versão mínima compatível.

## 1. Escopo da feature

- **Objetivo:** permitir que uma equipe rode `gitpr check` em CI/pipeline como um único comando que consolida linter, bridges externos, secret scanning, review de IA (opcional), risk scoring e baseline, produzindo artefatos estruturados e códigos de saída previsíveis.
- **Comandos/flags novos:**
  - `gitpr check` — executa o pipeline unificado.
  - `gitpr check --base <ref>` — define base de comparação.
  - `gitpr check --format {sarif|json|junit}` — seleciona formato de saída.
  - `gitpr check --output <path>` — escreve artefato em arquivo.
  - `gitpr check --fail-on {info|warning|minor|major|critical|blocker}` — define severidade mínima que causa falha.
  - `gitpr check --no-ia` — desabilita review de IA (modo rápido/barato).
  - `gitpr check --ia-only-high-risk` — roda IA apenas em arquivos de alto risco, se risk scoring existir.
  - `gitpr check --baseline <path>` — usa baseline específico.
  - `gitpr check --policy <name>@<version>` — ativa Policy Pack específico.
- **Comportamento padrão:** sem baseline, todos os findings são tratados como `new`. Com baseline, apenas `new` com severidade >= threshold causa falha.
- **Códigos de saída obrigatórios:**
  - `0` — sucesso (nenhum finding bloqueante);
  - `1` — falha por findings >= threshold;
  - `2` — erro de execução/configuração.
- **Fora de escopo nesta fase:** dashboard web, sincronização cloud, aprovação administrativa, assinatura criptográfica obrigatória, execução paralela de múltiplos linters, marketplace de regras.
- **Compatibilidade:** a introdução de `gitpr check` não deve alterar o comportamento dos comandos já existentes (`gitpr -r`, `gitpr pr`, `gitpr risk`, `gitpr baseline`). Deve reaproveitar os mesmos motores, apenas orquestrá-los em uma interface única.

## 2. Árvore de arquivos a criar/alterar

```text
src/domain/check/
├── check_types.py                # NOVO — dataclasses/enums
├── check_config.py               # NOVO — parsing de configuração/flags
├── check_runner.py               # NOVO — orquestra pipeline unificado
└── check_output.py               # NOVO — formata SARIF/JSON/JUnit

src/application/use_cases/
└── run_check.py                  # NOVO — orquestra linter, bridges, IA, risk, baseline

src/infrastructure/ci/
├── sarif_builder.py              # NOVO
├── junit_builder.py              # NOVO
└── github_checks_adapter.py      # NOVO (opcional, para GitHub Checks API)

core.py                            # ALTERAR — registrar `gitpr check` e integrar baseline/risk/policy
main.py                            # ALTERAR — CLI e formatos de saída
config.schema.yml                  # ALTERAR — schema de check/thresholds

src/ui/                            # ALTERAR somente se houver dashboard/TUI compatível

tests/domain/check/
├── test_check_config.py
├── test_check_output.py
└── test_check_types.py
tests/application/use_cases/
└── test_run_check.py
tests/infrastructure/ci/
├── test_sarif_builder.py
├── test_junit_builder.py
└── test_github_checks_adapter.py
tests/integration/
└── test_check_effect_on_pipeline.py
```

A skill DEVE adaptar caminhos à estrutura real. Não duplicar parser de findings ou mecanismo de cache se já existirem.

## 3. Contrato de dados obrigatório

```python
# src/domain/check/check_types.py
from dataclasses import dataclass, field
from enum import Enum


class CheckSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"
    BLOCKER = "blocker"


class CheckOutputFormat(str, Enum):
    SARIF = "sarif"
    JSON = "json"
    JUNIT = "junit"


@dataclass
class CheckFinding:
    fingerprint: str
    rule_id: str
    category: str
    file_path: str
    line_start: int
    line_end: int
    severity: CheckSeverity
    source: str                    # ai | linter | external | semgrep | gitleaks | bandit
    message: str
    suggestion: str | None
    baseline_status: str | None    # new | existing | resolved | ignored | accepted_debt
    risk_score: float | None
    provenance: dict = field(default_factory=dict)


@dataclass
class CheckResult:
    findings: list[CheckFinding]
    exit_code: int                 # 0 | 1 | 2
    fail_on: CheckSeverity
    output_format: CheckOutputFormat
    output_path: str | None
    analysis_version: str
    warnings: list[str]
```

```python
# src/domain/check/check_config.py
@dataclass
class CheckConfig:
    base_ref: str | None
    output_format: CheckOutputFormat
    output_path: str | None
    fail_on: CheckSeverity
    no_ia: bool
    ia_only_high_risk: bool
    baseline_path: str | None
    policy_name: str | None
    policy_version: str | None
```

```python
# src/application/use_cases/run_check.py
def run_check(
    config: CheckConfig,
    repo_path: str,
    ai_provider=None,               # None se no_ia=True
    scm_provider=None,               # None se não houver publicação
) -> CheckResult:
    ...
```

## 4. Pipeline unificado — ordem obrigatória

1. **Carregar configuração local** (`.gitpr/config.yml`, YAML, variáveis de ambiente) e resolver Policy Pack ativo, se houver.
2. **Obter diff normalizado** (local ou remoto via `--review-pr`), reaproveitando a mesma função já usada pelo restante do produto.
3. **Executar linter regex + bridges externos** (Checkstyle, ESLint, PHPCS, Stylelint, Semgrep, Gitleaks, Bandit — conforme habilitados).
4. **Executar secret scanning** (preset regex + Gitleaks, se disponível).
5. **Executar review de IA** (opcional, se `no_ia=false`), respeitando `ia_only_high_risk` se risk scoring existir.
6. **Executar risk scoring local** (se habilitado), calculando score por arquivo e agregado.
7. **Carregar baseline** (se existir) e classificar findings como new/existing/resolved/ignored/accepted_debt.
8. **Aplicar threshold de falha** (`--fail-on`): apenas findings `new` com severidade >= threshold causam exit_code 1.
9. **Montar saída estruturada** no formato selecionado (SARIF/JSON/JUnit).
10. **Escrever artefato** em arquivo, se `--output` for informado.
11. **Retornar exit_code** previsível para pipeline.

## 5. Mapeamento de severidade para SARIF/JUnit

| Severidade interna | SARIF level | JUnit severity |
|---|---|---|
| info | note | info |
| warning | warning | warning |
| minor | warning | warning |
| major | error | failure |
| critical | error | failure |
| blocker | error | failure |

Regras:

1. SARIF usa `level`: `note`, `warning`, `error`.
2. JUnit usa `failure`/`error`/`skipped` — mapear `blocker`/`critical`/`major` para `failure`.
3. Mapeamento deve ser configurável via override, seguindo o padrão de severidades já existente no projeto.
4. Nenhum finding deve ser descartado silenciosamente — todos aparecem na saída estruturada.

## 6. SARIF — requisitos obrigatórios

SARIF (Static Analysis Results Interchange Format) deve seguir o schema oficial (SARIF 2.1.0):

```json
{
  "version": "2.1.0",
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "GitPR",
          "version": "<gitpr_version>",
          "informationUri": "https://github.com/<user>/gitpr"
        }
      },
      "results": [
        {
          "ruleId": "SEC-AWS-ACCESS-KEY",
          "level": "error",
          "message": {"text": "Possível AWS Access Key ID hardcoded."},
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {"uri": "app/Services/UserService.php"},
                "region": {"startLine": 42, "endLine": 42}
              }
            }
          ],
          "properties": {
            "fingerprint": "sha256:...",
            "category": "security",
            "source": "linter",
            "baseline_status": "new",
            "risk_score": 85.0
          }
        }
      ]
    }
  ]
}
```

Requisitos:

1. `ruleId`, `message.text`, `locations[].physicalLocation` são obrigatórios por finding.
2. `fingerprint`, `baseline_status`, `risk_score` devem ir em `properties` (extensão SARIF).
3. Nenhum conteúdo de segredo deve aparecer em texto pleno — mascarar antes de qualquer output.
4. SARIF deve ser consumível por GitHub Code Scanning, GitLab SAST e outras ferramentas compatíveis.

## 7. JUnit — requisitos obrigatórios

JUnit XML deve seguir o schema padrão de testes:

```xml
<testsuites>
  <testsuite name="GitPR" tests="N" failures="F" errors="E">
    <testcase name="SEC-AWS-ACCESS-KEY" classname="app/Services/UserService.php">
      <failure message="Possível AWS Access Key ID hardcoded">...</failure>
    </testcase>
  </testsuite>
</testsuites>
```

Regras:

1. Cada finding vira um `testcase`.
2. Severidade `blocker`/`critical`/`major` → `failure`.
3. `warning`/`minor` → `warning` (se suportado) ou omitir.
4. `info` → omitir ou incluir como `system-out`.

## 8. Integração com baseline, risk e Policy Packs

1. **Baseline:** se existir, apenas findings `new` com severidade >= threshold causam falha. `existing`/`resolved`/`ignored`/`accepted_debt` não bloqueiam por padrão.
2. **Risk scoring:** se habilitado, score por arquivo e agregado deve ser incluído no contexto e no SARIF (`properties.risk_score`). Threshold de falha pode considerar risk score se configurado.
3. **Policy Packs:** política ativa pode fornecer caminhos críticos, pesos, thresholds e regras de baseline. `gitpr check` deve respeitar a política efetiva.

## 9. Configuração

```yaml
check:
  enabled: true
  default_output_format: "sarif"
  default_fail_on: "critical"
  no_ia_by_default: false
  ia_only_high_risk: false
  baseline_path: ".gitpr/baseline.json"
  policy_path: ".gitpr/policy.lock.yml"
  timeout_seconds: 120
```

Configuração local de overrides:

```yaml
# .gitpr/check.overrides.yml
overrides:
  fail_on: "major"
  ia_only_high_risk: true
```

A syntax de `add`, `remove` ou substituição deve ser alinhada ao formato de configuração já existente.

## 10. CLI e UX

### `gitpr check --help`

Deve listar todas as flags e exemplos.

### `gitpr check --format sarif --output gitpr-results.sarif`

Deve:

1. executar pipeline;
2. gerar SARIF;
3. escrever arquivo;
4. retornar exit_code.

### `gitpr check --format junit --output gitpr-results.xml`

Deve gerar JUnit XML.

### `gitpr check --fail-on warning`

Deve falhar se houver qualquer finding >= warning.

### `gitpr check --no-ia`

Deve desabilitar review de IA (modo rápido/barato).

### `gitpr check --ia-only-high-risk`

Deve rodar IA apenas em arquivos de alto risco (se risk scoring existir).

## 11. Testes obrigatórios — critérios de aceite

1. **Código de saída:** `0` sem finding bloqueante; `1` com finding >= threshold; `2` com erro de execução/configuração.
2. **SARIF válido:** saída deve validar contra schema SARIF 2.1.0; campos obrigatórios presentes por finding.
3. **JUnit válido:** saída deve validar contra schema JUnit XML; severidade mapeada corretamente.
4. **Baseline:** apenas findings `new` com severidade >= threshold causam falha; existing/resolved/ignored/accepted_debt não bloqueiam por padrão.
5. **Risk scoring:** score incluído no SARIF/JUnit quando habilitado; IA não é chamada para calcular score.
6. **Policy Pack:** política ativa altera caminhos críticos, pesos e thresholds conforme declarado.
7. **Privacidade/offline:** `--no-ia` não abre rede nem envia código para IA; secret scanning via regex é puramente local.
8. **Não-regressão:** comandos existentes (`gitpr -r`, `gitpr pr`, `gitpr risk`, `gitpr baseline`) mantêm comportamento anterior.
9. **Timeout:** execução que excede timeout retorna exit_code 2 com warning, sem travar pipeline.
10. **Formato inválido:** `--format` inválido deve listar opções válidas com mensagem clara, não lançar exceção genérica.
11. **Integração GitHub Checks:** se implementado, adapter deve publicar check no PR via API, respeitando permissões e sem expor segredos.
12. **Integração SARIF upload:** se implementado, SARIF deve ser consumível por GitHub Code Scanning/GitLab SAST sem conflito de schema.

Critério de feature completa: `gitpr check` funciona em pipeline CI com SARIF/JSON/JUnit, códigos de saída previsíveis, baseline/risk/policy integrados, e sem qualquer risco de execução de comando não sanitizado.

## 12. Ordem de execução recomendada

1. Confirmar modelo de finding, severidade, baseline, risk e policy já implementados/especificados.
2. Implementar contratos de `check_types.py` e `check_config.py`.
3. Implementar `sarif_builder.py` e `junit_builder.py` com fixtures de saída real.
4. Implementar `run_check.py` conectando linter, bridges, IA (opcional), risk, baseline.
5. Implementar `check_output.py` para SARIF/JSON/JUnit.
6. Registrar `gitpr check` em `core.py`/CLI com todas as flags.
7. Implementar integração GitHub Checks/SARIF upload, se priorizado.
8. Atualizar `config.schema.yml` e documentação (README/CLI help).
9. Validar manualmente em pipeline CI real (GitHub Actions/GitLab CI) com SARIF/JSON/JUnit.
10. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. Não começar por GitHub Checks/SARIF upload; validar primeiro que `gitpr check` local com SARIF/JSON/JUnit resolve o problema de CI.

## 13. Riscos e dependências

- **Dependência:** modelo de finding normalizado; sem ele, SARIF/JSON/JUnit não podem ser gerados de forma confiável.
- **Dependência:** baseline e supressões auditáveis; sem eles, threshold de falha não pode distinguir new/existing.
- **Dependência:** risk scoring; sem ele, `ia_only_high_risk` não pode ser implementado.
- **Dependência:** Policy Packs; sem eles, caminhos críticos/pesos/thresholds não podem ser configurados por organização.
- **Risco:** SARIF inválido pode quebrar GitHub Code Scanning. Validar schema antes de publicar.
- **Risco:** timeout de ferramenta externa pode travar pipeline. Timeout obrigatório e falha controlada.
- **Risco:** segredo em texto pleno em SARIF/JUnit pode vazar em logs. Mascaramento obrigatório.
- **Risco:** threshold muito baixo pode gerar ruído excessivo. Default conservador (`critical`) e configurável.

## 14. Fora de escopo

- Dashboard web ou agregação entre repositórios.
- Telemetria remota de resultados.
- Sincronização cloud de organização.
- Aprovação administrativa de thresholds.
- SSO/RBAC.
- Marketplace de regras.
- Execução de scripts/hooks/código Python dentro de regras.
- Skills arbitrárias descobertas dinamicamente.
- Enforcement bloqueante de Policy Packs (apenas informativo nesta versão).

## 15. Encaixe estratégico

`gitpr check` unificado é a fundação do CI/CD e do futuro plano Team: traduz linter, bridges, IA, risk e baseline em um único comando com saída estruturada e códigos de saída previsíveis. Nesta primeira versão deve permanecer no tier Free/Community, porque o valor imediato é adoção em pipelines individuais e open source. A monetização futura deve estar na colaboração: thresholds organizacionais, dashboards agregados, auditoria e suporte — não no bloqueio do uso local de `gitpr check`.
