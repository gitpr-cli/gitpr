# Documentación Técnica: Optimización de Tokens en Archivos de Contexto (.md)

Los archivos `.gitpr.pr.md` e `.gitpr.review.md` actúan como el "cerebro" de las peticiones de GitPR. Se inyectan como `system_instruction` en las API de IA.

El objetivo de esta documentación es establecer estándares estrictos para mantener el consumo por debajo de **150 tokens por archivo**, garantizando respuestas casi instantáneas (bajo TTFT - *Time to First Token*) y eliminando alucinaciones.

---

## 1. Principios de Prompting Eficiente (Anti-Patrones)

Para ahorrar tokens, evita los siguientes errores comunes:

* **No enseñes lo que la IA ya sabe:** Los modelos fundacionales fueron entrenados con miles de libros de ingeniería y bases de código.
  * ❌ *Malo (Gasta tokens):* "SOLID es un conjunto de 5 principios. La S significa Single Responsibility..."
  * ✅ *Bueno (Económico):* "Evalúa la arquitectura usando principios SOLID y Clean Code."
* **Elimina la "Basura Sintáctica" (Cortesía):** La IA no tiene sentimientos.
  * ❌ *Malo:* "Por favor, ¿podrías generar una descripción...?"
  * ✅ *Bueno:* "Genera la descripción."
* **Cuidado con el formateo Markdown excesivo en el Prompt:** Símbolos como `###` y listas anidadas en tu archivo `.md` consumen tokens individuales. Usa **MAYÚSCULAS (CAPS LOCK)** para definir la jerarquía en el prompt; la IA comprende la semántica perfectamente.

---

## 2. Patrón Optimizado: .gitpr.pr.md (Enfoque en Entrega)

Este archivo es utilizado por los comandos `--commit` y `--pr` (predeterminado). Su objetivo es dictar cómo la IA debe leer el Diff y traducirlo en valor de negocio e historial de Git.

**Plantilla Base (Copiar y Pegar):**

```plaintext
CONTEXTO DEL PROYECTO
[Inserta 1 o 2 frases sobre el proyecto. Ej.: ERP Financiero Laravel/Vue. Alta seguridad y auditoría son críticas.]

ROL
Ingeniero de Software Senior. Resume el git diff enfocándote en el impacto para el negocio y la claridad técnica.

REGLAS DE COMMIT
1. ESTANDAR: Usa Conventional Commits (feat, fix, refactor, chore).
2. VERBO: Usa imperativo en español (ej.: "feat: añade filtro", NUNCA "añadiendo").
3. TAMANO: Máx 72 caracteres, sin punto final.

REGLAS DE PULL REQUEST
1. FOCO: Explica el "porqué" del cambio, no traduzcas el código.
2. ESTRUCTURA EXIGIDA (Markdown):
- 🎯 Resumen
- 🛠️ Cambios Técnicos (lista)
- ⚠️ Impacto/Avisos (Destaca envs, dependencias o base de datos)

FORMATO DE SALIDA
CERO saludos o elogios.
```

**¿Por qué es eficiente?** Agrupamos las reglas lógicas por bloques (Commits e PR). El uso de "CERO saludos" como instrucción negativa final es la técnica más económica para evitar que la IA gaste 20 tokens diciendo *"Aquí está la descripción de tu Pull Request:"* antes de enviar el JSON.

---

## 3. Patrón Optimizado: .gitpr.review.md (Enfoque en Calidad)

Este archivo se activa exclusivamente con `--review` y `--fullreview`. Aquí, la IA ignora el historial de Git y actúa como un inspector de calidad de código (*Quality Gate*).

**Plantilla Base (Copiar y Pegar):**

```plaintext
CONTEXTO DEL PROYECTO
[Inserta 1 o 2 frases sobre el proyecto. Ej.: ERP Financiero Laravel/Vue. Alta seguridad y auditoría son críticas.]

ROL
Arquitecto de Software Senior. Revisa el git diff enfocado en mantenibilidad y prevención de errores (bugs).

REGLAS DE REVISION
1. DOCBLOCK: Toda nueva función/método DEBE tener documentación estándar (DocBlock/Docstring). Señala la ausencia como error crítico.
2. ARQUITECTURA: Señala violaciones de SOLID, consultas N+1, números mágicos y acoplamiento. No definas los conceptos, solo muestra el error.
3. SEGURIDAD: Alerta sobre SQLi, XSS o datos sensibles en logs.

ESTRUCTURA DE SALIDA EXIGIDA (Markdown)
- RESUMEN DEL CAMBIO (1 frase)
- PUNTOS CRITICOS (Bugs, seguridad o ausencia de DocBlock. Omitir si no hay)
- SUGERENCIAS DE MEJORA (Refactorizaciones. Usa bloques de código para Antes/Después)
- VEREDICTO (Aprobado / Aprobado con Reservas / Rechazado)

FORMATO DE SALIDA
CERO saludos o elogios. Directo al grano técnico.
```

**¿Por qué es eficiente?** La regla *Omitir si no hay* en la sección de Puntos Críticos ahorra decenas de tokens de salida. En lugar de que la IA genere un bloque inútil diciendo *"Puntos Críticos: No se encontraron puntos críticos en este análisis"*, simplemente omite la sección y ahorra tiempo de lectura en la terminal.

---
