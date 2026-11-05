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

> Os outros fluxos que exigem o baseline (`-l`, `-r`, `-f`, `-i`, `risk`, `review-pr`) saem com **1** perante um baseline inutilizável. Ver [Baseline: exit codes por fluxo](baseline-suppressions.pt_pt.md#baseline-inutilizável-exit-codes-por-fluxo).

---

## 4. Ordem de Execução do Pipeline

1. **Resolução de Política**: Carrega a política ativa ou solicitada via `--policy`. Falha com código 2 se inválida.
2. **Extração do Diff**: Obtém diff normalizado contra a base ou HEAD com exclusões inteligentes.
3. **Linter Estático e Segredos**: Executa regras regex, scanner de segredos e bridges SAST (Semgrep, Gitleaks, Bandit).
4. **Scoring de Risco Preliminar**: Identifica métricas de risco por ficheiro e agregadas do PR.
5. **Revisão de IA (Opcional)**: Executa o fornecedor de IA se configurado (degrada graciosamente se faltar chave).
6. **Classificação contra Baseline**: Compara achados com o baseline (estado: `new`, `existing`, `ignored`, `accepted_debt`, `resolved`). Sem baseline, todos os achados são contabilizáveis.
7. **Avaliação do Patamar**: Compara achados contabilizáveis contra `--fail-on`.
8. **Mascaramento e Geração do Artefacto**: Sanitiza dados confidenciais e serializa em SARIF, JSON ou JUnit XML.

---

## 5. Formatos de Artefactos

### SARIF 2.1.0 (`--format sarif`)
- Compatível nativamente com **GitHub Code Scanning**, **GitLab SAST** e Azure DevOps.
- Preenche `tool.driver.rules` dinamicamente a partir dos achados detetados.
- Mapeia gravidades (`error` $	o$ `error`, `warning` $	o$ `warning`, `info` $	o$ `note`).
- Insere `fingerprint`, `baseline_status` e `risk_score` em `properties`.

### Envelope JSON (`--format json`)
JSON estruturado contendo estado, resumo, métricas de risco e achados detalhados com mascaramento.

### JUnit XML (`--format junit`)
Relatório padrão XML suportado por Jenkins, GitLab CI test summary e Azure Pipelines.
- Achados bloqueantes geram tags `<failure>`.
- Achados informativos são registados em tags `<system-out>`.

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

## 7. Guia de Migração: A Atualizar do Fluxo de Trabalho Legado da Action

Antes da introdução do `gitpr check`, a action composta oficial (`action.yml`) executava dois comandos sequenciais discretos:
1. `gitpr --linter` (falhava imediatamente perante erros estáticos).
2. `gitpr --fullreview` (gerava em disco um ficheiro de texto não classificado `*_PR_FULLREVIEW.txt`, opcionalmente concatenado no `$GITHUB_STEP_SUMMARY`).

Esta alteração estrutural introduziu uma quebra de contrato ao atualizar para versões modernas do GitPR:
- **Ausência de `*_PR_FULLREVIEW.txt` em disco**: O comando `gitpr check` não cria este ficheiro de texto. Fluxos de trabalho legados que dependiam de `cat *_PR_FULLREVIEW.txt >> $GITHUB_STEP_SUMMARY` falharão ou produzirão resumos vazios.
- **SARIF e Code Scanning Nativo**: A saída padrão é agora SARIF 2.1.0 (`gitpr-results.sarif`), JSON ou JUnit XML, integrando-se diretamente no separador **Security > Code scanning alerts** do GitHub via `github/codeql-action/upload-sarif@v3`.
- **Chave de API Opcional e CI a Custo Zero**: O parâmetro `api-key` deixou de ser obrigatório (`required: false`). Os fluxos de trabalho podem ser executados sem custos ou offline com `no-ia: "true"`.
- **Códigos de Saída Determinísticos e Supressão por Baseline**: Em vez de falhas incondicionais em qualquer achado, os códigos de saída são estritamente controlados por `--fail-on` (predefinição `error`). Achados catalogados no `.gitpr/baseline.json` são suprimidos e não quebram o pipeline.

### Comparativo Contratual: Antes vs. Depois

| Característica | Fluxo de Trabalho Legado (`v0.0.12` – `v0.0.36`) | Verificação Unificada Moderna (`v0.0.37+`) |
|---|---|---|
| **Comando Subjacente** | `gitpr --linter` e depois `gitpr --fullreview` | `gitpr check` |
| **Artefacto Gerado** | `*_PR_FULLREVIEW.txt` (ficheiro de texto simples) | `gitpr-results.sarif` (SARIF 2.1.0), JSON ou JUnit XML |
| **Integração com GitHub UI** | Concatenação manual no `$GITHUB_STEP_SUMMARY` | Anotações inline nativas no PR e alertas em **Code Scanning** |
| **Exigência de Chave de IA** | Obrigatória (`required: true`) | Opcional (`required: false`); suporta `no-ia: "true"` |
| **Critério de Falha** | Falha do linter em erro; revisão irrestrita | Configurável via `--fail-on` (`info`, `warning`, `error`) |
| **Suporte a Baseline** | Sem suporte a supressões no CI | Supressões completas via `.gitpr/baseline.json` |
| **Códigos de Saída** | Não padronizados por subetapa | Normalizados: `0` (limpo), `1` (patamar violado), `2` (erro de execução) |

### Exemplos de Fluxo de Trabalho: Antes e Depois

#### ❌ Antes (Fluxo de Trabalho Legado)

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

#### ✅ Depois (Verificação Unificada Moderna)

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

### Preservar Revisões de Texto Isoladas

Caso o seu fluxo exija estritamente o ficheiro `*_PR_FULLREVIEW.txt` como texto simples (ex.: para arquivo ou parsers legados personalizados), execute o comando `gitpr --fullreview` numa etapa avulsa, em vez de recorrer ao `action.yml`:

```yaml
      - name: Executar Full Review Isolado (Saída Legada)
        env:
          DEFAULT_AI_PROVIDER: gemini
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          pip install gitpr-cli
          gitpr --fullreview
```
