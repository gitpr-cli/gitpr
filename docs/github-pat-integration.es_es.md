# Documentación Técnica: Integración y Seguridad del Token de GitHub (PAT)

Para que la funcionalidad de creación directa de Issues (`gitpr --issue`) funcione de forma automatizada, GitPR necesita comunicarse con la **API REST de GitHub**. Esta documentación explica cómo se produce esta autenticación y cómo se protegen tus credenciales localmente.

📖 **Documentación relacionada:** [Guía de la opción `--issue` (gitpr-issue-option.md)](gitpr-issue-option.md)

## 1. ¿Por qué necesitamos un Token (PAT)?
La creación de issues en repositorios remotos de forma programática requiere autenticación. GitHub recomienda utilizar un **Personal Access Token (PAT)** para que las herramientas de línea de comandos (CLI) puedan interactuar con tu cuenta de desarrollador de forma segura.

## 2. Ámbito Necesario (`repo`)
GitPR solo necesita el ámbito **`repo`** habilitado en el momento de la creación de tu PAT. Esto garantiza el permiso para leer los metadatos y crear la Issue en el proyecto correcto (ya sea privado o público).
Para agilizar este proceso, el propio CLI genera una URL de configuración dinámica. Extrae el nombre de tu repositorio local y compone un enlace que se abre en tu navegador con las opciones correctas ya preseleccionadas.

## 3. Seguridad y Cifrado Local (Design Patterns)
La seguridad de tus credenciales se trata con extrema seriedad. GitPR **nunca** envía tu clave a servidores de terceros que no sean la propia API de GitHub.

* **Cifrado Simétrico (Fernet):** En cuanto pegas tu Token en el terminal, GitPR utiliza la biblioteca nativa `cryptography` para cifrar la cadena en tiempo real.
* **Almacenamiento Seguro:** El token cifrado se guarda de forma permanente en el archivo global `~/.gitpr/.env` (en la carpeta raíz de tu usuario, inaccesible para otros usuarios del sistema operativo).
* **Clave Maestra de Descifrado:** La clave maestra necesaria para revertir este cifrado permanece aislada en tu máquina local (`~/.gitpr/secret.key`).

Gracias a esta arquitectura, en caso de que se produzca una fuga local y un script malicioso lea tu archivo `.env`, tu Token de GitHub seguirá siendo absolutamente ilegible y estará protegido.