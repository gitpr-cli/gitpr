# Documentación Técnica: Auto-Updater (--update)

GitPR dispone de un sistema de actualización automática (**Auto-Updater**) que mantiene la herramienta siempre en la versión más reciente, con verificación diaria y actualización mediante *hot-swap*.

---

## 1. Actualización Manual

```bash
gitpr -u
# o
gitpr --update
```

El comando fuerza la verificación e instalación inmediata de la versión más reciente.

---

## 2. Verificación Automática Diaria

En cada ejecución de GitPR (excepto los modos `--quiet` y `--hook`), la herramienta verifica silenciosamente si hay una nueva versión disponible. El resultado se almacena en caché durante **24 horas** en el archivo `~/.gitpr/update_cache.json` para evitar llamadas repetidas a la API.

Si hay una nueva versión, se muestra una notificación al final de la ejecución.

---

## 3. Métodos de Actualización

El Auto-Updater detecta automáticamente el método de instalación:

### 3.1 Instalación mediante pip

```bash
pip install --upgrade gitpr-cli
```

### 3.2 Instalación mediante Binario (PyInstaller)

GitPR usa la técnica de **Hot-Swap** para binarios standalone:

1. Verifica la versión más reciente en [GitHub Releases](https://github.com/gitpr-cli/gitpr.git/releases)
2. Descarga el nuevo ejecutable
3. Renombra el `.exe` actual a `.exe.old`
4. Mueve el nuevo binario a su lugar
5. En caso de fallo, revierte al `.exe.old` (rollback automático)
6. En la próxima ejecución, elimina el `.old` automáticamente (limpieza)

---

## 4. Guardián de Conexión

Antes de cualquier operación de red, GitPR verifica la conectividad mediante el socket `8.8.8.8:53`. Si no hay internet, la herramienta opera normalmente en modo offline — sin bloquearse ni mostrar errores de conexión.

---

## 5. Fuentes de Versión

| Fuente | Uso |
| --- | --- |
| **PyPI** | Versión para instalaciones pip (`pip install gitpr-cli`) |
| **GitHub Releases** | Versión para binarios standalone (`.exe`) |

La versión local se define en `src/updater.py` (`__version__`) y se incrementa en cada release.

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para información sobre la instalación y configuración inicial.
