# Documentação Técnica: Verificação Unificada de CI (`gitpr check`)

O comando `gitpr check` disponibiliza um ponto de entrada único concebido para pipelines de Integração Contínua (CI) como GitHub Actions, GitLab CI e Jenkins. Consolida análise estática, bridges SAST externos, deteção de segredos, revisão de código por IA opcional, avaliação de risco e baseline num único comando que gera artefactos normalizados (**SARIF 2.1.0**, **JSON** ou **JUnit XML**) com códigos de saída determinísticos.

---

## 1. Visão Geral

```bash
# Executa verificação unificada e emite SARIF diretamente no stdout
gitpr check

# Gera ficheiro SARIF estruturado para o GitHub Code Scanning
gitpr check --format sarif --output gitpr-results.sarif

# Verificação rápida de custo zero sem chamadas à IA
gitpr check --no-ia

# Define patamar mais restrito (falha em warnings ou erros)
gitpr check --fail-on warning

# Restringe a análise de IA apenas aos ficheiros de alto risco
gitpr check --ia-only-high-risk

# Avalia achados contra um baseline específico
gitpr check --baseline .gitpr/baseline.json

# Aplica um Policy Pack específico
gitpr check --policy security-strict@1.0.0
```

---

## 2. Opções da CLI e Variáveis de Ambiente

| Flag | Variável de Ambiente | Predefinição | Descrição |
|---|---|---|---|
| `--base <ref>` | `GITPR_CHECK_BASE` | Auto-detetado | Referência git para comparação do diff (`GITHUB_BASE_REF`, `origin/main` ou `HEAD`). |
| `--format {sarif\|json\|junit}` | `GITPR_CHECK_FORMAT` | `sarif` | Formato do artefacto gerado. |
| `-o`, `--output <path>` | `GITPR_CHECK_OUTPUT` | `None` (stdout) | Caminho do ficheiro de saída. Se omitido, emite no `stdout`. |
| `--fail-on <severity>` | `GITPR_CHECK_FAIL_ON` | `error` | Gravidade mínima que desencadeia código de saída 1. |
| `--no-ia` | `GITPR_CHECK_NO_IA` | `false` | Desativa revisão de IA (executa apenas linter, segredos, risco e baseline locais). |
| `--ia-only-high-risk` | `GITPR_CHECK_IA_ONLY_HIGH_RISK` | `false` | Executa IA apenas para ficheiros de risco alto ou crítico. |
| `--baseline <path>` | `GITPR_CHECK_BASELINE_PATH` | `.gitpr/baseline.json` | Caminho para o manifesto JSON de baseline. |
| `--policy <name>@<ver>` | `GITPR_CHECK_POLICY` | Lockfile ativo | Impõe um Policy Pack específico. |
| — | `GITPR_CHECK_TIMEOUT_SECONDS` | `300` | Prazo limite global de execução em segundos. |

---

## 3. Códigos de Saída (Exit Codes)

| Código | Estado | Significado |
|---|---|---|
| **`0`** | Sucesso | Nenhum achado contabilizável atingiu o patamar `--fail-on`. |
| **`1`** | Falha | Um ou mais achados contabilizáveis atingiram o patamar `--fail-on`. |
| **`2`** | Erro | Execução interrompida por erro de configuração, política inválida, baseline corrompido ou tempo limite excedido. |
