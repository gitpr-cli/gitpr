# Entendiendo el Chat Interactivo de GitPR

El Chat Interactivo de GitPR es un **asistente de pair-programming con IA** que se ejecuta directamente en tu terminal. Ve tus cambios no confirmados (`git diff`) y mantiene una conversación contextual, ayudándote a entender, refactorizar, probar y optimizar tu código.

## Iniciar el Chat

```bash
gitpr -ch
# o
gitpr --chat
```

Para sobrescribir el idioma de la interfaz en una sola sesión:

```bash
gitpr --lang en_us -ch
gitpr --lang es_es -ch
```

## Atajos de Teclado

| Tecla | Acción | Descripción |
|-------|--------|-------------|
| **F1** | Ayuda | Abre un modal mostrando todos los atajos y comandos slash |
| **F2** | Actualizar Diff | Actualiza el contexto de la IA con los últimos cambios de código |
| **F5** | Auto-Patch | Extrae bloques de código de la última respuesta de la IA y los guarda |
| **F6** | Exportar | Guarda toda la conversación en un archivo Markdown estructurado |
| **Esc** | Salir | Cierra la aplicación de chat |

## Comandos Slash

Escribe `/` en el campo de entrada para ver una lista desplegable de comandos disponibles. Sigue escribiendo para filtrar.

| Comando | Descripción |
|---------|-------------|
| `/explain` | Explica el diff actual línea por línea |
| `/tests` | Genera pruebas unitarias para las funciones modificadas |
| `/optimize` | Analiza la complejidad ciclomática y sugiere mejoras de rendimiento |
| `/clear` | Limpia la conversación e inicia una nueva sesión de chat para el diff actual |

Puedes escribir un comando parcial (ej.: `/ex`) y presionar **Enter** — se auto-completa al comando completo.

## Memoria y Sesiones

El chat persiste automáticamente tu conversación e historial de diffs en disco:

- **Ubicación:** `~/.gitpr/cache/chat/<UUID>/`
- **Clave de sesión:** Un UUID único de 15 caracteres (formato `XXXX-XXXXX-XXXX`) generado por rama y repositorio
- **Persistencia:** Volver a la misma rama reabre la sesión existente con todo el historial de conversación
- **Seguimiento de diffs:** Cada cambio de código se registra. La IA sabe cuándo has modificado archivos y actualiza su contexto

## Auto-Patch (F5)

Cuando la IA sugiere cambios de código (en bloques Markdown), presiona **F5** para extraerlos y guardarlos:

1. La última respuesta de la IA se escanea en busca de bloques de código con triples backticks (` ```python ... ``` `)
2. Todos los bloques se concatenan y se guardan en `GITPR_PATCH_SUGGESTION_<clave-aleatoria>.txt`
3. Cada clave es única (formato `aB3-xK9`), por lo que los parches anteriores nunca se sobrescriben

Revisa el archivo generado y aplica los cambios manualmente en tu proyecto.

### Acciones por Mensaje (Ctrl+Shift+A / Ctrl+Shift+E)

Puedes aplicar Auto-Patch y Exportar a **cualquier** mensaje de la IA en la conversación, no solo al último.

Navega entre los mensajes de la IA usando **F7** y **F8**. El mensaje enfocado se resalta con un borde izquierdo más brillante, y aparece una barra de acciones sobre el campo de entrada.

- **Ctrl+Shift+S** — Extrae bloques de código solo del **mensaje enfocado** y los guarda en `GITPR_PATCH_SUGGESTION_<clave>.txt`
- **Ctrl+Shift+E** — Exporta solo el **mensaje enfocado** a `MESSAGE_<id-sesión>_<clave>.md`

El foco predeterminado es siempre la respuesta más reciente de la IA.

## Exportar (F6)

Presiona **F6** para guardar toda la conversación en un archivo Markdown estructurado:

- **Nombre del archivo:** `GITPR_CHAT_EXPORT_<uuid-de-sesión>.md`
- **Formato:** Cada mensaje está etiquetado con su rol (Usuario / Asistente IA / Sistema) y separado por líneas horizontales
- **Casos de uso:** Documentación, compartir con el equipo o alimentar contexto para otras herramientas de IA

## Actualizar Diff (F2)

Mientras programas en otro editor, presiona **F2** para actualizar el contexto del chat:

- Si se detectan nuevos cambios desde la última instantánea del diff, la IA es notificada y puede ver tus ediciones más recientes
- Si nada cambió, se muestra un mensaje de confirmación

## Salir del Chat

Presiona **Esc** o **Ctrl+C** para cerrar el chat. Tu sesión se guarda automáticamente.

## Consejos

- Usa `/clear` para empezar de cero si la conversación se vuelve muy larga o quieres cambiar de tema
- Combina `--lang` con `--provider` para personalizar idioma y modelo de IA: `gitpr --lang es_es --provider gemini -ch`
- Los archivos `GITPR_CHAT_EXPORT_*.md` pueden ser commiteados en tu repositorio como notas de desarrollo
