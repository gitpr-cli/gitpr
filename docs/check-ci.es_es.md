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

