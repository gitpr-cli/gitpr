# Glossário — secret scanning no linter

> Vocabulário canônico da feature de detecção de segredo hardcoded no linter regex do GitPR.
> Mantido junto da [spec](20260921_skill_gitpr_secret_scanning_spec.md) e do [plano](20260921_skill_gitpr_secret_scanning_plan.md); os desvios aprovados vivem no [ADR-007](ADR-007-secret-ruleset-location-and-severity.md).
> Existe porque a spec usa três palavras — *preset*, *skill* e *severidade* — que já significam outra coisa neste repositório.

## Termos de domínio

| Termo | Definição |
|---|---|
| **security ruleset** | O conjunto de regras regex de detecção de segredo hardcoded que esta feature adiciona. Vive em módulo Python dentro de `src/` e entra no motor pelo mesmo caminho das demais regras. **Não** é uma skill, **não** é um preset. |
| **skill** | Persona de IA em `.gitpr/skill/.gitpr.<tipo>.md`, registrada em `SKILL_FILES_BY_TYPE` e editável pela tela de configuração. O catálogo de regras do linter é explicitamente *"a rule catalogue, not an AI persona"* ([src/config.py:135-141](../src/config.py#L135-L141)) e nunca foi uma skill — o security ruleset também não é. |
| **preset** | Termo **reservado** para linter externo: os catálogos remotos de PHPCS/ESLint/Stylelint consumidos pelo wizard `--linter-setup` (`templates/gitpr.linter-presets.json`, `~/.gitpr/conf/gitpr.linter-presets.json`). Não usar para pacote de regras regex. |
| **rule catalogue** | O arquivo `.gitpr/skill/.gitpr.linter.yml` (nome real, com ponto) — o conjunto **do usuário**, com as regras do projeto. Fica dentro da pasta de skills por herança histórica, mas não é uma skill. O wizard `--linter-setup` reescreve esse arquivo com `yaml.dump`, destruindo comentários e formatação ([src/linter_wizard.py:186-192](../src/linter_wizard.py#L186-L192)) — motivo pelo qual o security ruleset não é fundido nele. |
| **rule pack** | Pacote de regras em `~/.gitpr/plugins/linter/*.{yml,yaml}`, descoberto por varredura de extensão ([src/config.py:540-549](../src/config.py#L540-L549)). É **global à máquina**, aditivo e sem versionamento — serve para preferência pessoal, não para gate de CI de um projeto. |
| **rule** | Entrada do catálogo com as chaves que o motor lê: `name`, `level`, `regex`, `message`, `extensions`, `require_paths`, `ignore_paths`, `ignore_comments`. Não existem `id`, `category`, `pattern` nem `severity`. |
| **`name`** | A identidade de uma regra — "unique rule identifier (no spaces)" ([templates/gitpr.linter.yml:8](../templates/gitpr.linter.yml#L8)). Convenção do ruleset de segurança: kebab `sec-*` (ex.: `sec-aws-access-key`). É por esse nome que a lista de desligamento funciona. |
| **`level`** | A severidade. Aceita `error` e `warning`; **qualquer outro valor — incluindo `critical`, `blocker`, um typo ou a chave ausente — cai em `error`** ([src/linter_engine.py:57-63](../src/linter_engine.py#L57-L63)). |
| **alert** | A unidade de saída do linter — e não um "finding" estruturado. `parse_diff_and_lint` devolve `{"errors": [...], "warnings": [...]}` com strings já renderizadas (mensagem + arquivo + linha interpolados). Nenhum consumidor consegue refiltrar por regra ou caminho. |
| **gate** | Alerta de nível `error`. No fluxo `-l` termina em `sys.exit(1)` ([src/main.py:827](../src/main.py#L827)); no hook `pre-commit`, em `COMMIT BLOCKED!` ([scripts/pre-commit-template.sh:16-32](../scripts/pre-commit-template.sh#L16-L32)). |
| **advisory** | Alerta de nível `warning`. Aparece no relatório e no console, e o commit prossegue. |
| **`extensions: ["*"]`** | Extensão do motor que esta feature introduz: faz a regra valer para **todo** arquivo. Sem ela, "aplica a qualquer arquivo" é inexprimível e `.env`, `id_rsa` e `Dockerfile` ficam fora por construção. |
| **filtro de placeholder** | Rejeição de valores sabidamente de exemplo (`changeme`, `xxx`, `your_key_here`, `example`, `dummy`) por lookahead negativo dentro do próprio regex — porque o motor não tem `exclude_values` ([src/linter_engine.py:50](../src/linter_engine.py#L50) usa `re.search`, então lookaround funciona). |
| **não-eco** | Invariante da feature: nenhuma mensagem de regra pode conter o valor casado. O motor só substitui `{file_name}` e `{line_number}` ([src/linter_engine.py:51-55](../src/linter_engine.py#L51-L55)), então a redação é automática — e o teste existe para impedir que alguém a quebre escrevendo uma mensagem com amostra do segredo. |
| **match linha a linha** | Propriedade do motor: cada linha é testada isoladamente, após `.strip()`, sem `MULTILINE`/`DOTALL` ([src/linter_engine.py:50](../src/linter_engine.py#L50), [:299](../src/linter_engine.py#L299)). Regex com `\n` nunca casa; "contexto próximo entre linhas" é inexprimível. |
| **smart excludes** | Filtros aplicados **antes** do linter, na montagem do diff ([src/core.py:330](../src/core.py#L330), [:528](../src/core.py#L528)). Incluem a família de docs (`*.md`, `*.txt`, `*.rst`), `*.log`, lockfiles, minificados e imagens. O merge com o arquivo local do projeto é **união**, não override ([src/core.py:259-265](../src/core.py#L259-L265)): um projeto só acrescenta exclusões. |
| **ponto cego** | Nome curto para o efeito acima: um segredo vazado em README, log ou lockfile **não é detectado**, e o projeto não pode corrigir isso pela config. |
| **varredura retroativa** | Procurar segredo no histórico já commitado. Fora de escopo: a feature cobre apenas o diff corrente, como decidido na spec. |
| **proximidade entre linhas** | Conceito **inexistente** no motor, necessário para casar o par `AKIA…` + Secret Access Key "em contexto próximo". Sem ele, a regra de secret key fica fora do v1. |

## Chaves de configuração (dotenv plano, `~/.gitpr/.env`)

| Chave | Significado |
|---|---|
| `GITPR_LINTER_SECURITY` | Liga o security ruleset. Default `true`. Desligar remove as regras do merge — o resto do catálogo não é afetado. |
| `GITPR_LINTER_SECURITY_DISABLED_RULES` | Lista separada por `;` de `name` de regras a desligar (ex.: `sec-generic-credential-assignment;sec-db-connection-string`). Convenção de separador herdada de `GITPR_FIX_SAFE_EXCLUDED_PATHS`. |

Ambas precisam ser registradas em `FIELDS` ([src/config_schema.py](../src/config_schema.py)) na categoria `linter`: `tests/test_config_schema.py` falha se uma chave de `DEFAULT_CONFIG` ficar sem classificação.

Escapes existentes e **não** específicos desta feature: `git commit --no-verify`, `GITPR_SKIP_LINT`, `GITPR_SKIP_SMART_EXCLUDES` (desliga todos os excludes de uma vez).

## Notas de fidelidade

Cada nota registra uma premissa da spec que o código contradiz — verificado nesta sessão.

- **`severity` não existe.** A chave é `level` ([src/linter_engine.py:58](../src/linter_engine.py#L58)). A spec escreve `severity: blocker` / `severity: critical` (§3) — chave ignorada que **bloqueia**, exatamente o oposto do pretendido. `tests/test_plugins.py` já comete esse erro em oito fixtures.
- **Três níveis de severidade não existem.** Só `error` e `warning`; todo o resto é `error` ([src/linter_engine.py:57-63](../src/linter_engine.py#L57-L63)).
- **A lista fixa de presets não está em `core.py`.** Está em `src/config.py:142-151`, e o catálogo do linter está explicitamente fora dela.
- **`config.schema.yml` não existe.** O schema é `src/config_schema.py` (Python), com `ConfigField`/`FIELDS` e um teste de drift.
- **`presets/linter/` não existe**, e nada fora de `src/` entra no wheel ([pyproject.toml:30-32](../pyproject.toml#L30-L32) declara só `src`/`src.*`).
- **`src/domain/` não existe.** As features são pacotes planos (`src/fix/`, `src/review/`, `src/split/`) ou módulos planos (`src/linter_engine.py`).
- **`gitpr --linter security` é impossível**: `-l/--linter` é `is_flag=True` ([src/main.py:298-303](../src/main.py#L298-L303)).
- **`id` e `category` não existem** no schema de regra; a identidade é `name`.
- **`exclude_values` não existe**, mas é dispensável: lookahead negativo resolve.
- **Supressão inline não existe** — nenhum mecanismo, em lugar nenhum do repositório.
- **Não existe override por regra.** Local + plugins são concatenados sem dedup nem precedência ([src/config.py:562-612](../src/config.py#L562-L612)); a spec supõe (§5) que existe e manda reusá-lo.
- **O motor casa linha a linha**, sem exceção — a spec supõe contexto entre linhas para o par `AKIA…` + Secret Access Key citado na §1.
- **O relatório do linter é `.md`**, não `.txt` (`.txt` é de review/blame/issue), e fica em `.gitpr/reports/linter/`.
- **A doc do hook já promete bloqueio de "passwords"** ([docs/git-hooks-locais.md:31-34](../docs/git-hooks-locais.md#L31-L34)) que nenhuma regra implementa — a feature fecha essa promessa.
- **Nenhum prompt de IA procura segredo**: a divisão de responsabilidade do passo §0.4 é trivial, porque não há sobreposição.
