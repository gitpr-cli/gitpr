# Documentación Técnica: Proveedores de IA (--provider)

GitPR es **agnóstico de IA** y actualmente soporta dos proveedores: **Google Gemini** y **DeepSeek**. Puedes alternar entre ellos dinámicamente mediante la línea de comandos o la configuración persistente.

---

## 1. Selección mediante Línea de Comandos

```bash
gitpr -p gemini         # Fuerza Google Gemini en esta ejecución
gitpr -p deepseek       # Fuerza DeepSeek en esta ejecución
gitpr -c -p gemini      # Commit message con Gemini
gitpr -r -p deepseek    # Code review con DeepSeek
```

La flag `--provider` (`-p`) sobrescribe temporalmente el provider predeterminado configurado.

---

## 2. Configuración Persistente

Define el provider predeterminado en el archivo `~/.gitpr/.env`:

```ini
DEFAULT_AI_PROVIDER=gemini
# o
DEFAULT_AI_PROVIDER=deepseek
```

---

## 3. Modelos Disponibles

### 3.1 Google Gemini

| Modelo | Uso | Variable de Entorno |
| --- | --- | --- |
| `gemini-2.5-flash` | Primario (avanzado) — PRs, reviews, issues | `GEMINI_API_MODEL` |
| `gemini-2.5-flash-lite` | Secundario (simple) — clasificación en el blame | `SECONDARY_GEMINI_API_MODEL` |

### 3.2 DeepSeek

| Modelo | Uso | Variable de Entorno |
| --- | --- | --- |
| `deepseek-chat` | Primario y Secundario | `DEEPSEEK_API_MODEL` / `SECONDARY_DEEPSEEK_API_MODEL` |

---

## 4. Configuración de Claves de API

Las claves se almacenan de forma **cifrada** (Fernet) en el archivo `~/.gitpr/.env`:

```ini
GEMINI_API_KEY_ENCRYPTED=<hash_criptografado>
DEEPSEEK_API_KEY_ENCRYPTED=<hash_criptografado>
```

La clave maestra de descifrado se genera automáticamente en `~/.gitpr/secret.key`.

---

## 5. Fallback Automático

Si el provider configurado falla (error de red, cuota excedida, etc.), GitPR intenta automáticamente el **otro provider** disponible. Este comportamiento garantiza que el flujo de trabajo no se interrumpa por la indisponibilidad temporal de un servicio.

---

## 6. Parámetros de Generación

Ambos proveedores están configurados para una salida determinista:

| Parámetro | Valor |
| --- | --- |
| **Temperatura** | 0.0 |
| **Top P** | 0.1 |
| **Formato de salida** | JSON estructurado |
| **Retry** | 3 intentos, intervalo de 2s |
| **Caché** | MD5 (respuestas idénticas no consumen cuota) |

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para instrucciones sobre la configuración inicial de las claves de API.
