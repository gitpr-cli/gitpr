# Documentación Técnica: Revisores Sugeridos para Pull Requests

Al publicar un Pull Request mediante el publicador interactivo de GitPR (el modo `gitpr` por defecto), GitPR sugiere quién debería revisarlo: busca a las personas que trabajaron en el código que está modificando y propone hasta `GITPR_REVIEWER_SUGGESTION_TOP_N` candidatos (3 por defecto). Las sugerencias aparecen en un campo editable del Publicador de PR (TUI) y, en GitHub, se envían a la nueva pull request inmediatamente después de su creación.

El cálculo está activado por defecto y solo se ejecuta en el flujo del publicador interactivo — nunca con `--no-edit` ni `--no-publish`. Es puramente orientativo y totalmente no bloqueante: cualquier fallo o situación no soportada se convierte en un aviso y el flujo de publicación continúa sin cambios.

---

## 1. Cómo Funciona

GitPR no adivina: atribuye autoría real con `git blame`, ejecutado sobre las líneas exactas que añadió su diff, comparando la rama base con su working tree.

### 1.1 Autoría sobre las Líneas Añadidas

- La entrada es el mismo diff que GitPR ya calculó para el PR: rama base vs. working tree (cambios staged incluidos), con los smart-excludes aplicados. El parser consume ese texto del diff y nunca vuelve a ejecutar `git diff`.
- Solo las **líneas añadidas** (`+`) cuentan para la autoría. Las líneas eliminadas y de contexto se ignoran.
- Las líneas aún sin commitear — "Not Committed Yet", hash de blame `0000…` — se omiten: son su propio trabajo en curso.
- El blame se ejecuta sobre la working tree (sin revisión), por lo que coincide exactamente con el diff, incluidos los archivos staged y nuevos.
- Los archivos sin historial aprovechable (nuevos, binarios, clones shallow) no generan candidatos: se muestra un aviso y el análisis continúa.

### 1.2 Clasificación y Exclusiones

Cada autor encontrado se agrega por archivo y por línea y recibe una puntuación:

| Factor | Peso | Significado |
| --- | --- | --- |
| Líneas tocadas | 50% | Proporción de las líneas añadidas del diff escritas por la persona |
| Archivos tocados | 30% | Proporción de los archivos modificados en los que la persona tiene autoría |
| Recientemente | 20% | `1 / (1 + days / 90)` — semivida de 90 días desde la última modificación |

El autor del PR siempre se excluye, incluso cuando domina el diff. También se excluyen los **bots**: cualquier identidad cuyo nombre o parte local del correo termine en `[bot]`, o cuyo correo esté en la lista de bots conocidos (Dependabot, GitHub Actions, etc.). El dominio `users.noreply.github.com` nunca se trata como un bot — es el correo estándar de los usuarios reales de GitHub. Se puede excluir a más personas mediante `GITPR_REVIEWER_SUGGESTION_EXCLUDED`. Los empates se deshacen por líneas tocadas y el resultado se trunca en el `top_n` configurado (3 por defecto).

---

## 2. Configuración

La función viene activada por defecto. Desactívela por ejecución con la flag o globalmente a través del entorno:

```bash
gitpr --no-suggest-reviewers        # Desactiva el cálculo en esta ejecución
```

```bash
# ~/.gitpr/.env — desactiva globalmente y ajusta la clasificación
GITPR_SUGGEST_REVIEWERS=false
GITPR_REVIEWER_SUGGESTION_TOP_N=5
GITPR_REVIEWER_SUGGESTION_EXCLUDED=renovate[bot],qa@example.com
```

| Variable | Predeterminado | Descripción |
| --- | --- | --- |
| `GITPR_SUGGEST_REVIEWERS` | `true` | Interruptor general. Valores falsy: `false`, `0`, `no`, `off`, `n` |
| `GITPR_REVIEWER_SUGGESTION_TOP_N` | `3` | Cuántos candidatos sugerir; inválido o ≤ 0 vuelve a 3 |
| `GITPR_REVIEWER_SUGGESTION_EXCLUDED` | *(vacío)* | CSV opcional de correos o nombres a excluir, además del autor del PR y de los bots |

Las claves se leen de `~/.gitpr/.env` y nunca se escriben automáticamente. `--no-edit` y `--no-publish` nunca calculan sugerencias, independientemente de la configuración.

---

## 3. Revisores Sugeridos en el Publicador de PR (TUI)

### 3.1 La Sección de Revisores Sugeridos

En el flujo interactivo por defecto, GitPR muestra la línea `🔍 Buscando revisores sugeridos...` mientras se ejecuta el análisis, antes de que se abra el Publicador de PR. Cuando se abre, se muestra una sección editable **👥 Revisores Sugeridos**:

- Un campo de entrada rellenado previamente con los usuarios sugeridos de GitHub, separados por comas. Elimine un revisor vaciando el campo; añada uno escribiendo.
- Una indicación de solo lectura bajo el campo que explica cada sugerencia (líneas y archivos tocados, última actividad).
- Dejar el campo vacío no envía ningún revisor.

### 3.2 Publicación

Tras confirmar con F3, GitPR crea la pull request y después solicita los revisores aceptados en GitHub a través del endpoint `requested_reviewers` (`POST .../pulls/{number}/requested_reviewers`). El attach ocurre tanto en la ruta de creación como en la de actualización y **nunca es fatal**: si GitHub rechaza la solicitud — por ejemplo, un handle inválido escrito a mano, respondido con HTTP 422 — el PR permanece publicado y la TUI muestra un aviso (`⚠️ PR publicado, pero no se pudieron solicitar los revisores: {error}`).

### 3.3 Ayuda Contextual

La flag participa en el sistema de ayuda contextual:

```bash
gitpr -h --no-suggest-reviewers
```

---

## 4. Soporte y Limitaciones por Forge

| Forge | Sugerencia | Envío |
| --- | --- | --- |
| GitHub | Se muestra y es editable | Sí — se solicita vía `requested_reviewers` después de crear o actualizar el PR |
| GitLab | Solo se muestra localmente | No — sin endpoint equivalente |
| Bitbucket Cloud | Solo se muestra localmente | No — sin endpoint equivalente |
| Azure DevOps | Solo se muestra localmente | No — sin endpoint equivalente |

En los forges que no son GitHub, el campo de entrada no se muestra; la sección presenta a los candidatos con una nota de que la sugerencia es solo local. Para convertir los correos de GitHub en nombres de usuario, GitPR resuelve cada candidato con best-effort y nunca se bloquea en ello: los correos del dominio `users.noreply.github.com` se convierten directamente en un handle y cualquier otro correo recurre al fallback `/search/users in:email` de GitHub. Los candidatos cuyo correo GitHub no reconoce aparecen con nombre y correo y simplemente no se rellenan previamente — siempre puede escribir su handle.

Recibir menos sugerencias que `top_n` es normal: archivos sin historial, archivos binarios, un diff sin líneas añadidas o un repositorio recién creado producen resultados vacíos o parciales con un aviso — nunca un error. El análisis nunca se ejecuta en los flujos `--no-edit`/`--no-publish`, por lo que los pipelines automatizados no se ven afectados.

---

## 5. Para Desarrolladores y Plugins

El use case vive en cuatro módulos planos en `src/`: `reviewer_suggestion.py` contiene el dominio puro (dataclasses, pesos, lista de bots, `rank_reviewers()` — sin git, sin red), `diff_parser.py` implementa `parse_added_lines()` sobre el texto del diff, `blame_engine.py` ganó la fina `get_blame_for_range()` (el flujo de la arqueología no se refactorizó) y `suggest_reviewers.py` lo orquesta todo con `compute_reviewer_suggestions()`, que **nunca lanza excepción**. Las tres claves `GITPR_*` anteriores se declaran en `DEFAULT_CONFIG` en `src/config.py`, con `suggest_reviewers_enabled()` y `get_reviewer_suggestion_settings()`.

En el lado del SCM, el contrato base `ScmProvider` ganó un método **no abstracto** `request_pull_request_reviewers(repo, pr_id, reviewers)` cuyo comportamiento por defecto lanza `ScmNotSupportedError`; solo `github_provider.py` lo implementa, junto con `email_to_handle()`, exclusivo de GitHub. `main.py` restringe el cálculo al flujo TUI por defecto y entrega a la app un dict de vista `{"handles", "lines", "submittable", "note"}`. Todo el texto visible pasa por claves i18n `__()`, por lo que los 5 paquetes de idioma deben permanecer sincronizados cuando cambian los mensajes.

Registro de decisión de arquitectura y vocabulario canónico: [ADR-002 Sugerencia de Revisores](plans/ADR-002-reviewer-suggestion.md) y [Glosario de Sugerencia de Revisores](plans/glossary-reviewer-suggestion.md).

> **Nota:** Consulte también la [documentación de publicación de pull requests](pull-request-publication.md) para conocer el flujo completo de publicación, sus modos y sus flags.
