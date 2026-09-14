# Survey — `gitpr fix` (levantamento de fatos e decisões)

> Sessão `/grill-with-docs` de **2026-09-13**, branch `develop_natan`.
> Tarefa pedida: *"execute o plano `docs/plans/20260913_skill_gitpr_fix_command_spec.md`, salve o plano gerado em `docs/plans`"*.
> Plano gerado e aprovado: [20260913_skill_gitpr_fix_command_plan.md](../plans/20260913_skill_gitpr_fix_command_plan.md).
> Spec de origem: [20260913_skill_gitpr_fix_command_spec.md](../plans/20260913_skill_gitpr_fix_command_spec.md).

## 1. Contexto da tarefa

A spec pede um comando de primeira classe `gitpr fix` que transforme sugestões de review em diff
revisável — dry-run por padrão, `--apply` explícito, `--all-safe` para o conjunto classificado como
seguro, `--rollback` determinístico. A spec impõe um **passo 0 obrigatório** (itens 0.1 a 0.6) de
investigação antes de qualquer código; este survey é o resultado desse passo, mais as decisões do grill.

Três premissas da spec foram **derrubadas** pela investigação (seção 4). O escopo aprovado é a spec
completa (etapas 1–11) com as correções de rota registradas no plano.

## 2. Decisões do grill (4 rodadas)

### Rodada 1 — escopo e forma

| # | Questão | Decisão |
|---|---|---|
| Q1 | Escopo da entrega | Spec completa (etapas 1–11) |
| Q2 | Layout de arquivos (a spec pede `src/domain` + `src/application` + `src/infrastructure/git`) | Pacote `src/fix/`, mantendo os nomes de arquivo da spec, sem camadas DDD |
| Q3 | Refactor do chat (F5 / `ctrl+shift+s`) | Refatorar na mesma camada — **reformulada na rodada 2** |
| Q4 | Flag `--force` | Implementar, exigindo **frase digitada** (não `y/n`) |

Decidido sem perguntar, por regra do projeto: **nada é commitado** (CLAUDE.md proíbe `git add/commit/push`),
apesar de a spec §10 pedir "cada etapa um commit/PR isolado". As mudanças ficam na árvore de trabalho,
na ordem recomendada, para o usuário fatiar.

### Rodada 2 — depois dos fatos

| # | Questão | Decisão |
|---|---|---|
| Q5 | Fonte dos findings (não existe modelo de finding no projeto) | **Chamada nova de IA** sobre o último review, com IDs `FIX-001..N` atribuídos por nós; o contrato do `gitpr -r` fica intacto |
| Q6 | O que "compartilhar a camada" significa, dado que o chat não aplica nada | **Só extrair o helper** de blocos cercados; comportamento do chat inalterado (`.txt` no CWD) |
| Q7 | `src/fix/` contradiz o ADR-003, que rejeitou `src/release/` em favor de flat | Manter `src/fix/` e **registrar ADR-004** explicando por que `fix` difere de `release` |
| Q8 | Onde mora o `fix_history.json` | `.gitpr/fix_history.json` **rastreado no git** — a opção literal da spec (contrariou a recomendação de `~/.gitpr/`) |

### Rodada 3 — semântica de execução

| # | Questão | Decisão |
|---|---|---|
| Q9 | Instrução de sistema da chamada de IA | **Template novo** `templates/gitpr.fix.md` (+ pt_br) registrado em `SKILL_FILES_BY_TYPE` |
| Q10 | `gitpr fix --all-safe` sem `--apply` (a spec se contradiz entre §1 e §4) | **Só seleciona**; escrever exige `--apply`. Dry-run é o default universal |
| Q11 | Branch automática no `--all-safe` | **Cria por default** (`fix/gitpr-{datetime}`), com `--no-branch`; template usa `{datetime}` porque o vocabulário do projeto é `("branch", "datetime")` |
| Q12 | Árvore de trabalho suja (a spec omite) | Avisa/confirma **só quando o patch toca um arquivo já modificado** |

### Rodada 4 — entregáveis

| # | Questão | Decisão |
|---|---|---|
| Q13 | Cobertura de documentação | **5 variantes** de idioma (pt_br, pt_pt, es_es, fr_fr), como os outros 34 docs |
| Q14 | Extras além da spec | Expor `--list`/dry-run no MCP como **tool read-only** (13ª); sem `--format json`, sem tool de escrita |

## 3. Fatos levantados (passo 0 da spec)

### 3.1 — Comportamento real de F5 e `ctrl+s` (item 0.1)

- O chat TUI é **um arquivo só**: `src/ui/chat_app.py` (675 linhas). **Não existe `src/ui/chat/`** —
  caminho citado pela spec (`:47`).
- São **dois handlers distintos**, e a segunda tecla **não é `ctrl+shift+s`**:

  | Tecla | Handler | Linha |
  |---|---|---|
  | `f5` | `action_apply_code` — *"Extract the last AI code block and save it to a suggestion file"* | `chat_app.py:600` |
  | `ctrl+s` | `action_auto_patch_focused` — *"Ctrlhift+S: extract code from the focused AI message only"* | `chat_app.py:400` |

- `ctrl+shift+s` **não existe em nenhum `.py`** do repo. A string que o usuário vê, `"Ctrlhift+S"`, é um
  **literal i18n corrompido** (perdeu o "S" de "Shift") em `chat_app.py:78` e `:359`, com a chave duplicada
  verbatim nos `langs/*.json:388-390`. Já registrado como bug conhecido em
  `docs/claude-code/reports/develop_natan/2026-09-06_reviewer_suggestion.md:70` e no
  `ADR-002-reviewer-suggestion.md:127`.
- Os dois handlers são **duplicação copy-paste** (`:409-437` e `:616-647`): mesma regex, mesmo fallback,
  mesmo join, mesma escrita. A única diferença é a origem do texto (`ai_messages[-1]` vs `_focused_msg_content`).
- **Extração:** regex de blocos cercados, não parser de diff —
  ``re.findall(r"`{3}\s*(?:\w+)?\s*\n(.*?)`{3}", msg, re.DOTALL)``, com fallback por `split("```")`.
  Resposta sem bloco → notificação de warning, sem exceção.
- **Aplicação: nenhuma.** Não há `import subprocess` em `chat_app.py`, nem `git apply`, nem escrita em
  arquivo de código. O terminal do fluxo é gravar `GITPR_PATCH_SUGGESTION_<key>.txt` **no CWD** com os
  blocos concatenados por `"\n\n"` — texto que **nem é um unified diff**, portanto não passaria num `git apply`.
- **Validação: nenhuma.** Sem `git apply --check`, sem confirmação, sem tela de modal.
- **Proveniência: nenhuma.** O `.txt` não registra modelo, provider, prompt nem finding.
- Desenho original (não implementado) que gerou a memória do usuário: `docs/plans/plano_chat_interativo_híbrido.md:41-42`
  afirmava que F5 *"tenta aplicar a substituição no teu ficheiro local usando lógica de diff/patch"* — nunca foi implementado.

### 3.2 — Modelo de finding (item 0.2): **não existe**

- Nenhum dataclass/TypedDict/schema com `id`, `severity`, `category`, `file_path`, `line`, `suggestion`.
- O review devolve **envelope JSON de uma chave**: `{"review": "<Markdown livre>"}` — instrução em
  `core.py:806-812` (`review`/`fullreview`) e `core.py:797-804` (`filereview`). O consumidor lê
  `data.get("review", ...)` em `main.py:1386`.
- O template manda Markdown puro (CHANGE SUMMARY / CRITICAL POINTS / IMPROVEMENT SUGGESTIONS / VERDICT) e
  **nunca pede JSON nem patch**: `templates/gitpr.review.md:17-32`. A única instrução com cara de patch é
  *"Use short code blocks to show Before/After"*.
- O linter é o análogo mais próximo de "severidade", mas é **duas listas de strings pré-formatadas**
  (`linter_engine.py:220` → `alerts = {"errors": [], "warnings": []}`, decidido em `:58-63`). O único dict
  com campo `severity` é o do checkstyle externo (`:141-148`), **stringificado na linha seguinte** (`:202`).
- `blame_engine.py:246-249` tem classificação estruturada de dois valores (`ORIGIN`/`REFACTORING`), mas não é finding.
- Não existe prefixo `SEC-` gerador em `src/`.

### 3.3 — Normalização de saída de IA (item 0.3): **mínima, e não de findings**

- `call_ai_model` (`ai_providers.py:101`) força JSON no transporte: `response_mime_type: "application/json"`
  (Gemini, `:142-152`) e `response_format={"type":"json_object"}` (DeepSeek/Ollama, `:172-180`).
- Parse: `json.loads` cru (`:203`) + um "escudo" que desembrulha lista (`:205-207`). **Não há** reparo,
  strip de fence, regex de salvatagem nem `json_repair`. JSON malformado → retry 3× (2s) → `None`.
- A exceção é o chat: `call_ai_chat` (`:311`) **não** força JSON por decisão documentada no docstring
  (`:320-323`) e **não tem retry**.
- O review usa o caminho JSON, mas "estruturado" significa apenas o envelope de uma chave — não há estrutura abaixo do topo.

### 3.4 — `ai_providers.py` (item 0.4)

- `call_ai_model(provider, api_key, api_model, prompt, system_instruction, quiet=False, action="ai_call")`
  → `dict` + `_telemetry_meta`, ou `None`. Provider é o argumento posicional string: `gemini`, `deepseek`, `ollama`.
  Retry 3× fixo, mesmo provider.
- `call_ai_chat(provider, api_key, api_model, system_instruction, chat_history, new_message, quiet=False)` → `str` cru.
- Modelos: `get_api_model(provider, task_complexity)` (`config.py:367`), PRIMARY para `advanced`, SECONDARY para `simple`.
  Hoje `commit` é o único `simple` (`core.py:771`) — os três modos de review usam PRIMARY.
- **Não existe `expect_json`**: JSON é incondicional em `call_ai_model`.
- `get_skill_context(action_type, quiet=False)` (`core.py:658-707`) resolve `.gitpr/skill/<file>` pelo
  `SKILL_FILES_BY_TYPE` (`config.py:126-134`, 7 tipos) → fallback `.gitpr.md` → `""`. Um action type desconhecido
  cai no skill de **review** silenciosamente.

### 3.5 — Abstração de git (item 0.5): **não existe**

- 12 módulos chamam `subprocess.run(["git", ...])` inline, repetindo o mesmo boilerplate de encoding.
- O único wrapper nomeado é **privado de um módulo só**: `release_engine.py:71 _run_git(root, args)`.
- **`git apply`, `git stash` e `checkout -b`: zero ocorrências** em `src/` e `tests/`. Criação de branch não existe no projeto.
- Subcomandos em uso: `diff`, `log`, `blame`, `show`, `fetch`, `status`, `add`, `commit`, `push`, `config`,
  `remote`, `rev-parse`, `merge-base`, `symbolic-ref`, `ls-files`, `describe`, `tag`.
- Existe um parser **puro** de unified diff reaproveitável: `src/diff_parser.py` — `parse_added_lines(diff_text)`
  (`:105`) devolve `{arquivo: [linhas adicionadas]}`, com `_decode_git_path` (`:22`) para paths citados/octais do git.
  Só conta **adições** — insuficiente para o critério de linhas alteradas e para a heurística de assinatura removida.

### 3.6 — Convenção de branch (item 0.6): **não existe**

- Nenhum prefixo gerado, nenhum template de nome de branch, nenhuma criação de branch.
- O que existe é sanitização de branch para **nome de arquivo**, repetida em 4 lugares:
  `branch_name.replace("/", "-").replace("\\", "-")` (`main.py:770`, `:1328`, `:1760`, `blame_engine.py:389`, `issue_app.py:89`).
- `PR_DEFAULT_BASE` é a branch **alvo** do PR, não nomenclatura.
- O vocabulário de placeholder de template do projeto é `TEMPLATE_PLACEHOLDERS = ("branch", "datetime")`,
  `TEMPLATE_REQUIRED = ("datetime",)` (`config_schema.py:75`). O `{date}` da spec não existe.

### 3.7 — Infra adicional relevante

| Área | Fato |
|---|---|
| **CLI** | `@click.group(invoke_without_command=True)` + dispatch de ~29 flags em `if/elif`; 2 subcomandos reais (`release`, `config`). Precedente a copiar: `main.py:1587-1653`. O callback do grupo retorna cedo quando há subcomando (`:544-548`), preservando a superfície legada. |
| **Flags livres** | Nenhum dos nomes da spec existe. `--force` já existe no `release`, com outro sentido (namespaces de subcomando não colidem). `-f` no root é `--fullreview`. |
| **Config** | **`config.schema.yml` nunca existiu** e foi rejeitado pelo ADR-001 (*"só dotenv plano + Fernet"*). O mecanismo real: `DEFAULT_CONFIG` (`config.py:17-64`) + `config_schema.py` (dataclasses) + `get_*_settings()`. `tests/test_config_schema.py` **exige paridade** entre `DEFAULT_CONFIG` e `FIELDS_BY_KEY`, e entre os labels de skill e `SKILL_FILES_BY_TYPE`. |
| **`.gitpr/`** | **Não é gitignored** — 166 arquivos rastreados (`reports/` 136, `metrics/` 21, `skill/` 8, `conf/` 1). Paths são resolvidos com `os.getcwd()`, não com a raiz do repo. |
| **`.gitignore`** | Ignora `*.txt` globalmente — por isso os relatórios de review (`.txt`) não aparecem versionados. |
| **Testes** | `unittest.TestCase` dominante (38 arquivos); pytest como runner; sem `[tool.pytest.ini_options]`. **Um único** precedente de repo git real: `tests/test_suggest_reviewers.py:239-282` (`tempfile.mkdtemp` + `addCleanup` + `_git()` com `core.autocrlf=false`, `commit.gpgsign=false`). O portão de update é silenciado por `GITPR_SKIP_UPDATE_CHECK` em `tests/conftest.py:20-23`. |
| **Output** | **Sem `rich`** (não é dependência). Só `click.secho`/`click.echo`. Sem precedente de colorir linhas `+`/`-`. |
| **i18n** | A chave **é** a frase em inglês, verbatim. 6 arquivos em `langs/` (955 chaves no pt_br). Paridade forçada por `tests/test_i18n.py` via AST. |
| **MCP** | 12 tools documentadas, registry + `--list` + `--tool`. Stdout é o stream JSON-RPC (monkey-patchado). |
| **Docs** | 34 docs de usuário, **todos em 5 variantes** de idioma. `epilog` do subcomando usa `get_doc_url()`. |

## 4. Premissas da spec derrubadas

| Spec | Realidade |
|---|---|
| §0.1 / §5 / §8: o chat aplica patches de forma não-revisável, e isso é um gap de segurança a corrigir | O chat **só exporta** texto para `.txt`. Não há aplicação, então não há gap de segurança nem comportamento de risco a retro-corrigir. O que há é duplicação de handlers e um literal i18n corrompido (não-objetivo desta entrega). |
| §0.2: existe (ou pode existir) `gitpr fix SEC-001` endereçando um finding | Nenhum finding é produzido em lugar nenhum. Os IDs passam a ser atribuídos pela própria chamada de normalização (`FIX-001..N`), determinísticos via cache MD5 + temperatura 0.0. |
| §11: "Tier 1 — generalizar um mecanismo que já existe e funciona" | Só ~30 linhas da regex do chat são reaproveitáveis. O `fix` é capacidade nova: contrato de IA novo + primeira abstração de `git apply` do projeto. |
| §10: "Atualizar `config.schema.yml`" | Arquivo inexistente, rejeitado por ADR-001. Vira chaves `GITPR_FIX_*` em dotenv plano. |
| §10: "cada etapa um commit/PR isolado" | Contradiz o CLAUDE.md, que proíbe `git add`/`commit`/`push`. As mudanças ficam na árvore de trabalho. |
| §2: caminhos `src/ui/chat/`, `src/domain/fix/`, `src/application/use_cases/`, `src/infrastructure/git/` | Nenhum existe. O chat é um arquivo único; o projeto é flat com um sub-package (`src/infrastructure/scm/`). Decisão: `src/fix/` (ADR-004). |

## 5. Divergências CLAUDE.md × código (achadas de passagem)

| CLAUDE.md | Código |
|---|---|
| "All AI calls must return structured JSON" | Falso para `call_ai_chat` (Markdown livre, por decisão documentada). E "structured" é só o envelope de uma chave. |
| "Fallback: if configured provider fails, automatically try the other one" | **Não implementado.** `call_ai_model` tenta 3× o *mesmo* provider e devolve `None`. Nenhum caminho troca gemini↔deepseek. |
| "Automatic retry (3 attempts, 2s interval)" | Verdadeiro só em `call_ai_model`; `call_ai_chat` não tem retry. |
| "All documentation files have EN originals and `.pt_br.md` copies" | Subdimensionado: 34 docs têm **5** variantes. |

## 6. Resultado

Plano aprovado e salvo em `docs/plans/20260913_skill_gitpr_fix_command_plan.md`, com 12 decisões fechadas,
15 etapas de execução e as correções de rota acima. Nada foi commitado — as mudanças ficam na árvore de trabalho.
