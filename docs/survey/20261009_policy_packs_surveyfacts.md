# Survey — Policy Packs / Skills Compartilháveis

> Levantamento completo da sessão de spec de Policy Packs do GitPR (branch `develop_natan`,
> 2026-10-09). Fatos verificados no código, não em relatórios. O plano de execução que saiu
> daqui vive em
> [20261009_policy_packs_plansfacts.md](../plans/develop_natan/20261009_policy_packs_plansfacts.md);
> o vocabulário canônico, no [glossário](../plans/glossary-policy-packs.md); a decisão de
> arquitetura, no [ADR-011](../plans/ADR-011-policy-packs.md).

## 1. O pedido

Executar a spec [20261009_skill_gitpr_policy_packs_spec.md](../plans/20261009_skill_gitpr_policy_packs_spec.md)
(516 linhas, 17 seções): unificar skills, presets de linter YAML, regras de severidade,
caminhos críticos, configuração de risk score e convenções de PR/commit num **Policy Pack**
versionável e compartilhável — um manifesto declarativo aplicado por repositório.

Antes de codificar, a §0 da spec exige oito verificações no código real (skills fixas,
linter YAML, risk config, plugin system, precedência de config, `--init`, tratamento de
config de terceiros). Este survey é o resultado dessas oito verificações, mais as premissas
que elas derrubaram, mais as 20 decisões fixadas em 5 rodadas de entrevista.

## 2. Premissas da spec derrubadas pelo código

| # | A spec diz | O código diz | Efeito |
|---|---|---|---|
| P1 | "ALTERAR `config.schema.yml`" (§3) | O arquivo **nunca existiu**. Três relatórios anteriores já registram o desvio. O alvo real é `src/config_schema.py` — 1186 linhas, `KIND_*` widgets, `ConfigField`/`Group`/`Category`, `CATEGORIES` (14 entradas), `GROUPS`, `FIELDS` (56) | Alterar o módulo Python |
| P2 | `policy-packs/` na raiz do repositório (§3) | A raiz **não é empacotada**: `[tool.setuptools.packages.find] include = ["src","src.*"]`, sem `package_data`, sem `MANIFEST.in`, sem `setup.py`/`setup.cfg`. O wheel `gitpr_cli-1.3.0` contém apenas `.py` | Mover para `src/policy_packs/` + criar `[tool.setuptools.package-data]` |
| P3 | O sistema de plugins pode ser a infraestrutura de distribuição (§0.5) | O "plugin system" é `os.listdir("~/.gitpr/plugins/linter/")` — **sem manifesto, sem versão, sem checksum, sem OTA, sem registry**. Não há lifecycle a reutilizar | A condição da §0.5 falha → `~/.gitpr/policies/` próprio e `src/infrastructure/policy/` novos |
| P4 | `SeverityOverride(rule_id, severity)` com `severity: critical` (§4, §5) | O contrato real do linter é `name` (não `id`) + `level` ∈ {`error`, `warning`}. `src/linter_engine.py:72` decide por `level == "warning"`, e **tudo o que não é warning cai em errors**. `critical` é `RiskLevel.CRITICAL` — nível de **risco**, não severidade de regra. A ADR-007 registra a rejeição explícita de um terceiro nível | `SeverityOverride(rule_name, level)` |
| P5 | `linter.preset_file` (§5) | "Preset" já é vocabulário ocupado: `linter_wizard._LINTER_PRESETS` são **binários externos** (PHPCS, ESLint, Stylelint) | Renomear para `linter.rules_file` |
| P6 | Precedência termina em "6. CLI → 7. env" (§6.1) | O projeto faz o contrário em todos os pares reais: `--provider` vence `DEFAULT_AI_PROVIDER`; `--base` vence `PR_DEFAULT_BASE` | Inverter: CLI acima de env |
| P7 | A spec cita 6 skills (`review`, `pr`, `commit`, `issue`, `explain`, `mentor`) (§1.2) | `src/config.py:145-176` registra **11**: `commit`, `pr`, `review`, `filereview`, `issue`, `blame`, `release`, `fix`, `tests`, `explain`, `mentor`. Não existe skill `explain` como arquivo próprio — `explain` está em `SKILL_TYPES` mas o mapa real é `SKILL_FILES_BY_TYPE` | Validar contra `SKILL_TYPES`, o registro canônico |
| P8 | `risk.test_patterns`, `protected_paths`, `pr.required_sections`, `commit.allowed_types` configuram comportamento (§4, §5) | **Nenhum dos quatro tem consumidor.** `load_risk_config()` lê apenas `enabled`, `include_in_review`, `analysis_version`, `thresholds`, `weights` e `critical_paths`; `is_test_file()` é hardcoded | `test_patterns` vira chave real de `RiskConfig`; os outros três viram contexto de prompt |

## 3. A descoberta que a spec não previu — o cache

O `skill_context` **não entra na chave de cache**. Em `src/core.py`:

- `cache_scope = ""` (default), e a leitura é `get_cached_response(action_folder, prompt + cache_scope)`.
- O docstring do módulo registra a regra: *"`cache_scope` is appended to the cache key only —
  never to the prompt"*.
- O `skill_context` viaja em `instrucao_sistema`, um **argumento separado** de `prompt`, em
  todos os caminhos (`review`/`fullreview`/`filereview`, `pr`, `commit`, …).

Consequência: ativar um pack mudaria o `instrucao_sistema` mas **não** a chave. Num diff já
cacheado, o review sairia idêntico e o rótulo `Policy: nome@versão` da §7.3 estaria mentindo.
O `cache_scope` já existe exatamente para isto e o `DiffSource` já o usa para a origem remota.
Decisão: a identidade da política entra no `cache_scope` como
`::policy::<nome>@<versão>::<checksum>`.

## 4. Os oito pontos da §0, verificados

### 4.1 Skills fixas (`get_skill_context`)

Registro canônico em `src/config.py`: `SKILL_FILES_BY_TYPE` (11 entradas), `SKILL_TYPES`,
`DEFAULT_SKILL_TYPE = "review"`, e os helpers `skill_file_for()`, `skill_file_path()`,
`skill_template_remote_name()`, `skill_file_status()`. O comentário nas linhas 145-151 é
explícito: *"A file in the folder that is not listed here is not a skill and is never offered
for editing — `.gitpr.linter.yml` is the standing example"*.

`get_skill_context(action_type, quiet=False)` em `src/core.py` resolve o arquivo por
`resolve_skill_path()` com fallback para o legado `.gitpr.md`, e devolve `""` quando não há
nada. Um teste (`tests/`) afirma o acordo entre `config_schema.SKILL_LABELS` e
`config.SKILL_FILES_BY_TYPE`.

**Onze chamadas** consomem `get_skill_context`: o hub `core.generate_pr_content`
(pr/commit/review/filereview), `issue_engine.py`, `blame_engine.py` (mais um bypass direto),
`release_engine.py`, `fix/apply_fix.py`, `tests_generation/generate_test_file.py`,
`application/use_cases/generate_pr_explanation.py` e `generate_mentor_explanation.py`.

### 4.2 Linter YAML

- Regras em `.gitpr/skill/.gitpr.linter.yml` (projeto), `~/.gitpr/plugins/linter/*.yml`
  (global), mais `SECURITY_RULES` embutidas (`src/security_ruleset.py`, 7 regras).
- `load_linter_rules()` em `src/config.py:701-763` é o **único** ponto de merge, e é
  **puramente aditivo**: sem dedup, sem override por nome. Ordem: projeto → plugins → segurança.
- Schema real da regra: `name` (único, sem espaços), `level` (`error` bloqueia / `warning`
  alerta), `extensions`, `require_paths`, `ignore_paths`, `regex`, `message` (com
  `{file_name}` e `{line_number}`), `ignore_comments`.
- API pública: `parse_diff_and_lint(diff_text, is_full_file=False, file_path=None,
  skip_external=False, repo_path=".")` → `{"errors": [...], "warnings": [...]}`.
- `src/security_ruleset.py` tem 7 regras (`sec-aws-access-key`, `sec-github-token`,
  `sec-slack-token`, `sec-google-api-key`, `sec-private-key-block` = `error`;
  `sec-db-connection-string`, `sec-generic-credential-assignment` = `warning`), todas
  `extensions: ["*"]`.

### 4.3 Risk scoring

`src/domain/risk/risk_rules.py` concentra tudo: `DEFAULT_WEIGHTS` (15 sinais),
`DEFAULT_THRESHOLDS` (`low_max` 24, `medium_max` 49, `high_max` 79),
`DEFAULT_CRITICAL_PATTERNS` (4 grupos: `SECURITY_SENSITIVE`, `DATABASE_MIGRATION`,
`INFRASTRUCTURE`, `CRITICAL_PATH`), `NON_EXECUTABLE_PATTERNS`, o dataclass `RiskConfig` e
`load_risk_config()`.

Fatos relevantes para o pack:

- **Só `critical_paths` tem chave YAML**, e ela **substitui** `CRITICAL_PATH` — os outros
  três grupos de padrões não são alcançáveis por configuração.
- `weights` faz merge chave a chave; qualquer exceção no parsing devolve `RiskConfig()`
  (fail-safe silencioso).
- `RiskConfig.enabled` e `RiskConfig.include_in_review` são **parseados e nunca lidos** —
  código morto. O comportamento real de "incluir no review" vem da variável de ambiente
  `GITPR_RISK_INCLUDE_IN_REVIEW` lida em `core.py`.
- `is_test_file()` é **hardcoded** (partes do caminho `test`/`tests`/`__tests__`,
  `.test.`/`.spec.`, prefixos `test_`/sufixo `_test.py` etc.) — não há `test_patterns`.
- **O ponto de injeção já existe**: `src/application/use_cases/calculate_risk.py` faz
  `cfg = config or load_risk_config()`, ou seja, `calculate_risk(source, config=...)` já
  aceita um `RiskConfig` de fora.

### 4.4 Plugin system

`~/.gitpr/plugins/linter/*.yml|yaml` (regras) e prompts MCP. Descoberta por
`os.listdir`. **Sem** manifesto, versão, checksum, OTA ou registry. Não serve como
infraestrutura de distribuição de packs.

### 4.5 Configuração e precedência

`~/.gitpr/.env` via `load_dotenv(override=False)` — o que está no processo vence o arquivo.
`.gitpr/skill/` para conteúdo do projeto. `docs/*.md` + `README.*.md` em 5 idiomas.
A precedência documentada da spec (§6.1) contradiz os pares reais do projeto (ver P6).

### 4.6 `--init` e a TUI de configuração

`gitpr --init` é o wizard de forja SCM (`run_scm_init_wizard`), não de configuração geral.
A TUI de configuração é `src/config_schema.py` + seu app Textual, com 14 categorias. É onde
a nova categoria `policy` deve entrar — não há UX paralela a criar.

### 4.7 Config de terceiros

O plugin linter é o precedente: YAML de fora entra por `load_linter_rules()` **sem validação
de schema**. A ADR-007 registra que `severity` é uma chave **ignorada** nos fixtures de
plugin. O pack inverte isso: validação estrita, chave desconhecida = erro.

### 4.8 Versionamento e i18n

`src/updater.py` tem `__version__ = "1.3.0"` e `__lang_version__ = "v0.0.33"`. O
`parse_version()` é caseiro (`tuple(map(int, clean.split(".")))`) e **não sabe ler range**
— devolve `(0,0,0)` em qualquer coisa que não seja `X.Y.Z`. Para SemVer de verdade, é preciso
declarar `packaging` (que hoje **não** está em `pyproject.toml`).

O commit do risk scoring (c46440f) **não** tocou `updater.py`: nenhum bump de
`__lang_version__`. Três features seguidas mantiveram esse padrão.

### 4.9 O que já está pronto para o pack

- `.gitignore` ignora **apenas** `.gitpr/metrics/`; a ADR do ledger é explícita de que
  `.gitpr/skill/` "is NOT ignored — it is project content". `git check-ignore` confirma que
  `.gitpr/policy.lock.yml`, `.gitpr/policy.overrides.yml` e `.gitpr/fix_history.json` **não**
  estão ignorados. O requisito §7.1 (lockfile versionável) já está satisfeito.
- `src/domain/{linter,mentor,pr,risk,tests_generation}/`, `src/application/use_cases/` e
  `src/infrastructure/{git,linter,scm}/` já existem — a estrutura que a spec §3 propõe é a
  convenção vigente desde a ADR-009/ADR-010.
- `src/domain/__init__.py` **não** existe (namespace package); `src/domain/risk/__init__.py`
  existe. Os diretórios de teste das camadas novas também não levam `__init__.py`.

## 5. As 5 rodadas de entrevista

### Rodada 1 — Escopo e vocabulário

| # | Pergunta | Resposta |
|---|---|---|
| Q1 | Implementar a spec inteira (etapas 1–11) ou recortar num marco 1–7? | **Spec inteira** |
| Q2 | Usar os nomes inventados da spec (`rule_id`, `preset_file`, `severity: critical`) ou o vocabulário real? | **Nomes reais**; `config.schema.yml` → `src/config_schema.py` |
| Q3 | i18n: `__()` desde o início? Subir `__lang_version__`? | **`__()` com as chaves no repo, sem bump** |
| Q4 | Quantos idiomas na documentação? | **Matriz completa** — 5 docs + 5 READMEs |

### Rodada 2 — Morfologia

| # | Pergunta | Resposta |
|---|---|---|
| Q5 | Onde vivem os packs oficiais, dado que a raiz não é empacotada? | **`src/policy_packs/` + `package-data`** |
| Q6 | Reutilizar `~/.gitpr/plugins/` ou criar `~/.gitpr/policies/`? | **`~/.gitpr/policies/` próprio** |
| Q7 | Manter as superfícies sem consumidor (`test_patterns`, `protected_paths`, `required_sections`, `allowed_types`)? | **Tudo com consumidor real** |
| Q8 | O resolver é autoritativo sempre ou só com pack ativo? | **Só com pack ativo** |

### Rodada 3 — Contrato e proveniência

| # | Pergunta | Resposta |
|---|---|---|
| Q9 | `preset_file` colide com o vocabulário do wizard. Renomear? | **`linter.rules_file`** |
| Q10 | Como o cache reage a uma troca de política? | **`cache_scope` com `::policy::nome@versão::checksum`** |
| Q11 | Onde fica a config `policy:` da §11? | **Dividida: lockfile + `.env`/`GITPR_POLICY_*`** |
| Q12 | Onde vive o pack de uma equipe, ainda não instalado? | **`.gitpr/policies/<nome>/`** |
| Q13 | Como validar SemVer e range? | **Declarar `packaging`** |

### Rodada 4 — Resolução e conflito

| # | Pergunta | Resposta |
|---|---|---|
| Q14 | Vários packs ativos somam ou um substitui o outro? | **Substitui — um pack principal** |
| Q15 | Dois packs irmãos no DAG discordam de um escalar. O que acontece? | **Erro de validação, nomeando os dois** |
| Q16 | Dois packs definem uma regra de linter com o mesmo `name`. O que acontece? | **União por `name`, com precedência** |
| Q17 | Manter `RiskConfig.enabled`, que é código morto? | **Sai do schema** |

### Rodada 5 — Falha, justificativa e injeção

| # | Pergunta | Resposta |
|---|---|---|
| Q18 | Pack ausente / versão sumida / checksum divergente: abortar ou degradar? | **Aborta nos três casos** |
| Q19 | `reason` é obrigatório ao rebaixar severidade? | **Obrigatório ao rebaixar** |
| Q20 | Como a `EffectivePolicy` chega às 11 chamadas de `get_skill_context`? | **Global de módulo, lido por `get_skill_context`** |

### Decisões textuais (sem pergunta)

- `load_linter_rules(policy=None)`; overrides aplicados à lista **já mesclada**, incluindo as
  `SECURITY_RULES`; `parse_diff_and_lint` mantém a assinatura.
- Override nomeando regra inexistente é **erro de validação**, não warning.
- `install` = validar + copiar um diretório local para `~/.gitpr/policies/<nome>/`; sem
  download, sem "ref".
- `RiskConfig.enabled`/`include_in_review` ficam fora do schema; a flag morta é registrada
  como observação, não consertada (fora do escopo).
- `use`/`install`/`init --stack` seguem o precedente de `fix`/`split`:
  `click.confirm(default=False)`, `--yes` nunca pula a checagem de segurança, e
  `_may_ask_the_user()` (sem tty e sem `--yes` → falha com instrução, nunca escreve).
- Detector de stack novo e pequeno (`composer.json`+`artisan`, `package.json`+`vue`, …) em
  vez de repurposing `src/domain/tests_generation/framework_detector.py`.
- `tests/integration/` é criado, sem `__init__.py` (convenção de `tests/domain/`).

## 6. Conflito de regras do projeto

A §13 da spec manda "cada etapa deve ser um commit/PR isolado". O `CLAUDE.md` do projeto
proíbe terminantemente commit ou push por parte do agente. **O `CLAUDE.md` vence**: tudo
fica na árvore de trabalho, e a ordem de execução do plano é ordem, não sequência de commits.
