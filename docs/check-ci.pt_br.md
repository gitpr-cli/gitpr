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

---

## 6. Integração com GitHub Actions

Utilize a action composta oficial em `.github/workflows/ci.yml`:

```yaml
name: CI Check

on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write # Necessário para upload de SARIF no GitHub Code Scanning
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Executar GitPR Check
        uses: natanfiuza/gitpr@main
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }}
          format: sarif
          output: gitpr-results.sarif
          fail-on: error

      - name: Enviar SARIF para o GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: gitpr-results.sarif
```

---

## 7. Guia de Migração: Atualizando do Workflow Legado do Action

Antes da introdução do `gitpr check`, a action composta oficial (`action.yml`) executava dois comandos sequenciais discretos:
1. `gitpr --linter` (falhava imediatamente diante de erros estáticos).
2. `gitpr --fullreview` (gerava em disco um arquivo de texto não classificado `*_PR_FULLREVIEW.txt`, opcionalmente concatenado no `$GITHUB_STEP_SUMMARY`).

Essa mudança estrutural introduziu uma quebra de contrato ao atualizar para versões modernas do GitPR:
- **Ausência de `*_PR_FULLREVIEW.txt` em disco**: O comando `gitpr check` não cria esse arquivo de texto. Workflows legados que dependiam de `cat *_PR_FULLREVIEW.txt >> $GITHUB_STEP_SUMMARY` falharão ou produzirão resumos vazios.
- **SARIF e Code Scanning Nativo**: A saída padrão agora é SARIF 2.1.0 (`gitpr-results.sarif`), JSON ou JUnit XML, integrando-se diretamente à aba **Security > Code scanning alerts** do GitHub via `github/codeql-action/upload-sarif@v3`.
- **Chave de API Opcional e CI Custo Zero**: O input `api-key` deixou de ser obrigatório (`required: false`). Workflows podem rodar sem custos ou offline com `no-ia: "true"`.
- **Códigos de Saída Determinísticos e Supressão por Baseline**: Em vez de falhas incondicionais em qualquer achado, os códigos de saída são estritamente controlados por `--fail-on` (padrão `error`). Achados catalogados no `.gitpr/baseline.json` são suprimidos e não quebram o pipeline.

### Comparativo Contratual: Antes vs. Depois

| Característica | Workflow Legado (`v0.0.12` – `v0.0.36`) | Check Unificado Moderno (`v0.0.37+`) |
|---|---|---|
| **Comando Subjacente** | `gitpr --linter` e depois `gitpr --fullreview` | `gitpr check` |
| **Artefato Gerado** | `*_PR_FULLREVIEW.txt` (arquivo de texto puro) | `gitpr-results.sarif` (SARIF 2.1.0), JSON ou JUnit XML |
| **Integração com GitHub UI** | Concatenação manual no `$GITHUB_STEP_SUMMARY` | Anotações inline nativas no PR e alertas em **Code Scanning** |
| **Exigência de Chave de IA** | Obrigatória (`required: true`) | Opcional (`required: false`); suporta `no-ia: "true"` |
| **Critério de Falha** | Falha do linter em erro; review irrestrita | Configurável via `--fail-on` (`info`, `warning`, `error`) |
| **Suporte a Baseline** | Sem suporte a supressões no CI | Supressões completas via `.gitpr/baseline.json` |
| **Códigos de Saída** | Não padronizados por subetapa | Normalizados: `0` (limpo), `1` (threshold violado), `2` (erro de execução) |

### Exemplos de Workflow: Antes e Depois

#### ❌ Antes (Workflow Legado)

```yaml
name: CI Code Review (Legado)

on:
  pull_request:
    branches: [main]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # Invocação legada da composite action
      - name: Executar GitPR Review
        uses: natanfiuza/gitpr@v0.0.36
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }} # era obrigatório

      # Etapa dependente que quebra nas versões modernas:
      - name: Publicar Resumo do Step
        if: always()
        run: |
          REVIEW_FILE=$(ls *_PR_FULLREVIEW.txt 2>/dev/null | head -n 1)
          if [ -f "$REVIEW_FILE" ]; then
            cat "$REVIEW_FILE" >> $GITHUB_STEP_SUMMARY
          fi
```

#### ✅ Depois (Check Unificado Moderno)

```yaml
name: CI Check (Moderno)

on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write # Obrigatório para upload de SARIF no Code Scanning
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Executar GitPR Check Unificado
        uses: natanfiuza/gitpr@main
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }} # opcional quando no-ia for true
          format: sarif
          output: gitpr-results.sarif
          fail-on: error

      - name: Enviar SARIF para o GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: gitpr-results.sarif
```

### Preservando Reviews Textuais Avulsas

Caso seu fluxo exija estritamente o arquivo `*_PR_FULLREVIEW.txt` como texto puro (ex.: para arquivamento ou parsers personalizados legados), execute o comando `gitpr --fullreview` em uma etapa avulsa, em vez de usar `action.yml`:

```yaml
      - name: Executar Full Review Isolado (Saída Legada)
        env:
          DEFAULT_AI_PROVIDER: gemini
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          pip install gitpr-cli
          gitpr --fullreview
```
