---
name: windows-utf8-encoding-fix
description: Consoles Windows com cp1252 crasham em emojis; fix com sys.stdout.reconfigure
metadata:
  type: feedback
  source: docs/gemini/reports/develop_natan/2026-08-03_fix_pylance_import_and_encoding.md
  date: 2026-08-03
  branch: develop_natan
---

Consoles Windows que usam encoding cp1252 (legacy) crasham com `UnicodeEncodeError`
ao tentar imprimir emojis como 🚀. A solução aplicada em `src/main.py`:

```python
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```

Isso garante que qualquer caractere Unicode (emojis, acentos, símbolos) seja
exibido corretamente ou substituído silenciosamente, sem quebrar a execução.

Problema relacionado corrigido na mesma tarefa: Pylance/Pyright não resolvia
imports como `from src.i18n import ...` porque o root do projeto não estava
configurado. A solução em `pyproject.toml`:

```toml
[tool.pyright]
executionEnvironments = [
    { "root": "." }
]
```

**Why:** O crash acontecia no startup do `gitpr` em Windows — o banner com
emoji 🚀 era a primeira coisa impressa e já quebrava antes de qualquer
funcionalidade. O `errors='replace'` é consistente com a regra do projeto
de sempre usar `errors='replace'` em operações de encoding.

**How to apply:**
1. `sys.stdout.reconfigure()` deve ser uma das PRIMEIRAS coisas no `main()`
2. SEMPRE usar `errors='replace'`, nunca `errors='strict'` ou `errors='ignore'`
3. Verificar se outros streams (`sys.stderr`) também precisam de reconfigure
4. Ao adicionar novos emojis à interface, testar em terminal Windows com cp1252
5. O `[tool.pyright]` no `pyproject.toml` é obrigatório para Pylance resolver
   imports relativos ao source root

Relacionado: [[ui-subpackage-packaging]]
