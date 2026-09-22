# Survey — Secret scanning no linter regex do GitPR

> Levantamento completo da sessão de grill da skill `grill-with-docs`.
> Task: avaliar e redesenhar a spec `docs/plans/20260921_skill_gitpr_secret_scanning_spec.md` (152 linhas).
> Data: 2026-09-21 · Branch: `develop_natan`

---

## 1. Contexto da tarefa

A spec propõe elevar o GitPR de "linter de estilo" para "quality + security gate" adicionando um conjunto de regras de detecção de segredo hardcoded ao linter regex já existente. Ela é classificada pela própria autora como Tier 2 (diferenciação e retenção, esforço médio), destinada ao tier Free/Community, com a evolução para detecção por entropia e bridge SAST (Semgrep, Gitleaks, Bandit) reservada para os tiers pagos.

O problema não é o objetivo — é que a spec foi escrita supondo uma estrutura de repositório que **não é esta**. Dos seis pré-requisitos que ela mesma lista como bloqueantes (§0), cinco apontam para mecanismos que não existem neste código: a lista fixa de presets "em `core.py`", o arquivo `config.schema.yml`, um mecanismo de severidade bloqueante com três níveis, um mecanismo de exclusão de valor, e um mecanismo de supressão por linha. O sexto (smart excludes) existe, mas com escopo diferente do suposto. Como a spec é explícita em proibir implementação sem confirmar os passos 0.1–0.4, o grill foi feito inteiramente à luz do código real, com três agentes de exploração read-only.

O escopo desta sessão não é implementar: é documentar o desenho correto (grade de decisões Q1–Q10) para que a implementação possa acontecer depois sem nova rodada de perguntas de produto.

## 2. Relatório de fatos levantados

**Sete premissas da spec não correspondem ao código.** O levantamento foi feito com três agentes de exploração read-only (motor do linter; registro de skills e wiring do CLI; costuras com review de IA, smart excludes e bloqueio), com verificação direta das referências de linha antes de escrevê-las aqui.

### 2.1 "A lista fixa de presets/skills está declarada em `core.py`" (§0.2, §2) — está em `src/config.py`

`core.py` não contém lista alguma: `get_skill_context()` apenas delega para `skill_file_for()` ([src/core.py:739-760](src/core.py#L739-L760)). O registro canônico é um dict em [src/config.py:142-151](src/config.py#L142-L151):

```python
# src/config.py:142-151
SKILL_FILES_BY_TYPE = {
    "commit": ".gitpr.commit.md",
    "pr": ".gitpr.pr.md",
    "review": ".gitpr.review.md",
    "filereview": ".gitpr.filereview.md",
    "issue": ".gitpr.issue.md",
    "blame": ".gitpr.blame.md",
    "release": ".gitpr.release.md",
    "fix": ".gitpr.fix.md",
}
```

Mas o achado mais importante está no comentário que precede o dict ([src/config.py:135-141](src/config.py#L135-L141)): **o catálogo de regras do linter não é uma skill e não pertence a este registro.**

```
# A file in the folder that is not listed here is not a
# skill and is never offered for editing — .gitpr.linter.yml is the standing
# example (it is a rule catalogue, not an AI persona).
```

Ou seja: registrar o ruleset de segurança como "skill" seria contrariar uma decisão já tomada e documentada no código — e a tela de configuração passaria a listá-lo como persona de IA editável.

### 2.2 "Atualizar `config.schema.yml`" (§7.7) — o arquivo não existe

O schema de configuração é um **módulo Python**: [src/config_schema.py](src/config_schema.py), com `ConfigField` congelado ([src/config_schema.py:79-111](src/config_schema.py#L79-L111)) e a tupla `FIELDS` ([src/config_schema.py:251](src/config_schema.py#L251)). A garantia de que schema e defaults não divergem é um teste, não um arquivo: `tests/test_config_schema.py` falha se uma chave de `DEFAULT_CONFIG` não estiver classificada. Consequência prática para esta feature: **duas chaves novas de config exigem registro em `FIELDS`**, senão a suíte quebra.

### 2.3 "`gitpr --linter security`" (§1, §5) — impossível sem mudar a opção

`-l/--linter` é `is_flag=True` e não aceita valor ([src/main.py:298-303](src/main.py#L298-L303)); o fluxo testa o booleano puro em [src/main.py:759](src/main.py#L759) (`if linter:`). Não existe `--preset`, seletor de ruleset nem `click.Choice` no caminho do linter. O Click rejeitaria o argumento extra. Qualquer ativação seletiva exige mudar a declaração da opção ou usar config.

### 2.4 `presets/linter/security.yml` e `src/domain/linter/` (§2) — nenhum dos dois existe

Não há diretório `presets/` no repo, e nada fora de `src/` é empacotado: [pyproject.toml:30-32](pyproject.toml#L30-L32) declara `packages.find` com `include = ["src", "src.*"]` e **não há `package-data` nem `MANIFEST.in`**. O wheel publicado contém apenas `src/` e o `.dist-info` — é exatamente por isso que todo template existe só por HTTP. Um diretório `presets/` novo **não seria distribuído** sem mudança de empacotamento. Também não existe `src/domain/`; as features são pacotes planos (`src/fix/`, `src/review/`, `src/split/`, `src/branding/`) ou módulos planos (`src/linter_engine.py`, `src/linter_wizard.py`).

Leitura real das regras, exatamente dois lugares ([src/config.py:562-612](src/config.py#L562-L612)): o arquivo do projeto via `resolve_skill_path(".gitpr.linter.yml")` → `<cwd>/.gitpr/skill/.gitpr.linter.yml`, e os plugins globais `~/.gitpr/plugins/linter/*.{yml,yaml}` por varredura de extensão ([src/config.py:540-549](src/config.py#L540-L549)).

### 2.5 O schema real da regra tem 7 chaves, e nenhuma delas é `id`, `severity`, `category` ou `exclude_values` (§3)

Documentado no próprio template ([templates/gitpr.linter.yml:7-15](templates/gitpr.linter.yml#L7-L15)) e implementado em [src/linter_engine.py:13-71](src/linter_engine.py#L13-L71):

| Chave | Onde é lida | Observação |
|---|---|---|
| `name` | `linter_engine.py:68` | "Unique rule identifier (no spaces)" — é a **única identidade** da regra |
| `level` | `linter_engine.py:58` | **É a severidade.** A chave `severity` é silenciosamente ignorada |
| `regex` | `linter_engine.py:50` | A chave `pattern` não existe |
| `message` | `linter_engine.py:51-55` | Substitui só `{file_name}` e `{line_number}`, via `.replace()` |
| `extensions` | `linter_engine.py:16` | Regra **sem** `extensions` nunca roda |
| `require_paths` / `ignore_paths` | `linter_engine.py:20-35` | Globs compilados como regex com `*`→`.*`, não ancorados |
| `ignore_comments` | `linter_engine.py:43-46` | Heurística fixa: `^//`, `^#`, `^/\*`, `^\*` |

O erro tem consequência medida: `tests/test_plugins.py` usa `"severity": "error"` em oito fixtures (linhas 128, 148, 163, 168-169, 206, 226, 260) — chave ignorada que cai no default **bloqueante**. Os testes passam porque só afirmam nomes e contagens. É a armadilha que a nova feature não pode herdar.

### 2.6 Severidade tem **dois** valores, e qualquer outro vira bloqueio (§5, §0.3)

```python
# src/linter_engine.py:57-63
level = rule.get("level", "error").lower()
if level == "warning":
    alerts["warnings"].append(message)
else:
    alerts["errors"].append(message)
```

`warning` é o único valor não bloqueante. `critical`, `blocker`, `info`, `fatal`, um typo ou a ausência da chave caem todos em `errors`. O bloqueio real, verificado em primeira mão:

| Fluxo | Código | Comportamento |
|---|---|---|
| `gitpr -l` | [src/main.py:809-827](src/main.py#L809-L827) | TUI `LinterApp` quando interativo; texto puro em `--quiet`/`--hook`; **`sys.exit(1)` incondicional** em [src/main.py:827](src/main.py#L827) |
| Hook `pre-commit` | [scripts/pre-commit-template.sh:16-32](scripts/pre-commit-template.sh#L16-L32) | `gitpr --linter --quiet`; status ≠ 0 → "COMMIT BLOCKED!" + `exit 1` |
| `--no-edit` / TUI de publish | [src/main.py:2829](src/main.py#L2829), [src/ui/pr_publish_app.py:517-568](src/ui/pr_publish_app.py#L517-L568) | Modal oferecendo `--no-verify` ou abortar |
| `-r` / `-f` | [src/review/render.py:15-75](src/review/render.py#L15-L75) | **Puramente cosmético** — errors e warnings entram no mesmo bloco, sem exit code |
| `review-pr` | [src/review/remote_pr.py:274](src/review/remote_pr.py#L274) | Findings vão para o corpo do comentário; nunca bloqueia |
| MCP `run_linter` | [src/mcp_server.py:745-784](src/mcp_server.py#L745-L784) | JSON com `passed: errors == 0`; nunca levanta |
| Badge | [src/branding/badge_data.py:34-53](src/branding/badge_data.py#L34-L53) | Decorativo por contrato |

Risco registrado: **regex inválida vira erro bloqueante** ([src/linter_engine.py:64-71](src/linter_engine.py#L64-L71)). Um typo num ruleset de segurança bloquearia todo commit do usuário.

### 2.7 Não existe objeto de finding — e por isso a redação do segredo é automática

`parse_diff_and_lint` devolve `{"errors": [...], "warnings": [...]}`, duas listas de **strings já renderizadas**. Não há dataclass carregando arquivo, linha, regra ou nível; nenhum consumidor consegue refiltrar estruturalmente. Em compensação, a mensagem **nunca ecoa o valor casado**: os únicos placeholders substituídos são `{file_name}` e `{line_number}` ([src/linter_engine.py:51-55](src/linter_engine.py#L51-L55)). A preocupação de vazamento em comentário de PR se resolve por construção, não por código extra.

### 2.8 Supressão e exclusão de valor: nenhuma das duas existe (§4, §3)

Nenhum mecanismo de supressão inline em todo o repositório — nem `gitpr-ignore`, nem `noqa`, nem equivalente. Os únicos escapes possíveis hoje são `git commit --no-verify`, a env `GITPR_SKIP_LINT` e o `GITPR_SKIP_SMART_EXCLUDES` (que desliga *todos* os excludes de uma vez). `exclude_values` não existe no motor **mas é desnecessário**: o motor usa `re.search` ([src/linter_engine.py:50](src/linter_engine.py#L50)), então lookahead negativo dentro do próprio regex resolve o filtro de placeholder em YAML puro — o fallback que a spec abria na §3 (rebaixar a regra por falta de filtro) não precisa existir.

### 2.9 O motor casa **linha a linha**, sempre, e só linhas adicionadas

`code_line = line[1:].strip()` ([src/linter_engine.py:299](src/linter_engine.py#L299)) e `re.search(rule["regex"], code_line)` ([src/linter_engine.py:50](src/linter_engine.py#L50)). Não há `re.MULTILINE`/`re.DOTALL` em lugar nenhum e nenhum caminho junta linhas: padrão com `\n` **nunca** casa, em nenhum modo. No modo diff, só `+` é checado ([src/linter_engine.py:297](src/linter_engine.py#L297)).

Duas consequências diretas: (a) "AWS Secret Access Key em contexto próximo" é inexprimível sem um conceito novo de janela de proximidade entre linhas; (b) como o `.strip()` remove a indentação antes do match, âncoras `^\s*` são inúteis.

### 2.10 "Aplica a todo arquivo" é inexprimível

`if file_extension not in rule.get("extensions", []): return False` ([src/linter_engine.py:16](src/linter_engine.py#L16)), com `file_extension = current_file.split(".")[-1]` ([src/linter_engine.py:242](src/linter_engine.py#L242)) — case-sensitive. Um scanner de segredos precisa cobrir `.env`, `id_rsa`, `credentials`, `Dockerfile`, `terraform.tfvars`; hoje o motor só sabe dizer "só estes sufixos", e nenhuma extensão especial significa "todos". Sem mudança no motor, o caso mais comum de vazamento fica fora por construção.

### 2.11 Os smart excludes rodam **antes** do linter e não são removíveis pelo projeto (§0.5)

```python
# src/core.py:330
SMART_EXCLUDES = _load_smart_excludes() + _load_docs_smart_excludes()
```

consumido em [src/core.py:528](src/core.py#L528) (`git diff -U1 -w -M -B HEAD -- <excludes>`). O merge com o arquivo local do projeto é **união + dedup**, não override ([src/core.py:259-265](src/core.py#L259-L265)): um projeto só consegue *acrescentar* exclusões, nunca remover uma global. Efeito para a segurança: `.md`, `.txt`, `.rst`, `*.log`, lockfiles, minificados e imagens **nunca chegam ao linter** — e o projeto não tem como reverter isso sem `GITPR_SKIP_SMART_EXCLUDES`, que desliga tudo. `.env`, `*.json`, `*.yml`, `id_rsa` e `Dockerfile` **são** vistos (não estão nas listas).

### 2.12 Nenhum prompt de IA procura segredo — a divisão de responsabilidade é trivial (§0.4)

Grep por `secret|credential|password|senha|credencial` em todo `templates/`: zero ocorrências. O que existe é genérico — `templates/gitpr.review.md:10` pede "SQLi, XSS, data exposed in logs"; `gitpr.fix.md:14` tem `security` como *categoria* de patch, não instrução de detecção. Não há sobreposição entre o ruleset regex e o review de IA. O custo de mexer nos prompts, porém, é real: invalidaria o cache MD5 das reviews já feitas e criaria um segundo caminho de detecção não determinístico, que só roda quando o usuário paga uma chamada de IA.

### 2.13 Pré-artefatos: a doc já promete o que nenhuma regra cumpre

- [docs/git-hooks-locais.md:31-34](docs/git-hooks-locais.md#L31-L34): *"Exit Code 1: If forbidden strings (e.g.: console.log, **passwords**, localhost) are detected... aborts the commit"* — nenhuma regra implementa senha. Esta feature fecha uma promessa escrita.
- [docs/plans/20260809_criar_plugin_system.md:48](docs/plans/20260809_criar_plugin_system.md#L48) já planejava um "Security Pack (`security.yml`)" com AKIA/JWT/senha via `~/.gitpr/plugins/linter/`; [docs/plugins-system.md:57](docs/plugins-system.md#L57) usa `AKIA[0-9A-Z]{16}` como exemplo. O canal de plugin global existe e funciona — mas é global à máquina, não versionado e não serve como gate de CI de um projeto.
- [docs/linter-regras-customizadas.md](docs/linter-regras-customizadas.md) §2 documenta o YAML de regra **omitindo a chave `level`** — divergência doc/código a corrigir quando a feature for implementada.

Vocabulário: **`preset` já é um termo ocupado** neste repo — são os presets de *linter externo* (`~/.gitpr/conf/gitpr.linter-presets.json`, `LINTER_PRESETS_VERSION`, wizard `--linter-setup`), não pacotes de regras regex. E `KIND_SECRET` em [src/config_schema.py:27](src/config_schema.py#L27) é um tipo de campo de UI para token de API, não detecção.

## 3. Decisões tomadas

### Rodada 1 — escopo e postura do produto

| # | Questão | Decisão |
|---|---|---|
| Q1 | Entregável da sessão | Documentar o desenho; implementação em sessão separada |
| Q2 | Gate ou report | Gate só nas categorias de altíssima confiança; connection string e credencial genérica nunca bloqueiam |
| Q3 | Vocabulário de severidade | Não estender: `error`/`warning` apenas |
| Q4 | Onde o ruleset mora | Módulo Python dentro de `src/`, não arquivo fora do pacote |
| Q5 | Redação do valor casado | Automática por construção; vira invariante testado |

### Rodada 2 — limites do motor

| # | Questão | Decisão |
|---|---|---|
| Q6 | Termo canônico | "security ruleset"; `preset` permanece reservado para linter externo |
| Q7 | Aplicabilidade a arquivos | `extensions: ["*"]` no motor |
| Q8 | AWS Secret Access Key em contexto | Fora do v1 |

### Rodada 3 — costuras

| # | Questão | Decisão |
|---|---|---|
| Q9 | Ponto cego dos smart excludes | Aceito e documentado |
| Q10 | Prompts de review da IA | Não alterados |
| — | Fluxos cobertos | Todos os que já chamam o linter (`-l`, `-r`, `-f`, `--input`, MCP, badge, publish, `review-pr`) — é o mesmo motor |

## 4. Síntese do desenho aprovado

O que foi **substituído** em relação à spec: três níveis de severidade → dois; `presets/linter/security.yml` → módulo em `src/`; `gitpr --linter security` → chave de config; `exclude_values` → lookahead negativo; registro em `core.py` → merge em `load_linter_rules()`; `id`/`category` → `name` (única identidade do motor).

```
git diff (já filtrado pelos smart excludes)
   └─ parse_diff_and_lint
        ├─ load_linter_rules()  ── catálogo do projeto (.gitpr/skill/.gitpr.linter.yml)
        │                       ── plugins globais (~/.gitpr/plugins/linter/*.yml)
        │                       ── NOVO: security ruleset (src/, se GITPR_LINTER_SECURITY=true,
        │                                              menos GITPR_LINTER_SECURITY_DISABLED_RULES)
        └─ só linhas "+" → match linha a linha (após .strip())
             ├─ extensions: ["*"]  ← NOVO: regra vale em qualquer arquivo
             ├─ level: error   → alerts["errors"]   → TUI / exit 1 / hook bloqueia
             └─ level: warning → alerts["warnings"] → aviso; o commit prossegue
```

**Desenho fechado em uma frase:** o ruleset de segurança é um conjunto de regras no schema que o motor já entende, embutido no pacote (não baixado, não editável no arquivo do usuário), ligado por config e desligável regra a regra; ele bloqueia o commit apenas nas cinco categorias onde o padrão é prova suficiente, e reporta sem bloquear nas duas onde o falso positivo é esperado. Nenhuma linha do motor muda além de `extensions: ["*"]` e do ponto de merge.

**Riscos aceitos conscientemente:**

1. **Ponto cego dos docs e lockfiles** (Q9): `.md`, `.txt`, `*.log` e lockfiles nunca são varridos, e o projeto não pode remover essas exclusões (união, não override). Mitigação: documentar; `.env`, `id_rsa`, `credentials.json` e código-fonte estão cobertos.
2. **Sem escape por linha no v1**: um falso positivo em `error` só se resolve com `GITPR_LINTER_SECURITY_DISABLED_RULES` (desliga a categoria inteira) ou `--no-verify`. Mitigação: só as cinco categorias de padrão determinístico entram como `error`.
3. **`--no-verify` continua sendo a saída universal**: o gate não é intransponível, e não deve ser — é um aviso forte, não uma prisão.
4. **Sem varredura retroativa**: só o diff corrente; segredo já commitado não é encontrado (fora de escopo por decisão da spec, mantida).

**Registrado como follow-up (fora desta entrega):**

- Supressão por linha/arquivo (capacidade transversal ao linter, não específica da segurança).
- Detecção por entropia e bridge SAST (Gitleaks/Semgrep/Bandit) — tier pago.
- Regra com janela de proximidade entre linhas (o que permitiria o par AKIA + Secret Access Key).
- Varredura retroativa do histórico (`git log -p`), análoga ao `gitpr blame`.
