# Documentación Técnica: SCM Multi-Forge (ScmProvider)

GitPR publica Pull Requests e issues a través de una única abstracción, el `ScmProvider`, que admite cuatro forges de alojamiento Git: GitHub, GitLab, Bitbucket Cloud y Azure DevOps. Todos los flujos de publicación — el publicador interactivo de PR (modo predeterminado), la publicación directa (`--no-edit`) y la TUI de issues (`-is`) — resuelven el provider **del repositorio en el que se ejecutan** y llaman a la API del forge a través de él.

El forge pertenece al repositorio, no a la máquina: GitPR lo detecta a partir del remote `origin` (o lee un override explícito versionado con el proyecto) y mantiene **un token cifrado por forge** en `~/.gitpr/.env`. Una máquina puede, por tanto, trabajar con un repositorio GitLab y un repositorio GitHub al mismo tiempo, cada uno con su propia credencial.

Sin configuración de SCM, GitPR mantiene el comportamiento heredado exclusivo de GitHub — cero migración y salida byte-idéntica.

---

## 1. Forges Admitidos

| Forge | Clave del provider | Base de API predeterminada | Autenticación |
| --- | --- | --- | --- |
| GitHub | `github` | `https://api.github.com` | Personal Access Token (PAT) |
| GitLab | `gitlab` | `https://gitlab.com/api/v4` | Personal Access Token (PAT) |
| Bitbucket Cloud | `bitbucket` | `https://api.bitbucket.org/2.0` | Usuario + App Password (HTTP Basic) |
| Azure DevOps | `azure_devops` | `https://dev.azure.com` | Personal Access Token (PAT) |

### 1.1 Qué Forge Usa un Repositorio

El forge se resuelve por repositorio, en este orden:

1. **Override del proyecto** — `scm.provider` en `.gitpr/conf/gitpr.config.yml`, versionado con el repositorio. Siempre gana, y es así como se corrige un host self-managed cuyo dominio no nombra el forge.
2. **Detección del remote origin** — coincidencia de subcadena, sin distinguir mayúsculas de minúsculas, en la URL del `origin`.
3. **`github`** — el valor predeterminado histórico.

| La URL del remote contiene | Provider |
| --- | --- |
| `gitlab` | `gitlab` |
| `bitbucket` | `bitbucket` |
| `dev.azure.com` o `visualstudio.com` | `azure_devops` |
| cualquier otra cosa (por defecto) | `github` |

```yaml
# .gitpr/conf/gitpr.config.yml — versiónalo para compartir el forge con el equipo
scm:
  provider: gitlab
```

Un valor desconocido en el archivo de proyecto se ignora con una advertencia (un archivo malformado nunca puede tumbar todos los comandos), y la detección decide en su lugar.

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
| 1. Detección del forge | Detecta el forge a partir del remote `origin` y pide confirmación (puedes elegir otro forge; un host que no nombra forge se pregunta, nunca se presume) |
| 2. Extras del provider | Azure DevOps pide `organization` y `project`; Bitbucket pide el `username`, que forma parte de la credencial |
| 3. Base de API | Base de API personalizada para todos los forges excepto GitHub; el valor ya guardado para ese forge se ofrece como predeterminado |
| 4. Token | Pide el PAT — o la App Password en Bitbucket |
| 5. Validación | `test_connection()` — hasta 3 intentos; HTTP 401 (token caducado) vuelve a solicitarlo en amarillo; el resto de fallos aborta en rojo |
| 6. Persistencia | Solo en caso de éxito: escribe el token cifrado con Fernet en el slot de su forge (`GITLAB_TOKEN_ENCRYPTED`, …), la base de API y los extras, y registra `scm.provider` en el archivo de proyecto **solo cuando el forge elegido difiere del detectado** |

No se escribe nada cuando la validación falla. Ejecuta `gitpr --init` de nuevo en cada repositorio para cambiar de forge o renovar un token caducado; los tokens de los demás forges quedan intactos. Los valores de versiones anteriores (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`) se migran automáticamente en el primer comando tras la actualización.

---

## 3. Configuración Manual (.env)

Alternativa al wizard: edita `~/.gitpr/.env` directamente. Consulta la [guía de integración del GitHub PAT](github-pat-integration.md) para entender cómo GitPR protege los tokens en reposo.

| Variable | Forge | Descripción |
| --- | --- | --- |
| `GITPR_SCM_TOKEN` | todos | Token crudo, solo para entornos de CI/CD — único y global, se consulta antes que cualquier token guardado |
| `GITHUB_TOKEN_ENCRYPTED` | `github` | Token cifrado con Fernet del forge GitHub |
| `GITLAB_TOKEN_ENCRYPTED` | `gitlab` | Token cifrado con Fernet del forge GitLab |
| `BITBUCKET_TOKEN_ENCRYPTED` | `bitbucket` | Token cifrado con Fernet del forge Bitbucket |
| `AZURE_DEVOPS_TOKEN_ENCRYPTED` | `azure_devops` | Token cifrado con Fernet del forge Azure DevOps |
| `GITHUB_BASE_URL` / `GITLAB_BASE_URL` / `BITBUCKET_BASE_URL` / `AZURE_DEVOPS_BASE_URL` | forge propio | Base de API personalizada (self-managed/enterprise); vacía = SaaS público |
| `GITPR_SCM_ORGANIZATION` | `azure_devops` | Nombre de la organización — obligatorio (el error fail-fast indica la variable ausente) |
| `GITPR_SCM_PROJECT` | `azure_devops` | Nombre del proyecto — obligatorio |
| `GITPR_SCM_USERNAME` | `bitbucket` | Usuario de Bitbucket — obligatorio (App Password usa HTTP Basic) |

Cada forge lee solo su propio slot: un token de GitLab nunca responde por un repositorio de GitHub. GitHub sin configuración de SCM mantiene `GITHUB_TOKEN_ENCRYPTED` — cero migración.

### 3.1 Nota de Migración: Aprovisionamiento Automatizado y Slots por Forge

> [!WARNING]
> **Nota de Migración para Scripts de Aprovisionamiento e Infraestructura:**  
> Las claves globales heredadas `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` y `GITPR_SCM_BASE_URL` han sido dadas de baja de forma permanente. La migración automática en tiempo de ejecución elimina estas líneas de `~/.gitpr/.env` en la primera ejecución.  
> 
> Los scripts de aprovisionamiento automatizado de máquinas (Ansible, Docker, devcontainers, dotfiles o bootstrapping de VMs) ahora deben rellenar directamente los slots específicos de cada forge:
> - GitHub: `GITHUB_TOKEN_ENCRYPTED` (y opcionalmente `GITHUB_BASE_URL`)
> - GitLab: `GITLAB_TOKEN_ENCRYPTED` (y opcionalmente `GITLAB_BASE_URL`)
> - Bitbucket: `BITBUCKET_TOKEN_ENCRYPTED` (y `GITPR_SCM_USERNAME`)
> - Azure DevOps: `AZURE_DEVOPS_TOKEN_ENCRYPTED` (y `GITPR_SCM_ORGANIZATION` + `GITPR_SCM_PROJECT`)
> 
> Para servidores autohospedados (self-hosted) en dominios personalizados, configure el override en el archivo del proyecto en `.gitpr/conf/gitpr.config.yml` (`scm.provider: <forge>`) en lugar de intentar definir un proveedor global en `.env`. Los entornos CI efímeros deben continuar utilizando `GITPR_SCM_TOKEN` (token plano sin cifrar). Detalles de arquitectura en [ADR-0020](adr/0020-per-repo-scm-provisioning-migration.md) y [ADR-016](plans/ADR-016-per-provider-scm-settings.md).

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

Cuando el token es rechazado (HTTP 401), GitPR elimina el token caducado del slot de **ese** forge y pide uno nuevo — hasta 3 intentos. Prefiere los flujos interactivos (`gitpr`, `gitpr -is`) para reautenticarte: `--no-edit` publica directamente y no puede volver a solicitarlo.

Una ejecución no interactiva (hooks de git, servidor MCP, CI) nunca pregunta y nunca borra la credencial guardada: se detiene con un mensaje que indica `gitpr --init` en ese repositorio.

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

### 6.1 Contrato para Proveedores de Terceros (cambio incompatible desde la v1.2.0)

`ScmProvider.request_pull_request_reviewers()` devolvía `None`. Desde la **v1.2.0** devuelve `list[str]`: los logins que el forge **realmente asoció**, releídos del cuerpo de la respuesta. Una lista vacía significa "aceptado pero ignorado": así detecta GitPR un revisor que el forge descartó en silencio.

| | Hasta la v1.1.x | Desde la v1.2.0 |
| --- | --- | --- |
| Tipo de retorno | `None` | `list[str]` (logins asociados) |
| `[]` | — | Solicitud aceptada, nadie asociado |
| Valor por defecto en la clase base | `ScmNotSupportedError` | `ScmNotSupportedError` (sin cambios) |

**Quién se ve afectado:** solo las subclases que **sobrescriben** el método. Quien únicamente lo llama no se ve afectado. Una subclase que no lo sobrescribe sigue lanzando `ScmNotSupportedError`, como antes.

**Cómo migrar:** devuelva lo que el forge asoció. Si el forge no devuelve cuerpo, devuelva la lista que se le pidió asociar: es optimista y desactiva el aviso de "no asociado" para ese forge.

```python
class MyForgeProvider(ScmProvider):
    def request_pull_request_reviewers(self, repo, pr_id, reviewers) -> list[str]:
        body = self._post_reviewers(repo, pr_id, reviewers)
        return [r["login"] for r in body.get("requested_reviewers", [])]
        # ¿El forge no devuelve cuerpo? Use `return list(reviewers)`.
```

Una sobrescritura heredada que aún devuelve `None` sigue funcionando: el llamador la interpreta como "no se puede verificar" y omite el aviso de "no asociado". Se tolera, no se recomienda. Registro de la decisión: [ADR-0009](adr/0009-reviewer-attach-returns-read-back.md).

Registro de decisión de arquitectura y vocabulario canónico: [ADR-001 Abstracción SCM](plans/ADR-001-scm-abstraction.md) y [Glosario SCM Multi-Forge](plans/glossary-scm-multiforge.md).

> **Nota:** Consulta también la [documentación de integración del GitHub PAT](github-pat-integration.md) para crear tokens y comprender el cifrado de GitPR (Fernet).
