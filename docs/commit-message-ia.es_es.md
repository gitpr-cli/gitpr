# Documentación Técnica: Generación de Mensajes de Commit con IA (--commit)

El comando `--commit` (`-c`) de GitPR genera automáticamente mensajes de commit con el formato **Conventional Commits** usando inteligencia artificial para analizar tus cambios locales y ofrece un flujo TUI interactivo completo para seleccionar archivos, revisar el mensaje y realizar el commit.

---

## 1. Flujo Interactivo de Commit

```bash
gitpr -c
```

Al ejecutarse en un terminal interactivo, GitPR te guía a través de un flujo de 4 pasos:

1. **Selector de Stage ("Archivos fuera del stage")**:
   - Si hay archivos unstaged o untracked, GitPR abre la ventana modal `StageFilesScreen` con casillas de selección.
   - Puedes seleccionar con precisión qué archivos deseas añadir al stage (`git add`).
   - Usa **"Seleccionar todo"**, **"Deseleccionar todo"**, **"Stage Selected"** (Añadir seleccionados), **"Skip Staging"** (Omitir stage) o **"Cancelar"**.
   - Si todos los cambios ya están en el stage, esta pantalla se omite automáticamente.

2. **Generación del Mensaje con IA**:
   - Analiza el diff del stage (`git diff --cached`) aplicando las exclusiones inteligentes (`SMART_EXCLUDES`).
   - Genera el mensaje según el estándar Conventional Commits en segundo plano mientras muestra un modal animado de progreso (`CommitProgressScreen`).

3. **Revisión y Edición del Mensaje**:
   - Muestra el mensaje generado en el modal `CommitMessageScreen`.
   - Puedes revisar y editar el texto directamente antes de confirmar.
   - Pulsa **"Confirmar"** para continuar o **"Cancelar"** para abortar sin hacer commit.

4. **Ejecución Animada del Commit**:
   - Al confirmar, muestra el modal `CommitProgressScreen` con la barra deslizante animada en degradado.
   - Ejecuta el commit (`git commit -m "..."`) incluyendo la firma de coautoría.
   - Muestra los registros en tiempo real y el hash del commit generado, con el botón **"Cerrar"** para finalizar.

---

## 2. Formato Conventional Commits

La IA está instruida para generar mensajes con el estándar:

```
tipo: descripción corta

Cuerpo opcional con detalles adicionales
```

**Tipos utilizados:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

---

## 3. Integración con Git Hooks (No Interactivo)

El `--commit` se usa internamente por el hook `prepare-commit-msg`. Cuando se instala con `gitpr -ih`, el hook ejecuta:

```bash
gitpr --commit --hook <ruta-del-archivo-temporal>
```

La flag `--hook` mantiene la ejecución estrictamente no interactiva: no se abre ninguna pantalla TUI ni modal, y el mensaje sugerido se inyecta directamente en el editor de Git.

---

## 4. Configuración de Staging y Automatización

Puedes configurar el comportamiento del staging mediante variables de entorno en `~/.gitpr/.env`:

- `GITPR_AUTO_STAGE=true`: Añade automáticamente todos los archivos unstaged al stage sin abrir el selector.
- `GITPR_SKIP_UNSTAGED_CHECK=true`: Omite la comprobación de archivos fuera del stage.
- `--no-unstaged-check`: Flag de línea de comandos para omitir la comprobación de archivos fuera del stage en una ejecución puntual.

---

## 5. Personalización mediante Skill

El comportamiento de la IA puede personalizarse a través del archivo `.gitpr.commit.md` en `.gitpr/skill/`:

```bash
gitpr -s          # Descarga la plantilla .gitpr.commit.md
# Edita el archivo según las convenciones de tu equipo
gitpr -c          # La IA usará tus reglas personalizadas
```

---

## 6. Selección de Proveedor de IA

```bash
gitpr -c -p gemini       # Fuerza Google Gemini
gitpr -c -p deepseek     # Fuerza DeepSeek
gitpr -c -p ollama       # Fuerza Ollama local
```

---

## 7. Caché de Respuestas

GitPR genera un hash MD5 de tu diff del stage + instrucciones. Si ejecutas `gitpr -c` de nuevo **sin modificar el código en stage**, la respuesta se devuelve instantáneamente desde la caché local, ahorrando cuotas de la API.

---

## 8. Firma de Coautoría

Cada mensaje de commit generado por GitPR lleva automáticamente el trailer de coautoría:

```text
Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

El trailer se añade programáticamente (nunca por la IA) en todos los flujos: TUI interactiva de commit, hook `prepare-commit-msg`, auto-commit en la publicación de PR y la herramienta MCP `generate_commit_message`. Se separa del mensaje con líneas en blanco adicionales para que no aparezca a primera vista en las vistas previas colapsadas de commits de GitHub, y nunca se duplica cuando el mensaje ya lo contiene.

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para una visión general de todas las funcionalidades.
