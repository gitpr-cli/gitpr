# Documentación Técnica: Generación de Mensajes de Commit con IA (--commit)

El comando `--commit` (`-c`) de GitPR genera automáticamente mensajes de commit con el formato **Conventional Commits** usando inteligencia artificial para analizar tus cambios locales.

---

## 1. Uso Básico

```bash
gitpr -c
```

La herramienta analiza el `git diff HEAD` y muestra el mensaje sugerido directamente en la consola:

```
📝 Sugestão de Commit:

feat: adiciona validacao de email no formulario de cadastro

- Implementa regex de validacao RFC 5322
- Adiciona mensagens de erro localizadas (pt-BR)
- Corrige edge case de emails com dominios internacionais
```

---

## 2. Formato Conventional Commits

La IA está instruida para generar mensajes con el estándar:

```
tipo: descricao curta

Corpo opcional com detalhes adicionais
```

**Tipos utilizados:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

---

## 3. Integración con Git Hooks

El `--commit` se usa internamente por el hook `prepare-commit-msg`. Cuando se instala con `gitpr -ih`, el hook ejecuta:

```bash
gitpr --commit --hook <caminho-do-arquivo-temporario>
```

La flag `--hook` (interna/oculta) hace que el mensaje sugerido se inyecte directamente en el editor de Git, en lugar de mostrarse en la consola.

---

## 4. Personalización mediante Skill

El comportamiento de la IA puede personalizarse a través del archivo `.gitpr.commit.md` en la raíz del proyecto:

```bash
gitpr -s          # Baixa o template .gitpr.commit.md
# Edite o arquivo conforme as convenções da sua equipa
gitpr -c          # A IA usará as suas regras customizadas
```

---

## 5. Selección de Proveedor de IA

```bash
gitpr -c -p gemini       # Força Google Gemini
gitpr -c -p deepseek     # Força DeepSeek
```

---

## 6. Caché de Respuestas

GitPR genera un hash MD5 de tu diff + instrucciones. Si ejecutas `gitpr -c` de nuevo **sin modificar el código**, la respuesta se devuelve instantáneamente desde la caché local, ahorrando cuotas de la API.

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para una visión general de todas las funcionalidades.
