# Survey — `gitpr split`: commits atômicos por hunk

> Levantamento completo da sessão de grill da skill `grill-with-docs`.
> Task: executar o plano `docs/plans/20260918_skill_gitpr_split_command_spec.md`.
> Data: 2026-09-19 · Branch: `develop_natan`

---

## 1. Contexto da tarefa

A spec `docs/plans/20260918_skill_gitpr_split_command_spec.md` (221 linhas) pede um comando novo `gitpr split`: dado um working tree com mudanças não commitadas cobrindo múltiplas preocupações (bugfix + refatoração + config, tudo misturado), o GitPR analisa o diff, agrupa os hunks por intenção lógica usando IA, e propõe N commits atômicos — cada um com apenas os hunks relacionados e uma mensagem de commit gerada especificamente para aquele subconjunto.

A spec pede subopções `--dry-run` (default), `--apply`, `--interactive` e `--max-groups <n>`; classifica a entrega como Tier 2 (diferenciação e retenção) no tier Free/Community; define um contrato de dados em §3 que ela chama de **obrigatório**; exige 10 testes como critério de aceite (§7); e uma ordem de execução em 10 etapas (§8) onde "as etapas 1 e 2 são pré-requisitos de segurança que devem estar 100% testados antes de qualquer código que dependa deles ser escrito".

A própria §0 da spec reconhece o risco e exige que a skill **reporte explicitamente ao usuário, antes da implementação**, se o stage seletivo por hunk é uma extensão de algo existente ou uma capacidade nova construída do zero. É este o caso: **é do zero**.

**Três premissas da spec não correspondem ao código**, e uma decisão originalmente fechada no grill se revelou falha na rodada seguinte. Todas estão corrigidas abaixo.

---

## 2. Relatório de fatos levantados

Levantamento feito com três agentes de exploração read-only sobre o repositório, com leitura direta de confirmação nos pontos críticos.

### 2.1 A spec §0.1 manda reaproveitar um parser de hunks que não existe

A spec afirma que o agrupamento deve reaproveitar "o parser de diff já existente no motor de map-reduce". O motor de map-reduce **não tem parser**. Ele quebra o texto por granularidade de **arquivo**, numa única linha:

```python
# src/core.py:737
parts = re.split(r"(^diff --git a/)", diff_text, flags=re.MULTILINE)
```

O resultado é `list[str]` — fatias de texto cru. Sem dataclass, sem hunk, sem faixa de linhas, sem identidade por unidade.

O primitivo reutilizável mais próximo é `split_patch_sections(diff_text)` (`src/diff_parser.py:256`), que devolve `list[PatchSection]` (`PatchSection` é dataclass frozen em `:243`, com `path` e `text` verbatim, headers inclusos) — também **granularidade de arquivo**.

O `_HUNK_HEADER_RE` (`src/diff_parser.py:17`) é `^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@`: captura **apenas** o lado novo (start e count), não captura o lado antigo, e não captura corpo de hunk. Pior: seus grupos de captura são consumidos por `summarize_patch` e `parse_added_lines`, então **não pode ser alargado no lugar** sem quebrar os dois.

**Nenhuma biblioteca de parsing de diff está declarada** — `unidiff`, `whatthepatch`, `patch-ng`, `diff-match-patch`: nada em `pyproject.toml` nem no `Pipfile`.

Conclusão: o parser de hunks é código novo.

### 2.2 A spec §5 pede para confirmar se já existe stage seletivo — não existe

**Não existe nenhuma capacidade de staging seletivo no projeto.** A única escrita no índice é `stage_files(filepaths)` (`src/core.py:2031`), que roda `git add` em arquivos inteiros, tudo-ou-nada.

Varredura no repositório inteiro: `--cached` não aparece em lugar nenhum de `src/`; `update-index`, `add -p`, `--intent-to-add`, `diff --cached` e `git reset` também não. As três ocorrências de `git apply` são todas via `patch_applier._apply`, e usam exclusivamente `--check`, `[]` e `--reverse`.

Ou seja: `selective_stager.py` é construído do zero, e é de fato — como a spec suspeitava — o componente de maior risco técnico, porque erros nessa camada corrompem o histórico Git real do usuário.

### 2.3 O wrapper de `git apply` existe, é único, e está no pacote errado

`src/fix/patch_applier.py` está **completamente implementado** (nenhum stub nos sete módulos de `src/fix/`). O caminho único de aplicação é `_apply(args, diff_text, cwd)` (`:62`), que roda `["git", "apply"] + args + ["-"]` alimentando o patch por **stdin como bytes** — nunca por arquivo temporário, e nunca como texto. Isso é uma defesa deliberada contra Windows: o stdin em modo texto abre com universal-newlines na *escrita*, então todo `\n` do patch chegaria ao git como `\r\n` e o git recusaria o patch inteiro (falha total e silenciosa, só no Windows). Está documentado no docstring.

Os wrappers públicos são `check_patch` (`--check`), `apply_patch` (nada) e `reverse_patch` (`--reverse`). **`--cached` nunca é usado.**

O problema: esse módulo é o adaptador compartilhado de `git apply` do projeto, mas mora dentro de `src/fix/`, que é um pacote de *feature*. `split` precisa de um quarto verbo (`--cached`).

### 2.4 O pipeline de mensagem de commit é reutilizável sem atrito

Confirmado e limpo: `generate_pr_content(action_folder, action_type, diff_text, provider="gemini", cache_scope="", store_diff=False)` (`src/core.py:762`) recebe **uma string de diff crua** — o próprio docstring (`:771-774`) diz que a função não se importa de onde o diff veio. Chamada do fluxo de commit: `generate_pr_content("commit", "commit", diff, provider)`.

O que vem junto de graça: carregamento da skill `.gitpr.commit.md` via `get_skill_context`, cache MD5 em `~/.gitpr/cache/prompts/commit/`, tier de modelo `"simple"`, chunking map-reduce acima de 90000 "tokens" (`len//4`), e telemetria. Devolve `{"commit_message": "..."}`.

É exatamente o "reaproveitar 100%, só trocando a entrada" que a spec §4.6 pede.

### 2.5 `get_git_diff()` é inutilizável para esta feature

Esta é a descoberta que a spec não antecipou, e é a mais consequente.

```python
# src/core.py:528
cmd = ["git", "diff", "-U1", "-w", "-M", "-B", "HEAD", "--"] + SMART_EXCLUDES
```

**`-w` produz um diff que não pode ser aplicado.** Com `-w`, diferenças que são apenas de whitespace são renderizadas como *contexto* — e a linha de contexto emitida pode não bater byte a byte com o conteúdo do arquivo. O `git apply` então ou recusa o hunk, ou aplica conteúdo que difere do working tree. Isso quebra o critério de aceite #3 da spec (estado final byte-a-byte idêntico) e a cláusula de compatibilidade da §1.

O `-U1` agrava: uma linha de contexto é pouco para o `--check` ancorar. E `-B` (break rewrites) decompõe reescritas em delete+add, o que é ruim para aplicação.

`-M` (detecção de rename) é o único que **precisa ficar**: sem ele um rename vira delete + add, e o lado "add" é um arquivo untracked — que está fora de escopo — então o split commiteria um delete puro do caminho antigo enquanto o arquivo novo fica untracked. Isso tem cara de perda de dado.

Conclusão: `split` precisa da sua própria captura de diff, com flags seguras para aplicação.

### 2.6 A ordem "unstage antes de capturar o diff" estava errada

Descoberta na rodada de design, não na spec nem nas rodadas iniciais do grill.

Um arquivo novo *staged* e um rename *staged* só aparecem em `git diff HEAD` **porque o índice os rastreia**. Um `git reset` deixa o caminho novo como untracked — e untracked está fora de escopo — então o arquivo sai completamente do diff e, portanto, do plano.

Ou seja: com "unstage primeiro", um arquivo novo do usuário desapareceria silenciosamente do split. O plano mostrado e o plano aplicado divergiriam.

A correção não é "re-diff e aborta em divergência" (que responde um "sim" do usuário com um "não"): é **capturar o diff primeiro**. Hunks de `git diff HEAD` carregam pré-imagem baseada em HEAD independentemente do que está staged; depois do `git reset` o índice *é* HEAD, então as mesmas pré-imagens aplicam limpo. Captura primeiro, unstage por último — e o `--dry-run` continua sem tocar em nada, em qualquer estado de índice.

### 2.7 Fatos de infraestrutura levantados

| Item | Fato |
|---|---|
| `config.schema.yml` | **Não existe.** É um desvio já registrado 3 vezes (`2026-09-05_scm_multiforge_providers.md`, `2026-09-13_gitpr_fix_command.md`, e o survey do badge). O mecanismo real é `ConfigField`/`Category` em `src/config_schema.py` + `DEFAULT_CONFIG` e um getter em `src/config.py` (`get_fix_settings()` em `:724` é o molde) |
| Rótulos i18n | Precisam ser chamadas `__()` literais — `tests/test_i18n.py` varre a AST |
| `scripts/fix_mangled_i18n_keys.py` | **Não tocar** — `test_clean_keys_present_and_translated` afirma `len(CLEAN_KEYS) == 49` |
| Glossários | Convenção do repo é `docs/plans/glossary-<feature>.md` (6 existentes), **não** `CONTEXT.md` |
| ADRs | `docs/plans/ADR-NNN-<slug>.md`; 001–005 ocupados; `ADR-002` está duplicado no repo (pré-existente) |
| Testes | `unittest.TestCase` dominante; `tests/fix/git_fixture.py` tem `GitRepoTestCase` com `write/read/commit/patch_for/status_porcelain/seed`; `conftest.py` por diretório bane sockets não-loopback |
| `generate_pr_content` | Imprime um banner por chamada → N banners para N grupos. Aceito como saída de progresso |
| `execute_git_commit` | Não devolve hash (`core.py:2072`) → `commits_created` vem de `current_head()` depois de cada commit |
| TUI | `CommitMessageScreen` (`pr_publish_app.py:461`, proposta editável) e `CommitConfirmScreen` (`:311`) são o precedente do padrão "mostra proposta, confirma antes de aplicar" |

---

## 3. Decisões das rodadas

Seis rodadas. A fronteira está esgotada — nenhuma decisão ficou por assumir.

### Rodada 1 — Estrutura e escopo

| # | Questão | Decisão |
|---|---|---|
| D1 | Layout: DDD da spec vs convenção do projeto | `src/split/` (sub-pacote de feature) + `src/infrastructure/git/` (adaptador) |
| D2 | Spec §8 pede commit por etapa; CLAUDE.md proíbe commits | Uma passada só, tudo no working tree, sem commits da ferramenta |
| D3 | `--interactive` | **Adiado** — fora desta entrega |
| D4 | Arquivos untracked | Fora de escopo na v1, com aviso explícito nomeando-os |

### Rodada 2 — Captura de diff e índice

| # | Questão | Decisão |
|---|---|---|
| D5 | Flags do diff | `get_split_diff()` novo: `("--binary", "-M", "-U3")`, sem pathspec |
| D6 | Precondição do índice | Prompt para dar unstage, dobrado na confirmação de apply |
| D7 | Onde mora o wrapper de `--cached` | Move para `src/infrastructure/git/`, shim de re-export em `src/fix/` |
| D8 | Semântica de smart excludes | **Nenhuma exclusão no split** |

### Rodada 3 — Parser, IA e config

| # | Questão | Decisão |
|---|---|---|
| D9 | Onde mora o parser de hunks | Módulo novo em `src/split/`, reusando `split_patch_sections()` |
| D10 | Batching da classificação | Chamada única, sem batching; degrada para ungrouped |
| D11 | Chaves de config | Três: `MAX_GROUPS`(5), `REQUIRE_CONFIRMATION`(true), `MAX_HUNKS`(50) |
| D12 | Seções sem hunk (binário, rename puro, mode-only) | Grupos atômicos forçados |

### Rodada 4 — Docs, modelo e artefatos

| # | Questão | Decisão |
|---|---|---|
| D13 | Escopo de docs e i18n | **Passada completa** nos 6 `langs/*.json` + 5 READMEs |
| D14 | Como o contrato expressa grupo sem hunks | Supertype `ChangeUnit` |
| D15 | Glossário e ADR | Ambos: `docs/plans/glossary-gitpr-split.md` + `ADR-006-split-apply-safety.md` |
| D16 | `gitpr split` puro | Imprime o plano **e** oferece aplicar |

### Rodada 5 — Flags e tipo

| # | Questão | Decisão |
|---|---|---|
| D17 | Distinção entre os três modos | `--dry-run` ganha trabalho próprio: imprime e nunca pergunta |
| D18 | Como expressar `ChangeUnit` | **Union alias** PEP 604: `ChangeUnit = Hunk \| OpaqueSection` |

### Rodada 6 — Correções de segurança

| # | Questão | Decisão |
|---|---|---|
| D19 | Ponto de captura do diff vs unstage | **Captura primeiro, unstage por último** (ver §2.6) |
| D20 | CRLF | Documentar; `--check` é o portão. Falha alto, nunca corrompe |
| D21 | Binários | Adicionar `--binary` às flags |
| D22 | Origem do prompt de agrupamento | Instrução fixa embutida (não uma skill) |

---

## 4. Desvios do contrato "obrigatório" da spec §3

Quatro, todos com razão técnica:

| Contrato da spec | Desvio | Por quê |
|---|---|---|
| `HunkGroup.hunks: list[Hunk]` | `HunkGroup.units: list[ChangeUnit]` | D14 — um grupo forçado (rename puro, binário) não tem hunks; o campo mentiria |
| `Hunk` com 6 campos | + `file_header`, `old_count`, `new_count`, `ordinal` | O header de arquivo **não é reconstruível** a partir do path: `new file mode`, `deleted file mode`, `old mode`/`new mode` e a forma citada de paths não-ASCII são irrecuperáveis — e sintetizá-los quebra o `git apply` |
| `SplitPlan.ungrouped_hunks` / `total_hunks` | `ungrouped_units` / `total_units` | Consequência direta de D14 |
| `apply_split_plan(..., require_confirmation: bool)` | callable `confirm` injetável | Um caso de uso não deve ser dono de um prompt — e `CliRunner` não pode precisar de stdin |

Também removido: `generate_split_plan(..., include_staged, include_unstaged)`. Com D6 + D19 o staged e o unstaged são um diff só, e a distinção não significa nada.

---

## 5. Riscos aceitos conscientemente

1. **CRLF** — captura com `text=True` mais o `rstrip("\r")` de `split_patch_sections` remove os CRs, e o patch remontado é recusado em repositórios `core.autocrlf=false` com arquivos CRLF. Falha alta via `--check`, nunca aplicação corrompida. Revisitar (captura em bytes + parser próprio, abandonando o reuso) só se morder um usuário real.
2. **N banners** do `generate_pr_content` para N grupos. Aceito como saída de progresso.
3. **Sem rollback automático** em falha no meio da sequência — a spec §1 põe undo automático fora de escopo; os commits 1..N-1 permanecem intactos e o relatório diz exatamente o que foi aplicado. Índice tratado por sítio de falha: falha de staging dispara `unstage_all`; falha de commit deixa o grupo staged e diz isso verbatim, em vez de esconder quais hunks estavam em voo.
4. **Fallback terminal** (acrescentado pelo grill; a spec não tem saída para isso): quando forçar o arquivo inteiro num grupo ainda falha no `--check` — arquivo CRLF, unidade binária — as unidades vão para `ungrouped_units` com aviso. O laço de conflito é limitado e sempre termina.
