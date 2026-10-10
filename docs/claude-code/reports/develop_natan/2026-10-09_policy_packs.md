## Completion Report — Policy Packs (`gitpr policy`)

> Relatório de implementação. A especificação está em
> [docs/plans/20261009_skill_gitpr_policy_packs_spec.md](../../../plans/20261009_skill_gitpr_policy_packs_spec.md);
> o levantamento (com as 5 premissas da spec que caíram), em
> [docs/survey/20261009_policy_packs_surveyfacts.md](../../../survey/20261009_policy_packs_surveyfacts.md);
> o plano aprovado (5 rodadas, 20 decisões), em
> [docs/plans/develop_natan/20261009_policy_packs_plansfacts.md](../../../plans/develop_natan/20261009_policy_packs_plansfacts.md);
> o vocabulário canônico, em
> [docs/plans/glossary-policy-packs.md](../../../plans/glossary-policy-packs.md);
> a decisão de arquitetura, em
> [docs/plans/ADR-011-policy-packs.md](../../../plans/ADR-011-policy-packs.md).

### What was done

Um repositório passa a declarar `gitpr/laravel-quality@1.0.0` num lockfile versionado
(`.gitpr/policy.lock.yml`), e review, linter e risk score passam a operar sob a mesma
política — com proveniência rastreável por campo e sem nenhum download remoto.

A spec foi escrita sem conhecer o código: **cinco premissas caíram** no levantamento
(`policy-packs/` na raiz não é empacotada, `config.schema.yml` nunca existiu, a chave do
override é `name`+`level` e não `severity`/`critical`, quatro chaves não tinham consumidor,
e a CLI vence o env — não o contrário). Todas estão corrigidas abaixo, e uma descoberta
que a spec não previu — o `skill_context` não entra na chave do cache MD5 — virou o
`cache_scope()` da política.

1. **`src/domain/policy/`** (novo, 6 módulos, ~1875 linhas) — o núcleo puro.
   `policy_types.py` (`PolicySource`, `PackReference`, `SkillPolicy`, `SeverityOverride`,
   `EffectivePolicy`), `policy_manifest.py` (schema **fechado**: chave desconhecida, skill
   fora do registro de 11 tipos, `reason` ausente num rebaixamento e credencial detectada
   pelo `security_ruleset` são todos erro), `policy_compatibility.py` (`min_gitpr_version`
   via `packaging.specifiers`, contenção do caminho de asset), `policy_resolver.py`
   (ordenação topológica de `extends` com a cadeia no ciclo, conflito entre irmãos,
   união ordenada de listas, precedência de severidade, concatenação do contexto com
   delimitadores de origem e teto de caracteres) e `policy_checksum.py` (SHA-256 do
   manifesto + assets).
2. **`src/application/use_cases/`** (4 novos) — `validate_policy_pack` (o veredito
   estrito, com o desenvolvedor olhando), `install_policy_pack`, `activate_policy_pack`
   (`use` substitui, como decidido) e `resolve_effective_policy` — este roda uma vez no
   boot, é o **único** lugar que lê `policy.yml` e publica a política num global de
   módulo (`set_active_policy()`, espelhando `src/i18n.set_lang()`). Sem pack ativo ele
   não toca em nada e devolve uma política vazia.
3. **`src/infrastructure/policy/`** (novo) — `policy_pack_loader.py` descobre as três
   origens na ordem mais próxima primeiro (`.gitpr/policies/<nome>/` → `~/.gitpr/policies/`
   → `src/policy_packs/`) e `local_policy_repository.py` lê/escreve lockfile, overrides e
   o diretório instalado.
4. **`src/policy_packs/`** (novo, 4 packs) — `laravel-quality` (estende `php-security`),
   `php-security`, `vue-quality` e `node-quality`, cada um com `policy.yml`, `linter.yml`
   e `README.md`. Todos com `min_gitpr_version: ">=1.3.0"`.
5. **Integração** — `get_skill_context()` anexa o contexto do pack depois do arquivo
   local (e o devolve sozinho quando o repositório não tem skill própria);
   `generate_pr_content()` soma `::policy::<nome>@<versão>::<checksum>` à chave do cache
   (o `instrucao_sistema` é argumento separado e o MD5 não o vê, então sem isso a review
   cacheada sobreviveria à ativação do pack e o artefato carregaria o nome da política
   nova sobre a review da anterior); `load_linter_rules(policy=None)` ganhou a camada do
   pack **sob** o `.gitpr.linter.yml` e **sobre** o ruleset de segurança embutido, com os
   `severity_overrides` aplicados por último, contra o catálogo final;
   `calculate_risk` repassa o `RiskConfig` efetivo e `test_patterns` virou chave real de
   `RiskConfig`, consumida por `is_test_file()`/`requires_tests()`/`find_related_test_files()`.
6. **CLI** — grupo `policy` em `src/main.py` (582 linhas) com `list`, `validate`, `show`,
   `use`, `install`, `init --stack` e `off` (o `off` foi além da spec: sem ele o único
   jeito de voltar ao padrão seria editar o lockfile à mão). Leitura primeiro, escrita
   depois, com `click.confirm(default=False)`, `--yes` que pula a confirmação mas nunca a
   checagem, e um guarda de escrita que se recusa a gravar quando não há terminal.
7. **Configuração** — categoria `policy` em `src/config_schema.py` com
   `GITPR_POLICY_ENABLED` e `GITPR_POLICY_CONTEXT_MAX_CHARACTERS` (12000), semeados em
   `DEFAULT_CONFIG`. O pack ativo **não** é configuração de máquina: mora no lockfile do
   repositório, para poder ser revisado junto do código a que se aplica.
8. **Empacotamento** — `[tool.setuptools.package-data]` em `pyproject.toml` (bloco que
   não existia) e `packaging` declarado em `pyproject.toml` **e** `Pipfile`.
9. **Testes** — 224 testes novos em 9 módulos (domínio, casos de uso, integração com
   repositório git real e CLI), com os 13 critérios de aceite da §12 da spec como
   asserções nomeadas — incluindo o critério 10 (não-regressão sem pack) como teste de
   primeira classe.
10. **Documentação** — `docs/policy-packs.{md,pt_br,pt_pt,es_es,fr_fr}.md` (7 seções cada),
    entrada de comando e link na lista de documentação técnica dos 5 `README.*.md`, e as
    129 chaves novas traduzidas nos 6 arquivos de `langs/` — **sem** subir
    `__lang_version__`, como decidido no grill.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/domain/policy/` (6 arquivos) | feat | Tipos, manifesto de schema fechado, compatibilidade, resolver, checksum |
| `src/application/use_cases/{validate,install,activate,resolve}_policy_pack.py` | feat | Verificar, instalar, ativar e resolver a política efetiva |
| `src/application/use_cases/resolve_effective_policy.py` | feat | Único leitor de `policy.yml`; publica o global de módulo |
| `src/infrastructure/policy/{policy_pack_loader,local_policy_repository}.py` | feat | Descoberta das três origens; lockfile/overrides |
| `src/policy_packs/**` (13 arquivos) | feat | Quatro packs oficiais (yml + linter + README) |
| `src/main.py` | feat | Grupo `policy` com 7 comandos, guarda de escrita e epilog de doc |
| `src/config.py` | feat | `load_linter_rules(policy=None)`, merge de camadas, overrides de severidade, leitores `GITPR_POLICY_*` |
| `src/core.py` | feat | `get_skill_context` consulta a política; `cache_scope()` na chave do cache |
| `src/config_schema.py` | feat | Categoria `policy` + `GITPR_POLICY_ENABLED` e `GITPR_POLICY_CONTEXT_MAX_CHARACTERS` |
| `src/domain/risk/risk_rules.py` | feat | `test_patterns` como chave real de `RiskConfig`; `is_test_file(path, test_patterns)` |
| `src/infrastructure/git/test_matcher.py` | feat | `test_patterns` em `find_related_test_files`/`requires_tests` |
| `src/application/use_cases/calculate_risk.py` | feat | Aplica a política sobre o `RiskConfig` do projeto |
| `src/linter_engine.py` | refactor | `load_linter_rules(get_active_policy())` — sem mudança de assinatura pública |
| `pyproject.toml`, `Pipfile` | chore | `packaging` + `[tool.setuptools.package-data]` |
| `langs/{pt_br,pt_pt,es_es,es,fr_fr,fr}.json` | feat | 129 chaves novas por idioma (1308 → 1437), paridade exata entre os seis |
| `README*.md` (5) | docs | Entrada de comando + link da seção de documentação técnica |
| `docs/policy-packs*.md` (5) | docs | Documentação da feature em 5 idiomas |
| `docs/plans/{ADR-011,glossary}-policy-packs.md`, `docs/plans/develop_natan/20261009_policy_packs_plansfacts.md`, `docs/survey/20261009_policy_packs_surveyfacts.md` | docs | ADR, glossário, plano e levantamento da sessão |
| `tests/domain/policy/` (4), `tests/application/use_cases/test_*_policy_pack.py` (3), `tests/integration/` (2), `tests/test_policy_cli.py` | test | 224 testes novos |

### Impact

- **Functionality:** sem pack ativo, **nada muda** — `get_active_policy()` devolve uma
  política inativa, `risk_config_from_policy` devolve o mesmo objeto que
  `load_risk_config()` produziu, `load_linter_rules()` monta a lista na ordem de antes e
  `cache_scope()` é `""`. Com pack ativo, o contexto do pack entra no prompt (com
  delimitadores de origem e teto de caracteres), o linter obedece ao `rules_file` e aos
  overrides de `level`, e o risk score ganha `critical_paths`/`test_patterns`/pesos.
- **Performance:** a política é resolvida uma vez por processo, no boot, e o resultado
  fica no global de módulo — nenhum `policy.yml` é lido no meio de um fluxo. O checksum
  SHA-256 roda sobre o manifesto e os assets declarados, não sobre os arquivos alterados.
- **Compatibility:** dois campos novos na tela de configuração e duas variáveis de
  ambiente; nenhuma quebra de CLI (o grupo `policy` é novo, nenhuma flag existente mudou
  de nome ou de posição). `packaging>=23.0` é dependência nova — `pipenv install --dev`
  depois de puxar a branch. A chave de cache ganhou um sufixo **apenas com pack ativo**,
  então nenhuma entrada de cache existente é invalidada por esta feature.

### Verification

| Item do plano | Resultado |
|---|---|
| Suíte completa | Duas execuções: 3 falhas/2373 passam e, na repetição, 2 falhas/2374 passam (2 pulados e 134 subtestes em ambas) — as falhas estão detalhadas abaixo e **nenhuma é desta feature** |
| Testes da feature, isolados | 224 passam, 53 subtestes |
| Não-regressão sem pack (§12.10) | Teste de primeira classe em `tests/integration/test_policy_effect_on_review_linter_risk.py` |
| Efeito real e rastreável | `show` imprime a ladeira de precedência com a origem de cada campo; o linter e o risk score mudam com o pack |
| Cache | Review do mesmo diff antes e depois de `gitpr policy use` produz resultados diferentes (é o `cache_scope`) |
| Integridade | Asset editado ou pack removido abortam com a instrução de reativação |
| Sem execução arbitrária | Caminho que escapa do pack, skill inexistente, chave desconhecida, `reason` ausente e segredo detectado falham na validação, sem rede e sem subprocesso |
| Empacotamento | Wheel 1.3.0 contém os 13 arquivos dos 4 packs (antes o wheel só tinha `.py`) |
| CLI sem tty | `policy use/init/off/install < /dev/null` sem `--yes` falha com a instrução e não escreve nada |

Falhas da suíte completa, todas investigadas:

1. `tests/test_metrics.py::TestCycleReport::test_a_bare_call_reads_a_month_and_says_so` —
   **pré-existente**, já falhava no baseline desta sessão; a seção de ciclo é a única
   métrica que pergunta à rede, e `src/ledger.py`/`src/metrics.py` não foram tocados.
2. `tests/test_metrics.py::TestCycleLines::test_an_empty_window_says_so_instead_of_showing_zero`
   — mesma origem.
3. `tests/test_config_app.py::TestExit::test_confirming_the_discard_leaves_the_screen` —
   falhou na primeira execução da suíte completa e **não reproduziu na segunda**; passa
   isolado (1 teste) e com o módulo inteiro (78 testes). É dependência de ordem/tempo do
   TUI (Textual), não da categoria nova: nenhuma asserção do módulo conta linhas ou
   categorias da tela.

### Observações e desvios

1. **A §13 da spec manda um commit por etapa; o `CLAUDE.md` proíbe commitar.** O
   `CLAUDE.md` venceu: tudo está na árvore de trabalho, e a sequência de fases acima é
   ordem de execução, não de commit.
2. **`gitpr policy off` não está na spec** — foi acrescentado porque a spec descrevia a
   saída do pack apenas por edição manual do lockfile.
3. **`__lang_version__` não subiu**, como decidido no grill. Consequência prática: o
   runtime carrega `~/.gitpr/langs/*.json` e só rebaixa o arquivo quando o marcador muda,
   então as 129 chaves novas chegam ao usuário **no próximo release**, quando o marcador
   for bumpado e os `langs/` estiverem em `main`.
4. **`tests/sync_i18n.py` não pode ser rodado às cegas.** O extrator regex dele captura só
   o primeiro fragmento de uma concatenação implícita (`__("a" "b")` → `"a"`), enquanto o
   extrator AST de `tests/test_i18n.py` junta os fragmentos: hoje os dois discordam em 78
   chaves. Rodar o sync deixaria 78 chaves reais ausentes **e** inseriria 78 fragmentos
   truncados como órfãos, quebrando `test_no_missing_keys` e `test_no_orphan_keys` ao
   mesmo tempo. As 129 chaves foram computadas pelo extrator do teste e traduzidas à mão.
5. **Quatro chamadas `__(..., key=...)` escondiam uma chave errada** e foram corrigidas
   durante a feature: o kwarg `key` colide com o primeiro parâmetro posicional de `__()`,
   então a chave real era o literal anterior. Um teste-guarda para isso ficou como
   sugestão (abaixo), não como escopo.
6. **O checksum normaliza CRLF.** Um pack editado no Windows com fim de linha diferente
   não aborta por isso — a normalização está documentada em `docs/policy-packs.md` §4.1.
7. **Latência morta observada, não consertada:** `RiskConfig.enabled` e
   `RiskConfig.include_in_review` são parseados e nunca lidos. Ficaram **fora** do schema
   do pack (declarar no manifesto um campo que ninguém lê seria pior) e ficam registrados
   aqui como observação, já que consertá-los está fora do escopo desta feature.
8. **`test_mentor_cli` tem dependência de ordem** conhecida nesta suíte, e a §13 da spec
   (que pedia um commit por etapa) não pôde ser seguida — os dois pontos ficam registrados
   para quem for investigar a flakiness da suíte.

### Next steps

- **Bump de `__lang_version__`** no próximo release, para os `langs/*.json` atualizados
  serem realmente baixados (item 3 das observações).
- **Teste-guarda de i18n** sugerido: falhar quando qualquer `__()` receber um kwarg
  chamado `key` — pega a colisão do item 5 na hora em que ela é escrita, em vez de deixar
  a chave errada passar silenciosamente para o fallback em inglês.
- **Registry de packs** continua fora de escopo por decisão: `install` copia de um
  diretório local e nada nesta feature toca a rede.
- **`RiskConfig.enabled`/`include_in_review`** — decidir entre dar consumidor ou remover.
