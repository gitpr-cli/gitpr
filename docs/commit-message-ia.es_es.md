# Documentación Técnica: Generación de Mensajes de Commit con IA (--commit)

El comando `--commit` (`-c`) de GitPR genera automáticamente mensajes de commit con el formato **Conventional Commits** usando inteligencia artificial para analizar tus cambios locales.

---

## 1. Uso Básico

```bash
gitpr -c
```

La herramienta analiza el `git diff HEAD` y muestra el mensaje sugerido directamente en la consola:

```
📝 Sugerencia de Commit:

feat: añade validación de email en el formulario de registro

- Implementa regex de validación RFC 5322
- Añade mensajes de error localizados (pt-BR)
- Corrige edge case de emails con dominios internacionales


Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

---

## 2. Formato Conventional Commits

La IA está instruida para generar mensajes con el estándar:

```
tipo: descripción corta

Cuerpo opcional con detalles adicionales
```

**Tipos utilizados:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

---

## 3. Integración con Git Hooks

El `--commit` se usa internamente por el hook `prepare-commit-msg`. Cuando se instala con `gitpr -ih`, el hook ejecuta:

```bash
gitpr --commit --hook <caminho-do-arquivo-temporario>
```

La flag `--hook` (interna/oculta) hace que el mensaje sugerido se inyecte directamente en el editor de Git, en lugar de mostrarse en la consola.

---

## 4. Personalización mediante Skill

El comportamiento de la IA puede personalizarse a través del archivo `.gitpr.commit.md` en la raíz del proyecto:

```bash
gitpr -s          # Descarga la plantilla .gitpr.commit.md
# Edita el archivo según las convenciones de tu equipo
gitpr -c          # La IA usará tus reglas personalizadas
```

---

## 5. Selección de Proveedor de IA

```bash
gitpr -c -p gemini       # Fuerza Google Gemini
gitpr -c -p deepseek     # Fuerza DeepSeek
```

---

## 6. Caché de Respuestas

GitPR genera un hash MD5 de tu diff + instrucciones. Si ejecutas `gitpr -c` de nuevo **sin modificar el código**, la respuesta se devuelve instantáneamente desde la caché local, ahorrando cuotas de la API.

---

## 7. Firma de coautoría

Cada mensaje de commit generado por GitPR lleva automáticamente el trailer de coautoría:

```text
Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

El trailer se añade programáticamente (nunca por la IA) en todos los flujos: sugerencia en consola, hook `prepare-commit-msg`, auto-commit, TUI de publicación de PR y la herramienta MCP `generate_commit_message`. Se separa del mensaje con líneas en blanco adicionales para que no aparezca a primera vista en las vistas previas colapsadas de commits de GitHub, y nunca se duplica cuando el mensaje ya lo contiene.

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para una visión general de todas las funcionalidades.
