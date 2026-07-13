# Documentação Técnica: Arqueólogo de Código com Git Blame (--blame)

O **Arqueólogo de Código** do GitPR usa `git blame` combinado com inteligência artificial para rastrear a origem e evolução de regras de negócio no seu código. Ele classifica cada commit como **ORIGEM** (criação da regra) ou **REFATORACAO** (alteração posterior) e gera uma linha do tempo detalhada.

---

## 1. Sintaxe e Formatos

### 1.1 Modo Direto (linhas específicas)

```bash
gitpr -b src/core.py:140-195    # Intervalo de linhas
gitpr -b src/main.py:42          # Linha única
```

### 1.2 Modo Interativo

```bash
gitpr -b src/core.py             # O GitPR perguntará quais as linhas
```

O terminal apresentará:
```
📂 Arquivo selecionado: src/core.py
Quais linhas você deseja investigar? (Ex: 10-20 ou apenas 45)
```

---

## 2. Como Funciona

1. **`git blame`** captura o autor, data e hash de cada linha no intervalo especificado
2. A IA **classifica** cada commit como `ORIGEM` (criou a regra de negócio) ou `REFATORACAO` (alterou código existente)
3. O motor rastreia até **4 níveis de commits pai** para perceber a evolução completa
4. O resultado é apresentado no terminal (colorido) e guardado como relatório Markdown

### Output no Terminal

- 🟢 **Verde** = Commit de ORIGEM
- 🟡 **Amarelo** = Commit de REFATORACAO

---

## 3. Integração com Issues

O Arqueólogo pode alimentar a geração de **Issues de Dívida Técnica**:

```bash
gitpr -is -b src/legacy/parser.py:200-350
```

Neste modo, a IA gera uma issue a explicar **como o bloco evoluiu** e **porque precisa de ser refatorado**, usando a cronologia do blame como contexto.

---

## 4. Seleção de Fornecedor de IA

```bash
gitpr -b arquivo.py:10-50 -p gemini
gitpr -b arquivo.py:10-50 -p deepseek
```

> **Nota:** O Arqueólogo usa o modelo **secundário** (mais barato) para classificação de commits e o modelo **primário** (avançado) para o sumário executivo final, otimizando o consumo de quotas.
