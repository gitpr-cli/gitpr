# Documentação Técnica: Code Review com IA (--review / --fullreview / --input)

O GitPR CLI oferece três modos de code review usando inteligência artificial, cada um adequado a um momento diferente do ciclo de desenvolvimento. Todos os modos integram-se automaticamente com o **Linter Estático** (`.gitpr.linter.yml`), que adiciona alertas de regex ao topo do relatório.

---

## 1. Modos de Review

### 1.1 Review Local — `gitpr -r` (ou `--review`)

Analisa apenas as alterações **não commitadas** na working tree (`git diff HEAD`).

```bash
gitpr -r
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | `git diff HEAD` (alterações locais) |
| **Quando usar** | Antes de fazer commit, para validar a qualidade do código |
| **Output** | `{branch}_{datetime}_PR_REVIEW.txt` |
| **Ideal para** | Revisão rápida, validação pré-commit |

### 1.2 Full Review — `gitpr -f` (ou `--fullreview`)

Compara **todas** as alterações da branch atual contra a branch principal remota (`origin/main`).

```bash
gitpr -f
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Diff completo contra `origin/main` (faz `git fetch` antes) |
| **Quando usar** | Antes de abrir um Pull Request |
| **Output** | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| **Ideal para** | Revisão profunda de toda a feature branch |

### 1.3 Auditoria de Ficheiro — `gitpr -r -i <ficheiro>` (ou `--review --input`)

Analisa um **ficheiro inteiro**, ignorando o git diff. Útil para código legado ou refatorações.

```bash
gitpr -r -i src/legacy/parser.py
gitpr -f -i src/core.py
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Conteúdo integral do ficheiro no disco |
| **Quando usar** | Refatoração de código legado, auditoria de ficheiros críticos |
| **Output** | `{branch}_{datetime}_FILE_REVIEW.txt` |
| **Requer** | `--review` (`-r`) ou `--fullreview` (`-f`) |

---

## 2. Integração com o Linter Estático

Em todos os modos de review, o **Linter Estático** é executado automaticamente. Se houver violações das regras definidas no `.gitpr.linter.yml`, os alertas aparecem no topo do relatório, antes da análise da IA:

```
## 🚨 Alertas de Análise Estática Local (Regras YAML)
- 🚨 Uso de console.log detetado em app.js (Linha 42)
- ⚠️ Uso de localhost detetado em config.php (Linha 15)

---

## 🤖 Code Review da IA
...
```

---

## 3. Personalização via Skills

O comportamento da IA durante o review pode ser personalizado através dos ficheiros de template:

| Ficheiro | Modo | Função |
| --- | --- | --- |
| `.gitpr.review.md` | `--review` / `--fullreview` | Define o foco da análise (ex: SOLID, Clean Code, segurança) |
| `.gitpr.filereview.md` | `--input` (+ review) | Define regras de coesão e acoplamento para ficheiro completo |

Descarregue os templates com `gitpr -s` e edite conforme as regras de negócio da sua equipa.

---

## 4. Seleção de Fornecedor de IA

```bash
gitpr -r -p deepseek        # Review local com DeepSeek
gitpr -f -p gemini          # Full review com Gemini
gitpr -r -i arquivo.py -p deepseek  # Auditoria com DeepSeek
```

---

## 5. Variáveis de Ambiente

| Variável | Modo | Valor predefinido |
| --- | --- | --- |
| `OUTPUT_FILE_NAME_REVIEW` | `-r` | `{branch}_{datetime}_PR_REVIEW.txt` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `-f` | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `-i` | `{branch}_{datetime}_FILE_REVIEW.txt` |

> **Nota:** Consulte também a [documentação do Linter](linter-regras-customizadas.md) para criar regras de validação estática.
