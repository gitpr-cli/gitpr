---
name: spinner-adaptive-speed
description: Velocidade adaptativa do spinner baseada no comprimento da frase
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-25_mcp_prompts_and_annotations.md
  date: 2026-07-25
  branch: develop_natan
---

O método `_adaptive_speed()` em `src/spinner.py` ajusta dinamicamente a velocidade
de revelação caractere por caractere baseado no comprimento da palavra/frase:

| Comprimento | frames/letra | sleep_time | Exemplo |
|---|---|---|---|
| ≤ 15 chars | 4 | 0.08s | "Thinking" (~4.8s) |
| 16-35 chars | 2 | 0.06s | "Processing your request" (~4.2s) |
| 36+ chars | 1 | 0.04s | "Portraying a confident AI, even with 70% guesswork" (~2.2s) |

Sem essa adaptação, frases longas levavam ~18s para revelar (4 frames × 0.08s × 56 chars).
O método é chamado por `_next_word()` que gerencia a transição entre palavras.

**Why:** O merge dos templates com `words_happy.md` trouxe frases longas (até 60+
caracteres). A revelação letra a letra em velocidade fixa tornava o spinner
extremamente lento para essas frases. A velocidade adaptativa mantém a experiência
fluida independente do comprimento.

**How to apply:**
1. Ao adicionar novas frases ao template `gitpr.thinking-words.md`, verificar
   se os thresholds de comprimento ainda fazem sentido
2. O cálculo é feito uma vez por palavra (na transição), não por frame
3. Manter os thresholds como constantes no método para fácil ajuste
4. A lógica de "descoberta" de caracteres aleatórios é independente da velocidade
