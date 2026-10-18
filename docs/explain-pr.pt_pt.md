# Documentação Técnica: Guia do Revisor (`gitpr explain` / `--explain`)

O Guia do Revisor explica um conjunto de alterações do ponto de vista de quem vai rever. Em vez de descrever o aspeto do diff (a descrição do Pull Request já o faz), responde às quatro perguntas que um revisor coloca antes de aprovar: **o que muda**, **porque muda**, **onde focar a revisão** e **qual o risco de regressão**.

Está disponível como comando autónomo, como secção opcional do fluxo de Pull Request e através do servidor MCP e da extensão do VS Code.

---

## 1. Visão Geral

```bash
# Explica as alterações não commitadas no repositório atual
gitpr explain

# Força um fornecedor de IA específico nesta execução
gitpr explain --provider deepseek

# Inclui o Guia do Revisor na descrição do Pull Request (fluxo padrão de PR)
gitpr --explain

# O mesmo, guardando a descrição localmente sem abrir a TUI de publicação
gitpr --explain --no-publish

# Inclui sempre, sem passar a flag em cada execução
# (~/.gitpr/.env)
GITPR_EXPLAIN_BY_DEFAULT=true

# Ajuda contextual com a ligação para a documentação
gitpr -h --explain
```

---

## 2. Referência de Comandos

| Invocação | Âmbito | Escreve no disco | Publica |
|---|---|---|---|
| `gitpr explain [--provider <name>]` | Diff da árvore de trabalho (`git diff HEAD`) | Não | Não |
| `gitpr --explain` | Diff completo da branch contra a base remota | Sim (ficheiro `.md` do PR) | Sim, quando o PR é publicado |
| `gitpr --explain --no-publish` | Diff completo da branch contra a base remota | Sim (ficheiro `.md` do PR) | Não |
| `gitpr --explain --no-edit` | Diff completo da branch contra a base remota | Sim | Sim, diretamente |

### `gitpr explain`

| Opção | Predefinição | Descrição |
|---|---|---|
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Força o fornecedor de IA nesta execução (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Ajuda do Click mais a ligação para esta página. |

O comando autónomo imprime o guia no terminal e termina. Nunca cria ficheiro, nunca abre o editor e nunca comunica com o forge.

### Flag raiz `--explain`

| Flag | Variável de ambiente | Predefinição | Descrição |
|---|---|---|---|
| `--explain` | `GITPR_EXPLAIN_BY_DEFAULT` | `false` | Acrescenta a secção do Guia do Revisor à descrição do Pull Request gerada. |

Valores aceites por `GITPR_EXPLAIN_BY_DEFAULT` (sem distinguir maiúsculas de minúsculas): `true`, `1`, `yes`, `y`. Qualquer outro valor — incluindo a variável ausente — mantém a secção desligada. A chave é editável no ecrã de configuração (`gitpr config`), na categoria **PR**, e pode ser definida manualmente em `~/.gitpr/.env`.

A flag participa apenas no **fluxo padrão de Pull Request**. Os modos que terminam antes desse fluxo (`--commit`, `--review`, `--fullreview`, `--issue`, `--blame`, `--chat`, `gitpr tests generate` e os restantes subcomandos) ignoram-na.

---

## 3. Origens do Diff

Os dois pontos de entrada não explicam a mesma coisa:

| Ponto de entrada | Comando subjacente | Abrange |
|---|---|---|
| `gitpr explain` | `git diff -U1 -w -M -B HEAD -- <smart excludes>` | Alterações staged e unstaged de ficheiros seguidos, comparadas com `HEAD`. Os ficheiros não seguidos são avisados e **não** entram no prompt. |
| `--explain` (fluxo de PR) | `git fetch origin` → `git merge-base origin/<base> HEAD` → `git diff -U1 -w -M -B <merge-base> -- <smart excludes>` | Tudo o que a branch altera em relação ao ponto em que divergiu da branch base, incluindo o estado da árvore de trabalho. |

Em ambos os casos o diff é capturado com `-U1` (uma linha de contexto), `-w` (ignora espaços em branco), `-M` (deteção de renomeação), `-B` (pares quebrados) e as **smart excludes** resolvidas (lockfiles, artefactos gerados e outros caminhos que afogariam o sinal). O mesmo ficheiro auxiliar pode ser substituído com `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL` e `GITPR_SMART_EXCLUDES_LOCAL`.

Como o diff é recortado para leitura, não é um patch: não deve ser usado com `git apply`. Os comandos que precisam de um patch aplicável (`gitpr fix`, `gitpr split`) capturam o seu próprio diff.

---

## 4. Pipeline de Geração

1. **Verificação de diff vazio.** Um diff vazio ou apenas com espaços devolve imediatamente uma explicação vazia; o comando autónomo imprime `⚠️ No diff found...` e termina com código `1`.
2. **Fornecedor e chave.** O fornecedor vem de `--provider` ou `DEFAULT_AI_PROVIDER`. Se não houver chave configurada, o comando imprime `❌ No API key configured for <provider>. Generate one with --install.` em **stderr** e devolve uma explicação vazia. O `ollama` não precisa de chave.
3. **Seleção do modelo.** É usado o modelo avançado/primário (`get_api_model(provider, task_complexity="advanced")`): `GEMINI_API_MODEL_PRIMARY` ou `DEEPSEEK_API_MODEL_PRIMARY`, com a predefinição incorporada correspondente.
4. **Resolução da skill.** A instrução de sistema é `get_skill_context("explain", quiet=True)` — `.gitpr/skill/.gitpr.explain.md` quando existe, um `.gitpr.md` legado como fallback, ou então uma instrução incorporada equivalente ao template em inglês. O fluxo de PR passa `quiet=True` para que a mensagem "skill carregada" nunca polua a descrição gerada.
5. **Prompt.** O diff completo e as regras de explicação vão num único prompt. A saída deve ser um objeto JSON (a camada de fornecedores está configurada para respostas JSON).
6. **Chamada de IA.** `call_ai_model(..., action="explain")` usa temperatura `0.0` e tenta até **3** vezes com intervalo de **2 s**. Em caso de falha devolve `None`, e o comando informa que o guia não pôde ser gerado.
7. **Parsing.** `parse_explain_payload` aceita o **dict** já parseado do fornecedor e, por compatibilidade, uma string JSON. Uma string que não seja JSON válido é tratada como prosa: preenche `what_changes`, o campo `why_it_changes` recebe um placeholder `[FILL: ...]` e `has_sufficient_evidence` passa a `False`.
8. **Renderização.** `build_explain_markdown` monta a secção Markdown usada pelo fluxo de PR; o comando autónomo renderiza os mesmos dados num relatório colorido no terminal.

O fluxo **não** usa a cache local de respostas de IA e **não** grava uma linha no ledger de métricas. Cada execução chama o fornecedor.

---

## 5. Contrato de Saída

O modelo devolve um objeto JSON com quatro campos:

| Campo | Tipo | Significado |
|---|---|---|
| `what_changes` | string | 2–4 frases em linguagem simples a descrever a alteração funcional, sem jargão. |
| `why_it_changes` | string | A motivação inferida. Quando o diff não sustenta uma conclusão, o modelo deve usar `[FILL: What is the primary business motivation for this change?]` em vez de inventar uma. |
| `reviewer_focus_points` | array de objetos | 2–5 pontos concretos a inspecionar. Cada objeto tem `description` (obrigatório), `file_path` (opcional) e `related_line` (inteiro opcional). |
| `regression_risk` | string | Superfícies objetivas de risco: código partilhado crítico, migrações de esquema, alterações de autenticação, testes em falta, interfaces que quebram. |

A camada de fornecedores acrescenta `_telemetry_meta` ao dict; o parser ignora-o.

### Secção Markdown

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

`Where to focus review` só é emitido quando existe pelo menos um ponto de foco, e `Regression Risk` só quando o campo não está vazio.

### Indicador de evidência

`has_sufficient_evidence` é `False` quando o diff está vazio, quando não há chave de API disponível ou quando `what_changes` / `why_it_changes` contêm um marcador de placeholder (`[PREENCHER`, `[FILL`, `[TODO`, `[REQUIRED`). O comando autónomo imprime um aviso abaixo do relatório; a secção do PR não é suprimida — os placeholders permanecem visíveis para o autor os completar.

---

## 6. Onde o Guia Aparece

### Fluxo de PR (`--explain`)

Depois de gerados o título e o corpo do PR, o Guia do Revisor é anexado ao corpo como um bloco separado:

```text
<descrição do PR>

---

## 🧐 Reviewer Guide (Explain My PR)
...
```

O corpo combinado é escrito no ficheiro `.md` do PR e é o que será publicado quando o Pull Request for criado. Ativar `GITPR_EXPLAIN_BY_DEFAULT=true` produz o mesmo resultado sem a flag.

### Servidor MCP

A ferramenta `generate_pr_description` aceita `explain: bool = false` e anexa a mesma secção ao `pr_description` devolvido. A ferramenta calcula o diff completo da branch por conta própria; o guia é omitido se o modelo não devolver Markdown.

### Extensão do VS Code

O comando `gitpr.generatePrExplain` executa a geração de PR com `explain: true`. O comando simples `gitpr.generatePr` deixa a secção desligada.

---

## 7. Personalizar o Guia com uma Skill

As regras de explicação são uma **skill**, não texto de prompt fixo:

- Local predefinido: `.gitpr/skill/.gitpr.explain.md` no repositório.
- Descarregue-a com `gitpr --skill` (também disponível no assistente de instalação). Existem variantes de idioma para `en`, `pt_br`, `pt_pt`, `es_es` e `fr_fr`; o ficheiro é descarregado no idioma de interface ativo e **nunca é substituído** se já existir.
- Um `.gitpr.md` legado em `.gitpr/skill/` é usado como fallback quando o ficheiro específico está ausente.
- Quando nenhum dos dois existe, é usada a instrução incorporada; é equivalente ao template em inglês e também exige JSON estrito.
- O idioma do texto gerado segue a skill carregada, não o idioma de interface de `--lang`. Para obter o guia em português, por exemplo, descarregue ou escreva o `.gitpr.explain.md` em português.

O template instrui o modelo a escrever para um revisor que não escreveu o código, a nunca inventar motivação, a listar 2 a 5 pontos de foco e a devolver apenas o objeto JSON.

---

## 8. Erros e Códigos de Saída

| Situação | Comportamento | Código de saída |
|---|---|---|
| Guia gerado | Relatório no terminal (autónomo) ou secção anexada (fluxo de PR) | `0` |
| Sem diff / sem conteúdo | `⚠️ No diff found...` em stdout | `1` |
| Sem chave de API | Erro localizado em stderr; o comando autónomo também imprime `❌ Failed to generate PR explanation.` | `1` |
| O modelo não devolveu nada útil | `❌ Failed to generate PR explanation.` | `1` |
| Fluxo de PR, o modelo não devolveu nada | A secção é omitida silenciosamente da descrição; o resto do PR é produzido normalmente | `0` |
| Nome de fornecedor inválido | A camada de fornecedores reporta o fornecedor desconhecido; nenhum guia é produzido | `1` (autónomo) |

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

- **A saída autónoma é apenas o terminal.** `gitpr explain` não escreve ficheiro e não publica nada; para anexar a secção a um PR, use `--explain` no fluxo de PR.
- **`--explain` é exclusiva do fluxo padrão de PR.** Combiná-la com modos que terminam antes não tem efeito.
- **Sem cache, sem ledger.** Execuções repetidas chamam novamente o modelo, e a execução não é registada em `gitpr metrics`.
- **Os ficheiros não seguidos não são explicados.** As duas origens de diff só veem ficheiros seguidos. O comando autónomo avisa sobre ficheiros não seguidos, mas não os inclui; adicione-os com `git add` primeiro.
- **Sem chunking.** O diff inteiro vai num único prompt. Alterações muito grandes podem atingir o limite de contexto do fornecedor; divida o trabalho ou reveja um intervalo menor.
- **Sem semântica de patch.** O diff é capturado com `-w` e `-U1` para leitura. Não o reutilize para `git apply`.
- **A motivação é inferida.** O modelo é proibido de inventar justificação; quando o diff não traz evidência, emite um placeholder `[FILL: ...]`.
- **O idioma depende da skill.** Apenas o idioma da interface não traduz o guia gerado.

---

## 11. Documentação Relacionada

- [Publicação de Pull Request](pull-request-publication.pt_pt.md) — onde a secção é anexada e como o PR é publicado.
- [Templates de Skill](skill-template.pt_pt.md) — como os ficheiros `.gitpr.*.md` são resolvidos, descarregados e substituídos.
- [Fornecedores de IA](providers-ia.pt_pt.md) — fornecedores, modelos, tentativas e configuração de chaves.
- [TUI de Configuração](config-tui.pt_pt.md) — como editar `GITPR_EXPLAIN_BY_DEFAULT` em `gitpr config`.
- [Geração de Testes](tests-generate.pt_pt.md) — o outro comando de geração com IA.
- [Modo Mentor](mentor-mode.pt_pt.md) — as explicações pedagógicas adicionadas às revisões de código.
