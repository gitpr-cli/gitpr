# Plano de execução — Policy Packs (branch `develop_natan`)

> Execução da spec [20261009_skill_gitpr_policy_packs_spec.md](../20261009_skill_gitpr_policy_packs_spec.md),
> decidida em entrevista de 5 rodadas (2026-10-09). O levantamento que originou este plano
> vive em [20261009_policy_packs_surveyfacts.md](../../survey/20261009_policy_packs_surveyfacts.md);
> o vocabulário canônico, no [glossário](../glossary-policy-packs.md); a decisão de
> arquitetura, no [ADR-011](../ADR-011-policy-packs.md).

## Contexto

A spec quer unificar skills, regras de linter, severidade, caminhos críticos, risco e
convenções de PR/commit num **Policy Pack**: um manifesto YAML versionável que uma equipe
aplica em vários repositórios. Hoje cada uma dessas coisas se configura num lugar
diferente — `.gitpr/skill/.gitpr.review.md`, `.gitpr/skill/.gitpr.linter.yml`,
`.gitpr/skill/gitpr.risk.yml`, `~/.gitpr/.env` — e nada amarra o conjunto.

O resultado pretendido: um repositório declara `gitpr/laravel-quality@1.0.0` num lockfile
versionado, e review, linter e risk score passam a operar sob a mesma política, com
proveniência rastreável e sem download remoto.

A spec foi escrita sem conhecer o código. Seis premissas dela caíram no levantamento
(§2 do survey) e estão corrigidas neste plano.

## Passo 0 — Artefatos da sessão

| Arquivo | Papel |
|---|---|
| `docs/survey/20261009_policy_packs_surveyfacts.md` | Levantamento completo: premissas derrubadas, 5 rodadas, 20 decisões |
| `docs/plans/develop_natan/20261009_policy_packs_plansfacts.md` | Este plano |
| `docs/plans/glossary-policy-packs.md` | Vocabulário canônico |
| `docs/plans/ADR-011-policy-packs.md` | ADR da arquitetura de packs |

## Correções de premissa (a spec × o código real)

| A spec diz | A realidade | Decisão |
|---|---|---|
| `src/domain/policy/`, `src/application/use_cases/`, `src/infrastructure/policy/` são novos | Já é a convenção desde a ADR-009/ADR-010 | Mantido |
| `policy-packs/` na raiz do repo | Raiz não é empacotada: `include=["src","src.*"]`, `pyproject.toml` sem `package_data`/`MANIFEST.in`. O wheel 1.3.0 tem só `.py` | `src/policy_packs/` + `[tool.setuptools.package-data]` novo |
| "ALTERAR `config.schema.yml`" | Nunca existiu (3 relatórios registram o desvio). O alvo é `src/config_schema.py` (1186 linhas, 14 categorias, 56 campos) | Alterar o módulo |
| `SeverityOverride(rule_id, severity)` com `severity: critical` | Chave real é `name` + `level` ∈ {`error`,`warning`}. `critical` é nível de **risco** (`RiskLevel.CRITICAL`), e a ADR-007 registra a rejeição explícita de um terceiro nível de linter | `SeverityOverride(rule_name, level)` |
| `risk.test_patterns`, `protected_paths`, `pr.required_sections`, `commit.allowed_types` | Nenhum tem consumidor no código | `test_patterns` vira chave real de `RiskConfig`; os outros três são contexto de prompt |
| `__lang_version__` (implícito) | Três features seguidas não subiram o marcador | Chaves no repo, **sem bump** |
| Precedência: … → CLI (6) → env (7) | `--provider` vence `DEFAULT_AI_PROVIDER`; `--base` vence `PR_DEFAULT_BASE` | Invertido: CLI acima de env |
| `linter.preset_file` | "Preset" já significa binário externo (`linter_wizard._LINTER_PRESETS`) | Renomeado para `linter.rules_file` |

**Descoberta que a spec não previu:** o `skill_context` **não entra na chave de cache**.
Em `src/core.py` o `instrucao_sistema` (que carrega o `skill_context`) é argumento separado
do `prompt`, e o cache é lido com `get_cached_response(action_folder, prompt + cache_scope)`.
Sem tratar, ativar um pack num diff já cacheado não mudaria nada e o rótulo `policy name@version`
da §7.3 mentiria. O `cache_scope` existe exatamente para isto e o `DiffSource` já o usa.

## Decisões fixadas no grill

**Entrega** — spec inteira (etapas 1–11 da §13); nomes reais do projeto; `__()` com as chaves
no repositório e **sem** bump de `__lang_version__`; matriz completa de docs (5 idiomas +
5 READMEs + categoria em `config_schema.py`).

**Morfologia** — packs bundled em `src/policy_packs/`; instalados em `~/.gitpr/policies/`;
pack da equipe em `.gitpr/policies/<nome>/`; lockfile e overrides em `.gitpr/` (já
versionáveis — só `.gitpr/metrics/` está no `.gitignore`); config `policy:` **dividida**:
`active` no lockfile, `GITPR_POLICY_*` em `~/.gitpr/.env` + campos no `config_schema.py`;
`packaging` declarado em `pyproject.toml` **e** `Pipfile`.

**Contrato** — skills, regras de linter e `name`+`level` por injeção direta; pesos,
thresholds, `critical_paths` e `test_patterns` por injeção em `RiskConfig`;
`pr.required_sections`, `commit.allowed_types` e `protected_paths` como contexto de prompt;
`enabled` **fora** do schema; regras de linter em **união por `name` com precedência**;
override para regra inexistente é **erro**; `reason` **obrigatório** ao rebaixar
(`error`→`warning`).

**Comportamento** — o resolver só é autoritativo **com pack ativo** (sem pack,
`load_risk_config()` intocado); precedência `defaults → deps (topológica) → root →
overrides → CLI → env`; **um pack principal** (`use` substitui); irmãos no DAG discordando
de escalar = **erro de validação**; falha de resolução (pack ausente, versão sumida após
upgrade, checksum divergente) = **aborta**; `cache_scope` ganha
`::policy::<nome>@<versão>::<checksum>`; a política é publicada num **global de módulo**
que `get_skill_context` consulta (precedente: `src/i18n.py`, onde `set_lang()` reatribui
`CURRENT_LANG`/`TRANSLATIONS`).

**Conflito de regras do projeto:** a §13 manda um commit por etapa; o `CLAUDE.md` **proíbe**
commitar. O `CLAUDE.md` vence — tudo fica na árvore de trabalho, e a sequência abaixo é
ordem de execução, não de commit.

## Fase 1 — Domínio (etapas 1–2)

`src/domain/policy/` com `__init__.py` re-exportando a superfície (`src/domain/__init__.py`
não existe e não deve ser criado).

| Arquivo | Papel |
|---|---|
| `policy_types.py` | `PolicySource`, `PackReference`, `SkillPolicy`, `SeverityOverride`, `EffectivePolicy`, `PolicyManifest`, `PolicyError` |
| `policy_manifest.py` | Parsing e validação estrita (chave desconhecida = erro); `name` namespace/nome sem traversal; reuso das regex de `src/security_ruleset.py` para recusar segredo |
| `policy_compatibility.py` | `min_gitpr_version` × `updater.__version__` via `packaging.specifiers.SpecifierSet`; nomes de skill contra `config.SKILL_TYPES`; contenção de caminho de asset |
| `policy_resolver.py` | Ordenação topológica de `extends`, ciclo com a cadeia na mensagem, conflito entre irmãos, união ordenada, provenance, orçamento de contexto |
| `policy_checksum.py` | SHA-256 de `policy.yml` + assets declarados |

## Fase 2 — Casos de uso (etapa 2)

`src/application/use_cases/`: `validate_policy_pack.py`, `install_policy_pack.py`,
`activate_policy_pack.py`, `resolve_effective_policy.py`. O último roda uma vez no boot,
publica o global de módulo e é o **único** lugar que lê `policy.yml` (§8.3).

## Fase 3 — Infraestrutura

`src/infrastructure/policy/policy_pack_loader.py` (YAML + descoberta das três origens) e
`local_policy_repository.py` (leitura/escrita de `~/.gitpr/policies/`, `.gitpr/policies/`,
`policy.lock.yml`, `policy.overrides.yml`).

## Fase 4 — Packs oficiais (etapas 5 e 9)

`src/policy_packs/{laravel-quality,vue-quality,php-security,node-quality}/` com `policy.yml`,
`linter.yml` e `README.md` (+ `CHANGELOG.md` no laravel-quality). `laravel-quality extends
php-security`. Todos com `min_gitpr_version: ">=1.3.0"`. Mais o bloco
`[tool.setuptools.package-data]` no `pyproject.toml` — que não existe hoje.

Packs pequenos e opinativos, como a §9.4 pede.

## Fase 5 — Integração (etapa 6)

| Arquivo | Mudança |
|---|---|
| `src/core.py` | `get_skill_context` consulta a política; `generate_pr_content` soma `::policy::…` ao `cache_scope` |
| `src/config.py` | `load_linter_rules(policy=None)` — união por `name` com precedência, depois do merge das `SECURITY_RULES`; leitores `GITPR_POLICY_*` |
| `src/config_schema.py` | categoria `"policy"` + campos `GITPR_POLICY_*` |
| `src/application/use_cases/calculate_risk.py` | repassa o `RiskConfig` efetivo pelo parâmetro `config=` que já existe |
| `src/domain/risk/risk_rules.py` | `test_patterns` como chave real de `RiskConfig`; `is_test_file()` passa a consumi-la |
| `src/infrastructure/git/test_matcher.py` | idem |
| `src/linter_engine.py` | **sem mudança de assinatura** — a injeção é via `load_linter_rules` |
| `pyproject.toml`, `Pipfile` | declarar `packaging` |

`RiskConfig.enabled` e `include_in_review` são parseados e nunca lidos — não entram no
schema do pack. A flag morta fica registrada como observação, sem ser consertada.

## Fase 6 — CLI (etapas 7–8)

Grupo `policy` em `src/main.py`, modelado no grupo `metrics`: `@cli.group` com
`context_settings={"help_option_names": ["-h","--help"]}` e epilog com `get_doc_url`.

- Leitura primeiro: `list`, `validate`, `show`.
- Escrita depois: `use`, `install`, `init --stack` — `click.confirm(default=False)`, `--yes`
  que pula a confirmação mas nunca a checagem, e `_may_ask_the_user()` para não travar em
  pipe/CI.
- `install` sem registry não tem "ref": valida e copia um diretório local. Nenhum download.
- `init --stack` usa um detector novo e pequeno, em vez de forçar o `framework_detector`
  de testes a servir dois propósitos.

## Fase 7 — Testes

`tests/domain/policy/` (4 arquivos) e `tests/application/use_cases/` (3 arquivos) — ambos
existem e não levam `__init__.py`. `tests/integration/` é criado, também sem `__init__.py`,
com `conftest.py` local (fixture autouse `no_network`) e repos reais via
`tests/fix/git_fixture.py`. Os 13 critérios de aceite da §12 viram asserções nomeadas, com
o critério 10 (não-regressão sem pack) como teste de primeira classe.

## Fase 8 — Documentação (etapas 10–11)

`docs/policy-packs.{md,pt_br,pt_pt,es_es,fr_fr}.md`; entrada de comando nos 5 `README.*.md`
+ link na seção de documentação técnica; chaves novas em `langs/*.json` **sem** subir
`__lang_version__`; categoria `"policy"` na tela de configuração.

Depois: `docs/claude-code/reports/develop_natan/2026-10-09_policy_packs.md`.

## Verificação

1. **Suíte completa** — `python -m pytest tests/ -v`. `tests/test_skill_context.py` e
   `tests/test_plugins.py` são os sensores mais próximos das mudanças em `get_skill_context`
   e `load_linter_rules`.
2. **Não-regressão sem pack** — sem `.gitpr/policy.lock.yml`, `gitpr -r`, `gitpr -l`,
   `gitpr risk` e `gitpr` (PR) produzem a saída de antes (§12.10).
3. **Ciclo completo num fixture Laravel** — `policy list` → `policy validate` →
   `policy init --stack laravel` → `policy show`.
4. **Efeito real e rastreável** — o review anexa o contexto do pack, o linter obedece ao
   `rules_file` e aos overrides de `level`, o risk usa `critical_paths`/`test_patterns`.
5. **Cache** — `gitpr -r` num diff cacheado antes e depois de `policy use` produz reviews
   diferentes. É a prova de que o `cache_scope` funciona.
6. **Integridade** — asset editado ou pack removido de `~/.gitpr/policies/`: aborta com
   mismatch de checksum e diz como reativar.
7. **Sem execução arbitrária** — traversal, skill inexistente, chave desconhecida, `reason`
   ausente num rebaixamento e segredo no manifesto falham sem rede e sem subprocesso.
8. **Empacotamento** — `python -m build` e o wheel contém `src/policy_packs/**/*.yml`.
9. **CLI sem tty** — `gitpr policy use ... < /dev/null` sem `--yes` falha com instrução,
   não trava e não escreve.
