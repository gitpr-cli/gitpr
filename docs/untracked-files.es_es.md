# ⚠️ ¿Por qué GitPR ignoró mis archivos nuevos?

Si ejecutaste GitPR y recibiste un aviso de que se detectaron **archivos no monitorizados (untracked)**, ¡no te preocupes! Este es un comportamiento de seguridad y optimización nativo del sistema.

## 🔍 ¿Qué significa "No Monitorizado"?

Cuando creas un archivo nuevo en tu proyecto, Git no lo rastrea automáticamente. Queda en el estado *Untracked*. El comando que GitPR usa para leer tu código (`git diff HEAD`) analiza únicamente los archivos que Git ya conoce o que se han preparado para el commit (*Staged*).

## 🛡️ ¿Por qué GitPR no lee esos archivos automáticamente?

Diseñamos GitPR teniendo en mente tres pilares:
1. **Seguridad (Prevención de Fugas):** Imagina que creas un archivo `.env.local` con contraseñas de la base de datos de producción y olvidas añadirlo al `.gitignore`. Si GitPR leyera todo automáticamente, enviaría tus contraseñas a la API de la IA.
2. **Ahorro de Tokens (Dinero):** Algunos frameworks generan carpetas gigantes de caché o archivos compilados. Enviar basura a la IA consumiría tus tokens innecesariamente y haría la respuesta extremadamente lenta.
3. **Estándar Git:** GitPR respeta el ciclo de vida oficial de Git. La IA solo analiza lo que tú, como desarrollador, decides que tiene valor.

## ✅ ¿Cómo resolverlo?

La solución es muy sencilla. Solo tienes que indicarle a Git qué archivos nuevos forman parte de tu próximo commit usando el comando `add`:

```bash
# Para añadir un archivo específico:
git add src/meu_novo_arquivo.py

# O para añadir todos los archivos nuevos de una vez:
git add .

```

Después de ejecutar `git add`, basta con ejecutar el comando de **GitPR** de nuevo. ¡La IA ahora verá tus novedades y generará el análisis perfectamente! 🚀

## 🔎 Verificación Rápida: ¿Qué archivos no están en stage?

Puedes verificar rápidamente qué archivos no están en stage usando la flag `--status` — **sin IA, sin red, instantáneo**:

```bash
gitpr --status
```

Esto muestra todos los cambios no commiteados en 3 categorías: nuevos (no rastreados), modificados y eliminados. Consulta la [documentación de Git Status](git-status.es_es.md) para más detalles.

## 🛑 Omitir la verificación de unstaged

Si quieres omitir la verificación de archivos unstaged que se ejecuta antes de los comandos de IA, usa:

```bash
gitpr -c --no-unstaged-check
```

O define `GITPR_SKIP_UNSTAGED_CHECK=true` en tu archivo `~/.gitpr/.env` para omitirla permanentemente.

> 📖 **Documentación completa:** [docs/git-status.es_es.md](git-status.es_es.md) — cubre `--status`, `--no-unstaged-check`, herramientas MCP y la verificación de unstaged que ahora se ejecuta en todos los comandos (`-c`, `-r`, `-f`, `-is`).
