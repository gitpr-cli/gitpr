# Survey — Badge "GitPR" (selo automático no PR + snippet para o README)

> Levantamento completo da sessão de grill da skill `grill-with-docs`.
> Task: executar o plano `docs/plans/20260918_skill_gitpr_badge_spec.md`.
> Data: 2026-09-19 (sessão iniciada em 2026-09-18) · Branch: `develop_natan`

---

## 1. Contexto da tarefa

A spec `docs/plans/20260918_skill_gitpr_badge_spec.md` (155 linhas) pede duas coisas:

1. **Selo automático no corpo do PR** publicado, montado a partir de dados **reais** da revisão — o exemplo da spec é "0 issues, 94% clean", via shields.io.
2. **`gitpr badge --readme`** — um subcomando que produz um snippet estático de adoção para o README do usuário.

Contexto estratégico (spec §10): tier Free, marketing viral. Cada PR publicado carrega o nome do produto para um público que nunca ouviu falar dele. A spec também pede opt-out espelhando `GITPR_COAUTHOR`, uma árvore `src/domain/branding/` + `src/application/use_cases/`, um bloco em `config.schema.yml`, um aviso de transparência no `gitpr --init`, sete testes obrigatórios e uma ordem de execução em 8 etapas ("cada etapa deve ser um commit/PR isolado").

**A premissa central da spec não existe no código.** O fluxo padrão do `gitpr pr` não roda revisão nenhuma, não produz severidades e não mede duração — ou seja, "0 issues, 94% clean" é um número que o produto não tem como calcular. O grill reconstruiu o contrato em cima do que existe de verdade.

---

## 2. Relatório de fatos levantados

Levantamento feito com agentes de exploração read-only sobre o repositório. **Cinco premissas da spec não correspondem ao código.**

### 2.1 O fluxo padrão do `gitpr pr` não roda revisão nenhuma

`generate_pr_content(action_folder, action_type, diff_text, provider="gemini", cache_scope="", store_diff=False)` (`src/core.py:762-1131`) devolve **prosa achatada**, por ação:

| Operação | Chaves da resposta |
|---|---|
| `commit` | `{"commit_message"}` |
| `review` / `fullreview` / `filereview` | `{"review"}` (markdown) |
| `pr` | `{"commit_message", "pr_description"}` — **dois artefatos de uma só chamada** |

Não há severidade, não há estrutura por achado, não há contagem. O `action_folder` recebido é **sobrescrito** em `core.py:796-803` por um mapa indexado no `action_type`.

A única fonte de número estruturado disponível offline é o **linter local** (`{"errors": [...], "warnings": [...]}`), que o caminho padrão do `gitpr pr` **não chama** — ele roda em `-l`, em `-r`/`-f` e no `review-pr`, nunca no PR publisher.

**Duração não existe no caminho do PR.** `src/main.py` não tem um único `perf_counter`/`time.time`/`elapsed`; o único timer está dentro de `generate_pr_content` (`core.py:793`, `:1113`, `:1127`) e só alimenta a telemetria. O `meta_raw` do cache carrega `duration_ms` (`ai_providers.py:156-166`), mas ele só é gravado **em cache miss** — num cache hit o `return` acontece antes (`core.py:912-925`). Um selo de duração mostraria o tempo de uma execução antiga, ou nada.

### 2.2 Não existe função central de montagem do corpo do PR

A spec pede para hookar "a função central". Existem **quatro cópias independentes** do scaffold:

| Caminho | Onde | O que faz |
|---|---|---|
| TUI publisher | `src/ui/pr_publish_app.py` (semente `:736`, TextArea `:747`, composição `:1573`, scaffold local `:1611-1619`, POST `:1626-1634`) | o corpo publicado é o texto do TextArea — `full_body = pr_body` (`:1623`) |
| `--no-edit` | `src/main.py:2684` `_publish_pr_directly`, composição `:2699-2705` | `**Recommended Commit Message:**` + fence + `---` + `pr_description` |
| `--no-publish` | `src/main.py:1409-1426` | wrapper markdown do `.md` local (não publica) |
| `review-pr` | `src/review/remote_pr.py:78-104` `build_comment_body` | comentário de review (não é corpo de PR) |

O único compositor compartilhado é `compose_review_content` (`src/review/render.py:15-34`), que serve artefatos de review, não corpos de PR.

**Mas existe um contrato único de dados:** `pr_data = {"commit_message", "pr_description"}`, produzido em `src/main.py:1449-1452` e consumido por `PrPublishApp` (`pr_publish_app.py:735-736`) **e** por `_publish_pr_directly` (`main.py:2697`, chamado em `main.py:1470`). Mutar esse dict no ponto de produção atinge os dois caminhos de publicação e deixa o `.md` de `--no-publish` limpo — que é escrito antes, em outro ramo (`main.py:1409-1426`), a partir de `data`, não de `pr_data`.

### 2.3 `config.schema.yml` não existe

Não há nenhum arquivo com esse nome no repositório. É um **desvio já registrado duas vezes**: `docs/claude-code/reports/develop_natan/2026-09-05_scm_multiforge_providers.md:17` e `2026-09-13_gitpr_fix_command.md:12`.

O mecanismo real de configuração tem três camadas:

| Camada | Onde |
|---|---|
| `DEFAULT_CONFIG` (semeia `~/.gitpr/.env`) | `src/config.py:17-74` |
| `ConfigField` (alimenta a tela de Configuração) | `src/config_schema.py:82-111` (dataclass), `FIELDS` `:245`, `FIELDS_BY_KEY` `:958`, `KNOWN_KEYS` `:962`, `CATEGORIES` `:134-215` |
| Leitura | `~/.gitpr/.env` via dotenv (`ENV_FILE`, `config.py:14`) |

Labels e descrições precisam ser chamadas `__("...")` **literais** — o scanner de i18n é AST.

Precedente exato do que a spec pede: `ConfigField(key="GITPR_COAUTHOR", …, category="general", kind=KIND_BOOL)` (`config_schema.py:265-272`) — **presente na tela, ausente de `DEFAULT_CONFIG`**, porque o default é ligado por ausência, não por valor.

### 2.4 O linter é seguro no caminho do PR — mas fica mudo sem regras

`parse_diff_and_lint(diff_text, is_full_file=False, file_path=None, skip_external=False)` (`src/linter_engine.py:209`) devolve exatamente `{"errors": [str], "warnings": [str]}` — strings, dois níveis decididos em `:58-63`.

| Propriedade | Situação |
|---|---|
| Rede | **Nenhuma.** Todo o grafo de chamada é leitura de arquivo local + `__()` + métrica local |
| Download de template | **Nunca.** `templates/gitpr.linter.yml` só é alcançável por `gitpr --skill` (`core.py:1242`) |
| Regra ausente | `load_linter_rules()` (`config.py:540-590`) devolve `[]`, sem default e sem erro |
| YAML malformado | `except yaml.YAMLError` imprime em vermelho e **segue** (`config.py:555-570`) — nunca levanta |
| Subprocesso | Só com `skip_external=False` (bridge externo: `npx eslint …`). Com `True`, `external_linters = []` (`:225`) e os dois blocos do bridge ficam inalcançáveis |
| Árvore de trabalho | O caminho YAML lê só o `diff_text`; o bridge externo é que lê arquivos do disco — o motivo do `skip_external=True` no `review-pr` |
| Origem das regras | `<cwd>/.gitpr/skill/.gitpr.linter.yml` + `~/.gitpr/plugins/linter/*.yml` — **relativo ao CWD**, não à raiz do repo |
| Efeitos colaterais | `log_local_metric` (daemon thread, JSON em `~/.gitpr/metrics/`, `git remote -v`); `resolve_skill_path` move um `.gitpr.linter.yml` legado da raiz; `click.secho` vermelho no YAML quebrado |
| Duplicatas | Sim — nenhuma dedup; uma regra emite uma entrada por linha adicionada |

**O achado que decidiu o desenho:** sem regras configuradas, `linter_engine.py:226-227` **short-circuita e devolve listas vazias** — indistinguível, pelo valor de retorno, de um diff limpo. E esse é o caso **comum**: quem nunca rodou `gitpr --skill` não tem `.gitpr/skill/.gitpr.linter.yml`. Um selo verde "no issues" ali seria uma afirmação que o produto não fez.

Precedente de chamada: `src/review/remote_pr.py:274` — `parse_diff_and_lint(diff_text, skip_external=True)`, sem try/except (seguro, porque não levanta), usado só para o comentário opcional: falha do linter nunca invalida o review.

Forma gravada do linter nos cenários do demo (`src/demo/scenarios/security_issue.py:116-125`):

```python
"linter": {
    "errors": ["src/routes/invoices.ts:9 — 'req.user' dereferenced without a null check (rule: no-unchecked-session)."],
    "warnings": ["tests/invoices.test.ts:50 — test name exceeds 60 characters (rule: max-test-name-length)."],
},
```

### 2.5 Opt-out: `GITPR_COAUTHOR` é o precedente, com uma inconsistência conhecida

`coauthor_enabled()` (`src/config.py:298-311`) desliga para `false/0/no/off/n`; `suggest_reviewers_enabled()` (`:314-327`) é um duplicado quase idêntico; o helper compartilhado é `_env_bool_default_true(key)` (`:678-687`). Existe ainda um **terceiro** parser divergente, `_env_flag()` (`src/main.py:2351-2353`), que só considera verdadeiro `true/1/yes/y`.

`GITPR_COAUTHOR` **não** está em `DEFAULT_CONFIG` e **não** é documentado na doc do usuário — o opt-out é deliberadamente discreto. O trailer Co-Authored-By vive em `core.py:2044-2058` e é injetado pelos chamadores em quatro pontos, todos no momento do commit, nunca no corpo do PR.

Precedência de ambiente: todo `load_dotenv` usa `override=False`, então uma variável de processo vence silenciosamente o `.env` (documentado em `config.py:806-812`, explorado pelo `tests/conftest.py:22`).

### 2.6 shields.io e a construção de URL

**Não há uma única referência a shields.io no repositório** — só na spec. O precedente para um helper de URL pequeno, puro e sem rede é `src/doc_links.py`: `DOCS_BASE_URL = "https://gitpr.natanfiuza.dev.br/docs/"` (`:11`) e `doc_url(filename)` (`:14-28`), com `?lang=` para línguas não-inglesas. `get_doc_url()` (`core.py:487-493`) delega para ele.

Regras de escaping do shields.io para URLs estáticas: `-` → `--`, `_` → `__`, espaço → `_`, e percent-encode do restante não-ASCII.

### 2.7 Restrições de i18n

Seis arquivos `langs/{pt_br,pt_pt,es_es,es,fr_fr,fr}.json`, **1080 chaves cada**, com paridade exata exigida por `tests/test_i18n.py` (referência `pt_br`, piso anti-truncamento >500, gate de chaves faltantes e gate de órfãs). A extração é por AST e varre todo `src/` — logo `__` precisa ser importado direto (`from src.i18n import __`), nunca chamado como `i18n.__`.

**`tests/sync_i18n.py` não pode ser rodado**: o extrator regex trunca literais implicitamente concatenados e derrubaria 39 chaves. O caminho seguro é inserção cirúrgica ordenada com round-trip byte a byte (`.claude/memory/i18n-sync-canonicos-roundtrip.md:15-24`).

`__lang_version__` (`src/updater.py:11`) é o que faz um install existente baixar as chaves novas — hoje `v0.0.29`.

### 2.8 Empacotamento e testes

- `pyproject.toml`: `packages.find` com `include = ["src", "src.*"]`; **sem** `package_data`, `MANIFEST.in` ou dados no wheel. Um pacote novo feito só de `.py` é coletado automaticamente.
- Convenção de testes: `tests/<área>/test_<módulo>.py`, `conftest.py` com docstring de uma linha, grupos `class TestX:` com `def test_...`, `CliRunner` invocando o grupo real com `set_lang("en_us")` no `setUpClass`, stubs patchando o módulo **consumidor**. `tests/demo/conftest.py` é o molde para rede banida + sem API key + interface em inglês. Offline é obrigatório (`tests/README.md:78`).
- Suíte completa: **25 falhas pré-existentes**, nomeadas em `docs/claude-code/reports/develop_natan/2026-09-18_gitpr_demo_mode.md:75`.

---

## 3. Decisões tomadas

### Rodada 1

| # | Questão | Decisão |
|---|---|---|
| Q1 | Layout do código | **(a)** `src/branding/` — pacote de feature plano, como `src/fix/` e `src/review/`. As camadas `domain`/`application` da spec não existem no projeto |
| Q2 | Raio de alcance | **(a)** Só os caminhos que **publicam** corpo de PR: TUI e `--no-edit`. Não no `.md` local, não no MCP, não em comentário de review |
| Q3 | Default e consentimento | **(a)** Ligado por padrão, opt-out `GITPR_BADGE=false`, aviso no `--init` **e** na primeira publicação. Nunca um prompt |
| Q4 | Escopo da entrega | **(a)** Tudo: docs ×5, README ×5, selo dogfooded no README do próprio repo |

### Rodada 2

| # | Questão | Decisão |
|---|---|---|
| Q5 | Conteúdo do selo | **(a)** Contagens reais do linter local sobre o diff do PR (`parse_diff_and_lint`, `skip_external=True`) — offline, sem IA, sem rede |
| Q6 | Duração | **Descartada.** O único valor candidato só existe em cache miss; mostrá-lo seria mostrar o tempo de uma execução antiga |
| Q7 | Visibilidade | **(a)** Visível e editável no TUI (semeado no TextArea); anexado na composição no `--no-edit` |
| Q8 | Integração com o demo | **(a)** A etapa do PR do tour mostra o selo, montado do bloco `linter` gravado de cada cenário |

### Rodada 3

| # | Questão | Decisão |
|---|---|---|
| Q9 | O que o selo afirma | **(a)** Rótulo `GitPR`, mensagem `N errors · M warnings`; `no issues` quando ambos zero. **Sem o verbo "reviewed"** — o que rodou foi análise estática, não revisão de IA |
| Q10 | Alvo do clique | **(a)** Docs site: `https://gitpr.natanfiuza.dev.br/` |
| Q11 | Sem regras configuradas | **(a)** **Sem selo.** O selo só fala quando uma regra realmente rodou. É o caso comum de quem nunca configurou o linter, e a alternativa (verde "no issues") seria uma afirmação não sustentada por nada |

---

## 4. Síntese do desenho aprovado

**Premissas da spec substituídas:** `ReviewSummaryForBadge` com `blockers`/`criticals`/`duration_seconds` reduzida a `BadgeCounts(errors, warnings)`; `src/domain/branding/` + `src/application/use_cases/` → `src/branding/`; `config.schema.yml` → `ConfigField`; "função central de montagem do corpo" → um único ponto de mutação de `pr_data` em `src/main.py:1449-1452`; §9 ("cada etapa um commit") não pode ser honrada (o repo proíbe commit/push).

**Fluxo:**

```
diff_text (em escopo em main.py:1449)
   └─> collect_linter_counts()  ── None se load_linter_rules() == []  (Q11)
        └─> build_pr_badge()    ── "" se None
             └─> append_badge(pr_data["pr_description"], badge)
                  ├─> PrPublishApp (main.py:1518) ──> TextArea editável
                  └─> _publish_pr_directly (main.py:2697) ──> full_body
```

**Cor e mensagem:** `errors > 0` → `red`; `errors == 0 e warnings > 0` → `yellow`; ambos zero → `brightgreen` com `no issues`. O zero aparece junto (`0 errors · 2 warnings`), com pluralização por parte. O corpo recebe **apenas a imagem markdown** — `GitPR | 0 errors · 2 warnings` é a renderização dela pelo GitHub, não uma segunda linha de texto.

**Risco principal:** a viralidade só liga **depois** que o usuário configura regras de linter. Isso é consequência deliberada da Q11, mas reduz o alcance esperado pela spec §10 — a doc precisa transformar "configure suas regras" num passo explícito, não deixar o selo invisível sem explicação.

**Efeitos colaterais aceitos:** uma linha de métrica em `~/.gitpr/metrics/` e um `git remote -v` por publicação com selo; ruído vermelho no console (antes do TUI montar) se o YAML do próprio usuário estiver quebrado.

**Registrado como follow-up (fora desta entrega):** unificar os três parsers divergentes de boolean (`coauthor_enabled`, `suggest_reviewers_enabled`, `_env_flag`); extrair um `compose_pr_markdown()` compartilhado para as quatro cópias do scaffold; entrada em `HELP_MAP` para os subcomandos (`demo` e `badge`).
