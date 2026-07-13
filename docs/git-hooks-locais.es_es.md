# Documentación Técnica: Integración de Git Hooks Locales (GitPR)

Esta documentación detalla la arquitectura y el uso de la funcionalidad de Git Hooks automáticos del CLI de GitPR. La implementación adopta la práctica de ****Shift Left****, trasladando la validación de código y la generación de mensajes (IA) al momento exacto del commit, antes de cualquier integración con el servidor remoto.

---

## 1. Instalación Automatizada

Para instalar los hooks en tu repositorio local, navega hasta la raíz del proyecto (donde reside la carpeta oculta `.git`) y ejecuta:

```bash  
gitpr --installhooks  
# o  
gitpr -ih  
```

**Qué hace este comando bajo el capó:**

1. Verifica la integridad del directorio .git/hooks.  
2. Descarga la versión más reciente de los scripts pre-commit y prepare-commit-msg directamente del repositorio oficial de GitPR.  
3. Aplica automáticamente los permisos de ejecución POSIX (chmod +x) a los archivos, garantizando la compatibilidad entre Linux, macOS y entornos Git Bash en Windows.

---

## **2. Hook: pre-commit (Linter Estático)**

El hook de pre-commit actúa como un "guardaespaldas" local. Se dispara instantáneamente al ejecutar git commit, antes de que se solicite el mensaje de commit.

### **Cómo funciona:**

* El script invoca el comando gitpr --linter.  
* GitPR analiza el diff actual (archivos en *stage*) contra las reglas definidas en el archivo .gitpr.linter.yml.  
* **Exit Code 0:** Si no hay violaciones, el flujo de Git continúa normalmente.  
* **Exit Code 1:** Si se detectan cadenas prohibidas (ej.: console.log, contraseñas, localhost), el script intercepta la acción, muestra las alertas en el terminal y **aborta el commit**.

### **Ruta de Escape (Bypass)**

Si existe una necesidad estricta de eludir la validación del Linter local (por ejemplo, al subir un código temporal de debug en una rama aislada), utiliza la flag nativa de Git:

Bash

git commit --no-verify -m "Tu mensaje aquí"

---

## **3. Hook: prepare-commit-msg (IA Auto-Commit)**

Este hook elimina la necesidad de escribir mensajes de commit manualmente. Integra la inteligencia artificial de Gemini directamente en el ciclo de vida de Git, generando mensajes con el estándar *Conventional Commits* basados en tu código.

### **Cómo funciona:**

1. Añade tus archivos al stage (git add .).  
2. Ejecuta solo el comando base de commit, sin pasar el mensaje:  
   ```bash  
   git commit
   ```

3. El hook entra en acción mostrando el mensaje: 🤖 GitPR: Solicitando sugerencia de commit a la IA...  
4. GitPR ejecuta la flag oculta --hook, enviando tu *diff* a Gemini.  
5. La IA genera el mensaje y el script inyecta el resultado de forma limpia en la primera línea del archivo temporal de Git.  
6. Tu editor de texto predeterminado (Vim, Nano, VS Code) se abrirá con el mensaje ya rellenado. Basta con guardar y cerrar para confirmar el commit.

### **Preservación del Flujo Manual**

El script es lo suficientemente inteligente como para no sobrescribir tu intención. Si ejecutas el commit pasando la flag de mensaje explícita (-m), el hook reconoce el origen como "message" y **desactiva el procesamiento de la IA de forma silenciosa**:

```bash

# La IA NO se activará en este caso, respetando tu mensaje.  
git commit -m "fix: corrige problema de concorrência na API"
```

---

## **4. Resolución de Problemas (Troubleshooting)**

* **El Hook no se ejecuta (Linux/macOS):** Asegúrate de que los archivos en .git/hooks tienen permiso de ejecución. Puedes forzarlo con chmod \+x .git/hooks/pre-commit.  
* **Comando no encontrado:** Los scripts de los hooks están configurados para buscar tanto la instalación global (gitpr) como la ejecución local mediante entorno virtual (pipenv run python run.py). Si estás usando un gestor de dependencias diferente (como Poetry), puede que necesites editar los scripts dentro de la carpeta .git/hooks para reflejar tu entorno.
