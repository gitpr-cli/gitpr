# **Documentación Técnica: Linter Estático Personalizable (--linter)**


El CLI de GitPR dispone de un motor de análisis estático ultrarrápido que se ejecuta localmente, sin consumir cuotas de IA ni necesitar conexión a internet. Analiza únicamente las **líneas modificadas o añadidas** en tu git diff, garantizando feedback instantáneo.

## **1. Cómo Ejecutar el Linter**

Puedes activar el linter de tres formas:

1. **Manualmente:** Ejecutando gitpr --linter en el terminal.  
2. **Mediante Pre-commit Hook:** Automáticamente antes de cada commit (instalado con gitpr -ih).  
3. **Mediante CI/CD:** En GitHub Actions, bloqueando el merge en caso de que el código devuelva exit code 1.

---

## **2. Estructura del Archivo .gitpr.linter.yml**

Las reglas del Linter residen en el archivo .gitpr.linter.yml en la raíz de tu proyecto. El archivo se lee en cada ejecución y posee la siguiente estructura YAML:

```YAML

rules:  
  - name: "identificador-da-regra"  
    extensions: ["js", "php", "py"] \# Extensiones donde se aplica la regla  
    regex: 'sua-expressao-regular-aqui'  
    message: "🚨 Mensaje de error que aparecerá en el terminal ({file\_name}, Línea {line\_number})"  
    ignore\_comments: true \# Ignora si la regex coincide dentro de un comentario (//, \#, /\*)  
    ignore\_paths: \# Opcional: Carpetas donde esta regla NO debe ejecutarse  
      \- "vendor/\*"  
    require\_paths: \# Opcional: Carpetas exclusivas donde esta regla DEBE ejecutarse  
      \- "routes/\*"

external_linters:
  - name: "ESLint (JavaScript/TypeScript)"
    extensions: ["js", "ts", "vue", "jsx", "tsx"]
    command: "npx eslint --format checkstyle"

## ---

## **3. Tutorial: Creando Reglas con Expresiones Regulares (Regex)**

El motor de GitPR usa la biblioteca nativa de Regex de Python (re). El secreto de una buena regla de Linter es ser lo suficientemente restrictiva como para capturar el error, pero lo suficientemente flexible como para ignorar espacios en blanco adicionales.

### **Ejemplo Práctico 1: Prohibiendo Verbos en Rutas (Estándar RESTful)**

**El Problema:** En el estándar REST, las URLs no deben contener verbos (ej.: /api/buscar-usuarios), sino sustantivos y métodos HTTP adecuados (GET /api/usuarios).

Mira cómo configurar una regla en Laravel (PHP) para impedir esto:

```YAML

  \- name: "check-route-verbs"  
    extensions: \["php"\]  
    require\_paths:  
      \- "routes/\*"  
    regex: 'Route::\[a-zA-Z\]+\\s\*\\(\\s\*\[''"\](get|get-|busca|buscar|procura|procurar|pesquisa|pesquisar|lista|listar)'  
    message: "🚨 URI inadecuada en {file\_name} (Línea {line\_number}). Evita verbos como 'buscar' o 'listar' en la URL. Usa el estándar RESTful."  
    ignore\_comments: true

#### **Diseccionando la Regex anterior:**

Para entender cómo crear las tuyas, mira cómo se construyó esta pieza por pieza:

* Route:: → Busca exactamente la llamada a la Facade de Laravel.  
* [a-zA-Z]+ → Captura cualquier método HTTP que venga después (ej.: get, post, put).  
* \s\*(\s\* → El \s\* significa "cero o más espacios". Esto garantiza que el Linter capture tanto Route::get(' como Route::get ( '.  
* [''"] → Acepta tanto comillas simples como dobles para abrir la cadena de la URL.  
* (get|get-|busca|buscar...) → El grupo de captura principal. El pipe | funciona como un "O". Si se detecta cualquiera de estas palabras justo al inicio de la URL, la regla falla.

### **Ejemplo Práctico 2: Bloqueando Logs de Debug Olvidados**

**El Problema:** Los desarrolladores frecuentemente olvidan comandos de debug en el código antes de hacer el commit.

**Regla para PHP (dd o dump):**

```YAML

  \- name: "check-php-debug"  
    extensions: \["php"\]  
    regex: '\\b(dd|dump|var\_dump|print\_r)\\s\*\\('  
    message: "🚨 Código de debug olvidado ({file\_name}, Línea {line\_number})."  
    ignore\_comments: true

*Consejo Regex:* El \b (Word Boundary) garantiza que la palabra sea exacta. Captura el comando dd(), pero ignora la palabra add(), evitando falsos positivos.

**Regla para JavaScript (console.log):**

```YAML

  - name: "check-js-console"  
    extensions: \["js", "ts", "vue"\]  
    regex: 'console\\.(log|debug|info)\\s\*\\('  
    message: "🚨 Uso de console.log no permitido en producción ({file\_name}, Línea {line\_number})."  
    ignore\_comments: true

*Consejo Regex:* El punto \. necesita una barra invertida (escape), pues en el lenguaje Regex un punto solo significa "cualquier carácter".

---

## **4. Consejos de Oro para Regex en el Linter**

1. **Escapa los caracteres especiales:** Símbolos como ( ) [ ] { } . \* \+ ? ^ $ tienen funciones matemáticas en Regex. Si quieres buscarlos en el código, coloca una barra delante (ej.: \( para encontrar un paréntesis abierto).  
2. **Cuidado con las comillas en YAML:** En el archivo .yml, envuelve tu regex: siempre con comillas simples '...'. Si tu regex necesita una comilla simple dentro de ella, duplícala '' o usa comillas dobles por fuera "...".  
3. **Usa \s\* sin moderación:** Nunca presupongas que el formato del código es perfecto. Usa \s\* para cubrir espacios en blanco, tabs y saltos de línea entre comandos.

---

## **5. Integración con Linters Externos (Bridge vía Checkstyle)**

GitPR CLI no necesita reinventar la rueda. Si tu proyecto ya usa herramientas como PHP_CodeSniffer, ESLint o Stylelint, GitPR puede actuar como un puente, ejecutando esas herramientas en segundo plano y filtrando los errores **solo para las líneas que modificaste en tu Pull Request actual**.

Para ello, el linter externo debe soportar la salida de informes en formato `checkstyle` (estándar universal en CI/CD).

### **Tiempo de Espera (Timeout) del Linter Externo**

Cada subproceso de linter externo está limitado por un **tiempo de espera
(timeout) de 120 segundos** (configurable mediante `GITPR_LINTER_TIMEOUT` en
`~/.gitpr/.env`). Si un linter supera el límite, se omite — sus violaciones no
entran en el informe — en lugar de bloquear toda la revisión. Los valores no
válidos o no positivos vuelven al valor predeterminado de 120s.

### **Cómo Configurar Rápidamente (--linter-setup)**

En lugar de configurar el YAML manualmente, puedes usar nuestro asistente interactivo:
Ejecuta en el terminal:
`gitpr --linter-setup`

El asistente mostrará opciones preconfiguradas, te orientará sobre el comando de instalación en tu proyecto (ej.: `npm install --save-dev eslint`) e inyectará la configuración correcta automáticamente en tu `.gitpr.linter.yml`.

Los presets del asistente se controlan remotamente mediante el archivo `templates/gitpr.linter-presets.json` (caché local en `~/.gitpr/conf/`), lo que permite añadir nuevos linters sin esperar una nueva versión de GitPR.

---

## **6. Informes de Análisis (Markdown)**

Cada vez que el linter se ejecute (ya sea manualmente con `--linter` o automáticamente antes del commit), consolidará los errores generados por las Reglas de Regex y los Linters Externos en un único informe.

Este informe formateado en Markdown se guardará automáticamente, manteniendo un historial de tus auditorías locales.

**Ubicación Predeterminada:** `.gitpr/reports/linter/`

**Personalización:** Puedes cambiar el nombre y la carpeta de este archivo definiendo la variable `OUTPUT_FILE_NAME_LINTER` en tu archivo `~/.gitpr/.env`.
