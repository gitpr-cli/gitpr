# Secret scanning no linter do GitPR — documentos da sessão de grill

## Contexto

A spec [docs/plans/20260921_skill_gitpr_secret_scanning_spec.md](docs/plans/20260921_skill_gitpr_secret_scanning_spec.md) propõe um preset de segurança no linter regex. Ela foi escrita supondo uma estrutura de repositório que **não é esta**: assume `core.py` com a lista de presets, `config.schema.yml`, `presets/linter/`, `src/domain/`, severidade em três níveis (`blocker`/`critical`/`warning`), `id`/`category`/`exclude_values` no schema de regra, override por regra e supressão inline — **nenhum desses existe**. Três explorações read-only mapearam o código real e uma sessão de grill de três rodadas fechou 10 decisões.

Esta sessão **não implementa código** (Q1=b). Ela produz os documentos que substituem a spec como fonte de verdade e permitem implementar depois sem nova rodada de perguntas.

## Entregáveis

| Caminho                                                      | Artefato                                                                                                   | Origem                                             |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `docs/survey/20260921_gitpr_secret_scanning_surveyfacts.md`  | Survey da sessão (obrigatório da skill `grill-with-docs`)                                                  | estrutura fixa das surveys anteriores              |
| `docs/plans/20260921_skill_gitpr_secret_scanning_plan.md`    | Plano de implementação que substitui a spec                                                                | decisões Q1–Q10 + fatos                            |
| `docs/plans/glossary-gitpr-secret-scanning.md`               | Glossário canônico (termos + chaves de config + notas de fidelidade)                                       | convenção `docs/plans/glossary-<feature>.md`       |
| `docs/plans/ADR-007-secret-ruleset-location-and-severity.md` | ADR: por que não existe terceiro nível de severidade e por que o ruleset é separado do catálogo do usuário | convenção `ADR-NNN-<slug>.md` (próximo livre: 007) |

A spec original **não é alterada** — fica como registro do que foi pedido; as divergências vão nas "Notas de fidelidade" do glossário e no §2 do survey.

## Decisões fechadas (conteúdo do §3 do survey)

| #   | Decisão                                                                                                                                                                                                              |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Q1  | Entregável = documentos; implementação em sessão separada                                                                                                                                                            |
| Q2  | Gate (`error`) só nas categorias de altíssima confiança. Connection string e credencial genérica = `warning`, nunca gate                                                                                             |
| Q3  | Não estender o vocabulário de severidade: `error`/`warning` apenas                                                                                                                                                   |
| Q4  | Ruleset mora em **módulo Python dentro de `src/`** (nada fora de `src/` entra no wheel: [pyproject.toml:30-35](pyproject.toml#L30-L35) não tem `package-data`). Ativação por chave de config; desligamento por regra |
| Q5  | Redação do valor casado é automática (o motor só substitui `{file_name}`/`{line_number}`) → vira invariante testado                                                                                                  |
| Q6  | Termo canônico **"security ruleset"**; `preset` permanece reservado para linter externo (`gitpr.linter-presets.json`)                                                                                                |
| Q7  | `extensions: ["*"]` no motor: sem isso, "aplica a todo arquivo" é inexprimível e `.env`/`id_rsa`/`Dockerfile` ficam de fora                                                                                          |
| Q8  | "AWS Secret Access Key em contexto próximo" fica fora do v1 (exigiria janela de proximidade entre linhas — conceito inexistente no motor)                                                                            |
| Q9  | Ponto cego dos smart excludes aceito e documentado (`.md`, `.txt`, `*.log`, lockfiles nunca chegam ao linter; união de listas impede remoção por projeto)                                                            |
| Q10 | Prompts de review da IA não são alterados (evita invalidar o cache MD5 e um segundo caminho não determinístico)                                                                                                      |

Assumido e confirmado: o ruleset roda em **todos** os fluxos que chamam o linter — `-l`, `-r`, `-f`, `--input`, MCP `run_linter`, badge, publish de PR e `review-pr` — porque é o mesmo motor e não há caminho paralelo.

## Desenho técnico que os documentos devem registrar

- **Motor** (2 mudanças cirúrgicas): `_is_rule_applicable` aceita `"*"` em `extensions` ([src/linter_engine.py:13-37](src/linter_engine.py#L13-L37)); `load_linter_rules()` passa a concatenar o ruleset de segurança quando a chave de config estiver ligada ([src/config.py:562-612](src/config.py#L562-L612)).
- **Ruleset** em `src/security_ruleset.py`: lista de regras no schema real do motor — `name` (kebab `sec-*`, é a única identidade), `level`, `extensions: ["*"]`, `regex`, `message`. Sem `id`, `category`, `severity` ou `exclude_values`.
- **Filtro de placeholder sem `exclude_values`**: lookahead negativo dentro do próprio regex — `(?!(?:changeme|xxx+|your[_-]?(?:key|password|secret)_here|placeholder|example|dummy)['"])`. O motor usa `re.search`, então lookaround funciona; o fallback que a spec abria (§3) não é necessário.
- **Regras v1**: `error` para AWS access key (`AKIA[0-9A-Z]{16}`), token GitHub (`gh[pousr]_…`), token Slack (`xox[baprs]-…`), chave Google (`AIza…`), bloco de chave privada (`-----BEGIN [A-Z ]*PRIVATE KEY-----`); `warning` para connection string com credencial e atribuição genérica de credencial.
- **Config**: `GITPR_LINTER_SECURITY` (bool, default `true`) e `GITPR_LINTER_SECURITY_DISABLED_RULES` (lista separada por `;`, convenção de `GITPR_FIX_SAFE_EXCLUDED_PATHS`) — ambas registradas em `src/config_schema.py` na categoria `linter`, senão `tests/test_config_schema.py` falha.
- **Risco registrado**: regex inválida vira erro **bloqueante** ([src/linter_engine.py:64-71](src/linter_engine.py#L64-L71)) — um typo no ruleset bloqueia todo commit do usuário. Exige teste de compilação de todas as regras.
- **Limitações conhecidas** a documentar: match é linha a linha com `.strip()` prévio; só linhas `+` são checadas; `.env` e `id_rsa` cobertos, docs/logs/lockfiles não (smart excludes); `--linter` continua flag booleana, sem `--linter security`.
- **Testes**: `tests/test_security_ruleset.py` — positiva/negativa por categoria, filtro de placeholder, aplicabilidade a arquivo sem extensão, invariante de não-eco, e integração real via `parse_diff_and_lint` provando que rule de segurança cai em `errors` vs `warnings` corretamente ([src/linter_engine.py:57-63](src/linter_engine.py#L57-L63)).
- **Docs a atualizar na fase de implementação**: [docs/linter-regras-customizadas.md](docs/linter-regras-customizadas.md) (+ `.pt_br`, hoje omite a chave `level`), [docs/git-hooks-locais.md:31-34](docs/git-hooks-locais.md#L31-L34) (já promete bloqueio de "passwords" que nenhuma regra implementa), e a seção de linter do `CLAUDE.md`.

## Verificação

1. Os quatro arquivos existem nos caminhos da tabela; o survey segue a estrutura das surveys anteriores (`# Survey — …`, blockquote de identificação, `---`, §1 Contexto / §2 Relatório de fatos / §3 Decisões / §4 Síntese).
2. O survey e o glossário citam `arquivo:linha` reais — nenhuma afirmação sobre o código sem referência verificável.
3. Nenhum arquivo de código é tocado nesta sessão; `python -m pytest tests/ -q` continua no mesmo estado de antes (a suíte não é afetada).
4. O plano de implementação lista etapas executáveis isoladamente, cada uma com o teste que a valida — critério de pronto sem depender de nova decisão de produto.
