# Documentación Técnica: Verificación Unificada de CI (`gitpr check`)

El comando `gitpr check` proporciona un punto de entrada único diseñado para canales de Integración Continua (CI) como GitHub Actions, GitLab CI y Jenkins. Consolida análisis estático, puentes SAST externos, detección de secretos, revisión de código con IA opcional, evaluación de riesgo y baseline en un solo comando que genera artefactos estandarizados (**SARIF 2.1.0**, **JSON** o **JUnit XML**) y códigos de salida deterministas.

---

## 1. Visión General

```bash
# Ejecuta verificación unificada y emite SARIF en stdout
gitpr check

# Genera archivo SARIF para GitHub Code Scanning
gitpr check --format sarif --output gitpr-results.sarif

# Verificación rápida sin llamadas a IA
gitpr check --no-ia

# Falla en advertencias o errores
gitpr check --fail-on warning

# Restringe la IA solo a archivos de alto riesgo
gitpr check --ia-only-high-risk

# Evalúa contra un baseline específico
gitpr check --baseline .gitpr/baseline.json

# Aplica un Policy Pack específico
gitpr check --policy security-strict@1.0.0
```

---

## 2. Opciones de CLI y Variables de Entorno

| Flag | Variable de Entorno | Valor por Defecto | Descripción |
|---|---|---|---|
| `--base <ref>` | `GITPR_CHECK_BASE` | Auto-detectado | Referencia git para comparación (`GITHUB_BASE_REF`, `origin/main` o `HEAD`). |
| `--format {sarif\|json\|junit}` | `GITPR_CHECK_FORMAT` | `sarif` | Formato del artefacto emitido. |
| `-o`, `--output <path>` | `GITPR_CHECK_OUTPUT` | `None` (stdout) | Ruta para escribir el artefacto. Si se omite, se emite en `stdout`. |
| `--fail-on <severity>` | `GITPR_CHECK_FAIL_ON` | `error` | Severidad mínima que causa código de salida 1. |
| `--no-ia` | `GITPR_CHECK_NO_IA` | `false` | Desactiva revisión de IA. |
| `--ia-only-high-risk` | `GITPR_CHECK_IA_ONLY_HIGH_RISK` | `false` | Ejecuta IA solo para archivos con riesgo alto o crítico. |
| `--baseline <path>` | `GITPR_CHECK_BASELINE_PATH` | `.gitpr/baseline.json` | Ruta al manifiesto de baseline. |
| `--policy <name>@<ver>` | `GITPR_CHECK_POLICY` | Lockfile activo | Aplica un Policy Pack específico. |
| — | `GITPR_CHECK_TIMEOUT_SECONDS` | `300` | Tiempo límite global en segundos. |

---

## 3. Códigos de Salida

| Código | Estado | Significado |
|---|---|---|
| **`0`** | Éxito | Ningún hallazgo contable alcanzó el umbral `--fail-on`. |
| **`1`** | Fallo | Uno o más hallazgos contables alcanzaron el umbral `--fail-on`. |
| **`2`** | Error | Ejecución abortada por error de configuración, política no encontrada, baseline corrupto o tiempo excedido. |

> Los demás flujos que exigen el baseline (`-l`, `-r`, `-f`, `-i`, `risk`, `review-pr`) salen con **1** ante un baseline inutilizable. Ver [Baseline: exit codes por flujo](baseline-suppressions.es_es.md#baseline-inutilizable-exit-codes-por-flujo).

---

## 4. Orden de Ejecución del Pipeline

1. **Resolución de Política**: Carga la política activa o requerida mediante `--policy`. Falla con código 2 si no es válida.
2. **Extracción del Diff**: Obtiene el diff normalizado contra la rama base o HEAD con exclusiones inteligentes.
3. **Linter Estático y Secretos**: Ejecuta reglas regex, escáner de secretos y puentes SAST (Semgrep, Gitleaks, Bandit).
4. **Scoring de Riesgo Preliminar**: Identifica métricas de riesgo por archivo y agregadas del PR.
5. **Revisión de IA (Opcional)**: Ejecuta el proveedor de IA si está configurado (degrada de forma transparente si falta la clave).
6. **Clasificación contra Baseline**: Compara los hallazgos con el baseline (estado: `new`, `existing`, `ignored`, `accepted_debt`, `resolved`). Sin baseline, todos los hallazgos son contabilizables.
7. **Evaluación del Umbral**: Compara los hallazgos contabilizables frente a `--fail-on`.
8. **Enmascaramiento y Generación del Artefacto**: Sanitiza datos confidenciales y serializa en SARIF, JSON o JUnit XML.

---

## 5. Formatos de Artefactos

### SARIF 2.1.0 (`--format sarif`)
- Compatible de forma nativa con **GitHub Code Scanning**, **GitLab SAST** y Azure DevOps.
- Rellena `tool.driver.rules` dinámicamente a partir de los hallazgos detectados.
- Mapea niveles (`error` $	o$ `error`, `warning` $	o$ `warning`, `info` $	o$ `note`).
- Inserta `fingerprint`, `baseline_status` y `risk_score` en `properties`.

### Envoltorio JSON (`--format json`)
JSON estructurado que contiene estado, resumen, métricas de riesgo y hallazgos detallados con enmascaramiento.

### JUnit XML (`--format junit`)
Informe XML estándar compatible con Jenkins, resumen de pruebas de GitLab CI y Azure Pipelines.
- Los hallazgos bloqueantes generan etiquetas `<failure>`.
- Los hallazgos informativos se registran en etiquetas `<system-out>`.

---

## 6. Integración con GitHub Actions

Utilice la composite action oficial en `.github/workflows/ci.yml`:

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
      security-events: write # Requerido para subir SARIF a GitHub Code Scanning
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Ejecutar GitPR Check
        uses: natanfiuza/gitpr@main
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }}
          format: sarif
          output: gitpr-results.sarif
          fail-on: error

      - name: Subir SARIF a GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: gitpr-results.sarif
```

---

## 7. Guía de Migración: Actualización desde el Flujo de Trabajo Heredado de Action

Antes de la introducción de `gitpr check`, la composite action oficial (`action.yml`) ejecutaba dos comandos secuenciales discretos:
1. `gitpr --linter` (fallaba de inmediato ante errores estáticos).
2. `gitpr --fullreview` (generaba en disco un archivo de texto no clasificado `*_PR_FULLREVIEW.txt`, que opcionalmente se concatenaba en `$GITHUB_STEP_SUMMARY`).

Este cambio estructural introdujo una ruptura de contrato al actualizar a versiones modernas de GitPR:
- **Ausencia de `*_PR_FULLREVIEW.txt` en disco**: El comando `gitpr check` no genera este archivo de texto. Los flujos de trabajo heredados que dependían de `cat *_PR_FULLREVIEW.txt >> $GITHUB_STEP_SUMMARY` fallarán o producirán resúmenes vacíos.
- **SARIF y Code Scanning Nativo**: La salida estándar ahora es SARIF 2.1.0 (`gitpr-results.sarif`), JSON o JUnit XML, integrándose directamente en la pestaña **Security > Code scanning alerts** de GitHub mediante `github/codeql-action/upload-sarif@v3`.
- **Clave de API Opcional y CI a Coste Cero**: El parámetro `api-key` ya no es obligatorio (`required: false`). Los flujos de trabajo pueden ejecutarse sin coste u offline con `no-ia: "true"`.
- **Códigos de Salida Deterministas y Supresión por Baseline**: En lugar de fallos incondicionales ante cualquier hallazgo, los códigos de salida están estrictamente controlados por `--fail-on` (por defecto `error`). Los hallazgos registrados en `.gitpr/baseline.json` se suprimen y no interrumpen la canalización.

### Comparativa Contractual: Antes vs. Después

| Característica | Flujo Heredado (`v0.0.12` – `v0.0.36`) | Verificación Unificada Moderna (`v0.0.37+`) |
|---|---|---|
| **Comando Subyacente** | `gitpr --linter` y después `gitpr --fullreview` | `gitpr check` |
| **Artefacto Generado** | `*_PR_FULLREVIEW.txt` (archivo de texto plano) | `gitpr-results.sarif` (SARIF 2.1.0), JSON o JUnit XML |
| **Integración con GitHub UI** | Volcado manual en `$GITHUB_STEP_SUMMARY` | Anotaciones inline nativas en el PR y alertas en **Code Scanning** |
| **Obligatoriedad de Clave IA** | Requerida (`required: true`) | Opcional (`required: false`); soporta `no-ia: "true"` |
| **Criterio de Fallo** | Fallo del linter en error; revisión irrestricta | Configurable mediante `--fail-on` (`info`, `warning`, `error`) |
| **Soporte de Baseline** | Sin supresiones en CI | Supresiones completas mediante `.gitpr/baseline.json` |
| **Códigos de Salida** | No unificados por subetapa | Normalizados: `0` (limpio), `1` (umbral superado), `2` (error de ejecución) |

### Ejemplos de Flujo de Trabajo: Antes y Después

#### ❌ Antes (Flujo de Trabajo Heredado)

```yaml
name: CI Code Review (Heredado)

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

      # Invocación heredada de composite action
      - name: Ejecutar GitPR Review
        uses: natanfiuza/gitpr@v0.0.36
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }} # era obligatorio

      # Paso dependiente que falla en versiones modernas:
      - name: Publicar Resumen del Paso
        if: always()
        run: |
          REVIEW_FILE=$(ls *_PR_FULLREVIEW.txt 2>/dev/null | head -n 1)
          if [ -f "$REVIEW_FILE" ]; then
            cat "$REVIEW_FILE" >> $GITHUB_STEP_SUMMARY
          fi
```

#### ✅ Después (Verificación Unificada Moderna)

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
      security-events: write # Requerido para subir SARIF a Code Scanning
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Ejecutar GitPR Check Unificado
        uses: natanfiuza/gitpr@main
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }} # opcional si no-ia es true
          format: sarif
          output: gitpr-results.sarif
          fail-on: error

      - name: Subir SARIF a GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: gitpr-results.sarif
```

### Preservar Revisiones de Texto Independientes

Si su flujo de trabajo requiere estrictamente el archivo `*_PR_FULLREVIEW.txt` como texto plano (por ejemplo, para archivado histórico o herramientas heredadas), ejecute `gitpr --fullreview` como un paso independiente en lugar de utilizar `action.yml`:

```yaml
      - name: Ejecutar Full Review Independiente (Salida Heredada)
        env:
          DEFAULT_AI_PROVIDER: gemini
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          pip install gitpr-cli
          gitpr --fullreview
```
