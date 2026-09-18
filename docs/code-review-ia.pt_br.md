# Documentação Técnica: Code Review com IA (--review / --fullreview / --input)

O GitPR CLI oferece quatro modos de code review usando inteligência artificial, cada um adequado a um momento diferente do ciclo de desenvolvimento. Todos os modos integram-se automaticamente com o **Linter Estático** (`.gitpr.linter.yml`), que adiciona alertas de regex ao topo do relatório.

---

## 1. Modos de Review

### 1.1 Review Local — `gitpr -r` (ou `--review`)

Analisa apenas as alterações **não commitadas** no working tree (`git diff HEAD`).

```bash
gitpr -r
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | `git diff HEAD` (alterações locais) |
| **Quando usar** | Antes de commitar, para validar a qualidade do código |
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

### 1.3 Auditoria de Arquivo — `gitpr -r -i <arquivo>` (ou `--review --input`)

Analisa um **arquivo inteiro**, ignorando o git diff. Útil para código legado ou refatorações.

```bash
gitpr -r -i src/legacy/parser.py
gitpr -f -i src/core.py
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Conteúdo integral do arquivo no disco |
| **Quando usar** | Refatoração de código legado, auditoria de arquivos críticos |
| **Output** | `{branch}_{datetime}_FILE_REVIEW.txt` |
| **Requer** | `--review` (`-r`) ou `--fullreview` (`-f`) |

### 1.4 Review de Pull Request Remoto — `gitpr review-pr <number>`

Revisa um pull request que **já está aberto na forge**, buscando o seu diff direto da API. A branch não precisa ser local: nada é baixado nem trazido para a sua árvore de trabalho. É o modo para revisar o pull request de outra pessoa.

```bash
gitpr review-pr 123
gitpr review-pr 123 --provider deepseek
gitpr review-pr 123 --post-comment
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | O diff servido pela API da forge para aquele pull request |
| **Quando usar** | Revisar um pull request ao qual você foi convidado, sem fazer checkout da branch |
| **Output** | `{branch}_{datetime}_PR_REVIEW.txt`, nomeado pela branch de origem do pull request |
| **Publicação** | Nada, a menos que `--post-comment` seja informado; a revisão é então publicada como comentário |
| **Requer** | Uma forge configurada pelo `gitpr --init` que sirva um diff unificado — o Azure DevOps não serve |
| **Ideal para** | Revisão de código de contribuições de terceiros, e para repositórios que você nunca clona |

Roda o mesmo motor, a mesma skill e o mesmo cache que o `gitpr -r`, então o seu relatório lê como um review local do mesmo diff. Veja a [documentação de Review de Pull Request Remoto](review-pr.pt_br.md) para o contrato completo — as recusas que não custam token, o filtro de smart excludes, o escopo de cache e o rodapé do comentário.

---

## 2. Integração com o Linter Estático

Em todos os modos de review, o **Linter Estático** é executado automaticamente. Se houver violações das regras definidas no `.gitpr.linter.yml`, os alertas aparecem no topo do relatório, antes da análise da IA:

```
## 🚨 Alertas de Análise Estática Local (Regras YAML)
- 🚨 Uso de console.log detectado em app.js (Linha 42)
- ⚠️ Uso de localhost detectado em config.php (Linha 15)

---

## 🤖 Code Review da IA
...
```


Num review de pull request remoto (`gitpr review-pr`), apenas as regras YAML rodam: o bridge do linter externo executa binários contra arquivos **no disco**, que nesse modo seriam o que você tem em checkout, e não o pull request em revisão. Revisar a revisão errada e publicar os alertas como comentário é pior do que não executá-los.

---

## 3. Customização via Skills

O comportamento da IA durante o review pode ser customizado através dos arquivos de template:

| Arquivo | Modo | Função |
| --- | --- | --- |
| `.gitpr.review.md` | `--review` / `--fullreview` | Define o foco da análise (ex: SOLID, Clean Code, segurança) |
| `.gitpr.filereview.md` | `--input` (+ review) | Define regras de coesão e acoplamento para arquivo completo |

Baixe os templates com `gitpr -s` e edite conforme as regras de negócio da sua equipa.

---

## 4. Seleção de Provedor de IA

```bash
gitpr -r -p deepseek        # Review local com DeepSeek
gitpr -f -p gemini          # Full review com Gemini
gitpr -r -i arquivo.py -p deepseek  # Auditoria com DeepSeek
gitpr review-pr 123 --provider deepseek  # Review remoto com DeepSeek
```

O `-p` / `--provider` do grupo raiz não é herdado pelos subcomandos, então o `gitpr review-pr` escreve a mesma opção como `--provider`.

---

## 5. Variáveis de Ambiente

| Variável | Modo | Valor padrão |
| --- | --- | --- |
| `OUTPUT_FILE_NAME_REVIEW` | `-r`, `review-pr` | `{branch}_{datetime}_PR_REVIEW.txt` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `-f` | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `-i` | `{branch}_{datetime}_FILE_REVIEW.txt` |

> **Nota:** Consulte também a [documentação do Linter](linter-regras-customizadas.md) para criar regras de validação estática.
