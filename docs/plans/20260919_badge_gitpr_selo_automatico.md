# Badge "GitPR" — selo automático no PR + snippet estático para o README

## Context

A spec `docs/plans/20260918_skill_gitpr_badge_spec.md` pede duas coisas: um selo anexado automaticamente ao corpo do PR publicado, montado a partir de dados **reais** da revisão, e um comando `gitpr badge --readme` que imprime um snippet estático de adoção. O objetivo declarado é marketing viral (spec §10, tier Free): cada PR publicado carrega o nome do produto.

O levantamento mostrou que **a premissa central da spec não existe no código** — o fluxo padrão do `gitpr pr` não roda revisão nenhuma, não produz severidades e não mede duração. As decisões abaixo substituem essas premissas por dados que existem de verdade, sem inventar número. O selo diz apenas o que o linter local mediu, e **some quando não há nada medido** (Q11).

### Premissas da spec substituídas

| Spec assume                                                                                        | Realidade                                                                                                                                                                                                                                     | Decisão                                                                                         |
| -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `src/domain/branding/` + `src/application/use_cases/`                                              | Não existem camadas `domain`/`application`; as features são pacotes planos ([src/fix/](src/fix/), [src/review/](src/review/))                                                                                                                 | `src/branding/` (Q1)                                                                            |
| "função central de montagem do corpo do PR" para hookar                                            | **Quatro cópias independentes** do scaffold ([pr_publish_app.py:736](src/ui/pr_publish_app.py#L736), [main.py:2699](src/main.py#L2699), [main.py:1409](src/main.py#L1409), `review-pr`)                                                       | Um helper compartilhado, chamado por **um** ponto (Q2)                                          |
| `ReviewSummaryForBadge` com `blockers/criticals/warnings/total_findings/duration_seconds/provider` | O fluxo padrão **não roda review**: `generate_pr_content("pr", …)` devolve duas strings de prosa — sem severidade, sem duração ([core.py:827-851](src/core.py#L827-L851))                                                                     | Dataclass reduzida a `BadgeCounts(errors, warnings)`, do linter (Q5, Q6)                        |
| Verificação HTTP de que o selo renderiza                                                           | Nenhuma chamada de rede é necessária nem desejada                                                                                                                                                                                             | URL construída, nunca buscada                                                                   |
| Bloco em `config.schema.yml`                                                                       | **Esse arquivo não existe** (desvio registrado em [2026-09-05](docs/claude-code/reports/develop_natan/2026-09-05_scm_multiforge_providers.md#L17) e [2026-09-13](docs/claude-code/reports/develop_natan/2026-09-13_gitpr_fix_command.md#L12)) | `ConfigField` em [config_schema.py:265](src/config_schema.py#L265), espelhando `GITPR_COAUTHOR` |
| §9 "cada etapa deve ser um commit/PR isolado"                                                      | As regras do repo proíbem commit/push                                                                                                                                                                                                         | Entrega na árvore de trabalho, sem commits                                                      |

### Achados que mudaram o desenho

- **`parse_diff_and_lint(diff, skip_external=True)` é seguro no caminho do PR**: sem rede, sem download, sem subprocesso, e **nunca levanta** com regra ausente ou YAML quebrado ([linter_engine.py:209](src/linter_engine.py#L209)). Com `skip_external=False` ele executa binários configurados (ex.: `npx eslint`), que baixariam pacote — por isso `True`, o mesmo motivo do `review-pr`.
- **Sem regras, ele short-circuita e devolve listas vazias** ([linter_engine.py:226-227](src/linter_engine.py#L226-L227)) — indistinguível, pelo retorno, de um diff limpo. É o caso **comum** de quem nunca rodou `gitpr --skill`. Por isso o selo é omitido (Q11), e a detecção é perguntar antes: `load_linter_rules()` ([config.py:540](src/config.py#L540)) devolve `[]`.
- Os templates empacotados **não são fallback**: o wheel não leva arquivo não-`.py`, e `templates/gitpr.linter.yml` só é alcançável via `gitpr --skill`.
- Efeitos colaterais do linter, todos aceitos: `log_local_metric` grava um JSON em `~/.gitpr/metrics/` e roda `git remote -v`; YAML malformado imprime erro vermelho. Como o selo é montado **antes** do TUI montar (linha ~1453, antes do `while True:` de [main.py:1516](src/main.py#L1516)), o ruído cai no console, não dentro da tela.
- As regras são resolvidas a partir do **CWD** (`get_skill_dir()` = `os.getcwd() + "/.gitpr/skill"`): rodando de um subdiretório, não há regras e não há selo.
- As listas podem ter strings repetidas (não há dedup). O selo usa `len()`, nunca unicidade.
- `DOCS_BASE_URL` ([doc_links.py:11](src/doc_links.py#L11)) é a base do site; o selo aponta para a raiz `https://gitpr.natanfiuza.dev.br/` (Q10).

## Decisões (3 rodadas)

| #   | Decisão                                                                                                                                |
| --- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Q1  | Pacote `src/branding/`, sem camadas `domain`/`application`                                                                             |
| Q2  | Selo só nos dois caminhos que **publicam** corpo de PR: TUI e `--no-edit`. Não no `.md` local, não no MCP, não em comentário de review |
| Q3  | Ligado por padrão; opt-out `GITPR_BADGE=false`; aviso no `--init` **e** um aviso de uma linha na primeira publicação — nunca um prompt |
| Q4  | Escopo completo: docs ×5, README ×5, dogfooding do README do próprio repo                                                              |
| Q5  | Conteúdo = contagens reais do linter sobre o diff do PR                                                                                |
| Q6  | **Sem duração** — o único valor candidato só existe em cache miss                                                                      |
| Q7  | Visível e editável no TUI (semeado no TextArea); anexado na composição no `--no-edit`                                                  |
| Q8  | O tour do `demo` mostra o selo, montado do bloco `linter` gravado de cada cenário                                                      |
| Q9  | Rótulo `GitPR`, mensagem `N errors · M warnings`; `no issues` quando ambos zero. Sem verbo "reviewed"                                  |
| Q10 | Imagem clicável → `https://gitpr.natanfiuza.dev.br/`                                                                                   |
| Q11 | **Sem regras configuradas ⇒ sem selo.** O selo só fala quando uma regra rodou                                                          |

## Arquivos

```
src/branding/
├── __init__.py            # marcador de pacote (setuptools)
├── badge_data.py          # BadgeCounts + collect_linter_counts(diff_text)
└── badge_builder.py       # build_pr_badge / build_readme_badge / append_badge + escape shields

src/main.py                # ALTERAR — 1 ponto: monta e injeta em pr_data (~L1453); subcomando `badge`
src/config.py              # ALTERAR — badge_enabled() espelhando coauthor_enabled() (L298-311)
src/config_schema.py       # ALTERAR — ConfigField GITPR_BADGE (espelha GITPR_COAUTHOR, L265)
src/core.py                # ALTERAR — linha do aviso no wizard --init (run_scm_init_wizard)
src/demo/demo_screens.py   # ALTERAR — etapa do PR mostra o selo do cenário
src/updater.py             # ALTERAR — __lang_version__ -> v0.0.30
langs/*.json (6)           # ALTERAR — chaves novas de __() (paridade obrigatória)
docs/badge.md + 4          # NOVO
README.md + 4 variantes    # ALTERAR — selo dogfooded no topo + seção do comando
tests/badge/               # NOVO — suíte
```

## Contrato de dados

```python
@dataclass(frozen=True)
class BadgeCounts:
    errors: int
    warnings: int

def collect_linter_counts(diff_text: str) -> BadgeCounts | None:
    """None quando não há regras configuradas — nenhum selo é mostrado (Q11)."""

def build_pr_badge(counts: BadgeCounts) -> str: ...      # markdown, imagem linkada (Q10)
def build_readme_badge(style: str = "flat") -> str: ...  # estático, adoção
def append_badge(body: str, badge: str) -> str: ...      # idempotente, separador ---
```

**Cor e mensagem** (do que o usuário aprovou na Q9):

| errors | warnings | cor           | mensagem                |
| ------ | -------- | ------------- | ----------------------- |
| > 0    | qualquer | `red`         | `N errors · M warnings` |
| 0      | > 0      | `yellow`      | `0 errors · M warnings` |
| 0      | 0        | `brightgreen` | `no issues`             |

O zero é exibido junto (`0 errors · 2 warnings`), com pluralização por parte (`1 error`) — é exatamente o que a Q9 mostrou e aprovou. O corpo recebe **apenas a imagem markdown**: `GitPR | 0 errors · 2 warnings` é como o GitHub *renderiza* a imagem, não uma segunda linha de texto.

**Escaping shields.io**: substituições (`-` → `--`, `_` → `__`, espaço → `_`) e depois percent-encode do restante não-ASCII (`·` → `%C2%B7`), para a markdown carregar URL ASCII pura. Coberto por teste de igualdade exata.

`collect_linter_counts` envolve tudo em `try/except Exception: return None` — o selo **nunca** pode impedir a publicação.

## Onde o selo entra — um único ponto de inserção

`pr_data` é montado em [main.py:1449-1452](src/main.py#L1449-L1452), com o `diff_text` em escopo (usado logo abaixo em [main.py:1496](src/main.py#L1496)). Logo depois:

```python
badge = build_pr_badge(collect_linter_counts(diff_text))   # "" quando não há o que dizer
if badge:
    pr_data["pr_description"] = append_badge(pr_data["pr_description"], badge)
```

Isso satisfaz Q2/Q7 sem mudar assinatura nenhuma:

- **TUI** — o `pr_data` mutado chega em `PrPublishApp(pr_data=pr_data, …)` ([main.py:1518](src/main.py#L1518)) e é semeado em `self.pr_body` ([pr_publish_app.py:736](src/ui/pr_publish_app.py#L736)), visível e apagável no TextArea.
- **`--no-edit`** — `_publish_pr_directly` lê `pr_data.get("pr_description")` ([main.py:2697](src/main.py#L2697)) e o selo entra no `full_body` pelo caminho que já existe ([main.py:2699-2705](src/main.py#L2699-L2705)).
- **`--no-publish`** — escreve o `.md` do scaffold em [main.py:1409-1426](src/main.py#L1409-L1426), **antes** e em outro ramo: fica limpo (Q2).
- **Update de PR e F2 "salvar local"** reenviam/gravam o corpo corrente do TextArea — ou seja, o selo vai junto **se o usuário o tiver mantido**. É o comportamento correto: esses caminhos publicam o que está na tela.
- `append_badge` é idempotente (marca pela URL `img.shields.io/badge/GitPR`), então republicar não empilha selo.

## Opt-out, aviso e configuração

- `badge_enabled()` em [config.py](src/config.py) espelha `coauthor_enabled()` ([config.py:298-311](src/config.py#L298-L311)): desligado para `false/0/no/off/n`. **Não** entra em `DEFAULT_CONFIG` (precedente `GITPR_COAUTHOR`): o default é ligado por ausência, não por valor.
- `ConfigField` novo em [config_schema.py](src/config_schema.py), categoria `general`, `kind=KIND_BOOL`, label/description literais em `__()` (o scanner de i18n é AST). A description diz o default explicitamente ("ligado por padrão; `false` desliga"), porque a tela lê o env cru e um campo ausente aparece como não configurado. `KNOWN_KEYS` deriva de `FIELDS` — nada mais a tocar.
- Aviso no `--init` (wizard de forge, `run_scm_init_wizard`) e **um** aviso de uma linha na primeira publicação, controlado por um marcador no `~/.gitpr/.env` escrito pelo mesmo helper dos marcadores de versão (`LANG_VERSION`/`SMART_EXCLUDES_VERSION`) — localizado na implementação. Se não houver helper reaproveitável, o fallback é mostrar o aviso enquanto `GITPR_BADGE` estiver ausente.
- O texto do selo é **inglês fixo** (artefato público, como o corpo do PR). Os avisos, o help e a tela de config passam por `__()`.

## Comando `gitpr badge`

Subcomando registrado por decorator, como `demo`/`fix`/`release` — declarado antes do `return` de subcomando ([main.py:548-549](src/main.py#L548-L549)), o que o mantém fora dos gates de rede/update.

- `gitpr badge` — explica o que é e imprime o snippet.
- `gitpr badge --readme` — imprime **só** o snippet (pipe/`>>` friendly).
- `--style flat|flat-square|for-the-badge` (default `flat`); valor inválido → aviso amarelo e cai no `flat`.
- **Nunca escreve no README do usuário** — imprime (spec §5.4).
- Snippet: `[![GitPR](…/badge/GitPR-quality--checked-blue)](https://gitpr.natanfiuza.dev.br/)`.
- Sem entrada em `HELP_MAP` (precedente do `demo`): `gitpr badge --help` funciona, `gitpr -h --badge` continua erro.

## Demo

A etapa do PR passa a mostrar o selo, montado de `scenario["linter"]` (o bloco gravado de cada cenário, ex. [security_issue.py:116-125](src/demo/scenarios/security_issue.py#L116-L125)) — nenhum linter roda no tour, então nada de rede nem de leitura de `.gitpr/skill/`. Cenário com `errors` vazio mostra o selo amarelo; os dois cenários atuais têm esse formato.

## i18n

~10 chaves novas por arquivo em [langs/](langs/) ×6, paridade exata (o teste compara os seis; referência `pt_br`, piso anti-truncamento >500, gate de órfãs). `__lang_version__` → `v0.0.30` ([updater.py:11](src/updater.py#L11)) é o que faz um install existente baixar as chaves novas. **`tests/sync_i18n.py` não deve ser rodado** — o extrator regex dele trunca literais concatenados; a inserção é cirúrgica e ordenada, com round-trip byte a byte ([i18n-sync-canonicos-roundtrip](.claude/memory/i18n-sync-canonicos-roundtrip.md)).

## Testes (`tests/badge/`)

Segue [tests/README.md](tests/README.md) e o molde de [tests/demo/](tests/demo/) (`conftest.py` com rede banida por loopback, sem API key, interface em inglês). As sete provas obrigatórias da spec §8, mapeadas:

| #   | Arquivo                 | Prova                                                                                             |
| --- | ----------------------- | ------------------------------------------------------------------------------------------------- |
| 1   | `test_badge_builder.py` | cor por regra, plural, `no issues`, URL shields exata (escaping + percent-encode), link clicável  |
| 2   | `test_badge_data.py`    | contagens reais de um diff com regra; **`None` sem regras** (Q11); exceção do linter nunca escapa |
| 3   | `test_badge_optout.py`  | `false/0/no/off/n/NO` ⇒ sem selo; ausente ⇒ selo                                                  |
| 4   | `test_badge_append.py`  | idempotência (duas vezes = uma), separador `---`, corpo vazio                                     |
| 5   | `test_badge_cli.py`     | `--readme` imprime só o snippet; `--style for-the-badge`; estilo inválido → aviso + default; help |
| 6   | `test_badge_paths.py`   | TUI semeia com selo; `--no-edit` publica com selo; `--no-publish` **sem** selo                    |
| 7   | `test_badge_offline.py` | `socket`/`urllib`/`requests` armados para levantar durante toda a construção e impressão          |

Mais: um teste de que a etapa do PR do demo exibe o selo, e um de que o aviso de primeira publicação aparece uma vez só (HOME temporário).

## Verificação

```bash
python -m pytest tests/badge -q                   # suíte nova
python -m pytest tests/test_i18n.py -q            # paridade das 6 línguas
python -m pytest tests/demo -q                    # o tour continua verde
python -m pytest tests/ -q                        # suíte completa
```

A suíte completa tem **25 falhas pré-existentes**, listadas nominalmente no relatório do demo ([2026-09-18](docs/claude-code/reports/develop_natan/2026-09-18_gitpr_demo_mode.md#L75)): `test_config_app` (13), `test_suggest_reviewers` (5), `test_net_timeouts` (2) e uma em cada um de cinco outros arquivos. O critério é o **conjunto `FAILED` idêntico**, nome a nome — não a contagem.

End-to-end, em repo de rascunho com `.gitpr/skill/.gitpr.linter.yml` contendo uma regra que casa com o diff:

| Verificação     | Como                                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Offline real    | `python run.py badge --readme` imprime o snippet; `--style invalido` avisa e usa `flat`                                        |
| Corpo publicado | `resolve_scm_provider` stubado capturando `PullRequestRequest.description` nos caminhos `--no-edit` **e** TUI (via `run_test`) |
| `.md` local     | `--no-publish` gera arquivo **sem** selo                                                                                       |
| Sem regras      | removendo o `.gitpr/skill/.gitpr.linter.yml`, nenhum selo em nenhum caminho                                                    |
| Opt-out         | `GITPR_BADGE=false` ⇒ sem selo e sem aviso                                                                                     |
| Inspeção manual | abrir a URL shields construída no navegador (a URL é construída, nunca buscada pelo código)                                    |

## Ordem de execução

1. Survey do grill → `docs/survey/20260919_gitpr_badge_surveyfacts.md`
2. `src/branding/badge_data.py` + `badge_builder.py` + provas 1, 2 e 7 — **não seguir sem eles verdes**
3. `append_badge` + prova 4
4. Fiação em [main.py:1453](src/main.py#L1453) + prova 6 (os três caminhos)
5. `gitpr badge` + `GITPR_BADGE` (`ConfigField` + getter) + provas 3 e 5
6. Avisos (`--init` + primeira publicação) + chaves `__()` ×6 + `__lang_version__` → `v0.0.30`
7. Etapa do PR no demo + teste
8. `docs/badge.md` ×5 + README ×5 com o selo dogfooded
9. Suíte completa + relatório em `docs/claude-code/reports/develop_natan/2026-09-19_gitpr_badge.md`

## Avisos

- **Nada é commitado.** As regras do repo proíbem commit/push; tudo fica na árvore de trabalho. Isso contraria a §9 da spec ("cada etapa deve ser um commit/PR isolado"), que não pode ser honrada.
- **O selo quase nunca aparece no primeiro uso** — é a consequência deliberada da Q11. Quem nunca rodou `gitpr --skill` não tem regras, então não tem selo. A doc transforma isso em funil ("configure suas regras para o selo aparecer"), mas é honesto dizer: a viralidade só liga depois que o usuário configura o linter.
- **Efeito colateral do linter aceito**: uma linha de métrica em `~/.gitpr/metrics/` e um `git remote -v` por publicação com selo.
- **Ruído do YAML quebrado** cai no console antes do TUI montar — só acontece se o YAML do próprio usuário estiver inválido.
- **`gitpr -h --badge` não funciona** (subcomando sem `HELP_MAP`), igual ao `demo`.
- **Nome do arquivo de doc**: `docs/badge.md` — "badge" é o termo do produto e o nome do comando; se preferir o vocabulário do glossário, `docs/selo.md` implicaria renomear o comando.
