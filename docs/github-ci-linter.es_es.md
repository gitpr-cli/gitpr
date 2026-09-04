# **Documentación Técnica: Integración de Linter Local con GitHub Actions**

Esta documentación describe el proceso de implementación de `gitpr --linter` como un "Quality Gate" en el ciclo de vida de desarrollo, impidiendo que el código que viole las reglas estáticas del proyecto se fusione en la rama principal.

---

## **1. Funcionamiento Técnico**

El comando `gitpr --linter` está diseñado para operar con **códigos de salida (exit codes)** semánticos:

* **Exit Code 0:** Éxito. No se encontraron violaciones.  
* **Exit Code 1:** Fallo. Violaciones detectadas (bloquea el workflow de GitHub).

A diferencia de los modos de IA, el modo linter no requiere claves de API, lo que lo hace ideal para entornos de ejecución efímeros.

---

## **2. Configuración del Workflow (.yml)**

Cree el archivo `.github/workflows/gitpr-linter.yml` en su repositorio con la configuración a continuación. Esta acción se activará en todas las solicitudes de extracción (Pull Requests) dirigidas a las ramas `main` o `develop`.

```yaml
name: 🛡️ GitPR Static Analysis

on:  
  pull_request:  
    branches: [ "main", "develop" ]

jobs:  
  linter-validation:  
    runs-on: ubuntu-latest  
      
    steps:  
      - name: 📥 Clonar el Repositorio  
        uses: actions/checkout@v4  
        with:  
          # Necesario para permitir el 'git diff' contra la rama base  
          fetch-depth: 0 

      - name: 🐍 Configurar Entorno de Python  
        uses: actions/setup-python@v5  
        with:  
          python-version: '3.12'

      - name: ⚙️ Instalación de Dependencias  
        run: |  
          git clone https://github.com/gitpr-cli/gitpr.git.git /tmp/gitpr  
          pip install google-genai python-dotenv click cryptography pyyaml

      - name: 🚨 Ejecución del Linter Local  
        # El workflow fallará automáticamente si el código de salida es 1  
        run: python /tmp/gitpr/src/main.py --linter
```

---

## **3. Bloqueo del Botón de Merge (Branch Protection)**

Simplemente configurar el archivo `.yml` no impide físicamente el merge; solo indica el fallo. Para "bloquear" el botón de merge, siga estos pasos en la interfaz de GitHub:

1. Vaya a **Settings** > **Branches**.  
2. En **Branch protection rules**, haga clic en **Add rule** (o Edit en la regla de `main`).  
3. Marque la opción: **"Require status checks to pass before merging"**.  
4. En el campo de búsqueda que aparecerá, busque: `linter-validation` (o el nombre del job definido en su YAML).  
5. Marque también **"Require branches to be up to date before merging"** para garantizar que el diff probado sea el más reciente.  
6. Haga clic en **Save changes**.

---

## **4. Beneficios de la Implementación**

* **Cero Latencia de IA:** La validación se basa en Regex local, tomando milisegundos.  
* **Cero Coste:** No consume tokens de la API de Gemini.  
* **Seguridad:** Bloquea cadenas sensibles (contraseñas, IPs de prueba, registros de depuración) antes del Code Review humano.
