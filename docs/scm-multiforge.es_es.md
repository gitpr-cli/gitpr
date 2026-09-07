# Documentación Técnica: SCM Multi-Forge (ScmProvider)

GitPR publica Pull Requests e issues a través de una única abstracción, el `ScmProvider`, que admite cuatro forges de alojamiento Git: GitHub, GitLab, Bitbucket Cloud y Azure DevOps. Todos los flujos de publicación — el publicador interactivo de PR (modo predeterminado), la publicación directa (`--no-edit`) y la TUI de issues (`-is`) — resuelven el provider configurado a partir del remote `origin` del repositorio y llaman a la API del forge a través de él.

Sin configuración de SCM, GitPR mantiene el comportamiento heredado exclusivo de GitHub — cero migración y salida byte-idéntica.

---

## 1. Forges Admitidos

| Forge | Clave del provider | Base de API predeterminada | Autenticación |
| --- | --- | --- | --- |
| GitHub | `github` | `https://api.github.com` | Personal Access Token (PAT) |
| GitLab | `gitlab` | `https://gitlab.com/api/v4` | Personal Access Token (PAT) |
| Bitbucket Cloud | `bitbucket` | `https://api.bitbucket.org/2.0` | Usuario + App Password (HTTP Basic) |
| Azure DevOps | `azure_devops` | `https://dev.azure.com` | Personal Access Token (PAT) |

### 1.1 Detección Automática a partir del Remote Origin

El forge activo se detecta a partir de la URL del remote `origin` mediante una coincidencia de subcadena sin distinguir mayúsculas de minúsculas:

| La URL del remote contiene | Provider |
| --- | --- |
| `gitlab` | `gitlab` |
| `bitbucket` | `bitbucket` |
| `dev.azure.com` o `visualstudio.com` | `azure_devops` |
| cualquier otra cosa (por defecto) | `github` |

```bash
git remote get-url origin
# git@github.com:gitpr-cli/gitpr.git               -> github (por defecto)
# https://gitlab.com/acme/platform/web-app.git     -> gitlab
# https://bitbucket.org/acme/web-app               -> bitbucket
# https://dev.azure.com/acme/project/_git/web-app  -> azure_devops
```

El repositorio se direcciona mediante `RepoRef`, extraído de la URL del remote. El **workspace** es el propietario (owner) de GitHub, el namespace de GitLab (subgrupos incluidos), el workspace de Bitbucket o — en Azure DevOps — una etiqueta `{org}/{project}` solo para visualización, porque las llamadas a la API usan el `organization` y el `project` de la configuración.

---

## 2. Configuración Inicial — `gitpr --init`

El wizard interactivo detecta el forge, valida el token de acceso y persiste la configuración:

```bash
gitpr --init
```

| Paso | Qué ocurre |
| --- | --- |
| 1. Detección del forge | Detecta el forge a partir del remote `origin` y pide confirmación (puedes elegir otro forge) |
| 2. Extras del provider | Azure DevOps pide `organization` y `project`; Bitbucket pide el `username`, que forma parte de la credencial |
| 3. Base de API | Base de API personalizada para todos los forges excepto GitHub (GitLab/Azure DevOps self-managed, enterprise) |
| 4. Token | Pide el PAT — o la App Password en Bitbucket |
| 5. Validación | `test_connection()` — hasta 3 intentos; HTTP 401 (token caducado) vuelve a solicitarlo en amarillo; el resto de fallos aborta en rojo |
| 6. Persistencia | Solo en caso de éxito: escribe `GITPR_SCM_PROVIDER`, el token cifrado con Fernet y los extras en `~/.gitpr/.env` |

No se escribe nada cuando la validación falla. Ejecuta `gitpr --init` de nuevo en cualquier momento para cambiar de forge o renovar un token caducado.

---

## 3. Configuración Manual (.env)

Alternativa al wizard: edita `~/.gitpr/.env` directamente. Consulta la [guía de integración del GitHub PAT](github-pat-integration.md) para entender cómo GitPR protege los tokens en reposo.

| Variable | Forge | Descripción |
| --- | --- | --- |
| `GITPR_SCM_PROVIDER` | todos | Clave del provider activo (`github`, `gitlab`, `bitbucket`, `azure_devops`); vacía = comportamiento heredado de GitHub |
| `GITPR_SCM_TOKEN` | todos | Token crudo, solo para entornos de CI/CD |
| `GITPR_SCM_TOKEN_ENCRYPTED` | todos | Token cifrado con Fernet, escrito por `gitpr --init` y por el flujo de reautenticación |
| `GITPR_SCM_BASE_URL` | todos | Base de API personalizada (self-managed/enterprise); vacía = SaaS público |
| `GITPR_SCM_ORGANIZATION` | `azure_devops` | Nombre de la organización — obligatorio (el error fail-fast indica la variable ausente) |
| `GITPR_SCM_PROJECT` | `azure_devops` | Nombre del proyecto — obligatorio |
| `GITPR_SCM_USERNAME` | `bitbucket` | Usuario de Bitbucket — obligatorio (App Password usa HTTP Basic) |

GitHub sin configuración de SCM mantiene el almacenamiento heredado `GITHUB_TOKEN_ENCRYPTED` — cero migración.

---

## 4. Uso de GitPR con el Forge Configurado

### 4.1 Publicación de Pull Requests

```bash
gitpr                # Publicador interactivo (TUI) — revisa y confirma el PR
gitpr --no-edit      # Publica directamente, con auto-commit (omite la TUI)
gitpr --no-publish   # Genera solo el archivo de descripción del PR (.md), sin TUI
```

El publicador resuelve el provider a partir del remote `origin`, convierte el repositorio en un `RepoRef` y crea el pull request mediante `provider.create_pull_request()`. El número, la URL y el estado del PR devueltos por el forge se muestran en la TUI y se guardan en el archivo de salida.

### 4.2 Issues

```bash
gitpr -is            # Flujo de issue: borrador con IA -> TUI -> F3 crea la issue en el forge
```

F3 llama a `provider.create_issue()` en el forge configurado. Azure DevOps no tiene recurso de API para issues (los Work Items dependen de la plantilla de proceso del proyecto); por eso, GitPR indica que guardes el borrador localmente con F2. Bitbucket exige que el **Issue Tracker** del repositorio esté habilitado; de lo contrario, la API responde 404.

### 4.3 Caducidad del Token y Reautenticación (HTTP 401)

Cuando el token es rechazado (HTTP 401), GitPR elimina el token caducado del `.env` y pide uno nuevo — hasta 3 intentos. Prefiere los flujos interactivos (`gitpr`, `gitpr -is`) para reautenticarte: `--no-edit` publica directamente y no puede volver a solicitarlo.

---

## 5. Notas y Limitaciones por Forge

### 5.1 GitHub

- Las instalaciones existentes mantienen el comportamiento exacto (byte-paridad): payload, cabecera `Authorization: token` y el almacenamiento heredado `GITHUB_TOKEN_ENCRYPTED` permanecen sin cambios.
- Las sugerencias de revisores son nativas (`requested_reviewers`); desactívalas con `--no-suggest-reviewers`.

### 5.2 GitLab

- Merge requests: el identificador de la API es el `iid` del MR — nunca el id global con ámbito de proyecto.
- Borradores: GitLab no tiene flag de draft al crear un MR; por eso, GitPR añade el prefijo `"Draft: "` al título.
- Las rutas de repositorio (grupos y subgrupos) siempre llevan URL-quoted.
- El parámetro de estrategia de merge se ignora — GitLab hace el merge con su acción nativa.

### 5.3 Bitbucket Cloud

- Las credenciales son HTTP Basic: usuario + App Password. El username es obligatorio (`GITPR_SCM_USERNAME`) y forma parte de la credencial.
- Las issues exigen el Issue Tracker habilitado en el repositorio.
- Estrategias de merge: `merge` -> `merge_commit`, `squash` y `fast_forward`.

### 5.4 Azure DevOps

- `organization` y `project` son obligatorios — el error fail-fast indica las variables de entorno ausentes.
- Toda llamada REST lleva `api-version=7.1`.
- Los refs de rama usan el prefijo `refs/heads/`.
- Sin diff unificado de PR vía REST: `get_pull_request_diff()` devuelve un resumen textual por archivo (`path (+adds −dels)`) de la última iteración.
- Las issues no se admiten (`ScmNotSupportedError`) — guarda el borrador localmente con F2.
- Los remotes heredados `*.visualstudio.com` son aceptados por el detector.

---

## 6. Para Desarrolladores y Plugins

La abstracción vive en `src/infrastructure/scm/`: el contrato `ScmProvider` en `base.py`, un provider concreto por forge y el registro en `factory.py`. El código interno resuelve providers solo mediante `resolve_scm_provider()` y nunca importa las clases concretas directamente. Los métodos de los providers lanzan `ScmProviderError(provider, http_status, message)` — `http_status` es `0` en fallos de red — o `ScmNotSupportedError` cuando el forge no tiene operación equivalente. Nunca devuelven las tuplas heredadas `(ok, data, status)`.

`src/github_api.py` es un **shim obsoleto**: todavía expone las cuatro funciones heredadas con retornos en tupla para integraciones de terceros, pero toda llamada lanza un `DeprecationWarning`. El código nuevo y los plugins deben usar `resolve_scm_provider()`.

Registro de decisión de arquitectura y vocabulario canónico: [ADR-001 Abstracción SCM](plans/ADR-001-scm-abstraction.md) y [Glosario SCM Multi-Forge](plans/glossary-scm-multiforge.md).

> **Nota:** Consulta también la [documentación de integración del GitHub PAT](github-pat-integration.md) para crear tokens y comprender el cifrado de GitPR (Fernet).
