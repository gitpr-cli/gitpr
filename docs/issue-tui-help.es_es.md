# Documentación Técnica: Interfaz Gráfica de Terminal (TUI) — Issues

Esta documentación describe el funcionamiento de la interfaz gráfica interactiva (TUI) de GitPR para la generación y gestión de Issues, construida con la biblioteca de Python `textual`.

---

## 1. ¿Qué es la TUI de Issues?

Cuando ejecutas el comando `gitpr --issue` (o `-is`), GitPR analiza tu código y abre un panel interactivo directamente en el terminal. Esto te permite revisar, editar y mejorar la issue generada por la Inteligencia Artificial antes de guardarla o enviarla al repositorio remoto.

---

## 2. Motores de Contexto (3 Modos de Generación)

La funcionalidad de Issues posee **3 motores de contexto** distintos, activados según las flags combinadas con `--issue`. Cada motor alimenta a la IA con un conjunto diferente de información, adecuado al momento del ciclo de desarrollo.

### 2.1 Issue de Código Nuevo — `gitpr -is`

**Contexto:** `git diff` actual (cambios no commiteados).

```bash
gitpr -is
```

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | Diff local (`git diff HEAD`) |
| **Cuándo usar** | Antes de commitear — acabas de programar y quieres documentar la tarea |
| **Resultado** | Issue que describe exactamente lo que está en tu working tree |
| **Ideal para** | Documentación rápida de features, correcciones y refactorizaciones recién implementadas |

> **Consejo:** Este es el modo más rápido. La IA lee únicamente las líneas que modificaste y genera una issue enfocada y objetiva.

---

### 2.2 Issue de Épica / Release — `gitpr -is -ht`

**Contexto:** Historial completo de la rama actual (Git Log + Caché de PRs anteriores).

```bash
gitpr -is -ht
```

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | `git log` de la rama + caché local de PRs generados por GitPR |
| **Cuándo usar** | Al final de una feature branch con múltiples commits o al cerrar una release |
| **Resultado** | Issue consolidada con el panorama completo de todo lo que se desarrolló |
| **Ideal para** | Épicas, releases, features grandes que tardaron varios días/commits en completarse |

> **Consejo:** GitPR rastrea el historial de commits exclusivos de tu rama y los informes de PR ya generados para componer una visión de alto nivel. Si no hay commits exclusivos ni PRs anteriores, el comando mostrará un aviso y abortará.

---

### 2.3 Issue Arqueológica / Deuda Técnica — `gitpr -is -b arquivo:linhas`

**Contexto:** Línea de tiempo de un bloque específico de código mediante `git blame`.

```bash
gitpr -is -b src/core.py:140-195
```

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | `git blame` (historial de cambios línea a línea) + rastreo de commits padre (hasta 4 niveles) |
| **Cuándo usar** | Al identificar código heredado que necesita refactorización o documentar deuda técnica |
| **Resultado** | Issue que contiene la cronología del bloque: cuándo surgió, quién lo modificó, cómo evolucionó y por qué necesita ser refactorizado |
| **Ideal para** | Documentar deudas técnicas, justificar refactorizaciones, comprender la evolución de código crítico |

> **Consejo:** Puedes usar el formato interactivo también: `gitpr -is -b arquivo` (sin especificar líneas). GitPR preguntará qué líneas investigar.

---

## 3. Estructura de la Issue (Qué / Por Qué / Dónde / Cómo)

La IA de GitPR está instruida para generar el borrador de la issue siguiendo un patrón riguroso de ingeniería de software que facilita la comunicación del equipo:

| Sección | Descripción |
| --- | --- |
| **Qué (What)** | Checklists directos sobre las funcionalidades creadas o los problemas identificados |
| **Por Qué (Why)** | El contexto y la motivación técnica detrás de la implementación |
| **Dónde (Where)** | Especificación de las rutas, módulos, páginas o recursos afectados |
| **Cómo (How)** | Detalle técnico dividido en Backend/Motor, Base de Datos/Datos y Frontend/CLI/Interfaz |

> **Personalización:** Puedes personalizar la plantilla usada por la IA mediante el archivo `.gitpr.issue.md` en la raíz del proyecto (descárgalo con `gitpr -s`).

---

## 4. Atajos y Navegación de la TUI

La interfaz se diseñó para ser rápida y prescindir del uso constante del ratón. Puedes navegar por los campos usando la tecla `Tab` y utilizar los siguientes atajos:

| Tecla | Acción | Descripción |
| --- | --- | --- |
| **`F1`** | Ayuda | Abre un modal flotante con instrucciones rápidas de uso de la interfaz |
| **`F2`** | Guardar `.md` Local | Exporta el contenido de la pantalla a un archivo Markdown en la carpeta actual del proyecto. Ideal para cuando solo deseas el borrador para refinarlo posteriormente |
| **`F3`** | Crear en GitHub | Se conecta a la API REST de GitHub y crea la issue automáticamente en el repositorio remoto. El enlace directo a la issue recién creada se mostrará en el terminal |
| **`F4`** | Ayuda (alternativo) | Atajo alternativo para abrir las instrucciones de la TUI |
| **`Esc`** | Salir | Aborta la operación y cierra la interfaz sin guardar ningún cambio |
| **`Tab`** | Navegar | Alterna el foco entre los campos de título y cuerpo de la issue |

---

## 5. Integración con GitHub (Token PAT)

Para crear issues directamente en el repositorio remoto (`F3`), GitPR necesita un **Personal Access Token (PAT)** de GitHub con ámbito `repo`.

### 5.1 Configuración del Token

La primera vez que uses `F3`, GitPR hará lo siguiente:

1. Detectar que no hay ningún token configurado
2. Mostrar la URL de generación del token con los parámetros prerrellenados (ámbito `repo`)
3. Solicitar que pegues el token generado
4. Almacenarlo cifrado (Fernet) en el archivo `~/.gitpr/.env`

### 5.2 Seguridad

- El token se almacena como hash cifrado — nunca en texto plano
- La clave maestra de descifrado permanece en `~/.gitpr/secret.key`
- Consulta la guía completa en [github-pat-integration.md](github-pat-integration.md)

---

## 6. Ejemplos Prácticos

### Ejemplo 1: Documentar una feature antes de commitear

```bash
# Acabas de implementar un sistema de login
gitpr -is
# → La IA lee el diff, genera el borrador y abre la TUI
# → Revisa, ajusta el texto si es necesario
# → Pulsa F3 para crear la issue en GitHub
```

### Ejemplo 2: Generar una issue de release

```bash
# Tu branch feature/payment tiene 15 commits a lo largo de 3 días
git checkout feature/payment
gitpr -is -ht
# → La IA consolida todo el historial en una issue de épica
```

### Ejemplo 3: Documentar deuda técnica

```bash
# Encontraste un bloque de código confuso en el archivo heredado
gitpr -is -b src/legacy/parser.py:200-350
# → La IA rastrea la evolución del bloque desde el commit original
# → Genera una issue explicando la deuda técnica y sugiriendo refactorización
```

---

## 7. Archivos Relacionados

| Archivo | Función |
| --- | --- |
| `.gitpr.issue.md` | Plantilla local con reglas personalizadas para la generación de issues (descárgala con `gitpr -s`) |
| `~/.gitpr/.env` | Configuración global: claves de API y token de GitHub cifrado |
| `~/.gitpr/secret.key` | Clave maestra Fernet para el descifrado de las credenciales |

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para una visión general de todas las funcionalidades de GitPR.
