# **Guia Prático: Expressões Regulares Performáticas no GitPR**

O Linter Estático do GitPR processa o `git diff` linha por linha usando o motor nativo `re` do Python (NFA - *Nondeterministic Finite Automaton*). Motores NFA são poderosos, mas possuem um ponto cego perigoso: o **Retrocesso Catastrófico (Catastrophic Backtracking)**.

Este guia orienta como escrever regras para o `.gitpr.linter.yml` garantindo que o tempo de validação do commit permaneça na casa dos milissegundos.

---

## **1. O que é o Retrocesso Catastrófico?**

Ocorre quando uma Regex usa **quantificadores gulosos** `(*, +)` próximos uns dos outros ou aninhados, e a string testada quase dá *match*, mas falha no final.

Para tentar encontrar uma combinação válida, o motor "volta atrás" (backtracks) e tenta todas as permutações possíveis. O tempo de processamento cresce de forma exponencial ($O(2^n)$).

**O Exemplo Clássico (O Código da Morte):**

* **Regex:** `(a+)+$`  
* **Texto:** `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaX`  
* *Resultado:* O terminal trava. O motor tentará mais de 700 milhões de combinações antes de perceber que o X no final impede o *match*.

---

## **2. Regras de Ouro para Alta Performance**

### **Regra 1: "Falhe Rápido" usando Âncoras**

A melhor forma de economizar CPU é fazer a Regex desistir da linha o mais rápido possível.

Se a palavra proibida deve ser uma palavra isolada, use a fronteira de palavra `\b` (Word Boundary). Isso impede que a Regex analise o interior de strings longas desnecessariamente.

* ❌ **Lento:** `dd\(` *(Procura os caracteres 'd', 'd', '(' em todas as posições da linha)*  
* ✅ **Rápido:** `\bdd\(` *(Só inicia a busca no começo de uma palavra. Se a linha for `add()`, ele desiste no primeiro caractere)*

### **Regra 2: Substitua o `.*` por Classes Negadas `[^...]`**

O `.*` (qualquer coisa, zero ou mais vezes) é o maior causador de backtracking. Ele é guloso: vai até o final da linha, e depois começa a voltar de trás para frente procurando o resto da sua regra.

Se você está a procurar algo dentro de aspas ou parênteses, diga exatamente onde ele deve parar.

* ❌ **Lento:** `console\.log\(.*\)` *(Vai até o fim da linha antes de voltar para achar o parêntese final)*  
* ✅ **Rápido:** `console\.log\([^)]*\)` *(A classe `[^)]` significa: "Capture tudo, desde que NÃO seja um parêntese fechado". Ele para no exato milissegundo em que encontra o limite)*

### **Regra 3: Evite Quantificadores Opcionais Aninhados**

Nunca coloque um quantificador opcional (`*` ou `?`) logo após outro quantificador opcional, ou dentro de um grupo que também se repete.

* ❌ **Lento:** `(localhost\s*)*`  
* ✅ **Rápido:** `localhost(\s+localhost)*`

### **Regra 4: Desligue a Captura em Grupos `(?:...)`**

Por padrão, quando você usa parênteses `(get|post)` como a nossa regra de rotas, o Python guarda essa informação na memória para extração posterior. O GitPR não precisa extrair a palavra, ele só precisa saber se ela existe (`True` ou `False`).

Use grupos não-capturantes `(?:...)` para economizar alocação de memória.

* ❌ **Lento:** `Route::(get|post)\(`  
* ✅ **Rápido:** `Route::(?:get|post)\(`

---

## **3. Comparativo Prático para o `.gitpr.linter.yml`**

Veja como transformar regras ingênuas em regras blindadas:

| Objetivo | ❌ Regex Ingênua (Perigosa) | ✅ Regex Performática (GitPR) | Por que é melhor? |
| :---- | :---- | :---- | :---- |
| Bloquear IP Fixo | `[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+` | `\b(?:\d{1,3}\.){3}\d{1,3}\b` | Usa `\b` e `(?:)` para não alocar memória extra, e limita o tamanho a 3 dígitos. |
| Achar TODOs | `.*TODO.*` | `\bTODO\b:` | Elimina o `.*` inútil. A âncora `\b` já resolve a busca na linha inteira. |
| Rotas (Verbos) | `Route::.*\('get.*` | `Route::[A-Za-z]+(\s*['"](?:get\|post)` | Usa classe de caracteres e alternância sem captura rápida. |

**Dica de Prevenção:** Como o GitPR processa linhas com arquivos minificados (ex: `app.min.js`), uma única linha pode ter milhares de caracteres. Aplicar a **Regra 2 (Classes Negadas)** é a sua maior garantia contra travamentos de terminal.

---
