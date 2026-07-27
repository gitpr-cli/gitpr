# Métricas y Telemetría — Analytics Local Offline

GitPR incluye un **sistema de telemetría local y offline** que recolecta eventos
anónimos de uso (comandos CLI, llamadas de IA, ejecuciones del linter, git hooks)
para analytics del equipo. Nada sale de tu máquina — todos los datos permanecen
en `~/.gitpr/metrics/`.

## ✨ Qué Hace

Cada comando de GitPR genera un pequeño archivo JSON de evento registrando:

| Campo | Descripción |
|-------|-------------|
| `timestamp` | Cuándo ocurrió el evento (ISO 8601) |
| `command` | Qué comando se ejecutó (`commit`, `review`, `fullreview`, `linter`, `blame`, etc.) |
| `status` | Resultado (`success`, `error`, `triggered`, `no_changes`) |
| `provider` | Proveedor de IA usado (`gemini`, `deepseek`, `ollama`, `local`) |
| `tokens_estimated` | Conteo de tokens de los metadatos de uso de IA |
| `duration_ms` | Duración del comando en milisegundos |
| `repo` | Nombre del repositorio (`dueño/repo`) |
| `branch` | Nombre de la rama actual |

Campos adicionales como `linter_errors`, `linter_warnings`, `cache_hit` y
`map_reduce_triggered` proporcionan contexto más profundo para tipos específicos
de comando.

## 📁 Dónde se Almacenan los Datos

```
~/.gitpr/metrics/
├── {owner}/{branch}/
│   ├── XXXX-XXXXX-XXXX_20260726.json   ← archivo de evento
│   └── YYYY-YYYYY-YYYY_20260726.json
├── config.json                          ← estado de exportación
└── export/
    ├── gitpr_metrics_2026-07-26.csv     ← CSV consolidado
    └── gitpr_metrics_2026-07-26.json    ← JSON consolidado
```

Cada archivo de evento se nombra con un UUID único y fecha para evitar colisiones.

## 🚀 Comandos CLI

### Mostrar Resumen

```bash
gitpr --metrics
```

Muestra el total de archivos, uso en disco y la ruta del directorio de métricas.

### Exportar Datos

```bash
gitpr --metrics --export
```

Escanea todos los archivos de evento no exportados, los consolida en informes
CSV y JSON en `~/.gitpr/metrics/export/` y rastrea qué archivos han sido procesados.

- **Columnas CSV:** timestamp, command, status, provider, tokens_estimated,
  duration_ms, repo, branch
- **JSON:** array completo de payloads de eventos
- **Barra de progreso:** feedback visual mediante `click.progressbar()`

### Limpiar Datos

```bash
gitpr --metrics --purge
```

Elimina todos los archivos de métrica locales tras confirmación. Preserva
`config.json` para control futuro de exportación.

### Dashboard Interactivo

```bash
gitpr --metrics --dashboard
```

Abre un **dashboard TUI** (Textual) mostrando:

- **Barra de resumen:** total de eventos, errores, total de tokens, top comandos, top providers
- **Tabla de eventos:** últimos 100 eventos con timestamp, comando, estado, provider, tokens, duración
- **Atajos:** `F5` para actualizar, `Esc` para salir

## 🔧 Git Hooks (Recolección Automática)

Cuando se instalan mediante `gitpr --installhooks`, tres hooks adicionales
recolectan telemetría de comportamiento:

| Hook | Evento capturado |
|------|-----------------|
| `post-checkout` | Cambios de rama (cambios de contexto) |
| `pre-push` | Eventos de push (frecuencia de entrega) |
| `post-merge` | Eventos de pull/merge (frecuencia de integración) |

Estos hooks usan `gitpr --hook-event <nombre> --quiet` — una flag oculta que
registra el evento silenciosamente sin salida.

## 📊 Casos de Uso

- **Tech Lead:** Saber si el equipo está usando realmente las revisiones de IA o ignorando los hooks
- **Finanzas:** Comparar uso de Gemini vs. DeepSeek vs. Ollama para optimizar costes de API
- **Calidad:** Identificar qué módulos activan más el linter o el análisis de blame
- **Proceso:** Detectar si el map-reduce se está disparando con frecuencia (PRs grandes — posible problema de proceso)

## 🔒 Privacidad

- **100% local** — ningún dato se envía a servidores externos
- **Anónimo** — los eventos contienen repo/branch pero ningún contenido de archivos o diffs
- **Control del usuario** — la exportación y limpieza son manuales; nada se auto-elimina
- **Hooks opcionales** — los git hooks solo se instalan si ejecutas `gitpr --installhooks`

## 📚 Documentación Relacionada

- [Integración MCP](mcp-integration.md) — Configuración del servidor MCP
- [MCP Prompts](mcp-prompts.md) — Plantillas de mensaje predefinidas
- [MCP Tool Annotations](mcp-annotations.md) — Sugerencias de integración con IDEs

---
**Consejo profesional:** Combina las exportaciones de métricas con el pipeline
de CI de tu equipo ejecutando `gitpr --metrics --export` de forma programada y
versionando el CSV en tu repositorio.
