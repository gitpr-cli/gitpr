# Instalar GitPR desde el código fuente (y desbloquear el portero de versión)

Esta guía es para quien ejecuta GitPR desde un **checkout local** en lugar del
paquete publicado en PyPI, y que por eso se topa con el bloqueo de actualización
obligatoria.

> Si tu objetivo es solo probar un cambio antes de publicar una nueva versión en
> PyPI, la receta más corta de [testar_sem_usar_pypi.md](testar_sem_usar_pypi.md)
> (en portugués) puede bastar. Esta guía va más allá: explica **por qué** el
> bloqueo de actualización sigue disparándose en una instalación desde el código
> fuente y qué hacer al respecto.

---

## 1. El síntoma

Instalaste GitPR desde el repositorio, con la bandera de modo editable:

```bash
pip install -e .
```

Y, aun así, cada vez que lo ejecutas, GitPR se niega a funcionar:

```text
⚠️ A new version of GitPR is available: 1.1.0 -> 1.2.0
GitPR must be updated before it can run: pip install --upgrade gitpr-cli
```

El proceso termina con un estado distinto de cero y no hace ningún trabajo.
Ejecutar `pip install --upgrade gitpr-cli` es el movimiento obvio, pero es
exactamente lo que **no** quieres: sustituye tu checkout por el paquete
publicado.

---

## 2. Instalar desde el código fuente (modo editable)

El comando es `pip install -e .` — la `-e` viene de *editable* y el punto es el
directorio actual.

```bash
git clone https://github.com/gitpr-cli/gitpr.git
cd gitpr
pip install -e .
```

> Ojo con el **espacio y el punto** al final de `-e .`. El punto significa
> "instala el paquete de este directorio"; sin él, pip busca en PyPI un paquete
> con ese nombre literal y falla.

Confirma que se creó el punto de entrada:

```bash
gitpr --version
```

En modo editable Python no copia los archivos — enlaza la distribución instalada
directamente con tu directorio de trabajo. Guardar un archivo en el editor basta
para que el cambio valga en la siguiente ejecución de `gitpr`, sin reinstalar.

---

## 3. Por qué el bloqueo de actualización sigue disparándose

Esta es la parte que sorprende: **no es una instalación rota**. Es el portero de
actualización funcionando tal como fue diseñado, sobre un checkout que está por
detrás de la release publicada.

El portero está en `enforce_update_required()` ([src/updater.py](../../src/updater.py))
y compara dos versiones:

| Versión | De dónde viene |
| --- | --- |
| Remota | `https://pypi.org/pypi/gitpr-cli/json`, con caché de 24h en `~/.gitpr/update_cache.json` |
| Local | `__version__`, al principio de `src/updater.py` |

La ejecución se bloquea cuando la versión remota es **mayor** que la local. La
trampa está en el lado *local*: en una instalación editable, `src/updater.py` se
lee de **tu árbol de trabajo**, no de una copia congelada en el momento de la
instalación. Lo que diga `__version__` en el checkout que tienes abierto es la
versión que GitPR reporta — y, por lo tanto, la versión que el portero compara.

El escenario del fallo queda así:

| | Valor |
| --- | --- |
| Publicado en PyPI | `1.2.0` |
| `__version__` en tu checkout | `1.1.0` |
| Resultado | bloqueado en todos los comandos |

Un segundo síntoma, más sutil, del mismo mecanismo: `git stash`,
`git checkout` o `git switch` a una rama anterior al último corte de release
vuelve a bloquear GitPR de inmediato, porque el archivo en disco cambió aunque
no se haya reinstalado nada.

---

## 4. Desbloquear — opción A (recomendada): alinéate con la release

La corrección directa es hacer que el árbol en el que trabajas reporte una
versión **mayor o igual** a la que publica PyPI. En la práctica:

```bash
git switch main
git pull
pip install -e .
gitpr -u
```

El `gitpr -u` (`--update`) nunca se bloquea, así que es la forma más segura de
confirmar la situación antes de ejecutar algo más pesado. Imprime la comparación
y el comando de actualización, y no instala nada.

Ejecuta `pip install -e .` de nuevo también tras un `git pull` o un cambio de
rama que añada o renombre módulos. El enlace editable cubre el árbol de código,
pero un punto de entrada o dependencia nuevos en `pyproject.toml` solo llegan a
la distribución instalada con un `pip install -e .` nuevo.

> **No edites `__version__` a mano para falsificar una versión.** Subir la
> cadena sin cortar una release corrompe lo que reporta `gitpr -u` y esconde una
> necesidad real de actualización. El marcador de versión lo define el proceso
> de release, no la conveniencia del desarrollador.

---

## 5. Desbloquear — opción B: `GITPR_SKIP_UPDATE_CHECK` (uso local)

GitPR lee una variable de entorno que silencia la comprobación por completo.
Añade una línea al archivo de configuración global `~/.gitpr/.env`:

```bash
# ~/.gitpr/.env
GITPR_SKIP_UPDATE_CHECK=1
```

Guarda el archivo y ejecuta GitPR de nuevo — el bloqueo desapareció.

**Usa esto solo para desarrollo local y offline.** No es un sustituto de
actualizar una instalación de release: mientras la variable esté activada, un
GitPR genuinamente desactualizado se ejecuta en silencio, sin aviso y sin
protección contra comportamiento que ya se corrigió upstream.

Cuatro detalles que conviene conocer antes de depender de ella:

- **Cualquier valor no vacío desactiva la comprobación** — incluidos `0`, `false`
  y `no`. La variable se lee como una bandera simple
  (`bool(os.environ.get(..., "").strip())`), no se interpreta como booleano. Solo
  un valor vacío o con únicamente espacios mantiene la comprobación activada.
  Definir `GITPR_SKIP_UPDATE_CHECK=` por lo tanto **no hace nada**.
- **No es una clave de `DEFAULT_CONFIG`.** No aparece en la TUI de configuración
  y no la crea el asistente de instalación — tienes que añadir la línea a
  `~/.gitpr/.env` a mano.
- **Funciona a través de la carga del dotenv.** `~/.gitpr/.env` se carga en
  tiempo de import, antes de que se ejecute el portero, y por eso escribirla en
  el archivo funciona igual que exportarla en la shell. Exportarla para un solo
  comando también funciona:

  ```bash
  GITPR_SKIP_UPDATE_CHECK=1 gitpr -c
  ```

- **Para volver a activar la comprobación**, borra la línea de `~/.gitpr/.env`
  (o sobrescríbela con un valor vacío) y reinicia GitPR.

---

## 6. Lo que nunca se bloquea

No toda invocación pasa por el portero. La comprobación se omite para:

| Contexto | Motivo |
| --- | --- |
| `--quiet` | Scripts y automatización que descartan la salida |
| `--hook` | Hooks de git — nunca pueden romper un commit |
| `--mcp` / `gitpr-mcp` | Servidor MCP consumido por IDEs y agentes |
| `-u` / `--update` | Es justamente el comando que explica cómo actualizar |
| `-h --<flag>` | Ayuda contextual |
| `--help` / `--version` | Click resuelve ambos antes de que se ejecute el cuerpo del comando |
| **Cualquier subcomando** | `gitpr fix`, `gitpr review-pr`, `gitpr release`, `gitpr init` se despachan antes del portero |
| Offline | Cuando la versión remota es desconocida, la ejecución continúa — un usuario offline nunca puede quedar encerrado fuera de un comando que no puede arreglar |

En un checkout bloqueado, por lo tanto, `gitpr -u` y los subcomandos siguen
siendo utilizables para diagnóstico, incluso sin la variable de entorno.

---

## 7. Verificar la instalación

Confirma qué modo está activo:

```bash
pip list --editable
```

`gitpr-cli` debería aparecer en la lista. En un pip más antiguo, busca un
directorio `gitpr_cli.egg-info/` en la raíz del repositorio — su presencia es la
firma de una instalación editable.

> ¿Aparece `WARNING: Ignoring invalid distribution ~itpr-cli`? Son directorios
> `~itpr_cli-*.dist-info` dejados en `site-packages` por una operación de `pip`
> interrumpida — pip renombra una distribución a `~<nombre>` antes de borrarla,
> y una ejecución abortada deja el renombrado atrás. Son restos inertes que pip
> ignora; bórralos a mano si el aviso te molesta.

Después confirma la versión reportada:

```bash
gitpr -u
```

Compara la versión local impresa ahí con la línea `__version__` de
`src/updater.py` del checkout que tienes abierto. Si son distintas, la
instalación está apuntando a otro sitio que no es el árbol que crees estar
editando.

---

## 8. Volver a la instalación de PyPI

Cuando termines de desarrollar localmente:

```bash
pip uninstall gitpr-cli
pip install --upgrade gitpr-cli
```

Luego limpia lo que dejó atrás el modo editable:

- elimina la línea `GITPR_SKIP_UPDATE_CHECK` de `~/.gitpr/.env`;
- borra el directorio `gitpr_cli.egg-info/` en la raíz del repositorio (son
  metadatos de build desechables);
- confirma con `pip list --editable`, que ya no debería listar `gitpr-cli`.

---

## Véase también

- [auto-update.md](../auto-update.es_es.md) — el actualizador automático y el bloqueo de actualización obligatoria
- [testar_sem_usar_pypi.md](../testar_sem_usar_pypi.md) — probar sin gastar una versión en PyPI (en portugués)
- [ARCHITECTURE.md](../ARCHITECTURE.md) — mapa de módulos y flujo de comandos
