# Documentación Técnica: Code Review con IA (--review / --fullreview / --input)

El CLI de GitPR ofrece cuatro modos de code review usando inteligencia artificial, cada uno adecuado a un momento diferente del ciclo de desarrollo. Todos los modos se integran automáticamente con el **Linter Estático** (`.gitpr.linter.yml`), que añade alertas de regex en la parte superior del informe.

---

## 1. Modos de Review

### 1.1 Review Local — `gitpr -r` (o `--review`)

Analiza únicamente los cambios **no commiteados** en el working tree (`git diff HEAD`).

```bash
gitpr -r
```

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | `git diff HEAD` (cambios locales) |
| **Cuándo usar** | Antes de commitear, para validar la calidad del código |
| **Output** | `{branch}_{datetime}_PR_REVIEW.txt` |
| **Ideal para** | Revisión rápida, validación pre-commit |

### 1.2 Full Review — `gitpr -f` (o `--fullreview`)

Compara **todos** los cambios de la rama actual contra la rama principal remota (`origin/main`).

```bash
gitpr -f
```

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | Diff completo contra `origin/main` (hace `git fetch` antes) |
| **Cuándo usar** | Antes de abrir un Pull Request |
| **Output** | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| **Ideal para** | Revisión profunda de toda la feature branch |

### 1.3 Auditoría de Archivo — `gitpr -r -i <arquivo>` (o `--review --input`)

Analiza un **archivo entero**, ignorando el git diff. Útil para código heredado o refactorizaciones.

```bash
gitpr -r -i src/legacy/parser.py
gitpr -f -i src/core.py
```

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | Contenido íntegro del archivo en el disco |
| **Cuándo usar** | Refactorización de código heredado, auditoría de archivos críticos |
| **Output** | `{branch}_{datetime}_FILE_REVIEW.txt` |
| **Requiere** | `--review` (`-r`) o `--fullreview` (`-f`) |

### 1.4 Review de Pull Request Remoto — `gitpr review-pr <number>`

Revisa un pull request que **ya está abierto en la forge**, obteniendo su diff directamente de la API. La rama no tiene que ser local: nada se descarga ni se trae a tu árbol de trabajo. Es el modo para revisar el pull request de otra persona.

```bash
gitpr review-pr 123
gitpr review-pr 123 --provider deepseek
gitpr review-pr 123 --post-comment
```

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | El diff servido por la API de la forge para ese pull request |
| **Cuándo usarlo** | Revisar un pull request al que fuiste invitado, sin hacer checkout de la rama |
| **Output** | `{branch}_{datetime}_PR_REVIEW.txt`, nombrado por la rama de origen del pull request |
| **Publicación** | Nada, salvo que se indique `--post-comment`; la revisión se publica entonces como comentario |
| **Requiere** | Una forge configurada por `gitpr --init` que sirva un diff unificado — Azure DevOps no sirve |
| **Ideal para** | Revisión de código de contribuciones de terceros, y para repositorios que nunca clonas |

Ejecuta el mismo motor, la misma skill y la misma caché que `gitpr -r`, así que su informe se lee como un review local del mismo diff. Consulta la [documentación de Review de Pull Request Remoto](review-pr.md) para el contrato completo — los rechazos que no cuestan tokens, el filtro de smart excludes, el ámbito de caché y el pie del comentario.

---

## 2. Integración con el Linter Estático

En todos los modos de review, el **Linter Estático** se ejecuta automáticamente. Si hay violaciones de las reglas definidas en el `.gitpr.linter.yml`, las alertas aparecen en la parte superior del informe, antes del análisis de la IA:

```
## 🚨 Alertas de Análisis Estático Local (Reglas YAML)
- 🚨 Uso de console.log detectado en app.js (Línea 42)
- ⚠️ Uso de localhost detectado en config.php (Línea 15)

---

## 🤖 Code Review de la IA
...
```


En un review de pull request remoto (`gitpr review-pr`), solo se ejecutan las reglas YAML: el puente del linter externo ejecuta binarios contra archivos **en disco**, que en ese modo serían lo que tienes en checkout y no el pull request en revisión. Revisar la revisión equivocada y publicar las alertas como comentario es peor que no ejecutarlas.

---

## 3. Personalización mediante Skills

El comportamiento de la IA durante el review puede personalizarse a través de los archivos de plantilla:

| Archivo | Modo | Función |
| --- | --- | --- |
| `.gitpr.review.md` | `--review` / `--fullreview` | Define el foco del análisis (ej.: SOLID, Clean Code, seguridad) |
| `.gitpr.filereview.md` | `--input` (+ review) | Define reglas de cohesión y acoplamiento para archivo completo |

Descarga las plantillas con `gitpr -s` y edítalas según las reglas de negocio de tu equipo.

---

## 4. Selección de Proveedor de IA

```bash
gitpr -r -p deepseek        # Review local con DeepSeek
gitpr -f -p gemini          # Full review con Gemini
gitpr -r -i arquivo.py -p deepseek  # Auditoría con DeepSeek
gitpr review-pr 123 --provider deepseek  # Review remoto con DeepSeek
```

El `-p` / `--provider` del grupo raíz no lo heredan los subcomandos, así que `gitpr review-pr` escribe la misma opción como `--provider`.

---

## 5. Variables de Entorno

| Variable | Modo | Valor por defecto |
| --- | --- | --- |
| `OUTPUT_FILE_NAME_REVIEW` | `-r`, `review-pr` | `{branch}_{datetime}_PR_REVIEW.txt` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `-f` | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `-i` | `{branch}_{datetime}_FILE_REVIEW.txt` |

> **Nota:** Consulta también la [documentación del Linter](linter-regras-customizadas.md) para crear reglas de validación estática.
