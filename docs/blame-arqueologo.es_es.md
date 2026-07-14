# Documentación Técnica: Arqueólogo de Código con Git Blame (--blame)

El **Arqueólogo de Código** de GitPR usa `git blame` combinado con inteligencia artificial para rastrear el origen y la evolución de las reglas de negocio en tu código. Clasifica cada commit como **ORIGEM** (creación de la regla) o **REFATORACAO** (modificación posterior) y genera una línea de tiempo detallada.

---

## 1. Sintaxis y Formatos

### 1.1 Modo Directo (líneas específicas)

```bash
gitpr -b src/core.py:140-195    # Rango de líneas
gitpr -b src/main.py:42          # Línea única
```

### 1.2 Modo Interactivo

```bash
gitpr -b src/core.py             # GitPR preguntará qué líneas
```

El terminal mostrará:
```
📂 Archivo seleccionado: src/core.py
¿Qué líneas deseas investigar? (Ej.: 10-20 o solo 45)
```

---

## 2. Cómo Funciona

1. **`git blame`** captura el autor, la fecha y el hash de cada línea en el rango especificado
2. La IA **clasifica** cada commit como `ORIGEM` (creó la regla de negocio) o `REFATORACAO` (modificó código existente)
3. El motor rastrea hasta **4 niveles de commits padre** para comprender la evolución completa
4. El resultado se muestra en el terminal (a color) y se guarda como informe Markdown

### Output en el Terminal

- 🟢 **Verde** = Commit de ORIGEM
- 🟡 **Amarillo** = Commit de REFATORACAO

---

## 3. Integración con Issues

El Arqueólogo puede alimentar la generación de **Issues de Deuda Técnica**:

```bash
gitpr -is -b src/legacy/parser.py:200-350
```

En este modo, la IA genera una issue explicando **cómo evolucionó el bloque** y **por qué necesita ser refactorizado**, usando la cronología del blame como contexto.

---

## 4. Selección de Proveedor de IA

```bash
gitpr -b arquivo.py:10-50 -p gemini
gitpr -b arquivo.py:10-50 -p deepseek
```

> **Nota:** El Arqueólogo usa el modelo **secundario** (más barato) para la clasificación de commits y el modelo **primario** (avanzado) para el resumen ejecutivo final, optimizando el consumo de cuotas.
