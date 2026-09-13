# Registro de Uso — cada comando que ejecuta GitPR

GitPR mantiene un registro de su propio uso: una línea por cada comando, escrita en el momento en que el comando empieza. Es la respuesta a «¿qué ejecuté realmente, y cuándo?» — útil cuando una flag se comportó de forma inesperada, cuando quiere saber con qué frecuencia se usa una función, o cuando está reconstruyendo lo que ocurrió en un repositorio la semana pasada.

El registro es local, en texto plano, y nunca sale de su máquina. No se envía nada a ninguna parte.

---

## 1. Dónde Están los Archivos

Cada comando añade una línea en `~/.gitpr/logs/<uuid>.log`, y hay **un archivo por día**:

```text
~/.gitpr/logs/
├── 4b1c8d3e-1f27-5a44-9c0b-7d2e5f8a1b30.log   ← hoy
├── 9f2a7c10-6b83-5e21-8a4d-1c9f0e7b2d55.log   ← ayer
└── pr_desc/                                   ← el registro de publicación de PR, una función aparte
```

El nombre del archivo es un UUID **derivado de la fecha** — `uuid5` de `gitpr.usage.<YYYY-MM-DD>` — y no uno aleatorio. Es deliberado: un nombre aleatorio necesitaría un contador o un archivo de estado para saber qué archivo pertenece a hoy, y dos procesos de GitPR ejecutándose en el mismo instante podrían no coincidir. Derivado de la fecha, el mismo día resuelve siempre al mismo nombre, así que los comandos simultáneos simplemente añaden al mismo archivo.

Un día nuevo empieza un archivo nuevo. GitPR nunca los rota ni los borra — limpiar los antiguos es cosa suya.

---

## 2. Qué Contiene una Línea

```text
[2026-09-12 14:32:01] | v1.0.0 | gitpr -c | gitpr-cli/gitpr | Nataniel Fiuza <natan.fiuza@gmail.com>
```

| Campo | Origen | Notas |
| --- | --- | --- |
| Fecha y hora | el reloj local, cuando empieza el comando | `YYYY-MM-DD HH:MM:SS` |
| Versión | la versión de GitPR en ejecución | |
| Comando | el nombre del programa y las flags tal como se escribieron | `gitpr -c`, `gitpr-mcp --list` |
| Repositorio | `remote.origin.url`, reducida a `owner/repo` | `-` fuera de un repositorio, o sin remote de origen |
| Autor | `user.name` y `user.email` de la configuración de Git | `-` cuando Git no tiene identidad configurada |

El repositorio se reduce a su ruta, sea cual sea la forge: `git@github.com:owner/repo.git`, `https://gitlab.com/group/repo` y `https://dev.azure.com/org/project/_git/repo` se convierten en `owner/repo`, `group/repo` y `org/project/repo`.

Toda invocación queda registrada, incluidas `--help` y las que fallan. En el caso del servidor MCP eso significa su arranque: `gitpr-mcp` escribe una línea cuando el servidor se levanta, no una por llamada a una herramienta.

---

## 3. Cómo Desactivarlo

Lo controla `GITPR_SHOW_LOGS`, y viene **activada** por defecto — toda instalación ya tiene la línea sembrada en `~/.gitpr/.env`.

| Dónde | Cómo |
| --- | --- |
| En la pantalla de configuración | `gitpr config` → **General** → **Guardar registros generales** |
| En el archivo | `GITPR_SHOW_LOGS=false` en `~/.gitpr/.env` |
| En una sola ejecución | `GITPR_SHOW_LOGS=false gitpr -c` |

El entorno siempre gana al archivo (vea [la pantalla de configuración](config-tui.es_es.md) §2), así que la última fila desactiva ese comando concreto sin tocar nada más.

Desactivarlo detiene las líneas nuevas. No borra lo que ya está ahí.

---

## 4. Qué No Registra

El registro es deliberadamente delgado: registra *que* un comando se ejecutó y *cuál* fue, y nada sobre lo que leyó o produjo.

Nunca contiene el diff, contenido de archivos, rutas de archivos, texto de prompt o de skill, respuestas de la IA, los mensajes de commit y descripciones de PR generados, ni credencial alguna.

Los dos valores personales que sí guarda — el repositorio y el autor de Git — se quedan en la máquina, ya que el archivo es local y no se transmite nada.

---

## 5. Notas para Desarrolladores

| Archivo | Papel |
| --- | --- |
| `src/usage_log.py` | La función completa: derivación de la ruta, la consulta única a git, el formato de la línea y la escritura |
| `src/main.py` | Una llamada al principio del callback raíz — el punto único al que llega toda flag, todo subcomando y `--help` |
| `src/mcp_server.py` | Una llamada en `main()`, porque el script de consola `gitpr-mcp` nunca carga `main.py` |

Dos garantías que la implementación da a propósito:

- **La escritura es síncrona.** Un hilo en segundo plano — como hace el registrador de métricas locales — pierde la entrada siempre que el proceso termina antes de que el hilo sea planificado, y un registro que descarta comandos en silencio es peor que no tener registro.
- **Nunca puede molestar a un comando.** Todo fallo — sin git, sin permiso, sin directorio home — se traga: `log_usage()` vuelve sin escribir y el comando continúa. Tampoco imprime nunca nada, porque el servidor MCP reserva la stdout para su flujo JSON-RPC.

Añadir un tercer punto de entrada significa añadir una llamada en él. Nada llega al registro por sí solo.
