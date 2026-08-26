---
name: testes-i18n-pin-translations
description: Testes que afirmam texto de usuário quebram em máquinas pt-BR; fixar src.i18n.TRANSLATIONS = {} via mock.patch
metadata:
  type: feedback
  source: docs/claude-code/reports/develop_natan/2026-08-19_i18n_untranslated_keys_mangled_fix.md
  date: 2026-08-19
  branch: develop_natan
---

`tests/test_external_linters.py::TestGenerateLinterReportContent` falhou por semanas na
máquina do dev e apareceu como "2 pre-existing failures" em vários relatórios seguidos
(2026-08-15 a 2026-08-18). Não era bug do código: as assertions esperavam texto em inglês
e o `CURRENT_LANG` era auto-detectado do locale do SO como pt-BR, então a saída vinha
traduzida.

**Why:** `src/i18n.py` detecta o idioma do SO no import. Qualquer teste que compare
strings renderizadas por `__()` passa ou falha conforme a máquina onde roda — o mesmo
commit fica verde no CI em inglês e vermelho no notebook do dev.

**How to apply:**
- A correção adotada foi `mock.patch` fixando `src.i18n.TRANSLATIONS` em `{}` (dicionário
  vazio = fallback inglês), **não** setar `GITPR_LANG=en` por env: o env var é lido antes
  do teste rodar e não afeta um módulo já importado.
- Alternativa igualmente aceita: escrever assertions agnósticas de idioma (checar
  estrutura/números em vez de frases).
- Ao escrever teste novo que toca saída de usuário, decida explicitamente entre pinar as
  traduções ou não assertar texto — nunca deixe implícito.
- Sintoma de reconhecimento: teste passa no CI e falha localmente (ou vice-versa) sem
  nenhuma mudança de código.
- Ver [[i18n-auditoria-ast-categorias]].
