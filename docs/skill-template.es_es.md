# Documentación Técnica: Sistema de Skills y Plantillas (--skill)

GitPR utiliza un sistema de **Skills** (Prompt Engineering) que permite personalizar el comportamiento de la inteligencia artificial de acuerdo con las reglas de negocio de tu empresa. Los archivos de plantilla actúan como *System Instructions* de la IA.

---

## 1. Descargar las Plantillas

```bash
gitpr -s
# o
gitpr --skill
```

Este comando crea los siguientes archivos en la carpeta `.gitpr/skill/` del proyecto:

| Archivo | Función |
| --- | --- |
| `.gitpr.commit.md` | Reglas para la generación de mensajes de commit |
| `.gitpr.pr.md` | Estructura exigida para la descripción de Pull Request |
| `.gitpr.review.md` | Foco de arquitectura para el code review de diffs |
| `.gitpr.filereview.md` | Reglas de cohesión para la auditoría de archivo completo |
| `.gitpr.issue.md` | Estructura y detalle para la generación de Issues |
| `.gitpr.blame.md` | Foco del análisis arqueológico de código |
| `.gitpr.linter.yml` | Reglas de regex para la validación estática |

> **Importante:** El comando `--skill` **nunca sobrescribe** archivos locales existentes. Si un `.gitpr.*.md` ya existe, se conserva.

---

## 2. Cómo Funciona

Cada comando de GitPR busca automáticamente el archivo de skill correspondiente:

| Comando | Archivo de skill usado |
| --- | --- |
| `gitpr -c` | `.gitpr.commit.md` |
| `gitpr` (por defecto) | `.gitpr.pr.md` |
| `gitpr -r` / `gitpr -f` | `.gitpr.review.md` |
| `gitpr -r -i arquivo` | `.gitpr.filereview.md` |
| `gitpr -is` | `.gitpr.issue.md` |
| `gitpr -b arquivo` | `.gitpr.blame.md` |
| `gitpr -l` / `gitpr -r` | `.gitpr.linter.yml` |

Si el archivo de skill no existe, GitPR usa una plantilla interna por defecto.

---

## 3. Ejemplo de Personalización

**Archivo `.gitpr.commit.md`:**

```markdown
Todos los mensajes de commit DEBEN:
- Usar prefijo JIRA obligatorio: [PROJ-1234]
- Seguir Conventional Commits (feat, fix, refactor...)
- Estar escritos en portugués (Brasil)
- No exceder 72 caracteres en la línea de asunto
```

Después de crear este archivo, todas las ejecuciones de `gitpr -c` seguirán estas reglas.

---

## 4. Plantillas Remotas

Las plantillas oficiales están disponibles en:
```
https://github.com/gitpr-cli/gitpr/tree/main/templates/
```

El comando `--skill` descarga la versión más reciente de cada plantilla del repositorio oficial.

> **Nota:** Los archivos de skill pueden commitearse en el repositorio de tu equipo para compartir las reglas con todos los developers.

---

## 5. Editar desde la pantalla `gitpr config`

La pantalla `gitpr config` tiene una sección **Skills** que lista estos mismos archivos y abre cada uno en un editor, para ajustar una regla sin salir del terminal ([Pantalla de Configuración Interactiva](config-tui.es_es.md), §1.7).

- Una entrada por skill soportada por GitPR — los siete archivos `.gitpr.*.md` de la sección 1 anterior.
- Una skill que el proyecto todavía no tiene se lista como **no está en este proyecto**, con un botón **📥 Descargar la plantilla** que trae la plantilla publicada para su idioma de interfaz.
- `F2` guarda las skills editadas junto con los ajustes del `.env`; `Ctrl+R` dentro del panel descarta la edición y devuelve el texto del disco.
- Cada archivo conserva los finales de línea que ya tenía, así que guardar nunca convierte una línea intacta en un cambio.

Dos cosas quedan fuera de esa lista a propósito: el `.gitpr.linter.yml`, que ningún comando carga por este mecanismo ([Reglas Personalizadas del Linter](linter-regras-customizadas.es_es.md)), y cualquier otro archivo que guarde en `.gitpr/skill/` — la pantalla ofrece las skills que leen los comandos, no todo lo que contiene la carpeta.
