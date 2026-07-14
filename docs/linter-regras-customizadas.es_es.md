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

