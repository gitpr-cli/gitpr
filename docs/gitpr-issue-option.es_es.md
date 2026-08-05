# 🚀 Creación y Gestión de Issues con GitPR CLI

La funcionalidad `--issue` (o `-is`) transforma GitPR en un asistente de documentación avanzado. En lugar de escribir Issues desde cero, la Inteligencia Artificial lee tu contexto de trabajo, estructura la issue en el estándar **Qué / Por qué / Dónde / Cómo** y abre una interfaz visual directamente en tu terminal para que la revises antes de enviarla.

---

## 1. El Triple Motor de Contexto (¿Cuál usar y por qué?)

La IA de GitPR puede leer tres "idiomas" diferentes según la combinación de flags que utilices. Cada motor ha sido diseñado para un escenario específico del día a día del desarrollador:

### 🆕 Issue de Código Nuevo (El Por Defecto)
**Comando:** `gitpr --issue` o `gitpr -is`
* **Cómo funciona:** GitPR lee tu `git diff` actual (los cambios que acabas de hacer y aún no has guardado en un commit).
* **Por qué usarlo:** Ideal para documentar rápidamente una pequeña *feature* o *bugfix* que acabas de programar, garantizando que el seguimiento del problema quede registrado en GitHub antes de enviar el código.

### 📦 Issue de Release / Épico
**Comando:** `gitpr -is -ht` (Issue + History)
* **Cómo funciona:** GitPR compila todo el `git log` de la rama actual y lo combina con el banco de memoria de la propia IA (buscando descripciones de PRs antiguos de esta rama en la caché local).
* **Por qué usarlo:** Si has trabajado durante varios días en una rama, este comando genera una súper issue que resume toda la *feature*. Excelente para entregar documentación consolidada de una Release a los equipos de QA o Producto.

### 🕰️ Issue Arqueológica / Deuda Técnica
**Comando:** `gitpr -is -b src/archivo.py:10-20` (Issue + Blame)
* **Cómo funciona:** GitPR no mira el código nuevo. Activa el Motor Arqueológico para leer la línea de tiempo y la evolución histórica de esas líneas específicas.
* **Por qué usarlo:** Ideal para documentar deuda técnica. La IA estructura una issue explicando cómo evolucionó una regla de negocio heredada con el tiempo, por qué se convirtió en un problema y la justificación para una futura refactorización.

---

## 2. Autenticación y el Token PAT

Para que GitPR pueda crear la Issue directamente en tu repositorio remoto, necesita comunicarse con la **API REST de GitHub**.

1. La primera vez que ejecutes el comando, la herramienta solicitará un **Personal Access Token (PAT)**.
2. GitPR genera un enlace inteligente y lo muestra en la terminal. Simplemente haz clic en él: tu navegador se abrirá directamente en la página de creación de tokens de GitHub con el permiso correcto (`repo`) ya preseleccionado.
3. Pega el token en la terminal.

**Seguridad:** Tu token nunca se transmite en texto plano. En cuanto lo pegas, GitPR utiliza la librería `cryptography` para encriptar la clave simétricamente, guardando solo el hash seguro en el archivo oculto `~/.gitpr/.env` de tu máquina.

---

## 3. La Interfaz Gráfica de Terminal (TUI)

Una vez que la IA procesa el contexto y estructura la Issue, GitPR no envía los datos a ciegas. Abrirá una interfaz interactiva basada en la librería `textual`.

En esta elegante pantalla azul, puedes editar libremente el Título y el Cuerpo de la issue. Cuando estés satisfecho, utiliza los atalhos de teclado rápidos (sin necesidad de ratón):

* **`F4` (Ayuda):** Abre una ventana modal con explicaciones rápidas sobre la interfaz.
* **`F2` (Guardar Local):** Exporta el contenido de la pantalla a un archivo Markdown (`.md`) en tu carpeta actual. Útil si solo deseas el borrador para refinarlo más tarde.
* **`F3` (Crear en GitHub):** Dispara la solicitud oficial. En segundos, GitPR cierra la pantalla y muestra en la terminal el enlace verde de tu nueva issue ya creada y publicada en el repositorio.
* **`Esc` (Salir):** Aborta la operación de forma segura sin guardar nada.
