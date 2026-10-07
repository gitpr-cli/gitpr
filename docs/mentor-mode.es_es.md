# Documentación Técnica: Modo Mentor Junior (gitpr mentor / --mentor)

`gitpr mentor` transforma los hallazgos de revisión de código en comentarios pedagógicos, prácticos y formativos. Diseñado para desarrolladores junior y en formación, explica **qué** ocurre, **por qué** es importante, **analogías** cotidianas y conceptos clave **para aprender más**.

La funcionalidad es estrictamente **aditiva y opcional (opt-in)**: la revisión técnica original nunca se modifica ni elimina.

---

## 1. Visión General

El Modo Mentor Junior opera en dos modalidades:

1. **Flag `-r --mentor` / `-f --mentor`**: Ejecuta la revisión normal y adjunta la sección `## 🎓 Mentor (Orientación Junior)` al final del informe (`*_PR_REVIEW.txt` o `*_PR_FULLREVIEW.txt`).
2. **Comando `gitpr mentor [--finding <id>]`**: Lee los hallazgos de la última revisión y muestra las explicaciones directamente en la terminal sin tocar el disco.

### 1.1 Referencia de Comandos

```bash
gitpr -r --mentor              # Ejecuta revisión local y añade la sección Mentor
gitpr -f --mentor              # Ejecuta revisión completa y añade la sección Mentor
gitpr mentor                   # Muestra explicaciones en terminal para la última revisión
gitpr mentor --finding FIX-002 # Explica un hallazgo concreto según su ID
gitpr mentor --provider gemini # Fuerza un proveedor de IA específico
```

---

## 2. Configuración (`~/.gitpr/.env`)

| Clave | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `GITPR_REVIEW_MENTOR_MODE` | booleano | `false` | Si es `true`, activa automáticamente el modo mentor en `-r` y `-f`. |
| `GITPR_MENTOR_INCLUDE_ANALOGY` | booleano | `true` | Si es `false`, omite las analogías en las explicaciones. |

