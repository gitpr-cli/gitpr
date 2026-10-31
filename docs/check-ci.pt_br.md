# Documentação Técnica: Check Unificado de CI (`gitpr check`)

O comando `gitpr check` oferece um ponto de entrada único projetado para pipelines de Integração Contínua (CI) como GitHub Actions, GitLab CI e Jenkins. Ele consolida análise estática, bridges SAST externos, varredura de segredos, review de código por IA opcional, cálculo de risco e baseline em um único comando que produz artefatos padronizados (**SARIF 2.1.0**, **JSON** ou **JUnit XML**) com códigos de saída determinísticos.

---

## 1. Visão Geral

```bash
# Executa check unificado e emite SARIF diretamente na saída padrão (stdout)
gitpr check

# Gera arquivo SARIF estruturado para o GitHub Code Scanning
gitpr check --format sarif --output gitpr-results.sarif

# Check rápido de custo zero sem chamadas à IA
gitpr check --no-ia

# Define threshold mais estrito (falha em warnings ou erros)
gitpr check --fail-on warning

# Restringe a análise da IA apenas aos arquivos classificados como alto risco
gitpr check --ia-only-high-risk

# Avalia os achados contra um baseline específico
gitpr check --baseline .gitpr/baseline.json

# Aplica um Policy Pack específico
gitpr check --policy security-strict@1.0.0
```

---

## 2. Opções de CLI e Variáveis de Ambiente

A configuração respeita a ordem de precedência: **Flags da CLI > Variáveis de Ambiente > Padrões**.

| Flag | Variável de Ambiente | Padrão | Descrição |
|---|---|---|---|
| `--base <ref>` | `GITPR_CHECK_BASE` | Auto-detectado | Referência git para comparação do diff (detecta `GITHUB_BASE_REF`, `origin/main` ou `HEAD`). |
| `--format {sarif\|json\|junit}` | `GITPR_CHECK_FORMAT` | `sarif` | Formato do artefato gerado. |
| `-o`, `--output <path>` | `GITPR_CHECK_OUTPUT` | `None` (stdout) | Caminho do arquivo de saída. Se omitido, o artefato é emitido no `stdout`. |
| `--fail-on <severity>` | `GITPR_CHECK_FAIL_ON` | `error` | Severidade mínima que causa código de saída 1 (`info`, `warning`, `error`, `minor`, `major`, `critical`, `blocker`). |
| `--no-ia` | `GITPR_CHECK_NO_IA` | `false` | Desabilita review de IA (executa linter, segredos, risco e baseline locais). |
| `--ia-only-high-risk` | `GITPR_CHECK_IA_ONLY_HIGH_RISK` | `false` | Aciona a IA apenas para arquivos com nível de risco alto ou crítico. |
| `--baseline <path>` | `GITPR_CHECK_BASELINE_PATH` | `.gitpr/baseline.json` | Caminho para o manifesto de baseline JSON. |
| `--policy <name>@<ver>` | `GITPR_CHECK_POLICY` | Lockfile ativo | Impõe um Policy Pack específico para a execução. |
| — | `GITPR_CHECK_TIMEOUT_SECONDS` | `300` | Limite global de tempo de execução em segundos. |

---

## 3. Códigos de Saída (Exit Codes)

Os pipelines dependem de códigos de saída previsíveis:

| Código | Status | Significado |
|---|---|---|
| **`0`** | Sucesso | Nenhum achado contável atingiu ou superou o threshold de severidade `--fail-on`. |
| **`1`** | Falha | Um ou mais achados contáveis atingiram ou superaram o threshold `--fail-on`. |
| **`2`** | Erro | Execução interrompida por erro de configuração, política inválida, baseline corrompido, falha do provedor de IA ou tempo limite excedido. |

> Os outros fluxos que exigem o baseline (`-l`, `-r`, `-f`, `-i`, `risk`, `review-pr`) saem com **1** diante de um baseline inutilizável. Veja [Baseline: exit codes por fluxo](baseline-suppressions.pt_br.md#baseline-inutilizável-exit-codes-por-fluxo).

---

## 4. Ordem de Execução do Pipeline

1. **Resolução de Política**: Carrega política ativa ou solicitada via `--policy`.
2. **Extração do Diff**: Obtém diff normalizado contra a base ou HEAD com exclusões inteligentes.
3. **Linter Estático e Segredos**: Executa regras regex, scanner de segredos e bridges SAST (Semgrep, Gitleaks, Bandit).
4. **Scoring de Risco Preliminar**: Identifica métricas de risco por arquivo e agregadas do PR.
5. **Review de IA (Opcional)**: Aciona o provedor de IA se configurado (degrada graciosamente se faltar chave).
6. **Classificação contra Baseline**: Compara achados com o baseline (status: `new`, `existing`, `ignored`, `accepted_debt`, `resolved`). Sem baseline, todos os achados são contáveis.
7. **Avaliação do Threshold**: Compara achados contáveis contra `--fail-on`.
8. **Mascaramento e Geração do Artefato**: Sanitiza dados sensíveis e serializa em SARIF, JSON ou JUnit XML.

---

## 5. Formatos de Artefatos

### SARIF 2.1.0 (`--format sarif`)
- Compatível nativamente com **GitHub Code Scanning**, **GitLab SAST** e Azure DevOps.
- Preenche `tool.driver.rules` dinamicamente a partir dos achados detectados.
- Mapeia severidades (`error` $\to$ `error`, `warning` $\to$ `warning`, `info` $\to$ `note`).
- Insere `fingerprint`, `baseline_status` e `risk_score` em `properties`.

### Envelope JSON (`--format json`)
JSON estruturado contendo status, resumo, métricas de risco e achados detalhados com mascaramento.

### JUnit XML (`--format junit`)
Relatório padrão XML suportado por Jenkins, GitLab CI test summary e Azure Pipelines.
- Achados bloqueantes geram tags `<failure>`.
- Achados informativos são registrados em tags `<system-out>`.
