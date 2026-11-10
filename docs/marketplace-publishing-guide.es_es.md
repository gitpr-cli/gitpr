# Guía de Publicación y Configuración en Marketplaces (VS Code y Cursor)

Esta guía proporciona instrucciones paso a paso para publicar la **Extensión de Editor de GitPR** en el **Visual Studio Marketplace** (para VS Code) y en el **Open VSX Registry** (para Cursor y otros editores de código abierto).

---

## Visión General

La publicación está completamente automatizada mediante GitHub Actions (`.github/workflows/extension.yml`). Cuando se envía una etiqueta (tag) de release oficial (`ext-v*`), el flujo de trabajo:
1. Valida que la versión de la etiqueta git coincida estrictamente con el campo `"version"` en `extensions/vscode/package.json`.
2. Compila TypeScript y ejecuta los tests de integración de Mocha.
3. Empaqueta la extensión en un paquete `.vsix` que contiene el icono oficial y la licencia.
4. **Crea un GitHub Release oficial** con el paquete `.vsix` adjunto permanentemente para descarga directa.
5. Evalúa `VSCE_PAT` y `OVSX_PAT` de forma independiente (**Granular Marketplace Gate**):
   - Si `VSCE_PAT` está configurado, publica en Visual Studio Marketplace.
   - Si `OVSX_PAT` está configurado, publica en Open VSX Registry.
   - Si falta alguno de los secretos, registra un aviso informativo y una tabla de resumen en el flujo sin bloquear el GitHub Release.

---

## 1. Configuración de Visual Studio Marketplace (Microsoft / VS Code)

### Paso 1.1: Organización en Azure DevOps
1. Inicie sesión en [Azure DevOps](https://dev.azure.com) con la cuenta Microsoft que gestiona la extensión de GitPR.
2. Si aún no tiene una organización, cree una (por ejemplo, `natanfiuza` o el nombre de organización de desarrollo elegido).

### Paso 1.2: Generar Personal Access Token (PAT)
1. En Azure DevOps, haga clic en el icono de engranaje **User Settings** (esquina superior derecha, junto a su foto de perfil) y seleccione **Personal access tokens**.
2. Haga clic en **+ New Token**.
3. Complete los detalles:
   - **Name**: `gitpr-marketplace-publish`
   - **Organization**: Seleccione **All accessible organizations**. *(Crucial: vsce requiere un PAT con ámbito multiorganización).*
   - **Expiration**: Seleccione 1 año (o 90 días, según sus requisitos de seguridad).
   - **Scopes**: Haga clic en **Show all scopes** en la parte inferior, desplácese hacia abajo hasta **Marketplace** y seleccione:
     - `Acquire`
     - `Manage` (permite publicar extensiones)
4. Haga clic en **Create** y **copie el PAT inmediatamente**.

### Paso 1.3: Crear Publisher en Visual Studio Marketplace
1. Vaya al [Portal de Administración de Visual Studio Marketplace](https://marketplace.visualstudio.com/manage).
2. Haga clic en **Create publisher**.
3. Introduzca los datos:
   - **ID**: `natanfiuza` *(debe coincidir con `"publisher": "natanfiuza"` en `package.json`)*.
   - **Name**: `Natan Fiuza`
   - **Email**: `contato@natanfiuza.dev.br`
4. Confirme la creación.

### Paso 1.4: Añadir el Secreto a GitHub
1. En el repositorio de GitHub, navegue a **Settings > Secrets and variables > Actions**.
2. Haga clic en **New repository secret**.
3. Nombre: `VSCE_PAT`
4. Valor: Pegue su Personal Access Token de Azure DevOps.

---

## 2. Configuración de Open VSX Registry (Eclipse Foundation / Cursor)

El Open VSX Registry proporciona la búsqueda de extensiones en Cursor, VSCodium, Gitpod y otros IDEs de código abierto.

### Paso 2.1: Crear Cuenta
1. Vaya a [open-vsx.org](https://open-vsx.org) e inicie sesión utilizando su cuenta de GitHub (`natanfiuza`).

### Paso 2.2: Registrar el Namespace
1. Vaya a la sección [Open VSX Namespaces](https://open-vsx.org/user-settings/namespaces) o solicite la creación del namespace `natanfiuza`.
2. Si la creación autoservicio está disponible en la configuración de usuario, cree el namespace `natanfiuza` *(debe coincidir con `"publisher": "natanfiuza"` en `package.json`)*.
3. Si la titularidad del namespace requiere verificación, vincule su organización de GitHub o perfil personal según las indicaciones de Open VSX.

### Paso 2.3: Generar Access Token
1. Vaya a [User Settings > Access Tokens](https://open-vsx.org/user-settings/tokens) en open-vsx.org.
2. Cree un nuevo token (por ejemplo, `gitpr-ovsx-token`).
3. Copie la cadena de texto del token generado.

### Paso 2.4: Añadir el Secreto a GitHub
1. En el repositorio de GitHub, navegue a **Settings > Secrets and variables > Actions**.
2. Haga clic en **New repository secret**.
3. Nombre: `OVSX_PAT`
4. Valor: Pegue su Access Token de Open VSX.

---

## 3. Verificación Local y Dry-Run (Opcional)

Antes de activar el release público, puede probar la autenticación y el empaquetado localmente:

### Verificar PATs con las CLIs
```bash
cd extensions/vscode

# Probar PAT de Visual Studio Marketplace
npx @vscode/vsce verify-pat natanfiuza -p "<SU_VSCE_PAT>"

# Probar PAT de Open VSX
npx ovsx verify-pat -p "<SU_OVSX_PAT>"
```

### Test Local de Empaquetado
```bash
npm run compile
npm test
npm run package
```
Esto genera `gitpr-0.1.0.vsix` conteniendo `images/icon.png`, `LICENSE.txt`, bundles compilados y archivos de manifiesto.

---

## 4. Activación del Release Automatizado

Cuando esté listo para publicar un nuevo release:

1. Asegúrese de que `extensions/vscode/package.json` tenga la versión que desea publicar (por ejemplo, `"version": "0.1.0"`).
2. Confirme (commit) cualquier cambio pendiente en `main` o en su rama de release.
3. Cree y envíe una etiqueta git anotada que coincida con `ext-v<versión>`:
   ```bash
   git tag ext-v0.1.0
   git push origin ext-v0.1.0
   ```
4. GitHub Actions ejecutará el flujo de trabajo **Editor Extension**:
   - Valida que `ext-v0.1.0` coincida con `0.1.0`.
   - Ejecuta las pruebas y compila el VSIX.
   - **Crea el GitHub Release** con `gitpr-0.1.0.vsix` adjunto como asset.
   - Publica automáticamente en Visual Studio Marketplace y/o Open VSX Registry si sus respectivos secretos (`VSCE_PAT`, `OVSX_PAT`) están configurados. Si aún no están configurados, el VSIX permanece disponible en GitHub Releases y la publicación en marketplaces se activará una vez añadidos los secretos.

---

## 5. Mantenimiento y Próximos Releases

- **Incremento de versión**: Actualice `"version"` en `extensions/vscode/package.json` y envíe la etiqueta correspondiente (por ejemplo, `ext-v0.1.1`).
- **Expiración de tokens**: Los PATs de Azure DevOps expiran después de un máximo de 1 año. Recuerde regenerar `VSCE_PAT` y actualizar el secreto del repositorio antes de su vencimiento.
