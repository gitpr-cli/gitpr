# Documentación Técnica: Auto-Updater (--update)

GitPR se distribuye exclusivamente a través de PyPI. El **Auto-Updater** comprueba diariamente si se ha publicado una nueva versión y mantiene la herramienta siempre en la release más reciente.

---

## 1. Verificación Manual

```bash
gitpr -u
# o
gitpr --update
```

El comando fuerza una verificación inmediata en PyPI y muestra el comando de actualización. **No** instala nada — la actualización en sí siempre la realiza tu gestor de paquetes.

---

## 2. Bloqueo Obligatorio de Actualización

En cada ejecución de GitPR (excepto en los modos `--quiet`, `--hook` y `--mcp`), la herramienta comprueba si se ha publicado una versión más nueva. El resultado se guarda en caché durante **24 horas** en el archivo `~/.gitpr/update_cache.json` para evitar llamadas repetidas a la API.

Cuando la versión publicada es más nueva que la local, GitPR **bloquea la ejecución**: muestra ambas versiones, indica el comando `pip install --upgrade gitpr-cli` y termina con un estado distinto de cero, sin realizar ningún trabajo.

No existe ninguna flag, fallback ni modo de compatibilidad que mantenga en ejecución una **release instalada** desactualizada — actualizar es la única forma de continuar. Un checkout usado para desarrollo local tiene una única variable de escape, documentada en [Instalar GitPR desde el código fuente](tutorial/install-from-source.es_es.md).

### Excepciones

El bloqueo nunca se activa para:

| Contexto | Motivo |
| --- | --- |
| `--quiet` | Scripts y automatizaciones que descartan la salida |
| `--hook` | Git hooks (`prepare-commit-msg`, métricas) — nunca pueden romper un commit |
| `--mcp` / `gitpr-mcp` | Servidor MCP consumido por IDEs y agentes |
| `-u` / `--update` | Es precisamente el comando que explica cómo actualizar |
| `-h --<flag>` | Ayuda contextual |

`--help` y `--version` tampoco se ven afectados: Click los resuelve antes de que se ejecute el cuerpo del comando.

### Comportamiento Offline

Cuando no es posible determinar la versión publicada — sin internet y sin caché del día actual — GitPR se ejecuta con normalidad. Un usuario offline nunca debe quedar atrapado en un comando que no puede ejecutar.

---

## 3. Aplicar la Actualización

```bash
pip install --upgrade gitpr-cli
```

Los usuarios de `pipx`, `uv` o `poetry` deben actualizar con su propia herramienta (`pipx upgrade gitpr-cli`, `uv tool upgrade gitpr-cli`, …).

---

## 4. Guardián de Conexión

Antes de cualquier operación de red, GitPR verifica la conectividad mediante el socket `8.8.8.8:53`. Si no hay internet, la herramienta opera con normalidad en modo offline — sin bloquearse ni mostrar errores de conexión.

---

## 5. Fuente de Versión

| Fuente | Uso |
| --- | --- |
| **PyPI** (`pypi.org/pypi/gitpr-cli/json`) | Fuente única de la versión publicada |

La versión local se define en `src/updater.py` (`__version__`) y se incrementa con cada release.

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para información sobre instalación y configuración inicial.
