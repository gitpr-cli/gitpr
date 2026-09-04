# Documentación Técnica: Sistema de Skills y Plantillas (--skill)

GitPR utiliza un sistema de **Skills** (Prompt Engineering) que permite personalizar el comportamiento de la inteligencia artificial de acuerdo con las reglas de negocio de tu empresa. Los archivos de plantilla actúan como *System Instructions* de la IA.

---

## 1. Descargar las Plantillas

```bash
gitpr -s
# o
gitpr --skill
```

Este comando crea los siguientes archivos en la raíz de tu proyecto:

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
https://github.com/gitpr-cli/gitpr.git/tree/main/templates/
```

El comando `--skill` descarga la versión más reciente de cada plantilla del repositorio oficial.

> **Nota:** Los archivos de skill pueden commitearse en el repositorio de tu equipo para compartir las reglas con todos los developers.
