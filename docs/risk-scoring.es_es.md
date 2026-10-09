# Documentación Técnica: Puntuación de Riesgo Local (gitpr risk)

`gitpr risk` calcula una puntuación de riesgo local, determinista y explicable para cada archivo modificado y para el pull request / diff en su conjunto. Utiliza señales del repositorio y de Git — rutas críticas, ausencia de pruebas, migraciones de bases de datos, historial de errores y reversiones, tamaño del diff y hallazgos estáticos — para priorizar la atención humana en la revisión de código y orientar el foco de la IA, sin depender de la red, sin consumir cuotas de IA y sin bloquear el flujo de trabajo.

---

## 1. Visión General

La Puntuación de Riesgo Local opera en tres interfaces complementarias:

1. **Línea de Comandos Independiente (`gitpr risk`)**: Evalúa el diff del árbol de trabajo o de la rama contra una referencia base y muestra un desglose coloreado de los niveles de riesgo, puntuación y factores contribuyentes.
2. **Inspección por Archivo Específico (`gitpr risk --file <path>`)**: Aísla el cálculo de riesgo para un único archivo indicado, detallando sus señales puntuadas y la correlación de pruebas.
3. **Contexto Aditivo en la Revisión de Código (`gitpr -r` / `gitpr -f` / `gitpr --review-pr`)**: Cuando está habilitado (`GITPR_RISK_INCLUDE_IN_REVIEW=true`), adjunta automáticamente la sección `## ⚡ Risk Assessment` al archivo de informe generado e inyecta un resumen estructurado en las instrucciones del modelo de IA para centrar el análisis en archivos críticos.

### 1.1 Referencia de Comandos

```bash
gitpr risk                        # Calcula el riesgo del diff local sin confirmar (o de la rama)
gitpr risk --file src/auth.py     # Desglosa factores de riesgo de un archivo específico
gitpr risk --format json          # Retorna JSON estructurado para CI/CD y automatizaciones
gitpr risk --base main            # Evalúa el riesgo contra una referencia base explícita
gitpr risk --no-history           # Desactiva la lectura del historial de Git para ejecución ultrarrápida
```

| Opción | Descripción |
|---|---|
| **`--file <path>`** | Calcula los factores de riesgo detallados para un archivo específico |
| **`--format {text\|json}`** | Selecciona salida legible en terminal (por defecto) o JSON estructurado |
| **`--base <ref>`** | Calcula el diff contra una rama o confirmación base explícita |
| **`--no-history`** | Omite la extracción del historial de confirmaciones para optimizar tiempo de ejecución |

---

## 2. Modelo de Puntuación y Fórmula de Agregación

Todas las puntuaciones se normalizan estrictamente en el rango **`0.0 – 100.0`**.

### 2.1 Niveles de Riesgo y Umbrales (Thresholds)

| Nivel | Rango de Puntos | Badge | Significado |
|---|---|---|---|
| **LOW** | 0.0 – 24.0 | `LOW 🟢` | Cambios rutinarios con baja probabilidad de regresión |
| **MEDIUM** | 25.0 – 49.0 | `MEDIUM 🟡` | Modificaciones moderadas que requieren vigilancia normal |
| **HIGH** | 50.0 – 79.0 | `HIGH 🟠` | Cambios significativos en áreas críticas o sin pruebas |
| **CRITICAL** | 80.0 – 100.0 | `CRITICAL 🔴` | Alta exposición a incidentes, bloqueadores o impacto estructural grave |

### 2.2 Tabla de Pesos y Señales

| Señal | Puntos por Defecto | Condición / Patrón |
|---|---:|---|
| **`CRITICAL_PATH`** | +25 | Autenticación, autorización, permisos, pagos, políticas, facturación |
| **`SECURITY_SENSITIVE`** | +25 | Configuraciones de seguridad, criptografía, sesiones, gestión de tokens |
| **`DATABASE_MIGRATION`** | +20 | Cambios de esquema, migraciones de base de datos, SQL estructural |
| **`INFRASTRUCTURE`** | +20 | Flujos de CI/CD, Dockerfiles, Terraform, configuraciones Kubernetes |
| **`NO_TEST_CHANGE`** | +15 | Código ejecutable de producción modificado sin pruebas correspondientes en el diff |
| **`LARGE_DIFF`** | +5 a +15 | Volumen del diff: >= 50 líneas (+5), >= 100 líneas (+10), >= 300 líneas (+15) |
| **`HISTORICAL_BUGS`** | +10 a +20 | Archivo asociado a confirmaciones de corrección de errores en la ventana reciente (90 días / 50 commits) |
| **`HISTORICAL_REVERTS`** | +10 | Archivo afectado por confirmaciones de reversión (`revert` o `rollback`) |
| **`HIGH_CHURN`** | +15 | Frecuencia de modificación elevada (>= 20 confirmaciones en la ventana reciente) |
| **`FINDING_BLOCKER`** | +25 | Hallazgo bloqueador detectado por linter o detector de secretos |
| **`FINDING_CRITICAL`** | +15 | Hallazgo de error crítico reportado por el linter estático |
| **`FINDING_WARNING`** | +3 | Advertencia no bloqueante reportada por el linter estático |
| **`TEST_PRESENT`** | -10 | Señal mitigadora: prueba correspondiente añadida o modificada junto al código |
| **`NEW_FILE`** | 0 | Informativo: archivo recién creado sin historial previo de confirmaciones |

### 2.3 Fórmula de Agregación (50 / 30 / 20)

La puntuación agregada del pull request/diff combina las puntuaciones individuales:
- **50%**: Mayor puntuación entre los archivos individuales (`max_file_score`)
- **30%**: Media ponderada por la cantidad de líneas modificadas (`weighted_avg_lines`)
- **20%**: Puntuación agregada de evidencias críticas (`critical_evidence_score`)

### 2.4 Reglas Obligatorias de Elevación

1. **Piso High**: Si cualquier archivo individual obtiene **>= 80.0**, el nivel agregado del PR no puede ser inferior a `HIGH`.
2. **Piso Critical**: Si existe cualquier hallazgo bloqueador (`FINDING_BLOCKER`) o archivo con puntuación **>= 90.0**, el nivel del PR se clasifica automáticamente como `CRITICAL`.
3. **Saturación y Límites**: Las puntuaciones se limitan estrictamente entre `0.0` y `100.0`. Los puntos negativos se permiten únicamente para mitigaciones explícitas (`TEST_PRESENT`).

---

## 3. Configuración y Personalización

### 3.1 Configuración Global (`~/.gitpr/.env` o `gitpr config`)

| Clave | Tipo | Por Defecto | Descripción |
|---|---|---|---|
| `GITPR_RISK_INCLUDE_IN_REVIEW` | booleano | `true` | Adjunta automáticamente la sección de Evaluación de Riesgo a las revisiones de código (`-r`, `-f`, `--review-pr`). |

### 3.2 Reglas Personalizadas vía YAML (`.gitpr/skill/gitpr.risk.yml`)

Puede configurar rutas, pesos y umbrales específicos del proyecto en el archivo `.gitpr/skill/gitpr.risk.yml` o `.gitpr.risk.yml`:

```yaml
risk:
  enabled: true
  include_in_review: true
  analysis_version: "1.0"
  thresholds:
    low_max: 24
    medium_max: 49
    high_max: 79
  weights:
    critical_path: 25
    security_sensitive: 25
    database_migration: 20
    infrastructure: 20
    no_test_change: 15
    test_present: -10
  critical_paths:
    - "app/Http/Middleware/**"
    - "app/Policies/**"
    - "database/migrations/**"
    - ".github/workflows/**"
```

---

## 4. Garantías de Rendimiento y Privacidad

- **100% Offline y Determinista**: Se ejecuta completamente sobre los diffs locales y metadatos de Git. Nunca realiza llamadas de red ni envía código a servidores externos.
- **Ejecución en Milisegundos**: Concluido casi instantáneamente, ideal para hooks locales de Git y flujos de CI/CD.
- **Honestidad Epistémica**: En caso de que el historial de Git sea inaccesible (ej.: shallow clone en CI), la señal se marca como `SIGNAL_UNAVAILABLE` con aviso no bloqueante, en lugar de generar puntuaciones artificiales.

