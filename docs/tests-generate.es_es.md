# Documentación Técnica: Generación de Pruebas con IA (`gitpr tests generate`)

`gitpr tests generate` convierte un conjunto de cambios en un fichero de pruebas completo. Detecta el framework de pruebas del proyecto, calcula la ruta de destino convencional, pide a la IA una suite lista para ejecutar, valida la sintaxis con el toolchain local cuando está disponible y — solo con `--apply` — escribe el fichero en disco.

El comando nunca ejecuta las pruebas generadas y nunca hace stage ni commit de nada.

---

## 1. Visión General

```bash
# Genera pruebas para el diff completo del árbol de trabajo (dry run)
gitpr tests generate

# Genera pruebas para un fichero
gitpr tests generate --file src/auth/limiter.py

# Apunta a un hallazgo de la última revisión de código
gitpr tests generate --finding FIX-001

# Fuerza el framework en lugar de detectarlo automáticamente
gitpr tests generate --framework vitest

# Escribe el fichero generado en disco (pide confirmación)
gitpr tests generate --file src/auth/limiter.py --apply

# Ayuda contextual con el enlace a la documentación
gitpr tests generate -h
```

---

## 2. Referencia de Comandos

```text
gitpr tests generate [--file PATH] [--finding ID] [--framework NAME] [--apply] [--provider NAME]
```

| Opción | Valor por defecto | Descripción |
|---|---|---|
| `--file PATH` | — | Genera pruebas para este fichero en lugar del diff completo. |
| `--finding ID` | — | Genera pruebas para un hallazgo específico de la última revisión de código (por ejemplo `FIX-001`). |
| `--framework NAME` | Detectado automáticamente | Fuerza el framework: `pest`, `phpunit`, `jest`, `vitest`, `pytest`. |
| `--apply` | `false` | Escribe el fichero generado en disco tras el dry run y las confirmaciones. |
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Fuerza el proveedor de IA para esta ejecución (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Ayuda de Click más el enlace a esta página. |

`--file` y `--finding` son mutuamente excluyentes en la práctica: `--finding` tiene prioridad y `--file` se sobrescribe con la ruta del fichero del hallazgo.

---

## 3. Resolución del Objetivo

El comando decide qué enviar al modelo antes de generar nada:

| Invocación | Contenido del objetivo |
|---|---|
| *(sin flags de objetivo)* | Diff del árbol de trabajo: `git diff HEAD` con las smart excludes. |
| `--file PATH` | `git diff HEAD -- PATH`. Si ese diff está vacío y el fichero existe, se usa en su lugar el **contenido completo del fichero**. |
| `--finding ID` | Se carga la última revisión (`resolve_review` → `collect_candidates` → `find_candidate`), y el prompt recibe los metadatos del hallazgo, su `suggested_test` y su parche `diff_unified`. El scaffold usa el `file_path` del hallazgo. |

Si el contenido resuelto está vacío, el comando imprime `❌ No changes or target content found to generate tests.` y sale con código `1`.

Para `--finding`, la revisión debe existir y ser legible. Si falla la resolución de la candidatura, el comando imprime un aviso y recurre a un contexto mínimo que solo contiene `Finding ID: <id>`; en ese caso la prueba generada tiene muy poco con lo que trabajar.

---

## 4. Detección de Framework

La detección se ejecuta solo en la **raíz del repositorio**. La primera coincidencia gana, en este orden:

| Orden | Framework | Indicadores |
|---|---|---|
| 1 | `pest` | `pest.php`, `tests/Pest.php` o `pestphp/pest` en `composer.json` (`require` / `require-dev`). |
| 2 | `phpunit` | `phpunit.xml`, `phpunit.dist.xml`, `phpunit.xml.dist` o `phpunit/phpunit` en `composer.json`. |
| 3 | `vitest` | `vitest.config.{ts,js,mjs,mts}`, `vite.config.{ts,js}` o `vitest` en las dependencias o scripts de `package.json`. |
| 4 | `jest` | `jest.config.{js,ts,mjs,cjs,json}` o `jest` en las dependencias o scripts de `package.json`. |
| 5 | `pytest` | `pytest.ini`, `conftest.py`, `tox.ini`, `setup.cfg`, un `pyproject.toml` que mencione pytest, o `tests/test_*.py` / `tests/*_test.py`. |
| — | `unknown` | No se encontró ningún indicador. Un aviso indica que se use `--framework`. |

`--framework` se aplica primero. El valor se compara sin distinguir mayúsculas con los cinco nombres conocidos; un valor desconocido produce un aviso y recurre a la detección automática en lugar de fallar.

---

## 5. Convenciones de Ruta del Scaffold

La ruta de destino se calcula antes de llamar a la IA, y el prompt la recibe como objetivo obligatorio.

### Pest / PHPUnit

- Se elimina `app/` del inicio de la ruta.
- La suite es **Feature** cuando el primer segmento restante es `Http`, `Controllers`, `Livewire` o `Filament`; en caso contrario es **Unit**.
- El nombre del fichero recibe el sufijo `Test.php` a menos que el stem ya termine en `Test`.

| Origen | Destino |
|---|---|
| `app/Http/Controllers/Api/UserController.php` | `tests/Feature/Http/Controllers/Api/UserControllerTest.php` |
| `app/Services/UserService.php` | `tests/Unit/Services/UserServiceTest.php` |
| *(sin fichero de origen, Pest)* | `tests/Feature/GeneratedTest.php` |
| *(sin fichero de origen, PHPUnit)* | `tests/Unit/GeneratedTest.php` |

### Jest / Vitest

- Se elimina `src/` del inicio de la ruta.
- `.ts` / `.tsx` → `.test.ts`; `.vue` → `.spec.js`; cualquier otro → `.test.js`.

| Origen | Destino |
|---|---|
| `src/components/Button.vue` | `tests/components/Button.spec.js` |
| `src/utils/date.ts` | `tests/utils/date.test.ts` |
| `src/lib/api.js` | `tests/lib/api.test.js` |
| *(sin fichero de origen, Vitest)* | `tests/generated.test.ts` |
| *(sin fichero de origen, Jest)* | `tests/generated.test.js` |

### pytest

- Se elimina `src/` o `app/` del inicio de la ruta.
- Se antepone `test_` a menos que el stem ya empiece por él.

| Origen | Destino |
|---|---|
| `src/core.py` | `tests/test_core.py` |
| `app/services/auth.py` | `tests/services/test_auth.py` |
| *(sin fichero de origen)* | `tests/test_generated.py` |

### Desconocido

| Origen | Destino |
|---|---|
| `src/model.py` | `tests/test_model.py` |
| *(sin fichero de origen)* | `tests/test_generated.txt` |

El scaffold también registra `already_exists`, que controla la confirmación de sobrescritura en `--apply`.

---

## 6. Pipeline de Generación

1. **Detección de framework** — override o indicadores del repositorio (sección 4).
2. **Scaffold** — ruta de destino convencional (sección 5).
3. **Proveedor y clave** — `--provider` o `DEFAULT_AI_PROVIDER`. Sin clave, el comando añade un aviso (`No API key configured for <provider>...`), devuelve contenido vacío y sale con código `1`. `ollama` no necesita clave.
4. **Modelo** — se usa el modelo avanzado/primario (`task_complexity="advanced"`).
5. **Skill** — `get_skill_context("tests", quiet=True)` lee `.gitpr/skill/.gitpr.tests.md`; sin él, se usa una instrucción integrada equivalente a la plantilla en inglés. La skill define la persona de QA y el envelope JSON.
6. **Prompt** — framework, ruta de destino, tipo de objetivo, metadatos de fichero/hallazgo y el diff completo.
7. **Llamada a la IA** — `call_ai_model(..., action="tests")`, temperatura `0.0`, hasta **3** intentos con un intervalo de **2 s**.
8. **Parseo** — el proveedor devuelve un **dict** ya parseado; también se acepta una cadena JSON. Una cadena que no sea JSON se trata como bloque de código: se eliminan las vallas y todo el texto pasa a ser el fichero de pruebas, con el escenario `Generated from raw model output`.
9. **Validación de sintaxis** — el toolchain local comprueba el código generado cuando está disponible (sección 7).
10. **Escritura opcional** — solo cuando se pasa `--apply` (sección 8).

No hay caché de prompt ni registro en el ledger de métricas: cada ejecución llama al proveedor.

---

## 7. Validación de Sintaxis

La validación es de mejor esfuerzo y nunca bloquea la generación:

| Framework | Herramienta | Comando | Observaciones |
|---|---|---|---|
| Pest / PHPUnit | `php` | `php -l <temp>.php` | Se omite cuando PHP no está en el `PATH`. |
| Jest / Vitest | `node` | `node --check <temp>.js` | El fichero temporal siempre usa sufijo `.js`, incluso para fuentes TypeScript. Detecta errores graves de sintaxis, no errores de tipo. |
| pytest | `python` / `python3` | `python -m py_compile <temp>.py` | Se omite cuando ninguno de los binarios está en el `PATH`. |
| desconocido | — | — | Sin validación. |

Una validación fallida añade un aviso (`Syntax validation failed ... Marked as EXPERIMENTAL / low confidence.`), pero el contenido generado se sigue devolviendo y aún puede escribirse con `--apply`. El contenido generado vacío se informa como inválido.

---

## 8. Escritura con `--apply`

El comando **siempre** imprime primero el dry run: framework, ruta de destino, escenarios cubiertos y el código generado completo. La escritura solo ocurre después y solo cuando `--apply` está presente.

| Paso | Condición | Respuesta por defecto |
|---|---|---|
| Confirmación de sobrescritura | La ruta de destino ya existe (`already_exists`) | **No** |
| Confirmación de escritura | Siempre | **Sí** |

Si se rechaza cualquiera de las confirmaciones, el comando imprime un mensaje de cancelación y vuelve sin escribir. Cuando se acepta, crea los directorios padre y escribe el fichero en UTF-8 con `errors='replace'`, relativo al **directorio de trabajo actual**.

**No** ejecuta `git add`, no hace commit y no ejecuta las pruebas generadas.

---

## 9. Ejemplo de Salida

```text
$ gitpr tests generate --file src/auth/limiter.py

🧪 Analyzing diff and generating test file...

📋 Target Framework: PYTEST
📂 Target Test Path: tests/test_limiter.py

🧪 Covered Scenarios:
  • Happy path: request under the limit is allowed
  • Boundary: request exactly at the limit
  • Regression: counter expiration resets the window

--- Generated Test Code ---
def test_request_under_limit_is_allowed():
    ...
---

ℹ️ Dry-run mode. Run with --apply to write to disk.
```

Con `--apply`, el mismo informe va seguido de las confirmaciones y de `✅ Test file successfully created at '<path>'!`.

---

## 10. Errores y Códigos de Salida

| Situación | Comportamiento | Código de salida |
|---|---|---|
| Pruebas generadas (dry run o aplicadas) | Informe y, con `--apply`, el fichero | `0` |
| Sin diff / sin contenido de fichero | `❌ No changes or target content found to generate tests.` | `1` |
| Sin clave de API | Aviso más `❌ Test generation failed.` (contenido vacío) | `1` |
| El modelo no devolvió nada útil | Aviso más `❌ Test generation failed.` | `1` |
| Falló la validación de sintaxis | Solo aviso; el contenido se sigue mostrando/aplicando | `0` |
| El usuario rechaza una confirmación | Mensaje de cancelación | `0` |
| Uso inválido de la CLI | Error de uso de Click | `2` |

---

## 11. Limitaciones

- **Detección solo en la raíz.** Los indicadores de framework se buscan en la raíz del repositorio. Los monorepos con configuraciones por paquete no están soportados; usa `--framework`.
- **Gana la primera coincidencia.** Un repositorio con indicadores PHP y JS se detecta como PHP, porque PHP se comprueba primero.
- **La prueba generada no se ejecuta.** Solo se comprueba la sintaxis, y solo cuando el binario correspondiente está instalado. Una prueba sintácticamente válida puede fallar en tiempo de ejecución.
- **La validación de TypeScript es superficial.** `node --check` analiza el fichero como JavaScript; los errores de tipo y muchas construcciones específicas de TS no se validan.
- **Un framework desconocido produce un fichero `.txt`.** Sin framework no hay convención ni comprobación de sintaxis, y el destino es `tests/test_generated.txt` (o `tests/test_<stem><ext>`).
- **`--file` sin diff envía el fichero entero.** Para un fichero grande sin cambios, esto puede consumir una parte importante de la ventana de contexto; el comando no hace chunking.
- **`--finding` depende de la última revisión.** Lee el artefacto de revisión producido por `gitpr -r` / `gitpr -f` a través de la maquinaria de `fix`. Sin revisión, el contexto se degrada al ID del hallazgo.
- **Las rutas son relativas al directorio actual.** Ejecutar desde un subdirectorio escribe la prueba relativa a ese subdirectorio, no a la raíz del repositorio.
- **Sin caché, sin ledger.** Las ejecuciones repetidas vuelven a llamar al proveedor, y la ejecución no queda registrada en `gitpr metrics`.
- **Sin integración con git.** El nuevo fichero queda sin rastrear; `git add` y el commit son responsabilidad tuya.
- **El comando `/tests` del chat es independiente.** No delega en este motor; usa `gitpr tests generate` para la generación estructurada.
- **El texto generado sigue el idioma de la skill**, no el idioma de interfaz de `--lang`.

---

## 12. Documentación Relacionada

- [Revisión de Código con IA](code-review-ia.es_es.md) — de dónde vienen los hallazgos consumidos por `--finding`.
- [Comando Fix](fix-command.es_es.md) — los hallazgos de revisión y la maquinaria de parches compartida con `--finding`.
- [Plantillas de Skill](skill-template.es_es.md) — cómo se resuelve, descarga y sobrescribe `.gitpr.tests.md`.
- [Proveedores de IA](providers-ia.es_es.md) — proveedores, modelos, reintentos y configuración de claves.
- [Guía del Revisor](explain-pr.es_es.md) — el otro comando de generación con IA.
- [Verificación Unificada de CI](check-ci.es_es.md) — qué validaciones se ejecutan en CI en su lugar.
