# **Guía Práctica: Expresiones Regulares de Alto Rendimiento en GitPR**

El Linter Estático de GitPR procesa el `git diff` línea por línea utilizando el motor nativo `re` de Python (NFA - *Nondeterministic Finite Automaton*). Los motores NFA son potentes, pero tienen un punto ciego peligroso: el **Retroceso Catastrófico (Catastrophic Backtracking)**.

Esta guía explica cómo escribir reglas para `.gitpr.linter.yml` garantizando que el tiempo de validación del commit se mantenga en el rango de los milisegundos.

---

## **1. ¿Qué es el Retroceso Catastrófico?**

Ocurre cuando una Regex utiliza **cuantificadores codiciosos** `(*, +)` cerca unos de otros o anidados, y la cadena probada casi coincide (*match*), pero falla al final.

Para intentar encontrar una combinación válida, el motor "retrocede" (backtracks) y prueba todas las permutaciones posibles. El tiempo de procesamiento crece de forma exponencial ($O(2^n)$).

**El Ejemplo Clásico (El Código de la Muerte):**

* **Regex:** `(a+)+$`  
* **Texto:** `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaX`  
* *Resultado:* La terminal se bloquea. El motor intentará más de 700 millones de combinaciones antes de darse cuenta de que la `X` al final impide la coincidencia.

---

## **2. Reglas de Oro para un Alto Rendimiento**

### **Regla 1: "Falla Rápido" usando Anclas**

La mejor forma de ahorrar CPU es hacer que la Regex desista de la línea lo más rápido posible.

Si la palabra prohibida debe ser una palabra aislada, utilice el límite de palabra `\b` (Word Boundary). Esto evita que la Regex analise el interior de cadenas largas innecesariamente.

* ❌ **Lento:** `dd\(` *(Busca los caracteres 'd', 'd', '(' en todas las posiciones de la línea)*  
* ✅ **Rápido:** `\bdd\(` *(Solo inicia la búsqueda al principio de una palabra. Si la línea es `add()`, desiste en el primer carácter)*

### **Regla 2: Reemplace `.*` por Clases Negadas `[^...]`**

El `.*` (cualquier cosa, cero o más veces) es el mayor causador de backtracking. Es codicioso: va hasta el final de la línea y luego comienza a retroceder de derecha a izquierda buscando el resto de su regla.

Si está buscando algo dentro de comillas o paréntesis, especifique exactamente dónde debe detenerse.

* ❌ **Lento:** `console\.log\(.*\)` *(Va hasta el final de la línea antes de retroceder para encontrar el paréntesis de cierre)*  
* ✅ **Rápido:** `console\.log\([^)]*\)` *(La clase `[^)]` significa: "Captura todo, siempre que NO sea un paréntesis de cierre". Se detiene en el milisegundo exacto en que encuentra el límite)*

### **Regra 3: Evite Cuantificadores Opcionales Anidados**

Nunca coloque un cuantificador opcional (`*` o `?`) justo después de otro cuantificador opcional, o dentro de un grupo que también se repita.

* ❌ **Lento:** `(localhost\s*)*`  
* ✅ **Rápido:** `localhost(\s+localhost)*`

### **Regla 4: Desactive la Captura en Grupos `(?:...)`**

Por defecto, cuando utiliza paréntesis `(get|post)` como en nuestra regla de rutas, Python guarda esa información en memoria para su extracción posterior. GitPR no necesita extraer la palabra, solo necesita saber si existe (`True` o `False`).

Utilice grupos de no captura `(?:...)` para ahorrar asignación de memoria.

* ❌ **Lento:** `Route::(get|post)\(`  
* ✅ **Rápido:** `Route::(?:get|post)\(`

---

## **3. Comparativa Práctica para `.gitpr.linter.yml`**

Vea cómo transformar reglas ingenuas en reglas blindadas:

| Objetivo | ❌ Regex Ingenua (Peligrosa) | ✅ Regex de Alto Rendimiento (GitPR) | ¿Por qué es mejor? |
| :---- | :---- | :---- | :---- |
| Bloquear IP Fija | `[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+` | `\b(?:\d{1,3}\.){3}\d{1,3}\b` | Usa `\b` y `(?:)` para no asignar memoria extra y limita el tamaño a 3 dígitos. |
| Buscar TODOs | `.*TODO.*` | `\bTODO\b:` | Elimina el `.*` inútil. El ancla `\b` resuelve la búsqueda en toda la línea. |
| Rutas (Verbos) | `Route::.*\('get.*` | `Route::[A-Za-z]+(\s*['"](?:get\|post)` | Usa clases de caracteres y alternancia rápida sin captura. |

**Consejo de Prevención:** Como GitPR procesa líneas en archivos minificados (ej: `app.min.js`), una sola línea puede contener miles de caracteres. Aplicar la **Regla 2 (Clases Negadas)** es su mayor garantía contra bloqueos de terminal.

---
