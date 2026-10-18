# Documentação Técnica: Guia do Revisor (`gitpr explain` / `--explain`)

O Guia do Revisor explica um conjunto de mudanças do ponto de vista de quem vai revisar. Em vez de descrever como o diff é (a descrição do Pull Request já faz isso), ele responde às quatro perguntas que um revisor faz antes de aprovar: **o que muda**, **por que muda**, **onde focar a revisão** e **qual o risco de regressão**.

Ele está disponível como comando standalone, como seção opcional do fluxo de Pull Request e por meio do servidor MCP e da extensão do VS Code.

---

## 1. Visão geral

```bash
# Explica as mudanças não commitadas no repositório atual
gitpr explain

# Força um provedor de IA específico nesta execução
gitpr explain --provider deepseek

# Inclui o Guia do Revisor na descrição do Pull Request (fluxo padrão de PR)
gitpr --explain

# O mesmo, salvando a descrição localmente sem abrir a TUI de publicação
gitpr --explain --no-publish

# Inclui sempre, sem passar a flag em toda execução
# (~/.gitpr/.env)
GITPR_EXPLAIN_BY_DEFAULT=true

# Ajuda contextual com o link da documentação
gitpr -h --explain
```

---

## 2. Referência de comandos

| Invocação | Escopo | Grava em disco | Publica |
|---|---|---|---|
| `gitpr explain [--provider <name>]` | Diff da árvore de trabalho (`git diff HEAD`) | Não | Não |
| `gitpr --explain` | Diff completo da branch contra a base remota | Sim (arquivo `.md` do PR) | Sim, quando o PR é publicado |
| `gitpr --explain --no-publish` | Diff completo da branch contra a base remota | Sim (arquivo `.md` do PR) | Não |
| `gitpr --explain --no-edit` | Diff completo da branch contra a base remota | Sim | Sim, diretamente |

### `gitpr explain`

| Opção | Padrão | Descrição |
|---|---|---|
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Força o provedor de IA nesta execução (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Ajuda do Click mais o link para esta página. |

O comando standalone imprime o guia no terminal e encerra. Nunca cria arquivo, nunca abre o editor e nunca conversa com o forge.

### Flag raiz `--explain`

| Flag | Variável de ambiente | Padrão | Descrição |
|---|---|---|---|
| `--explain` | `GITPR_EXPLAIN_BY_DEFAULT` | `false` | Acrescenta a seção do Guia do Revisor à descrição do Pull Request gerada. |

Valores aceitos por `GITPR_EXPLAIN_BY_DEFAULT` (sem diferenciar maiúsculas de minúsculas): `true`, `1`, `yes`, `y`. Qualquer outro valor — inclusive a variável ausente — mantém a seção desligada. A chave é editável na tela de configuração (`gitpr config`), na categoria **PR**, e pode ser definida manualmente em `~/.gitpr/.env`.

A flag participa apenas do **fluxo padrão de Pull Request**. Modos que encerram antes desse fluxo (`--commit`, `--review`, `--fullreview`, `--issue`, `--blame`, `--chat`, `gitpr tests generate` e os demais subcomandos) a ignoram.

---

## 3. Origens do diff

Os dois pontos de entrada não explicam a mesma coisa:

| Ponto de entrada | Comando por trás | Abrange |
|---|---|---|
| `gitpr explain` | `git diff -U1 -w -M -B HEAD -- <smart excludes>` | Mudanças staged e unstaged de arquivos rastreados, comparadas com `HEAD`. Arquivos não rastreados são avisados e **não** entram no prompt. |
| `--explain` (fluxo de PR) | `git fetch origin` → `git merge-base origin/<base> HEAD` → `git diff -U1 -w -M -B <merge-base> -- <smart excludes>` | Tudo o que a branch muda em relação ao ponto em que divergiu da branch base, incluindo o estado da árvore de trabalho. |

Nos dois casos o diff é capturado com `-U1` (uma linha de contexto), `-w` (ignora espaços em branco), `-M` (detecção de renomeação), `-B` (pares quebrados) e as **smart excludes** resolvidas (lockfiles, artefatos gerados e outros caminhos que afogariam o sinal). O mesmo arquivo auxiliar pode ser sobrescrito com `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL` e `GITPR_SMART_EXCLUDES_LOCAL`.

Como o diff é recortado para leitura, ele não é um patch: não deve ser usado com `git apply`. Comandos que precisam de um patch aplicável (`gitpr fix`, `gitpr split`) capturam o próprio diff.

---

## 4. Pipeline de geração

1. **Verificação de diff vazio.** Um diff vazio ou só com espaços retorna imediatamente uma explicação vazia; o comando standalone imprime `⚠️ No diff found...` e sai com código `1`.
2. **Provedor e chave.** O provedor vem de `--provider` ou `DEFAULT_AI_PROVIDER`. Se não houver chave configurada, o comando imprime `❌ No API key configured for <provider>. Generate one with --install.` em **stderr** e retorna uma explicação vazia. `ollama` não precisa de chave.
3. **Seleção do modelo.** Usa-se o modelo avançado/primário (`get_api_model(provider, task_complexity="advanced")`): `GEMINI_API_MODEL_PRIMARY` ou `DEEPSEEK_API_MODEL_PRIMARY`, com o padrão embutido correspondente.
4. **Resolução da skill.** A instrução de sistema é `get_skill_context("explain", quiet=True)` — `.gitpr/skill/.gitpr.explain.md` quando existe, um `.gitpr.md` legado como fallback, ou então uma instrução embutida equivalente ao template em inglês. O fluxo de PR passa `quiet=True` para que a mensagem "skill carregada" nunca polua a descrição gerada.
5. **Prompt.** O diff completo e as regras de explicação vão em um único prompt. A saída deve ser um objeto JSON (a camada de provedores está configurada para respostas JSON).
6. **Chamada de IA.** `call_ai_model(..., action="explain")` usa temperatura `0.0` e tenta até **3** vezes com intervalo de **2 s**. Em caso de falha retorna `None`, e o comando informa que o guia não pôde ser gerado.
7. **Parsing.** `parse_explain_payload` aceita o **dict** já parseado do provedor e, por compatibilidade, uma string JSON. Uma string que não é JSON válido é tratada como prosa: preenche `what_changes`, o campo `why_it_changes` recebe um placeholder `[FILL: ...]` e `has_sufficient_evidence` passa a `False`.
8. **Renderização.** `build_explain_markdown` monta a seção Markdown usada pelo fluxo de PR; o comando standalone renderiza os mesmos dados em um relatório colorido no terminal.

O fluxo **não** usa o cache local de respostas de IA e **não** grava linha no ledger de métricas. Toda execução chama o provedor.

---

## 5. Contrato de saída

O modelo retorna um objeto JSON com quatro campos:

| Campo | Tipo | Significado |
|---|---|---|
| `what_changes` | string | 2–4 frases em linguagem simples descrevendo a mudança funcional, sem jargão. |
| `why_it_changes` | string | A motivação inferida. Quando o diff não sustenta uma conclusão, o modelo deve usar `[FILL: What is the primary business motivation for this change?]` em vez de inventar uma. |
| `reviewer_focus_points` | array de objetos | 2–5 pontos concretos a inspecionar. Cada objeto tem `description` (obrigatório), `file_path` (opcional) e `related_line` (inteiro opcional). |
| `regression_risk` | string | Superfícies objetivas de risco: código compartilhado crítico, migrações de esquema, mudanças de autenticação, testes ausentes, interfaces que quebram. |

A camada de provedores acrescenta `_telemetry_meta` ao dict; o parser o ignora.

### Seção Markdown

```markdown
## 🧐 Reviewer Guide (Explain My PR)

### 🔍 What changes
...

### 💡 Why it changes
...

### 🎯 Where to focus review
- **Validate token expiration** (`src/auth/tokens.py:45`)
- **Check backward compatibility of the refresh endpoint**

### ⚠️ Regression Risk
...
```

`Where to focus review` só é emitido quando existe ao menos um ponto de foco, e `Regression Risk` só quando o campo não está vazio.

### Indicador de evidência

`has_sufficient_evidence` é `False` quando o diff está vazio, quando não há chave de API disponível ou quando `what_changes` / `why_it_changes` contêm um marcador de placeholder (`[PREENCHER`, `[FILL`, `[TODO`, `[REQUIRED`). O comando standalone imprime um aviso abaixo do relatório; a seção do PR não é suprimida — os placeholders continuam visíveis para o autor completá-los.

---

## 6. Onde o guia aparece

### Fluxo de PR (`--explain`)

Depois que o título e o corpo do PR são gerados, o Guia do Revisor é anexado ao corpo como um bloco separado:

```text
<descrição do PR>

---

## 🧐 Reviewer Guide (Explain My PR)
...
```

O corpo combinado é gravado no arquivo `.md` do PR e é o que será publicado quando o Pull Request for criado. Ativar `GITPR_EXPLAIN_BY_DEFAULT=true` produz o mesmo resultado sem a flag.

### Servidor MCP

A ferramenta `generate_pr_description` aceita `explain: bool = false` e anexa a mesma seção ao `pr_description` retornado. A ferramenta calcula o diff completo da branch por conta própria; o guia é omitido se o modelo não retornar Markdown.

### Extensão do VS Code

O comando `gitpr.generatePrExplain` executa a geração de PR com `explain: true`. O comando simples `gitpr.generatePr` deixa a seção desligada.

---

## 7. Personalizando o guia com uma skill

As regras de explicação são uma **skill**, não texto de prompt fixo:

- Local padrão: `.gitpr/skill/.gitpr.explain.md` no repositório.
- Baixe-a com `gitpr --skill` (também disponível no assistente de instalação). Existem variantes de idioma para `en`, `pt_br`, `pt_pt`, `es_es` e `fr_fr`; o arquivo é baixado no idioma de interface ativo e **nunca é sobrescrito** se já existir.
- Um `.gitpr.md` legado em `.gitpr/skill/` é usado como fallback quando o arquivo específico está ausente.
- Quando nenhum dos dois existe, usa-se a instrução embutida; ela é equivalente ao template em inglês e também exige JSON estrito.
- O idioma do texto gerado segue a skill carregada, não o idioma de interface de `--lang`. Para obter o guia em português, por exemplo, baixe ou escreva o `.gitpr.explain.md` em português.

O template instrui o modelo a escrever para um revisor que não escreveu o código, nunca inventar motivação, listar de 2 a 5 pontos de foco e retornar apenas o objeto JSON.

---

## 8. Erros e códigos de saída

| Situação | Comportamento | Código de saída |
|---|---|---|
| Guia gerado | Relatório no terminal (standalone) ou seção anexada (fluxo de PR) | `0` |
| Sem diff / sem conteúdo | `⚠️ No diff found...` em stdout | `1` |
| Sem chave de API | Erro localizado em stderr; o standalone também imprime `❌ Failed to generate PR explanation.` | `1` |
| Modelo não retornou nada útil | `❌ Failed to generate PR explanation.` | `1` |
| Fluxo de PR, modelo não retornou nada | A seção é omitida silenciosamente da descrição; o restante do PR é produzido normalmente | `0` |
| Nome de provedor inválido | A camada de provedores reporta o provedor desconhecido; nenhum guia é produzido | `1` (standalone) |

---

## 9. Exemplo

```text
$ gitpr explain

🧐 Analyzing diff from reviewer perspective...

============================================================
  REVIEWER GUIDE (Explain My PR)
============================================================

🔍 What changes:
  Adds a Redis-backed rate limiter to the login route and wires it
  into the authentication middleware.

💡 Why it changes:
  Mitigates brute-force credential stuffing without changing the
  login response contract.

🎯 Where to focus review:
  • Verify the key expiration strategy [src/auth/limiter.py:25]
  • Confirm legitimate shared-IP users are not locked out [src/auth/middleware.py]

⚠️ Regression Risk:
  Users behind shared NATs may be throttled together; no test covers
  the limit boundary yet.

⚠️ Notice: Inferred with partial context. Some fields contain placeholders to complete.
```

---

## 10. Limitações

- **A saída standalone é apenas o terminal.** `gitpr explain` não grava arquivo e não publica nada; para anexar a seção a um PR, use `--explain` no fluxo de PR.
- **`--explain` é exclusivo do fluxo padrão de PR.** Combiná-la com modos que encerram antes não tem efeito.
- **Sem cache, sem ledger.** Execuções repetidas chamam o modelo de novo, e a execução não é registrada em `gitpr metrics`.
- **Arquivos não rastreados não são explicados.** As duas origens de diff só enxergam arquivos rastreados. O comando standalone avisa sobre arquivos não rastreados, mas não os inclui; adicione-os com `git add` primeiro.
- **Sem chunking.** O diff inteiro vai em um único prompt. Mudanças muito grandes podem atingir o limite de contexto do provedor; divida o trabalho ou revise um intervalo menor.
- **Sem semântica de patch.** O diff é capturado com `-w` e `-U1` para leitura. Não o reutilize para `git apply`.
- **A motivação é inferida.** O modelo é proibido de inventar justificativa; quando o diff não traz evidência, ele emite um placeholder `[FILL: ...]`.
- **O idioma depende da skill.** Apenas o idioma da interface não traduz o guia gerado.

---

## 11. Documentação relacionada

- [Publicação de Pull Request](pull-request-publication.pt_br.md) — onde a seção é anexada e como o PR é publicado.
- [Templates de Skill](skill-template.pt_br.md) — como arquivos `.gitpr.*.md` são resolvidos, baixados e sobrescritos.
- [Provedores de IA](providers-ia.pt_br.md) — provedores, modelos, tentativas e configuração de chaves.
- [TUI de Configuração](config-tui.pt_br.md) — como editar `GITPR_EXPLAIN_BY_DEFAULT` em `gitpr config`.
- [Geração de Testes](tests-generate.pt_br.md) — o outro comando de geração com IA.
- [Modo Mentor](mentor-mode.pt_br.md) — as explicações pedagógicas adicionadas às revisões de código.
