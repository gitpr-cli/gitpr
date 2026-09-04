# 📦 Cómo GitPR Maneja Diffs Gigantes (Map-Reduce)

Si GitPR mostró el mensaje **"📦 ¡Diff gigante detectado! Procesando en N lotes (Map-Reduce)..."**, tus cambios eran demasiado grandes para que la IA los analizara en una sola llamada. No te preocupes — nada se pierde. Esta página explica qué ocurre entre bastidores.

## 🔍 ¿Por qué hay un límite de tamaño?

Los modelos de IA tienen una ventana de contexto limitada. GitPR estima el tamaño de tu diff usando la regla segura de **4 caracteres por token**. Cuando la estimación supera los **90.000 tokens** (unos 360.000 caracteres), una sola llamada a la API podría fallar, truncar el análisis o producir resultados de baja calidad.

## ⚙️ ¿Cómo funciona el pipeline Map-Reduce?

1. **División (Split):** el diff se divide en lotes, respetando siempre los límites de archivo (las cabeceras `diff --git`). Un archivo nunca se corta por la mitad.
2. **Map:** cada lote se envía a la IA, que devuelve un resumen técnico de lo que cambió en esa parte. La consola muestra el progreso:

   ```text
   📦 ¡Diff gigante detectado! Procesando en 4 lotes (Map-Reduce)...
   ⏳ Analizando lote 1/4...
   ⏳ Analizando lote 2/4...
   ```

3. **Reduce:** los resúmenes parciales se unifican y se envían en una llamada final que genera el resultado real — el mensaje de commit (`-c`), la revisión de código (`-r`/`-f`) o la descripción del Pull Request (comando por defecto).

## 💡 Conviene saber

- **Totalmente automático:** no hay flag que activar. El chunking solo se activa cuando el diff supera el límite; los diffs más pequeños siguen usando una única llamada a la IA.
- **Mismo proveedor y modelo:** los lotes usan el motor de IA que configuraste (Gemini, DeepSeek u Ollama), con una pausa de 1 segundo entre llamadas para respetar los límites de peticiones.
- **Los smart excludes van primero:** los lock files, los assets minificados y otros ruidos se eliminan del diff antes de la estimación de tamaño — lo que a menudo evita el chunking por completo.
- **Compromiso de calidad:** el resultado final se genera a partir de resúmenes técnicos en lugar del diff en bruto, por lo que los detalles muy finos pueden condensarse. Para ramas gigantes, dividir el trabajo en PRs más pequeñas sigue dando a la IA el mejor material.

🔗 Repositorio: [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
